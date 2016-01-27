from PyQt5.QtCore import Qt

from cadnano.enum import ItemType

from .cnoutlineritem import CNOutlinerItem, NAME_COL, VISIBLE_COL, COLOR_COL

from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController


class VirtualHelixItem(AbstractVirtualHelixItem, CNOutlinerItem):
    _filter_name = "virtual_helix"
    def __init__(self, id_num, part_item):
        AbstractVirtualHelixItem.__init__(self, id_num, part_item)
        model_part = self._model_part
        CNOutlinerItem.__init__(self, model_part, parent=part_item)
        name, color = self.getProperty(['name', 'color'])
        self.setData(NAME_COL, Qt.DisplayRole, name)
        self.setData(COLOR_COL, Qt.DisplayRole, color)
        self._controller = VirtualHelixItemController(self, model_part, False, False)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def __hash__(self):
        """ necessary as CNOutlinerItem as a base class is unhashable
        but necessary due to __init__ arg differences for whatever reason
        overload
        """
        return hash((self._id_num, self._model_part))

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.VIRTUALHELIX
    # end def

    def updateCNModel(self):
        """
        """
        cn_model = self._cn_model
        new_name = self.data(NAME_COL, Qt.DisplayRole)
        new_is_visible = self.data(VISIBLE_COL, Qt.DisplayRole)
        new_color = self.data(COLOR_COL, Qt.DisplayRole)
        name, is_visible, color = self.getProperty(['name', 'is_visible', 'color'])
        # work around to disable name editing for VirtualHelixItems
        # QTreeWidgetItem can't have only single columns editable, its all or none
        if new_name != name:
            self.treeWidget().model().blockSignals(True)
            self.setData(NAME_COL, Qt.DisplayRole, name)
            self.treeWidget().model().blockSignals(False)
        if new_is_visible != is_visible:
            self.setProperty('is_visible', new_is_visible)
        if new_color != color:
            self.setProperty('color', new_color)
    # end def

    ### SLOTS ###
# end class
