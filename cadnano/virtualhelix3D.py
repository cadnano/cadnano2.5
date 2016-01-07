import numpy as np
import math
import pandas as pd
from collections import deque

DEFAULT_CACHE_SIZE = 20

def defaultProperties(label):
    props = [
    ('name', "vh%d" % (label)),
    ('color', '#ffffffff'),
    ('active_phos', None),
    ('eulerZ', 10.),
    ('scamZ', 10.),
    ('neighbor_active_angle', 0.0),
    ('neighbors', [])
    ('bases_per_repeat', 21)
    ('turns_per_repeat', 2)
    ('repeats', 2)
    ('bases_per_turn', 10.5), # bases_per_repeat/turns_per_repeat
    ('twist_per_base', 360 / 10.5) # 360/_bases_per_turn
    ]
    return tuple(zip(*props))
# end def

def defaultDataFrame(size):
    dummy_label = 999
    columns, row = defaultProperties(dummy_label)
    df = pd.DataFrame([row for i in range(size)], columns=columns)
    return df
# end def
DEFAULT_SIZE = 256
DEFAULT_FULL_SIZE = DEFAULT_SIZE*48

class VirtualHelixGroup(object):
    def __init__(self):
        """ this is composed of a group of arrays
        that
        1. contain the coordinates of every virtual base stored
            in their index order per label
        2. contains the label per coordinate
        """

        # 1. per virtual base pair allocations
        self.total_points = 0
        self.coords = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.directions = np.zeros((DEFAULT_FULL_SIZE, 3), dtype=float))
        self.fwd_phosphates = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.rev_phosphates = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.labels = np.zeros((DEFAULT_FULL_SIZE, 1), dtype=int)
        self.indices = np.zeros((DEFAULT_FULL_SIZE, 1), dtype=int)

        # 2. per virtual helix allocations
        self.total_labels = 0
        """
        for doing 2D X,Y manipulation for now.  keep track of
        XY position of virtual helices
        """
        self.origins = np.full((DEFAULT_SIZE, 2), np.inf, dtype=float)

        """
        book keeping for fast lookup of indices for insertions and deletions
        and coordinate points
        the length of this is the max label used
        """
        self.offset_and_size = []

        self.properties = defaultDataFrame(DEFAULT_SIZE)

        self.fwd_strandsets = []
        self.rev_strandsets = []

        # Cache Stuff
        self._point_cache = {}
        self._point_cache_keys = deque([None]*DEFAULT_CACHE_SIZE)
        self._origin_cache = {}
        self._origin_cache_keys = deque([None]*DEFAULT_CACHE_SIZE)
    # end def

    def getOffsetAndSize(self, label):
        offset_and_size = self.offset_and_size
        offset_and_size[label] if label < len(offset_and_size) else return None
    # end def

    def getCoordinates(self, label):
        """ return a view onto the numpy array for a
        given label
        """
        match_label_idxs = self.getOffsetAndSize(label)
        if match_label_idxs is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))
        else:
            offset, size = match_label_idxs
            lo, hi = offset, offset + size
            return self.coords[lo:hi]
    # end def

    def getCoordinate(self, label, idx):
        """
        given a label get the coordinate at a given index
        """
        match_label_idxs = self.getOffsetAndSize(label)
        if match_label_idxs is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))
        else:
            offset, size = match_label_idxs
            if idx < size:
                return self.coords[offset + idx]
            else:
                raise IndexError("idx {} greater than size {}".format(idx, size))
    # end def

    def translateCoordinates(self, labels, delta):
        """ delta is a sequence of floats of length 3
        """
        self._origin_cache = {} # clear cache
        self._point_cache = {}
        origins = self.origins
        delta_origin = delta[:2] # x, y only
        for label in labels:
            coords = self.getCoordinates(label)
            coords += delta # use += to modify the view
            origins[label] += delta_origin
    # end def

    def getIndices(self, label):
        """ return a view onto the numpy array for a
        given label
        """
        match_label_idxs = self.getOffsetAndSize(label)
        if match_label_idxs is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))
        else:
            offset, size = match_label_idxs
            lo, hi = offset, offset + size
            return self.indices[lo:hi]
    # end def

    def getNeighbors(self, label, radius, idx=0):
        """ might use radius = 2.1*RADIUS
        return list of neighbor labels and the indices nearby
        """
        match_label_idxs = self.getOffsetAndSize(label)
        coord = self.getCoordinate(label, idx)
        neighbors, indices = self.queryPoint(radius, *coord)
        non_label_idxs, _ = np.where(neighbors != label)
        return list(zip(np.take(neighbors, non_label_idxs),
                        np.take(indices, non_label_idxs)    ))
    # end def

    def getOriginNeighbors(self, label, radius):
        """ might use radius = 2.1*RADIUS
        for now return a set of neighbor labels
        """
        origin = self.origins[label]
        neighbors = self.queryOrigin(radius, *origin)
        neighbor_candidates = set(neighbors)
        neighbor_candidates.discard(label)
        return neighbor_candidates
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

        self._point_cache = {} # clear cache

        match_label_idxs = self.getOffsetAndSize(label)

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
            number_of_new_elements = (label - len(offset_and_size) + 1)
            offset_and_size += [None]*number_of_new_elements
            self._origin_cache = {} # clear cache
            hi_idx_limit = len_coords
            new_lims = (len_coords, len_coords + num_points)
            offset_and_size[label] = (len_coords, num_points)
            # assign origin on creation, resizing as needed
            self.origins = np.append(   self.origins,
                                        np.full((number_of_new_elements, 2),
                                                np.inf, dtype=float),
                                        axis=0)
            self.origins[label] = points[0][:2] # x, y only
            if not label < len(self.properties):
                self.properties = self.properties.append(defaultDataFrame(100),
                                                        ignore_index=True)
            self.properties.loc[label, 'name'] = "vh%d" % (label)
            self.total_labels += 1

        # Did exceed allocation???
        if self.total_points + num_points > len_coords:
            diff = self.total_points + num_points - len_coords
            number_of_new_elements = math.ceil(diff / DEFAULT_FULL_SIZE)*DEFAULT_SIZE
            # resize per virtual base allocations
            coords = np.append(coords,
                                np.full((number_of_new_elements, 3),
                                        np.inf, dtype=float),
                                axis=0)
            directions = np.append(directions,
                                np.zeros(number_of_new_elements, 3),
                                            dtype=float),
                                axis=0)
            fwd_phosphates = np.append(rev_phosphates,
                                np.full((number_of_new_elements, 3),
                                        np.inf, dtype=float),
                                axis=0)
            rev_phosphates = np.append(rev_phosphates,
                                np.full((number_of_new_elements, 3),
                                        np.inf, dtype=float),
                                axis=0)
            labels = np.append(labels,
                                np.zeros((number_of_new_elements, 3),
                                            dtype=float),
                                axis=0)
            indices = np.append(indices,
                                np.zeros((number_of_new_elements, 3),
                                        dtype=float),
                                axis=0)

        # end if exceeded allocation
        move_idx_start = insert_idx + num_points
        move_idx_end = move_idx_start + total_points - insert_idx
        coords[move_idx_start:move_idx_end] = coords[insert_idx:total_points]
        directions[move_idx_start:move_idx_end] = directions[insert_idx:total_points]
        fwd_phosphates[move_idx_start:move_idx_end] = fwd_phosphates[insert_idx:total_points]
        rev_phosphates[move_idx_start:move_idx_end] = rev_phosphates[insert_idx:total_points]
        labels[move_idx_start:move_idx_end] = labels[insert_idx:total_points]
        indices[move_idx_start:move_idx_end] = indices[insert_idx:total_points]


        # self.coords = np.insert(coords, insert_idx, points, axis=0)
        # # insertions are always extending an existing label
        # self.labels = np.insert(labels, hi_idx_limit, num_points*[label], axis=0)
        # self.indices = np.insert(indices, hi_idx_limit, list(range(*new_lims)), axis=0)
        self.total_points += num_points
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

    def setZCoordinates(self, label, z_points, idx_start=0):
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
            len_z_pts = len(z_points)
            if idx_start + len_z_pts > size:
                err = ("Number of Points {} out of range for"
                        "start index {} given existing size {}")
                raise IndexError(err.format(len_z_pts, idx_start, size))
            lo = offset + idx_start
            hi = lo + len_z_pts
            self.coords[lo:hi][2] = z_points
    # end def

    def removeCoordinates(self, label, length, is_start):
        """ remove coordinates given a length, reindex as necessary
        is_start means whether the removal occurs at the start or the
        end of a virtual helix since virtual helix arrays are always
        contiguous
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

        self._point_cache = {} # clear cache

        if match_label_idxs is not None:
            offset, size = match_label_idxs
            lo, hi = offset, offset + size
            if length > size:
                raise IndexError("length longer {} than indices existing".format(length))
            elif offset_and_size[label][1] == length:
                self._origin_cache = {} # clear cache
                offset_and_size[label] = None
                self.origins[label] = (np.inf, np.inf)  # set off to infinity
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

    def queryPoint(self, radius, x, y, z):
        """
        cached query
        """
        qc = self._point_cache
        query = (radius, x, y, z)
        if query in self._point_cache:
            return qc.get(query)
        else:
            res = self._queryPoint(radius, x, y, z)
            self._point_cache_keys.append(query)
            qc[query] =  res
            # limit the size of the cache
            old_key = self._point_cache_keys.popleft()
            del qc[old_key]
            return res
    # end def

    def _queryPoint(self, radius, x, y, z):
        """ return the indices of all virtual helices closer
        than radius
        """
        difference = self.coords - (x, y, z)
        # compute square of distance to point
        delta = inner1d(difference, difference)
        close_points, _ = np.where(delta < radius*radius)
        # return list(zip(    np.take(self.labels, close_points),
        #                     np.take(self.indices, close_points) ))
        return (np.take(self.labels, close_points),
                            np.take(self.indices, close_points) )
    # end def

    def queryOrigin(self, radius, x, y):
        """ Hack for now to get 2D behavior
        """
        qc = self._origin_cache
        query = (radius, x, y)
        if query in self._origin_cache:
            return qc.get(query)
        else:
            res = self._queryOrigin(radius, x, y)
            self._origin_cache_keys.append(query)
            qc[query] =  res
            # limit the size of the cache
            old_key = self._origin_cache_keys.popleft()
            del qc[old_key]
            return res
    # end def

    def _queryOrigin(self, radius, x, y):
        """ return the indices of all labels closer
        than radius
        """
        difference = self.origins - (x, y)
        # compute square of distance to point
        delta = inner1d(difference, difference)
        close_points, _ = np.where(delta < radius*radius)
        return close_points
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
