# -*- coding: utf-8 -*-
"""VirtualHelixItem for the PropertyView.

Attributes:
    KEY_COL (int): QTreeWidgetItem column that will display property keys
    VAL_COL (int): QTreeWidgetItem column that will display property values
"""
from typing import (
    List
)

from PyQt5.QtCore import (
    Qt,
    QModelIndex
)
from PyQt5.QtWidgets import (
    QTreeWidgetItem,
    QDoubleSpinBox,
    QSpinBox,
    QWidget,
    QStyleOptionViewItem
)

from cadnano.proxies.cnenum import (
    ItemEnum,
    EnumType
)
from cadnano.controllers import VirtualHelixItemController
from .cnpropertyitem import CNPropertyItem
from cadnano.cntypes import (
    VirtualHelixT,
    NucleicAcidPartT,
    KeyT,
    ValueT
)


KEY_COL = 0
VAL_COL = 1


class VirtualHelixSetItem(CNPropertyItem):
    """VirtualHelixItem class for the PropertyView.
    """
    _GROUPNAME = "helices"

    def __init__(self, **kwargs):
        """Summary

        Args:
            model_part (NucleicAcidPart): The model part
            parent (TYPE): Description
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            key (str, optional): Default is ``None``
        """
        super(VirtualHelixSetItem, self).__init__(**kwargs)
        if self._key == "name":
            for outline_vh in self.outlineViewObjList():
                self._controller_list.append(VirtualHelixItemController(self, outline_vh.part(), True, False))
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self) -> EnumType:
        """Overrides AbstractPropertyPartItem.itemType

        Returns:
            ItemEnum: VIRTUALHELIX
        """
        return ItemEnum.VIRTUALHELIX
    # end def

    # SLOTS
    def partVirtualHelixPropertyChangedSlot(self, sender: NucleicAcidPartT,
                                                    id_num: int,
                                                    virtual_helix: VirtualHelixT,
                                                    keys: KeyT,
                                                    values: ValueT):
        """
        Args:
            sender: Model object that emitted the signal.
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            keys: Description
            values: Description
        """
        if virtual_helix in self.outlineViewObjSet():
            for key, val in zip(keys, values):
                # print("change slot", key, val)
                self.setValue(key, val)
    # end def

    def partVirtualHelixResizedSlot(self, sender: NucleicAcidPartT,
                                        id_num: int,
                                        virtual_helix: VirtualHelixT):
        # print("resize slot")
        if virtual_helix in self.outlineViewObjSet():
            val = virtual_helix.getSize()
            self.setValue('length', int(val))
    # end def

    def partVirtualHelixRemovingSlot(self, sender: NucleicAcidPartT,
                                        id_num: int,
                                        virtual_helix: VirtualHelixT,
                                        neighbors: List[int]):
        """
        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            neighbors (list):
        """
        if virtual_helix in self.outlineViewObjSet():
            self.disconnectSignals()
            self.parent().removeChild(self)
    # end def

    def partVirtualHelixRemovedSlot(self, sender: NucleicAcidPartT, id_num: int):
        """
        Args:
            sender: Model object that emitted the signal.
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
        """
    # end def

    def configureEditor(self, parent_qw: QWidget,
                            option: QStyleOptionViewItem,
                            model_index: QModelIndex) -> QWidget:
        """
        Args:
            parent_qw: Description
            option: Description
            model_index: Description

        Returns:
            the widget used to edit the item specified by index for editing
        """
        cn_m = self.outlineViewObj()
        key = self.key()
        if key == 'eulerZ':
            editor = QDoubleSpinBox(parent_qw)
            tpb, _ = cn_m.getTwistPerBase()
            editor.setSingleStep(tpb)
            editor.setDecimals(1)
            editor.setRange(0, 359)
        elif key == 'scamZ':
            editor = QDoubleSpinBox(parent_qw)
            tpb, _ = cn_m.getTwistPerBase()
            editor.setSingleStep(tpb)
            editor.setDecimals(1)
            editor.setRange(0, 359)
        elif key == 'length':
            editor = QSpinBox(parent_qw)
            bpr, length = cn_m.getProperty(['bases_per_repeat', 'length'])
            editor.setRange(length, 4*length)
            editor.setSingleStep(bpr)
        elif key == 'z' and cn_m.part().isZEditable():
            editor = QDoubleSpinBox(parent_qw)
            bw = cn_m.part().baseWidth()
            editor.setSingleStep(bw)
            editor.setRange(-bw*21, bw*21)
        else:
            editor = CNPropertyItem.configureEditor(self, parent_qw, option, model_index)
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
            for vh in self.outlineViewObjList():
                # print("vh", vh.idNum(), value, vh.getSize())
                if value != vh.getSize():
                    vh.setSize(value)
        elif key == 'z':
            # print("Property view 'z' updating", key, value)
            for vh in self.outlineViewObjList():
                if value != vh.getZ():
                    vh.setZ(value)
        else:
            for vh in self.outlineViewObjList():
                if value != vh.getProperty(key):
                    vh.setProperty(key, value)
        u_s.endMacro()
    # end def
# end class
