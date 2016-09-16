# -*- coding: utf-8 -*-
from uuid import uuid4

from cadnano import util
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from .changeinstancepropertycmd import ChangeInstancePropertyCommand
from cadnano.setpropertycmd import SetPropertyCommand
# from cadnano.addinstancecmd import AddInstanceCommand
# from cadnano.removeinstancecmd import RemoveInstanceCommand

class Part(CNObject):
    """A Part is a group of VirtualHelix items that are on the same lattice.
    Parts are the model component that most directly corresponds to a
    DNA origami design.

    Parts are always parented to the document.
    Parts know about their oligos, and the internal geometry of a part
    Copying a part recursively copies all elements in a part: StrandSets,
    Strands, etc

    PartInstances are parented to either the document or an assembly
    PartInstances know global position of the part
    Copying a PartInstance only creates a new PartInstance with the same
    Part(), with a mutable parent and position field.
    """
    editable_properties = ['name', 'color', 'is_visible', 'grid_type']

    def __init__(self, *args, **kwargs):
        """Sets the parent document, sets bounds for part dimensions, and sets up
        bookkeeping for partInstances, Oligos, VirtualHelix's, and helix ID
        number assignment.
        """
        self._document = document = kwargs.get('document', None)
        super(Part, self).__init__(document)
        self._instance_count = 0
        self._instances = set()
        # Properties
        self.view_properties = {}

        # TODO document could be None
        self._group_properties = {'name': "Part%d" % len(document.children()),
                                  'color': "#cc0000", # outlinerview will override from styles
                                  'is_visible': True
                                  }

        self.uuid = kwargs['uuid'] if 'uuid' in kwargs else uuid4().hex

        # Selections
        self._selections = {}

        if self.__class__ == Part:
            e = "This class is abstract. Perhaps you want HoneycombPart."
            raise NotImplementedError(e)
    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<%s %s>" % (cls_name, str(id(self))[-4:])

    ### SIGNALS ###

    partZDimensionsChangedSignal = ProxySignal(CNObject, int, int, bool, name='partZDimensionsChangedSignal')
    """self, id_min, id_max, zoom_to_fit"""

    partInstanceAddedSignal = ProxySignal(CNObject, name='partInstanceAddedSignal')
    """self"""

    partParentChangedSignal = ProxySignal(CNObject, name='partParentChangedSignal')
    """self"""

    partRemovedSignal = ProxySignal(CNObject, name='partRemovedSignal')
    """self"""

    partPropertyChangedSignal = ProxySignal(CNObject, object, object, name='partPropertyChangedSignal')
    """self, property_name, new_value"""

    partSelectedChangedSignal = ProxySignal(CNObject, object, name='partSelectedChangedSignal')
    """self, is_selected"""

    partActiveChangedSignal = ProxySignal(CNObject, bool, name='partActiveChangedSignal')
    """self, is_active"""

    partViewPropertySignal = ProxySignal(CNObject, str, str, object, name='partViewPropertySignal')
    """self, view, key, val"""

    partDocumentSettingChangedSignal = ProxySignal(object, str, object, name='partDocumentSettingChangedSignal')
    """self, key, value"""

    ### SLOTS ###

    ### ACCESSORS ###
    def document(self):
        return self._document
    # end def

    def setDocument(self, document):
        self._document = document
    # end def

    def canRemove(self):
        """If _instance_count == 1 you could remove the part
        """
        return self._instance_count == 1
    # end def

    def canReAdd(self):
        """If _instance_count == 0 you could re-add the part
        """
        return self._instance_count == 0
    # end def

    def incrementInstance(self, document, obj_instance):
        self._instance_count += 1
        self._instances.add(obj_instance)
        self._document = document
        document.addInstance(obj_instance)
        if self._instance_count == 1:
            document.addRefObj(self)
    # end def

    def decrementInstance(self, obj_instance):
        ic = self._instance_count
        self._instances.remove(obj_instance)
        document = self._document
        document.removeInstance(obj_instance)
        if ic == 0:
            raise IndexError("Can't have less than zero instance of a Part")
        ic -= 1
        if ic == 0:
            document.removeRefObj(self)
            self._document = None
        self._instance_count = ic
        return ic
    # end def

    def getProperty(self, key):
        return self._group_properties[key]
    # end def

    def getOutlineProperties(self):
        props = self._group_properties
        return props['name'], props['color'], props['is_visible']
    # end def

    def getColor(self):
        return self._group_properties['color']

    def setInstanceProperty(self, part_instance, key, value):
        self.view_properties[key] = value
    # end def

    def getInstanceProperty(self, part_instance, key):
        return self.view_properties[key]
    # end def

    def getName(self):
        return self._group_properties['name']
    # end def

    def getModelProperties(self):
        """

        Returns:
            dict: group properties
        """
        return self._group_properties
    # end def

    def setProperty(self, key, value, use_undostack=True):
        if key == 'is_visible':
            self._document.clearAllSelected()
        if use_undostack:
            c = SetPropertyCommand([self], key, value)
            self.undoStack().push(c)
        else:
            self._setProperty(key, value)
    # end def

    def _setProperty(self, key, value):
        self._group_properties[key] = value
        self.partPropertyChangedSignal.emit(self, key, value)
    # end def

    def changeInstanceProperty(self, part_instance, view, key, value, use_undostack=True):
        c = ChangeInstancePropertyCommand(self, part_instance, view, key, value)
        util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
    # end def
# end class
