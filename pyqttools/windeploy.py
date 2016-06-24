import sys
import os.path
from subprocess import PIPE, Popen, check_output
import shutil
import glob

"""
If you install Qt5 / PyQt5 with pyqt5_check.py this will
create a relocatable build of this such that we can create a wheel

"""
""" Install Qt5 libraries to environment root

Use otool -l <file> to look for

LC_RPATH for rpaths to delete
and use `install_name_tool` `-add_rpath` and `-delete_rpath` to change it

change LC_ID_DYLIB to change the name of the LC_ID_DYLIB which is a little
harder to do

you can list files only with
otool -L <file> | awk '{print $1}'

"""

def getsitePackagesPath():
    if hasattr(sys, 'real_prefix'):
        # virtualenv
        for path in sys.path:
            sp_paths = [p for p in sys.path if p.endswith('site-packages')]
            if sp_paths:
                return sp_paths[-1]
            else:
                raise OSError("no site-packages found")
    else:
        import site
        sp_paths = [p for p in site.getsitepackages() if p.endswith('site-packages')]
        if sp_paths:
            return sp_paths[-1]
# end def

site_packages_path = getsitePackagesPath()

def installRename(file_list, in_path, out_path=""):
    """ For renaming PyQt5 *.so rpaths such that the Qt5 libraries will
    be located in the Python root of the environment either
    or bin folder.

    LC_ID_DYLIB is also renamed to be a relative path but I think this is
    unnecessary

    Args:
        in_path (str): location of PyQt5 build
        out_path (Optional[str]): location to copy renamed fixed module to
        old_rpath (Optional[str]): rpath to remove
    """
    if out_path:
        if os.path.exists(out_path):
            shutil.rmtree(out_path)
        shutil.copytree(in_path, out_path)
    else:
        out_path = in_path

    for file_name in file_list:
        cmd_add_rpath = ["windeploy.exe",
                        os.path.join(out_path, file_name)
                        ]
        cmd_add_rpath = ' '.join(cmd_add_rpath)
        renameproc = Popen(cmd_add_rpath, shell=True,
                                        cwd=out_path)
        renameproc.wait()
# end for

def moveExtras(destination_path):
    """
    Copy resourses, plugins like, translations}
    extras to Qt/[resourses, plugins, translations]
    a la the official wheels
    """
    destination_path = os.path.abspath(destination_path)
    dst_path = os.path.join(destination_path, 'Qt')
    if os.path.exists(dst_path):
        shutil.rmtree(dst_path)
    plugin_path = os.path.join(dst_path, 'Qt', 'plugins')
    os.makedirs(plugin_path)
    folder_list = [ 'audio',
                    'bearer',
                    'generic',
                    'geoservices',
                    'iconengines',
                    'imageformats',
                    'mediaservice',
                    'platforms',
                    'playlistformats',
                    'position',
                    'printsupport',
                    'sceneparsers',
                    'sensorgestures',
                    'sensors',
                    'sqldrivers']
    for folder in folder_list:
        src = os.path.join(destination_path, folder)
        if os.path.exists(src):
            dst = os.path.join(plugin_path, folder)
            shutil.copytree(src, dst)
    for folder in ['resources', 'translations']:
        src = os.path.join(destination_path, folder)
        if os.path.exists(src):
            dst = os.path.join(dst_path, folder)
            shutil.copytree(src, dst)
    # end for
# end def

def copyPyQt5(destination_path):
    """ Location to put a folder called PyQt5
    """
    destination_path = os.path.abspath(destination_path)
    dst_path = os.path.join(destination_path, 'PyQt5')
    if os.path.exists(dst_path):
        shutil.rmtree(dst_path)
    src = os.path.join(site_packages_path, 'PyQt5')
    if not os.path.exists(src):
        raise ValueError("Source PyQt5 %s does not exist" % (src))
    shutil.copytree(src, dst_path)

    filepath_list = glob.glob(os.path.join(dst_path, '*.pyd'))
    file_list = [os.path.basename(x) for x in filepath_list]
    # copy special init which fixes Library path
    shutil.copy2('__wininit__.py', os.path.join(dst_path, '__init__.py'))
    return dst_path, file_list
# end def

def createPyQt5Module(destination_path):
    if not os.path.exists(destination_path):
        raise ValueError("%s must exist" % (destination_path))
    dst_path, file_list = copyPyQt5(destination_path)
    installRename(file_list, dst_path)
    moveExtras(destination_path)
    return [os.path.splitext(x)[0] for x in file_list]
# end def

if __name__ == '__main__':
    if len(sys.argv) > 1:
        in_path =  os.path.abspath(sys.argv[1])
        if not os.path.exists(in_path):
            raise ValueError("Input path not found")
    else:
        raise ValueError("wrong number of arguments")

    file_list = createPyQt5Module(in_path)
#end def