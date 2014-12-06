# Copyright 2011 Autodesk, Inc.  All rights reserved.
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

"""
solidrootitem.py
Created by Simon Breslav on 2011-10-05.
"""

from controllers.viewrootcontroller import ViewRootController
from origamipartitem import OrigamiPartItem
import maya.cmds as cmds

import util
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QGraphicsRectItem'])


class SolidRootItem(object):
    """
    SolidRootItem is the root item in the SolidView, it does not have a
    visual representation in the 3D view
    """
    def __init__(self, parent, document, modState):
        self._document = document
        self._controller = ViewRootController(self, document)
        self._modelPart = None
        self._partItems = {}
        self._modifyState = modState
        self._selectionFilterDict = {}
        self.oldSelectionStrandList = []
        self._selectedDict = {}

    ### SLOTS ###
    def partAddedSlot(self, sender, modelPart):
        """
        Receives notification from the model that a part has been added.
        """
        #print "SolidRootItem.partAddedSlot!"
        self._modelPart = modelPart
        partItem = OrigamiPartItem(modelPart, self)
        self._partItems[partItem] = True
        self.setModifyState(self._modifyState)

    def selectedChangedSlot(self, itemDict):
        """docstring for selectedChangedSlot"""
        pass
    # end def

    def selectionFilterChangedSlot(self, filterNameList):
        self.clearSelectionFilterDict()
        for filterName in filterNameList:
            self.addToSelectionFilterDict(filterName)
    # end def

    def resetRootItemSlot(self, doc):
        pass
    # end def

    def clearSelectionsSlot(self, doc):
        cmds.select(clear=True)
        for strand in self._selectedDict.keys():
            self.removeFromSelectionDict(strand)
    # end def
    ### METHODS ###

    def document(self):
        return self._document
    # end def

    def selectedChanged(self, strandList, value):
        """is called from Mom when selection changed in 3D"""
        # print "selected changed 3D", strandList, self._selectedDict
        if len(strandList) == 0 and len(self._selectedDict) == 0:
            return
        for strand in self._selectedDict.keys():
            self.removeFromSelectionDict(strand)
            temp = self._document.removeStrandFromSelection(strand)
            # print temp, "cupcake"
        self._document.updateSelection()
        for strand in strandList:
            self.addToSelectionDict(strand)
            self._document.addStrandToSelection(strand, value)

        self._document.updateSelection()
        # self.oldSelectionStrandList = strandList
        # pass
    # end def

    def addToSelectionDict(self, item):
        self._selectedDict[item] = True
    # end def

    def removeFromSelectionDict(self, item):
        if item in self._selectedDict:
            del self._selectedDict[item]
    # end def

    def partItems(self):
        """Return a list of partItems associated with this RootItem"""
        return self._partItems
    # end def

    def removeOrigamiPartItem(self, partItem):
        """Remove a given partItem"""
        del self._partItems[partItem]
    # end def

    def setModifyState(self, val):
        """Notifies all the associated partItems of the Modify State Change"""
        self._modifyState = val
        for p in self._partItems:
            p.setModifyState(val)
    # end def

    def clearSelectionFilterDict(self):
        self._selectionFilterDict = {}
    # end def

    def selectionFilterDict(self):
        return self._selectionFilterDict
    # end def

    def addToSelectionFilterDict(self, filterName):
        self._selectionFilterDict[filterName] = True
    # end def

    def removeFromSelectionFilterDict(self, filterName):
        del self._selectionFilterDict[filterName]
    # end def
# end class
