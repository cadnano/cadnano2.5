"""VirtualHelixItem for the PropertyView.

Attributes:
    KEY_COL (int): QTreeWidgetItem column that will display property keys
    VAL_COL (int): QTreeWidgetItem column that will display property values
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox
from cadnano.cnenum import ItemType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from .cnpropertyitem import CNPropertyItem

KEY_COL = 0
VAL_COL = 1

class VirtualHelixSetItem(CNPropertyItem):
    """VirtualHelixItem class for the PropertyView.
    """
    _GROUPNAME = "helices"

    def __init__(self, **kwargs):
        """Summary

        Args:
            model_part (Part): The model part
            parent (TYPE): Description
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            key (None, optional): Description
        """
        super().__init__(**kwargs)
        if self._key == "name":
            for vh in self.cnModelList():
                self._controller_list.append(VirtualHelixItemController(self, vh.part(), True, False))
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
    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, virtual_helix, keys, values):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            keys (TYPE): Description
            values (TYPE): Description

        Returns:
            TYPE: Description
        """
        # print("prop slot", self._cn_model_set)
        if virtual_helix in self.cnModelSet():
            for key, val in zip(keys, values):
                # print("change slot", key, val)
                self.setValue(key, val)
    # end def

    def partVirtualHelixResizedSlot(self, sender, id_num, virtual_helix):
        # print("resize slot")
        if virtual_helix in self.cnModelSet():
            val = virtual_helix.getSize()
            self.setValue('length', int(val))
    # end def

    def partVirtualHelixRemovingSlot(self, sender, id_num, virtual_helix, neighbors):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            neighbors (list):
        """
        if virtual_helix in self.cnModelSet():
            self.disconnectSignals()
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
        cn_m = self.cnModel()
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
            # print("Property view 'length' updating")
            for vh in self.cnModelList():
                if value != vh.getSize():
                    vh.setSize(value)
        elif key == 'z':
            # print("Property view 'z' updating", key, value)
            for vh in self.cnModelList():
                if value != vh.getZ():
                    vh.setZ(value)
        else:
            for vh in self.cnModelList():
                if value != vh.getProperty(key):
                    vh.setProperty(key, value)
        u_s.endMacro()
    # end def
# end class
