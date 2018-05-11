# -*- coding: utf-8 -*-
"""
script for downloading and installing Qt5, sip, and PyQt5 into python
environment.  This is tested primarily in virtualenv using virtualenvwrapper
on OS X and Linux.  Uses wget on Linux and curl on OS X

For OS X you need Xcode installed


Files get placed in your virtualenv root path which
is at:

    distutils.sysconfig.BASE_PREFIX

Be sure to create your virtualenv with

    mkvirtualenv --always-copy <myenv>

or

    virtualenv --always-copy <myenv>

where <myenv> is the name you want for the environment
since sip needs to copy sip.h to your includes directory

Running:

    python getpyqt5.py

Should be all you need to do.

If something goes wrong mid-installing, this doesn't yet recover cleanly
so you might try deleting the '*.tar.gz' files and extracted folders and trying
again if you don't have write permissions correct and are installing at the
system level and say need to run:

    sudo python getpyqt5.py


Advanced stuff Moving Qt installs around

https://code.qt.io/cgit/installer-framework/installer-framework.git/tree/src/libs/installer/resources/files-to-patch-macx-emb-arm-qt5

and

https://code.qt.io/cgit/installer-framework/installer-framework.git/tree/src/libs/installer/qtpatch.cpp

In order to move Qt5 installation around you need to rewrite path strings in the
build binaries.  These files are:

    bin/qmake
    bin/lrelease
    bin/qdoc

    *.la
    *.prl
    *.pc
    *.pri
    *.cmake

So when you build the reference Qt, make the path crazy long so that the
patched strings will always be shorter and you can pad with zeros
"""

import sys
import distutils.sysconfig
import os
import subprocess
from subprocess import PIPE, Popen
import platform
import shutil

QT_VERSION = '5.10.0'
SIP_VERSION = '4.19.7'
PYQT5_VERSION = '5.10'
SIP_DEV_VERSION = '4.19.7.dev1801161332'
PYQT5_DEV_VERSION = '5.10.dev1801191340'
PYQT3D_VERSION = '5.10.dev1801191735'


