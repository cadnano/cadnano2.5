#!/usr/bin/env python
# encoding: utf-8


class Insertion(object):
    """Insertions do affect an applied sequence and do not store a sequence
    themselves.  They are a skip if the length is less than 0

    Args:
        index (int): the index into the `StrandSet` the `Insertion` occurs at
        length (int): length of `Insertion`
    """
    __slots__ = '_length', '_index'

    def __init__(self, index, length):
        self._length = length
        self._index = index
    # end def

    def length(self):
        """This is the length of a sequence that is immutable by the strand

        Returns:
            int: length of `Insertion`
        """
        return self._length

    def setLength(self, length):
        """Setter for the length

        Args:
            length (int):
        """
        self._length = length
    # end def

    def updateIdx(self, delta):
        """Increment the index by delta

        Args:
            delta (int): can be negative
        """
        self._index += delta
    # end def

    def idx(self):
        """
        Returns:
            int: the index into the `StrandSet` the `Insertion` occurs at
        """
        return self._index
    # end def

    def isSkip(self):
        """

        Returns:
            bool: True is is a skip, False otherwise
        """
        return self._length < 0
# end class
