# cadnano 2.5 
This is a development version of cadnano ported to `Qt5/PyQt5`,
the dev branch is most up to date.  `cadnano` looks better in lower case.

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

to run with a GUI:

    python bin/main.py

when in python interpreter you can just:

    import cadnano

And script your designs without a GUI


## INSTALLATION

Note: Things are changing all the time, and this guide may not be completely 
up to date. If you are having problems following this guide, please report 
the issue on [github](https://github.com/cadnano/cadnano2.5/issues)!


### Step 1: Make sure you have git (and know how to open a Terminal)

Cadnano 2.5 is currently under heavy development. The recommended way to install
cadnano is to use Git. This is what all modern software developers use to manage
and distribute code and makes it very easy to get the latest version or revert 
to an older version (in case the newest version breaks some feature you rely on).

While there are graphical user interfaces available for git, the instructions below
will use terminal/command-line/shell commands. If you haven't used a terminal 
before, don't fret: Just copy/paste the commands into the terminal. You open a 
terminal by:
* Windows: Start -> Command Prompt, or WindowsKey+R and type ```cmd.exe``` plus enter.
* OS X: Apps -> Terminal, or Command+Spacebar and type ```terminal``` plus enter.
* Linux: If you are using Linux, you know this already.

As of March 2016, the easiest ways to install git, depending on your platform, are:
* Windows: Download Git from the official [website](https://git-scm.com/downloads)
* OS X: Open a terminal and type ```git```. If git is already installed, you should
see a "usage" description and a list of available commands. If git is not installed,
you should see a popup window asking you to install OS X developer tools. Follow 
the "Developer tools" guide, installing either the full package or "just the tools".
After installation, type ```git``` again and make sure it works.
* Linux: Use your package manager to install git; use google if you don't know 
how to use your package manager.


### Step 2: Download cadnano 2.5 using Git

1. First, select a suitable folder on your computer where you would like the 
cadnano2.5 source code be be located. The following will assume this location to be
`<your user directory>/Dev/cadnano2.5`.
2. Open a terminal and type `mkdir ~/Dev` and then `cd ~/Dev` to navigate to the 
"Dev" folder. On Windows, type `makedir ~\Dev` and `cd ~\Dev`.
3. Use git to download cadnano2.5. In your terminal, type: 
`git clone https://github.com/cadnano/cadnano2.5.git`.
You should see git downloading cadnano2.5 into a subdirectory of the same name.
4. Navigate to the cadnano2.5 root directory by typing: `cd cadnano2.5` 
(or ~/Dev/cadnano2.5).

You now have cadnano2.5 on your computer and you can run it by typing:

    python ~/Dev/cadnano2.5/bin/main.py

However, this will only work if you have both python and the PyQt5 library installed. 
Installation of these are described in the following two steps below...

Note: It is possible to use cadnano2.5 as a python library to create and manipulate
cadnano designs (.json files). This can be a *very* convenient way to create new 
designs or perform repetitive tasks or analyses, e.g. if you want to color-code
all oligos by length or helix or similar. We are currently working on some examples
showcasing the use of "cadnano-as-a-library" which will be placed in the "examples"
folder inside the root cadnano2.5 directory.

#### Step 2.1: Staying up-to-date with git and exploring git branches

Above we used the `git clone` command to download the cadnano repository to our
computer. If you want to see if there is a new version available, go to your
cadnano2.5 root folder and pull the latest version using: (As always, replace 
forward slashes with backslashes on Windows...)

    cd ~/Dev/cadnano2.5
    git pull

When developing software, it is often convenient to work on different aspects of 
the software separately, in separate "versions". In git, these separately-developed
versions are called "branches". By default git will use the "master" branch,
but some features may only be available in another branch.
You can see the different branches on the [cadnano github page](https://github.com/cadnano/cadnano2.5),
(in the "Branch:" pull-down menu at near the top of the page)
or by typing `git branch -r` in your terminal.
If you want to check out another branch to see how it works, simply type
`git checkout <branch name>` in your terminal.
You can always go back to the default master branch by typing `git checkout master`.


### Step 3: Make sure you have Python

Unless you have good reason otherwise, we highly recommend using the [Anaconda Python 
distribution](https://www.continuum.io/downloads). Even if your system already 
have python installed, using Anaconda makes everything a lot easier. 
Anaconda makes it easy to have many different versions of python and libraries
installed on the same computer. It is also by far the easiest way to download
binary packages on Windows (for instance many scientific packages).

1. Download and install [Anaconda](https://www.continuum.io/downloads)
2. Verify Anaconda is properly installed: In your terminal type ```which python``` 
(on OS X) or ```where python``` (on Windows). You should see a line ending in 
```anaconda3/bin/python``` (or similar).


### Step 4(a). PyQt5 Installation (using Anaconda)

Cadnano 2.5 uses PyQt5 to display the graphical user interface.

If you have Anaconda, the easiest way to get PyQt5 is to use the `conda` package 
manager. 
As mentioned above, the `conda` package manager makes it easy to install different
versions of python and python libraries side-by-side on the same computer. 
It does this by creating separate "environments", where each environment has 
its own libraries installed. Two environments can share the same library without 
taking up extra space. 
We highly recommend installing PyQt5 in a clean `conda` environment using the 
`conda` package manager. 

Unfortunately, Anaconda doesn't have an official PyQt5 build at the moment, 
but unofficial builds are available from the Anaconda Cloud. 
You can see a list of unofficial builds here: https://anaconda.org/search?q=pyqt5
You need to select a version that fits both your operating system (OSX/Windows),
and your Python version. You can see the supported OS for each package in the
right-most column. To see the supported Python version you have to click the 
package, select the "Files" tab, and look at the file names.
Below are some commands that have been shown to work, depending on your platform
and desired version of Python.

Create a new conda environment with PyQt5 installed by copy and pasting 
any one of the following lines to your terminal (and press enter):

OS X or Linux:

    conda create --no-default-packages -n pyqt5 -c https://conda.anaconda.org/spyder-ide pyqt5 python=3.5
    conda create --no-default-packages -n pyqt5 -c https://conda.anaconda.org/mmcauliffe pyqt5 python=3.4
    conda create --no-default-packages -n pyqt5 -c https://conda.anaconda.org/mmcauliffe pyqt5 python=2.7
    conda create --no-default-packages -n pyqt5 -c https://conda.anaconda.org/dsdale24 pyqt5 python=2.7

Windows:

    conda create --no-default-packages -n pyqt5 -c https://conda.anaconda.org/inso pyqt5 python=3.5
    conda create --no-default-packages -n pyqt5 -c https://conda.anaconda.org/mmcauliffe pyqt5 python=3.5
    conda create --no-default-packages -n pyqt5 -c https://conda.anaconda.org/dsdale24 pyqt5 python=3.4


Then activate your new "pyqt5" conda python environment by typing:

    activate pyqt5           (if on Windows)
    source activate pyqt5    (if on OS X or Linux)



Notes: 
* If you get a "SegFault Error" when running cadnano 2.5, try removing the current pyqt5 
package (using ```conda uninstall pyqt5```) and then install a different pyqt5 version/build.
* Before doing the step above, you may want to check if an official
Anaconda pyqt5 build is available. You can check this simply using `conda search
pyqt5` or `conda install pyqt5` (without the "-c" channel argument).
* There is an open issue on Anaconda to support PyQt5: 
[ContinuumIO/anaconda-issues#138](https://github.com/ContinuumIO/anaconda-issues/issues/138).


### Step 4(b). PyQt5 Installation (manually, without Anaconda)

If you do *not* have Anaconda, you have to install PyQt5 manually. This may be a bit
tricky. Only do this if you know what you are doing.

The requirements PyQt5 and sip are available from Riverbank Computing Limited at:

* [PyQt5 downloads](http://www.riverbankcomputing.com/software/pyqt/download5)
* [SIP downloads](http://www.riverbankcomputing.com/software/sip/download)

#### Windows:

On Windows just download the installer from Riverbank computing for your python
version.  We have no experience with other installation methods other than
Anaconda for Windows. See below.

#### Mac and Linux:

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




## *nno2stl*: Conversion of cadnano *.json files to 3D STL model

The purpose of this is for 3D printing cadnano designs.  see bin/creatsly.py
