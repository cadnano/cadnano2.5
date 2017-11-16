from __future__ import division
from collections import namedtuple
import math

Matrix3 = namedtuple('Matrix3', ['n11','n12', 'n13',
                                'n21', 'n22', 'n23',
                                'n31', 'n32', 'n33'])
"""
namedtuple: 3 x 3 matrix
"""

def getInverse(m4):
    """
    Args:
        m4 (Matrix4):

    Returns:
        Matrix3:
    """
    o0 =   m4[10] * m4[5] - m4[6] * m4[9]
    o1 = - m4[10] * m4[1] + m4[2] * m4[9]
    o2 =   m4[6 ] * m4[1] - m4[2] * m4[5]
    o3 = - m4[10] * m4[4] + m4[6] * m4[8]
    o4 =   m4[10] * m4[0] - m4[2] * m4[8]
    o5 = - m4[6] * m4[0] + m4[2] * m4[4]
    o6 =   m4[9] * m4[4] - m4[5] * m4[8]
    o7 = - m4[9] * m4[0] + m4[1] * m4[8]
    o8 =   m4[5] * m4[0] - m4[1] * m4[4]

    det = m4[0] * o0 + m4[1] * o3 + m4[2] * o6
    if det == 0:
        raise ValueError("getInverse(): can't invert matrix, determinant is 0")

    return Matrix3(o0/det, o1/det, o2/det,
                    o3/det, o4/det, o5/det,
                    o6/det, o7/det, o8/det)
# end def

def transpose(m):
    """Compute the inverse of `m`

    Args:
        m (Matrix3):

    Returns:
        Matrix3: the inverse
    """
    return Matrix3(m[0], m[3], m[6],
                    m[1], m[4], m[7],
                     m[2], m[5], m[8])
# end def

def getNormalMatrix(m):
    """ Normalize the matrix `m`
    Args:
        m (Matrix3):

    Returns:
        Matrix3
    """
    return transpose(getInverse( m ))