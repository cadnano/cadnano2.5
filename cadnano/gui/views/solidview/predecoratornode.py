# Copyright 2011 Autodesk, Inc.  All rights reserved.
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files ( the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to 
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do 
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
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
predecoratornode.py
Created by Alex Tessier on 2011-08-25
A Maya Node for creating a Staple Modifier indicator on top of a Helix Shape 
"""
import sys
import math
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx


nodeName = "spPreDecoratorNode"
id = OpenMaya.MTypeId( 0x00117703 )


gons = [
    2,10,1,
    1,11,2,
    1,8,7,
    1,7,11,
    1,10,8,
    5,2,6,
    10,2,5,
    2,11,6,
    4,9,3,
    3,12,4,
    5,6,3,
    3,9,5,
    6,12,3,
    7,8,4,
    4,12,7,
    4,8,9,
    5,9,10,
    6,11,12,
    7,12,11,
    8,10,9 ]

class PreDecoratorNode( OpenMayaMPx.MPxNode):
    outputMesh = OpenMaya.MObject()
    radiusAttr = OpenMaya.MObject()
    pointArray = OpenMaya.MObject()
    vtx = []

    def __init__( self):
        OpenMayaMPx.MPxNode.__init__( self)

    def compute( self, plug, data):
        radiusData = data.inputValue( PreDecoratorNode.radiusAttr )
        radius = radiusData.asDouble()

        # make the meshDataObj for the plug
        fnMeshData = OpenMaya.MFnMeshData()
        outMeshDataObj = fnMeshData.create()

        # create the mesh and assign to the data
        self.createMesh( radius, outMeshDataObj )
        handle = data.outputValue( PreDecoratorNode.outputMesh )
        handle.setMObject( outMeshDataObj )
        handle.setClean()

        data.setClean( plug )

    def createMesh( self, radius, outputMeshDataObj ):
        self.vtx = []
        self.createPoints( radius )
        num_verts = 12
        num_faces  = 20
        edges_per_face = 3

        pointArray = OpenMaya.MFloatPointArray()
        for i in range( 0, num_verts ):
            pointArray.append( self.vtx[i] ) # can we skip this copy?

        nFaceConnects = num_faces * edges_per_face;
        nEdges = nFaceConnects / 2

        faceCounts = OpenMaya.MIntArray()
        for i in range( 0, num_faces ):
            faceCounts.append( edges_per_face )

        faceConnects = OpenMaya.MIntArray()
        for i in range( 0, num_faces*edges_per_face ):
            faceConnects.append( gons[i] - 1 )

        outputMesh = OpenMaya.MFnMesh()
        newTransform = outputMesh.create( num_verts, num_faces, pointArray, \
                                          faceCounts, faceConnects, \
                                          outputMeshDataObj )
        outputMesh.updateSurface()

    def FILL(  self, x, y, z ):
        self.vtx.append( OpenMaya.MFloatPoint(  x, y, z ) )

    def createPoints( self, radius ):
        a = math.sqrt(  (  1.0 - math.sqrt(  .2 ) ) / 2.0 ) * radius
        b = math.sqrt(  (  1.0 + math.sqrt(  .2 ) ) / 2.0 ) * radius
        z = 0.0

        self.FILL(  b,  a,  z )
        self.FILL(  b, -a,  z )
        self.FILL( -b, -a,  z )
        self.FILL( -b,  a,  z )

        self.FILL(  0, -b, -a )
        self.FILL(  0, -b,  a )
        self.FILL(  0,  b,  a )
        self.FILL(  0,  b, -a )

        self.FILL( -a,  0, -b )
        self.FILL(  a,  0, -b )
        self.FILL(  a,  0,  b )
        self.FILL( -a,  0 , b )

def nodeCreator( ):
    return OpenMayaMPx.asMPxPtr( PreDecoratorNode() )

def nodeInitialize( ):
    typedAttr = OpenMaya.MFnTypedAttribute()
    PreDecoratorNode.outputMesh = typedAttr.create( "outputMesh",
                                                      "om",
                                                       OpenMaya.MFnData.kMesh )

    nAttr = OpenMaya.MFnNumericAttribute()

    PreDecoratorNode.radiusAttr = nAttr.create( 'radius',
                                                  'r',
                                                  OpenMaya.MFnNumericData.kDouble,
                                                  1.0 )

    nAttr.setStorable( True )
    nAttr.setWritable( True )

    PreDecoratorNode.addAttribute( PreDecoratorNode.outputMesh )
    PreDecoratorNode.addAttribute( PreDecoratorNode.radiusAttr )


    PreDecoratorNode.attributeAffects(
        PreDecoratorNode.radiusAttr,
        PreDecoratorNode.outputMesh)


def initializePlugin( obj ):
    plugin = OpenMayaMPx.MFnPlugin( obj)

    try:
        plugin.registerNode( nodeName, id, nodeCreator, nodeInitialize)
    except:
        sys.stderr.write( "Failed to register node %s\n" % nodeName)
        raise

def uninitializePlugin( obj):
    plugin = OpenMayaMPx.MFnPlugin( obj)

    try:
        plugin.deregisterNode( id)
    except:
        sys.stderr.write( "Failed to deregister node %s\n" % nodeName)
        raise
