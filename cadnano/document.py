# -*- coding: utf-8 -*-

from operator import itemgetter
from uuid import uuid4
from typing import (
    Set,
    List,
    Tuple,
    Iterable,
    Iterator,
    Optional
)

from cadnano import (
    app,
    setBatch,
    util
)
from cadnano.addinstancecmd import AddInstanceCommand
from cadnano.proxies.cnenum import (
    EnumType,
    GridEnum,
    ModEnum,
    PointEnum,
    ViewSendEnum
)
from cadnano.proxies.cnobject import CNObject
from cadnano.objectinstance import ObjectInstance
from cadnano.proxies.cnproxy import (
    ProxySignal,
    UndoStack
)
from cadnano.docmodscmd import (
    AddModCommand,
    ModifyModCommand,
    RemoveModCommand
)
from cadnano.fileio.decode import decodeFile
from cadnano.fileio.encode import encodeToFile

from cadnano.part import Part
from cadnano.part.nucleicacidpart import NucleicAcidPart
from cadnano.part.refreshsegmentscmd import RefreshSegmentsCommand
from cadnano.oligo import Oligo
from cadnano.strandset import StrandSet
from cadnano.strand import Strand

from cadnano.cntypes import (
    DocCtrlT,
    DocT,
    WindowT
)

# Type Aliases
EndsSelected = Tuple[bool, bool]

