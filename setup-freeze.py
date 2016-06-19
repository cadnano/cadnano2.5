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
    icon = "bin/logo.ico"
else:
    base = None
    executable_name = "cadnano"
    icon = "bin/logo.png"


executables = [
    Executable('bin/main.py',
               base=base,
               targetName=executable_name,
               icon=icon)
]

# Get the version number
version_ns = {}
ver_path = convert_path('cadnano/_version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), version_ns)

setup(name='cadnano',
      version=version_ns['__version__'],
      description='',
      options=dict(build_exe=build_options),
      executables=executables)
