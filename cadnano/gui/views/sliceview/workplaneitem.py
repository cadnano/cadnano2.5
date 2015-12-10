from PyQt5.QtWidgets import QGraphicsItem

ROOT3 = 1.732051

"""
cells of the form
[(a, b)] --> map to
x = a*radius*scale_factor, y = b*radius*scale_factor
where x and y are the centroids
"""

UNIT_CELLS {
    'honeycomb': {  'cell': [   (0, 0),
                                (ROOT3, 1),
                                (ROOT3, 3),
                                (0, 4)
                            ]
                    'pitch': (2*ROOT3, 6)
    }
    'square': {     'cell':   [(0, 0)]
                    'pitch': (2, 2)
    }
    'superhoneycomb': {  'cell': [   (0, 0),
                                (ROOT3, 1),
                                (ROOT3, 3),
                                (0, 4),
                                (0, 2)
                            ]
                    'pitch': (2*ROOT3, 6)
    }
}


class WorkplaneItem(QGraphicsItem):
    def __init__(self, scale_factor, part_item):
        super(WorkplaneItem, self).__init__(part_item)
        self.scale_factor = scale_factor
        self.setUnitCell(UNIT_CELLS['honeycomb'])
    # end def

    def setUnitCell(self, info):
        self.unit_cell = info['cell']
        self.unit_pitch = info['pitch']
    # end def

    def _spawnEmptyHelixItemAt(self, row, column):
        helix = EmptyHelixItem(row, column, self)
        # helix.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
        self._empty_helix_hash[(row, column)] = helix
    # end def

    def _killHelixItemAt(row, column):
        s = self._empty_helix_hash[(row, column)]
        s.scene().removeItem(s)
        del self._empty_helix_hash[(row, column)]
    # end def

    def _setLattice(self, old_coords, new_coords):
        """A private method used to change the number of rows,
        cols in response to a change in the dimensions of the
        part represented by the receiver"""
        old_set = set(old_coords)
        old_list = list(old_set)
        new_set = set(new_coords)
        new_list = list(new_set)
        for coord in old_list:
            if coord not in new_set:
                self._killHelixItemAt(*coord)
        # end for
        for coord in new_list:
            if coord not in old_set:
                self._spawnEmptyHelixItemAt(*coord)
        # end for
        # self._updateGeometry(newCols, newRows)
        # self.prepareGeometryChange()
        # the Deselector copies our rect so it changes too
        self.deselector.prepareGeometryChange()
        if not getReopen():
            self.zoomToFit()
    # end def

    def isEvenParity(self, row, column):
        return (row % 2) == (column % 2)
    # end def

    def isOddParity(self, row, column):
        return (row % 2) ^ (column % 2)
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