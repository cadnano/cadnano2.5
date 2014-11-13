from cadnano.enum import LatticeType
from cadnano.part.part import Part

class Crossovers:
    SQUARE_SCAF_LOW = [[4, 26, 15], [18, 28, 7], [10, 20, 31], [2, 12, 23]]
    SQUARE_SCAF_HIGH = [[5, 27, 16], [19, 29, 8], [11, 21, 0], [3, 13, 24]]
    SQUARE_STAP_LOW = [[31], [23], [15], [7]]
    SQUARE_STAP_HIGH = [[0], [24], [16], [8]]


class SquarePart(Part):
    _STEP = 32  # 21 in honeycomb
    _SUB_STEP_SIZE = _STEP / 4
    _TURNS_PER_STEP = 3.0
    _HELICAL_PITCH = _STEP/_TURNS_PER_STEP
    _TWIST_PER_BASE = 360/_HELICAL_PITCH # degrees
    _TWIST_OFFSET = 180 + _TWIST_PER_BASE/2 # degrees
    
    # Used in VirtualHelix::potentialCrossoverList
    _SCAFL = Crossovers.SQUARE_SCAF_LOW
    _SCAFH = Crossovers.SQUARE_SCAF_HIGH
    _STAPL = Crossovers.SQUARE_STAP_LOW
    _STAPH = Crossovers.SQUARE_STAP_HIGH

    def __init__(self, *args, **kwargs):
        super(SquarePart, self).__init__(self, *args, **kwargs)
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
        return LatticeType.SQUARE
    # end def

    def isEvenParity(self, row, column):
        return (row % 2) == (column % 2)
    # end def

    def isOddParity(self, row, column):
        return (row % 2) ^ (column % 2)
    # end def

    def getVirtualHelixNeighbors(self, virtual_helix):
        """
        returns the list of neighboring virtualHelices based on parity of an
        input virtual_helix

        If a potential neighbor doesn't exist, None is returned in it's place
        """
        neighbors = []
        vh = virtual_helix
        if vh == None:
            return neighbors

        # assign the method to a a local variable
        getVH = self.virtualHelixAtCoord
        # get the vh's row and column r,c
        (r,c) = vh.coord()

        if self.isEvenParity(r, c):
            neighbors.append(getVH((r,      c + 1   )))  # p0 neighbor (p0 is a direction)
            neighbors.append(getVH((r + 1,  c       )))  # p1 neighbor
            neighbors.append(getVH((r,      c - 1   )))  # p2 neighbor
            neighbors.append(getVH((r - 1,  c       )))  # p2 neighbor
        else:
            neighbors.append(getVH((r,      c - 1   )))  # p0 neighbor (p0 is a direction)
            neighbors.append(getVH((r - 1,  c       )))  # p1 neighbor
            neighbors.append(getVH((r,      c + 1   )))  # p2 neighbor
            neighbors.append(getVH((r + 1,  c       )))  # p3 neighbor
        # For indices of available directions, use range(0, len(neighbors))
        return neighbors  # Note: the order and presence of Nones is important
    # end def

    def latticeCoordToPositionXY(self, row, column, scale_factor=1.0):
        """
        make sure self._radius is a float
        """
        radius = self._RADIUS
        y = row*2*radius
        x = column*2*radius
        return scale_factor*x, scale_factor*y
    # end def

    def positionToCoord(self, x, y, scale_factor=1.0):
        """
        """
        radius = self._RADIUS
        row = int(y/(2*radius*scale_factor) + 0.5)
        column = int(x/(2*radius*scale_factor) + 0.5)
        return row, column
    # end def

    def fillSimpleRep(self, sr):
        super(SquarePart, self).fillSimpleRep(sr)
        sr['.class'] = 'SquarePart'
