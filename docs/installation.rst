.. cadnano installation

Installation
============

Install Python 3.6
------------------

There are many ways to get Python on your system.

- On Mac, `Homebrew <http://brew.sh/>`__ is a great way to install Python.

- If you just want a clean Python install and nothing else, installers from `python.org <https://www.python.org/>`__ work great too.

- If you prefer the complete "batteries included" option, `Anaconda Python <https://www.continuum.io/downloads>`__ is available for Mac, Windows or Linux.

cadnano will run on Python 3.5 and 3.6, but we only support 3.6. We do not support Python 2.X.


Install cadnano
---------------
Using python 3.6  `pip` will install cadnano and all dependencies from PyPi
::

   $ pip3 install cadnano

or from a root of a cloned `cadnano2.5 <https://github.com/cadnano/cadnano2.5>` repository::

   $ python setup.py install

Both of these methods will install key dependencies like:

-   `PyQt5>=5.8.2 <https://pypi.python.org/pypi/PyQt5/5.8>`
-   `numpy>=1.10.0 <https://pypi.python.org/pypi/numpy/1.11.2>`
-   `pandas>=0.18 <https://pypi.python.org/pypi/pandas/0.19.0>`
-   `pytz>=2011k <https://pypi.python.org/pypi/pytz/2016.7>`
-   `python-dateutil>=2 <https://pypi.python.org/pypi/python-dateutil/2.5.3>`

After `pip` or `setup.py` installation you can install Windows start menu shortcuts or a MacOS Application
of cadanno by running at the commandline::

    $ cadnanoinstall

Allowing you to click on the application icon to launch cadnano.  otherwise just run at the command line::

    $ cadnano

to launch.

Advanced: Building from scratch
-------------------------------

Should the above not work for you:

1. Let us know
2. The requirements ``PyQt5`` and ``SIP`` are available from Riverbank
   Computing Limited at:

-  `Qt5 <https://www.qt.io/download/>`__
-  `PyQt5
   downloads <http://www.riverbankcomputing.com/software/pyqt/download5>`__
-  `SIP
   downloads <http://www.riverbankcomputing.com/software/sip/download>`__

Windows
~~~~~~~

Instructions to come.

Mac and Linux
~~~~~~~~~~~~~

These instructions can work 10.10 Yosemite and 10.11 El Capitan under
Xcode 7.0.1 and 6.5. It has also been tested on Debian 7.9 Wheezy Please
provide feedback if you have problems running this in issues.

You can run the included ``getpyqt5.py`` which will grab, build and
install ``Qt5``, ``SIP`` and ``PyQt5`` in your python environment. It is
cleanest using ``virtualenv`` and ``virtualenvwrapper`` creating a
virtualenv with:

::

    mkvirtualenv --always-copy <myvenv>
    python pyqttools/install_pyqt_from_src.py

and then running the script, but you can definitely install in your
system python if you run:

::

    sudo python pyqttools/install_pyqt_from_src.py

This script only builds required parts of ``Qt5`` and ``PyQt5``. 
Manual installation of ``PyQt5`` is fine too, but you'll need to troubleshoot on your own.

1. Install ``Qt5``. download the `online
   installer <http://www.qt.io/download-open-source/>`__
2. Build sip and PyQt5 against this ``Qt5``

Of course there are many ways to accomplish this feat, but needless to
say OS X and Linux installs of ``PyQt5`` can be painful for some people.

