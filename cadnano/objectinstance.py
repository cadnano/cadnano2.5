from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject


class ObjectInstance(CNObject):
    def __init__(self, reference_object, parent=None):
        super(ObjectInstance, self).__init__(reference_object)
        self._parent = parent   # parent is either a document or assembly
        self._ref_object = reference_object
        # self._position = [0, 0, 0, 0, 0, 0]  # x, y, z, phi, theta, psi
        self._properties = {}
    # end def

    # SIGNALS #
    instanceDestroyedSignal = ProxySignal(CNObject,         name="instanceDestroyedSignal")
    instancePropertyChangedSignal = ProxySignal(CNObject,   name="instancePropertyChangedSignal")
    instanceParentChangedSignal = ProxySignal(CNObject,     name="instanceParentChangedSignal")

    # SLOTS #

    # METHODS #
    def destroy(self):
        self.setParent(None)
        self.deleteLater()
    # end def

    def reference(self):
        return self._ref_object
    # end def

    def parent(self):
        return self._parent
    # end def

    def properties(self):
        return self._properties.copy()
    # end def

    def setProperty(self, key, val):
        self._properties[key] = val
    # end def

    def getProperty(self, key):
        return self._properties[key]
    # end def

    def shallowCopy(self):
        oi = ObjectInstance(self._ref_object, self._parent)
        oi._properties =  oi._properties.copy()
        return oi
    # end def

    def deepCopy(self, reference_object, parent):
        oi = ObjectInstance(reference_object, parent)
        oi._properties =  oi._properties.copy()
        return oi
    # end def
# end class
