from enum import Enum as _Enum


class EnumMask(object):
    def __init__(self, enum, value):
        self._enum=enum
        self._value=value
 
    def __and__(self, other):
        assert isinstance(other,self._enum)
        return self._value&other.bwv
 
    def __or__(self, other):
        assert isinstance(other,self._enum)
        return EnumMask(self._enum, self._value|other.bwv)
 
    def __repr__(self):
        return "<{} for {}: {}>".format(
            self.__class__.__name__,
            self._enum,
            self._value
        )

class Enum(_Enum):
    @property
    def bwv(self): # bitwise value
        cls=self.__class__
        idx=list(cls.__members__.values()).index(self)
        return 2**idx
 
    def __or__(self, other):
        return EnumMask(self.__class__, self.bwv|other.bwv)
 
    def __and__(self, other):
        if isinstance(other, self.__class__):
            return self.bwv&other.bwv
        elif isinstance(other, EnumMask):
            return other&self
        else: raise

class PartType(_Enum):
    PLASMIDPART = 0
    ORIGAMIPART = 1
    DNAPART = 2

class ItemType(_Enum):
    DNA = 0
    PLASMID = 1
    RNA = 2
    PEPTIDE = 3
    PROTEIN = 4
    ORIGAMI = 5
    OLIGO = 6
    SELECTION = 7
    ANNOTATION = 8


class LatticeType:
    HONEYCOMB = 0
    SQUARE = 1

class EndType:
    FIVE_PRIME = 0
    THREE_PRIME = 1


class StrandType:
    SCAFFOLD = 0
    STAPLE = 1


class Parity:
    EVEN = 0
    ODD = 1


class BreakType:
    LEFT5PRIME = 0
    LEFT3PRIME = 1
    RIGHT5PRIME = 2
    RIGHT3PRIME = 3


class Crossovers:
    HONEYCOMB_SCAF_LEFT = [[1, 11], [8, 18], [4, 15]]
    HONEYCOMB_SCAF_RIGHT = [[2, 12], [9, 19], [5, 16]]
    HONEYCOMB_STAP_LEFT = [[6], [13], [20]]
    HONEYCOMB_STAP_RIGHT = [[7], [14], [0]]
    SQUARE_SCAF_LEFT = [[4, 26, 15], [18, 28, 7], [10, 20, 31], [2, 12, 23]]
    SQUARE_SCAF_RIGHT = [[5, 27, 16], [19, 29, 8], [11, 21, 0], [3, 13, 24]]
    SQUARE_STAP_LEFT = [[31], [23], [15], [7]]
    SQUARE_STAP_RIGHT = [[0], [24], [16], [8]]


class HandleOrient:
    LEFT_UP = 0
    RIGHT_UP = 1
    LEFT_DOWN = 2
    RIGHT_DOWN = 3

class PartEdges(Enum):
    NONE     = 0x0001
    TOP      = 0x0002
    LEFT     = 0x0004
    RIGHT    = 0x0008
    BOTTOM   = 0x0010
    TOPLEFT  = TOP|LEFT
    TOPRIGHT = TOP|RIGHT
    BOTLEFT  = BOTTOM|LEFT
    BOTRIGHT = BOTTOM|RIGHT
    SIDE     = LEFT|RIGHT
    TOPBOT   = TOP|BOTTOM

