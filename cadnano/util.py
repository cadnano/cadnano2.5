"""
util
Created by Jonathan deWerd.
"""
import inspect
from traceback import extract_stack
from random import Random
import string
import sys
import os
from os import path
import platform
# import imp
from itertools import dropwhile, starmap

IS_PY_3 = int(sys.version_info[0] > 2)
prng = Random()

def clamp(x, minX, maxX):
    if x < minX:
        return minX
    elif x > maxX:
        return maxX
    else:
        return x

def overlap(x,y, a,b):
    """
    finds the overlap of the range x to y in a to b
    assumes an overlap exists, i.e.
        y >= a and b >= x
    """
    c = clamp(x, a, b)
    d = clamp(y, a, b)
    return c, d
# end def

def trace(n):
    """Returns a stack trace n frames deep"""
    s = extract_stack()
    frames = []
    for f in s[-n-1:-1]:
        # f is a stack frame like
        # ('/path/script.py', 42, 'funcname', 'current = line - of / code')
        frames.append( (path.basename(f[0])+':%i'%f[1])+'(%s)'%f[2] )
    return " > ".join(frames)

def strToDna(seqStr):
    """Returns str having been reduced to capital ACTG."""
    return "".join([c for c in seqStr if c in 'ACGTacgt']).upper()

if IS_PY_3:
    complement = str.maketrans('ACGTacgt','TGCATGCA')
else:
    complement = string.maketrans('ACGTacgt','TGCATGCA')
def rcomp(seqStr):
    """Returns the reverse complement of the sequence in seqStr."""
    return seqStr.translate(complement)[::-1]
def comp(seqStr):
    """Returns the complement of the sequence in seqStr."""
    return seqStr.translate(complement)

if IS_PY_3:
    whitetoQ = str.maketrans(' ','?')
else:
    whitetoQ = string.maketrans(' ','?')
def markwhite(seqStr):
    return seqStr.translate(whitetoQ)

def nowhite(seqStr):
    """Gets rid of whitespace in a string."""
    return ''.join([c for c in seqStr if c in string.letters])

nearest=lambda a,l:min(l,key=lambda x:abs(x-a))

def isWindows():
    if platform.system() == 'Windows':
        return True
    else:
        return False

def isMac():
    try:
        return platform.system() == 'Darwin'
    except:
        return path.exists('/System/Library/CoreServices/Finder.app')

def isLinux():
    if platform.system() == 'Linux':
        return True
    else:
        return False

def methodName():
    """Returns string containing name of the calling method."""
    return inspect.stack()[1][3]

def starmapExec(f, tupleIter):
    """
    takes a function f and * starmaps the list but drops the results
    """
    list(dropwhile(lambda x: True, starmap(f, tupleIter)))
# end def

def execCommandList(model_object, commands, desc=None, use_undostack=True):
    """
    This is a wrapper for performing QUndoCommands, meant to ensure
    uniform handling of the undoStack and macro descriptions.

    When using the undoStack, commands are pushed onto self.undoStack()
    as part of a macro with description desc. Otherwise, command redo
    methods are called directly.
    """
    if use_undostack:
        undoStackId = str(id(model_object.undoStack()))[-4:]
        # print "<QUndoStack %s> %s" % (undoStackId, desc)
        model_object.undoStack().beginMacro(desc)
        for c in commands:
            model_object.undoStack().push(c)
        model_object.undoStack().endMacro()
    else:
        # print "<NoUndoStack> %s" % (desc)
        for c in commands:
            c.redo()
# end def

def this_path():
    return os.path.abspath(os.path.dirname(__file__))

# maps plugin path (extension stripped) -> plugin module
loadedPlugins = {}

def unloadedPlugins():
    """ Returns a list of plugin paths that have yet to
    be loaded but are in the top level of one of the
    search directories specified in pluginDirs"""
    internalPlugins = os.path.join(this_path(), 'plugins')
    pluginDirs = [internalPlugins]
    results = []
    for pluginDir in pluginDirs:
        if not os.path.isdir(pluginDir):
            continue
        for dirent in os.listdir(pluginDir):
            f = os.path.join(pluginDir, dirent)
            isfile = os.path.isfile(f)
            hasValidSuffix = dirent.endswith(('.py', '.so'))
            if isfile and hasValidSuffix:
                results.append(f)
            if os.path.isdir(f) and\
               os.path.isfile(os.path.join(f, '__init__.py')):
                results.append(f)
    return list(filter(lambda x: x not in loadedPlugins, results))

def loadPlugin(f):
    pass
    # path, fname = os.path.split(f)
    # name, ext = os.path.splitext(fname)
    # pluginKey = os.path.join(path, name)
    # try:
    #     mod = loadedPlugins[pluginKey]
    #     return mod
    # except KeyError:
    #     pass
    # file, filename, data = imp.find_module(name, [path])
    # mod = imp.load_module(name, file, filename, data)
    # loadedPlugins[pluginKey] = mod
    # return mod

def loadAllPlugins():
    loadedAPlugin = False
    for p in unloadedPlugins():
        loadPlugin(p)
        loadedAPlugin = True
    return loadedAPlugin

def beginSuperMacro(model_object, desc=None):
    """
    SuperMacros can be used to nest multiple command lists.

    Normally execCommandList macros all the commands in a list.
    In some cases, multiple command lists need to be executed separately
    because of dependency issues. (e.g. in part.autoStaple, strands
    must be completely 1. created and 2. split before 3. xover installation.)
    """
    model_object.undoStack().beginMacro(desc)
# end def

def endSuperMacro(model_object):
    """Ends a SuperMacro. Should be called after beginSuperMacro."""
    model_object.undoStack().endMacro()
# end def

def findChild(self):
    """
    When called when self isa QGraphicsItem, iterates through self's
    childItems(), placing a red rectangle (a sibling of self) around
    each item in sequence (press return to move between items). Since
    the index of each child item is displayed as it is highlighted,
    one can use findChild() to quickly get a reference to one of self's
    children. At each step, one can type a command letter before
    hitting return. The command will apply to the current child.
    Command Letter:     Action:
    <return>            Advance to next child
    s<return>           Show current child
    S<return>           Show current child, hide siblings
    h<return>           Hide current child
    r<return>           return current child
    """
    from PyQt5.QtWidgets import QGraphicsRectItem
    from PyQt5.QtGui import QPen
    from PyQt5.QtCore import Qt

    children = self.childItems()
    parent = self.parentItem()
    childVisibility = [(child, child.isVisible()) for child in children]
    for n in range(len(children)):
        child = children[n]
        print("Highlighting %s.childItems()[%i] = %s"%(self, n, child))
        childBR = child.mapToItem(parent, child.boundingRect())
        childBR = childBR.boundingRect()  # xform gives us a QPolygonF
        debugHighlighter = QGraphicsRectItem(childBR, parent)
        debugHighlighter.setPen(QPen(Qt.red))
        debugHighlighter.setZValue(9001)
        while True:
            # wait for return to be pressed while spinning the event loop.
            # also process single-character commands.
            command = raw_input()
            if command == 's':    # Show current child
                child.show()
            elif command == 'h':  # Hde current child
                child.hide()
            elif command == 'S':  # Show only current child
                for c in children:
                    c.hide()
                child.show()
            elif command == 'r':  # Return current child
                for child, wasVisible in childVisibility:
                    child.setVisible(wasVisible)
                return child
            else:
                break
        debugHighlighter.scene().removeItem(debugHighlighter)
        for child, wasVisible in childVisibility:
            child.setVisible(wasVisible)