def get_qt5(pyroot_path, qt5_path, is_static=False, clean=False, use_wget=False):
    """
    http://qt-project.org/doc/qt-5/qt-conf.html
    """

    qt5_zip = 'qt-everywhere-src-%s.tar.xz' % (QT_VERSION)
    qt5_src_path = 'qt-everywhere-src-%s' % (QT_VERSION)

    if clean:
        try:
            os.remove(os.path.join(pyroot_path, qt5_zip))
        except Exception:
            pass
        shutil.rmtree(os.path.join(pyroot_path, qt5_src_path), ignore_errors=True)
        shutil.rmtree(qt5_path, ignore_errors=True)

    static_str = '-static' if is_static else ''
    if os.path.exists(os.path.join(qt5_path, 'bin', 'qmake')):
        print(qt5_path)
        print("Already have Qt5")
        return

    if os.path.exists(os.path.join(pyroot_path, qt5_zip)):
        wget_str = ''
    else:
        if use_wget:
            wget_str = 'wget --output-document=%s \"http://download.qt.io/official_releases/qt/%s/%s/single/%s\";' %\
                       (qt5_zip, QT_VERSION[0:4], QT_VERSION, qt5_zip)
        else:
            # Qt has a redirect so use -L for curl
            wget_str = 'curl -L -O \"http://download.qt.io/official_releases/qt/%s/%s/single/%s\";' %\
                       (QT_VERSION[0:4], QT_VERSION, qt5_zip)
        print(wget_str)

    if os.path.exists(os.path.join(pyroot_path, qt5_src_path)):
        extract_str = ''
    else:
        extract_str = 'tar -xzf %s;' % (qt5_zip)

    cd_str = 'cd %s;' % (qt5_src_path)
    mkdir_str = 'mkdir build; cd build;'
    if sys.platform in ['linux', 'Linux']:
        config_str = '../configure %s ' % (static_str) +\
            '-opensource -prefix %s -confirm-license ' % (qt5_path) +\
            '-optimized-qmake -c++11 -system-sqlite ' +\
            '-no-pulseaudio -nomake examples -qt-xcb -no-xcb-xlib '
    else:
        # Get the OS X SDK
        # macsdk = "xcodebuild -showsdks | awk '/^$/{p=0};p; /macOS SDKs:/{p=1}' | tail -1 | cut -f3"
        xcb_proc = Popen(['xcodebuild', '-showsdks'], stdout=PIPE)
        awk_proc = Popen(['awk', '/^$/{p=0};p; /macOS SDKs:/{p=1}'], stdin=xcb_proc.stdout, stdout=PIPE)
        tail_proc = Popen(['tail', '-1'], stdin=awk_proc.stdout, stdout=PIPE)
        cut_proc = Popen(['cut', '-f3'], stdin=tail_proc.stdout, stdout=PIPE)
        xcb_proc.stdout.close()  # enable write error
        awk_proc.stdout.close()  # enable write error
        tail_proc.stdout.close()  # enable write error
        out, err = cut_proc.communicate()
        if not isinstance(out, str):
            # output of communicate is bytes
            macsdk_str = out.decode('utf-8').strip()
        else:
            macsdk_str = out.strip()

        # config_str = '../configure %s ' % (static_str) +\
        config_str = '../configure %s ' % (static_str) +\
            '-release -opensource -prefix %s -confirm-license ' % (qt5_path) +\
            '-c++std c++11 -sql-sqlite %s ' % (macsdk_str) +\
            '-no-glib -no-xcb-xlib ' +\
            '-no-xinput2 -nomake examples '

    config_str += \
        '-skip qtactiveqt -skip qtandroidextras -skip qtconnectivity ' +\
        '-skip qtdeclarative -skip qtdoc -skip qtenginio ' +\
        '-skip qtgraphicaleffects -skip qtlocation -skip qtquick1 ' +\
        '-skip qtquickcontrols -skip qtscript -skip qtsensors ' +\
        '-skip qtserialport -skip qttools -skip qttranslations ' +\
        '-skip qtwinextras ' +\
        '-skip qtxmlpatterns -skip qtwebchannel '
    if sys.platform in ['linux', 'Linux']:
        config_str += '-skip qtmacextras;'
    else:
        config_str += '-skip qtx11extras;'

    def qt5Build():
        print("Building qt5")
        qt_cmds = ['%s %s %s %s %s make -j4; make install' %
                   (wget_str,
                    extract_str,
                    cd_str,
                    mkdir_str,
                    config_str
                    )]
        qt5build = subprocess.Popen(qt_cmds, shell=True, cwd=pyroot_path)
        qt5build.wait()
    qt5Build()
# end def


