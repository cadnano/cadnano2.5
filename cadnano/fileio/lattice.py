"""
"""
from math import ceil, floor, sqrt

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
    HELICAL_PITCH = STEP/TURNS_PER_STEP
    TWIST_PER_BASE = 360./HELICAL_PITCH  # degrees
    TWIST_OFFSET = -(360./10.5)*1.0  # degrees
    SUB_STEP_SIZE = STEP/3.

    # Manually tuned grid offsets
    PAD_GRID_XL = -100
    PAD_GRID_XH = 70
    PAD_GRID_YL = -150
    PAD_GRID_YH = 105

    @staticmethod
    def isEvenParity(row, column):
        return (row % 2) == (column % 2)
    # end def

    @staticmethod
    def isOddParity(row, column):
        return (row % 2) ^ (column % 2)
    # end def

    @staticmethod
    def distanceFromClosestLatticeCoord(x, y, radius, scale_factor=1.0):
        column_guess = x/(radius*root3)
        row_guess = -(y - radius*2)/(radius*3)

        possible_columns = (floor(column_guess), ceil(column_guess))
        possible_rows = (floor(row_guess), ceil(row_guess))

        best_guess = None
        shortest_distance = float('inf')

        for row in possible_rows:
            for column in possible_columns:
                guess_x, guess_y = HoneycombDnaPart.latticeCoordToPositionXY(radius, -row, column, scale_factor)
                squared_distance = (guess_x-x)**2 + (-guess_y-y)**2
                distance = sqrt(squared_distance)

                if distance < shortest_distance:
                    best_guess = (row, column)
                    shortest_distance = distance

        return (shortest_distance, best_guess)
    # end def

    @staticmethod
    def legacyLatticeCoordToPositionXY(radius, row, column, scale_factor=1.0):
        """Convert legacy row,column coordinates to latticeXY."""
        x = (column)*radius*root3
        if HoneycombDnaPart.isEvenParity(row, column):   # odd parity
            y = -row*radius*3 + radius
        else:                               # even parity
            y = -row*radius*3
        # Make sure radius is a float
        return scale_factor*x, scale_factor*y
    # end def

    @staticmethod
    def latticeCoordToPositionXY(radius, row, column, scale_factor=1.0, invert=False):
        """Convert row, column coordinates to latticeXY."""
        x = column*radius*root3*scale_factor
        y_offset = radius
        if HoneycombDnaPart.isEvenParity(row, column):
            y = (row*radius*3. + radius + y_offset)*scale_factor  # even parity
        else:
            y = (row*radius*3. + y_offset)*scale_factor  # odd parity
        return x, y if not invert else -y
    # end def

    @staticmethod
    def positionToLatticeCoord(radius, x, y, scale_factor=1.0, strict=False):
        assert isinstance(radius, float)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(scale_factor, float)
        assert isinstance(strict, bool)

        float_column = x/(radius*root3*scale_factor) + 0.5
        column = int(float_column) if float_column >= 0 else int(float_column - 1)

        row_temp = y/(radius*scale_factor)
        if (row_temp % 3) + 0.5 > 1.0: # odd parity
            float_row = (y-radius)/(scale_factor*radius*3) + radius
        else: # even parity
            float_row = y/(scale_factor*radius*3) + radius
        row = int(float_row) if float_row >= 0 else int(float_row - 1)
        # TODO:  should scale_factor be 1.0 here?  1/scale_factor?
        gridpoint_center_x, gridpoint_center_y = HoneycombDnaPart.latticeCoordToPositionXY(radius,
                                                                                           row,
                                                                                           column,
                                                                                           scale_factor,
                                                                                           invert=True)
        unscaled_gridpoint_center_x, unscaled_gridpoint_center_y = HoneycombDnaPart.latticeCoordToPositionXY(radius, row, column)
        inverted_gridpoint_center_x, inverted_gridpoint_center_y = HoneycombDnaPart.latticeCoordToPositionXY(radius,
                                                                                                             row,
                                                                                                             column,
                                                                                                             1/scale_factor)

        model_radius = radius*scale_factor
        x_difference = abs(x-gridpoint_center_x)
        y_difference = abs(y-gridpoint_center_y)

