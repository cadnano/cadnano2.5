from enum import Enum as _Enum


def enumNames(cls):
    return [a for a, b in sorted(filter(lambda z: isinstance(z[1], int),
            cls.__dict__.items()), key=lambda x: x[1])]
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


class Enum(_Enum):
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


class PartType(_Enum):
    NUCLEICACIDPART = 1
    PLASMIDPART = 2


class PointType:
    """For serializing virtual helices as only pointing in the Z direction
    or pointing in arbitrary directions.
    """
    Z_ONLY = 0
    ARBITRARY = 1
ENUM_NAMES['point_type'] = enumNames(PointType)


class ItemType(_Enum):
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


class StrandType:
    SCAFFOLD = 0
    STAPLE = 1
    FWD = 0
    REV = 1


class ModType:
    END_5PRIME = 0
    END_3PRIME = 1
    INTERNAL = 2


class LatticeType:
    SQUARE = 0
    HONEYCOMB = 1


class GridType:
    NONE = 0
    SQUARE = 1
    HONEYCOMB = 2
ENUM_NAMES['grid_type'] = enumNames(GridType)

# class BreakType:
#     LEFT5PRIME = 0
#     LEFT3PRIME = 1
#     RIGHT5PRIME = 2
#     RIGHT3PRIME = 3


# class HandleOrient:
#     LEFT_UP = 0
#     RIGHT_UP = 1
#     LEFT_DOWN = 2
#     RIGHT_DOWN = 3

# class PartEdges(Enum):
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