def get_sip(pyroot_path, dev=False, is_static=False, use_wget=False):
    """
    sip copies sip.h to your python include path
    distutils.sysconfig.get_python_inc(prefix=sys.prefix))
    so if using virtualenv you need to make it with

    mkvirtualenv --always-copy in order to get write
    access
    to prevent issues with write access to the includes directory
    """
    static_str = '--static' if is_static else ''
    if dev:
        # https://www.riverbankcomputing.com/static/Downloads/sip/sip-4.19.7.dev1712162258.tar.gz
        sip_str = 'sip-%s' % (SIP_DEV_VERSION)
        sip_zip = '%s.tar.gz' % (sip_str)
        sip_url = "https://www.riverbankcomputing.com/static/Downloads/sip/%s" % (sip_zip)
    else:
        sip_str = 'sip-%s' % (SIP_VERSION)
        sip_zip = '%s.tar.gz' % (sip_str)

    if os.path.exists(os.path.join(pyroot_path, sip_zip)):
        print("Found", os.path.join(pyroot_path, sip_zip))
        wget_str = ''
    else:
        if dev:
            if use_wget:
                wget_str = "wget %s;" % (sip_url)
            else:
                wget_str = "curl -L -O %s;" % (sip_url)
        else:
            if use_wget:
                wget_str = 'wget http://sourceforge.net/projects/pyqt/files/sip/%s/%s;' %\
                           (sip_str, sip_zip)
            else:
                wget_str = 'curl -L -O http://sourceforge.net/projects/pyqt/files/sip/%s/%s;' %\
                           (sip_str, sip_zip)
    extract_str = 'tar -xzf %s;' % (sip_zip)
    cd_str = 'cd %s;' % (sip_str)
    config_str = 'python configure.py %s ' % static_str +\
                 '--incdir=%s;' % (distutils.sysconfig.get_python_inc(prefix=sys.prefix))
    # make_str = 'make; make install'

    def sipBuild():
        print("Building sip")
        qt_cmds = ['%s %s %s %s make -j2; make install;' %
                   (wget_str,
                    extract_str,
                    cd_str,
                    config_str
                    )]
        sipbuild = subprocess.Popen(qt_cmds, shell=True, cwd=pyroot_path)
        sipbuild.wait()
    sipBuild()
# end def


def get_pyqt5(pyroot_path, qt5_path, is_static=False, dev=False, use_wget=False):
    qmake_path = os.path.join(qt5_path, 'bin', 'qmake')
    static_str = '--static' if is_static else ''
    if dev:
        dev_str = PYQT5_DEV_VERSION
        pyqt5_str = 'PyQt5_gpl-%s' % (dev_str)
        pyqt5_zip = '%s.tar.gz' % (pyqt5_str)
        pyqt5_url = "https://www.riverbankcomputing.com/static/Downloads/PyQt5/%s" % (pyqt5_zip)
    else:
        pyqt5_str = 'PyQt-gpl-%s' % (PYQT5_VERSION)
        pyqt5_zip = '%s.tar.gz' % (pyqt5_str)
        pyqt5_url = 'http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-%s/%s' % (PYQT5_VERSION, pyqt5_zip)

    if os.path.exists(os.path.join(pyroot_path, pyqt5_zip)):
        wget_str = ''
    else:
        if use_wget:
            wget_str = 'wget %s;' % (pyqt5_url)
        else:
            wget_str = 'curl -L -O %s;' % (pyqt5_url)

    extract_str = 'tar -xzf %s;' % (pyqt5_zip)
    cd_str = 'cd %s;' % pyqt5_str
    config_str = 'python configure.py --verbose ' +\
        '--confirm-license %s ' % (static_str) +\
        '--qmake=%s ' % (qmake_path) +\
        '--no-designer-plugin --no-qml-plugin --no-qsci-api ' +\
        '--enable=QtCore --enable=QtGui --enable=QtSvg --enable=QtOpenGL ' +\
        '--enable=QtWidgets --enable=QtPrintSupport --enable=QtTest '
    if sys.platform in ['linux', 'linux']:
        config_str += '--enable=QtX11Extras;'
    else:
        config_str += '--enable=QtMacExtras --no-python-dbus;'

    def pyqt5Build():
        print("Building PyQt5")
        print('\n'.join([wget_str, extract_str, cd_str, config_str]))
        qt_cmds = ['%s %s %s %s make -j2; make install;' %
                   (wget_str,
                    extract_str,
                    cd_str,
                    config_str
                    )]
        # print(qt_cmds)
        pyqt5build = subprocess.Popen(qt_cmds, shell=True, cwd=pyroot_path)
        pyqt5build.wait()
    pyqt5Build()
# end def


