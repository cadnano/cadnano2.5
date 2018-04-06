# -*- coding: utf-8 -*-

class Insertion(object):
    """:class:`Insertion`s do affect an applied sequence and do not store a sequence
    themselves.  They are a skip if the length is less than 0

    Args:
        index: the index into the :class:`StrandSet` the :class:`Insertion`
            occurs at
        length: length of :class:`Insertion`
    """

    def __init__(self, index: int, length: int):
        self._length = length
        self._index = index
    # end def

    def length(self) -> int:
        """This is the length of a sequence that is immutable by the strand

        Returns:
            length of :class:`Insertion`
        """
        return self._length

    def setLength(self, length: int):
        """Setter for the length

        Args:
            length:
        """
        self._length = length
    # end def

    def updateIdx(self, delta: int):
        """Increment the index by delta

        Args:
            delta: can be negative
        """
        self._index += delta
    # end def

    def idx(self) -> int:
        """
        Returns:
            the index into the :class:`StrandSet` the :class:`Insertion` occurs at
        """
        return self._index
    # end def

    def isSkip(self) -> bool:
        """

        Returns:
            ``True`` is is a skip, ``False ``otherwise
        """
        return self._length < 0
# end class
