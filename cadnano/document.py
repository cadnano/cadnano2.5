#!/usr/bin/env python
# encoding: utf-8

from operator import itemgetter

from cadnano import app
from cadnano import preferences as prefs
from cadnano import util
from cadnano.cnproxy import ProxyObject, ProxySignal
from cadnano.cnproxy import UndoStack, UndoCommand
from cadnano.oligo import Oligo
from cadnano.strand import Strand
from cadnano.strandset import StrandSet
from cadnano.virtualhelix import VirtualHelix
from cadnano.part import Part
from cadnano.part import HoneycombPart, SquarePart
from cadnano.part import DnaPart
from cadnano.part.origamipart import OrigamiPart
from cadnano.objectinstance import ObjectInstance
from cadnano.addinstancecmd import AddInstanceCommand


class Document(ProxyObject):
    """
    The Document class is the root of the model. It has two main purposes:
    1. Serve as the parent all Part objects within the model.
    2. Track all sub-model actions on its undoStack.
    """

    def __init__(self, parent=None):
        super(Document, self).__init__(parent)

        self._undostack = UndoStack()
        self._children = []
        self._controller = None
        self._selected_instance = None
        # the dictionary maintains what is selected
        self._selection_dict = {}
        # the added list is what was recently selected or deselected
        self._selected_changed_dict = {}
        app().documentWasCreatedSignal.emit(self)
    # end def

    ### SIGNALS ###
    documentPartAddedSignal =  ProxySignal(object,
                                        ProxyObject,
                                        name='documentPartAddedSignal') # doc, part
    documentAssemblyAddedSignal =  ProxySignal(object,
                                        ProxyObject,
                                        name='documentAssemblyAddedSignal') # doc, assembly

    # dict of tuples of objects using the reference as the key,
    # and the value is a tuple with meta data
    # in the case of strands the metadata would be which endpoints of selected
    # e.g. { objectRef: (value0, value1),  ...}
    documentSelectedChangedSignal = ProxySignal(dict,
                                         name='documentSelectedChangedSignal') # tuples of items + data
    documentSelectionFilterChangedSignal = ProxySignal(list,
                                  name='documentSelectionFilterChangedSignal')
    documentViewResetSignal = ProxySignal(ProxyObject,
                                               name='documentViewResetSignal')
    documentClearSelectionsSignal = ProxySignal(ProxyObject,
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

    def removeAllChildren(self):
        """Used to reset the document. Not undoable."""
        self.documentClearSelectionsSignal.emit(self)
        for child in self._children:
            child.remove(use_undostack=False)
    # end def

    def removeChild(self, child):
        self.documentClearSelectionsSignal.emit(self)
        self._children.remove(child)
    # end def

    # def assemblies(self):
    #     """Returns a list of assemblies associated with the document."""
    #     return self._assemblies

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def selectedInstance(self):
        return self._selected_instance

    def addToSelection(self, obj, value):
        self._selection_dict[obj] = value
        self._selected_changed_dict[obj] = value
    # end def

    def removeFromSelection(self, obj):
        if obj in self._selection_dict:
            del self._selection_dict[obj]
            self._selected_changed_dict[obj] = (False, False)
            return True
        else:
            return False
    # end def

    def clearSelections(self):
        """
        Only clear the dictionary
        """
        self._selection_dict = {}
    # end def

    def addStrandToSelection(self, strand, value):
        ss = strand.strandSet()
        if ss in self._selection_dict:
            self._selection_dict[ss][strand] = value
        else:
            self._selection_dict[ss] = {strand: value}
        self._selected_changed_dict[strand] = value
    # end def

    def removeStrandFromSelection(self, strand):
        ss = strand.strandSet()
        if ss in self._selection_dict:
            temp = self._selection_dict[ss]
            if strand in temp:
                del temp[strand]
                if len(temp) == 0:
                    del self._selection_dict[ss]
                self._selected_changed_dict[strand] = (False, False)
                return True
            else:
                return False
        else:
            return False
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
        self._selected_changed_dict = {}
        self.documentClearSelectionsSignal.emit(self)
    # end def

    def isModelSelected(self, obj):
        return obj in self._selection_dict
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
        # outList = self._selection_dict[strandset].keys()
        # outList.sort(key=Strand.lowIdx)
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

    # def operateOnStrandSelection(self, method, arg, both=False):
    #     pass
    # # end def

    def deleteSelection(self, use_undostack=True):
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
                part = strand.virtualHelix().part()
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
            OrigamiPart.removeXover(part, strand, strand3p, useUndo)
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

    def paintSelection(self, scafColor, stapColor, use_undostack=True):
        """Delete xovers if present. Otherwise delete everything."""
        scaf_oligos = {}
        stap_oligos = {}
        for strandset_dict in self._selection_dict.values():
            for strand, value in strandset_dict.items():
                if strand.isScaffold():
                    scaf_oligos[strand.oligo()] = True
                else:
                    stap_oligos[strand.oligo()] = True

        if use_undostack:
            self.undoStack().beginMacro("Paint strands")
        for olg in scaf_oligos.keys():
            olg.applyColor(scafColor)
        for olg in stap_oligos.keys():
            olg.applyColor(stapColor)
        if use_undostack:
            self.undoStack().endMacro()

    def resizeSelection(self, delta, use_undostack=True):
        """
        Moves the selected idxs by delta by first iterating over all strands
        to calculate new idxs (method will return if snap-to behavior would
        create illegal state), then applying a resize command to each strand.
        """
        resize_list = []

        # calculate new idxs
        for strandset_dict in self._selection_dict.values():
            for strand, selected in strandset_dict.items():
                part = strand.virtualHelix().part()
                idx_low, idx_high = strand.idxs()
                new_low, new_high = strand.idxs()
                delta_low = delta_high = delta

                # process xovers to get revised delta
                if selected[0] and strand.connectionLow():
                    new_low = part.xoverSnapTo(strand, idx_low, delta)
                    if new_low is None:
                        return
                    delta_high = new_low-idx_low
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

    def updateSelection(self):
        """
        do it this way in the future when we have
        a better signaling architecture between views
        """
        # self.documentSelectedChangedSignal.emit(self._selected_changed_dict)
        """
        For now, individual objects need to emit signals
        """
        for obj, value in self._selected_changed_dict.items():
            obj.selectedChangedSignal.emit(obj, value)
        # end for
        self._selected_changed_dict = {}
        # for ss in self._selection_dict:
        #     print(self.sortedSelectedStrands(ss))
    # end def

    def resetViews(self):
        # This is a fast way to clear selections and the views.
        # We could manually deselect each item from the Dict, but we'll just
        # let them be garbage collect
        # the dictionary maintains what is selected
        self._selection_dict = {}
        # the added list is what was recently selected or deselected
        self._selected_changed_dict = {}
        self.documentViewResetSignal.emit(self)
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def addHoneycombPart(self,  max_row=prefs.HONEYCOMB_PART_MAXROWS,
                                max_col=prefs.HONEYCOMB_PART_MAXCOLS,
                                max_steps=prefs.HONEYCOMB_PART_MAXSTEPS):
        """
        Create and store a new origamipart and instance, and return the instance.
        """
        origamipart = None
        origamipart = HoneycombPart(document=self, max_row=max_row,
                            max_col=max_col, max_steps=max_steps)
        self._addPart(ObjectInstance(origamipart))
        return origamipart
    # end def

    def addSquarePart(self, max_row=prefs.SQUARE_PART_MAXROWS,
                            max_col=prefs.SQUARE_PART_MAXCOLS,
                            max_steps=prefs.SQUARE_PART_MAXSTEPS):
        """
        Create and store a new origamipart and instance, and return the instance.
        """
        origamipart = None
        if len(self._children) == 0:
            origamipart = SquarePart(document=self, max_row=max_row,
                                max_col=max_col, max_steps=max_steps)
            self._addPart(ObjectInstance(origamipart))
        return origamipart
    # end def

    def addHpxPart(self, max_row=prefs.HONEYCOMB_PART_MAXROWS,
                         max_col=prefs.HONEYCOMB_PART_MAXCOLS,
                         max_steps=prefs.HONEYCOMB_PART_MAXSTEPS):
        """
        Create and store a new origamipart and instance, and return the instance.
        """
        origamipart = HpxPart(document=self, max_row=max_row,
                              max_col=max_col, max_steps=max_steps)
        self._addPart(ObjectInstance(origamipart))
        return origamipart
    # end def

    def addSpxPart(self, max_row=prefs.SQUARE_PART_MAXROWS,
                         max_col=prefs.SQUARE_PART_MAXCOLS,
                         max_steps=prefs.SQUARE_PART_MAXSTEPS):
        """
        Create and store a new origamipart and instance, and return the instance.
        """
        origamipart = SpxPart(document=self, max_row=max_row,
                              max_col=max_col, max_steps=max_steps)
        self._addPart(ObjectInstance(origamipart))

    def removeAllParts(self):
        """Used to reset the document. Not undoable.
        DEPRECATED, use removeAllChildren
        """
        self.documentClearSelectionsSignal.emit(self)
        for item in self._children:
            if isinstance(item, Part):
                part.remove(use_undostack=False)
    # end def

    def addDnaPart(self):
        """Create and store a new dnapart and instance, and return the instance."""
        dnapart = DnaPart(document=self)
        self._addPart(ObjectInstance(dnapart))
        return dnapart
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
# end class
