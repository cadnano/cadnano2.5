#!/usr/bin/env python
# encoding: utf-8

from operator import itemgetter
from uuid import uuid4
from cadnano import app
from cadnano import util
from cadnano.addinstancecmd import AddInstanceCommand
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.cnproxy import UndoStack
from cadnano.docmodscmd import AddModCommand, RemoveModCommand, ModifyModCommand
from cadnano.cnenum import ModType
from cadnano.objectinstance import ObjectInstance
from cadnano.part import Part
from cadnano.part.refreshsegmentscmd import RefreshSegmentsCommand
from cadnano.part.nucleicacidpart import NucleicAcidPart
from cadnano.strand import Strand
from cadnano import setBatch
from cadnano.fileio.nnodecode import decodeFile
from cadnano.fileio.nnoencode import encodeToFile

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
        self._controller = None
        self._selected_instance = None
        # the dictionary maintains what is selected
        self._selection_dict = {}
        self._active_part = None

        self._filename = None

        # the added list is what was recently selected or deselected
        self._strand_selected_changed_dict = {}
        self.view_names = []
        self.filter_set = set()
        self._mods = {}  # modifications keyed by mod id
        this_app = app()
        this_app.documentWasCreatedSignal.emit(self)
    # end def

    # SIGNALS #
    documentPartAddedSignal = ProxySignal(object, CNObject, name='documentPartAddedSignal')
    """`Document`, `Part`"""

    documentAssemblyAddedSignal = ProxySignal(object, CNObject, name='documentAssemblyAddedSignal')
    """`Document`, `Assembly`"""

    documentSelectionFilterChangedSignal = ProxySignal(object, name='documentSelectionFilterChangedSignal')
    documentPreXoverFilterChangedSignal = ProxySignal(str, name='documentPreXoverFilterChangedSignal')
    documentViewResetSignal = ProxySignal(CNObject, name='documentViewResetSignal')
    documentClearSelectionsSignal = ProxySignal(CNObject, name='documentClearSelectionsSignal')
    documentModAddedSignal = ProxySignal(object, object, object, name='documentModAddedSignal')
    documentModRemovedSignal = ProxySignal(object, object, name='documentModRemovedSignal')
    documentModChangedSignal = ProxySignal(object, object, object, name='documentModChangedSignal')

    # SLOTS #

    # ACCESSORS #
    def undoStack(self):
        """This is the actual undoStack to use for all commands. Any children
        needing to perform commands should just ask their parent for the
        undoStack, and eventually the request will get here.
        """
        return self._undostack

    def children(self):
        """Returns a list of parts associated with the document.

        Returns:
            list: list of all child objects
        """
        return self._children

    def addRefObj(self, child):
        """For adding Part and Assembly object references
        Args:
            child (object):
        """
        self._children.add(child)

    def addInstance(self, instance):
        """Add an ObjectInstance to the list of instances

        Args:
            instance (ObjectInstance):
        """
        self._instances.add(instance)

    def removeInstance(self, instance):
        """ Remove an ObjectInstance from the list of instances

        Args:
            instance (ObjectInstance):
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

    def setFilterSet(self, filter_list):
        """ Set the Document filter list.

        Emits `documentSelectionFilterChangedSignal`

        Args:
            filter_list (list): list of filter key names
        """
        vhkey = 'virtual_helix'
        fs = self.filter_set
        if vhkey in filter_list and vhkey not in fs:
            self.clearAllSelected()
        if vhkey in fs and vhkey not in filter_list:
            self.clearAllSelected()

        self.filter_set = fs = set(filter_list)
        self.documentSelectionFilterChangedSignal.emit(fs)
    # end def

    def removeRefObj(self, child):
        """ Remove child Part or Assembly

        Args:
            child (object):
        """
        self._children.remove(child)
    # end def

    def activePart(self):
        return self._active_part
    # end def

    def setActivePart(self, part):
        # print("DC setActivePart")
        self._active_part = part
    # end def

    def deactivateActivePart(self):
        # print("DC deactive Part")
        self._active_part = None
    # end def

    def fileName(self):
        return self._filename
    # end def

    def setFileName(self, fname):
        self._filename = fname
    # end def

    def writeToFile(self, filename):
        """ Convenience wrapper for `encodeToFile` to set the `document`
        argument to `self`

        Args:
            filename (str): full path file name
        """
        encodeToFile(filename, self)
    # end def

    def readFile(self, filename):
        """ Convenience wrapper for `decodeFile` to always emit_signals and
        set the `document` argument to `self`

        Args:
            filename (str): full path file name
        """
        return decodeFile(filename, document=self, emit_signals=True)
    # end def

    # def assemblies(self):
    #     """Returns a list of assemblies associated with the document."""
    #     return self._assemblies

    # PUBLIC METHODS FOR QUERYING THE MODEL #
    # def selectedInstance(self):
    #     return self._selected_instance

    def addStrandToSelection(self, strand, value):
        """ Add `Strand` object to Document selection

        Args:
            strand (Strand):
            value (tuple): of :obj:`bool` of form::

                (is low index selected, is high index selected)

        Returns:
            bool: True if successful, False otherwise
        """
        ss = strand.strandSet()
        if ss in self._selection_dict:
            self._selection_dict[ss][strand] = value
        else:
            self._selection_dict[ss] = {strand: value}
        self._strand_selected_changed_dict[strand] = value
    # end def

    def removeStrandFromSelection(self, strand):
        """Remove `Strand` object from Document selection

        Args:
            strand (Strand):

        Returns:
            bool: True if successful, False otherwise
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

    def addVirtualHelicesToSelection(self, part, id_nums):
        """If the Part isn't in the _selection_dict its not
        going to be in the changed_dict either, so go ahead and add

        Args:
            part (Part):
            id_nums (array-like):
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

    def removeVirtualHelicesFromSelection(self, part, id_nums):
        """Remove from the `Part` selection the `VirtualHelix` objects specified
        by id_nums.

        Args:
            part (Part)
            id_nums (array-like)
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

    def selectedOligos(self):
        """As long as one endpoint of a strand is in the selection, then the
        oligo is considered selected.

        Returns:
            set: or :obj:`None` if nothing is found
        """
        s_dict = self._selection_dict
        selected_oligos = set()
        for ss in s_dict.keys():
            for strand in ss:
                selected_oligos.add(strand.oligo())
            # end for
        # end for
        return selected_oligos if len(selected_oligos) > 0 else None
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

    def isModelStrandSelected(self, strand):
        ss = strand.strandSet()
        if ss in self._selection_dict:
            if strand in self._selection_dict[ss]:
                return True
            else:
                return False
        else:
            return False
    # end def

    def isVirtualHelixSelected(self, part, id_num):
        """For a given part

        Args:
            part (Part): part in question
            id_num (int): ID number of a virtual helix

        Returns:
            bool: True if id_num is selected else False
        """
        if part in self._selection_dict:
            return id_num in self._selection_dict[part]
        else:
            return False
    # end def

    def isOligoSelected(self, oligo):
        """Determine if given `Oligo` is selected

        Args:
            oligo (Oligo)

        Returns:
            bool: True if `oligo` is selected otherwise False
        """
        strand5p = oligo.strand5p()
        return self.isModelStrandSelected(strand5p)
    # end def

    def selectOligo(self, oligo):
        """Select given `Oligo`

        Args:
            oligo (Oligo):
        """
        strand5p = oligo.strand5p()
        both_ends = (True, True)
        for strand in strand5p.generator3pStrand():
            self.addStrandToSelection(strand, both_ends)
        self.updateStrandSelection()
    # end def

    def deselectOligo(self, oligo):
        """Deselect given `Oligo`

        Args:
            oligo (Oligo):
        """
        strand5p = oligo.strand5p()
        for strand in strand5p.generator3pStrand():
            self.removeStrandFromSelection(strand)
        self.updateStrandSelection()
    # end def

    def getSelectedStrandValue(self, strand):
        """ strand is an objects to look up
        it is prevetted to be in the dictionary

        Args:
            strand (Strand):
        """
        return self._selection_dict[strand.strandSet()][strand]
    # end def

    def sortedSelectedStrands(self, strandset):
        """ Get a list sorted from low to high index of `Strands` in a `StrandSet`
        that are selected

        Args:
            strandset (StrandSet):

        Returns:
            list: of :obj: `Strand`
        """
        out_list = [x for x in self._selection_dict[strandset].items()]
        getLowIdx = lambda x: Strand.lowIdx(itemgetter(0)(x))
        out_list.sort(key=getLowIdx)
        return out_list
    # end def

    def determineStrandSetBounds(self, selected_strand_list, strandset):
        """ Determine the bounds of a :class:`StrandSet` `strandset` among a
        a list of selected strands in that same `strandset`

        Args:
            selected_strand_list (list):
            strandset (StrandSet):

        Returns:
            tuple: of :obj:`int`
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

    def getSelectionBounds(self):
        """ Get the index bounds of a strand selection

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

    def deleteStrandSelection(self, use_undostack=True):
        """
        Delete selected strands. First iterates through all selected strands
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

    def resizeSelection(self, delta, use_undostack=True):
        """ Moves the selected idxs by delta by first iterating over all strands
        to calculate new idxs (method will return if snap-to behavior would
        create illegal state), then applying a resize command to each strand.

        Args:
            delta (float):
            use_undostack (bool): optional, default is True
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
        """ do it this way in the future when we have
        a better signaling architecture between views
        For now, individual objects need to emit signals

        """
        for obj, value in self._strand_selected_changed_dict.items():
            obj.strandSelectedChangedSignal.emit(obj, value)
        # end for
        self._strand_selected_changed_dict = {}
    # end def

    def resetViews(self):
        """ This is a fast way to clear selections and the views.
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

    def makeNew(self, fname=None):
        self.resetViews()
        setBatch(True)
        self.removeAllChildren()  # clear out old parts
        setBatch(False)
        self.undoStack().clear()  # reset undostack
        self.deactivateActivePart()
        self._filename = fname if fname else "untitled.json"
    # end def

    def setViewNames(self, view_name_list, do_clear=False):
        """ Tell the model what views the document should support
        Allows non-visible views to be used.
        Intended to be called at application launch only at present.

        Args:
            view_name_list (list):
            do_clear (bool): optional, clear the names or not? defaults to False
        """
        view_names = [] if do_clear else self.view_names
        for view_name in view_name_list:
            if view_name not in view_names:
                view_names.append(view_name)
        self.view_names = view_names
    # end def

    # PUBLIC METHODS FOR EDITING THE MODEL #
    def createNucleicAcidPart(self, use_undostack=True):
        """ Create and store a new DnaPart and instance, and return the instance.

        Args:
            use_undostack (bool): optional, defaults to True
        """
        dnapart = NucleicAcidPart(document=self)
        self._addPart(dnapart, use_undostack=use_undostack)
        return dnapart
    # end def


    def getParts(self):
        """Get all child `Part` in the document

        Yields:
            Part: the next Part in the the list of children
        """
        for item in self._children:
            if isinstance(item, Part):
                yield item
    # end def

    def getPartUUID(self, uuid):
        """ Get the part given the uuid string

        Args:
            uuid (str):

        Returns:
            Part or None if no matching part is found
        """
        for item in self._children:
            if isinstance(item, Part) and item.uuid == uuid:
                return item
    # end def

    # PUBLIC SUPPORT METHODS #
    def controller(self):
        return self._controller
    # end def

    def setController(self, controller):
        """Called by DocumentController setDocument method."""
        self._controller = controller
    # end def

    def setSelectedInstance(self, new_instance):
        if self._selected_instance == new_instance:
            return
        self._selected_instance = new_instance
    # end def

    # PRIVATE SUPPORT METHODS #
    def _addPart(self, part, use_undostack=True):
        """Add part to the document via AddInstanceCommand.
        """
        c = AddInstanceCommand(self, part)
        util.doCmd(self, c, use_undostack)
    # end def

    def createMod(self, params, mid=None, use_undostack=True):
        """ Create a modification

        Args:
            params (dict):
            mid (str): optional, modification ID string
            use_undostack (bool): optional, default is True

        Returns:
            tuple: of :obj:`dict`, :obj:`str` of form::

                (dictionary of modification paramemters, modification ID string)
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

    def modifyMod(self, params, mid, use_undostack=True):
        """Modify an existing modification

        Args:
            params (dict):
            mid (str): optional, modification ID string
            use_undostack (bool): optional, default is True
        """
        if mid in self._mods:
            c = ModifyModCommand(self, params, mid)
            util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def destroyMod(self, mid, use_undostack=True):
        """Destroy an existing modification

        Args:
            mid (str): optional, modification ID string
            use_undostack (bool): optional, default is True
        """
        if mid in self._mods:
            c = RemoveModCommand(self, mid)
            util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def getMod(self, mid):
        """Get an existing modification

        Args:
            mid (str): optional, modification ID string

        Returns:
            dict or None
        """
        return self._mods.get(mid)
    # end def

    def getModProperties(self, mid):
        """Get an existing modification properties

        Args:
            mid (str): optional, modification ID string

        Returns:
            dict or None
        """
        return self._mods.get(mid)['props']
    # end def

    def getModLocationsSet(self, mid, is_internal):
        """Get an existing modifications locations in a Document
        (Part, Virtual Helix ID, Strand)

        Args:
            mid (str): optional, modification ID string
            is_internal (bool):

        Returns:
            dict or None
        """
        if is_internal:
            return self._mods[mid]['int_locations']
        else:
            return self._mods[mid]['ext_locations']
    # end def

    def addModInstance(self, mid, is_internal, part, key):
        """ Add an instance of a modification to the Document

        Args:
            mid (str): modification id string
            is_internal (bool):
            part (Part): associated Part
            key (str): key of the modification at the part level
        """
        location_set = self.getModLocationsSet(mid, is_internal)
        doc_key = ''.join((part.uuid, ',', key))
        location_set.add(doc_key)
    # end def

    def removeModInstance(self, mid, is_internal, part, key):
        """Remove an instance of a modification from the Document

        Args:
            mid (str): modification id string
            is_internal (bool):
            part (Part): associated Part
            key (str): key of the modification at the part level
        """
        location_set = self.getModLocationsSet(mid, is_internal)
        doc_key = ''.join((part.uuid, ',', key))
        location_set.remove(doc_key)
    # end def

    def modifications(self):
        """ Get a copy of the dictionary of the modifications in this Document

        Returns:
            dict:
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

    def getModStrandIdx(self, key):
        """ Convert a key of a mod instance relative to a part
        to a part, a strand and an index

        Args:
            key (str): Mod key
        """
        keylist = key.split(',')
        part_uuid = keylist[0]
        id_num = int(keylist[1])
        is_fwd = int(keylist[2])    # enumeration of StrandType.FWD or StrandType.REV
        idx = int(keylist[3])
        part = self.getPartUUID(part_uuid)
        if part is None:
            raise KeyError("Part with uuid {} not found".format(part_uuid))
        strand = part.getStrand(is_fwd, id_num, idx)
        return part, strand, idx
    # end def

    def getModSequence(self, mid, mod_type):
        """Getter for the modification sequence give by the arguments

        Args:
            mid (str or None): mod id or None
            mod_type (int): [ModType.END_5PRIME, ModType.END_3PRIME]

        Returns:
            tuple: of :obj:`str` of form::

                (sequence, name)
        """
        mod_dict = self._mods.get(mid)
        name = '' if mid is None else mod_dict['name']
        if mod_type == ModType.END_5PRIME:
            seq = '' if mid is None else mod_dict['seq5p']
        elif mod_type == ModType.END_3PRIME:
            seq = '' if mid is None else mod_dict['seq3p']
        else:
            seq = '' if mid is None else mod_dict['seqInt']
        return seq, name
# end class
