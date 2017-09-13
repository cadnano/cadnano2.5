#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# make Wheels with:
# python setup.py bdist_wheel --plat-name macosx_10_10_x86_64 --python-tag cp35.cp36
# python setup.py bdist_wheel --plat-name win_amd64 --python-tag cp35.cp36
# twine upload dist/*

import os
import shutil
import sys
import ast
import re

from setuptools import find_packages
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from setuptools.command.install import install as _install
from distutils import log as setup_log

from os.path import join as pjoin
from os.path import relpath as rpath

# Begin modified code from Flask's version getter
# BSD license
# Copyright (c) 2015 by Armin Ronacher and contributors.
# https://github.com/pallets/flask
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('cadnano/__init__.py', 'rb') as initfile:
    version = str(ast.literal_eval(_version_re.search(
                                   initfile.read().decode('utf-8')).group(1)))
# end Flask derived code

__doc__ = '''
===================================================================
cadnano: computer-aided design tool for creating DNA nanostructures
===================================================================

**cadnano** %s beta

Installation
------------

If you would like to install cadnano in your local Python environment
you may do so the setup.py script::

  $ python setup.py install

or::

  $ pip install cadnano
''' % (version)

LONG_DESCRIPTION = __doc__

PACKAGE_PATH = os.path.abspath(os.path.dirname(__file__))
MODULE_PATH = pjoin(PACKAGE_PATH, 'cadnano')
INSTALL_EXE_PATH = pjoin(MODULE_PATH, 'install_exe')
TESTS_PATH = pjoin(MODULE_PATH, 'tests')
TEST_DATA_PATH = pjoin(TESTS_PATH, 'data')
IMAGES_PATH1 = pjoin(MODULE_PATH, 'gui', 'ui', 'mainwindow', 'images')
IMAGES_PATH2 = pjoin(MODULE_PATH, 'gui', 'ui', 'dialogs', 'images')

# batch files and launch scripts

test_files = [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
              os.walk(TESTS_PATH) for f in files]
test_data_files = [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
                   os.walk(TEST_DATA_PATH) for f in files]
cn_files = [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
            os.walk(IMAGES_PATH1) for f in files]
cn_files += [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
             os.walk(IMAGES_PATH2) for f in files]
cn_files += test_files + test_data_files

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
    path_scheme = {'scripts': 'bin'}
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
    new_cadnano_binary_fps = [pjoin(script_path, fn) for fn in cadnano_binaries]
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

if len(sys.argv) > 0 and sys.argv[1] == 'install':
    cmdclass = {'install': CNINSTALL}
else:
    cmdclass = {'install': _install}

# Build the C API and Cython extensions
is_py_3 = int(sys.version_info[0] > 2)

exclude_list = ['*.genbank', '*.fasta',
                '*.tests.*', '*.tests', 'tests.*', 'tests', '*.test',
                'pyqtdeploy', 'nno2stl', '*.autobreak']
cn_packages = find_packages(exclude=exclude_list)

install_requires = ['sip>=4.19',
j                   'PyQt5>=5.9.0',
                    'numpy>=1.10.0',
                    'pandas>=0.18',
                    'pytz>=2011k',
                    'python-dateutil>=2',
                    'termcolor>=1.1.0'
                    ]

if sys.platform == 'win32':
    install_requires += ['pypiwin32', 'winshell']

setup(
    name='cadnano',
    version=version,
    license='multiple',
    author='Nick Conway, Shawn Douglas',
    author_email='a.grinner@gmail.com',
    url='https://github.com/cadnano/cadnano2.5',
    description='computer-aided design tool for creating DNA nanostructures',
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'Programming Language :: C',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'License :: OSI Approved :: BSD License'
    ],
    packages=cn_packages,
    ext_modules=[],
    zip_safe=False,
    install_requires=install_requires,
    scripts=[],
    package_data={'cadnano': cn_files},
    entry_points=entry_points,
    cmdclass=cmdclass,
    platforms='any'
)
