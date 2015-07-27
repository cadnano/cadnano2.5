import cadnano.util as util
from cadnano.cnproxy import ProxyObject, ProxySignal
from cadnano.cnproxy import UndoCommand, UndoStack

class ObjectInstance(ProxyObject):

    def __init__(self, reference_object, parent=None):
        super(ObjectInstance, self).__init__(reference_object)
        self._parent = parent   # parent is either a document or assembly
        self._object = reference_object
        self._position = [0, 0, 0, 0, 0, 0]  # x, y, z,phi, theta, psi
    # end def

    ### SIGNALS ###
    instanceDestroyedSignal = ProxySignal(ProxyObject,
                                        name="instanceDestroyedSignal")
    instanceMovedSignal = ProxySignal(ProxyObject,
                                            name="instanceMovedSignal")
    instanceParentChangedSignal = ProxySignal(ProxyObject,
                                        name="instanceParentChangedSignal")

    ### SLOTS ###

    ### METHODS ###
    def undoStack(self):
        return self._document.undoStack()

    def destroy(self):
        self.setParent(None)
        self.deleteLater()
    # end def

    def reference(self):
        return self._object
    # end def

    def wipe(self, doc):
       self._object.setDocument(None)
       doc.setSelectedInstance(None)
       doc.removeChild(self._object)
    # end def

    def unwipe(self, doc):
        obj = self._object
        obj.setDocument(doc)
        doc.addChild(obj)
        doc.setSelectedInstance(self)
    # end def

    def parent(self):
        return self._parent

    def position(self):
        return self._position

    def shallowCopy(self):
        oi = ObjectInstance(self._object, self._parent)
        oi._position = list(self._position)
        return oi
    # end def

    def deepCopy(self, reference_object, parent):
        oi = ObjectInstance(reference_object, parent)
        oi._position = list(self._position)
        return oi