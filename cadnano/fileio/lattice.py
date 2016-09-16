"""
"""
from math import ceil, floor

root3 = 1.732051
class HoneycombDnaPart(object):
    """
    SCAF_LOW = [[1, 11], [8, 18], [4, 15]]
    SCAF_HIGH = [[2, 12], [9, 19], [5, 16]]
    STAP_LOW = [[6, 16], [3, 13], [10, 20]]
    STAP_HIGH = [[7, 17], [4, 14], [0, 11]]

    # from 0: DR U DL aka 210 90 330
    SCAF_LOW = [[1, 12], [8, 19], [5, 15]]
    SCAF_HIGH = [[2, 13], [9, 20], [6, 16]]
    STAP_LOW = [[17], [3], [10]]
    STAP_HIGH = [[18], [4], [11]]
    """
    STEP = 21  # 32 in square
    TURNS_PER_STEP = 2.0
    HELICAL_PITCH = STEP / TURNS_PER_STEP
    TWIST_PER_BASE = 360. / HELICAL_PITCH # degrees
    TWIST_OFFSET = -(360. / 10.5)*1.0 # degrees
    SUB_STEP_SIZE = STEP / 3.

    @staticmethod
    def isEvenParity(row, column):
        return (row % 2) == (column % 2)
    # end def

    @staticmethod
    def isOddParity(row, column):
        return (row % 2) ^ (column % 2)
    # end def

    @staticmethod
    def legacyLatticeCoordToPositionXY(radius, row, column, scale_factor=1.0):
        """make sure radius is a float"""
        x = column*radius*root3
        if HoneycombDnaPart.isOddParity(row, column):   # odd parity
            y = -row*radius*3 + radius
        else:                               # even parity
            y = -row*radius*3
        return scale_factor*x, scale_factor*y
    # end def

    @staticmethod
    def latticeCoordToPositionXY(radius, row, column, scale_factor=1.0):
        """make sure radius is a float"""
        x = column*radius*root3
        if HoneycombDnaPart.isOddParity(row, column):   # odd parity
            y = row*radius*3 + radius
        else:                               # even parity
            y = row*radius*3
        return scale_factor*x, scale_factor*y
    # end def

    @staticmethod
    def positionToLatticeCoord(radius, x, y, scale_factor=1.0):
        column = int(x / (radius*root3*scale_factor) + 0.5)

        row_temp = y / (radius*scale_factor)
        if (row_temp % 3) + 0.5 > 1.0:
            # odd parity
            row = int((row_temp - 1)/3 + 0.5)
        else:
            # even parity
            row = int(row_temp/3 + 0.5)
        return row, column
    # end def

    @staticmethod
    def positionToLatticeCoordRound(radius, x, y,
                                round_up_row, round_up_col, scale_factor=1.0):
        roundRow = ceil if round_up_row else floor
        roundCol = ceil if round_up_col else floor
        column = roundCol(x / (radius*root3*scale_factor))

        row_temp = y / (radius*scale_factor)
        if (row_temp % 3) + 0.5 > 1.0:
            # odd parity
            row = roundRow((row_temp - 1)/3.)
        else:
            # even parity
            row = roundRow(row_temp/3.)
        return row, column
    # end def
# end class

class SquareDnaPart(object):
    """
    SCAF_LOW = [[4, 26, 15], [18, 28, 7], [10, 20, 31], [2, 12, 23]]
    SCAF_HIGH = [[5, 27, 16], [19, 29, 8], [11, 21, 0], [3, 13, 24]]
    STAP_LOW = [[31], [23], [15], [7]]
    STAP_HIGH = [[0], [24], [16], [8]]
    """
    STEP = 32  # 21 in honeycomb
    SUB_STEP_SIZE = STEP / 4
    TURNS_PER_STEP = 3.0
    HELICAL_PITCH = STEP / TURNS_PER_STEP
    TWIST_PER_BASE = 360. / HELICAL_PITCH # degrees
    TWIST_OFFSET = 180. + TWIST_PER_BASE / 2 # degrees

    @staticmethod
    def isEvenParity(row, column):
        return (row % 2) == (column % 2)
    # end def

    @staticmethod
    def isOddParity(row, column):
        return (row % 2) ^ (column % 2)
    # end def

    @staticmethod
    def legacyLatticeCoordToPositionXY(radius, row, column, scale_factor=1.0):
        """
        """
        y = -row*2*radius
        x = column*2*radius
        return scale_factor*x, scale_factor*y
    # end def


    @staticmethod
    def latticeCoordToPositionXY(radius, row, column, scale_factor=1.0):
        """
        """
        y = row*2*radius
        x = column*2*radius
        return scale_factor*x, scale_factor*y
    # end def

    @staticmethod
    def positionToLatticeCoord(radius, x, y, scale_factor=1.0):
        """
        """
        row = int(y/(2.*radius*scale_factor) + 0.5)
        column = int(x/(2.*radius*scale_factor) + 0.5)
        return row, column
    # end def

    @staticmethod
    def positionToLatticeCoordRound(radius, x, y, scale_factor=1.0):
        """
        """
        row = round(y/(2.*radius*scale_factor))
        column = round(x/(2.*radius*scale_factor))
        return row, column
    # end def

# end class
