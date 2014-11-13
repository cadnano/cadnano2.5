
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
