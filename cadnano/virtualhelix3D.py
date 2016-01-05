import numpy as np


def distanceToPoint(origin, direction, point):
        direction_distance = np.dot(point - origin,  direction)
        # point behind the ray
        if direction_distance < 0:
            diff = origin - point
            return diff*diff

        v = (direction * direction_distance ) + origin
        diff = v - point
        return diff*diff
# end def


class VirtualHelixArray(object):
    def __init__(self):
        """ this is composed of a group of arrays
        that
        1. contain the coordinates of every base
        """
        self.virtual_helix_coords = np.zeros((0, 3), dtype=float))
        self.virtual_helix_labels = np.zeros((0, 1), dtype=int)
        self.virtual_helix_indices = np.zeros((0, 1), dtype=int)
        self._query_cache = {}

        # index of re
        self.removed_set = set()
    # end def

    def addPoints(self, label, points):

    # end def