def get_pyqt3d(pyroot_path, qt5_path, use_wget=False):
    qmake_path = os.path.join(qt5_path, 'bin', 'qmake')
    pyqt3d_str = 'PyQt3D_gpl-%s' % (PYQT3D_VERSION)
    pyqt3d_zip = '%s.tar.gz' % (pyqt3d_str)
    pyqt3d_url = "https://www.riverbankcomputing.com/static/Downloads/PyQt3D/%s" % (pyqt3d_zip)

    if os.path.exists(os.path.join(pyroot_path, pyqt3d_str)):
        wget_str = ''
    else:
        if use_wget:
            wget_str = 'wget %s;' % (pyqt3d_url)
        else:
            wget_str = 'curl -L -O %s;' % (pyqt3d_url)

    extract_str = 'tar -xzf %s;' % (pyqt3d_zip)
    cd_str = 'cd %s;' % pyqt3d_str

    config_str = 'python configure.py ' +\
        '--qmake=%s ' % (qmake_path)  # '--sipdir %s ' %

    def pyqt3dBuild():
        print("Building PyQt3D")
        print('\n'.join([wget_str, extract_str, cd_str, config_str]))
        qt_cmds = ['%s %s %s %s; make -j2; make install;' %
                   (wget_str,
                    extract_str,
                    cd_str,
                    config_str
                    )]
        print(qt_cmds)
        pyqt5build = subprocess.Popen(qt_cmds, shell=True, cwd=pyroot_path)
        pyqt5build.wait()
    pyqt3dBuild()
# end def


def checker(dev=False, do_clean_qt=False, is_static=False):
    try:
        if do_clean_qt:
            raise OSError("Just jumping out of this block for cleaning")
        import PyQt5  # noqa
        print("PyQt5 import success. No need to do anything.")
    except ImportError:
        print("Need to install PyQt5")
        if not platform.system() in ['Linux', 'Darwin']:
            raise OSError("Download PyQt5 installer from Riverbank software")
        else:
            if sys.platform in ['linux', 'Linux']:
                print("OS is Linux")
                use_wget = True    # use wget on Linux
            else:
                print("OS is macOS")
                use_wget = False    # use curl on OS X
            pyroot_path = distutils.sysconfig.BASE_PREFIX
            qt5_path = os.path.join(pyroot_path, 'Qt%s' % (QT_VERSION[0:4]))
            # clean = False
            get_qt5(pyroot_path, qt5_path,
                    is_static=is_static,
                    clean=do_clean_qt,
                    use_wget=use_wget)
            get_sip(pyroot_path,
                    dev=dev,
                    is_static=is_static,
                    use_wget=use_wget)
            get_pyqt5(pyroot_path, qt5_path,
                      dev=dev,
                      is_static=is_static,
                      use_wget=use_wget)
    try:
        import PyQt5.Qt3DCore  # noqa
        print("PyQt3D import success. No need to do anything.")
    except ImportError:
        if not platform.system() in ['Linux', 'Darwin']:
            raise OSError("Download PyQt3D installer from Riverbank software")
        else:
            if sys.platform in ['linux', 'Linux']:
                print("OS is Linux")
                use_wget = True    # use wget on Linux
            else:
                print("OS is macOS")
                use_wget = False    # use curl on OS X
            pyroot_path = distutils.sysconfig.BASE_PREFIX
            qt5_path = os.path.join(pyroot_path, 'Qt%s' % (QT_VERSION[0:4]))
            get_pyqt3d(pyroot_path, qt5_path,
                       use_wget=use_wget)
# end def


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanqt",
                        help="clean up the Qt install",
                        action="store_true")
    parser.add_argument("--static",
                        help="build Qt statically",
                        action="store_true")
    parser.add_argument("--dev",
                        help="use development versions of PyQt5 and SIP hardcoded here",
                        action="store_true")
    args = parser.parse_args()
    if args.dev:
        print("Building in dev mode")
    if args.cleanqt:
        print("Removing Qt5 files and redownloading if necessary")
    if args.static:
        print("Doing a static Qt5/PyQt5 build")
    checker(dev=args.dev, do_clean_qt=args.cleanqt, is_static=args.static)
