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

def normalizeV2(v):
    x, y = v
    mag = math.sqrt(x**2 + y**2)
    if mag < 1e-8:
        return Vector3(0,0,0)
    else:
        return x/mag, v.y/mag
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

def v3SetX(v, x):
    return Vector3(x, v.y, v.z)

def v3SetY(v, y):
    return Vector3(v.x, y, v.z)

def v3SetZ(v, z):
    return Vector3(v.x, v.y, z)

def addVectors(v1, v2):
    return Vector3(v1.x+v2.x, v1.y+v2.y, v1.z+v2.z)

def subVectors(v1, v2):
    """ return v1 - v2
    """
    return Vector3(v1.x-v2.x, v1.y-v2.y, v1.z-v2.z)

def multiplyScalar(v, s):
    """ return v1*s
    """
    return Vector3(v.x*s, v.y*s, v.z*s)

def v2DistanceAndAngle(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dist = math.sqrt(dx*dx + dy*dy)
    angle = math.atan2(dy, dx)
    return dist, angle

def v2dot(a, b):
    return a[0]*b[0]+a[1]*b[1]

def v2AngleBetween(a, b):
    a = normalizeV2(a)
    b = normalizeV2(b)
    numerator = v2dot(a, b)
    xa, xa = a
    xb, yb = a
    maga = math.sqrt(xa**2 + ya**2)
    magb = math.sqrt(xb**2 + yb**2)
    return math.acos(num/(maga*magb))
# end def
# end def
