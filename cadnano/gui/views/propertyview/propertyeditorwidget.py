"""Summary

Attributes:
    COLOR_PATTERN (TYPE): Description
"""
import re
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtWidgets import QTreeWidget, QHeaderView
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtWidgets import QStyleOptionButton, QStyleOptionViewItem
from PyQt5.QtWidgets import QStyle, QCommonStyle

from cadnano.cnenum import ItemType
from cadnano.gui.palette import getBrushObj
from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from cadnano.gui.views.pathview import pathstyles as styles

from .oligoitem import OligoSetItem
from .nucleicacidpartitem import NucleicAcidPartSetItem
from .virtualhelixitem import VirtualHelixSetItem
from .cnpropertyitem import CNPropertyItem

COLOR_PATTERN = re.compile("#[0-9a-f].....")
_FONT = QFont(styles.THE_FONT, 12)
_QCOMMONSTYLE = QCommonStyle()


class PropertyEditorWidget(QTreeWidget):
    """
    PropertyEditorWidget enables direct editing attributes of an
    item that is selected in the Outliner.
    """
    def __init__(self, parent=None):
        """Summary

        Args:
            parent (None, optional): Description
        """
        super(PropertyEditorWidget, self).__init__(parent)
        self._cn_model_set = set()
        self._cn_model_list = []
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)  # no mac focus halo
    # end def

    def undoStack(self):
        return self._document.undoStack()
    # end def

    def configure(self, window, document):
        """Summary

        Args:
            window (TYPE): Description
            document (TYPE): Description

        Returns:
            TYPE: Description
        """
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
        h.resizeSection(0, 200)
        h.resizeSection(1, 100)
        h.setSectionResizeMode(QHeaderView.Interactive)
        # h.setStretchLastSection(False)

        custom_delegate = CustomStyleItemDelegate(self)
        self.setItemDelegate(custom_delegate)

        self.model().dataChanged.connect(self.dataChangedSlot)

        # Add some dummy items
        # p1 = self.addDummyRow("sequence", "ATCGACTGATCG")
        # p2 = self.addDummyRow("circular",  True)
    # end def

    # def addDummyRow(self, property_name, value, parent_QTreeWidgetItem=None):
    #     if parent_QTreeWidgetItem is None:
    #         parent_QTreeWidgetItem = self.invisibleRootItem()
    #     tw_item = QTreeWidgetItem(parent_QTreeWidgetItem)
    #     tw_item.setData(0, Qt.EditRole, property_name)
    #     tw_item.setData(1, Qt.EditRole, value)
    #     tw_item.setFlags(tw_item.flags() | Qt.ItemIsEditable)
    #     return tw_item
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def outlinerItemSelectionChanged(self):
        """Summary

        Returns:
            TYPE: Description

        Raises:
            NotImplementedError: Description
        """
        o = self._window.outliner_widget
        for child in self.children():
            if isinstance(child, (CNPropertyItem)):
                child.disconnectSignals()

        selected_items = o.selectedItems()

        self.clear()    # remove pre-existing items
        self._cn_model_set.clear()
        self._cn_model_list = []
        # print("prop multiple selected:", len(selected_items))
        # if len(selected_items):
        #     print(selected_items[0])

        # get the selected item
        item_types = set([item.itemType() for item in selected_items])
        num_types = len(item_types)
        if num_types != 1:  # assume no mixed types for now
            return
        item_type = item_types.pop()
        cn_model_list = [item.cnModel() for item in selected_items if item.isSelected()]

        '''Workaround as items in QTreeWidget.selectedItems() may be not
        actually selected
        '''
        if len(cn_model_list) == 0:
            return
        self._cn_model_set = set(cn_model_list)
        self._cn_model_list = cn_model_list

        # special case for parts since there is currently no part filter
        if item_type is ItemType.NUCLEICACID:
            pe_item = NucleicAcidPartSetItem(parent=self)
            self.show()
            return

        item = selected_items[0]
        if item.FILTER_NAME not in self._document.filter_set:
            return
        if item_type is ItemType.OLIGO:
            pe_item = OligoSetItem(parent=self)
            self.show()
        elif item_type is ItemType.VIRTUALHELIX:
            pe_item = VirtualHelixSetItem(parent=self)
            self.show()
        else:
            raise NotImplementedError
    # end def

    def partAddedSlot(self, sender, model_part):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            model_part (Part): The model part

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def clearSelectionsSlot(self, doc):
        """Summary

        Args:
            doc (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def dataChangedSlot(self, top_left, bot_right):
        """docstring for propertyChangedSlot

        Args:
            top_left (TYPE): Description
            bot_right (TYPE): Description
        """
        c_i = self.currentItem()
        if c_i is None:
            return
        if c_i == self.itemFromIndex(top_left):
            c_i.updateCNModel()
    # end def

    def selectedChangedSlot(self, item_dict):
        """Summary

        Args:
            item_dict (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        """Summary

        Args:
            filter_name_list (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        """Summary

        Args:
            filter_name (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def resetRootItemSlot(self, doc):
        """Summary

        Args:
            doc (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.clear()
    # end def

    ### ACCESSORS ###
    def window(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._window
    # end def

    def cnModelSet(self):
        return self._cn_model_set
    # end def

    def cnModelList(self):
        return self._cn_model_list
    # end def

    ### METHODS ###
    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController

        Args:
            document (TYPE): Description
        """
        self._document = document
        self._controller = ViewRootController(self, document)
    # end def

# end class PropertyEditorWidget


class CustomStyleItemDelegate(QStyledItemDelegate):
    """Summary
    """
    def createEditor(self, parent_QWidget, option, model_index):
        """Summary

        Args:
            parent_QWidget (TYPE): Description
            option (TYPE): Description
            model_index (TYPE): Description

        Returns:
            TYPE: Description
        """
        column = model_index.column()
        treewidgetitem = self.parent().itemFromIndex(model_index)
        if column == 0:  # Property Name
            return None
        elif column == 1:
            editor = treewidgetitem.configureEditor(parent_QWidget, option, model_index)
            return editor
        else:
            return QStyledItemDelegate.createEditor(self,
                                                    parent_QWidget,
                                                    option, model_index)
    # end def

    def updateEditorGeometry(self, editor, option, model_index):
        """Summary

        Args:
            editor (TYPE): Description
            option (TYPE): Description
            model_index (TYPE): Description

        Returns:
            TYPE: Description
        """
        column = model_index.column()
        if column == 0:
            editor.setGeometry(option.rect)
        elif column == 1:
            value = model_index.model().data(model_index, Qt.EditRole)
            data_type = type(value)
            if data_type is bool:
                rect = QRect(option.rect)
                delta = option.rect.width() / 2 - 9
                rect.setX(option.rect.x() + delta)  # Hack to center the checkbox
                editor.setGeometry(rect)
            else:
                editor.setGeometry(option.rect)
        else:
            QStyledItemDelegate.updateEditorGeometry(self, editor, option, model_index)
    # end def

    def paint(self, painter, option, model_index):
        """Summary

        Args:
            painter (TYPE): Description
            option (TYPE): Description
            model_index (TYPE): Description

        Returns:
            TYPE: Description
        """
        # row = model_index.row()
        column = model_index.column()
        if column == 0:  # Part Name
            option.displayAlignment = Qt.AlignVCenter
            QStyledItemDelegate.paint(self, painter, option, model_index)
        if column == 1:  # Visibility
            value = model_index.model().data(model_index, Qt.EditRole)
            data_type = type(value)
            if data_type is str:
                # print("val", value)
                if COLOR_PATTERN.search(value):
                    # print("found color")
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
            elif data_type is float:
                option.displayAlignment = Qt.AlignVCenter
                QStyledItemDelegate.paint(self, painter, option, model_index)
            elif data_type is bool:
                element = _QCOMMONSTYLE.PE_IndicatorCheckBox
                styleoption = QStyleOptionButton()
                styleoption.rect = QRect(option.rect)
                checked = value
                styleoption.state |= QStyle.State_On if checked else QStyle.State_Off
                styleoption.palette.setBrush(QPalette.Button, Qt.white)
                styleoption.palette.setBrush(QPalette.HighlightedText, Qt.black)
                _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
                if checked:
                    element = _QCOMMONSTYLE.PE_IndicatorMenuCheckMark
                    _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
        else:
            QStyledItemDelegate.paint(self, painter, option, model_index)
    # end def
# end class CustomStyleItemDelegate
