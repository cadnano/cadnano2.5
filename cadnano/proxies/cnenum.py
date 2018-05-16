from enum import IntEnum, Enum
from typing import NewType

# Type Alias IntEnum member Alias
EnumType = int

def enumNames(cls):
    return [a for a, b in sorted(cls.__members__.items(), key=lambda x: x[1])]

ENUM_NAMES = {}

class EnumMask(object):
    def __init__(self, enum, value):
        self._enum = enum
        self._value = value

    def __and__(self, other):
        assert isinstance(other, self._enum)
        return self._value & other.bwv

    def __or__(self, other):
        assert isinstance(other, self._enum)
        return EnumMask(self._enum, self._value | other.bwv)

    def __repr__(self):
        return "<{} for {}: {}>".format(
            self.__class__.__name__,
            self._enum,
            self._value
        )


class BitEnum(Enum):
    @property
    def bwv(self):  # bitwise value
        cls = self.__class__
        idx = list(cls.__members__.values()).index(self)
        return 2**idx

    def __or__(self, other):
        return EnumMask(self.__class__, self.bwv | other.bwv)

    def __and__(self, other):
        if isinstance(other, self.__class__):
            return self.bwv & other.bwv
        elif isinstance(other, EnumMask):
            return other & self
        else:
            raise


class PartEnum(IntEnum):
    NUCLEICACIDPART = 1
    PLASMIDPART = 2


class PointEnum(IntEnum):
    """For serializing virtual helices as only pointing in the Z direction
    or pointing in arbitrary directions.

    NOTE: This exists for legacy part importing of lattice designs when moving
    towards the v3 file convention
    """
    Z_ONLY = 0
    ARBITRARY = 1


ENUM_NAMES['point_type'] = enumNames(PointEnum)


class AxisEnum(IntEnum):
    X = 1
    Y = 2
    Z = 4


class ItemEnum(IntEnum):
    # DNA = 0
    # PLASMID = 1
    # RNA = 2
    # PEPTIDE = 3
    # PROTEIN = 4
    OLIGO = 6
    # SELECTION = 7
    # ANNOTATION = 8
    NUCLEICACID = 9
    VIRTUALHELIX = 10

# class EndType:
#     FIVE_PRIME = 0
#     THREE_PRIME = 1


class StrandEnum(IntEnum):
    SCAFFOLD = 0
    STAPLE = 1
    FWD = 0
    REV = 1


class ModEnum(IntEnum):
    END_5PRIME = 0
    END_3PRIME = 1
    INTERNAL = 2


class LatticeEnum(IntEnum):
    SQUARE = 0
    HONEYCOMB = 1


class GridEnum(IntEnum):
    NONE = 0
    SQUARE = 1
    HONEYCOMB = 2

ENUM_NAMES['grid_type'] = enumNames(GridEnum)

class OrthoViewEnum(IntEnum):
    SLICE = 0
    GRID = 1
    BOTH = 2


class ViewSendEnum(IntEnum):
    ALL = 1
    GRID = 2
    SLICE = 4
    PATH = 8
    OUTLINER = 16
    PROPERTY = 32

class ViewReceiveEnum(IntEnum):
    ALL = 1
    GRID = 3
    SLICE = 5
    PATH = 9
    OUTLINER = 17
    PROPERTY = 33

ENUM_NAMES['view_type'] = enumNames(ViewSendEnum)

class HandleEnum(IntEnum):
    TOP_LEFT = 1
    TOP = 2
    TOP_RIGHT = 4
    RIGHT = 8
    BOTTOM_RIGHT = 16
    BOTTOM = 32
    BOTTOM_LEFT = 64
    LEFT = 128


ENUM_NAMES['handle_type'] = enumNames(HandleEnum)

# class BreakEnum(IntEnum):
#     LEFT5PRIME = 0
#     LEFT3PRIME = 1
#     RIGHT5PRIME = 2
#     RIGHT3PRIME = 3


# class HandleOrientEnum(IntEnum):
#     LEFT_UP = 0
#     RIGHT_UP = 1
#     LEFT_DOWN = 2
#     RIGHT_DOWN = 3

# class PartEdgesEnum(BitEnum):
#     NONE     = 0x0001
#     TOP      = 0x0002
#     LEFT     = 0x0004
#     RIGHT    = 0x0008
#     BOTTOM   = 0x0010
#     TOPLEFT  = TOP|LEFT
#     TOPRIGHT = TOP|RIGHT
#     BOTLEFT  = BOTTOM|LEFT
#     BOTRIGHT = BOTTOM|RIGHT
#     SIDE     = LEFT|RIGHT
#     TOPBOT   = TOP|BOTTOM
