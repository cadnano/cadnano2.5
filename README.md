# cadnano 2.5  *radnano*
This is a development version of cadnano ported to `Qt5/PyQt5`,
the dev branch is most up to date.  `cadnano` looks better in lower case

## Changes
A number of organizational and style changes have occured from cadnano 2

* cadnano can be run in python without Qt installed at all
* Python 3 compatible
* no more camel-case'd variables (fixes namespace collisions)
* QUndoCommands are broken out to their own modules
* added a STL generator to generate models for 3D printing (experimental)
* added a PDB file generator (experimental, requires additional dependency)
* Maya code removed.
* Added ability to take advantage of `pyqtdeploy` tool to build standalone
versions that can be destributed as binary (not currently finished)
* stablized code base so fewer crashes

The only additional burden for development on this code base is installing PyQt5
to use the GUI which is not a one click situation.  Below gives details on
installing PyQt5.  If you just want to script your designs (no GUI) you
**DO NOT** need to install PyQt5.

## Running

to run with a GUI from the command line :

    cadnano

when in python interpreter you can just:

    import cadnano

And script your designs without a GUI

## Installation

Currently, cadnano will run on Python 3.3, 3.4 and 3.5.

We do not support Python 2.X.

There are many ways to get Python on your system.  Anaconda Python is a great
easy way on both Mac OS X, Windows and Linux.

On OS X, `homebrew` is another great way to install Python 3.X.

### PyQt5 Installation

Install SIP and PyQt as the dependencies.

Currently (6/27/2016), PyQt5 v 5.6  the is a bug with QGraphicsItem.itemChange
that prevents us from being able to use the wheel on pypi.  We've built our
own versions for Windows and Mac OS X for Python 3.5 64 bit that don't have this
problem:

[Mac Python 3.5 SIP 64-bit]
[Mac Python 3.5 PyQt5 64-bit]

    pip install sip-4.16.9-cp35-none-macosx_10_10_x86_64.wh
    pip install PyQt5-5.5.1-cp35-none-macosx_10_10_x86_64.whl

[Windows Python 3.5 SIP 64-bit]
[Windows Python 3.5 PyQt5 64-bit]

    pip install PyQt5-5.6.1-cp35-none-win_amd64.whl
    pip install sip-4.18.1-cp35-none-win_amd64.wh


#### PyQt5 building from scratch

the requirements PyQt5 and sip are available from Riverbank Computing Limited at:

* [Qt5](https://www.qt.io/download/)
* [PyQt5 downloads](http://www.riverbankcomputing.com/software/pyqt/download5)
* [SIP downloads](http://www.riverbankcomputing.com/software/sip/download)

### Windows from scratch

Instructions coming

#### Mac and Linux from scratch

These instructions can work 10.10 Yosemite and  10.11 El Capitan
under Xcode 7.0.1 and 6.5.  It has also been tested on Debian 7.9 Wheezy
Please provide feedback if you have problems running this in issues.

You can run the included `pyqt5_check.py` which will grab, build and install
`Qt5`, `sip` and `PyQt5` in your python environment.  It is cleanest using
`virtualenv` and `virtualenvwrapper` creating a virtualenv with:

    mkvirtualenv --always-copy <myvenv>
    python pyqt5_check.py

and then running the script, but you can definitely install in your system
python if you run:

    sudo python pyqt5_check.py

This script only builds required parts of Qt5 and PyQt5 in the interest of time.

Manual installation of PyQt5 is fine too, but you'll need to trouble shoot on
your own

1.  Install Qt5. download the [online installer](http://www.qt.io/download-open-source/)
2.  Build sip and PyQt5 against this Qt5

Of course there are many ways to accomplish this feat, but needless to say
OS X and Linux installs of `PyQt5` can be painful for some people.

# *nno2stl*: Conversion of cadnano *.json files to 3D STL model

The purpose of this is for 3D printing cadnano designs.  see bin/creatsly.py
C:\Users\Nick\Documents\GitHub\rcedit\Default>rcedit.exe C:\Users\Nick\Documents\GitHub\cadnano2.5\cadnano\install_exe\cadnano.exe --set-icon C:\Users\Nick\Downloads\radnano-app-icon.ico
