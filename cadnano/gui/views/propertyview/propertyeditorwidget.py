from cadnano.gui.views.pathview import pathstyles as styles

from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .dnapartitem import DnaPartItem
from .origamipartitem import OrigamiPartItem
import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QFont, QPalette, QPen, QBrush, QDrag
from PyQt5.QtGui import QColor #, QPainterPath
from PyQt5.QtWidgets import QTreeWidget, QHeaderView
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate
from PyQt5.QtWidgets import QSpinBox, QLineEdit, QPushButton
from PyQt5.QtWidgets import QStyleOptionButton, QStyleOptionViewItem
from PyQt5.QtWidgets import QAbstractItemView, QCheckBox
from PyQt5.QtWidgets import QStyle, QCommonStyle

_FONT = QFont(styles.THE_FONT, 12)
_QCOMMONSTYLE = QCommonStyle()


class PropertyEditorWidget(QTreeWidget):
    """
    PropertyEditorWidget enables direct editing attributes of an
    item that is selected in the Outliner.
    """
    def __init__(self, parent=None):
        super(PropertyEditorWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect,0) # no mac focus halo

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

        custom_delegate = CustomDelegate()
        self.setItemDelegate(custom_delegate)


        # self.itemFromIndex(model_index).setPartProperty()
        self.model().dataChanged.connect(self.dataChangedSlot)

        # Add some dummy items
        # p1 = self.addDummyRow("sequence", "ATCGACTGATCG")
        # p2 = self.addDummyRow("circular",  True)
    # end def

    def addDummyRow(self, property_name, value, parentQTreeWidgetItem = None):
        if parentQTreeWidgetItem == None:
            parentQTreeWidgetItem = self.invisibleRootItem()
        tw_item = QTreeWidgetItem(parentQTreeWidgetItem)
        tw_item.setData(0, Qt.EditRole, property_name)
        tw_item.setData(1, Qt.EditRole, value)
        tw_item.setFlags(tw_item.flags() | Qt.ItemIsEditable)
        return tw_item
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def outlinerItemSelectionChanged(self):
        o = self._window.outliner_widget
        sel = o.selectedItems()
        self.clear()
        if len(sel) == 1:
            # get the selected part
            partitem = sel[0]
            part = partitem.part()
            pe_item = DnaPartItem(part, self)
            # self.show()
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
            c_i.updateModel()
    # end def

    def selectedChangedSlot(self, item_dict):
        print("prop_editor: selectedChangedSlot")
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
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

# end class CustomDelegate


class CustomDelegate(QStyledItemDelegate):
    def createEditor(self, parentQWidget, option, model_index):
        column = model_index.column()
        if column == 0: # Property Name
            return None
        elif column == 1: # Visibility checkbox
            data_type = type(model_index.model().data(model_index, Qt.DisplayRole))
            if data_type is str:
                editor = QLineEdit(parentQWidget)
            elif data_type is int:
                editor = QSpinBox(parentQWidget)
            elif data_type is bool:
                editor = QCheckBox(parentQWidget)
            else:
                raise NotImplementedError
            return editor
        else:
            return QStyledItemDelegate.createEditor(self, \
                            parentQWidget, option, model_index)
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
                delta = option.rect.width()/2 - 9
                rect.setX(option.rect.x() + delta) # Hack to center the checkbox
                editor.setGeometry(rect)
            else:
                editor.setGeometry(option.rect)
        else:
            QStyledItemDelegate.updateEditorGeometry(self, editor, option, model_index)
    # end def

    def paint(self, painter, option, model_index):
        column = model_index.column()
        if column == 0: # Part Name
            option.displayAlignment = Qt.AlignVCenter
            QStyledItemDelegate.paint(self, painter, option, model_index)
        if column == 1: # Visibility
            value = model_index.model().data(model_index, Qt.EditRole)
            data_type = type(value)
            if data_type is str:
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
# end class CustomDelegate
