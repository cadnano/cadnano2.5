#!/usr/bin/env python3
# encoding: utf-8
import sys
import os
# import logging
# logger = logging.getLogger(__name__)
LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(LOCAL_DIR)
sys.path.append(ROOT_DIR)
sys.path.insert(0, '.')

PROJECT_DIR = os.path.dirname(ROOT_DIR)

# CADNANO_DEFAULT_DOCUMENT = 'simple.json'

# os.environ['CADNANO_DEFAULT_DOCUMENT'] = os.path.join(PROJECT_DIR, 'cadnano',
#                                             'tests', 'data',
#                                             CADNANO_DEFAULT_DOCUMENT)

"""
run with:

    python bin/main.py 2>/dev/null

to push GObject warnings to /dev/null on linux
"""

if "-t" in sys.argv:
    os.environ['CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME'] = 'YES'


def main(argv=None):
    # print(argv)
    from cadnano import initAppWithGui
    # Things are a lot easier if we can pass None instead of sys.argv and only fall back to sys.argv when we need to.
    app = initAppWithGui(argv, do_exec=False)
    if app.argns.profile:
        print("Collecting profile data into cadnano.profile")
        import cProfile
        cProfile.runctx('app.exec_()', None, locals(), filename='cadnano.profile')
        print("Done collecting profile data. Use -P to print it out.")
    if not app.argns.profile and not app.argns.print_stats:
        sys.exit(app.exec_())
    if app.argns.print_stats:
        from pstats import Stats
        s = Stats('cadnano.profile')
        print("Internal Time Top 10:")
        s.sort_stats('cumulative').print_stats(10)
        print("\nTotal Time Top 10:")
        s.sort_stats('time').print_stats(10)
    # elif "-t" in sys.argv:
    #     print("running tests")
    #     from tests.runall import main as runTests
    #     runTests(useXMLRunner=False)

if __name__ == '__main__':
    main()
