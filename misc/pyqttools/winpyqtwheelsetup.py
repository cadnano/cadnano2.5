
"""
Create wheel with
python setup.py bdist_wheel --plat-name win_amd64 --python-tag cp35
"""

import os.path
import glob

from os.path import join as pjoin
from os.path import relpath as rpath

from setuptools import find_packages

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup

PACKAGE_PATH = os.path.abspath(os.path.dirname(__file__))
MODULE_PATH = pjoin(PACKAGE_PATH, 'PyQt5')
Qt5_PATH = pjoin(MODULE_PATH, 'Qt')
UIC_PATH = pjoin(MODULE_PATH, 'uic')

search_path = pjoin(MODULE_PATH, '*.pyd')
filepath_list = glob.glob(search_path)
file_list = [os.path.basename(x) for x in filepath_list]

search_path = pjoin(MODULE_PATH, '*.pyi')
filepath_list = glob.glob(search_path)
file_list += [os.path.basename(x) for x in filepath_list]

search_path = pjoin(MODULE_PATH, '*.dll')
filepath_list = glob.glob(search_path)
file_list += [os.path.basename(x) for x in filepath_list]

package_files = [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
                 os.walk(Qt5_PATH) for f in files]

package_files += [rpath(pjoin(root, f), MODULE_PATH) for root, _, files in
                  os.walk(UIC_PATH) for f in files]

packages = find_packages()
setup(
    name='PyQt5',
    version='5.6.1',
    license='GPLv3',
    url='https://www.riverbankcomputing.com/software/pyqt/download5',
    description='PyQt5',
    classifiers=[
        'Programming Language :: C',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    packages=packages,
    package_data={'PyQt5': package_files + file_list},
    zip_safe=False,
)
