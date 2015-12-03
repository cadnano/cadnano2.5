# -*- coding: utf-8 -*-
class Box(object):
    def __init__(self, min_point, max_point):
        self.min_pt = min_point
        self.max_pt = max_point
    # end def

    def set(self, min_point, max_point):
        self.min_pt = min_point
        self.max_pt = max_point
    # end def

    def containsPoint(self, point):
        """
        point -- Vector3 to check for inclusion.
        Returns true if the specified point lies
        within the boundaries of this box.
        """
        if point.x < self.min_pt.x or point.x > self.max_pt.x or \
             point.y < self.min_pt.y or point.y > self.max_pt.y or \
             point.z < self.min_pt.z or point.z > self.max_pt.z:
            return False
        else:
            return True
    # end def

    def containsBox(self, box):
        if (self.min_pt.x <= box.min_pt.x ) and ( box.max_pt.x <= self.max_pt.x ) and \
             ( self.min_pt.y <= box.min_pt.y ) and ( box.max_pt.y <= self.max_pt.y ) and \
             ( self.min_pt.z <= box.min_pt.z ) and ( box.max_pt.z <= self.max_pt.z ):
            return True
        return False
    # end def

    def doesBoxSpan(self, box):
        if (self.min_pt.x <= box.min_pt.x ) and ( box.max_pt.x <= self.max_pt.x ) and \
             ( self.min_pt.y <= box.min_pt.y ) and ( box.max_pt.y <= self.max_pt.y ) and \
             ( self.min_pt.z <= box.min_pt.z ) and ( box.max_pt.z <= self.max_pt.z ):
            return True
        return False
    # end def


    def clone(self):
        """Returns a copy of this box."""
        return Box(Vector3(*self.min_pt), Vector3(*self.max_pt))
    # end def

    def center(self):
        """ Returns the center point of this box.
        """
        return multiplyScalar(addVectors( self.min_pt, self.max_pt), 0.5 )
    # end def

    def size(self):
        """Returns the width, height, and depth of this box.
        """
        return subVectors( self.max_pt, self.min_pt)
# end class