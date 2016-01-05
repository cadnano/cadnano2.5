import numpy as np
from collections import deque

DEFAULT_CACHE_SIZE = 20

class VirtualHelixGroup(object):
    def __init__(self):
        """ this is composed of a group of arrays
        that
        1. contain the coordinates of every virtual base stored
            in their index order per label
        2. contains the label per coordinate
        """
        self.coords = np.zeros((0, 3), dtype=float))
        self.labels = np.zeros((0, 1), dtype=int)
        self.indices = np.zeros((0, 1), dtype=int)

        # book keeping for fast lookup of indices for insertions and deletions
        # and coordinate points
        self.offset_and_size = []
        self.fwd_strandsets = []    # list of lists
        self.rev_strandsets = []
        self._query_cache = {}
        self._cache_keys = deque([None]*DEFAULT_CACHE_SIZE)
    # end def

    def getCoordinates(self, label):
        """ return a view onto the numpy array for a
        given label
        """
        offset_and_size = self.offset_and_size
        coords = self.coords
        if label < len(offset_and_size):
            match_label_idxs = offset_and_size[label]
        else:
            match_label_idxs = None
        if match_label_idxs is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))
        else:
            offset, size = match_label_idxs
            lo, hi = offset, offset + size
            return coords[lo:hi]
    # end def

    def getCoordinate(self, label, idx):
        """
        """
        pass
    # end def

    def getIndices(self, label):
        """ return a view onto the numpy array for a
        given label
        """
        offset_and_size = self.offset_and_size
        indices = self.indices
        if label < len(offset_and_size):
            match_label_idxs = offset_and_size[label]
        else:
            match_label_idxs = None
        if match_label_idxs is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))
        else:
            offset, size = match_label_idxs
            lo, hi = offset, offset + size
            return indices[lo:hi]
    # end def

    def addCoordinates(self, label, points, is_append):
        """ Points will only be added on the ends of a virtual helix
        not internally.  NO GAPS!

        label (int): integer index label of the virtual helix
        points (ndarray): n x 3 shaped numpy ndarray of floats or
                        2D Python list

        points are stored in order and by index
        """
        offset_and_size = self.offset_and_size
        coords = self.coords
        len_coords = len(coords)
        labels = self.labels
        indices = self.indices
        num_points = len(points)

        self._query_cache = {} # clear cache

        if label < len(offset_and_size):
            match_label_idxs = offset_and_size[label]
        else:
            match_label_idxs = None

        if match_label_idxs is not None:
            offset, size = match_label_idxs
            lo_idx_limit, hi_idx_limit = offset, offset + size
            if is_append:
                insert_idx = hi_idx_limit
            else: # prepend
                insert_idx = match_label_idxs[0]
            new_lims = (hi_idx_limit, hi_idx_limit + num_points)
            old_offset, old_size = offset_and_size[label]
            offset_and_size[label] = (old_offset, old_size + num_points)
        else: # new label / virtual helix insert after all other points
            # expand offset and size as required
            offset_and_size += [None]*(label - len(offset_and_size) + 1)

            hi_idx_limit = len_coords
            new_lims = (len_coords, len_coords + num_points)
            offset_and_size[label] = (len_coords, num_points)

        self.coords = np.insert(coords, insert_idx, points, axis=0)
        # insertions are always extending an existing label
        self.labels = np.insert(labels, hi_idx_limit, num_points*[label], axis=0)
        self.indices = np.insert(indices, hi_idx_limit, list(range(*new_lims)), axis=0)
    # end def

    def setCoordinates(self, label, points, idx_start=0):
        """ change the coordinates stored
        """
        offset_and_size = self.offset_and_size
        if label < len(offset_and_size):
            match_label_idxs = offset_and_size[label]
        else:
            match_label_idxs = None
        if match_label_idxs is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))
        else:
            offset, size = match_label_idxs
            if idx_start + len(points) > size:
                err = ("Number of Points {} out of range for"
                        "start index {} given existing size {}")
                raise IndexError(err.format(len(points), idx_start, size))
            lo = offset + idx_start
            hi = lo + len(points)
            self.coords[lo:hi] = points
    # end def

    def removeCoordinates(self, label, length, is_start):
        """ remove coordinates given a slice, reindex as necessary
        is_start means whether the removal occurs at the start or the
        end of a virtual helix
        """
        labels = self.labels
        offset_and_size = self.offset_and_size[label]
        indices = self.indices
        coords = self.coords

        current_offset_and_size_length = len(offset_and_size)
        if label < current_offset_and_size_length:
            match_label_idxs = offset_and_size[label]
        else:
            raise IndexError("Label {} out of range".format(label))

        self._query_cache = {} # clear cache

        if match_label_idxs is not None:
            offset, size = match_label_idxs
            lo, hi = offset, offset + size
            if length > size:
                raise IndexError("length longer {} than indices existing".format(length))
            elif offset_and_size[label][1] == length:
                offset_and_size[label] = None
                # trim the unused labels at the end
                remove_count = 0
                for i in range(current_offset_and_size_length - 1, label - 1, -1):
                    if offset_and_size[i] is None:
                        remove_count += 1
                    else:
                        break
                self.offset_and_size = offset_and_size[:old_length - remove_count]
            if is_start:
                idx_start, idx_stop = lo, lo + length
            else:
                idx_start, idx_stop = hi - length, hi
        else:
            raise KeyError("Label {} not in VirtualHelixGroup".format(label))

        the_slice = np.s_[idx_start:idx_stop]
        self.coords = np.delete(coords, the_slice, axis=0)
        self.labels = np.delete(labels, the_slice, axis=0)
        if is_start: # we need to renumber indices
            indices[idx_stop:hi] -= length
        self.indices = np.delete(indices, the_slice, axis=0)
    # end def

    def queryPoint(self, x, y, z, radius):
        qc = self._query_cache
        query = (x, y, z, radius)
        if query in self._query_cache:
            return qc.get(query)
        else:
            res = self._queryPoint(x, y, z, radius)
            self._cache_keys.append(query)
            qc[query] =  res
            # limit the size of the cache
            old_key = self._cache_keys.popleft()
            del qc[old_key]
            return res
    # end def

    def _queryPoint(self, x, y, z, radius):
        """ return the indices of all virtual helices closer
        than radius
        """
        difference = self.coords - (x, y, z)
        # compute square of distance to point
        delta = inner1d(difference, difference)
        close_points = np.where(delta < radius*radius)
        return list(zip(    np.take(self.labels, close_points),
                            np.take(self.indices, close_points) ))
    # end def

# end class

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

def remapSlice(start, stop, length):
    """ remap a slice to positive indices for a given
    length
    """
    new_start = length - start if start < 0 else start
    new_stop = length - stop if stop < 0 else stop

    if new_stop < new_start:
        raise IndexError("Stop {} must be greater than or equal to start {}".format(stop, start))
    return start, stop
# end def
