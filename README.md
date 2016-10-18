
[![Build Status](https://travis-ci.org/cadnano/cadnano2.5.svg?branch=master)](https://travis-ci.org/cadnano/cadnano2.5) [![Documentation Status](https://readthedocs.org/projects/cadnano/badge/?version=master)](http://cadnano.readthedocs.io/en/master/?badge=master)

# *radnano* : cadnano 2.5 beta

`cadnano` looks better in lower case

## Running

to run with a GUI from the command line :

    cadnano

when in a python interpreter you can just:

    import cadnano

And script your designs without a GUI

## Install

    pip install cadnano

## License

The code is dual licensed as GPLv3 and BSD-3 except the file: `cadnano/gui/views/outlinerview/outlinertreewidget.py`, which is GPL3 only because it fixes a bug in Qt5 using derived code.
This way, cadnano scripts that don't use the GUI can be released under GPLv3 or BSD-3 license.

The full license can be found in LICENSE