#        from cadnano.util import qtdb_trace
#        qtdb_trace()

        print('[LATT]  rad %s' % model_radius)
        print('[LATT]  row %s' % row)
        print('[LATT]  col %s' % column)
        print('[LATT]  x   %s' % x)
        print('[LATT]  y   %s' % y)
#        print('[LATT]  sx  %s' % (x/scale_factor))
#        print('[LATT]  xy  %s' % (y/scale_factor))
        print('[LATT]  gpx %s' % gridpoint_center_x)
        print('[LATT]  gpy %s' % gridpoint_center_y)
        print('[LATT]  xdf %s' % x_difference)
        print('[LATT]  ydf %s' % y_difference)
        print('[LATT]  sum %s' % (x_difference**2 + y_difference**2))
#        print('[LATT]  upx %s' % unscaled_gridpoint_center_x)
#        print('[LATT]  upy %s' % unscaled_gridpoint_center_y)
#        print('[LATT]  ipx %s' % inverted_gridpoint_center_x)
#        print('[LATT]  ipy %s' % inverted_gridpoint_center_y)


#        if abs(x-gridpoint_center_x)**2 + abs(y-gridpoint_center_y)**2 >= (radius*scale_factor)**2:
#            print('[LATT] None')
#        else:
#            print('[LATT] %s, %s' % row, column)

        if abs(x-gridpoint_center_x)**2 + abs(y-gridpoint_center_y)**2 >= (radius*scale_factor)**2:
            print('[LATT] None')
        else:
            print('[LATT] %s, %s' % (row, column))
        print('\n')
#            from cadnano.util import qtdb_trace
#            qtdb_trace()

        if not strict:
            return row, column
        else:
            gridpoint_center_x, gridpoint_center_y = HoneycombDnaPart.latticeCoordToPositionXY(radius, row, column)
            if (x-gridpoint_center_x)**2 + (y-gridpoint_center_y)**2 >= radius**2:
                return None
            else:
                return row, column
    # end def

    @staticmethod
    def positionToLatticeCoordRound(radius, x, y, round_up_row, round_up_col,
                                    scale_factor=1.0):
        roundRow = ceil if round_up_row else floor
        roundCol = ceil if round_up_col else floor
        column = roundCol(x/(radius*root3*scale_factor))

        row_temp = y/(radius*scale_factor)
        if (row_temp % 3) + 0.5 > 1.0: # odd parity
            row = roundRow((row_temp - 1)/3.)
        else: # even parity
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
    SUB_STEP_SIZE = STEP/4
    TURNS_PER_STEP = 3.0
    HELICAL_PITCH = STEP/TURNS_PER_STEP
    TWIST_PER_BASE = 360./HELICAL_PITCH  # degrees
    TWIST_OFFSET = 180. + TWIST_PER_BASE/2  # degrees

    # Manually tuned grid offsets
    PAD_GRID_XL = -80
    PAD_GRID_XH = 80
    PAD_GRID_YL = -80
    PAD_GRID_YH = 80

    @staticmethod
    def isEvenParity(row, column):
        return (row % 2) == (column % 2)
    # end def

    @staticmethod
    def isOddParity(row, column):
        return (row % 2) ^ (column % 2)
    # end def

    @staticmethod
    def distanceFromClosestLatticeCoord(x, y, radius, scale_factor=1.0):
        column_guess = x/(2*radius)
        row_guess = y/(2*radius)

        possible_columns = (floor(column_guess), ceil(column_guess))
        possible_rows = (floor(row_guess), ceil(row_guess))

        best_guess = None
        shortest_distance = float('inf')

        for row in possible_rows:
            for column in possible_columns:
                guess_x, guess_y = SquareDnaPart.latticeCoordToPositionXY(radius, -row, column, scale_factor)
                squared_distance = (guess_x-x)**2 + (-guess_y-y)**2
                distance = sqrt(squared_distance)

                if distance < shortest_distance:
                    best_guess = (row, column)
                    shortest_distance = distance

        return (shortest_distance, best_guess)
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
        float_row = y/(2.*radius*scale_factor) + 0.5
        float_column = x/(2.*radius*scale_factor) + 0.5

        row = int(float_row) if float_row >= 0 else int(float_row - 1)
        column = int(float_column) if float_column >= 0 else int(float_column - 1)

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
