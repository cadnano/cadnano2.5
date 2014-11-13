# -*- coding: utf-8 -*-
from __future__ import division
from collections import namedtuple
import math


Vector3 = namedtuple('Vector3', ['x', 'y', 'z'])
Vector2 = namedtuple('Vector2', ['x', 'y'])

def crossProduct(a, b):
    """ return normalized cross product
    """
    x = a.y*b.z - a.z*b.y
    y = -(a.x*b.z - a.z*b.x)
    z = a.x*b.y - a.y*b.x
    mag = math.sqrt(x**2 + y**2 + z**2)
    if mag < 1e-8:
        return Vector3(0,0,0)
    else:
        return Vector3(x/mag, y/mag, z/mag)
# end def

def normalizeV3(v):
    mag = math.sqrt(v.x**2 + v.y**2 + v.z**2)
    if mag < 1e-8:
        return Vector3(0,0,0)
    else:
        return Vector3(v.x/mag, v.y/mag, v.z/mag)
# end def

def normalToPlane(v1, v2, v3):
    """  Calculate unit normal to the normal to 
    the plane defined by vertices v1, v2, and v3
    """
    subVector = lambda a, b: Vector3(a.x - b.x, a.y - b.y, a.z - b.z)
    a = subVector(v3, v2)
    b = subVector(v1, v2)
    return crossProduct(a, b)
# end def

def applyMatrix3(m, v):
    x = m[0] * v.x + m[1] * v.y + m[2] * v.z
    y = m[3] * v.x + m[4] * v.y + m[5] * v.z
    z = m[6] * v.x + m[7] * v.y + m[8] * v.z
    return Vector3(x, y, z)
# end def

def applyMatrix4(m, v):
    x = m[0] * v.x + m[1] * v.y + m[2] * v.z + m[3]
    y = m[4] * v.x + m[5] * v.y + m[6] * v.z + m[7]
    z = m[8] * v.x + m[9] * v.y + m[10] * v.z + m[11]
    return Vector3(x, y, z)
# end def