# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt

from cadnano.proxies.cnenum import ItemEnum

from .cnoutlineritem import (
    CNOutlinerItem,
    NAME_COL,
    VISIBLE_COL,
    COLOR_COL,
    LEAF_FLAGS
)
from cadnano.views.abstractitems import AbstractVirtualHelixItem
from cadnano.controllers import VirtualHelixItemController


class OutlineVirtualHelixItem(AbstractVirtualHelixItem, CNOutlinerItem):
    FILTER_NAME = "virtual_helix"
    CAN_NAME_EDIT = False

    def __init__(self, id_num, part_item):
        AbstractVirtualHelixItem.__init__(self, id_num, part_item)
        part = part_item.part()
        CNOutlinerItem.__init__(self, part, parent=part_item)
        self.setFlags(LEAF_FLAGS)
        self._controller = VirtualHelixItemController(self, part, False, False)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def __hash__(self):
        """ necessary as CNOutlinerItem as a base class is unhashable
        but necessary due to __init__ arg differences for whatever reason
        overload
        """
        return hash((self._id_num, self._model_part))

    def __repr__(self):
        return "VHI Outline %d" % self._id_num

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemEnum.VIRTUALHELIX
    # end def

    def updateCNModel(self):
        """Overloading CNOutlinerItem.updateCNModel
        """
        new_name = self.data(NAME_COL, Qt.DisplayRole)
        new_is_visible = self.data(VISIBLE_COL, Qt.DisplayRole)
        new_color = self.data(COLOR_COL, Qt.DisplayRole)
        part, id_num = self._model_part, self._id_num
        name, is_visible, color = part.getVirtualHelixProperties(id_num, ['name', 'is_visible', 'color'])
        # work around to disable name editing for OutlineVirtualHelixItems
        # QTreeWidgetItem can't have only single columns editable, its all or none
        if new_name != name:
            self.treeWidget().model().blockSignals(True)
            self.setData(NAME_COL, Qt.DisplayRole, name)
            self.treeWidget().model().blockSignals(False)
        if new_is_visible != is_visible:
            part.setVirtualHelixProperties(id_num, ['is_visible'], [new_is_visible])
        if new_color != color:
            part.setVirtualHelixProperties(id_num, ['color'], [new_color])
    # end def

    def isModelSelected(self, document):
        """Make sure the item is selected in the model

        Args:
            document (Document): reference the the model :class:`Document`
        """
        return document.isVirtualHelixSelected(self._model_part, self._id_num)
    # end def

    ### SLOTS ###
# end class
