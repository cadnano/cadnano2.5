"""
util.py
"""
import inspect
from traceback import extract_stack
from random import Random
import string
import sys
import os
from os import path
import platform
import argparse
import logging
import logging.handlers
logger = logging.getLogger(__name__)
# import imp
from itertools import dropwhile, starmap

IS_PY_3 = int(sys.version_info[0] > 2)
prng = Random()

def clamp(x, min_x, max_x):
    if x < min_x:
        return min_x
    elif x > max_x:
        return max_x
    else:
        return x

def overlap(x, y, a, b):
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

nearest=lambda a, l:min(l, key=lambda x: abs(x - a) )

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

def finalizeCommands(model_object, commands, desc=None):
    """
    used to enable interaction with the model but not push
    commands to the undostack.  In practice:

    1. Call a bunch of commands and don't push them to the undostack AKA:
        cmd.redo()
    2. call finalizeCommands() to push the cummulative change to the stack

    this assumes that the UndoCommands provided this function are respresent
    a transition from the initial state to the final state
    UndoCommands need to implement specialUndo which could just call normal
    undo
    """
    # 1. undo the command to get back to the initial _state
    for c in commands:
        c.specialUndo()
        # c.undo()
    # 2. push all the "undoable" commands to the undostac
    model_object.undoStack().beginMacro(desc)
    for c in commands:
        model_object.undoStack().push(c)
    model_object.undoStack().endMacro()
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
    When called when self is a QGraphicsItem, iterates through self's
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
# end def

def parse_args(argv=None, gui=None):
    """
    Uses argparse to parse commandline args.
    Returns a NameSpace object. This can easily be converted to a regular dict through:
        argns.__dict__

    This also presents a nice command line help to the user, exposed with --help flag:
        python main.py --help

    If gui is set to "qt", then the parser will use parse_known_args.
    Unlike parse_args(), parse_known_args() will not cause abort by show the help message and exit,
    if it finds any unrecognized command-line arguments.
    Alternatively, you can initialize your app via
        app = QApplication(sys.argv)
        parse_args(app.arguments())
    QApplication.arguments() returns a list of arguments with all Qt arguments stripped away.
    Qt command line args include:
        -style=<style> -stylesheet=<stylesheet> -widgetcount -reverse -qmljsdebugger -session=<session>
    """
    parser = argparse.ArgumentParser(description="cadnano 2.5")
    parser.add_argument("--testing", "-t", action="store_true", help="Enable testing mode/environment.")
    parser.add_argument("--profile", "-p", action="store_true", help="Profile app execution.")
    parser.add_argument("--print-stats", "-P", action="store_true", help="Print profiling statistics.")
    parser.add_argument("--interactive", "-i", action="store_true", help="Enable interactive (console) mode.")
    parser.add_argument('--loglevel',
                        help="Specify logging level. Can be either DEBUG, INFO, WARNING, ERROR or any integer.")
    parser.add_argument("--debug-modules", nargs='*', metavar="MODULE-STR",
                        help="Debug modules whose names start with any of the given strings. For instance, to "\
                             "debug the cadnano file decoder, use --debug-modules cadnano.fileio.nnodecode ."\
                             "To debug all gui modules, use --debug-modules cadnano.gui .")
    parser.add_argument("--file", "-f", metavar="designfile.json", help="cadnano design to load upon start up.")
    if gui and (gui is True or gui.lower() == "qt"):
        # Command line args might include Qt-specific switches and parameters.
        argns, unused = parser.parse_known_args(argv)
    else:
        argns, unused = parser.parse_args(argv), None
    return argns, unused

def init_logging(args=None, logdir=None):
    """
    Set up standard logging system based on parameters in args, e.g. loglevel and testing.
    """
    if args is None:
        args = {}
    if logdir is None:
        appname = "cadnano"
        try:
            import appdirs
            logdir = appdirs.user_log_dir(appname)
        except ImportError:
            if os.environ.get('APPDATA'):
                logdir = os.path.join(os.environ['APPDATA'], appname, "Logs")
            elif sys.platform == 'darwin':
                logdir = os.path.join(os.path.expanduser("~"), "Library", "Logs", appname)
            else:
                logdir = os.path.join(os.path.expanduser("~"), "."+appname, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logfilepath = os.path.join(logdir, appname+".log")

    ## We want different output formatting for file vs console logging output.
    ## File logs should be simple and easy to regex; console logs should be short and nice on the eyes
    logfilefmt = "%(asctime)s %(levelname)-6s - %(name)s:%(lineno)s - %(funcName)s() - %(message)s"
    logdatefmt = "%Y%m%d-%H:%M:%S"
    loguserfmt = "%(asctime)s %(levelname)-5s %(module)30s:%(lineno)-4s%(funcName)16s() %(message)s"
    logtimefmt = "%H:%M:%S" # Nice for output to user in console and testing.
    # See https://docs.python.org/3/library/logging.html#logrecord-attributes for full list of attributes

    # Loglevel (for console messages)
    if args.get('loglevel'):
        try:
            loglevel = int(args['loglevel'])
        except (TypeError, ValueError):
            loglevel = getattr(logging, args['loglevel'].upper())
    else:
        loglevel = logging.DEBUG if args.get('testing') else logging.WARNING

    if args.get('basic_logging', False):
        logging.basicConfig(level=loglevel,
                            format=loguserfmt,
                            datefmt=logtimefmt,
                            filename=logfilename)
        logger.debug("Logging system initialized with loglevel %s", loglevel)
    else:

        # Set up custom logger:
        logging.root.setLevel(logging.DEBUG)

        # Add a rotating file handler:
        logfilehandler = logging.handlers.RotatingFileHandler(logfilepath, maxBytes=2*2**20, backupCount=2)
        logfileformatter = logging.Formatter(fmt=logfilefmt, datefmt=logdatefmt)
        logfilehandler.setFormatter(logfileformatter)
        logging.root.addHandler(logfilehandler)
        print("Logging to file:", logfilepath)

        # Add a custom StreamHandler for outputting to the console (default level is 0 = ANY)
        logstreamhandler = logging.StreamHandler() # default stream is sys.stderr
        logging.root.addHandler(logstreamhandler)
        logstreamformatter = logging.Formatter(loguserfmt, logtimefmt)
        logstreamhandler.setFormatter(logstreamformatter)

        # Set filter for debugging:
        if args.get('debug_modules'):
            debug_modules = args['debug_modules']
            def module_debug_filter(record):
                """
                All Filters attached to a logger or handler are asked.
                The record is discarted if any of the attached Filters return False.
                """
                return any(record.name.startswith(modstr) for modstr in args['debug_modules']) \
                    or record.levelno >= loglevel
            logstreamhandler.addFilter(module_debug_filter)
            # Default level is 0, which is appropriate when using module_debug_filter
        else:
            # only set a min level if we are not using module_debug_filter. (Level is an additional filter.)
            logstreamhandler.setLevel(loglevel)
    logger.info("Logging system initialized...")

def read_fasta(fp):
    name, seq = None, []
    for line in fp:
        line = line.rstrip()
        if line.startswith(">"):
            if name: yield (name, ''.join(seq))
            name, seq = line, []
        else:
            seq.append(line)
    if name: yield (name, ''.join(seq))
