

from cadnano.part.part import Part
from cadnano.enum import LatticeType


class Crossovers:
    HONEYCOMB_SCAF_LOW = [[1, 11], [8, 18], [4, 15]]
    HONEYCOMB_SCAF_HIGH = [[2, 12], [9, 19], [5, 16]]
    HONEYCOMB_STAP_LOW = [[6], [13], [20]]
    HONEYCOMB_STAP_HIGH = [[7], [14], [0]]

    # # from 0: DR U DL aka 210 90 330
    # HONEYCOMB_SCAF_LOW = [[1, 12], [8, 19], [5, 15]]
    # HONEYCOMB_SCAF_HIGH = [[2, 13], [9, 20], [6, 16]]
    # HONEYCOMB_STAP_LOW = [[17], [3], [10]]
    # HONEYCOMB_STAP_HIGH = [[18], [4], [11]]

root3 = 1.732051


class HoneycombPart(Part):
    _STEP = 21  # 32 in square
    _TURNS_PER_STEP = 2.0
    _HELICAL_PITCH = _STEP/_TURNS_PER_STEP
    _TWIST_PER_BASE = 360/_HELICAL_PITCH # degrees
    _TWIST_OFFSET = 0 # degrees
    
    _active_base_index = _STEP
    _SUB_STEP_SIZE = _STEP / 3
    # Used in VirtualHelix::potentialCrossoverList
    _SCAFL = Crossovers.HONEYCOMB_SCAF_LOW
    _SCAFH = Crossovers.HONEYCOMB_SCAF_HIGH
    _STAPL = Crossovers.HONEYCOMB_STAP_LOW
    _STAPH = Crossovers.HONEYCOMB_STAP_HIGH

    def __init__(self, *args, **kwargs):
        super(HoneycombPart, self).__init__(self, *args, **kwargs)
        self._max_row = kwargs.get('max_row')
        if self._max_row == None:
            raise ValueError("%s: Need max_row kwarg" % (type(self).__name__))
        self._max_col = kwargs.get('max_col')
        if self._max_col == None:
            raise ValueError("%s: Need max_col kwarg" % (type(self).__name__))
        self._max_base = kwargs.get('max_steps') * self._STEP - 1
        if self._max_base == None:
            raise ValueError("%s: Need max_base kwarg" % (type(self).__name__))

    def crossSectionType(self):
        """Returns the cross-section type of the DNA part."""
        return LatticeType.HONEYCOMB

    def isEvenParity(self, row, column):
        return (row % 2) == (column % 2)
    # end def

    def isOddParity(self, row, column):
        return (row % 2) ^ (column % 2)
    # end def

    def getVirtualHelixNeighbors(self, virtualHelix):
        """
        returns the list of neighboring virtualHelices based on parity of an
        input virtualHelix

        If a potential neighbor doesn't exist, None is returned in it's place
        """
        neighbors = []
        vh = virtualHelix
        if vh == None:
            return neighbors

        # assign the method to a a local variable
        getVH = self.virtualHelixAtCoord
        # get the vh's row and column r,c
        (r,c) = vh.coord()

        if self.isEvenParity(r, c):
            neighbors.append(getVH((r,      c + 1   )))  # p0 neighbor (p0 is a direction)
            neighbors.append(getVH((r - 1,  c       )))  # p1 neighbor
            neighbors.append(getVH((r,      c - 1   )))  # p2 neighbor
        else:
            neighbors.append(getVH((r,      c - 1   )))  # p0 neighbor (p0 is a direction)
            neighbors.append(getVH((r + 1,  c       )))  # p1 neighbor
            neighbors.append(getVH((r,      c + 1   )))  # p2 neighbor
        # For indices of available directions, use range(0, len(neighbors))
        return neighbors  # Note: the order and presence of Nones is important
    # end def

    def latticeCoordToPositionXY(self, row, column, scale_factor=1.0):
        """make sure self._radius is a float"""
        radius = self._RADIUS
        x = column*radius*root3
        if self.isOddParity(row, column):   # odd parity
            y = row*radius*3 + radius
        else:                               # even parity
            y = row*radius*3
        return scale_factor*x, scale_factor*y
    # end def

    def positionToCoord(self, x, y, scale_factor=1.0):
        radius = self._RADIUS
        column = int(x / (radius*root3*scale_factor) + 0.5)

        row_temp = y / (radius*scale_factor)
        if (row_temp % 3) + 0.5 > 1.0:
            # odd parity
            row = int((row_temp - 1)/3 + 0.5)
        else:
            # even parity
            row = int(row_temp/3 + 0.5)
    # end def

    ########################## Archiving / Unarchiving #########################
    def fillSimpleRep(self, sr):
        super(HoneycombPart, self).fillSimpleRep(sr)
        sr['.class'] = 'HoneycombPart'
