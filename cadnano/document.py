#!/usr/bin/env python
# encoding: utf-8

from operator import itemgetter
import cadnano.util as util

import cadnano.preferences as prefs

from cadnano.cnproxy import ProxyObject, ProxySignal
from cadnano.cnproxy import UndoStack, UndoCommand

from cadnano.strand import Strand
from cadnano.oligo import Oligo
from cadnano.strandset import StrandSet
from cadnano.virtualhelix import VirtualHelix
from cadnano.part import Part
from cadnano.part import HoneycombPart
from cadnano.part import SquarePart
from cadnano import app

class Document(ProxyObject):
    """
    The Document class is the root of the model. It has two main purposes:
    1. Serve as the parent all Part objects within the model.
    2. Track all sub-model actions on its undoStack.
    """


    def __init__(self, parent=None):
        super(Document, self).__init__(parent)

        self._undostack = UndoStack()
        self._parts = []
        self._assemblies = []
        self._controller = None
        self._selected_part = None
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

    def parts(self):
        """Returns a list of parts associated with the document."""
        return self._parts

    def assemblies(self):
        """Returns a list of assemblies associated with the document."""
        return self._assemblies

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def selectedPart(self):
        return self._selected_part

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
        min_low_delta = strandset.partMaxBaseIdx()
        min_high_delta = strandset.partMaxBaseIdx()  # init the return values
        ss_dict = self._selection_dict[strandset]
        # get the StrandSet index of the first item in the list
        ss_idx = strandset._findIndexOfRangeFor(selected_strand_list[0][0])[2]
        ss_list = strandset._strand_list
        len_ss_list = len(ss_list)
        max_ss_idx = len_ss_list - 1
        i = 0
        for strand, value in selected_strand_list:
            while strand != ss_list[ss_idx]:
                # incase there are gaps due to double xovers
                ss_idx += 1
            # end while
            idxL, idxH = strand.idxs()
            if value[0]:    # the end is selected
                if ss_idx > 0:
                    low_neighbor = ss_list[ss_idx - 1]
                    if low_neighbor in ss_dict:
                        valueN = ss_dict[low_neighbor]
                        # we only care if the low neighbor is not selected
                        temp = min_low_delta if valueN[1] \
                                        else idxL - low_neighbor.highIdx() - 1
                    # end if
                    else:  # not selected
                        temp = idxL - low_neighbor.highIdx() - 1
                    # end else
                else:
                    temp = idxL - 0
                # end else
                if temp < min_low_delta:
                    min_low_delta = temp
                # end if
                # check the other end of the strand
                if not value[1]:
                    temp = idxH - idxL - 1
                    if temp < min_high_delta:
                        min_high_delta = temp
            # end if
            if value[1]:
                if ss_idx < max_ss_idx:
                    high_neighbor = ss_list[ss_idx + 1]
                    if high_neighbor in ss_dict:
                        valueN = ss_dict[high_neighbor]
                        # we only care if the low neighbor is not selected
                        temp = min_high_delta if valueN[0] \
                                        else high_neighbor.lowIdx() - idxH - 1
                    # end if
                    else:  # not selected
                        temp = high_neighbor.lowIdx() - idxH - 1
                    # end else
                else:
                    temp = strandset.partMaxBaseIdx() - idxH
                # end else
                if temp < min_high_delta:
                    min_high_delta = temp
                # end if
                # check the other end of the strand
                if not value[0]:
                    temp = idxH - idxL - 1
                    if temp < min_low_delta:
                        min_low_delta = temp
            # end if
            # increment counter
            ss_idx += 1
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
        # end for Mark train bus to metro
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
                idxL, idxH = strand.idxs()
                strand5p = strand.connection5p()
                strand3p = strand.connection3p()
                # both ends are selected
                strand_dict[strand] = selected[0] and selected[1]

                # only look at 3' ends to handle xover deletion
                sel3p = selected[0] if idxL == strand.idx3Prime() else selected[1]
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
            Part.removeXover(part, strand, strand3p, useUndo)
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
                idxL, idxH = strand.idxs()
                newL, newH = strand.idxs()
                deltaL = deltaH = delta

                # process xovers to get revised delta
                if selected[0] and strand.connectionLow():
                    newL = part.xoverSnapTo(strand, idxL, delta)
                    if newL == None:
                        return
                    deltaH = newL-idxL
                if selected[1] and strand.connectionHigh():
                    newH = part.xoverSnapTo(strand, idxH, delta)
                    if newH == None:
                        return
                    deltaL = newH-idxH

                # process endpoints
                if selected[0] and not strand.connectionLow():
                    newL = idxL + deltaL
                if selected[1] and not strand.connectionHigh():
                    newH = idxH + deltaH

                if newL > newH:  # check for illegal state
                    return

                resize_list.append((strand, newL, newH))
            # end for
        # end for

        # execute the resize commands
        if use_undostack:
            self.undoStack().beginMacro("Resize Selection")

        for strand, idxL, idxH in resize_list:
            Strand.resize(strand, (idxL, idxH), use_undostack)

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
        #     print self.sortedSelectedStrands(ss)
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
        Create and store a new DNAPart and instance, and return the instance.
        """
        dnapart = None
        if len(self._parts) == 0:
            dnapart = HoneycombPart(document=self, max_row=max_row, 
                                max_col=max_col, max_steps=max_steps)
            self._addPart(dnapart)
        return dnapart

    def addSquarePart(self, max_row=prefs.SQUARE_PART_MAXROWS, 
                            max_col=prefs.SQUARE_PART_MAXCOLS, 
                            max_steps=prefs.SQUARE_PART_MAXSTEPS):
        """
        Create and store a new DNAPart and instance, and return the instance.
        """
        dnapart = None
        if len(self._parts) == 0:
            dnapart = SquarePart(document=self, max_row=max_row, 
                                max_col=max_col, max_steps=max_steps)
            self._addPart(dnapart)
        return dnapart

    def removeAllParts(self):
        """Used to reset the document. Not undoable."""
        self.documentClearSelectionsSignal.emit(self)
        for part in self._parts:
            part.remove(use_undostack=False)
    # end def

    def removePart(self, part):
        self.documentClearSelectionsSignal.emit(self)
        self._parts.remove(part)
        

    ### PUBLIC SUPPORT METHODS ###
    def controller(self):
        return self._controller

    def setController(self, controller):
        """Called by DocumentController setDocument method."""
        self._controller = controller
    # end def

    def setSelectedPart(self, newPart):
        if self._selected_part == newPart:
            return
        self._selected_part = newPart
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _addPart(self, part, use_undostack=True):
        """Add part to the document via AddPartCommand."""
        c = self.AddPartCommand(self, part)
        util.execCommandList(
                        self, [c], desc="Add part", use_undostack=use_undostack)
        return c.part()
    # end def

    ### COMMANDS ###
    class AddPartCommand(UndoCommand):
        """
        Undo ready command for deleting a part.
        """
        def __init__(self, document, part):
            super(Document.AddPartCommand, self).__init__("add part")
            self._doc = document
            self._part = part
        # end def

        def part(self):
            return self._part
        # end def

        def redo(self):
            if len(self._doc._parts) == 0:
                self._doc._parts.append(self._part)
                self._part.setDocument(self._doc)
                self._doc.setSelectedPart(self._part)
                self._doc.documentPartAddedSignal.emit(self._doc, self._part)
        # end def

        def undo(self):
            self._doc.removePart(self._part)
            self._part.setDocument(None)
            self._doc.setSelectedPart(None)
            self._part.partRemovedSignal.emit(self._part)
            # self._doc.documentPartAddedSignal.emit(self._doc, self._part)
        # end def
    # end class
# end class
