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
partitem.py
Created by Simon Breslav on 2011-07-21
"""

from string import *
import math
import random
import os
import sys
from views import styles
from model.enum import LatticeType
from model.enum import StrandType
from model.virtualhelix import VirtualHelix

import maya.OpenMayaUI as mui
import maya.OpenMaya as mo
import maya.cmds as cmds
import util

from controllers.mayacontrollers.mayaObjectManager import Mom
from controllers.itemcontrollers.partitemcontroller import PartItemController
from virtualhelixitem import VirtualHelixItem

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'pyqtSlot', 'QObject'])


class PartItem(object):
    """
    PartItem stores VirtualHelixItems for a given DNA Part model
    """
    def __init__(self, modelPart, parent=None):
        """
        Loads in all the Maya plugins (Nodes) needed for visualizing
        the model (XXX [SB] -this code should probably go somewhere else).
        Initiates some private variables that are constant across all
        strands (XXX [SB] -this code should also probably go somewhere else).
        Sets up PartItemController that is used to setup all the
        slots and signals between strand model and this PartItem.
        """
        self._parentItem = parent
        pluginPath = os.path.join(os.environ['CADNANO_PATH'],
                                  "views",
                                  "solidview")
        hchPath = os.path.join(pluginPath, "halfcylinderhelixnode.py")
        smiPath = os.path.join(pluginPath, "predecoratornode.py")

        if(not cmds.pluginInfo(hchPath, query=True, loaded=True)):
            cmds.loadPlugin(hchPath)

        if(not cmds.pluginInfo(smiPath, query=True, loaded=True)):
            cmds.loadPlugin(smiPath)

        if(not cmds.pluginInfo(hchPath, query=True, loaded=True)):
            print "HalfCylinderHelixNode failed to load"
            return

        #print "maya PartItem created"
        self._type = modelPart.crossSectionType()

        #self.mayaScale = 1.0
        #later updates using basecount from the VH
        # XXX [SB] - need to ask CandNano for rows and cols...
        # top left cornder of maya 3d scene X Y Z
        self.mayaOrigin = (-15 * 2.25, 16 * 2.25, 0.0)
        self.helixRadius = 1.125  # diamiter is 2.25nm
        self._virtualHelixItems = {}

        self._part = modelPart
        self._controller = PartItemController(self, modelPart)

        self.modifyState = False
    # end def

    def parentItem(self):
        """Return parent item, which is SolidRootItem in this case"""
        return self._parentItem
    # end def

    def setModifyState(self, val):
        """Change Modify state for all the strands in this PartItem"""
        self.modifyState = val
        self.updateModifyState()
    # end def

    def updateModifyState(self):
        """Update Modify state for all the strands in this PartItem"""
        for sh in self._virtualHelixItems:
            sh.setModifyState(self.modifyState)
            sh.updateDecorators()
    # end def

    def isInModifyState(self):
        """Accessor for Modify State"""
        return self.modifyState
    # end def

    def type(self):
        """Accessor for Cross Section Type, (Honeycomb vs. Square)"""
        return self._type
    # end def

    def part(self):
        """Accessor for the part model"""
        return self._part
    # end def

    def setPart(self, p):
        """set part model"""
        self._part = p
    # end def

    ### SLOTS ###
    def partDimensionsChangedSlot(self, part):
        """
        Receives notification from the model when a dimentions of the part
        changes. Needs to change an attribute of every Maya Helix Nodes, so
        that they are all are aligned corectly with new strands that are
        created.
        """
        mom = Mom()
        for vh in self._virtualHelixItems:
            for mID in vh.StrandIDs():
                cylinderName = "%s%s" % (mom.helixNodeName, mID)
                totalNumBases = self._part.maxBaseIdx()
                cmds.setAttr("%s.totalBases" % cylinderName,
                                                int(totalNumBases))
            vh.updateDecorators()
    # end def

    def partParentChangedSlot(self, sender, part):
        """partParentChangedSlot - empty"""
        pass
    # end def

    def partRemovedSlot(self, sender, part):
        """clears out private variables and disconnects signals"""
        # print "solidview.PartItem.partRemovedSlot"
        self._virtualHelixItems = None
        self._parentItem.removePartItem(self)
        self._parentItem = None
        self._part = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partPreDecoratorSelectedSlot(self, sender, row, col, baseIdx):
        """partPreDecoratorSelectedSlot - empty"""
        pass
    # end def

    def partVirtualHelixAddedSlot(self, sender, virtualHelix):
        """Receives notification when new VitualHelix is added"""
        sh = self.createNewVirtualHelixItem(virtualHelix)
        sh.setModifyState(self.modifyState)
    # end def

    @pyqtSlot(tuple)
    def partVirtualHelixRenumberedSlot(self, sender, coord):
        """partVirtualHelixRenumberedSlot - empty"""
        pass
    # end def

    @pyqtSlot(tuple)
    def partVirtualHelixResizedSlot(self, sender, coord):
        """partVirtualHelixResizedSlot - empty"""
        pass
    # end def

    @pyqtSlot(list)
    def partVirtualHelicesReorderedSlot(self, sender, orderedCoordList):
        """partVirtualHelicesReorderedSlot - empty"""
        pass
    # end def

    def updatePreXoverItemsSlot(self, sender, virtualHelix):
        """updatePreXoverItemsSlot - empty"""
        pass
    # end def

    ### METHODS ###
    def cadnanoToMayaCoords(self, row, col):
        """Converts cadnano row and col to Maya coordinates"""
        x, y = self.part().latticeCoordToPositionXY(row, col)
        return x + self.mayaOrigin[0], self.mayaOrigin[1] - y
    # end def

    def createNewVirtualHelixItem(self, virtualHelix):
        """Create a new Virtual Helix """
        coords = virtualHelix.coord()
        #print "solidview.PartItem.createNewVirtualHelixItem: %d %d" % \
        #                                                (coords[0], coords[1])
        # figure out Maya Coordinates
        x, y = self.cadnanoToMayaCoords(coords[0], coords[1])
        #print virtualHelix
        newHelix = VirtualHelixItem(self, virtualHelix, x, y)
        self._virtualHelixItems[newHelix] = True
        return newHelix
    # end def

    def removeVirtualHelixItem(self, vhelixItem):
        """Remove a new Virtual Helix """
        del self._virtualHelixItems[vhelixItem]
    # end def
# end class
