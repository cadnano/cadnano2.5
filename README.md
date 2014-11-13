# Conversion of cadnano .nno files to 3D STL model

The purpose of this is for 3D printing

# PyQt5 Installation

if on Windows just download the installer for your python
if on Linux or Mac follow this path:

you can run `pyqt5_check.py` which will grab, build and install
`Qt5`, `sip` and `PyQt5` in your python environment.  Its cleanest using 
`virtualenv` and `virtualenvwrapper` creating a virtualenv with:

    mkvirtualenv -p /path/to/python/of/choice/bin/python
    python pyqt5_check.py

and then running the script, but you can definitely install in your system
python if you run:

    sudo python pyqt5_check.py

or you can manually:

1.  Install Qt5 (download online installer)
2.  Build sip and PyQt5 against this Qt5

Of course there are many ways to accomplish this feat, but needless to say
OS X and Linux installs of `PyQt5` can be painful.

