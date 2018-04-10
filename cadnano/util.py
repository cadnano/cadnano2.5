# -*- coding: utf-8 -*-
from typing import (
    Union,
    Tuple,
    Iterable,
    List
)
import argparse
import inspect
import logging
import logging.handlers
import os
import platform
import string
import sys
from os import path
from traceback import extract_stack

from cadnano.cntypes import (
    CNObjectT,
    UndoCommandT
)

logger = logging.getLogger(__name__)

IS_PY_3 = int(sys.version_info[0] > 2)

relpath = os.path.relpath
dirname = os.path.dirname
abspath = os.path.abspath
CADNANO_PATH = dirname(abspath(__file__))
NumT = Union[int, float]

def clamp(x: NumT, min_x: NumT, max_x: NumT) -> NumT:
    if x < min_x:
        return min_x
    elif x > max_x:
        return max_x
    else:
        return x


def overlap(x: NumT, y: NumT, a: NumT, b: NumT) -> Tuple[NumT, NumT]:
    """Finds the overlap of (x, y) and (a, b).
    Assumes an overlap exists, i.e. y >= a and b >= x.
    """
    c = clamp(x, a, b)
    d = clamp(y, a, b)
    return c, d
# end def


try:
    from termcolor import colored
except ImportError:
    print("pip3 install termcolor")

    def colored(s, color=None, **kwargs):
        return s


def trace(n):
    """Returns a stack trace n frames deep"""
    s = extract_stack()
    frames = []
    for f in s[-n-1:-1]:
        # f is a stack frame like
        # ('/path/script.py', 42, 'funcname', 'current = line - of / code')
        frames.append((colored(path.basename(f[0]) + ':%i' % f[1], 'blue') + '(' + colored(f[2], 'green') + ')'))
    sep = colored(" > ", 'yellow')
    return sep.join(frames)


if IS_PY_3:
    complement = str.maketrans('ACGTacgt', 'TGCATGCA')
else:
    complement = string.maketrans('ACGTacgt', 'TGCATGCA')


def rcomp(seq_str: str) -> str:
    """Returns the reverse complement of the sequence in seq_str."""
    return seq_str.translate(complement)[::-1]


def comp(seq_str: str) -> str:
    """Returns the complement of the sequence in seq_str."""
    return seq_str.translate(complement)


if IS_PY_3:
    whitetoQ = str.maketrans(' |', '??')
else:
    whitetoQ = string.maketrans(' |', '??')


def markwhite(seq_str: str) -> str:
    return seq_str.translate(whitetoQ)


def nowhite(seq_str: str) -> str:
    """Gets rid of non-letters in a string."""
    return ''.join([c for c in seq_str if c in string.letters])


def nearest(a: NumT, l: Iterable[NumT]): return min(l, key=lambda x: abs(x - a))

def isWindows() -> bool:
    """Returns True if platform is detected as Windows, otherwise False"""
    if platform.system() == 'Windows':
        return True
    else:
        return False

def isMac() -> bool:
    """Returns True if platform is detected as Darwin, otherwise False"""
    try:
        return platform.system() == 'Darwin'
    except Exception:
        return path.exists('/System/Library/CoreServices/Finder.app')

def isLinux() -> bool:
    """Returns True if platform is detected as Linux, otherwise False"""
    if platform.system() == 'Linux':
        return True
    else:
        return False

def methodName() -> str:
    """Returns string containing name of the calling method."""
    return inspect.stack()[1][3]


def execCommandList(model_object: CNObjectT,
                    commands: List[UndoCommandT],
                    desc: str = None,
                    use_undostack: bool = True):
    """This is a wrapper for performing QUndoCommands, meant to ensure
    uniform handling of the undoStack and macro descriptions.

    When using the undoStack, commands are pushed onto self.undoStack()
    as part of a macro with description desc. Otherwise, command redo
    methods are called directly.
    """
    if use_undostack:
        us = model_object.undoStack()
        us.beginMacro(desc)
        for c in commands:
            us.push(c)
        us.endMacro()
    else:
        for c in commands:
            c.redo()
# end def


def doCmd(model_object: CNObjectT, command: UndoCommandT, use_undostack: bool):
    """Helper for pushing onto the undostack
    """
    if use_undostack:
        model_object.undoStack().push(command)
    else:
        command.redo()
# end def


