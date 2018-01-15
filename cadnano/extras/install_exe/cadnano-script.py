#!C:\Anaconda3\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'cadnano==2.5.0','console_scripts','cadnano'
__requires__ = 'cadnano==2.5.0'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('cadnano==2.5.0', 'console_scripts', 'cadnano')()
    )
