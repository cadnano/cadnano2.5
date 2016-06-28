#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__doc__ = '''
=========================================================
cadnano: DNA nanostructure CAD software
=========================================================

**cadnano**

Installation
------------

If you would like to install cadnano in your local Python environment
you may do so the setup.py script::

  $ python setup.py install
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
import distutils.command

from distutils.command.install import install as _install
from distutils import log as setup_log

from os.path import join as pjoin
from os.path import relpath as rpath

# with open('new_readme.rst') as fd:
#     LONG_DESCRIPTION = fd.read()
LONG_DESCRIPTION = __doc__

PACKAGE_PATH =          os.path.abspath(os.path.dirname(__file__))
MODULE_PATH =           pjoin(PACKAGE_PATH, 'cadnano')
INSTALL_EXE_PATH =      pjoin(MODULE_PATH, 'install_exe')
TESTS_PATH =            pjoin(MODULE_PATH, 'tests')
IMAGES_PATH1 =           pjoin(MODULE_PATH, 'gui', 'ui', 'mainwindow', 'images')
IMAGES_PATH2 =           pjoin(MODULE_PATH, 'gui', 'ui', 'dialogs', 'images')

# batch files and launch scripts

test_files = [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
                os.walk(TESTS_PATH) for f in files]
cn_files = [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
                os.walk(IMAGES_PATH1) for f in files]
cn_files += [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
                os.walk(IMAGES_PATH2) for f in files]

entry_points = {'console_scripts': [
        'cadnano = cadnano.bin.main:main',
        'cadnanoinstall = cadnano.install_exe.cadnanoinstall:post_install'
        ]}

if sys.platform == 'win32':
    path_scheme = {
        'scripts': 'Scripts',
    }
    cadnano_binaries = ['cadnano.exe']
    cn_files += [pjoin('install_exe', 'cadnano.exe')]
else:
    cadnano_binaries = []
    path_scheme = {
    'scripts': 'bin',
    }
cadnano_binary_fps = [pjoin(INSTALL_EXE_PATH, fn) for fn in cadnano_binaries]
script_path = os.path.join(sys.exec_prefix, path_scheme['scripts'])

# Insure that the copied binaries are executable
def makeExecutable(fp):
    ''' Adds the executable bit to the file at filepath `fp`
    '''
    mode = ((os.stat(fp).st_mode) | 0o555) & 0o7777
    setup_log.info("Adding executable bit to %s (mode is now %o)", fp, mode)
    os.chmod(fp, mode)
# en def

def _post_install(dir):
    new_cadnano_binary_fps = [pjoin( script_path, fn)
                                     for fn in cadnano_binaries]
    print(new_cadnano_binary_fps)
    print(cadnano_binary_fps)
    [shutil.copy2(o, d) for o, d in zip(cadnano_binary_fps,
                                           new_cadnano_binary_fps)]
    list(map(makeExecutable, new_cadnano_binary_fps))
# end def

class CNINSTALL(_install):
    def run(self):
        _install.run(self)
        self.execute(_post_install, (self.install_lib,),
                     msg="Running post install task")
# end class

if sys.argv[1] == 'install':
    cmdclass = {'install': CNINSTALL}
else:
    cmdclass = {'install': _install}

# Build the C API and Cython extensions
is_py_3 = int(sys.version_info[0] > 2)

exclude_list = ['*.genbank', '*.fasta',
                '*.tests.*', '*.tests', 'tests.*', 'tests', '*.test',
                'pyqtdeploy', 'nno2stl', '*.autobreak']
cn_packages = find_packages(exclude=exclude_list)

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
    packages=cn_packages,
    ext_modules=[],
    # test_suite='tests',
    zip_safe=False,
    install_requires=[
        # 'PyQt5>=5.6', Uncomment this when Official wheels get fixed
        'numpy>=1.10.0',
        'pandas>=0.18',
        'pytz>=2011k',
        'python-dateutil>=2'
    ],
    scripts=[],
    package_data={'cadnano': cn_files},
    entry_points=entry_points,
    cmdclass=cmdclass
)