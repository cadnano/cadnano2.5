import sys
import distutils
import os
import subprocess
import platform

QT_VERSION = '5.3.2'
SIP_VERSION = '4.16.4'
PYQT5_VERSION = '5.3.2'

def get_qt5(pyroot_path, qt5_path, is_static=False):
    static_str = '-static' if is_static else ''
    if os.path.exists(qt5_path):
        print("Already have Qt5")
        return

    qt5_zip = 'qt-everywhere-opensource-src-%s.tar.gz' % (QT_VERSION)
    qt5_src_path = 'qt-everywhere-opensource-src-%s' % (QT_VERSION)

    if os.path.exists(os.path.join(pyroot_path, qt5_zip)):
        wget_str = ''
    else:
        wget_str = 'wget --output-file=%s http://download.qt-project.org/official_releases/qt/%s/%s/single/%s;' %\
                    (qt5_zip, QT_VERSION[0:3], QT_VERSION, qt5_zip)
    
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
        config_str = '../configure %s ' % (static_str) +\
            '-opensource -prefix %s -confirm-license ' % (qt5_path) +\
            '-optimized-qmake -c++11 -system-sqlite -sdk macosx10.9 ' +\
            '-no-glib -no-alsa -no-gtkstyle -no-pulseaudio -no-xcb-xlib ' +\
            '-no-xinput2 -no-dbus -nomake examples '

    config_str += \
        '-skip qtactiveqt -skip qtandroidextras -skip qtconnectivity ' +\
        '-skip qtdeclarative -skip qtdoc -skip qtenginio ' +\
        '-skip qtgraphicaleffects -skip qtlocation -skip qtquick1 ' +\
        '-skip qtquickcontrols -skip qtscript -skip qtsensors ' +\
        '-skip qtserialport -skip qttools -skip qttranslations ' +\
        '-skip qtwebkit -skip qtwebkit-examples -skip qtwinextras ' +\
        '-skip qtxmlpatterns '
    if sys.platform in ['linux', 'Linux']:
        config_str += '-skip qtmacextras;'
    else:
        config_str += '-skip qtx11extras;'

    def qt5Build():
        print("Building qt5")
        qt_cmds = ['%s %s %s %s %s make -j4; make install' %\
                    (   wget_str, 
                        extract_str,
                        cd_str,
                        mkdir_str,
                        config_str
                    )]
        qt5build = subprocess.Popen(qt_cmds, shell=True, 
                                        cwd=pyroot_path)
        qt5build.wait()
    qt5Build()

    # if sys.platform in ['linux', 'Linux']:
    #     qt_setup_file = 'qt-opensource-linux-x64-%s.run' % (QT_VERSION)
    #     wget_str = 'wget http://download.qt-project.org/official_releases/qt/%s/%s/%s' %
    #                                 (QT_VERSION[0:3], QT_VERSION, qt_setup_file)
    #     './%s' % (qt_setup_file)
    # else:
    #     qt_setup_file = 'qt-opensource-mac-x64-clang-%s.dmg' % (QT_VERSION)
    #     wget_str = 'wget http://download.qt-project.org/official_releases/qt/%s/%s/%s' %
    #                                 (QT_VERSION[0:3], QT_VERSION, qt_setup_file)
    # raise OSError("Run %s and install to %s and rerun setup" %
    #                         (qt_setup_file, qt5_path) )
# end def

def get_sip(pyroot_path, is_static=False):
    """
    sip copies sip.h to your python include path
    distutils.sysconfig.get_python_inc(prefix=sys.prefix))
    so if using virtualenv you need to make it with

    mkvirtualenv -p /path/to/python/bin/python in order to get write
    access
    """
    static_str = '--static' if is_static else ''
    sip_str = 'sip-%s' % (SIP_VERSION)
    sip_zip = '%s.tar.gz' % (sip_str)

    if os.path.exists(os.path.join(pyroot_path, sip_zip)):
        wget_str = ''
    else:
        wget_str = 'wget http://sourceforge.net/projects/pyqt/files/sip/%s/%s;' %\
                (sip_str, sip_zip)
    extract_str = 'tar -xzf %s;' % (sip_zip)
    cd_str = 'cd %s;' % (sip_str)
    config_str = 'python configure.py %s ' % static_str +\
                '--incdir=%s;' % (distutils.sysconfig.get_python_inc(prefix=sys.prefix))
    make_str = 'make; make install'

    def sipBuild():
        print("Building sip")
        qt_cmds = ['%s %s %s %s make -j2; make install;' %\
                    (   wget_str, 
                        extract_str,
                        cd_str,
                        config_str
                    )]
        sipbuild = subprocess.Popen(qt_cmds, shell=True, 
                                        cwd=pyroot_path)
        sipbuild.wait()
    sipBuild()
# end def

def get_pyqt5(pyroot_path, qt5_path, is_static=False):
    qmake_path = os.path.join(qt5_path, 'bin', 'qmake')
    static_str = '--static' if is_static else ''

    if sys.platform in ['linux', 'Linux']:  # hack for broken configure.py in 5.3.2
        PYQT5_VERSION = '5.4-snapshot-837edec02d98'
        pyqt5_str = 'PyQt-gpl-%s' % (PYQT5_VERSION)
        pyqt5_zip = '%s.tar.gz' % (pyqt5_str)
        pyqturl = 'http://www.riverbankcomputing.com/static/Downloads/PyQt5/%s' %\
            (pyqt5_zip)
    else:
        pyqt5_str = 'PyQt-gpl-%s' % (PYQT5_VERSION)
        pyqt5_zip = '%s.tar.gz' % (pyqt5_str)
        pyqturl = 'http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-%s/%s;' %\
                        (PYQT5_VERSION, pyqt5_zip)

    # os.environ['QTDIR'] = qt5_path
    # os.environ['QMAKESPEC'] = os.path.join(qt5_path, 'mkspecs', 'macx-clang')
    # os.environ['DYLD_LIBRARY_PATH'] = ';%s/lib' % qt5_path
    if os.path.exists(os.path.join(pyroot_path, pyqt5_zip)):
        wget_str = ''
    else:
        wget_str = 'wget %s;' % (pyqturl)

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
        config_str += '--enable=QtMacExtras;'

    def pyqt5Build():
        print("Building pyqt5")
        qt_cmds = ['%s %s %s %s make -j2; make install;' %\
                    (   wget_str,
                        extract_str,
                        cd_str,
                        config_str
                    )]
        pyqt5build = subprocess.Popen(qt_cmds, shell=True, 
                                        cwd=pyroot_path)
        pyqt5build.wait()
    pyqt5Build()
# end def    

"""
http://qt-project.org/doc/qt-5/qt-conf.html
"""

def checker():
    is_static = False
    try:
        raise OSError()
        import PyQt5
        print("import success!")
    except:
        print("need to install")
        if not platform.system() in ['Linux', 'Darwin']:
            raise OSError("Download PyQt5 installer from Riverbank software")
        else:
            print("OS is Linux or Mac")
            pyroot_path = distutils.sysconfig.BASE_PREFIX
            qt5_path = os.path.join(pyroot_path, 'Qt%s' % (QT_VERSION[0:3]) )
            get_qt5(pyroot_path, qt5_path, is_static=is_static)
            try:
                import sip
            except:
                get_sip(pyroot_path, is_static=is_static)
            get_pyqt5(pyroot_path, qt5_path, is_static=is_static)
# end def

if __name__ == '__main__':
    checker()
