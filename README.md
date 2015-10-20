# cadnano 2.5  *radnano*
This is a development version of cadnano ported to `Qt5/PyQt5`,
the dev branch is most up to date.  `cadnano` looks better in lower case

## Changes
A number of organizational and style changes have occured from cadnano 2

* cadnano can be run in python without Qt installed at all
* Python 3 compatible
* no more camel-case'd variables (fixes namespace collisions)
* QUndoCommands are broken out to their own modules
* added a STL generator to generate models for 3D printing
* Maya code removed.
* Added ability to take advantage of `pyqtdeploy` tool to build standalone
versions that can be destributed as binary (not currently finished)
* stablized code base so fewer crashes

The only additional burden for development on this code base is installing PyQt5
to use the GUI which is not a one click situation.  Below gives details on
installing PyQt5.  If you just want to script your designs (no GUI) you
**DO NOT** need to install PyQt5.

## Running

to run with a GUI:

    python bin/main.py

when in python interpreter you can just:

    import cadnano

And script your designs without a GUI

## PyQt5 Installation

the requirements PyQt5 and sip are available from Riverbank Computing Limited at:

* [PyQt5 downloads](http://www.riverbankcomputing.com/software/pyqt/download5)
* [SIP downloads](http://www.riverbankcomputing.com/software/sip/download)

### Windows

On Windows just download the installer for your python version.

### Mac and Linux

These instructions can work for 10.10 Yosemite, and possibly for 10.11 El Capitan under Xcode 7.0.1, using Qt5.5.1 but this has not yet been tested.  Please provide feedback if it works for you. Linux seems to have no problems.

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

### Anaconda Installation

First create a new conda environment. The default anaconda install typically
have PyQt4 installed, and that doesn't always play well with PyQt5, so we need
to create an empty one.

(If you know what you are doing, you can omit the `--no-default-packages` flag.)

    conda create --no-default-packages -n pyqt5 python=3

followed by:

    activate pyqt5

Second, install PyQt5 in the new environment. (Make sure you have activated
the `pyqt5` environment using the `activate` command). Unfortunately, Anaconda
doesn't have an official PyQt5 build at the moment, but [`dsdale24` has 64-bit Win/OSX/Linux builds on his channel](https://anaconda.org/dsdale24/pyqt5).
Install this using:

    conda install -c https://conda.anaconda.org/dsdale24 pyqt5

Note: Before doing the step above, you may want to check if an official
Anaconda pyqt5 build is available. You can check this simply using `conda search
pyqt5` or `conda install pyqt5`.

There is an open issue on Anaconda to support PyQt5: [ContinuumIO/anaconda-issues#138](https://github.com/ContinuumIO/anaconda-issues/issues/138).

# *nno2stl*: Conversion of cadnano *.json files to 3D STL model

The purpose of this is for 3D printing cadnano designs.  see bin/creatsly.py
