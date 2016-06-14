#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
=========================================================
cadnano: DNA nanostructure CAD software
=========================================================

**cadnano**

Installation
------------

If you would like to install cadnano in your local Python environment
you may do so using either pip or the setup.py script::

  $ pip install cadnano
            or
  $ python setup.py install

'''

import os
import shutil
import subprocess
import sys

try:
    from setuptools import setup, Extension
    from setuptools.command import install_lib, sdist, build_ext
    from setuptools import log as setup_log
except ImportError:
    from distutils.core import setup, Extension
    from distutils.command import install_lib, sdist, build_ext
    from distutils import log as setup_log


from os.path import join as pjoin
from os.path import relpath as rpath

# from Cython.Build import cythonize

with open('new_readme.rst') as fd:
    LONG_DESCRIPTION = fd.read()


PACKAGE_PATH =          os.path.abspath(os.path.dirname(__file__))
MODULE_PATH =           pjoin(PACKAGE_PATH, 'cadnano')
TESTS_PATH =            pjoin(MODULE_PATH, 'tests')

CADNANO_BUILT = False


# Find all necessary primer3 binaries / data files to include with the package
cadnano_binaries = ['oligotm', 'ntthal', 'primer3_core']
cadnano_binary_fps = [pjoin(PACKAGE_PATH, fn) for fn in cadnano_binaries]

test_files = [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
                os.walk(TESTS_PATH) for f in files]

cadnano_files = test_files


# Insure that the copied binaries are executable
def makeExecutable(fp):
    ''' Adds the executable bit to the file at filepath `fp`
    '''
    mode = ((os.stat(fp).st_mode) | 0o555) & 0o7777
    setup_log.info("Adding executable bit to %s (mode is now %o)", fp, mode)
    os.chmod(fp, mode)


class CustomInstallLib(install_lib.install_lib):

    def run(self):
        global CADNANO_BUILT
        install_lib.install_lib.run(self)
        # Copy binary files over to build directory and make executable
        if not self.dry_run:
            if not CADNANO_BUILT:
                pass
            new_cadnano_binary_fps = [pjoin(self.install_dir, 'cadnano', 'bin',
                                 , fn) for fn in cadnano_binaries]
            [shutil.copyfile(o, d) for o, d in zip(cadnano_binary_fps,
                                                   new_cadnano_binary_fps)]
            list(map(makeExecutable, new_cadnano_binary_fps))


class CustomSdist(sdist.sdist):

    def run(self):
        global CADNANO_BUILT
        # Clean up the cadnano build prior to sdist command to remove
        # binaries and object/library files
        CADNANO_BUILT = False
        sdist.sdist.run(self)


class CustomBuildExt(build_ext.build_ext):

    def run(self):
        global CADNANO_BUILT
        # Build primer3 prior to building the extension, if not already built
        if not self.dry_run and not CADNANO_BUILT:
            CADNANO_BUILT = True
        build_ext.build_ext.run(self)


# Build the C API and Cython extensions

if ('build_ext' in sys.argv or 'install' in sys.argv):
    if not CADNANO_BUILT:
        CADNANO_BUILT = True

is_py_3 = int(sys.version_info[0] > 2)

# Insure that we don't include the built Cython module in the dist
if 'sdist' in sys.argv:
    # remove all *.c file
    c_files = []
    for fn in c_files:
        os.remove(os.path.join(MODULE_PATH, fn))


setup(
    name='cadnano',
    version='2.5.0',
    license='GPLv2',
    author='Nick Conway, Shawn Douglas',
    author_email='a.grinner@gmail.com',
    url='https://github.com/cadnano/cadnano2.5',
    description='radnano',
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'Programming Language :: C',
        'Programming Language :: Cython',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'
    ],
    packages=['cadnano'],
    ext_modules=[],
    package_data={'cadnano': cadnano_files},
    cmdclass={'install_lib': CustomInstallLib, 'sdist': CustomSdist,
              'build_ext': CustomBuildExt},
    test_suite='tests',
    zip_safe=False,
    install_requires=[
        'PyQt5>=5.6',
        'numpy>=1.10.0',
        'pandas>=0.21',
        'pytz>=2011k',
        'python-dateutil >= 2'
    ]
)
