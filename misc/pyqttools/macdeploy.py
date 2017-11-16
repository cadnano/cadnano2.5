import sys
import os.path
import shutil
import glob
from subprocess import Popen, check_output

pjoin = os.path.join

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
        return site.getsitepackages()[0]
# end def


QT_VERSION = "5.5"
PY_VERSION = "%d.%d" % (sys.version_info[0], sys.version_info[1])
python_root = os.path.abspath(sys.exec_prefix)
site_packages_path = getsitePackagesPath()


def getLinkedInfo(file_name, do_print=False):
    """ Wrapper for `otool -l`
    """
    output = check_output(["otool -l %s | awk '{print $2}';" % file_name], shell=True)
    split_out = output.decode('utf8').split('\n')
    paths = {'LC_RPATH': [], 'LC_ID_DYLIB': []}
    for i, line in enumerate(split_out):
        if line == 'LC_RPATH':
            paths['LC_RPATH'].append(split_out[i + 2].strip())
        elif line == 'LC_ID_DYLIB':
            paths['LC_ID_DYLIB'].append(split_out[i + 2].strip())
    if do_print:
        print(paths)
    return paths
# end def


def installRename(file_list, in_path, out_path="", old_rpath=""):
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
        if old_rpath:
            cmd_delete_rpath = ["install_name_tool",
                                "-delete_rpath",
                                old_rpath,
                                pjoin(out_path, file_name)
                                ]
            cmd_delete_rpath = ' '.join(cmd_delete_rpath)
            renameproc = Popen(cmd_delete_rpath, shell=True, cwd=out_path)
            renameproc.wait()
        cmd_add_rpath = ["install_name_tool",
                         "-add_rpath",
                         "@loader_path/Qt/lib",
                         pjoin(out_path, file_name)
                         ]
        cmd_add_rpath = ' '.join(cmd_add_rpath)
        renameproc = Popen(cmd_add_rpath, shell=True, cwd=out_path)
        renameproc.wait()

        cmd_id = ["install_name_tool",
                  "-id",
                  "@executable_path/lib/python{}/site-packages/PyQt5/{}".format(PY_VERSION, file_name),
                  pjoin(out_path, file_name)
                  ]
        cmd_id = ' '.join(cmd_id)
        idproc = Popen(cmd_id, shell=True, cwd=out_path)
        idproc.wait()
# end for


def copyFrameworks(destination_path, get_translations=False):
    """
    Copy Qt/{lib, plugins, translations}
    """
    destination_path = os.path.abspath(destination_path)
    dst_path = pjoin(destination_path, 'Qt')
    if os.path.exists(dst_path):
        shutil.rmtree(dst_path)

    plugin_path = 'Qt%s/plugins' % (QT_VERSION)
    shutil.copytree(os.path.join(python_root, plugin_path),
                    pjoin(dst_path, 'plugins'))
    if get_translations:
        translations_path = 'Qt%s/translations' % (QT_VERSION)
        shutil.copytree(pjoin(python_root, translations_path),
                        pjoin(dst_path, 'translations'))

    check_path = pjoin(python_root, 'Qt{}/lib/*.framework'.format(QT_VERSION))
    filepath_list = glob.glob(check_path)
    file_list = [os.path.splitext(os.path.basename(x))[0] for x in filepath_list]

    qt_src = "Qt{}/lib/{}.framework/Versions/5/{}"
    src_path = pjoin(python_root, qt_src)
    dst_path = pjoin(destination_path, qt_src)
    for file_name in file_list:
        src = src_path.format(QT_VERSION, file_name, file_name)
        dst = dst_path.format('', file_name, file_name)
        this_dst_dir = os.path.dirname(dst)
        if not os.path.exists(this_dst_dir):
            os.makedirs(this_dst_dir)
        shutil.copy2(src, dst)
    # end for
# end def


def copyPyQt5(destination_path):
    """ Location to put a folder called PyQt5
    """
    destination_path = os.path.abspath(destination_path)
    dst_path = pjoin(destination_path, 'PyQt5')
    if os.path.exists(dst_path):
        shutil.rmtree(dst_path)
    src = pjoin(site_packages_path, 'PyQt5')
    if not os.path.exists(src):
        raise ValueError("Source PyQt5 %s does not exist" % (src))
    shutil.copytree(src, dst_path)

    filepath_list = glob.glob(dst_path + '/*.so')
    file_list = [os.path.basename(x) for x in filepath_list]
    shutil.copy2('__wininit__.py', pjoin(dst_path, 'PyQt5', '__init__.py'))
    return dst_path, file_list
# end def


def createPyQt5Module(destination_path):
    if not os.path.exists(destination_path):
        raise ValueError("%s must exist" % (destination_path))
    dst_path, file_list = copyPyQt5(destination_path)
    copyFrameworks(dst_path)
    check_rpath_file = os.path.join(dst_path, file_list[0])
    path_dict = getLinkedInfo(check_rpath_file)
    rpath = path_dict['LC_RPATH'][0]
    installRename(file_list, dst_path, old_rpath=rpath)
    return [os.path.splitext(x)[0] for x in file_list]
# end def


cn_packages = find_packages(exclude=exclude_list)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        in_path = os.path.abspath(sys.argv[1])
        if not os.path.exists(in_path):
            raise ValueError("Input path not found")
    else:
        raise ValueError("wrong number of arguments")

    file_list = createPyQt5Module(in_path)
# end def
