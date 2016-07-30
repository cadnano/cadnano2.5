#!/usr/bin/env python
"""
From http://stackoverflow.com/questions/7827430/
https://creativecommons.org/licenses/by-sa/3.0/

This creates an app to launch a python script. The app is created in the
directory where python is called. A version of Python is created via a
softlink, named to match the app, which means that the name of the app rather
than Python shows up as the name in the menu bar, etc, but this requires
locating an app version of Python (expected name
.../Resources/Python.app/Contents/MacOS/Python in directory tree of calling
python interpreter).

Run this script with one or two arguments:
    <python script>
    <project name>

The script path may be specified relative to the current path or given
an absolute path, but will be accessed via an absolute path. If the
project name is not specified, it will be taken from the root name of
the script.

"""

import sys
import os
import os.path
import stat
# import shutil

pjoin = os.path.join


def Usage():
    print("\n\tUsage: python " + sys.argv[0] + " <python script> [<project name>]\n")
    sys.exit()

version = "1.0.0"
bundleIdentifier = "org.test.test"

if not 2 <= len(sys.argv) <= 3:
    Usage()

script = os.path.abspath(sys.argv[1])
if not os.path.exists(script):
    print("\nFile " + script + " not found")
    Usage()
if os.path.splitext(script)[1].lower() != '.py':
    print("\nScript " + script + " does not have extension .py")
    Usage()

if len(sys.argv) == 3:
    project = sys.argv[2]
else:
    project = os.path.splitext(os.path.split(script)[1])[0]

apppath = os.path.abspath(pjoin('.', project + ".app"))
projectversion = project + " " + version
if os.path.exists(apppath):
    print("\nSorry, an app named " + project + " exists in this location (" + str(apppath) + ")")
    sys.exit()

os.makedirs(pjoin(apppath, "Contents", "MacOS"))

f = open(pjoin(apppath, "Contents", "Info.plist"), "w")
f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleExecutable</key>
    <string>main.sh</string>
    <key>CFBundleGetInfoString</key>
    <string>{:}</string>
    <key>CFBundleIconFile</key>
    <string>app.icns</string>
    <key>CFBundleIdentifier</key>
    <string>{:}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{:}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>{:}</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleVersion</key>
    <string>{:}</string>
    <key>NSAppleScriptEnabled</key>
    <string>YES</string>
    <key>NSMainNibFile</key>
    <string>MainMenu</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
'''.format(projectversion, bundleIdentifier, project, projectversion, version))
f.close()

# not sure what this file does
f = open(pjoin(apppath, 'Contents', 'PkgInfo'), "w")
f.write("APPL????")
f.close()

# adding icon
# os.makedirs(pjoin(apppath, "Contents", "Resources"))
# shutil.copy2(my_icon, pjoin(apppath, "Contents", "Resources", "%s.icns" % project))

python_exe = os.path.realpath(sys.executable)
# create a script that launches python with the requested app
shell = pjoin(apppath, "Contents", "MacOS", "main.sh")
# create a short shell script
f = open(shell, "w")
f.write('#!/bin/sh\nexec "' + python_exe + '" "' + script + '"\n')
f.close()
os.chmod(shell, os.stat(shell).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
