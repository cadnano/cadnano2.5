Generally there will be some sort of missing dependecy if you try to just install
PyQt with a blanket `python configure.py`.  Therefore, it is important to select only
the modules you need, as this will speed up the build time anyway.

On Mac and Linux, create a virtualenv and install inside of there.  No need
to install to system level python, and you can easily use the latest
Qt 5 version no problem.

On windows, it is advised to skip the virtual environment.

# PyQt5 setup debian

PyQt4’s QtGui module has been split into PyQt5’s QtGui, QtPrintSupport and QtWidgets modules.

First install into your virtualenv sip using:

    wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.3/sip-4.16.3.tar.gz
    python configure.py
    make; make install

Install qt to your home folder somewhere by downloading Qt for qt-project

    ./qt-opensource-linux-x64-5.3.1.run:

    wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.3.2/PyQt-gpl-5.3.2.tar.gz
    tar -xzf PyQt-gpl-5.3.2.tar.gz
    cd PyQt-gpl-5.3.2

    python configure.py --confirm-license --qmake=/home/nick/Qt5.3.1/5.3/gcc_64/bin/qmake --no-designer-plugin --no-qml-plugin  --no-qsci-api --enable=QtCore --enable=QtGui --enable=QtSvg --enable=QtOpenGL --enable=QtWidgets --enable=QtPrintSupport --enable=QtTest --enable=QtX11Extras

    make; make install


# PyQt4 setup debian

Install Qt4 packages using apt-get

    sudo apt-get install libqt4-dev libqt4-opengl libqt4-opengl-dev libqt4-svg

Install SIP as above.
Install PyQt4

    wget http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.2/PyQt-x11-gpl-4.11.2.tar.gz
    tar -xzf PyQt-x11-gpl-4.11.2.tar.gz
    cd PyQt-x11-gpl-4.11.2

    python configure.py --confirm-license --qmake=/home/nick/Qt5.3.1/5.3/gcc_64/bin/qmake --no-designer-plugin --no-qml-plugin --no-qsci-api --enable=QtCore --enable=QtGui --enable=QtSvg --enable=QtOpenGL  --enable=QtWidgets  --enable=QtPrintSupport --enable=QtTest

    make; make install


# Mac OS X 10.9

Install the QtCreator app.  I put it in my home directory

Install sip

    wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.3/sip-4.16.3.tar.gz
    tar -xzf sip-4.16.3.tar.gz
    cd sip-4.16.3

    python configure.py --static
    make; make install

Install PyQt5

    wget http:/ /sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.3.2/PyQt-gpl-5.3.2.tar.gz
    tar -xzf PyQt-gpl-5.3.2.tar.gz
    cd PyQt-gpl-5.3.2

    python configure.py --confirm-license --static --qmake=/Users/nick/Qt/5.3/clang_64/bin/qmake --no-designer-plugin --no-qml-plugin  --no-qsci-api --enable=QtCore --enable=QtGui --enable=QtSvg --enable=QtOpenGL --enable=QtWidgets --enable=QtPrintSupport --enable=QtTest --enable=QtMacExtras

    make; make install


# pyqtdeploy
## OSX 10.9

change:

    Qt/5.3/clang_64/mkspecs/qdevice.pri

    !host_build:QMAKE_MAC_SDK = macosx10.9


## Qt static configure
./configure -static -opensource -prefix /Users/nick/Qt/5.3/clang_64 -optimized-qmake -c++11 -system-sqlite -sdk macosx10.9 -no-glib -no-alsa -no-gtkstyle -no-pulseaudio -no-xcb-xlib -no-xinput2 -no-dbus
make sub-src

# build stand-along

    pyqtdeploy cadnano.pdy

copy cadnano.pro to the build directory as it has fixes for ffi.h issues

    ~/Qt/5.3/clang_64/bin/qmake cadnano.pro