def finalizeCommands(model_object: CNObjectT,
                    commands: List[UndoCommandT],
                    desc: str = None):
    """Used to enable interaction with the model but not push
    commands to the undostack.  In practice:

    1. Call a bunch of commands and don't push them to the undostack AKA:
        cmd.redo()
    2. call finalizeCommands() to push the cummulative change to the stack

    This assumes that the UndoCommands provided this function respresent
    a transition from the initial state to the final state

    Note:
        UndoCommands need to implement specialUndo (e.g. just call normal undo.)
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


def this_path() -> str:
    return os.path.abspath(os.path.dirname(__file__))

def beginSuperMacro(model_object: CNObjectT, desc: str = None):
    """SuperMacros can be used to nest multiple command lists.

    Normally execCommandList macros all the commands in a list.
    In some cases, multiple command lists need to be executed separately
    because of dependency issues. (e.g. in part.autoStaple, strands
    must be completely 1. created and 2. split before 3. xover installation.)
    """
    model_object.undoStack().beginMacro(desc)
# end def


def endSuperMacro(model_object: CNObjectT):
    """Ends a SuperMacro. Should be called after beginSuperMacro."""
    model_object.undoStack().endMacro()
# end def

def parse_args(argv=None, use_gui: bool = False):
    """Uses argparse to process commandline arguments.
    This also presents a nice command line help to the user, exposed with
    ``--help`` flag::

        python main.py --help

    Args:
        argv: you can initialize your app via::

                app = QApplication(sys.argv)
                parse_args(app.arguments())

            :meth:`QApplication.arguments()` returns a list of arguments with all Qt
            arguments stripped away. Qt command line args include::

                -style=<style> -stylesheet=<stylesheet> -widgetcount -reverse -qmljsdebugger -session=<session>

        use_gui: Default is ``False. ``True`` use then the parser will use
            :func:`parse_known_args`, otherwise :func:`parse_args()`. Unlike
            :func:`parse_args()`, :func:`parse_known_args()` will not cause
            abort by show the help message and exit, if it finds any
            unrecognized command-line arguments.

    Returns:
        NameSpace object. This can easily be converted to a regular dict through:
        argns.__dict__
    """
    parser = argparse.ArgumentParser(description="cadnano 2.5")
    parser.add_argument("--testing", "-t", action="store_true", help="Enable testing mode/environment.")
    parser.add_argument("--profile", "-p", action="store_true", help="Profile app execution.")
    parser.add_argument("--print-stats", "-P", action="store_true", help="Print profiling statistics.")
    parser.add_argument('--loglevel',
                        help="Specify logging level. Can be either DEBUG, INFO, WARNING, ERROR or any integer.")
    parser.add_argument("--debug-modules", nargs='*', metavar="MODULE-STR",
                        help="Debug modules whose names start with any of the given strings. For instance, to "
                             "debug the cadnano file decoder, use --debug-modules cadnano.fileio.decode ."
                             "To debug all gui modules, use --debug-modules cadnano.gui .")
    parser.add_argument("--file", "-f", metavar="designfile.json", help="cadnano design to load upon start up.")
    if use_gui:
        # Command line args might include Qt-specific switches and parameters.
        argns, unused = parser.parse_known_args(argv)
    else:
        argns, unused = parser.parse_args(argv), None
    return argns, unused


def init_logging(args=None, logdir: str = None):
    """Set up standard logging system based on parameters in args, e.g. loglevel
    and testing.
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

    # We want different output formatting for file vs console logging output.
    # File logs should be simple and easy to regex; console logs should be short and nice on the eyes
    logfilefmt = "%(asctime)s %(levelname)-6s - %(name)s:%(lineno)s - %(funcName)s() - %(message)s"
    logdatefmt = "%Y%m%d-%H:%M:%S"
    loguserfmt = "%(asctime)s %(levelname)-5s %(module)30s:%(lineno)-4s%(funcName)16s() %(message)s"
    logtimefmt = "%H:%M:%S"  # Nice for output to user in console and testing.
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
                            filename=logfilepath)
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
        logstreamhandler = logging.StreamHandler()  # default stream is sys.stderr
        logging.root.addHandler(logstreamhandler)
        logstreamformatter = logging.Formatter(loguserfmt, logtimefmt)
        logstreamhandler.setFormatter(logstreamformatter)

        # Set filter for debugging:
        if args.get('debug_modules'):
            def module_debug_filter(record):
                """All Filters attached to a logger or handler are asked.
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
            if name:
                yield (name, ''.join(seq))
            name, seq = line, []
        else:
            seq.append(line)
    if name:
        yield (name, ''.join(seq))


def qtdb_trace():
    """Make ``PDB`` usable by calling :func:`pyqtRemoveInputHook`.

    Otherwise, ``PDB`` is useless as the message::

        > QCoreApplication::exec: The event loop is already running

    is spammed to the console.

    When done, call qtdb_resume from the PDB prompt to return things back to
    normal.

    Note that ``PDB`` will drop you into the current frame (this function) and
    hitting 'n' is required to return to the frame you wanted ``PDB`` originally.
    This could probably be optimized at some point to manipulate the frame PDB
    starts in.
    """
    if False:
        logger.info('No debug')
        return
    else:
        import pdb
        from PyQt5.QtCore import pyqtRemoveInputHook

    pyqtRemoveInputHook()
    pdb.set_trace()


def qtdb_resume():
    """Resume normal PyQt operations after calling :fund:`qtdb_trace`.

    Note that this function assumes that pyqtRemoveInputHook has been called
    """
    from PyQt5.QtCore import pyqtRestoreInputHook

    pyqtRestoreInputHook()


def to_dot_path(filename: str) -> str:
    subpath = relpath(dirname(abspath(filename)), CADNANO_PATH)
    if sys.platform == 'win32':
        subpath = subpath.replace('\\', '.')
    else:
        subpath = subpath.replace('/', '.')
    return 'cadnano.' + subpath