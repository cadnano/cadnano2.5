
[![Build Status](https://travis-ci.org/cadnano/cadnano2.5.svg?branch=master)](https://travis-ci.org/cadnano/cadnano2.5) [![Documentation Status](https://readthedocs.org/projects/cadnano/badge/?version=master)](http://cadnano.readthedocs.io/en/master/?badge=master)

# *radnano* : cadnano 2.5

## Install

    pip3 install cadnano

For more detail, see this [documentation](http://cadnano.readthedocs.io/).

## Running

To run with a GUI from the command line:

    cadnano

## Scripting

When in a python interpreter you can just:

    import cadnano

and script your designs without a GUI. See our [scripting](http://cadnano.readthedocs.io/en/master/scripting.html) docs.

## License

The code is dual licensed as GPLv3 and BSD-3 except the file: `cadnano/gui/views/outlinerview/outlinertreewidget.py`, which is GPL3 only because it fixes a bug in Qt5 using derived code.
This way, cadnano scripts that don't use the GUI can be released under GPLv3 or BSD-3 license.

The full license can be found in LICENSE

