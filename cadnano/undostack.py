# -*- coding: utf-8 -*-
from collections import deque

from cadnano.undocommand import UndoCommand


class UndoStack(object):
    def __init__(self, limit=10):
        self.undostack = deque()    # not using deque maxlen because pattern is awkward
        self.redostack = []
        self.limit = limit

        self.top_macro = None
        self.current_macro = None
        self.macro_stack = []
        self.macro_count = 0
    # end def

    def push(self, undocommand):
        if self.macro_count > 0:
            self.current_macro.addCommand(undocommand)
        else:
            self.appendUndoStack(undocommand)
    # end def

    def appendUndoStack(self, undocommand):
        stack = self.undostack
        stack.append(undocommand)
        undocommand.redo()
        if len(stack) > self.limit:
            stack.popleft()
    # end def

    def beginMacro(self, message):
        new_macro = UndoCommand(message)
        if self.current_macro is not None:
            self.macro_stack.append(self.current_macro)
        self.current_macro = new_macro
        if self.macro_count == 0:
            self.top_macro = new_macro
        self.macro_count += 1
        # print('b', new_macro, self.macro_count)
    # end def

    def endMacro(self):
        self.macro_count -= 1
        try:
            self.current_macro = self.macro_stack.pop()
        except:
            self.current_macro = None
        # print('e', self.current_macro self.macro_count)
        if self.macro_count == 0:
            self.appendUndoStack(self.top_macro)
    # end def

    def undo(self):
        if self.canUndo():
            undo_cmd = self.undostack.pop()
            undo_cmd.undo()
            self.redostack.append(undo_cmd)
    # end def

    def redo(self):
        if self.canRedo():
            redo_cmd = self.redostack.pop()
            redo_cmd.redo()
            self.undostack.append(redo_cmd)
    # end def

    def canUndo(self):
        return True if len(self.undostack) > 0 else False
    # end def

    def canRedo(self):
        return True if len(self.redostack) > 0 else False
    # end def

    def setUndoLimit(self, lim):
        self.limit = lim
    # end def