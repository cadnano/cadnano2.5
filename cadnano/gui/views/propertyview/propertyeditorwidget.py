
import re

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtWidgets import QTreeWidget, QHeaderView
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate
from PyQt5.QtWidgets import QSpinBox, QLineEdit
from PyQt5.QtWidgets import QStyleOptionButton, QStyleOptionViewItem
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QStyle, QCommonStyle

from cadnano import util
from cadnano.enum import ItemType
from cadnano.gui.palette import getColorObj, getPenObj, getBrushObj
from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from cadnano.gui.views.pathview import pathstyles as styles
from .plasmidpartitem import PlasmidPartItem
from .oligoitem import OligoItem
from .nucleicacidpartitem import NucleicAcidPartItem
from .virtualhelixitem import VirtualHelixItem

COLOR_PATTERN = re.compile("#[0-9a-f].....")
_FONT = QFont(styles.THE_FONT, 12)
_QCOMMONSTYLE = QCommonStyle()


class PropertyEditorWidget(QTreeWidget):
    """
    PropertyEditorWidget enables direct editing attributes of an
    item that is selected in the Outliner.
    """
    def __init__(self, parent=None):
        super(PropertyEditorWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0) # no mac focus halo

    def configure(self, window, document):
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._root = self.invisibleRootItem()

        # Appearance
        self.setFont(_FONT)
        # Columns
        self.setColumnCount(2)
        self.setIndentation(14)
        # Header
        self.setHeaderLabels(["Property", "Value"])
        h = self.header()
        h.setSectionResizeMode(QHeaderView.Stretch)
        h.setSectionsMovable(True)

        custom_delegate = CustomStyleItemDelegate(self)
        self.setItemDelegate(custom_delegate)

        self.model().dataChanged.connect(self.dataChangedSlot)

        # Add some dummy items
        # p1 = self.addDummyRow("sequence", "ATCGACTGATCG")
        # p2 = self.addDummyRow("circular",  True)
    # end def

    def addDummyRow(self, property_name, value, parent_QTreeWidgetItem=None):
        if parent_QTreeWidgetItem is None:
            parent_QTreeWidgetItem = self.invisibleRootItem()
        tw_item = QTreeWidgetItem(parent_QTreeWidgetItem)
        tw_item.setData(0, Qt.EditRole, property_name)
        tw_item.setData(1, Qt.EditRole, value)
        tw_item.setFlags(tw_item.flags() | Qt.ItemIsEditable)
        return tw_item
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def outlinerItemSelectionChanged(self):
        o = self._window.outliner_widget
        selected_items = o.selectedItems()
        self.clear()    # remove pre-existing items
        if len(selected_items) == 1:
            # get the selected item
            item = selected_items[0]
            item_type = item.itemType()
            if item_type is ItemType.PLASMID:
                pe_item = PlasmidPartItem(item.part(), self)
                self.show()
            elif item_type is ItemType.OLIGO:
                pe_item = OligoItem(item.modelOligo(), self)
                pass
            elif item_type is ItemType.VIRTUALHELIX:
                pe_item = VirtualHelixItem(item.modelVirtualHelix(), self)
            elif item_type is ItemType.NUCLEICACID:
                # print("nucleicacid selected")
                pe_item = NucleicAcidPartItem(item.part(), self)
                self.show()
            else:
                raise NotImplementedError
        else:
            pass
            # self.hide() # show nothing
    # end def

    # def itemClicked(self, item, column):
    #     print("itemClicked", item, column)
    #
    # def itemDoubleClicked(self, item, column):
    #     print("itemDoubleClicked", item, column)

    def partAddedSlot(self, sender, model_part):
        pass
    # end def

    def clearSelectionsSlot(self, doc):
        pass
    # end def

    def dataChangedSlot(self, top_left, bot_right):
        """docstring for propertyChangedSlot"""
        c_i = self.currentItem()
        if c_i is None:
            return
        if c_i == self.itemFromIndex(top_left):
            print (c_i)
            c_i.updateModel()
    # end def

    def selectedChangedSlot(self, item_dict):
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        pass
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        pass
    # end def

    def resetRootItemSlot(self, doc):
        pass
    # end def

    ### ACCESSORS ###
    def window(self):
        return self._window
    # end def

    ### METHODS ###
    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController"""
        self._document = document
        self._controller = ViewRootController(self, document)
    # end def

# end class PropertyEditorWidget


class CustomStyleItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent_QWidget, option, model_index):
        column = model_index.column()
        if column == 0: # Property Name
            return None
        elif column == 1: # Visibility checkbox
            data_type = type(model_index.model().data(model_index, Qt.DisplayRole))
            if data_type is str:
                editor = QLineEdit(parent_QWidget)
            elif data_type is int:
                editor = QSpinBox(parent_QWidget)
            elif data_type is bool:
                editor = QCheckBox(parent_QWidget)
            elif data_type is type(None):
                return None
            else:
                raise NotImplementedError
            return editor
        else:
            return QStyledItemDelegate.createEditor(self, \
                            parent_QWidget, option, model_index)
    # end def

    def setEditorData(self, editor, model_index):
        column = model_index.column()
        if column == 0: # Property
            # textQString = model_index.model().data(model_index, Qt.EditRole)
            # editor.setText(textQString)
            return
        elif column == 1: # Value
            value = model_index.model().data(model_index, Qt.EditRole)
            data_type = type(value)
            if data_type is str:
                editor.setText(value)
            elif data_type is int:
                editor.setValue(value)
            elif data_type is bool:
                editor.setChecked(value)
            else:
                raise NotImplementedError
        else:
            QStyledItemDelegate.setEditorData(self, editor, model_index)
    # end def

    def setModelData(self, editor, model, model_index):
        column = model_index.column()
        if column == 0: # Property
            # textQString = editor.text()
            # model.setData(model_index, textQString, Qt.EditRole)
            return
        elif column == 1: # Value
            data_type = type(model_index.model().data(model_index, Qt.DisplayRole))
            if data_type is str:
                new_value = editor.text()
            elif data_type is int:
                new_value = editor.value()
            elif data_type is bool:
                new_value = editor.isChecked()
            elif data_type is type(None):
                return
            else:
                raise NotImplementedError
            model.setData(model_index, new_value, Qt.EditRole)
        else:
            QStyledItemDelegate.setModelData(self, editor, model, model_index)
    # end def

    def updateEditorGeometry(self, editor, option, model_index):
        column = model_index.column()
        if column == 0:
            editor.setGeometry(option.rect)
        elif column == 1:
            value = model_index.model().data(model_index, Qt.EditRole)
            data_type = type(value)
            if data_type is bool:
                rect = QRect(option.rect)
                delta = option.rect.width() / 2 - 9
                rect.setX(option.rect.x() + delta) # Hack to center the checkbox
                editor.setGeometry(rect)
            else:
                editor.setGeometry(option.rect)
        else:
            QStyledItemDelegate.updateEditorGeometry(self, editor, option, model_index)
    # end def

    def paint(self, painter, option, model_index):
        row = model_index.row()
        column = model_index.column()
        if column == 0: # Part Name
            option.displayAlignment = Qt.AlignVCenter
            QStyledItemDelegate.paint(self, painter, option, model_index)
        if column == 1: # Visibility
            value = model_index.model().data(model_index, Qt.EditRole)
            data_type = type(value)
            if data_type is str:
                if COLOR_PATTERN.search(value):
                    element = _QCOMMONSTYLE.PE_IndicatorCheckBox
                    styleoption = QStyleOptionViewItem()
                    styleoption.palette.setBrush(QPalette.Button, getBrushObj(value))
                    styleoption.rect = QRect(option.rect)
                    _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
                option.displayAlignment = Qt.AlignVCenter
                QStyledItemDelegate.paint(self, painter, option, model_index)
            elif data_type is int:
                option.displayAlignment = Qt.AlignVCenter
                QStyledItemDelegate.paint(self, painter, option, model_index)
            elif data_type is bool:
                element = _QCOMMONSTYLE.PE_IndicatorCheckBox
                styleoption = QStyleOptionButton()
                styleoption.rect = QRect(option.rect)
                checked = value
                styleoption.state |= QStyle.State_On if checked else QStyle.State_Off
                _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
                if checked:
                    element =  _QCOMMONSTYLE.PE_IndicatorMenuCheckMark
                    _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
                # option.displayAlignment = Qt.AlignVCenter
                # QStyledItemDelegate.paint(self, painter, option, model_index)
        else:
            QStyledItemDelegate.paint(self, painter, option, model_index)
    # end def
# end class CustomStyleItemDelegate
