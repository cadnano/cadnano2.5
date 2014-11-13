#!/usr/bin/env python
# encoding: utf-8
import sys
import os
LOCAL_DIR = os.path.dirname(os.path.realpath(__file__)) 
PROJECT_DIR = os.path.dirname(LOCAL_DIR)
sys.path.append(PROJECT_DIR)
sys.path.insert(0, '.')

"""
run with 

    python bin/main.py 2>/dev/null 

to push GObject warnings to /dev/null on linux
"""

if "-t" in sys.argv:
    os.environ['CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME'] = 'YES'

def main(args):
    print(args)
    from cadnano import initAppWithGui
    app = initAppWithGui(args)
    if "-p" in args:
        print("Collecting profile data into cadnano.profile")
        import cProfile
        cProfile.runctx('app.exec_()', None, locals(), filename='cadnano.profile')
        print("Done collecting profile data. Use -P to print it out.")
    elif "-P" in args:
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
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main(sys.argv)
