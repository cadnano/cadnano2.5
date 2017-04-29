#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
"""
From http://stackoverflow.com/questions/8015225/
How-to-force-sphinx-to-use-python-3-x-interpreter
"""

import sys

if __name__ == '__main__':
    from sphinx import main, make_main
    if sys.argv[1:2] == ['-M']:
        sys.exit(make_main(sys.argv))
    else:
        sys.exit(main(sys.argv))