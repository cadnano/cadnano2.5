"""
Create sip wheel with
python setup.py bdist_wheel --plat-name macosx_10_10_x86_64 --python-tag cp35
python setup.py bdist_wheel --plat-name win_amd64 --python-tag cp35
"""

import sys
import os.path
import glob

from os.path import join as pjoin
from os.path import relpath as rpath

import distutils.sysconfig

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

PACKAGE_PATH = os.path.abspath(os.path.dirname(__file__))

if sys.platform == 'win32':
    data_files = [pjoin(PACKAGE_PATH, 'sip.pyd'), pjoin(PACKAGE_PATH, 'sip.pyi')]
    rel_path = '..\\..\\'
else:
    data_files = [pjoin(PACKAGE_PATH, 'sip.so')]
    rel_path = '../../'

setup(
    name='sip',
    version='4.18.1',
    license='GPLv3',
    url='https://www.riverbankcomputing.com/software/sip/download',
    description='sip',
    classifiers=[
        'Programming Language :: C',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    py_modules=['sipconfig', 'sipdistutils'],
    data_files=[(rel_path, data_files)],
    zip_safe=False,
)
