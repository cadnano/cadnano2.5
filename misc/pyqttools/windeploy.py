import sys
import os.path
from subprocess import Popen
import shutil
import glob

"""
If you install Qt5 / PyQt5 with pyqt5_check.py this will
create a relocatable build of this such that we can create a wheel

uses Qt5 windeployqt.exe tool for windows

PyQt5
https://hu-my.sharepoint.com/personal/nick_conway_wyss_harvard_edu/_layouts/15/guestaccess.aspx?guestaccesstoken=ngRHdMEIrmXYJ3W2dOIrs9L68nVLqeslinQHsbwcGCg%3d&docid=08daf362df3b14bf084973d85e4efd662
sip
https://hu-my.sharepoint.com/personal/nick_conway_wyss_harvard_edu/_layouts/15/guestaccess.aspx?guestaccesstoken=hHzHovkboxbgsl5ZH46X%2f4uSw52mVuRsTSJOONafsis%3d&docid=06d4c2a4776be46f8b0aad84f43c58532

"""
""" Install Qt5 libraries to environment root

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
        out_path (:obj:`str`, optional): location to copy renamed fixed module to
        old_rpath (:obj:`str`, optional): rpath to remove
    """
    if out_path:
        if os.path.exists(out_path):
            shutil.rmtree(out_path)
        shutil.copytree(in_path, out_path)
    else:
        out_path = in_path

    for file_name in file_list:
        cmd_add_rpath = ["windeployqt.exe",
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
    local_path = os.path.join(os.path.abspath(destination_path), 'PyQt5')
    dst_path = os.path.join(local_path, 'Qt')
    if os.path.exists(dst_path):
        shutil.rmtree(dst_path)
    plugin_path = os.path.join(dst_path, 'plugins')
    os.makedirs(plugin_path)
    folder_list = ['audio',
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
        src = os.path.join(local_path, folder)
        if os.path.exists(src):
            dst = os.path.join(plugin_path, folder)
            shutil.move(src, dst)
    for folder in ['resources', 'translations']:
        src = os.path.join(local_path, folder)
        if os.path.exists(src):
            dst = os.path.join(dst_path, folder)
            shutil.move(src, dst)
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
    shutil.copy2('winpyqtwheelsetup.py', os.path.join(destination_path, 'setup.py'))
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
        in_path = os.path.abspath(sys.argv[1])
        if not os.path.exists(in_path):
            raise ValueError("Input path not found")
    else:
        raise ValueError("wrong number of arguments")

    file_list = createPyQt5Module(in_path)
# end def
