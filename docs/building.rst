.. cadnano building

Building
========

Building Qt, PyQt5, SIP, and PyQt3D from source
-----------------------------------------------

.. warning::
   Not recommended for novice users. But a great way to learn :)


If the packages available on pypi are lagging behind some bleeding-edge feature in Qt, 
sometimes it's necessary to build everything from source. In the cadnano directory there's
a script called getpyqt5.py. Before using it, make sure your virtualenv was created with
the `--always-copy`_ flag. 

.. _--always-copy: https://virtualenv.pypa.io/en/stable/reference/#cmdoption-always-copy

::

   mkvirtualenv --always-copy <myenv>

The source urls are typically out of date as soon as the script is more than about
1 month old, so you'll need to update it manually.
