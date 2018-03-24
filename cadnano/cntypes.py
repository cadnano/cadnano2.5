# -*- coding: utf-8 -*-
from typing import Tuple
from typing import List
from typing import Dict
from typing import Set
from typing import Iterable
from typing import Union
import numpy as np

cn = lambda x: 'cadnano.' + x
OligoT =    cn('oligo.Oligo')
StrandT =   cn('strand.Strand')
SegmentT =  Tuple[int,  int]
WindowT =   cn('views.documentwindow.DocumentWindow')
DocT =      cn('document.Document')
DocCtrlT =  cn('controllers.DocumentController')
NucleicAcidPartT = cn('part.nucleicacidpart.NucleicAcidPart')
VirtualHelixT = cn('part.virtualhelix.VirtualHelix')

RectT = Tuple[float, float, float, float]
IntT = Union[np.int64, int]
IntTuple = (np.int64, int)
KeyT = Union[str, Iterable[str]]
ValueT = Union[object, Iterable[object]]
Vec2T = Tuple[float, float]
Vec3T = Union[np.ndarray, Tuple[float, float, float]]
HitListT = List[Tuple[int, List[int], List[int] ]]
PointsT = Tuple[np.ndarray, np.ndarray, np.ndarray]
ABInfoT = Tuple[int, bool, int, int]

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
SubQueryIDNumT = List[Tuple[int, Tuple[List[int], List[int]]]]
QueryIDNumT = Tuple[SubQueryIDNumT, SubQueryIDNumT]