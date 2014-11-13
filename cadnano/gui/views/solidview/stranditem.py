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
stranditem.py
Created by Simon Breslav on 2011-10-05.
"""

from controllers.mayacontrollers.mayaObjectManager import Mom
from controllers.itemcontrollers.strand.stranditemcontroller \
                                                import StrandItemController
from model.enum import StrandType
from model.enum import LatticeType

from cadnano import app
import maya.OpenMayaUI as mui
import maya.OpenMaya as mo
import maya.cmds as cmds
import util

util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'pyqtSlot', \
                                        'QObject', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QColor'])


class StrandItem(object):
    """
    StrandItem is the visual representation of the strand in the 3D SolidView.
    For this visual representation, StrandItem creates HalfCylinderHelixNode
    Node inside of Maya, so while the StrandItem itself does not get drawn in
    any way, it is the object that communicates with Maya Nodes associated
    with a given strand.
    """
    def __init__(self, mID, modelStrand, virtualHelixItem):
        """
        The parent should be a VirtualHelixItem.
        Initialize function creates the Maya Node for the strand, and setups
        the lookup tables inside of mayaObjectManager (Mom) so that the Maya
        Node can be globally found given a strand, and the other way around.
        Also, sets up StrandItemController that is used to setup all the
        slots and signals between strand model and this strandItem.
        """
        self._modelStrand = modelStrand
        self._virtualHelixItem = virtualHelixItem
        self._viewroot = app().activeDocument.win.solidroot
        mayaNodeInfo = ()
        # print "solidview.StrandItem.__init__ %s" % mID
        if(modelStrand.strandSet().isScaffold()):
            mayaNodeInfo = self.createMayaHelixNodes(virtualHelixItem.x(),
                                                     virtualHelixItem.y(),
                                      modelStrand.oligo().color(),
                                      StrandType.SCAFFOLD,
                                      mID)
        else:
            mayaNodeInfo = self.createMayaHelixNodes(virtualHelixItem.x(),
                                                     virtualHelixItem.y(),
                                      modelStrand.oligo().color(),
                                      StrandType.STAPLE,
                                      mID)
        #self.onStrandDidMove(strand)
        m = Mom()
        m.cnToMaya[modelStrand] = mayaNodeInfo
        m.mayaToCn[mayaNodeInfo[2]] = modelStrand
        m.mayaToCn[mayaNodeInfo[0]] = modelStrand
        self.updateSize()
        self._controller = StrandItemController(self, modelStrand)
    # end def

    ### SLOTS ###
    def strandResizedSlot(self, strand, indices):
        """Receives notification from the model when a strand is resized"""
        #print "solid.StrandItem.strandResizedSlot", self._modelStrand.idxs()
        self.updateSize()
        self._virtualHelixItem.updateDecorators()
        m = Mom()
        m.updateSelectionBoxes()

    def strandUpdateSlot(self, strand):
        """strandUpdateSlot - empty"""
        pass

    def sequenceAddedSlot(self, oligo):
        """sequenceAddedSlot - empty"""
        pass

    def sequenceClearedSlot(self, oligo):
        """sequenceClearedSlot - empty"""
        pass

    def strandRemovedSlot(self, strand):
        """
        Receives notification from the model when a strand is removed.
        Deletes the strand related mapping in mayaObjectManager, deletes all
        the Maya nodes, deletes all the decorators(live in the
        virtualHelixItem right now), deletes itself from the virtualHelixItem,
        and disconnects itself from the controller.
        """
        mom = Mom()
        mID = mom.strandMayaID(strand)
        mom.removeIDMapping(mID, strand)
        # print "solidview.StrandItem.strandRemovedSlot %s" % mID
        transformName = "%s%s" % (mom.helixTransformName, mID)
        cylinderName = "%s%s" % (mom.helixNodeName, mID)
        meshName = "%s%s" % (mom.helixMeshName, mID)
        if cmds.objExists(transformName):
            cmds.delete(transformName)
        if cmds.objExists(cylinderName):
            cmds.delete(cylinderName)
        if cmds.objExists(meshName):
            cmds.delete(meshName)
        if mID in self._virtualHelixItem.StrandIDs():
            self._virtualHelixItem.StrandIDs().remove(mID)
        self._virtualHelixItem.updateDecorators()
        self._virtualHelixItem.removeStrandItem(self)
        self._virtualHelixItem = None
        self._modelStrand = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def oligoAppearanceChangedSlot(self, oligo):
        """
        Receives notification from the model when a oligo changes appearance.
        Updates the color of the strandItem associated with this strand
        """
        mom = Mom()
        id = mom.strandMayaID(self._modelStrand)
        self.updateColor(id, oligo.color())
        pass

    def oligoSequenceAddedSlot(self, oligo):
        """oligoSequenceAddedSlot - empty"""
        pass

    def oligoSequenceClearedSlot(self, oligo):
        """oligoSequenceClearedSlot - empty"""
        pass

    def strandHasNewOligoSlot(self, strand):
        """
        Receives notification from the model when there is a new oligo.
        Updates the color of the strandItem associated with this strand
        """
        mom = Mom()
        self._controller.reconnectOligoSignals()
        mID = mom.strandMayaID(strand)
        self.updateColor(mID, strand.oligo().color())

    def strandInsertionAddedSlot(self, strand, insertion):
        """strandInsertionAddedSlot - empty"""
        pass

    def strandInsertionChangedSlot(self, strand, insertion):
        """strandInsertionChangedSlot - empty"""
        pass

    def strandInsertionRemovedSlot(self, strand, index):
        """strandInsertionRemovedSlot - empty"""
        pass

    def strandModsAddedSlot(self, strand, mods):
        """strandModsAddedSlot - empty"""
        pass

    def strandModsChangedSlot(self, strand, mods):
        """strandModsChangedSlot - empty"""
        pass

    def strandModsRemovedSlot(self, strand, index):
        """strandModsRemovedSlot - empty"""
        pass

    def strandModifierAddedSlot(self, strand, modifier):
        """strandModifierAddedSlot - empty"""
        pass

    def strandModifierChangedSlot(self, strand, modifier):
        """strandModifierChangedSlot - empty"""
        pass

    def strandModifierRemovedSlot(self, strand, index):
        """strandModifierRemovedSlot - empty"""
        pass

    def selectedChangedSlot(self, strand, indices):
        #print "solidview.stranditem.selectedChangedSlot", strand, indices

        mom = Mom()
        if mom.ignoreExternalSelectionSignal:
            return
        mID = mom.strandMayaID(strand)
        mom.ignoreExternalSelectionSignal = True
        transformName = "%s%s" % (mom.helixTransformName, mID)
        if cmds.objExists(transformName):
            if(indices[0] or indices[1]):
                cmds.select(transformName, add=True)
                # print "selecting a strand"
                self._viewroot.addToSelectionDict(strand)
            else:
                # print "deselecting in the slot"
                cmds.select(transformName, deselect=True)
                self._viewroot.removeFromSelectionDict(strand)
        mom.ignoreExternalSelectionSignal = False
    # end def

    ### METHODS ###
    def createMayaHelixNodes(self, x, y, colorname, strandType, mID):
        """
        Create all the Maya nodes, set the initial attributes and connections.
        There are 3 Maya nodes associated with each Strand: Transform Node,
        Shape Node (spHalfCylinderHelixNode), and a Mesh Node (a generic Maya
        Node that is used for rendering) The Mesh Node is the child of the
        Transform Node, and spHalfCylinderHelixNode node inputs the shape data
        into the Mesh Node, using cmds.connectAttr command
         ________________
        | Transform Node |
         ----------------
                |
         ________________  .inMesh          .outputMesh _____________________
        |   Mesh Node    |<---------------------------| HalfCylinderHelixNode |
         ----------------                              -----------------------
        """
        m = Mom()
        cylinderName = "%s%s" % (m.helixNodeName, mID)
        transformName = "%s%s" % (m.helixTransformName, mID)
        meshName = "%s%s" % (m.helixMeshName, mID)
        # shaderName = "%s%s" % (m.helixShaderName, mID)
        cmds.createNode("transform", name=transformName, skipSelect=True)
        cmds.setAttr("%s.rotateX" % transformName, 90)
        cmds.setAttr("%s.translateX" % transformName, x)
        cmds.setAttr("%s.translateY" % transformName, y)
        cmds.createNode("mesh",
                        name=meshName,
                        parent=transformName,
                        skipSelect=True)
        cmds.createNode("spHalfCylinderHelixNode",
                        name=cylinderName,
                        skipSelect=True)
        cmds.connectAttr("%s.outputMesh" % cylinderName,
                         "%s.inMesh" % meshName)
        # XXX - [SB] This should go away and we will ask the model for
        # the right numbers...
        vhi = self._virtualHelixItem
        part = vhi.partItem().part()
        cSType = part.crossSectionType()
        cmds.setAttr("%s.rotation" % cylinderName, part.twistPerBase())
        cmds.setAttr("%s.parity" % cylinderName, vhi.isEvenParity())
        if cSType == LatticeType.HONEYCOMB:
            cmds.setAttr("%s.rotationOffset" % cylinderName, 250)
            cmds.setAttr("%s.decoratorRotOffset" % cylinderName, 90)
        elif cSType == LatticeType.SQUARE:
            cmds.setAttr("%s.rotationOffset" % cylinderName, 125)
            cmds.setAttr("%s.decoratorRotOffset" % cylinderName, 200)
        else:
            raise NotImplementedError
        cmds.setAttr("%s.strandType" % cylinderName, strandType)
        self.updateColor(mID, colorname)

        cmds.select(transformName)
        cmds.polySoftEdge(a=89.99)
        cmds.setAttr("%s.displayEdges" % meshName, 2)
        cmds.select(clear=True)
        return (cylinderName, transformName, meshName)

    def updateColor(self, mID, colorname):
        """
        Update the color of the Maya's Mesh Node associated with a this
        StrandItem, this is done by creating a shadingNode for each color or
        connecting the Mesh Mode to an existing shadingNode if one exists
        for a given color.
        """
        m = Mom()
        meshName = "%s%s" % (m.helixMeshName, mID)
        color = QColor(colorname)
        colorval = "%d_%d_%d" % (color.red(), color.green(), color.blue())
        shaderName = "%s%d_%d_%d" % (m.helixShaderName, color.red(),
                                                  color.green(),
                                                  color.blue())
        if not cmds.objExists(shaderName):
            # Shader does not exist create one
            cmds.shadingNode('lambert', asShader=True, name=shaderName)
            cmds.sets(n="%sSG" % shaderName, r=True, nss=True, em=True)
            cmds.connectAttr("%s.outColor" % shaderName,
                             "%sSG.surfaceShader" % shaderName)
            cmds.setAttr("%s.color" % shaderName,
                         color.redF(), color.greenF(), color.blueF(),
                         type="double3")
            cmds.sets(meshName, forceElement="%sSG" % shaderName)
        else:
            #shader exist connect
            cmds.sets(meshName, forceElement="%sSG" % shaderName)

    def updateSize(self):
        """
        Update Maya's Half Cylinder Node attributes related to the size
        """
        mom = Mom()
        mID = mom.strandMayaID(self._modelStrand)
        cylinderName = "%s%s" % (mom.helixNodeName, mID)
        endpoints = self._modelStrand.idxs()
        totalNumBases = \
                self._virtualHelixItem.virtualHelix().part().maxBaseIdx()
        cmds.setAttr("%s.startBase" % cylinderName,
                             endpoints[0])

        cmds.setAttr("%s.endBase" % cylinderName,
                             endpoints[1])
        cmds.setAttr("%s.totalBases" % cylinderName, int(totalNumBases))
