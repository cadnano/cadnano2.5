from __future__ import division
from collections import namedtuple
import math

Matrix4 = namedtuple('Matrix4', ['n11','n12', 'n13', 'n14',
                                'n21', 'n22', 'n23', 'n24',
                                'n31', 'n32', 'n33', 'n34',
                                'n41', 'n42', 'n43', 'n44'])

def makeTranslation(x,y,z):
    return Matrix4( 1., 0., 0., x,
                    0., 1., 0., y,
                    0., 0., 1., z,
                    0., 0., 0., 1.)

def makeRotationZ(theta):
        c = math.cos(theta)
        s = math.sin(theta)
        return Matrix4(
            c, - s, 0, 0,
            s,  c, 0, 0,
            0,  0, 1, 0,
            0,  0, 0, 1
        )
# end def