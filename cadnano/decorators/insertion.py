#!/usr/bin/env python
# encoding: utf-8

class Insertion(object):
    """
    Insertions do affect an applied sequence and do not store a sequence
    themselves.  They are a skip if the length is less than 0
    """
    def __init__(self, index, length):
        self._length = length
        self._index  = index
    # end def

    def length(self):
        """
        This is the length of a sequence that is immutable by the strand
        """
        return self._length

    def setLength(self, length):
        self._length = length
    # end def

    def updateIdx(self, delta):
        self._index += delta
    # end def

    def idx(self):
        return self._index
    # end def

    def isSkip(self):
        return self.length() < 0
# end class