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

Use rcedit to change icon
'''

import os
import shutil
import subprocess
import sys

from setuptools import find_packages
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension
from distutils.command import install_lib, sdist, build_ext, install_scripts
from distutils.command.install import install as _install
from distutils import log as setup_log
from distutils.util import convert_path

from os.path import join as pjoin
from os.path import relpath as rpath

# from Cython.Build import cythonize

with open('new_readme.rst') as fd:
    LONG_DESCRIPTION = fd.read()


PACKAGE_PATH =          os.path.abspath(os.path.dirname(__file__))
MODULE_PATH =           pjoin(PACKAGE_PATH, 'cadnano')
BIN_PATH =              pjoin(MODULE_PATH, 'install_exe')
TESTS_PATH =            pjoin(MODULE_PATH, 'tests')

# batch files and launch scripts


test_files = [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
                os.walk(TESTS_PATH) for f in files]

# cadnano_files = [] + cadnano_binary_fps


# Insure that the copied binaries are executable
def makeExecutable(fp):
    ''' Adds the executable bit to the file at filepath `fp`
    '''
    mode = ((os.stat(fp).st_mode) | 0o555) & 0o7777
    setup_log.info("Adding executable bit to %s (mode is now %o)", fp, mode)
    os.chmod(fp, mode)


if sys.platform == 'win32':
    path_scheme = {
        'scripts': 'Scripts',
    }
    cadnano_binaries = ['cadnano.exe']
    cadnano_binary_fps = [pjoin(BIN_PATH, fn) for fn in cadnano_binaries]
else:
    path_scheme = {
    'scripts': 'bin',
    }
script_path = os.path.join(sys.exec_prefix, path_scheme['scripts'])

# class CustomInstallLib(install_lib.install_lib):

#     def run(self):
#         install_lib.install_lib.run(self)
#         # Copy binary files over to build directory and make executable
#         if not self.dry_run:
#             new_cadnano_binary_fps = [pjoin( script_path, fn)
#                                              for fn in cadnano_binaries]
#             print(new_cadnano_binary_fps)
#             print(cadnano_binary_fps)
#             [shutil.copyfile(o, d) for o, d in zip(cadnano_binary_fps,
#                                                    new_cadnano_binary_fps)]
#             list(map(makeExecutable, new_cadnano_binary_fps))

def _post_install(dir):
    new_cadnano_binary_fps = [pjoin( script_path, fn)
                                     for fn in cadnano_binaries]
    print(new_cadnano_binary_fps)
    print(cadnano_binary_fps)
    [shutil.copyfile(o, d) for o, d in zip(cadnano_binary_fps,
                                           new_cadnano_binary_fps)]
    list(map(makeExecutable, new_cadnano_binary_fps))


class myinstall(_install):
    def run(self):
        _install.run(self)
        self.execute(_post_install, (self.install_lib,),
                     msg="Running post install task")

# Build the C API and Cython extensions
is_py_3 = int(sys.version_info[0] > 2)

# Insure that we don't include the built Cython module in the dist
if 'sdist' in sys.argv:
    # remove all *.c file
    c_files = []
    for fn in c_files:
        os.remove(os.path.join(MODULE_PATH, fn))


exclude_list = ['*.genbank', '*.fasta',
                '*.tests.*', '*.tests', 'tests.*', 'tests', '*.test',
                'pyqtdeploy', 'nno2stl', '*.autobreak']
cn_packages = find_packages(exclude=exclude_list)
# print(cn_packages)

# Get the version number
version_ns = {}
ver_path = convert_path('cadnano/_version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), version_ns)

# Get cadnano variables
cadnano_ns = {}
cadnano_path = convert_path('cadnano/_info.py')
with open(cadnano_path) as cadnano_file:
    exec(cadnano_file.read(), cadnano_ns)

setup(
    name='cadnano',
    version=version_ns['__version__'],
    license=license,
    author=cadnano_ns['author'],
    author_email=cadnano_ns['email'],
    url=cadnano_ns['url'],
    description='radnano',
    long_description=LONG_DESCRIPTION,
    classifiers=cadnano_ns['classifiers'],
    cmdclass={'install': myinstall},
    packages=cn_packages,
    ext_modules=[],
    # test_suite='tests',
    zip_safe=False,
    install_requires=[
        'PyQt5>=5.6',
        'numpy>=1.10.0',
        'pandas>=0.18',
        'pytz>=2011k',
        'python-dateutil>=2'
    ],
    entry_points={
        'console_scripts': [
            'cadnano = cadnano.bin.main:main',
        ],
    }

)
