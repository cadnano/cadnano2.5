# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem

class QAbstractPartItem(QGraphicsRectItem):
    """ Use for single inheritance
    QAbstractPartItem is a base class for partitems in all views.
    It includes slots that get connected in PartItemController which
    can be overridden.

    If you want to add a new signal to the model, adding the slot here
    means it's not necessary to add the same slot to every item across
    all views.
    """

    def __init__(self, model_part_instance, viewroot, parent):
        super(QAbstractPartItem, self).__init__(parent)
        self._model_instance = model_part_instance
        self._model_part = m_p = model_part_instance.reference()
        self._model_props = m_p.getModelProperties()
        self._viewroot = viewroot
        self._oligo_item_hash = {}
        self._virtual_helix_item_hash = {}
        self.active_virtual_helix_item = None
        self.is_active = False
        m_p.setInstanceProperty(model_part_instance, '%s:position' % (viewroot.name), (0., 0.))
    # end def

    def part(self):
        return self._model_part

    def partInstance(self):
        return self._model_instance

    def cnModel(self):
        return self._model_part

    def getFilterSet(self):
        return self._viewroot._document.filter_set
    # end def

    def setMovable(self, is_movable):
        self._viewroot.manager.select_tool.resetSelections()
        self.setFlag(QGraphicsItem.ItemIsMovable, is_movable)
    # end def

    def isMovable(self):
        return self.flags() & QGraphicsItem.ItemIsMovable
    # end def

    def finishDrag(self):
        """ set the view position in the model
        Does NOT convert to model coordinates, for now
        """
        pos = self.pos()
        position = pos.x(), pos.y()
        view_name = self._viewroot.name
        self._model_part.changeInstanceProperty(self._model_instance,
                                        view_name, 'position', position)
    # end def

    def document(self):
        """Return a reference to the model's document object"""
        return self._model_part.document()
    # end def

    def scaleFactor(self):
        return self.scale_factor
    # end def

    def idToVirtualHelixItem(self, id_num):
        return self._virtual_helix_item_hash[id_num]
    # end def

    def setActive(self):
        self._model_part.setActive(True)
    # end def

    def partZDimensionsChangedSlot(self, part, min_id_num, max_id_num):
        """ Accounts for Z translations in parts
        Args:
            part (Part):
            min_id_num (int): id number of the least Z Virtual Helix
            max_id_num (int): id number of most Z Virtual Helix
        """
        pass

    def partOligoAddedSlot(self, part, oligo):
        pass

    def partParentChangedSlot(self, sender):
        pass

    def partPropertyChangedSlot(model_part, property_key, new_value):
        pass

    def partRemovedSlot(self, sender):
        pass

    def partSelectedChangedSlot(self, model_part, is_selected):
        pass

    def partActiveVirtualHelixChangedSlot(self, sender, id_num):
        pass

    def partActiveBaseInfoSlot(self, sender, info):
        pass

    def partActiveChangedSlot(self, sender, is_active):
        pass

    def partInstancePropertySlot(self, sender, view_name, key, value):
        if view_name == self._viewroot.name:
            if key == 'position':
                self.setPos(*value)
    # end def

    def partVirtualHelixAddedSlot(self, model_part, id_num, virtual_helix, neighbors):
        pass

    def partVirtualHelixRemovingSlot(self, sender, id_num, virtual_helix, neighbors):
        pass

    def partVirtualHelixRemovedSlot(self, sender, id_num):
        pass

    def partVirtualHelixResizedSlot(self, sender, id_num, virtual_helix):
        pass

    def partVirtualHelicesTranslatedSlot(self, sender, vh_set):
        pass

    def partVirtualHelicesSelectedSlot(self, sender, vh_set, is_adding):
        """ is_adding (bool): adding (True) virtual helices to a selection
        or removing (False)
        """
        pass

    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, virtual_helix, new_value):
        pass

    def partDocumentSettingChangedSlot(self, part, key, value):
        pass
    # end defS
# end class


class AbstractPartItem(object):
    """ Use for multiple inheritance
    AbstractPartItem is a base class for partitems in all views.
    It includes slots that get connected in PartItemController which
    can be overridden.

    If you want to add a new signal to the model, adding the slot here
    means it's not necessary to add the same slot to every item across
    all views.
    """

    def __init__(self):
        self._oligo_item_hash = {}
        self._virtual_helix_item_hash = {}
        self.active_virtual_helix_item = None
        self.is_active = False
    # end def

    def part(self):
        return self._model_part
    # end def

    def setMovable(self, is_movable):
        self.setFlag(QGraphicsItem.ItemIsMovable, is_movable)
    # end def

    def document(self):
        """Return a reference to the model's document object"""
        return self._model_part.document()
    # end def

    def scaleFactor(self):
        return self.scale_factor
    # end def

    def idToVirtualHelixItem(self, id_num):
        return self._virtual_helix_item_hash[id_num]
    # end def

    def setActive(self):
        print("AbstractPartItem setActive", self._model_part)
        self._model_part.setActive(True)
    # end def

    def partZDimensionsChangedSlot(self, part, min_id_num, max_id_num):
        """ Accounts for Z translations in parts
        Args:
            part (Part):
            min_id_num (int): id number of the least Z Virtual Helix
            max_id_num (int): id number of most Z Virtual Helix
        """
        pass

    def partOligoAddedSlot(self, part, oligo):
        pass

    def partParentChangedSlot(self, sender):
        pass

    def partPropertyChangedSlot(model_part, property_key, new_value):
        pass

    def partRemovedSlot(self, sender):
        pass

    def partSelectedChangedSlot(self, model_part, is_selected):
        pass

    def partActiveVirtualHelixChangedSlot(self, sender, id_num):
        pass

    def partActiveBaseInfoSlot(self, sender, info):
        pass

    def partActiveChangedSlot(self, sender, is_active):
        pass

    def partInstancePropertySlot(self, sender, view_name, key, value):
        pass

    def partVirtualHelixAddedSlot(self, model_part, id_num, virtual_helix, neighbors):
        pass

    def partVirtualHelixRemovingSlot(self, sender, id_num, virtual_helix, neighbors):
        pass

    def partVirtualHelixRemovedSlot(self, sender, id_num):
        pass

    def partVirtualHelixResizedSlot(self, sender, id_num, virtual_helix):
        pass


    def partVirtualHelicesTranslatedSlot(self, sender, vh_set):
        pass

    def partVirtualHelicesSelectedSlot(self, sender, vh_set, is_adding):
        """is_adding (bool): adding (True) virtual helices to a selection
        or removing (False)
        """
        pass

    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, virtual_helix, new_value):
        pass

    def partDocumentSettingChangedSlot(self, part, key, value):
        pass
    # end def
# end class
