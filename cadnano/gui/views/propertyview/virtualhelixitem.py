"""VirtualHelixItem for the PropertyView.

Attributes:
    KEY_COL (int): QTreeWidgetItem column that will display property keys
    VAL_COL (int): QTreeWidgetItem column that will display property values
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox
from cadnano.enum import ItemType
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from .cnpropertyitem import CNPropertyItem

KEY_COL = 0
VAL_COL = 1

class SimpleVirtualHelixItem(AbstractVirtualHelixItem):
    """ Has no part_item
    """
    def __init__(self, id_num, part):
        self._id_num = id_num
        self._part_item = None
        self._model_part = part
        self.is_active = False

    @property
    def editable_properties(self):
        return self._model_part.vh_editable_properties

class VirtualHelixSetItem(CNPropertyItem):
    """VirtualHelixItem class for the PropertyView.
    """
    _GROUPNAME = "helices"

    def __init__(self, reference_list, parent, key=None):
        """Summary

        Args:
            model_part (Part): The model part
            parent (TYPE): Description
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            key (None, optional): Description
        """
        if key is None:
            reference_list = [SimpleVirtualHelixItem(id_num, part) for part, id_num in reference_list]
            self.lookup = set(reference_list)

        super(VirtualHelixSetItem, self).__init__(reference_list, parent, key=key)
        if key is None:
            for vhi in reference_list:
                self._controller_list.append(VirtualHelixItemController(self, vhi.part(), True, False))
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        """Overrides AbstractPropertyPartItem.itemType

        Returns:
            ItemType: VIRTUALHELIX
        """
        return ItemType.VIRTUALHELIX
    # end def

    # SLOTS
    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, keys, values):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            keys (TYPE): Description
            values (TYPE): Description

        Returns:
            TYPE: Description
        """
        if (sender, id_num) in self.lookup:
            for key, val in zip(keys, values):
                # print("change slot", key, val)
                self.setValue(key, val)

    def partVirtualHelixRemovingSlot(self, sender, id_num, neighbors):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            neighbors (list):
        """
        if (sender, id_num) in self.lookup:
            self.disconnectSignals()
            self._cn_model_list = None
            self.parent().removeChild(self)
    # end def

    def partVirtualHelixRemovedSlot(self, sender, id_num):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
        """
        pass
    # end def

    def configureEditor(self, parent_QWidget, option, model_index):
        """Summary

        Args:
            parent_QWidget (TYPE): Description
            option (TYPE): Description
            model_index (TYPE): Description

        Returns:
            TYPE: Description
        """
        cn_m = self._cn_model_list[0]
        key = self.key()
        if key == 'eulerZ':
            editor = QDoubleSpinBox(parent_QWidget)
            tpb, _ = cn_m.getTwistPerBase()
            editor.setSingleStep(tpb)
            editor.setDecimals(1)
            editor.setRange(0, 359)
        elif key == 'scamZ':
            editor = QDoubleSpinBox(parent_QWidget)
            tpb, _ = cn_m.getTwistPerBase()
            editor.setSingleStep(tpb)
            editor.setDecimals(1)
            editor.setRange(0, 359)
        elif key == 'length':
            editor = QSpinBox(parent_QWidget)
            bpr, length = cn_m.getProperty(['bases_per_repeat',
                                                    'length'])
            editor.setRange(length, 4*length)
            editor.setSingleStep(bpr)
        elif key == 'z' and self._model_part.isZEditable():
            editor = QDoubleSpinBox(parent_QWidget)
            bw = cm.part().baseWidth()
            editor.setSingleStep(bw)
            editor.setRange(-bw*21, bw*21)
        else:
            editor = CNPropertyItem.configureEditor(self, parent_QWidget, option, model_index)
        return editor
    # end def

    def updateCNModel(self):
        """Notify the cadnano model that a property may need updating.
        This method should be called by the item model dataChangedSlot.
        """
        value = self.data(1, Qt.DisplayRole)
        key = self._key
        u_s = self.treeWidget().undoStack()
        u_s.beginMacro("Multi Property VH Edit: %s" % key)
        if key == 'length':
            # print("Property view 'length' updating",
            #     key, value, [x.idNum() for x in self._cn_model_list])
            for vhi in self._cn_model_list:
                vhi.setSize(value)
        elif key == 'z':
            # print("Property view 'z' updating", key, value)
            for vhi in self._cn_model_list:
                vhi.setZ(value)
        else:
            print("yeak", key)
            for vhi in self._cn_model_list:
                vhi.setProperty(key, value)
        u_s.endMacro()
    # end def

    def setValue(self, property_key, new_value):
        """Summary

        Args:
            property_key (TYPE): Description
            new_value (TYPE): Description

        Returns:
            TYPE: Description
        """
        p_i = self._prop_items[property_key]
        current_value = p_i.data(VAL_COL, Qt.DisplayRole)
        if current_value != new_value:
            p_i.setData(VAL_COL, Qt.EditRole, new_value)
    # end def

    def getItemValue(self, property_key):
        """Summary

        Args:
            property_key (TYPE): Description

        Returns:
            TYPE: Description
        """
        return self._prop_items[property_key].data(VAL_COL, Qt.DisplayRole)
    # end def
# end class
