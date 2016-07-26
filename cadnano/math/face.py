# -*- coding: utf-8 -*-
from collections import namedtuple

Face = namedtuple('Face', ['normal', 'v1', 'v2', 'v3'])
"""
:obj:`namedtuple` of :obj:`tuple`: 4 x 3 tuple of tuples corresponding
    to the normal and the three points comprising a `Face`
"""