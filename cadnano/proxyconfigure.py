import cadnano.cnproxy as cnp


def proxyConfigure(signal_type=None):
    """ call once per application at the start of
    the import chain
    """
    if signal_type == "blinker":
        import blinker

        def emit(self, a, *args):
            self.send(a, data=args)

        def newsignal(self, *args, **kwargs):
            name = kwargs.get('name')
            if name is None:
                raise ValueError("missing name")
            return blinker.base.signal(name)

        blinker.base.NamedSignal.emit = emit

        cnp.ProxySignal = newsignal
        cnp.ProxyObject = cnp.CNObject
        import cadnano
        cadnano.app = cnp.app

    elif signal_type == "PyQt":
        from PyQt5.QtCore import QObject, pyqtSignal
        from PyQt5.QtWidgets import QUndoCommand, QUndoStack
        cnp.ProxySignal = pyqtSignal
        cnp.BaseObject = QObject
        cnp.UndoCommand = QUndoCommand
        cnp.UndoStack = QUndoStack
    else:
        cnp.ProxySignal = cnp.DummySignal
        cnp.BaseObject = cnp.ProxyObject
        # cnp.UndoCommand = cnp.UndoCommand
        # cnp.UndoStack = cnp.UndoStack
        import cadnano
        cadnano.app = cnp.app
