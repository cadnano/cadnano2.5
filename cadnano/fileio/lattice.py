"""
"""
from math import ceil, floor, sqrt
import random
from typing import (
    List,
    Tuple
)
from cadnano.cntypes import (
    Vec2T
)

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
    def isEvenParity(row: int, column: int) -> bool:
        """Return if the given row and column have even parity."""
        return (row % 2) == (column % 2)
    # end def

    @staticmethod
    def isOddParity(row: int, column: int) -> bool:
        """Return if the given row and column have odd parity."""
        return (row % 2) ^ (column % 2)
    # end def

    @staticmethod
    def distanceFromClosestLatticeCoord(x: float, y: float,
                                        radius: float,
                                        scale_factor: float = 1.0) -> Vec2T:
        """Given a x and y position, determine closest lattice coordinate and
        the distance to the center of those coordinates.
        """
        column_guess = x/(radius*root3)
        row_guess = -(y - radius*2)/(radius*3)

        possible_columns = (floor(column_guess), ceil(column_guess))
        possible_rows = (floor(row_guess), ceil(row_guess))

        best_guess = None
        shortest_distance = float('inf')

        for row in possible_rows:
            for column in possible_columns:
                guess_x, guess_y = HoneycombDnaPart.latticeCoordToQtXY(radius, row, column, scale_factor)
                squared_distance = abs(guess_x-x)**2 + abs(guess_y-y)**2
                distance = sqrt(squared_distance)

                if distance < shortest_distance:
                    best_guess = (row, column)
                    shortest_distance = distance
        return (shortest_distance, best_guess)
    # end def

    @staticmethod
    def legacyLatticeCoordToPositionXY( radius: float,
                                        row: int, column: int,
                                        scale_factor: float = 1.0) -> Vec2T:
        """Convert legacy row,column coordinates to latticeXY."""
        x = column*radius*root3
        y_offset = radius
        if HoneycombDnaPart.isEvenParity(row, column):
            y = -row*radius*3. + radius + y_offset
        else:
            y = -row*radius*3. + y_offset
        # Make sure radius is a float
        return scale_factor*x, scale_factor*y
    # end def

    @staticmethod
    def latticeCoordToModelXY(  radius: float,
                                row: int, column: int,
                                scale_factor: float = 1.0) -> Vec2T:
        """Convert row, column coordinates to latticeXY."""
        x = column*radius*root3*scale_factor
        y_offset = radius
        if HoneycombDnaPart.isEvenParity(row, column):
            y = (row*radius*3. + radius + y_offset)*scale_factor
        else:
            y = (row*radius*3. + y_offset)*scale_factor
        return x, y
    # end def

    @staticmethod
    def latticeCoordToQtXY( radius: float,
                            row: int, column: int,
                            scale_factor: float = 1.0) -> Vec2T:
        """Call :meth:`HoneyCombDnaPart.latticeCoordToQtXY` with the supplied row
        parameter inverted (i.e. multiplied by -1) to reflect the coordinates
        used by Qt.

        Args:
            radius: the model radius
            row: the row in question
            column: the column in question
            scale_factor: the scale factor to be used in the calculations

        Returns:
            The x, y coordinates of the given row and column
        """
        return HoneycombDnaPart.latticeCoordToModelXY(radius, -row, column, scale_factor)
    # end def

    @staticmethod
    def positionModelToLatticeCoord(radius: float,
                                    x: float, y: float,
                                    scale_factor: float = 1.0,
                                    strict: bool = False) -> Tuple[int, int]:
        """Convert a model position to a lattice coordinate."""
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

        if not strict:
            return row, column
        else:
            gridpoint_center_x, gridpoint_center_y = HoneycombDnaPart.latticeCoordToQtXY(radius,
                                                                                         row,
                                                                                         column,
                                                                                         scale_factor)

            if abs(x-gridpoint_center_x)**2 + abs(y+gridpoint_center_y)**2 >= (radius*scale_factor)**2:
                return None
            else:
                return row, column
    # end def

    @staticmethod
    def positionQtToLatticeCoord(   radius: float,
                                    x: float, y: float,
                                    scale_factor: float = 1.0,
                                    strict: bool = False) -> Tuple[int, int]:
        """Convert a Qt position to a lattice coordinate."""
        return HoneycombDnaPart.positionModelToLatticeCoord(radius, x, -y, scale_factor, strict)
    # end def

    @staticmethod
    def positionToLatticeCoordRound(radius: float,
                                    x: float, y: float,
                                    round_up_row: bool, round_up_col: bool,
                                    scale_factor: float = 1.0) -> Vec2T:
        """Convert a model position to a rounded lattice coordinate."""
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

    @staticmethod
    def isInLatticeCoord(   radius_tuple: Tuple[float, float],
                            xy_tuple: Tuple[float, float],
                            coordinate_tuple: Tuple[int, int],
                            scale_factor: float) -> bool:
        """Determine if given x-y coordinates are inside a VH at a given
        row-column coordinate
        """
        if xy_tuple is None or coordinate_tuple is None:
            return False

        assert isinstance(radius_tuple, tuple) and len(radius_tuple) is 2
        assert isinstance(xy_tuple, tuple) and len(xy_tuple) is 2 and all(isinstance(i, float) for i in xy_tuple)
        assert isinstance(coordinate_tuple, tuple) and len(coordinate_tuple) is 2 and all(isinstance(i, int) for i in coordinate_tuple)
        assert isinstance(scale_factor, float)

        part_radius, item_radius = radius_tuple
        row, column = coordinate_tuple
        x, y = xy_tuple

        row_x, row_y = HoneycombDnaPart.latticeCoordToQtXY(part_radius,
                                                           row,
                                                           column,
                                                           scale_factor)
        return abs(row_x - x)**2 + abs(row_y - y)**2 <= item_radius**2
    # end def

    @staticmethod
    def sanityCheckCalculations(iterations: int = 100000000):
        """Ensure that the values returned by latticeCoordToQtXY and
        positionQtToLatticeCoord return consistent results.
        """
        for _ in range(iterations):
            radius = 1.125
            scale_factor = 13.333333333333334
            row = random.randint(-1000, 1000)
            col = random.randint(-1000, 1000)

            x_position, y_position = HoneycombDnaPart.latticeCoordToQtXY(radius, row, col, scale_factor)
            output_row, output_column = HoneycombDnaPart.positionQtToLatticeCoord(radius, x_position, y_position,
                                                                                  scale_factor)

            assert row == output_row, '''
                Rows do not match:  %s != %s.
                    Inputs:
                    radius          %s
                    scale factor    %s
                    row             %s
                    column          %s
            ''' % (row, output_row, radius, scale_factor, row, col)
            assert col == output_column, '''
                    Rows do not match:  %s != %s.
                    Inputs:
                    radius          %s
                    scale factor    %s
                    row             %s
                    column          %s
            ''' % (col, output_column, radius, scale_factor, row, col)
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
    def isEvenParity(row: int, column: int) -> bool:
        """Return if the given row and column have even parity."""
        return (row % 2) == (column % 2)
    # end def

    @staticmethod
    def isOddParity(row: int, column: int) -> bool:
        """Return if the given row and column have odd parity."""
        return (row % 2) ^ (column % 2)
    # end def

    @staticmethod
    def distanceFromClosestLatticeCoord(radius: float,
                                        x: float, y: float,
                                        scale_factor: float = 1.0) -> Vec2T:
        """
        Given a x and y position, determine closest lattice coordinate and the
        distance to the center of those coordinates.
        """
        column_guess = x/(2*radius)
        row_guess = y/(2*radius)

        possible_columns = (floor(column_guess), ceil(column_guess))
        possible_rows = (floor(row_guess), ceil(row_guess))

        best_guess = None
        shortest_distance = float('inf')

        for row in possible_rows:
            for column in possible_columns:
                guess_x, guess_y = SquareDnaPart.latticeCoordToModelXY(radius, -row, column, scale_factor)
                squared_distance = (guess_x-x)**2 + (-guess_y-y)**2
                distance = sqrt(squared_distance)

                if distance < shortest_distance:
                    best_guess = (row, column)
                    shortest_distance = distance

        return (shortest_distance, best_guess)
    # end def

    @staticmethod
    def legacyLatticeCoordToPositionXY( radius: float,
                                        row: int, column: int,
                                        scale_factor: float = 1.0) -> Vec2T:
        """Convert legacy row, column coordinates to latticeXY."""
        y = -row*2*radius
        x = column*2*radius
        return scale_factor*x, scale_factor*y
    # end def

    @staticmethod
    def latticeCoordToModelXY(  radius: float,
                                row: int, column: int,
                                scale_factor: float = 1.0) -> Vec2T:
        """Convert row, column coordinates to latticeXY."""
        y = row*2*radius
        x = column*2*radius
        return scale_factor*x, scale_factor*y
    # end def

    @staticmethod
    def latticeCoordToQtXY( radius: float,
                            row: int, column: int,
                            scale_factor: float = 1.0) -> Vec2T:
        """
        Call SquareDnaPart.latticeCoordToQtXY with the supplied row
        parameter inverted (i.e. multiplied by -1) to reflect the coordinates
        used by Qt.

        Args:
            radius (float): the model radius
            row (int): the row in question
            column (int): the column in question
            scale_factor (float): the scale factor to be used in the calculations

        Returns:
            The x, y coordinates of the given row and column
        """
        return SquareDnaPart.latticeCoordToModelXY(radius, row, column, scale_factor)
    # end def

    @staticmethod
    def positionModelToLatticeCoord(radius: float,
                                    x: float, y: float,
                                    scale_factor: float = 1.0,
                                    strict: bool = False) -> Tuple[int, int]:
        """Convert a model position to a lattice coordinate."""
        float_row = y/(2.*radius*scale_factor) + 0.5
        float_column = x/(2.*radius*scale_factor) + 0.5

        row = int(float_row) if float_row >= 0 else int(float_row - 1)
        column = int(float_column) if float_column >= 0 else int(float_column - 1)

        if not strict:
            return row, column
        else:
            gridpoint_center_x, gridpoint_center_y = SquareDnaPart.latticeCoordToQtXY(radius,
                                                                                      row,
                                                                                      column,
                                                                                      scale_factor)

            if abs(x-gridpoint_center_x)**2 + abs(y-gridpoint_center_y)**2 >= (radius*scale_factor)**2:
                return None
            else:
                return row, column
    # end def

    @staticmethod
    def positionQtToLatticeCoord(   radius: float,
                                    x: float, y: float,
                                    scale_factor: float = 1.0,
                                    strict: bool = False) -> Tuple[int, int]:
        """Convert a Qt position to a lattice coordinate."""
        return SquareDnaPart.positionModelToLatticeCoord(radius, x, -y, scale_factor, strict)
    # end def

    @staticmethod
    def positionToLatticeCoordRound(radius: float,
                                    x: float, y: float,
                                    scale_factor: float = 1.0) -> Tuple[int, int]:
        """Convert a model position to a rounded lattice coordinate."""
        row = round(y/(2.*radius*scale_factor))
        column = round(x/(2.*radius*scale_factor))
        return row, column
    # end def

    @staticmethod
    def isInLatticeCoord(   radius_tuple: Tuple[float, float],
                            xy_tuple: Tuple[float, float],
                            coordinate_tuple: Tuple[int, int],
                            scale_factor: float) -> bool:
        """Determine if given x-y coordinates are inside a VH at a given
        row-column coordinate
        """
        if xy_tuple is None or coordinate_tuple is None:
            return False

        assert isinstance(radius_tuple, tuple) and len(radius_tuple) is 2
        assert isinstance(xy_tuple, tuple) and len(xy_tuple) is 2 and all(isinstance(i, float) for i in xy_tuple)
        assert isinstance(coordinate_tuple, tuple) and len(coordinate_tuple) is 2 and all(isinstance(i, int) for i in coordinate_tuple)
        assert isinstance(scale_factor, float)

        part_radius, item_radius = radius_tuple
        row, column = coordinate_tuple
        x, y = xy_tuple

        row_x, row_y = SquareDnaPart.latticeCoordToQtXY(part_radius,
                                                        row,
                                                        column,
                                                        scale_factor)
        return abs(row_x - x)**2 + abs(row_y  - y)**2 <= item_radius**2
    # end def
# end class
