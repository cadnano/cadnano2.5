# -*- coding: utf-8 -*-
class Box(object):
    """Cube box object

    For doing an oct tree type thing

    Args:
        min_point (Tuple): length 3 lower left corner
        max_point (Tuple): length 3 diagonal opposite top corner
    """

    def __init__(self, min_point, max_point):
        self.min_pt = min_point
        self.max_pt = max_point
    # end def

    def set(self, min_point, max_point):
        """Set the Tuples

        Setter for setting the bounding points of the Box

        Args:
            min_point (Tuple): length 3 lower left corner
            max_point (Tuple): length 3 diagonal opposite top corner
        """
        self.min_pt = min_point
        self.max_pt = max_point
    # end def

    def containsPoint(self, point):
        """ Is the `point` within this Box?

        Args:
            point (Vector3): to check for inclusion.

        Returns:
            bool:  True if the specified point lies within the boundaries
                of this box False otherwise
        """
        if point.x < self.min_pt.x or point.x > self.max_pt.x or \
             point.y < self.min_pt.y or point.y > self.max_pt.y or \
             point.z < self.min_pt.z or point.z > self.max_pt.z:
            return False
        else:
            return True
    # end def

    def containsBox(self, box):
        """ Does this object contain the Box box?

        Args:
            Box:

        Returns:
            bool: True if `box` is in `self` otherwise False
        """
        if (self.min_pt.x <= box.min_pt.x ) and ( box.max_pt.x <= self.max_pt.x ) and \
             ( self.min_pt.y <= box.min_pt.y ) and ( box.max_pt.y <= self.max_pt.y ) and \
             ( self.min_pt.z <= box.min_pt.z ) and ( box.max_pt.z <= self.max_pt.z ):
            return True
        return False
    # end def

    def doesBoxSpan(self, box):
        """ doe this object contain the Box `box`?
        Args:
            Box:

        Returns:
            bool: True if `box` spans `self` otherwise False
        """
        if (self.min_pt.x <= box.min_pt.x ) and ( box.max_pt.x <= self.max_pt.x ) and \
             ( self.min_pt.y <= box.min_pt.y ) and ( box.max_pt.y <= self.max_pt.y ) and \
             ( self.min_pt.z <= box.min_pt.z ) and ( box.max_pt.z <= self.max_pt.z ):
            return True
        return False
    # end def


    def clone(self):
        """Clone this Box

        Returns:
            Box: a copy of this box.
        """
        return Box(Vector3(*self.min_pt), Vector3(*self.max_pt))
    # end def

    def center(self):
        """ Return the center of this Box

        Returns:
            Vector3: the center point of this box.
        """
        return multiplyScalar(addVectors( self.min_pt, self.max_pt), 0.5 )
    # end def

    def size(self):
        """Find the dimensions of the Box

        Returns:
            Tuple: the width, height, and depth of this box.
        """
        return subVectors( self.max_pt, self.min_pt)
# end class