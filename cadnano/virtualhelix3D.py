import numpy as np
import math
import pandas as pd
from collections import deque
"""
inner1d(a, a) is equivalent to np.einsum('ik,ij->i', a, a)
equivalent to np.sum(a*a, axis=1)
but faster
"""
from numpy.core.umath_tests import inner1d

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
    ('helical_pitch', 1.)
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
        self.radius = 2     # probably a property???

        # 1. per virtual base pair allocations
        self.total_points = 0
        self.axis_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.fwd_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.rev_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.labels = np.full((DEFAULT_FULL_SIZE, 1), -1, dtype=int)
        self.indices = np.zeros((DEFAULT_FULL_SIZE, 1), dtype=int)

        # 2. per virtual helix allocations
        self.total_labels = 0
        """
        for doing 2D X,Y manipulation for now.  keep track of
        XY position of virtual helices
        """
        self.origin_pts = np.full((DEFAULT_SIZE, 2), np.inf, dtype=float)
        self.directions = np.zeros((DEFAULT_SIZE, 3), dtype=float))
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

        # scratch allocations for vector calculations
        self.m3_scratch0 = np.zeros((3,3), dtype=float)
        self.m3_scratch1 = np.zeros((3,3), dtype=float)
        self.m3_scratch2 = np.zeros((3,3), dtype=float)
        self.eye3_scratch = np.eye(3, 3, dtype=float)    # don't change this
        self.delta2D_scratch = np.empty((1,), dtype=float)
        self.delta3D_scratch = np.empty((1,), dtype=float)
    # end def

    def getOffsetAndSize(self, label):
        offset_and_size = self.offset_and_size
        offset_and_size[label] if label < len(offset_and_size) else return None
    # end def

    def getCoordinates(self, label):
        """ return a view onto the numpy array for a
        given label
        """
        offset_and_size = self.getOffsetAndSize(label)
        if offset_and_size is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))

        offset, size = offset_and_size
        lo, hi = offset, offset + size
        return (self.axis_pts[lo:hi],
                self.fwd_pts[lo:hi],
                self.rev_pts[lo:hi] )
    # end def

    def getCoordinate(self, label, idx):
        """
        given a label get the coordinate at a given index
        """
        offset_and_size = self.getOffsetAndSize(label)
        if offset_and_size is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))

        offset, size = offset_and_size
        if idx < size:
            return self.axis_pts[offset + idx]
        else:
            raise IndexError("idx {} greater than size {}".format(idx, size))
    # end def

    def translateCoordinates(self, labels, delta):
        """ delta is a sequence of floats of length 3
        for now support XY translation
        """
        self._origin_cache = {} # clear cache
        self._point_cache = {}
        origin_pts = self.origin_pts
        delta_origin = delta[:2] # x, y only
        for label in labels:
            coord_pts, fwd_pts, rev_pts = self.getCoordinates(label)
            coord_pts += delta # use += to modify the view
            fwd_pts += delta # use += to modify the view
            rev_pts += delta # use += to modify the view
            origin_pts[label] += delta_origin
    # end def

    def getIndices(self, label):
        """ return a view onto the numpy array for a
        given label
        """
        offset_and_size = self.getOffsetAndSize(label)
        if offset_and_size is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))

        offset, size = offset_and_size
        lo, hi = offset, offset + size
        return self.indices[lo:hi]
    # end def

    def getNeighbors(self, label, radius, idx=0):
        """ might use radius = 2.1*RADIUS
        return list of neighbor labels and the indices nearby
        """
        offset_and_size = self.getOffsetAndSize(label)
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
        origin = self.origin_pts[label]
        neighbors = self.queryOrigin(radius, *origin)
        neighbor_candidates = set(neighbors)
        neighbor_candidates.discard(label)
        return neighbor_candidates
    # end def

    def addCoordinates(self, label, points, is_right):
        """ Points will only be added on the ends of a virtual helix
        not internally.  NO GAPS!
        handles reindex the points in self.indices

        label (int): integer index label of the virtual helix
        points (ndarray): n x 3 shaped numpy ndarray of floats or
                        2D Python list

                        points are stored in order and by index
        is_right (bool): whether we are extending in the positive index direction
                        or prepending
        """
        offset_and_size = self.getOffsetAndSize(label)

        # 1. Find insert indices
        if offset_and_size is None:
            raise IndexError("Label {} does not exists".format(label))

        offset_and_size = self.offset_and_size
        len_axis_pts = len(self.axis_pts)

        coord_pts, fwd_pts, rev_pts = points
        num_points = len(coord_pts) # number of points being added

        self._point_cache = {} # clear cache

        # 1. existing label
        offset, size = offset_and_size
        lo_idx_limit, hi_idx_limit = offset, offset + size
        if is_right:
            insert_idx = hi_idx_limit
        else: # prepend
            insert_idx = offset

        new_lims = (hi_idx_limit, hi_idx_limit + num_points)
        old_offset, old_size = offset_and_size[label]
        offset_and_size[label] = (old_offset, old_size + num_points)

        # 2. Did exceed allocation???
        if self.total_points + num_points > len_axis_pts:
            diff = self.total_points + num_points - len_axis_pts
            number_of_new_elements = math.ceil(diff / DEFAULT_FULL_SIZE)*DEFAULT_FULL_SIZE
            total_rows = len_axis_pts + number_of_new_elements
            # resize per virtual base allocations
            self.axis_pts.resize((total_rows, 3))
            self.axis_pts[len_axis_pts:, :] = np.inf

            self.fwd_pts.resize((total_rows, 3))
            self.fwd_pts[len_axis_pts:, :] = np.inf

            self.rev_pts.resize((total_rows, 3))
            self.rev_pts[len_axis_pts:, :] = np.inf

            self.labels.resize((total_rows, 3))
            self.labels[len_axis_pts:, :] = -1

            self.indices.resize((total_rows, 3))
            self.indices[len_axis_pts:, :] = 0
        # end if exceeded allocation
        axis_pts = self.axis_pts
        fwd_pts = self.fwd_pts
        rev_pts = self.rev_pts
        labels = self.labels
        indices = self.indices

        # 3. Move Existing data
        move_idx_start = insert_idx + num_points
        move_idx_end = move_idx_start + total_points - insert_idx

        axis_pts[move_idx_start:move_idx_end] = axis_pts[insert_idx:total_points]
        axis_pts[insert_idx:move_idx_start] = coord_pts

        fwd_pts[move_idx_start:move_idx_end] = fwd_pts[insert_idx:total_points]
        fwd_pts[insert_idx:move_idx_start] = fwd_pts
        rev_pts[move_idx_start:move_idx_end] = rev_pts[insert_idx:total_points]
        rev_pts[insert_idx:move_idx_start] = rev_pts

        # just overwrite everything for indices and labels no need to move
        labels[insert_idx:move_idx_start] = label
        indices[lo_idx_limit:move_idx_start] = list(range(num_points + size))

        self.total_points += num_points
    # end def

    def getDirections(self, labels):
        """
        labels: array_like list of indices or scalar index
        """
        return np.take(self.directions, labels, axis=0)
    # end def

    def normalize(self, v):
        norm = np.linalg.norm(v)
        if norm == 0:
           return v
        return v / norm
    # end def

    def lengthSq(self, v):
        return inner1d(v, v)

    def cross(self, a, b):
        ax, ay, az = a
        bx, by, bz = b
        c = [ay*bz - az*by,
             az*bx - ax*bz,
             ax*by - ay*bx]
        return c
    # end def

    def makeRotation(self, v1, v2):
        """ create a rotation matrix for an object pointing
        in the v1 direction to the v2 direction

        see http://math.stackexchange.com/questions/180418/calculate-rotation-matrix-to-align-vector-a-to-vector-b-in-3d/180436#180436
        """
        if v1 == v2:
            return self.eye3_scratch.copy()

        v1 = self.normalize(v1)
        v2 = self.normalize(v2)

        v = np.cross(v1, v2)
        sin_squared = inner1d(v, v)
        cos_ = inner1d(v1, v2) # fast dot product

        m1 = self.m3_scratch1
        m2 = self.m3_scratch2
        m0 = self.m3_scratch0
        m0 = m0.fill(0.)

        m0[1, 0] =  v[2]
        m0[0, 1] =  -v[2]
        m0[2, 0] =  -v[1]
        m0[0, 2] =  v[1]
        m0[2, 1] =  v[0]
        m0[1, 2] =  -v[0]

        # do the following efficiently
        # self.eye3_scratch + m0 + np.dot(m0, m0)*((1 - cos_)/sin_squared)
        np.dot(m0, m0, out=m1)
        np.add(self.eye3_scratch, m0, out=m2)
        np.add(m2, m1*((1 - cos_)/sin_squared), out=m0)
        return m0
    # end def

    def createLabel(self, label, origin, direction, num_points):
        offset_and_size = self.getOffsetAndSize(label)

        if offset_and_size is not None:
            raise IndexError("Label {} already exists")

        offset_and_size = self.offset_and_size
        len_axis_pts = len(self.axis_pts)
        num_points = len(points)

        # 1. New label / virtual helix insert after all other points
        # expand offset and size as required
        self._origin_cache = {} # clear cache

        number_of_new_elements = label - len(offset_and_size) + 1
        offset_and_size += [None]*number_of_new_elements

        lo_idx_limit = len_axis_pts
        new_lims = (len_axis_pts, len_axis_pts + num_points)
        offset_and_size[label] = (len_axis_pts, num_points)

        # 2. Assign origin on creation, resizing as needed
        len_origin_pts = len(self.origin_pts)
        if label >= len_origin_pts:
            diff = label - len_origin_pts
            number_of_new_elements = math.ceil(diff / DEFAULT_SIZE)*DEFAULT_SIZE
            total_rows = len_origin_pts + number_of_new_elements
            # resize adding zeros
            self.origin_pts.resize((total_rows, 2))
            self.origin_pts[len_origin_pts:, :] = np.inf

            self.directions.resize((total_rows, 3))
            self.directions[len_origin_pts:, :] = 0    # unnecessary

            self.properties = self.properties.append(
                                        defaultDataFrame(number_of_new_elements),
                                        ignore_index=True)

        self.origin_pts[label] = origin[:2]
        self.directions[label] = direction
        self.properties.loc[label, 'name'] = "vh%d" % (label)
        self.total_labels += 1

        # 3. Create points
        points = self.pointsFromDirection(label, origin, direction, num_points, 0)
        self.addCoordinates(label, points, is_right=False)
    # end def

    def pointsFromDirection(self, label, origin, direction, num_points, index):
        """ Assumes always prepending or appending points.  no insertions.
        changes eulerZ of the label properties as required for prepending points

        origin: (1,3) ndarray or length 3 sequence.  The origin should be
                    referenced from an index of 0.
        direction: (1,3) ndarray or length 3 sequence

        index: the offset index into a helix to start the helix at.  Useful for
            appending points. if index less than zero

        returns:
            None
        """
        rad = self.radius
        hp, twist_per_base, eulerZ = self.properties.loc[label,
                                                            ['helical_pitch',
                                                            'twist_per_base',
                                                            'eulerZ']]
        twist_per_base *= math.pi/180.
        eulerZ_new = eulerZ + twist_per_base*index

        fwd_angles = [i*twist_per_base + eulerZ_new for i in range(num_points)]
        rev_angles = [a + math.pi for a in fwd_angles]
        z_pts = np.arange(index, num_points + index)

        fwd_pts = rad*np.column_stack(( np.cos(fwd_angles),
                                        np.sin(fwd_angles),
                                        np.zeros(num_points)))
        fwd_pts[:,2] = z_pts
        rev_pts = rad*np.column_stack(( np.cos(rev_angles),
                                        np.sin(rev_angles),
                                        np.zeros(num_points)))
        rev_pts[:,2] = z_pts

        coord_pts = np.zeros((num_points,3))
        coord_pts[:,2] = z_pts

        # create scratch array for stashing intermediate results
        scratch = np.zeros((3, num_points), dtype=float)
        # rotate about 0 index and then translate
        m = self.makeRotation((1, 0, 0), direction)

        np.add(np.dot(m, fwd_pts.T, out=scratch).T, origin, out=fwd_pts)
        np.add(np.dot(m, rev_pts.T, out=scratch).T, origin, out=rev_pts)
        np.add(np.dot(m, coord_pts.T, out=scratch).T, origin, out=coord_pts)

        if index < 0:
            self.properties.loc[label, 'eulerZ'] = eulerZ_new

        return (coord_pts, fwd_pts, rev_pts)
    # end def

    def resizeLabel(self, label, is_right, delta):
        """ label (int): the label of the virtual helix
            is_right (bool): whether this is a left side (False) or
                    right side (True) operation
            delta (int): number of virtual base pairs to add to (+) or trim (-)
            from the virtual helix
            returns: None
        """
        offset_and_size = self.getOffsetAndSize(label)
        if offset_and_size is None:
            raise IndexError("Label {} does not exist")

        offset, size = offset_and_size
        len_axis_pts = len(self.axis_pts)
        direction = self.directions[label]
        origin = self.origin_pts[label]
        if delta > 0:   # adding points
            if is_right:
                index = size
            else:
                index = -delta
            # 3. Create points
            points = self.pointsFromDirection(label, origin, direction, delta, index)
            self.addCoordinates(label, points, is_right=is_right)
            # TODO add checks for resizing strandsets here

        elif delta < 0: # trimming points
            if abs(delta) >= size:
                raise ValueError("can't delete virtual helix this way")
            # TODO add checks for strandsets etc here:

            self.removeCoordinates(label, abs(delta), is_right)
        else: # delta == 0
            return
    # end def

    def removeLabel(self, label):
        """
        label (int):
        """
        offset_and_size = self.getOffsetAndSize(label)
        if offset_and_size is None:
            raise IndexError("Label {} does not exist")
        offset, size = offset_and_size
        did_remove = self.removeCoordinates(label, size, is_right=False)
        assert did_remove
    # end def

    def resetCoordinates(self, label):
        """ call this after changing helix properties
        """
        offset_and_size = self.getOffsetAndSize(label)
        if offset_and_size is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))
        offset, size = offset_and_size
        origin = self.origin_pts[label]
        direction = self.origin_pts[direction]
        points = self.pointsFromDirection(label, origin, direction, size)
        self.setCoordinates(label, points)
    # end def

    def setCoordinates(self, label, points, idx_start=0):
        """ change the coordinates stored, useful when adjusting
        helix properties

        label: the label to apply this to

        points: tuple containing axis, and forward and reverse phosphates
        points

        idx_start: index offset into the virtual helix to assign points to.
        """
        offset_and_size = self.getOffsetAndSize(label)
        if offset_and_size is None:
            raise KeyError("label {} not in VirtualHelixGroup".format(label))

        offset, size = offset_and_size
        if idx_start + len(points) > size:
            err = ("Number of Points {} out of range for"
                    "start index {} given existing size {}")
            raise IndexError(err.format(len(points), idx_start, size))

        coord_pts, fwd_pts, rev_pts = points
        lo = offset + idx_start
        hi = lo + len(coord_pts)
        self.axis_pts[lo:hi] = coord_pts
        self.fwd_pts[lo:hi] = fwd_pts
        self.rev_pts[lo:hi] = rev_pts
    # end def

    def removeCoordinates(self, label, length, is_right):
        """ remove coordinates given a length, reindex as necessary
        label (int):
        length (int):
        is_right (bool): whether the removal occurs at the right or left
        end of a virtual helix since virtual helix arrays are always
        contiguous

        returns (bool): True if label is removed, False otherwise
        """

        offset_and_size = self.getOffsetAndSize(label)

        if offset_and_size is None:
            raise KeyError("Label {} not in VirtualHelixGroup".format(label))

        offset, size = offset_and_size

        if length > size:
            raise IndexError("length longer {} than indices existing".format(length))
        lo, hi = offset, offset + size
        if is_right:
            idx_start, idx_stop = hi - length, hi
        else:
            idx_start, idx_stop = lo, lo + length

        self._point_cache = {} # clear cache
        offset_and_size = self.offset_and_size[label]
        current_offset_and_size_length = len(offset_and_size)

        # 1. Move the good data

        relocate_idx_end = idx_start + total_points - length
        total_points = self.total_points

        axis_pts = self.axis_pts
        axis_pts[idx_start:relocate_idx_end] = axis_pts[idx_stop:total_points]
        axis_pts[relocate_idx_end:total_points] = np.inf

        fwd_pts = self.fwd_pts
        fwd_pts[idx_start:relocate_idx_end] = fwd_pts[idx_stop:total_points]
        fwd_pts[relocate_idx_end:total_points] = np.inf

        rev_pts = self.rev_pts
        rev_pts[idx_start:relocate_idx_end] = rev_pts[idx_stop:total_points]
        rev_pts[relocate_idx_end:total_points] = np.inf

        labels = self.labels
        labels[idx_start:relocate_idx_end] = labels[idx_stop:total_points]
        labels[relocate_idx_end:total_points] = -1

        indices = self.indices
        indices[idx_start:relocate_idx_end] = indices[idx_stop:total_points]
        indices[relocate_idx_end:total_points] = 0
        if not is_right:
            # We need to adjust the base index
            # lo offset index should not change for a given label
            indices[lo:lo + length] -= length

        # 2. Adjust the offsets of labels greater than label
        for i, item in enumerate(offset_and_size[label:]):
            if item is not None:
                offset, size = item
                offset_and_size[i + label] = (offset - length, size)

        # 3. Check if we need to remove Virtual Helix
        if offset_and_size[label][1] == length:
            self.total_labels -= 1
            self._origin_cache = {} # clear cache
            offset_and_size[label] = None
            self.origin_pts[label] = (np.inf, np.inf)  # set off to infinity
            # trim the unused labels at the end
            remove_count = 0
            for i in range(current_offset_and_size_length - 1, label - 1, -1):
                if offset_and_size[i] is None:
                    remove_count += 1
                else:
                    break
            self.offset_and_size = offset_and_size[:old_length - remove_count]
            did_remove = True
        else:
            did_remove = False
        self.total_points -= length
        return did_remove
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
        difference = self.axis_pts - (x, y, z)
        ldiff = len(difference)
        delta = self.delta3D_scratch
        if ldiff != len(delta):
            self.delta3D_scratch = delta = np.empty((ldiff,), dtype=float)

        # compute square of distance to point
        delta = inner1d(difference, difference, out=delta)
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
        difference = self.origin_pts - (x, y)
        ldiff = len(difference)
        delta = self.delta2D_scratch
        if ldiff != len(delta):
            self.delta2D_scratch = delta = np.empty((ldiff,), dtype=float)

        # compute square of distance to point
        inner1d(difference, difference, out=delta)
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
