.. cadnano virtualenv

Virtualenv
==========

We develop cadnano using `virtualenv`_ and `virtualenvwrapper`_. Virtualenvs make it harder to mess up your entire system, and easy to start over when you mess up locally. If you wish to make modifications to the cadnano source code, you can first start by replicating our setup.

.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _virtualenvwrapper: http://virtualenvwrapper.readthedocs.io

What are virtual environments?
------------------------------

A virtual environment consists of a separate copy of ``python3`` that lives in your home directory and some scripts that set up your shell environment so the local python copy is used instead of the system python. Virtualenvwrapper is a shell script that provides some convenient commands to easily manage multiple virtualenvs.

When a virtualenv is activated in the terminal (using the ``workon`` command), everything feels basically the same, but there are a few important differences.

::

   shawn ~/Desktop/projects/cadnano2.5 $ which python
   /usr/bin/python
   shawn ~/Desktop/projects/cadnano2.5 $ workon c25
   (c25) shawn ~/Desktop/projects/cadnano2.5 $ which python
   /Users/shawn/.virtualenvs/c25/bin/python

You'll notice the active virtualenv prefixes your path with its name ("c25" in my case). Behind the scenes, your paths are set up such that the local copy of ``python3`` will run instead of whatever is in your default path, as well the python package manager ``pip3``. Thus, any libraries or packages that you install with the virtualenv active will go into the virtualenv subfolder as well.


Setting up virtualenv and virtualenvwrapper
-------------------------------------------

These instructions assume you've already set up python3 on your system. (Personally, I use Homebrew to do this.)

.. note::
   If you only wish to run cadnano, none of this necessary. Just perform the basic `installation`_.

.. _`installation`: installation.html

**Getting started**

Run this command from the terminal:

::

   pip3 install virtualenv virtualenvwrapper


**Updating your .bash_profile**

We want to invoke virtualenvwrapper whenever we open a terminal window. To do this, we edit ``.bash_profile``.
Here are the virtualenv-related lines of my .bash_profile, per the `virtualenvwrapper docs`_:

.. _virtualenvwrapper docs: http://virtualenvwrapper.readthedocs.io/en/latest/install.html#shell-startup-file

::

   export WORKON_HOME=$HOME/.virtualenvs
   export PROJECT_HOME=$HOME/Devel
   export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3
   source /Library/Frameworks/Python.framework/Versions/3.6/bin/virtualenvwrapper.sh

Once you add these lines, open a new terminal window to verify they are working. If you get an error, you may need to confirm your python3 is correctly installed, and possibly modify the path to ``virtualenvwrapper.sh`` if you aren't using homebew and your copy of python3 lives somewhere else.

**Creating a virtualenv**

Use the virtualenvwrapper command ``mkvirtualenv`` to create a new virtualenv. For this example, we'll call our virtualenv "cndev":

::

   shawn ~ $ mkvirtualenv cndev
   Using base prefix '/Library/Frameworks/Python.framework/Versions/3.6'
   New python executable in /Users/shawn/.virtualenvs/cndev/bin/python3.6
   Also creating executable in /Users/shawn/.virtualenvs/cndev/bin/python
   Installing setuptools, pip, wheel...done.
   virtualenvwrapper.user_scripts creating /Users/shawn/.virtualenvs/cndev/bin/predeactivate
   virtualenvwrapper.user_scripts creating /Users/shawn/.virtualenvs/cndev/bin/postdeactivate
   virtualenvwrapper.user_scripts creating /Users/shawn/.virtualenvs/cndev/bin/preactivate
   virtualenvwrapper.user_scripts creating /Users/shawn/.virtualenvs/cndev/bin/postactivate
   virtualenvwrapper.user_scripts creating /Users/shawn/.virtualenvs/cndev/bin/get_env_details


If everything worked, you should see an output resembling the above.


Running cadnano from a virtualenv
---------------------------------

Now that we have a virtualenv working, let's get all the cadnano dependencies, and download the git repository.

::

   (cndev) shawn ~ $ pip3 install PyQt5 PyQt3D pandas termcolor
   Collecting PyQt5
     Using cached PyQt5-5.9.2-5.9.3-cp35.cp36.cp37-abi3-macosx_10_6_intel.whl
   Collecting PyQt3D
     Using cached PyQt3D-5.9.2-5.9.3-cp35.cp36.cp37-abi3-macosx_10_6_intel.whl
   Collecting pandas
     Using cached pandas-0.22.0-cp36-cp36m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl
   Collecting termcolor
   Collecting sip<4.20,>=4.19.4 (from PyQt5)
     Using cached sip-4.19.6-cp36-cp36m-macosx_10_6_intel.whl
   Collecting numpy>=1.9.0 (from pandas)
     Using cached numpy-1.14.0-cp36-cp36m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl
   Collecting pytz>=2011k (from pandas)
     Using cached pytz-2017.3-py2.py3-none-any.whl
   Collecting python-dateutil>=2 (from pandas)
     Using cached python_dateutil-2.6.1-py2.py3-none-any.whl
   Collecting six>=1.5 (from python-dateutil>=2->pandas)
     Using cached six-1.11.0-py2.py3-none-any.whl
   Installing collected packages: sip, PyQt5, PyQt3D, numpy, pytz, six, python-dateutil, pandas, termcolor
   Successfully installed PyQt3D-5.9.2 PyQt5-5.9.2 numpy-1.14.0 pandas-0.22.0 python-dateutil-2.6.1 pytz-2017.3 sip-4.19.6 six-1.11.0 termcolor-1.1.0
   (cndev) shawn ~/Desktop $ git clone https://github.com/cadnano/cadnano2.5.git
   Cloning into 'cadnano2.5'...
   remote: Counting objects: 15865, done.
   remote: Compressing objects: 100% (219/219), done.
   remote: Total 15865 (delta 288), reused 288 (delta 198), pack-reused 15448
   Receiving objects: 100% (15865/15865), 12.38 MiB | 846.00 KiB/s, done.
   Resolving deltas: 100% (12982/12982), done.
   (cndev) shawn ~/Desktop $ cd cadnano2.5/
   (cndev) shawn ~/Desktop/cadnano2.5 $ python cadnano/bin/main.py

If everything works, the cadnano window should open.


Useful virtualenvwrapper commands
---------------------------------

**workon**: activate the virtualenv, e.g. ``workon cndev``

**deactivate**: drop out of the virtualenv, back into the normal terminal

**lssitepackages**: list the active virtualenv's installed packages

**rmvirtualenv**: remove the virtualenv, e.g. ``rmvirtualenv cndev``
