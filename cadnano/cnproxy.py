class CNObject(object):
    def __init__(self, parent):
        self.parent = parent
        self._signals = {}
    #end def

    def parent(self):
        return self.parent
    #end def

    def setParent(self, parent):
        self.parent = parent
    #end def

    def connect(self, sender, bsignal, method):
        f = lambda x, y: method(x, *y)
        bsignal.connect(method, sender=sender)
        self.signals[(sender, bsignal, method)] = f

    def disconnect(self, sender, bsignal, method):
        f  = self.signals[(sender, bsignal, method)]
        bsignal.disconnect(f, sender=sender)
        del self.signals[(sender, bsignal, method)]

    def signals(self):
        return self.signals
    # end def

    def deleteLater(self):
        pass
    #end def
#end class

# class DummySignal(object):
#     def __init__(self, *args):
#         """ We don't actually do anything with argtypes. """
#         self.signalEmitters = {}
#         self.argtypes = args
#     # def __call__(self, emitter):
#     #     return self.__get__(emitter)

#     def __get__(self, emitter):
#         try:
#             return self.signalEmitters[emitter]
#         except KeyError:
#             new_sig = DummyBoundSignal()
#             self.signalEmitters[emitter] = new_sig
#             return new_sig

# class DummyBoundSignal(object):
#     def __init__(self):
#         self.targets = {}
#     def connect(self, target):
#         self.targets.add(target)
#     def disconnect(self, target):
#         self.targets.remove(target)
#     def emit(self, *args):
#         for t in self.targets:
#             t(*args)

class DummySignal(object):
    def __init__(self, *args, **kwargs):
        name = kwargs.get('name')
        if name is None:
            raise ValueError("missing name")
        self.targets = {}
        self.argtypes = args
        self.name = name
    def connect(self, target):
        self.targets.add(target)
    def disconnect(self, target):
        self.targets.remove(target)
    def emit(self, *args):
        for t in self.targets:
            t(*args)
# end class


from cadnano import undostack
from cadnano import undocommand

ProxySignal = DummySignal
ProxyObject = CNObject
UndoCommand = undocommand.UndoCommand
UndoStack = undostack.UndoStack

class TempApp(object):
    documentWasCreatedSignal = ProxySignal(name='documentWasCreatedSignal')

tapp = TempApp()


