###############################################################################
#
# Copyright 2011 Autodesk, Inc.  All rights reserved.
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###############################################################################


import maya.cmds as cmds
import maya.mel as mel

# Original States
hiddenElements = []
elementsToHide = ["toolBar", "dockControl"]
mainMenuBarVisible = None
gridVisible = None

modelEditors = []
backgroundColors = []
"""
Hideable Stuff:
    UIElements
    Grid
    MainMenuBar
"""

def simplifyUI():
    hideUIElements()
    hideMainMenuBar()
    hideGrid()
    #mel.eval("toggleModelEditorBarsInAllPanels 0;")

def restoreUI():
    restoreUIElements()
    restoreMainMenuBar()
    restoreGrid()
    #mel.eval("toggleModelEditorBarsInAllPanels 1;")

def setViewportQuality():
    global modelEditors
    global backgroundColors
    backgroundColors.append(cmds.displayRGBColor('background',q=True))
    backgroundColors.append(cmds.displayRGBColor('backgroundTop',q=True))
    backgroundColors.append(cmds.displayRGBColor('backgroundBottom',q=True))
    cmds.displayRGBColor('background', 1, 1, 1)
    cmds.displayRGBColor('backgroundTop', 0.762112, 0.87892, 1)
    cmds.displayRGBColor('backgroundBottom', 1, 1, 1)

    for i in cmds.lsUI(panels=True):
        if cmds.modelEditor(i, query=True, exists=True):
            sts = cmds.modelEditor(i, query=True, stateString=True)
            sts = sts.replace("$editorName", i)
            modelEditors.append(sts)
            cmds.modelEditor(i, edit=True, displayAppearance="smoothShaded", lineWidth=2)
                                 #, rendererName="hwRender_OpenGL_Renderer")

def restoreViewportQuality():
    global modelEditors
    global backgroundColors
    bc = backgroundColors
    cmds.displayRGBColor('background', bc[0][0], bc[0][1], bc[0][2])
    cmds.displayRGBColor('backgroundTop', bc[1][0], bc[1][1], bc[1][2])
    cmds.displayRGBColor('backgroundBottom', bc[2][0], bc[2][1], bc[2][2])

    for e in modelEditors:
        mel.eval(e)

def hideMainMenuBar():
    global mainMenuBarVisible
    mainMenuBarVisible = cmds.optionVar(q="mainWindowMenubarVis")
    #mel.eval("setMainMenubarVisible 0;")

def restoreMainMenuBar():
    global mainMenuBarVisible
    #mel.eval("setMainMenubarVisible " + str(mainMenuBarVisible) + ";")

def hideUIElements():
    global hiddenElements
    global elementsToHide
    for i in cmds.lsUI(ctl=True):
        for e in elementsToHide:
            if i.find(e) != -1 and cmds.control(i, q=True, visible=True):
                hiddenElements.append(i)
                #print "hiding... " + i
                cmds.control(i, e=True, visible=False)
                break

def restoreUIElements():
    global hiddenElements
    for e in hiddenElements:
        #print "restoring... " + e
        cmds.control(e, e=True, visible=True)
    hiddenElements = []

def hideGrid():
    global gridVisible
    gridVisible = cmds.optionVar(q="showGrid")
    cmds.grid(toggle=0)

def restoreGrid():
    global gridVisible
    cmds.grid(toggle=gridVisible)
