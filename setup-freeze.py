from cx_Freeze import setup, Executable
import sys
from distutils.util import convert_path

# Dependencies are automatically detected, but it might need
# fine tuning.

build_options = {"packages": [],
                 "excludes": [],
                 "includes": [],
                 "include_files": [],
                 "bin_path_includes": [],
                 "optimize": 2,
                 "silent": False,
                }

if sys.platform == 'win32':
    base = 'Win32GUI'
    executable_name = "cadnano.exe"
    build_options["include_msvcr"] = True
    icon = "logo/logo.ico"
else:
    base = None
    executable_name = "cadnano"
    icon = "logo/logo.png"


executables = [
    Executable('cadnano/bin/main.py',
               base=base,
               targetName=executable_name,
               icon=icon)
]

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

with open('new_readme.rst') as fd:
    LONG_DESCRIPTION = fd.read()

setup(name='cadnano',
      version=version_ns['__version__'],
      license=license,
      author=cadnano_ns['author'],
      author_email=cadnano_ns['email'],
      url=cadnano_ns['url'],
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
      options=dict(build_exe=build_options),
      executables=executables)
