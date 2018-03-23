# -*- coding: utf-8 -*-
from typing import Tuple
from typing import List
from typing import Dict
from typing import Set
from typing import Iterable
from typing import Union
import numpy as np

OligoType = 'cadnano.oligo.Oligo'
StrandType = 'cadnano.strand.Strand'
SegmentType = Tuple[int,  int]

RectType = Tuple[float, float, float, float]
IntType = Union[np.int64, int]
IntTuple = (np.int64, int)
KeyType = Union[str, Iterable[str]]
ValueType = Union[object, Iterable[object]]
Vec3Type = Union[np.ndarray, Tuple[float, float, float]]
HitListType = List[Tuple[int, List[int], List[int] ]]
HitDictType = Dict[int, Tuple[HitListType, HitListType]]
PointsType = Tuple[np.ndarray, np.ndarray, np.ndarray]

'''
tuple: of :obj:`list`, fwd_axis_hits, rev_axis_hits
where each element in the list is::

    :obj:`tuple` of :obj:`int`, :obj:`tuple`

corresponding to an index into id_num and a tuple of hits on a neighbors
looking like::

    :obj:`tuple` of :obj:`list`:

with the item in the first element::

                the neighbors ID
and the item in second element::

                the index into that neighbor
'''
SubQIDType = List[Tuple[int, Tuple[List[int], List[int]]]]
QueryIDNumType = Tuple[SubQIDType, SubQIDType]