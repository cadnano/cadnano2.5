TEMPLATE = app

CONFIG += warn_off release
QT += widgets svg

RESOURCES = resources/pyqtdeploy.qrc

SOURCES = pyqtdeploy_main.cpp pyqtdeploy_start.cpp pdytools_module.cpp
HEADERS = pyqtdeploy_version.h frozen_bootstrap.h

DEFINES += XML_STATIC
INCLUDEPATH += 
INCLUDEPATH += /usr/local/Cellar/python3/3.4.1/Frameworks/Python.framework/Versions/3.4/include/python3.4m
INCLUDEPATH += /Users/nick/Downloads/Python-3.4.1/Modules
INCLUDEPATH += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes
INCLUDEPATH += /Users/nick/Downloads/Python-3.4.1/Modules/expat

LIBS += -L/usr/local/Cellar/python3/3.4.1/Frameworks/Python.framework/Versions/3.4/lib/python3.4/config-3.4m -lpython3.4

LIBS += -L/usr/local/Cellar/python3/3.4.1/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages -lsip
LIBS += -L/usr/local/Cellar/python3/3.4.1/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/PyQt5 -lQtCore -lQtGui -lQtWidgets -lQtSvg
LIBS += -lz
SOURCES += 
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/sha512module.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/callbacks.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/libffi_osx/x86/x86-ffi64.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/libffi_osx/x86/darwin64.S
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/libffi_osx/ffi.c

SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/malloc_closure.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/arraymodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_math.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_json.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/expat/xmltok.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_struct.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_datetimemodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/stgdict.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/sha1module.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/timemodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_randommodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/sha256module.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/selectmodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/zlibmodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/callproc.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/md5module.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/pyexpat.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/expat/xmlrole.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/_ctypes.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/cfield.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/mathmodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/expat/xmlparse.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_heapqmodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/socketmodule.c
SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/binascii.c

!win32 {
    DEFINES += HAVE_EXPAT_CONFIG_H
    SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/grpmodule.c
    SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_posixsubprocess.c
}

linux-* {
    LIBS += -lffi
    LIBS += -lm
}

macx {
    DEFINES += MACOSX
    INCLUDEPATH += /Users/nick/Downloads/Python-3.4.1/Modules/_ctypes/libffi_osx/include
}

win32 {
    DEFINES += COMPILED_FROM_DSP
    SOURCES += /Users/nick/Downloads/Python-3.4.1/Modules/_winapi.c
    SOURCES += /Users/nick/Downloads/Python-3.4.1/PC/msvcrtmodule.c
}

linux-* {
    LIBS += -lutil -ldl
}

win32 {
    LIBS += -ladvapi32 -lshell32 -luser32
}
