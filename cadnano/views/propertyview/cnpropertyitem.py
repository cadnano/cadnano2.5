# -*- coding: utf-8 -*-
"""cnpropertyitem description"""
from typing import (
    List,
    Set
)

from PyQt5.QtCore import (
    Qt,
    QModelIndex
)
from PyQt5.QtWidgets import (
    QTreeWidgetItem,
    QDoubleSpinBox,
    QSpinBox,
    QLineEdit,
    QCheckBox,
    QComboBox,
    QWidget,
    QStyleOptionViewItem
)

from cadnano.views.outlinerview.cnoutlineritem import CNOutlinerItem
from cadnano.proxies.cnenum import (
    ENUM_NAMES,
    EnumType
)
from cadnano.cntypes import (
    PropertyEditorWidgetT
)
KEY_COL = 0
VAL_COL = 1


class CNPropertyItem(QTreeWidgetItem):
    """enum types from cadnano.proxies.cnenum are supported by the convention that
    the key will end with the string '_type' and the list of ENUM_NAMES
    is fetched by key to populate the QComboBox

    Attributes:
        is_enum (bool): Description
    """
    _GROUPNAME = "items"

    def __init__(self, parent: PropertyEditorWidgetT, key: str = None):
        """
        Args:
            parent: Description
            key: Default is ``None``
        """
        super(CNPropertyItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        cn_model_list = self.outlineViewObjList()
        self._controller_list = []
        self.is_enum = False
        if key is None:
            root = parent.invisibleRootItem()  # add propertyitems as siblings
            # root = parent
            # Properties
            self._prop_items = {}

            model_props = {}
            for cn_model in cn_model_list:
                for cn_key, cn_val in cn_model.getModelProperties().items():
                    if cn_key in model_props:
                        if cn_val != model_props[cn_key]:
                            model_props[cn_key] = '~~multiple~~'
                    else:
                        model_props[cn_key] = cn_val
            # end for

            # add properties alphabetically, but with 'name' on top
            if len(cn_model_list) == 1:
                name = cn_model_list[0].getName()
                if name is None:
                    name = "generic"
            else:
                # print("trying multiple")
                name = "%d %s..." % (len(cn_model_list), self._GROUPNAME)
            self._key = the_key = "name"
            self._prop_items[the_key] = self
            self.setData(KEY_COL, Qt.EditRole, the_key)
            self.setData(VAL_COL, Qt.EditRole, name)

            constructor = type(self)
            for that_key in sorted(model_props):
                if that_key == 'name':
                    continue
                p_i = constructor(parent=root, key=that_key)
                self._prop_items[that_key] = p_i
                p_i.setData(KEY_COL, Qt.EditRole, that_key)
                model_value = model_props[that_key]
                if that_key.endswith('_type'):
                    model_value = ENUM_NAMES[that_key][model_value]
                    p_i.is_enum = True
                elif isinstance(model_value, float):
                    model_value = "%0.2f" % model_value
                elif isinstance(model_value, bool):
                    model_value = model_value
                elif isinstance(model_value, int):
                    model_value = str(model_value)
                elif not isinstance(model_value, str):  # can't get non-strings to work
                    model_value = str(model_value)
                p_i.setData(VAL_COL, Qt.EditRole, model_value)
        else:
            self._key = key
    # end def

    @property
    def _viewroot(self):
        return self.treeWidget()

    def key(self) -> str:
        """
        Returns:
            the key string
        """
        return self._key

    ### PUBLIC SUPPORT METHODS ###
    def outlineViewObj(self) -> CNOutlinerItem:
        """Summary

        Returns:
            TYPE: Description
        """
        return self.outlineViewObjList()[0]
    # end def

    def outlineViewObjList(self) -> List[CNOutlinerItem]:
        """Summary

        Returns:
            list: cn_model items
        """
        return self.treeWidget().outlineViewObjList()
    # end def

    def outlineViewObjSet(self) -> Set[CNOutlinerItem]:
        return self.treeWidget().outlineViewObjSet()

    def itemType(self) -> EnumType:
        """
        Returns:
            None
        """
        return None
    # end def

    def disconnectSignals(self):
        """
        """
        for controller in self._controller_list:
            controller.disconnectSignals()
        self._controller_list = []
    # end def

    def configureEditor(self, parent_qw: QWidget,
                            option: QStyleOptionViewItem,
                            model_inde: QModelIndex) -> QWidget:
        """
        Args:
            parent_qw: Description
            option Description
            model_index: Description

        Returns:
            the widget used to edit the item specified by index for editing

        Raises:
            NotImplementedError: Description
        """
        cn_m = self.outlineViewObj()
        key = self.key()
        if key == 'name':
            return QLineEdit(parent_qw)
        elif key not in cn_m.editable_properties:
            return None
        if self.is_enum:
            editor = QComboBox(parent_qw)
            for val in ENUM_NAMES[key]:
                editor.addItem(val)
        else:
            data_type = type(model_index.model().data(model_index, Qt.DisplayRole))
            if data_type is str:
                editor = QLineEdit(parent_qw)
            elif data_type is int:
                editor = QSpinBox(parent_qw)
                editor.setRange(-359, 359)
            elif data_type is float:
                editor = QDoubleSpinBox(parent_qw)
                editor.setDecimals(0)
                editor.setRange(-359, 359)
            elif data_type is bool:
                editor = QCheckBox(parent_qw)
            elif isinstance(None, data_type):
                return None
            else:
                raise NotImplementedError
        return editor
    # end def

    def updateCNModel(self):
        """Summary

        Returns:
            TYPE: Description
        """
        value = self.data(VAL_COL, Qt.DisplayRole)
        key = self._key
        u_s = self.treeWidget().undoStack()
        u_s.beginMacro("Multi Property Edit: %s" % key)
        if self.is_enum:
            value = ENUM_NAMES[key].index(value)
        cn_model_list = self.outlineViewObjList()
        if isinstance(cn_model_list, list):
            # print("list found")
            for cn_model in cn_model_list:
                cn_model.setProperty(key, value)
        else:  # called from line 65: p_i = constructor(cn_model, root, key=key)
            # print("single model found")
            cn_model_list.setProperty(key, value)
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
        if p_i.is_enum:
            new_value = ENUM_NAMES[property_key][new_value]
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
