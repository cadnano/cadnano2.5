#!/usr/bin/env python
# encoding: utf-8

from operator import itemgetter

from cadnano import app
from cadnano import preferences as prefs
from cadnano import util
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.cnproxy import UndoStack, UndoCommand

from cadnano.strand import Strand

from cadnano.part import Part
from cadnano.part.nucleicacidpart import NucleicAcidPart
from cadnano.objectinstance import ObjectInstance
from cadnano.addinstancecmd import AddInstanceCommand
from cadnano.part.pmodscmd import AddModCommand, RemoveModCommand, ModifyModCommand

class Document(CNObject):
    """
    The Document class is the root of the model. It has two main purposes:
    1. Serve as the parent all Part objects within the model.
    2. Track all sub-model actions on its undoStack.
    """
    __slots__ = ('_undostack', '_children',
                '_instances', '_controller', '_selected_instance'
                '_selection_dict', '_strand_selected_changed_dict',
                'view_names', 'filter_set')
    def __init__(self, parent=None):
        super(Document, self).__init__(parent)

        self._undostack = UndoStack()
        self._children = []     # for storing a reference to Parts (and Assemblies)
        self._instances = []    # for storing instances of Parts (and Assemblies)
        self._controller = None
        self._selected_instance = None
        # the dictionary maintains what is selected
        self._selection_dict = {}
        # the added list is what was recently selected or deselected
        self._strand_selected_changed_dict = {}
        self.view_names = []
        self.filter_set = set()
        self._mods = {} # modifications keyed by mod id
        app().documentWasCreatedSignal.emit(self)
    # end def

    ### SIGNALS ###
    documentPartAddedSignal =  ProxySignal(object,
                                        CNObject,
                                        name='documentPartAddedSignal') # doc, part
    documentAssemblyAddedSignal =  ProxySignal(object,
                                        CNObject,
                                        name='documentAssemblyAddedSignal') # doc, assembly

    # dict of tuples of objects using the reference as the key,
    # and the value is a tuple with meta data
    # in the case of strands the metadata would be which endpoints of selected
    # e.g. { objectRef: (value0, value1),  ...}
    documentSelectedChangedSignal = ProxySignal(dict,
                                         name='documentSelectedChangedSignal') # tuples of items + data
    documentSelectionFilterChangedSignal = ProxySignal(object,
                                  name='documentSelectionFilterChangedSignal')
    documentPreXoverFilterChangedSignal = ProxySignal(str,
                                   name='documentPreXoverFilterChangedSignal')

    documentViewResetSignal = ProxySignal(CNObject,
                                               name='documentViewResetSignal')
    documentClearSelectionsSignal = ProxySignal(CNObject,
                                         name='documentClearSelectionsSignal')
    ### SLOTS ###

    ### ACCESSORS ###
    def undoStack(self):
        """
        This is the actual undoStack to use for all commands. Any children
        needing to perform commands should just ask their parent for the
        undoStack, and eventually the request will get here.
        """
        return self._undostack

    def children(self):
        """Returns a list of parts associated with the document."""
        return self._children

    def addChild(self, child):
        self._children.append(child)

    def addInstance(self, instance):
        self._instances.append(instance)

    def removeInstance(self, instance):
        self._instances.remove(instance)
        self.documentClearSelectionsSignal.emit(self)

    def removeAllChildren(self):
        """Used to reset the document. Not undoable."""
        self.documentClearSelectionsSignal.emit(self)
        for child in self._children:
            child.remove(use_undostack=False)
    # end def

    def setFilterSet(self, filter_list):
        vhkey = 'virtual_helix'
        fs = self.filter_set
        if vhkey in filter_list and vhkey not in fs:
            self.clearAllSelected()
        if vhkey in fs and vhkey not in filter_list:
            self.clearAllSelected()

        self.filter_set = fs = set(filter_list)
        print("setting fs", fs)
        self.documentSelectionFilterChangedSignal.emit(fs)
    # end def

    def removeChild(self, child):
        self._children.remove(child)
    # end def

    # def assemblies(self):
    #     """Returns a list of assemblies associated with the document."""
    #     return self._assemblies

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    # def selectedInstance(self):
    #     return self._selected_instance

    def addStrandToSelection(self, strand, value):
        ss = strand.strandSet()
        if ss in self._selection_dict:
            self._selection_dict[ss][strand] = value
        else:
            self._selection_dict[ss] = {strand: value}
        self._strand_selected_changed_dict[strand] = value
    # end def

    def removeStrandFromSelection(self, strand):
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
        """ If the Part isn't in the _selection_dict its not
        going to be in the changed_dict either, so go ahead and add

        """
        selection_dict = self._selection_dict
        if part not in selection_dict:
            # print("creating new set", id(part))
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

    def selectionDict(self):
        return self._selection_dict
    # end def

    def selectedOligos(self):
        """
        as long as one endpoint of a strand is in the selection, then the oligo
        is considered selected
        """
        s_dict = self._selection_dict
        selected_oligos = set()
        for ss in s_dict.keys():
            for strand in ss:
                 selected_oligos.add(strand.oligo())
            # end for
        # end for
        return selected_oligos if len(selected_oligos) > 0 else None
    #end def

    def clearAllSelected(self):
        self._selection_dict = {}
        # the added list is what was recently selected or deselected
        self._strand_selected_changed_dict = {}
        self.documentClearSelectionsSignal.emit(self)
    # end def

    # def isModelSelected(self, obj):
    #     return obj in self._selection_dict
    # # end def

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
        if part in self._selection_dict:
            return id_num in self._selection_dict[part]
        else:
            return False
    # end def

    def isOligoSelected(self, oligo):
        strand5p = oligo.strand5p()
        return self.isModelStrandSelected(strand5p)
    # end def

    def selectOligo(self, oligo):
        strand5p = oligo.strand5p()
        both_ends = (True, True)
        for strand in strand5p.generator3pStrand():
            self.addStrandToSelection(strand, both_ends)
        self.updateStrandSelection()
    # end def

    def deselectOligo(self, oligo):
        strand5p = oligo.strand5p()
        for strand in strand5p.generator3pStrand():
            self.removeStrandFromSelection(strand)
        self.updateStrandSelection()
    # end def

    def getSelectedValue(self, obj):
        """
        obj is an objects to look up
        it is prevetted to be in the dictionary
        """
        return self._selection_dict[obj]

    def getSelectedStrandValue(self, strand):
        """
        strand is an objects to look up
        it is prevetted to be in the dictionary
        """
        return self._selection_dict[strand.strandSet()][strand]
    # end def

    def sortedSelectedStrands(self, strandset):
        out_list = [x for x in self._selection_dict[strandset].items()]
        getLowIdx = lambda x: Strand.lowIdx(itemgetter(0)(x))
        out_list.sort(key=getLowIdx)
        return out_list
    # end def

    def determineStrandSetBounds(self, selected_strand_list, strandset):
        length = strandset.length()
        min_high_delta = min_low_delta = max_ss_idx = length - 1 # init the return values
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
                        temp = min_low_delta if value_N[1] \
                                        else idx_low - low_neighbor.highIdx() - 1
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
                        temp = min_high_delta if value_N[0] \
                                        else high_neighbor.lowIdx() - idx_high - 1
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
        min_low_delta = -1
        min_high_delta = -1
        for strandset in self._selection_dict.keys():
            selected_list = self.sortedSelectedStrands(strandset)
            temp_low, temp_high = self.determineStrandSetBounds(
                                                    selected_list, strandset)
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
            if xoList: # end xover macro if it was started
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

    # def paintSelection(self, scafColor, stapColor, use_undostack=True):
    #     """Delete xovers if present. Otherwise delete everything."""
    #     scaf_oligos = {}
    #     stap_oligos = {}
    #     for strandset_dict in self._selection_dict.values():
    #         for strand, value in strandset_dict.items():
    #             if strand.isScaffold():
    #                 scaf_oligos[strand.oligo()] = True
    #             else:
    #                 stap_oligos[strand.oligo()] = True

    #     if use_undostack:
    #         self.undoStack().beginMacro("Paint strands")
    #     for olg in scaf_oligos.keys():
    #         olg.applyColor(scafColor)
    #     for olg in stap_oligos.keys():
    #         olg.applyColor(stapColor)
    #     if use_undostack:
    #         self.undoStack().endMacro()

    def resizeSelection(self, delta, do_maximize=False, use_undostack=True):
        """
        Moves the selected idxs by delta by first iterating over all strands
        to calculate new idxs (method will return if snap-to behavior would
        create illegal state), then applying a resize command to each strand.
        """
        resize_list = []
        if do_maximize:
            print("this could be maximized")
        # calculate new idxs
        for strandset_dict in self._selection_dict.values():
            for strand, selected in strandset_dict.items():
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

                resize_list.append((strand, new_low, new_high))
            # end for
        # end for

        # execute the resize commands
        if use_undostack:
            self.undoStack().beginMacro("Resize Selection")

        for strand, idx_low, idx_high in resize_list:
            Strand.resize(strand, (idx_low, idx_high), use_undostack)

        if use_undostack:
            self.undoStack().endMacro()
    # end def

    def updateStrandSelection(self):
        """
        do it this way in the future when we have
        a better signaling architecture between views
        """
        # self.documentSelectedChangedSignal.emit(self._strand_selected_changed_dict)
        """
        For now, individual objects need to emit signals
        """
        for obj, value in self._strand_selected_changed_dict.items():
            obj.strandSelectedChangedSignal.emit(obj, value)
        # end for
        self._strand_selected_changed_dict = {}
    # end def

    def resetViews(self):
        """
        This is a fast way to clear selections and the views.
        We could manually deselect each item from the Dict, but we'll just
        let them be garbage collect
        the dictionary maintains what is selected
        """
        print("reset views")
        self._selection_dict = {}
        # the added list is what was recently selected or deselected
        self._strand_selected_changed_dict = {}
        self.documentViewResetSignal.emit(self)
    # end def

    def setViewNames(self, view_name_list, do_clear=False):
        """ tell the model what views the document should support
        Allows non-visible views to be used.
        Intended to be called at application launch only at
        present
        """
        view_names = [] if do_clear else self.view_names
        for view_name in view_name_list:
            if not view_name in view_names:
                view_names.append(view_name)
        self.view_names = view_names
    # end def

    # def newViewProperties(self):
    #     """ get a dictionary prepopulated with a view dictionary
    #     for use with view specific parameters
    #     """
    #     return {key:{} for key in self.view_names}
    # # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def addDnaPart(self):
        """
        Create and store a new DnaPart and instance, and return the instance.
        """
        dnapart = NucleicAcidPart(document=self)
        self._addPart(ObjectInstance(dnapart))
        return dnapart
    # end def

    def removeAllParts(self):
        """Used to reset the document. Not undoable.
        DEPRECATED, use removeAllChildren
        """
        self.documentClearSelectionsSignal.emit(self)
        for item in self._children:
            if isinstance(item, Part):
                part.remove(use_undostack=False)
    # end def

    def getParts(self):
        for item in self._children:
            if isinstance(item, Part):
                yield item
    # end def

    ### PUBLIC SUPPORT METHODS ###
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

    ### PRIVATE SUPPORT METHODS ###
    def _addPart(self, part_instance, use_undostack=True):
        """Add part to the document via AddInstanceCommand."""
        c = AddInstanceCommand(self, part_instance)
        util.execCommandList(
                        self, [c], desc="Add part", use_undostack=use_undostack)
        return c.instance()
    # end def

    def createMod(self, params, mid=None, use_undostack=True):
        if mid is None:
            mid =  str(uuid4())
        elif mid in self._mods:
            raise KeyError("createMod: Duplicate mod id: {}".format(mid))

        name = params.get('name', mid)
        color = params.get('color', '#00FF00')
        seq5p = params.get('seq5p', '')
        seq3p = params.get('seq3p', '')
        seqInt = params.get('seqInt', '')
        note = params.get('note', '')

        cmdparams = {
            'name': name,
            'color': color,
            'note': note,
            'seq5p': seq5p,
            'seq3p': seq3p,
            'seqInt': seqInt,
            'ext_locations': set(), # external mods, mod belongs to idx outside of strand
            'int_locations': set()  # internal mods, mod belongs between idx and idx + 1
        }

        item = { 'name': name,
            'color': color,
            'note': note,
            'seq5p': seq5p,
            'seq3p': seq3p,
            'seqInt': seqInt
        }
        cmds = []
        c = AddModCommand(self, cmdparams, mid)
        cmds.append(c)
        util.execCommandList(self, cmds, desc="Create Mod", \
                                                use_undostack=use_undostack)
        return item, mid
    # end def

    def modifyMod(self, params, mid, use_undostack=True):
        if mid in self._mods:
            cmds = []
            c = ModifyModCommand(self, params, mid)
            cmds.append(c)
            util.execCommandList(self, cmds, desc="Modify Mod", \
                                                use_undostack=use_undostack)
    # end def

    def destroyMod(self, mid):
        if mid in self._mods:
            cmds = []
            c = RemoveModCommand(self, mid)
            cmds.append(c)
            util.execCommandList(self, cmds, desc="Remove Mod", \
                                                use_undostack=use_undostack)
    # end def

    def getMod(self, mid):
        return self._mods.get(mid)
    # end def

    def getModLocationsSet(self, mid, is_internal):
        if is_internal:
            return self._mods[mid]['int_locations']
        else:
            return self._mods[mid]['ext_locations']
    # end def

    def mods(self, get_instances=False):
        """
        """
        mods = self._mods
        res = {}
        for mid in list(mods.keys()):
            if mid != 'int_instances' and mid != 'ext_instances':
                res[mid] = mods[mid].copy()
                if get_instances:
                    res[mid]['int_locations'] = list(res[mid]['int_locations'])
                    res[mid]['ext_locations'] = list(res[mid]['ext_locations'])
                else:
                    del res[mid]['int_locations']
                    del res[mid]['ext_locations']
        return res
    #end def
# end class