class Document(CNObject):
    """
    The Document class is the root of the model. It has two main purposes:
    1. Serve as the parent all Part objects within the model.
    2. Track all sub-model actions on its undoStack.

    Args:
        parent (CNObject): optional, defaults to None

    Attributes:
        view_names (list): views the document should support
        filter_set (set): filters that should be applied when selecting.
    """

    def __init__(self, parent=None):
        super(Document, self).__init__(parent)

        self._undostack = us = UndoStack()  # notice NO parent, what does this mean?
        us.setUndoLimit(30)
        self._children = set()     # for storing a reference to Parts (and Assemblies)
        self._instances = set()    # for storing instances of Parts (and Assemblies)
        self._app_window = None
        # the dictionary maintains what is selected
        self._selection_dict = {}
        self._active_part = None

        self._filename = None

        # the added list is what was recently selected or deselected
        self._strand_selected_changed_dict = {}
        self.view_names = []
        self.filter_set: Set[str] = set()
        self._mods = {}  # modifications keyed by mod id
        this_app = app()
        this_app.documentWasCreatedSignal.emit(self)
    # end def

    # SIGNALS #
    # Signal 1. Connected to the ViewRoots
    documentPartAddedSignal = ProxySignal(object, CNObject, name='documentPartAddedSignal')
    """`Document`, `Part`"""

    documentAssemblyAddedSignal = ProxySignal(object, CNObject, name='documentAssemblyAddedSignal')
    """`Document`, `Assembly`"""
    documentSelectionFilterChangedSignal = ProxySignal(object, name='documentSelectionFilterChangedSignal')
    documentPreXoverFilterChangedSignal = ProxySignal(str, name='documentPreXoverFilterChangedSignal')
    documentViewResetSignal = ProxySignal(CNObject, name='documentViewResetSignal')
    documentClearSelectionsSignal = ProxySignal(CNObject, name='documentClearSelectionsSignal')
    documentChangeViewSignalingSignal = ProxySignal(int, name='documentChangeViewSignalingSignal')

    # Signal 1. Connected to the ModTool
    documentModAddedSignal = ProxySignal(object, object, object, name='documentModAddedSignal')
    documentModRemovedSignal = ProxySignal(object, object, name='documentModRemovedSignal')
    documentModChangedSignal = ProxySignal(object, object, object, name='documentModChangedSignal')

    # SLOTS #

    # ACCESSORS #
    def undoStack(self) -> UndoStack:
        """This is the actual undoStack to use for all commands. Any children
        needing to perform commands should just ask their parent for the
        undoStack, and eventually the request will get here.
        """
        return self._undostack

    def children(self) -> Set[CNObject]:
        """Returns a list of parts associated with the document.

        Returns:
            list: list of all child objects
        """
        return self._children

    def addRefObj(self, child: CNObject):
        """For adding Part and Assembly object references
        Args:
            child (object):
        """
        self._children.add(child)

    def addInstance(self, instance: ObjectInstance):
        """Add an ObjectInstance to the list of instances

        Args:
            instance:
        """
        self._instances.add(instance)

    def removeInstance(self, instance: ObjectInstance):
        """ Remove an ObjectInstance from the list of instances

        Args:
            instance:
        """
        self._instances.remove(instance)
        self.documentClearSelectionsSignal.emit(self)

    def removeAllChildren(self):
        """Used to reset the document. Not undoable."""
        self.documentClearSelectionsSignal.emit(self)
        for child in list(self._children):
            child.remove(use_undostack=True)
        self.undoStack().clear()
        self.deactivateActivePart()
    # end def

    def setFilterSet(self, filter_list: List[str]):
        """ Set the Document filter list.

        Emits `documentSelectionFilterChangedSignal`

        Args:
            filter_list: list of filter key names
        """
        assert isinstance(filter_list, list)

        vhkey = 'virtual_helix'
        fs = self.filter_set
        if vhkey in filter_list and vhkey not in fs:
            self.clearAllSelected()
        if vhkey in fs and vhkey not in filter_list:
            self.clearAllSelected()

        self.filter_set = fs = set(filter_list)
        self.documentSelectionFilterChangedSignal.emit(fs)
    # end def

    def removeRefObj(self, child: CNObject):
        """ Remove child Part or Assembly

        Args:
            child:
        """
        self._children.remove(child)
    # end def

    def activePart(self) -> Part:
        return self._active_part
    # end def

    def setActivePart(self, part: Part):
        self._active_part = part
    # end def

    def deactivateActivePart(self):
        self._active_part = None
    # end def

    def changeViewSignaling(self, signal_enum: int = ViewSendEnum.ALL):
        '''Turn on and off viwe signaling for enabled slots in views.
        Signals the root item in each view

        Arg:
            signal_enum: Default turns on all views signals
        '''
        self.documentChangeViewSignalingSignal.emit(signal_enum)
    # end def

    def fileName(self) -> str:
        return self._filename
    # end def

    def setFileName(self, fname: str):
        self._filename = fname
    # end def

    def writeToFile(self, filename: str, legacy: bool = False):
        """ Convenience wrapper for `encodeToFile` to set the `document`
        argument to `self`

        Args:
            filename: full path file name
            legacy: attempt to export cadnano2 format
        """
        encodeToFile(filename, self, legacy)
    # end def

    def readFile(self, filename: str) -> DocT:
        """Convenience wrapper for ``decodeFile`` to always emit_signals and
        set the ``document`` argument to ``self``

        Args:
            filename: full path file name

        Returns:
            self ``Document`` object with data decoded from ``filename``
        """
        print("reading file", filename)
        return decodeFile(filename, document=self, emit_signals=True)
    # end def

    # def assemblies(self):
    #     """Returns a list of assemblies associated with the document."""
    #     return self._assemblies

    # PUBLIC METHODS FOR QUERYING THE MODEL #

    def addStrandToSelection(self, strand: Strand, value: EndsSelected):
        """ Add `Strand` object to Document selection

        Args:
            strand:
            value: of the form::

                (is low index selected, is high index selected)

        """
        ss = strand.strandSet()
        if ss in self._selection_dict:
            self._selection_dict[ss][strand] = value
        else:
            self._selection_dict[ss] = {strand: value}
        self._strand_selected_changed_dict[strand] = value
    # end def

    def removeStrandFromSelection(self, strand: Strand) -> bool:
        """Remove ``Strand`` object from Document selection

        Args:
            strand:

        Returns:
            ``True`` if successful, ``False`` otherwise
        """
        ss = strand.strandSet()
        if ss in self._selection_dict:
            temp = self._selection_dict[ss]
            if strand in temp:
                del temp[strand]
                if len(temp) == 0:
                    del self._selection_dict[ss]
                self._strand_selected_changed_dict[strand] = (False, False)
                return True
            else:
                return False
        else:
            return False
    # end def

    def addVirtualHelicesToSelection(self, part: Part, id_nums: Iterable[int]):
        """If the ``Part`` isn't in the ``_selection_dict`` its not
        going to be in the changed_dict either, so go ahead and add

        Args:
            part: The Part
            id_nums: List of virtual helix ID numbers
        """
        selection_dict = self._selection_dict
        if part not in selection_dict:
            selection_dict[part] = s_set = set()
        else:
            s_set = selection_dict[part]
        changed_set = set()
        for id_num in id_nums:
            if id_num not in s_set:
                s_set.add(id_num)
                changed_set.add(id_num)
        if len(changed_set) > 0:
            part.partVirtualHelicesSelectedSignal.emit(part, changed_set, True)
    # end def

    def removeVirtualHelicesFromSelection(self, part: Part, id_nums: Iterable[int]):
        """Remove from the ``Part`` selection the ``VirtualHelix`` objects
        specified by id_nums.

        Args:
            part:
            id_nums:
        """
        # print("remove called", id(part), id_nums,  self._selection_dict.get(part))
        selection_dict = self._selection_dict
        if part in selection_dict:
            s_set = selection_dict[part]
            changed_set = set()
            for id_num in id_nums:
                if id_num in s_set:
                    s_set.remove(id_num)
                    if len(s_set) == 0:
                        del selection_dict[part]
                    changed_set.add(id_num)
            if len(changed_set) > 0:
                part.partVirtualHelicesSelectedSignal.emit(part, changed_set, False)
    # end def

    def selectedOligos(self) -> Set[Oligo]:
        """As long as one endpoint of a strand is in the selection, then the
        oligo is considered selected.

        Returns:
            Set of zero or more selected :obj:`Oligos`
        """
        s_dict = self._selection_dict
        selected_oligos = set()
        for ss in s_dict.keys():
            for strand in ss:
                selected_oligos.add(strand.oligo())
            # end for
        # end for
        return selected_oligos
    # end def

    def clearAllSelected(self):
        """Clear all selections
        emits documentClearSelectionsSignal
        """
        # print("clearAllSelected")
        self._selection_dict = {}
        # the added list is what was recently selected or deselected
        self._strand_selected_changed_dict = {}
        self.documentClearSelectionsSignal.emit(self)
    # end def

    def isModelStrandSelected(self, strand: Strand) -> bool:
        ss = strand.strandSet()
        if ss in self._selection_dict:
            if strand in self._selection_dict[ss]:
                return True
            else:
                return False
        else:
            return False
    # end def

    def isVirtualHelixSelected(self, part: Part, id_num: int) -> bool:
        """For a given ``Part``

        Args:
            part: ``Part`` in question
            id_num: ID number of a virtual helix

        Returns:
            ``True`` if ``id_num`` is selected else ``False``
        """
        if part in self._selection_dict:
            return id_num in self._selection_dict[part]
        else:
            return False
    # end def

    def isOligoSelected(self, oligo: Oligo) -> bool:
        """Determine if given ``Oligo`` is selected

        Args:
            oligo: ``Oligo`` object

        Returns:
            ``True`` if ``oligo`` is selected otherwise ``False``
        """
        strand5p = oligo.strand5p()
        for strand in strand5p.generator3pStrand():
            if self.isModelStrandSelected(strand):
                return True
        return False
    # end def

    def selectOligo(self, oligo: Oligo):
        """Select given ``Oligo``

        Args:
            oligo: ``Oligo`` object
        """
        strand5p = oligo.strand5p()
        both_ends = (True, True)
        for strand in strand5p.generator3pStrand():
            self.addStrandToSelection(strand, both_ends)
        self.updateStrandSelection()
    # end def

    def deselectOligo(self, oligo: Oligo):
        """Deselect given ``Oligo``

        Args:
            oligo: ``Oligo`` object
        """
        strand5p = oligo.strand5p()
        for strand in strand5p.generator3pStrand():
            self.removeStrandFromSelection(strand)
        self.updateStrandSelection()
    # end def

    def getSelectedStrandValue(self, strand: Strand) -> EndsSelected:
        """Strand is an object to look up
        it is pre-vetted to be in the dictionary

        Args:
            strand: ``Strand`` object in question

        Returns:
            Tuple of the end point selection
        """
        return self._selection_dict[strand.strandSet()][strand]
    # end def

    def sortedSelectedStrands(self, strandset: StrandSet) -> List[Strand]:
        """Get a list sorted from low to high index of `Strands` in a `StrandSet`
        that are selected

        Args:
            strandset: :obj:`StrandSet` to get selected strands from

        Returns:
            List of :obj:`Strand`s
        """
        out_list = [x for x in self._selection_dict[strandset].items()]

        def getLowIdx(x): return Strand.lowIdx(itemgetter(0)(x))
        out_list.sort(key=getLowIdx)
        return out_list
    # end def

    def determineStrandSetBounds(self,  selected_strand_list: List[Tuple[Strand, EndsSelected]],
                                        strandset: StrandSet) -> Tuple[int, int]:
        """Determine the bounds of a :class:`StrandSet` ``strandset`` among a
        a list of selected strands in that same ``strandset``

        Args:
            selected_strand_list: list of ``( Strands, (is_low, is_high) )`` items
            strandset: of interest

        Returns:
            tuple: min low bound and min high bound index
        """
        length = strandset.length()
        min_high_delta = min_low_delta = max_ss_idx = length - 1  # init the return values
        ss_dict = self._selection_dict[strandset]

        for strand, value in selected_strand_list:
            idx_low, idx_high = strand.idxs()
            low_neighbor, high_neighbor = strandset.getNeighbors(strand)
            # print(low_neighbor, high_neighbor)
            if value[0]:    # the end is selected
                if low_neighbor is None:
                    temp = idx_low - 0
                else:
                    if low_neighbor in ss_dict:
                        value_N = ss_dict[low_neighbor]
                        # we only care if the low neighbor is not selected
                        temp = min_low_delta if value_N[1] else idx_low - low_neighbor.highIdx() - 1
                    # end if
                    else:  # not selected
                        temp = idx_low - low_neighbor.highIdx() - 1
                    # end else

                if temp < min_low_delta:
                    min_low_delta = temp
                # end if
                # check the other end of the strand
                if not value[1]:
                    temp = idx_high - idx_low - 1
                    if temp < min_high_delta:
                        min_high_delta = temp

            # end if
            if value[1]:
                if high_neighbor is None:
                    temp = max_ss_idx - idx_high
                else:
                    if high_neighbor in ss_dict:
                        value_N = ss_dict[high_neighbor]
                        # we only care if the low neighbor is not selected
                        temp = min_high_delta if value_N[0] else high_neighbor.lowIdx() - idx_high - 1
                    # end if
                    else:  # not selected
                        temp = high_neighbor.lowIdx() - idx_high - 1
                    # end else

                # end else
                if temp < min_high_delta:
                    min_high_delta = temp
                # end if
                # check the other end of the strand
                if not value[0]:
                    temp = idx_high - idx_low - 1
                    if temp < min_low_delta:
                        min_low_delta = temp
            # end if
        # end for
        return (min_low_delta, min_high_delta)
    # end def

    def getSelectionBounds(self) -> Tuple[int, int]:
        """Get the index bounds of a strand selection

        Returns:
            tuple: of :obj:`int`
        """
        min_low_delta = -1
        min_high_delta = -1
        for strandset in self._selection_dict.keys():
            selected_list = self.sortedSelectedStrands(strandset)
            temp_low, temp_high = self.determineStrandSetBounds(selected_list, strandset)
            if temp_low < min_low_delta or min_low_delta < 0:
                min_low_delta = temp_low
            if temp_high < min_high_delta or min_high_delta < 0:
                min_high_delta = temp_high

        return (min_low_delta, min_high_delta)
    # end def

    def deleteStrandSelection(self, use_undostack: bool = True):
        """Delete selected strands. First iterates through all selected strands
        and extracts refs to xovers and strands. Next, calls removeXover
        on xoverlist as part of its own macroed command for isoluation
        purposes. Finally, calls removeStrand on all strands that were
        fully selected (low and high), or had at least one non-xover
        endpoint selected.
        """
        xoList = []
        strand_dict = {}
        for strandset_dict in self._selection_dict.values():
            for strand, selected in strandset_dict.items():
                part = strand.part()
                idx_low, idx_high = strand.idxs()
                strand5p = strand.connection5p()
                strand3p = strand.connection3p()
                # both ends are selected
                strand_dict[strand] = selected[0] and selected[1]

                # only look at 3' ends to handle xover deletion
                sel3p = selected[0] if idx_low == strand.idx3Prime() else selected[1]
                if sel3p:  # is idx3p selected?
                    if strand3p:  # is there an xover
                        xoList.append((part, strand, strand3p, use_undostack))
                    else:  # idx3p is a selected endpoint
                        strand_dict[strand] = True
                else:
                    if not strand5p:  # idx5p is a selected endpoint
                        strand_dict[strand] = True

        if use_undostack and xoList:
            self.undoStack().beginMacro("Delete xovers")
        for part, strand, strand3p, useUndo in xoList:
            NucleicAcidPart.removeXover(part, strand, strand3p, useUndo)
            self.removeStrandFromSelection(strand)
            self.removeStrandFromSelection(strand3p)
        self._selection_dict = {}
        self.documentClearSelectionsSignal.emit(self)
        if use_undostack:
            if xoList:  # end xover macro if it was started
                self.undoStack().endMacro()
            if True in strand_dict.values():
                self.undoStack().beginMacro("Delete selection")
            else:
                return  # nothing left to do
        for strand, delete in strand_dict.items():
            if delete:
                strand.strandSet().removeStrand(strand)
        if use_undostack:
            self.undoStack().endMacro()
    # end def

    def resizeSelection(self, delta: int, use_undostack: bool = True):
        """Moves the selected idxs by delta by first iterating over all strands
        to calculate new idxs (method will return if snap-to behavior would
        create illegal state), then applying a resize command to each strand.

        Args:
            delta:
            use_undostack: optional, default is ``True``
        """
        resize_list = []
        vh_set = set()
        # calculate new idxs
        part = None
        for strandset_dict in self._selection_dict.values():
            for strand, selected in strandset_dict.items():
                if part is None:
                    part = strand.part()
                idx_low, idx_high = strand.idxs()
                new_low, new_high = strand.idxs()
                delta_low = delta_high = delta

                # process xovers to get revised delta
                if selected[0] and strand.connectionLow():
                    new_low = part.xoverSnapTo(strand, idx_low, delta)
                    if new_low is None:
                        return
                    delta_high = new_low - idx_low
                if selected[1] and strand.connectionHigh():
                    new_high = part.xoverSnapTo(strand, idx_high, delta)
                    if new_high is None:
                        return
                    delta_low = new_high - idx_high

                # process endpoints
                if selected[0] and not strand.connectionLow():
                    new_low = idx_low + delta_low
                if selected[1] and not strand.connectionHigh():
                    new_high = idx_high + delta_high

                if new_low > new_high:  # check for illegal state
                    return

                vh_set.add(strand.idNum())
                resize_list.append((strand, new_low, new_high))
            # end for
        # end for

        # execute the resize commands
        us = self.undoStack()
        if use_undostack:
            us.beginMacro("Resize Selection")

        for strand, idx_low, idx_high in resize_list:
            Strand.resize(strand,
                          (idx_low, idx_high),
                          use_undostack,
                          update_segments=False)
        if resize_list:
            cmd = RefreshSegmentsCommand(part, vh_set)
            if use_undostack:
                us.push(cmd)
            else:
                cmd.redo()

        if use_undostack:
            us.endMacro()
    # end def

    def updateStrandSelection(self):
        """Do it this way in the future when we have
        a better signaling architecture between views
        For now, individual objects need to emit signals

        """
        oligos_selected_set = set()
        oligos_set = set()
        for obj, value in self._strand_selected_changed_dict.items():
            oligo = obj.oligo()
            oligos_set.add(oligo)
            if True in value:
                oligos_selected_set.add(oligo)
            obj.strandSelectedChangedSignal.emit(obj, value)
        # end for
        for oligo in oligos_selected_set:
            oligo.oligoSelectedChangedSignal.emit(oligo, True)
        oligos_deselected_set = oligos_set - oligos_selected_set
        for oligo in oligos_deselected_set:
            oligo.oligoSelectedChangedSignal.emit(oligo, False)
        self._strand_selected_changed_dict = {}
    # end def

    def resetViews(self):
        """This is a fast way to clear selections and the views.
        We could manually deselect each item from the Dict, but we'll just
        let them be garbage collect
        the dictionary maintains what is selected
        """
        # print("reset views")
        self._selection_dict = {}
        # the added list is what was recently selected or deselected
        self._strand_selected_changed_dict = {}
        self.documentViewResetSignal.emit(self)
    # end def

    def makeNew(self, fname: str = "untitled.json"):
        """For use in creating a new ``Document``

        Args:
            fname: new filename, default is ``untitled.json``
        """
        self.clearAllSelected()
        self.resetViews()
        setBatch(True)
        self.removeAllChildren()  # clear out old parts
        setBatch(False)
        self.undoStack().clear()  # reset undostack
        self.deactivateActivePart()
        self._filename = fname
    # end def

    def setViewNames(self, view_name_list: List[str], do_clear: bool = False):
        """Tell the model what views the document should support
        Allows non-visible views to be used.
        Intended to be called at application launch only at present.

        Args:
            view_name_list: List of view names like `slice`, `path`, or `inspector`
            do_clear:: optional, clear the names or not? defaults to ``False``
        """
        view_names = [] if do_clear else self.view_names
        for view_name in view_name_list:
            if view_name not in view_names:
                view_names.append(view_name)
        self.view_names = view_names
    # end def

    # PUBLIC METHODS FOR EDITING THE MODEL #
    def createNucleicAcidPart(  self,
                                use_undostack: bool = True,
                                grid_type: EnumType = GridEnum.NONE,
                                is_lattice: bool = True
                            ) -> NucleicAcidPart:
        """Create and store a new DnaPart and instance, and return the instance.

        Args:
            use_undostack: optional, defaults to True
            grid_type: optional default to GridEnum.NONE

        Returns
            new :obj:`NucleicAcidPart`
        """
        dna_part = NucleicAcidPart(document=self, grid_type=grid_type, is_lattice=is_lattice)
        self._addPart(dna_part, use_undostack=use_undostack)
        return dna_part
    # end def

    def getParts(self) -> Iterator[Part]:
        """Get all child :obj:`Part` in the document

        Yields:
            the next :obj:`Part` in the the Set of children
        """
        for item in self._children:
            if isinstance(item, Part):
                yield item
    # end def

    def getPartByUUID(self, uuid: str) -> Part:
        """Get the part given the uuid string

        Args:
            uuid: of the part

        Returns:
            Part

        Raises:
            KeyError: no part with that UUID
        """
        for item in self._children:
            if isinstance(item, Part) and item.uuid == uuid:
                return item
        raise KeyError("Part with uuid {} not found".format(uuid))
    # end def

    # PUBLIC SUPPORT METHODS #
    def appWindow(self) -> WindowT:
        return self._app_window
    # end def

    def setAppWindow(self, app_window: WindowT):
        """Called by :meth:`CNMainWindow.setDocument` method."""
        self._app_window = app_window
    # end def

    # PRIVATE SUPPORT METHODS #
    def _addPart(self, part: Part, use_undostack: bool = True):
        """Add part to the document via AddInstanceCommand.
        """
        c = AddInstanceCommand(self, part)
        util.doCmd(self, c, use_undostack)
    # end def

    def createMod(  self,
                    params: dict,
                    mid: str = None,
                    use_undostack: bool = True) -> Tuple[dict, str]:
        """Create a modification

        Args:
            params:
            mid: optional, modification ID string
            use_undostack: optional, default is ``True``

        Returns:
            tuple of :obj:`dict`, :obj:`str` of form::

                (dictionary of modification paramemters, modification ID string)

        Raises:
            KeyError: Duplicate mod ID
        """
        if mid is None:
            mid = uuid4().hex
        elif mid in self._mods:
            raise KeyError("createMod: Duplicate mod id: {}".format(mid))

        name = params.get('name', mid)
        color = params.get('color', '#00FF00')
        seq5p = params.get('seq5p', '')
        seq3p = params.get('seq3p', '')
        seqInt = params.get('seqInt', '')
        note = params.get('note', '')

        cmdparams = {
            'props': {'name': name,
                      'color': color,
                      'note': note,
                      'seq5p': seq5p,
                      'seq3p': seq3p,
                      'seqInt': seqInt,
                      },
            'ext_locations': set(),  # external mods, mod belongs to idx outside of strand
            'int_locations': set()   # internal mods, mod belongs between idx and idx + 1
        }

        item = {'name': name,
                'color': color,
                'note': note,
                'seq5p': seq5p,
                'seq3p': seq3p,
                'seqInt': seqInt
                }
        c = AddModCommand(self, cmdparams, mid)
        util.doCmd(self, c, use_undostack=use_undostack)
        return item, mid
    # end def

    def modifyMod(self, params: dict, mid: str, use_undostack: bool = True):
        """Modify an existing modification

        Args:
            params:
            mid: optional, modification ID string
            use_undostack: optional, default is ``True``
        """
        if mid in self._mods:
            c = ModifyModCommand(self, params, mid)
            util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def destroyMod(self, mid: str, use_undostack: bool = True):
        """Destroy an existing modification

        Args:
            mid: optional, modification ID string
            use_undostack: optional, default is ``True``
        """
        if mid in self._mods:
            c = RemoveModCommand(self, mid)
            util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def getMod(self, mid: str) -> Optional[dict]:
        """Get an existing modification

        Args:
            mid: modification ID string

        Returns:
            dict or None
        """
        return self._mods.get(mid)
    # end def

    def getModProperties(self, mid: str) -> Optional[dict]:
        """Get an existing modification properties

        Args:
            mid: modification ID string

        Returns:
            dict or None
        """
        return self._mods.get(mid)['props']
    # end def

    def getModLocationsSet(self, mid: str, is_internal: bool) -> dict:
        """Get an existing modifications locations in a ``Document``
        (``Part``, Virtual Helix ID, ``Strand``)

        Args:
            mid: modification ID string
            is_internal:

        Returns:
            dict
        """
        if is_internal:
            return self._mods[mid]['int_locations']
        else:
            return self._mods[mid]['ext_locations']
    # end def

    def addModInstance(self, mid: str, is_internal: bool, part: Part, key: str):
        """Add an instance of a modification to the Document

        Args:
            mid: modification id string
            is_internal:
            part: associated Part
            key: key of the modification at the part level
        """
        location_set = self.getModLocationsSet(mid, is_internal)
        doc_key = ''.join((part.uuid, ',', key))
        location_set.add(doc_key)
    # end def

    def removeModInstance(self, mid: str, is_internal: bool, part: Part, key: str):
        """Remove an instance of a modification from the Document

        Args:
            mid: modification id string
            is_internal:
            part: associated Part
            key: key of the modification at the part level
        """
        location_set = self.getModLocationsSet(mid, is_internal)
        doc_key = ''.join((part.uuid, ',', key))
        location_set.remove(doc_key)
    # end def

    def modifications(self) -> dict:
        """Get a copy of the dictionary of the modifications in this ``Document``

        Returns:
            dictionary of the modifications
        """
        mods = self._mods
        res = {}
        for mid in list(mods.keys()):
            mod_dict = mods[mid]
            res[mid] = {'props': mod_dict['props'].copy(),
                        'int_locations': list(mod_dict['int_locations']),
                        'ext_locations': list(mod_dict['ext_locations'])
                        }
        return res
    # end def

    def getModStrandIdx(self, key: str) -> Tuple[Part, Strand, int]:
        """Convert a key of a mod instance relative to a part
        to a part, a strand and an index

        Args:
            key: Mod key

        Returns:
            tuple of the form::

                (Part, Strand, and index)
        """
        keylist = key.split(',')
        part_uuid = keylist[0]
        id_num = int(keylist[1])
        is_fwd = int(keylist[2])    # enumeration of StrandEnum.FWD or StrandEnum.REV
        idx = int(keylist[3])
        part = self.getPartByUUID(part_uuid)
        strand = part.getStrand(is_fwd, id_num, idx)
        return part, strand, idx
    # end def

    def getModSequence(self, mid: str, mod_type: int) -> Tuple[str, str]:
        """Getter for the modification sequence give by the arguments

        Args:
            mid: mod id or ``None``
            mod_type: [ModEnum.END_5PRIME, ModEnum.END_3PRIME]

        Returns:
            tuple: of :obj:`str` of form::

                (sequence, name)
        """
        mod_dict = self._mods.get(mid)
        name = '' if mid is None else mod_dict['name']
        if mod_type == ModEnum.END_5PRIME:
            seq = '' if mid is None else mod_dict['seq5p']
        elif mod_type == ModEnum.END_3PRIME:
            seq = '' if mid is None else mod_dict['seq3p']
        else:
            seq = '' if mid is None else mod_dict['seqInt']
        return seq, name
    # end def

    def getGridType(self) -> EnumType:
        """Get the current Grid type

        Returns:
            The current Grid type
        """
        if self.activePart():
            return self.activePart().getGridType()
    # end def

    def setGridType(self, grid_type: EnumType):
        """Set the current Grid type
        """
        if self.activePart():
            self.activePart().setGridType(grid_type)
    # end def
# end class
