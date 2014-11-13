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
virtualhelixitem.py
Created by Simon Breslav on 2011-08-29.
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
#from model.strands.normalstrand import NormalStrand
#from model.strands.xoverstrand import XoverStrand3, XoverStrand5

from controllers.mayacontrollers.mayaObjectManager import Mom
from controllers.itemcontrollers.virtualhelixitemcontroller \
                                            import VirtualHelixItemController

import maya.OpenMayaUI as mui
import maya.OpenMaya as mo
import maya.cmds as cmds
import util

from .stranditem import StrandItem

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'pyqtSlot', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QColor'])


class VirtualHelixItem(object):
    """
    VirtualHelixItem is the container for StrandItems for is the Maya 3D View,
    it does not get visualized in any way right now.
    """
    baseWidth = styles.PATH_BASE_WIDTH

    def __init__(self, partItem, modelVirtualHelix, x, y):
        """
        Initialize member variables.
        Setup VirtualHelixItemController, that takes care of all the
        slots and signals between VirtualHelix model and this VirtualHelixItem.
        """
        self._partItem = partItem
        self._modelVirtualHelix = modelVirtualHelix
        self._x = x
        self._y = y
        coords = modelVirtualHelix.coord()
        self._row = coords[0]
        self._col = coords[1]
        self.strandIDs = []
        self._modState = False
        self._strandItems = {}
        self.stapleIndicatorCount = 0
        self.stapleModIndicatorIDs = []

        self._controller = VirtualHelixItemController(self, modelVirtualHelix)
    # end def

    def partItem(self):
        """PartItem Accessor - parent Item"""
        return self._partItem

    def virtualHelix(self):
        """VirtualHelix Model Accessor"""
        return self._modelVirtualHelix

    def number(self):
        """VirtualHelix Model Index Number Accessor"""
        return self._modelVirtualHelix.number()

    def row(self):
        """Row Accessor"""
        return self.coord()[0]

    def col(self):
        """Col Accessor"""
        return self.coord()[1]

    def x(self):
        """Actual x position in the the Maya 3D View"""
        return self._x
    # end def

    def y(self):
        """Actual y position in the the Maya 3D View"""
        return self._y
    # end def

    def coord(self):
        """Returns a tuple (row, column) of the VitualHelix model"""
        return self._modelVirtualHelix.coord()
    # end def

    def isEvenParity(self):
        """Returns parity of the VitualHelix model"""
        return self._modelVirtualHelix.isEvenParity()

    def StrandIDs(self):
        """
        Returns a list of Strand IDs within this VH, the IDs are suffixes
        of Maya Nodes, and are used to for Maya<->Cadnano communication
        in mayaObjectManager
        """
        return self.strandIDs

    def setModifyState(self, val):
        """Update Modify state for this VirtualHelixItem"""
        self._modState = val

    ### SLOTS ###
    def strandAddedSlot(self, sender, strand):
        """
        Instantiates a StrandItem upon notification that the model has a
        new Strand.  The StrandItem is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').
        """
        #print "solidview.VirtualHelixItem.strandAddedSlot"
        m = Mom()
        mID = m.strandMayaID(strand)
        self.strandIDs.append(mID)
        sI = StrandItem(mID, strand, self)
        self._strandItems[sI] = True
        self.updateDecorators()
        #print "solidview.VirtualHelixItem.strandAddedSlot done %s" % mID
    # end def

    @pyqtSlot(object)
    def decoratorAddedSlot(self, decorator):
        """decoratorAddedSlot - empty"""
        pass

    @pyqtSlot(object)
    def virtualHelixNumberChangedSlot(self, virtualHelix):
        """virtualHelixNumberChangedSlot - empty"""
        pass
    # end def

    @pyqtSlot(object)
    def virtualHelixRemovedSlot(self, virtualHelix):
        """
        Clears out private variables and disconnects signals
        """
        #print "solidview.VirtualHelixItem.virtualHelixRemovedSlot"
        self._partItem.removeVirtualHelixItem(self)
        self._partItem = None
        self._modelVirtualHelix = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def updateDecorators(self):
        """
        Clears out Pre-Decorators, and re-populates them if they should be
        visible
        """
        self.clearDecorators()
        if self._modState:
            m = Mom()
            for mID in self.strandIDs:
                mayaNodeInfo = "%s%s" % (m.helixMeshName, mID)
                #print "mayaNodeInfo: %s" % mayaNodeInfo
                strand = m.mayaToCn[mayaNodeInfo]
                if(strand.strandSet().isStaple()):
                    self.createDecorators(strand)

    def cadnanoVBaseToMayaCoords(self, base, strand):
        """
        Given a Strand and a Base, returns a 3D location of that base
        """
        m = Mom()
        mID = m.strandMayaID(strand)
        cylinderName = "%s%s" % (m.helixNodeName, mID)
        if cmds.objExists(cylinderName):
            rise = cmds.getAttr("%s.rise" % cylinderName)
            startBase = cmds.getAttr("%s.startBase" % cylinderName)
            startPos = cmds.getAttr("%s.startPos" % cylinderName)
            base0Pos = startPos[0][1] + (startBase * rise)
            ourPos = base0Pos - (base * rise)
            zComp = ourPos

            rotation = cmds.getAttr("%s.rotation" % cylinderName)
            radius = cmds.getAttr("%s.radius" % cylinderName)
            parity = cmds.getAttr("%s.parity" % cylinderName)
            strandType = cmds.getAttr("%s.strandType" % cylinderName)
            rotationOffset = cmds.getAttr("%s.rotationOffset" % cylinderName)
            decoratorRotOffset = cmds.getAttr("%s.decoratorRotOffset"
                                              % cylinderName)
            # not clear why decoratorRotOffset is not in radians but
            # rotationOffset is
            decoratorRotOffset = decoratorRotOffset * math.pi / 180
            starting_rotation = (math.pi * (not parity)) + rotationOffset + \
                                decoratorRotOffset + \
                                (math.pi * strandType)
            fullrotation = -rotation * base * math.pi / 180
            #print full rotation
            xComp = self._x + radius * \
                    math.cos(starting_rotation + fullrotation)
            yComp = self._y + radius * \
                    math.sin(starting_rotation + fullrotation)
            #print "%f %f %f" % (xComp, yComp, zComp)
            return (xComp, yComp, zComp)
        else:
            raise IndexError

    def clearDecorators(self):
        """Remove all the Pre-Decortators"""
        m = Mom()
        for mID in self.stapleModIndicatorIDs:
            transformName = "%s%s" % (m.decoratorTransformName, mID)
            #print "delete %s" % transformName
            m = Mom()
            m.removeDecoratorMapping(mID)
            if cmds.objExists(transformName):
                cmds.delete(transformName)
        self.stapleModIndicatorIDs = []
        self.stapleIndicatorCount = 0

    def createDecorators(self, strand):
        """Create a set of new Pre-Decortators for a given strand"""
        m = Mom()
        strandId = m.strandMayaID(strand)
        totalNumBases = self._modelVirtualHelix.part().maxBaseIdx()
        preDecoratorIdxList = strand.getPreDecoratorIdxList()

        for baseIdx in preDecoratorIdxList:
            # XXX [SB+AT] NOT THREAD SAFE
            while cmds.objExists("%s%s_%s" % (m.decoratorNodeName,
                                              strandId,
                                              self.stapleIndicatorCount)):
                self.stapleIndicatorCount += 1
            stapleId = "%s_%s" % (strandId, self.stapleIndicatorCount)
            coords = self.cadnanoVBaseToMayaCoords(baseIdx, strand)
            stapleModNodeInfo = self.createDecoratorNodes(coords, stapleId)
            self.stapleModIndicatorIDs.append(stapleId)
            m = Mom()
            m.decoratorToVirtualHelixItem[stapleModNodeInfo[2]] = (self,
                                                                   baseIdx,
                                                                   strand)
            m.decoratorToVirtualHelixItem[stapleModNodeInfo[1]] = (self,
                                                                   baseIdx,
                                                                   strand)

    def createDecoratorNodes(self, coords, mID):
        """Create a actual Maya Nodes for a new Pre-Decortators"""
        m = Mom()
        stapleModIndicatorName = "%s%s" % (m.decoratorNodeName, mID)
        transformName = "%s%s" % (m.decoratorTransformName, mID)
        meshName = "%s%s" % (m.decoratorMeshName, mID)
        shaderName = "%s" % m.decoratorShaderName

        cmds.createNode("transform", name=transformName, skipSelect=True)
        cmds.setAttr("%s.rotateX" % transformName, 90)
        cmds.setAttr("%s.translateX" % transformName, coords[0])
        cmds.setAttr("%s.translateY" % transformName, coords[1])
        cmds.setAttr("%s.translateZ" % transformName, coords[2])
        cmds.createNode("mesh",
                        name=meshName,
                        parent=transformName,
                        skipSelect=True)
        #cmds.createNode("spPreDecoratorNode", name=stapleModIndicatorName)
        cmds.createNode("polySphere",
                        name=stapleModIndicatorName,
                        skipSelect=True)
        cmds.setAttr("%s.radius" % stapleModIndicatorName, .25)
        cmds.setAttr("%s.subdivisionsAxis" % stapleModIndicatorName, 4)
        cmds.setAttr("%s.subdivisionsHeight" % stapleModIndicatorName, 4)

        #cmds.connectAttr("%s.outputMesh" % stapleModIndicatorName,
        #                 "%s.inMesh" % meshName)
        cmds.connectAttr("%s.output" % stapleModIndicatorName,
                         "%s.inMesh" % meshName)

        if not cmds.objExists(shaderName):
            # Shader does not exist create one
            cmds.shadingNode('lambert', asShader=True, name=shaderName)
            cmds.sets(n="%sSG" % shaderName, r=True, nss=True, em=True)
            cmds.connectAttr("%s.outColor" % shaderName,
                             "%sSG.surfaceShader" % shaderName)
            cmds.setAttr("%s.color" % shaderName,
                         0.0, 0.0, 0.0,
                         type="double3")
            cmds.sets(meshName, forceElement="%sSG" % shaderName)
        else:
            #shader exist connect
            cmds.sets(meshName, forceElement="%sSG" % shaderName)
        return (stapleModIndicatorName, transformName, meshName, shaderName)
    # end def

    def removeStrandItem(self, strandItem):
        """Remove a StrandItem from the local list of StrandItems"""
        del self._strandItems[strandItem]
    # end def
