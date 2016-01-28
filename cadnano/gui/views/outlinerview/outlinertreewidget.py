from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QBrush, QColor, QFont, QPalette, QPen
from PyQt5.QtWidgets import QTreeWidget, QHeaderView
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate
from PyQt5.QtWidgets import QSpinBox, QLineEdit, QPushButton
from PyQt5.QtWidgets import QStyleOptionButton, QStyleOptionViewItem
from PyQt5.QtWidgets import QAbstractItemView, QCheckBox
from PyQt5.QtWidgets import QStyle, QCommonStyle
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QItemSelection

from cadnano.enum import PartType
from cadnano.gui.palette import getColorObj, getPenObj, getBrushObj
from cadnano.gui.views.pathview import pathstyles as styles
from cadnano.gui.controllers.viewrootcontroller import ViewRootController

from .cnoutlineritem import NAME_COL, VISIBLE_COL, COLOR_COL
from .nucleicacidpartitem import NucleicAcidPartItem
from .virtualhelixitem import VirtualHelixItem
from .oligoitem import OligoItem

_FONT = QFont(styles.THE_FONT, 12)
_QCOMMONSTYLE = QCommonStyle()

class OutlinerTreeWidget(QTreeWidget):
    """ The there needs to always be a currentItem which defaults
    to row 0, column 0 at the root
    """
    def __init__(self, parent=None):
        super(OutlinerTreeWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0) # no mac focus halo

    def configure(self, window, document):
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._root = self.invisibleRootItem()
        self._instance_items = {}

        # Appearance
        self.setFont(_FONT)
        # Columns
        self.setColumnCount(3)
        self.setIndentation(14)
        # Header
        self.setHeaderLabels(["Name", "", ""])
        h = self.header()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Fixed)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionsMovable(True)
        self.setColumnWidth(0, 140)
        self.setColumnWidth(1, 18)
        self.setColumnWidth(2, 18)
        # self.setUniformRowHeights(True)

        # Dragging
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.model_selection_changes = (set(), set())
        # self.do_filter = True   # make sure filter is called only when necessary
        self.is_child_adding = 0

        custom_delegate = CustomStyleItemDelegate()
        self.setItemDelegate(custom_delegate)

        self.selectionModel().selectionChanged.connect(self.selectionFilter)
        self.model().dataChanged.connect(self.dataChangedSlot)
        # self.itemSelectionChanged.connect(self.selectedChangedSlot)
        self.itemClicked.connect(self.itemClickedHandler)
    # end def

    def selectionFilter(self, selected_items, deselected_items):
        """ Disables selections of items not in the active filter set.
        I had issues with segfaults subclassing QItemSelectionModel so
        this is the next best thing I think
        """
        # print("!!!!!!!!filter", len(selected_items), len(deselected_items))
        filter_set = self._document.filter_set
        out_deselection = []
        out_selection = []
        flags = QItemSelectionModel.Current | QItemSelectionModel.Deselect
        for index in selected_items.indexes():
            item = self.itemFromIndex(index)
            if item._filter_name not in filter_set:
                if index.column() == 0:
                    # print("deselect", item._filter_name,
                    #                     index.row(), index.column())
                    out_deselection.append(index)
            else:
                out_selection.append(index)
        if len(out_deselection) > 0:
            self.indexFromItem(item)
            sm = self.selectionModel()
            deselection = QItemSelection(out_deselection[0], out_deselection[-1])
            sm.blockSignals(True)
            sm.select(deselection, flags)
            sm.blockSignals(False)

        # now group the indices into items in sets
        tbs, tbd = self.model_selection_changes
        for idx in out_selection:
            item = self.itemFromIndex(idx)
            tbs.add(item)
        for idx in deselected_items.indexes():
            item = self.itemFromIndex(idx)
            tbd.add(item)
    # end def

    def itemClickedHandler(self, tree_widget_item, column):
        # print("I'm click", tree_widget_item.__class__.__name__,
        #    tree_widget_item.isSelected())
        document = self._document
        model_to_be_selected, model_to_be_deselected = self.model_selection_changes
        print("click column", column)
        #1. handle clicks on check marks
        if column == VISIBLE_COL:
            self.blockSignals(True)
            if tree_widget_item.data(column, Qt.DisplayRole):
                print("unchecking", tree_widget_item.__class__.__name__)
                tree_widget_item.setData(column, Qt.EditRole, False)
                # self.closePersistentEditor(tree_widget_item, column)
            else:
                print("checking", tree_widget_item.__class__.__name__)
                tree_widget_item.setData(column, Qt.EditRole, True)
                # self.closePersistentEditor(tree_widget_item, column)
            self.blockSignals(False)
        # else:
        #     self.openPersistentEditor(tree_widget_item, column)


        # 2. handle document selection
        if isinstance(tree_widget_item, NucleicAcidPartItem):
            pass
        elif isinstance(tree_widget_item, VirtualHelixItem):
            for item in model_to_be_selected:
                id_num, part = item.idNum(), item.part()
                is_selected = document.isVirtualHelixSelected(part, id_num)
                # print("select id_num", id_num, is_selected)
                if not is_selected:
                    document.addVirtualHelicesToSelection(part, [id_num])
            model_to_be_selected.clear()
            for item in model_to_be_deselected:
                if isinstance(item, VirtualHelixItem):
                    id_num, part = item.idNum(), item.part()
                    is_selected = document.isVirtualHelixSelected(part, id_num)
                    # print("de id_num", id_num, is_selected)
                    if is_selected:
                        document.removeVirtualHelicesFromSelection(part, [id_num])
            model_to_be_deselected.clear()
        elif isinstance(tree_widget_item, OligoItem):
            pass
        # end def
    # end def

    def dataChangedSlot(self, top_left, bottom_right):
        if self.is_child_adding == 0:
            if top_left == bottom_right:
                item = self.itemFromIndex(top_left)
                if isinstance(item, (VirtualHelixItem, NucleicAcidPartItem, OligoItem)):
                    # print("dataChanged", item.__class__.__name__)
                    item.updateCNModel()
            else:
                selection = QItemSelection(top_left, bottom_right)
                for index in selection.indexes():
                    if index.column() == 0:
                        item = self.itemFromIndex(index)
                        if isinstance(item, (VirtualHelixItem, NucleicAcidPartItem, OligoItem)):
                            item.updateCNModel()
    # end def

    def addDummyRow(self, part_name, visible, color, parent_QTreeWidgetItem=None):
        if parent_QTreeWidgetItem is None:
            parent_QTreeWidgetItem = self.invisibleRootItem()
        tw_item = QTreeWidgetItem(parent_QTreeWidgetItem)
        tw_item.setData(0, Qt.EditRole, part_name)
        tw_item.setData(1, Qt.EditRole, visible)
        tw_item.setData(2, Qt.EditRole, color)
        tw_item.setFlags(tw_item.flags() | Qt.ItemIsEditable)
        return tw_item
    # end def

    def getInstanceCount(self):
        return len(self._instance_items)

    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender, model_part_instance):
        """
        Receives notification from the model that a part has been added.
        Parts should add themselves to the QTreeWidget by passing parent=self.
        """
        model_part = model_part_instance.reference()
        part_type = model_part.partType()
        if part_type == PartType.NUCLEICACIDPART:
            self.is_child_adding += 1
            na_part_item = NucleicAcidPartItem(model_part, parent=self)
            self._instance_items[model_part_instance] = na_part_item
            self.setCurrentItem(na_part_item)
            self.is_child_adding -= 1
        else:
            print(part_type)
            raise NotImplementedError
    # end def

    # def selectedChangedSlot(self):
    #     for mpi in self._instance_items:
    #         if self._instance_items[mpi] in self.selectedItems():
    #             mpi.reference().setSelected(True)
    #         else:
    #             mpi.reference().setSelected(False)
    # # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        pass
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        pass
    # end def

    def resetRootItemSlot(self, doc):
        pass
    # end def

    def clearSelectionsSlot(self, doc):
        self.selectionModel().clearSelection()
    # end def

    ### ACCESSORS ###
    def window(self):
        return self._window
    # end def

    ### METHODS ###
    def removePartItem(self, part_item):
        index = self.indexOfTopLevelItem(part_item)
        self.takeTopLevelItem(index)
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController"""
        self._document = document
        self._controller = ViewRootController(self, document)
        if len(self._instance_items) > 0:
            raise ImportError
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState"""
        for part_item in self._instance_items:
            part_item.setModifyState(bool)
    # end def
# end class OutlinerTreeWidget


class CustomStyleItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent_QWidget, option, model_index):
        column = model_index.column()
        if column == NAME_COL: # Model name
            editor = QLineEdit(parent_QWidget)
            editor.setAlignment(Qt.AlignVCenter)
            return editor
        # elif column == 1: # Visibility checkbox
        #     editor = QCheckBox(parent_QWidget)
        #     # setAlignment doesn't work https://bugreports.qt-project.org/browse/QTBUG-5368
        #     return editor
        elif column == COLOR_COL: # Color Picker
            print("##############dsfsdfdsdfgsdfg")
            editor = QColorDialog(parent_QWidget)
            return editor
        # elif column == 3: # SpinBox Example
        #     editor = QSpinBox(parent_QWidget)
        #     editor.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        #     editor.setMinimum(0)
        #     editor.setMaximum(100)
        #     return editor
        else:
            return QStyledItemDelegate.createEditor(self, \
                            parent_QWidget, option, model_index)
    # end def

    def setEditorData(self, editor, model_index):
        column = model_index.column()
        if column == NAME_COL: # Part Name
            text_QString = model_index.model().data(model_index, Qt.EditRole)
            editor.setText(text_QString)
        # elif column == VISIBLE_COL: # Visibility
        #     value = model_index.model().data(model_index, Qt.EditRole)
        #     editor.setChecked(value)
        elif column == COLOR_COL: # Color
            value = model_index.model().data(model_index, Qt.EditRole)
            # editor.setText(value)
            editor.setCurrentColor(QColor(value))
        # elif column == 3: # SpinBox Example
        #     value = model_index.model().data(model_index, Qt.EditRole)
        #     editor.setValue(value)
        else:
            QStyledItemDelegate.setEditorData(self, editor, model_index)
    # end def

    def setModelData(self, editor, model, model_index):
        column = model_index.column()
        if column == NAME_COL: # Part Name
            text_QString = editor.text()
            model.setData(model_index, text_QString, Qt.EditRole)
        # elif column == VISIBLE_COL: # Visibility
        #     value = editor.isChecked()
        #     model.setData(model_index, value, Qt.EditRole)
        elif column == COLOR_COL: # Color
            # color = editor.text()
            # model.setData(model_index, color, Qt.EditRole)
            color = editor.currentColor()
            model.setData(model_index, color.name(), Qt.EditRole)

        # elif column == 3: # SpinBox Example
        #     value = editor.value()
        #     model.setData(model_index, value, Qt.EditRole)
        else:
            QStyledItemDelegate.setModelData(self, editor, model, model_index)
    # end def

    def updateEditorGeometry(self, editor, option, model_index):
        column = model_index.column()
        if column == NAME_COL:
            editor.setGeometry(option.rect)
        # elif column == VISIBLE_COL:
        #     rect = QRect(option.rect)
        #     delta = option.rect.width() / 2 - 9
        #     rect.setX(option.rect.x() + delta) # Hack to center the checkbox
        #     editor.setGeometry(rect)
        elif column == COLOR_COL:
            pass
            # editor.setGeometry(option.rect)
        else:
            QStyledItemDelegate.updateEditorGeometry(self, editor, option, model_index)
    # end def

    def paint(self, painter, option, model_index):
        column = model_index.column()
        new_rect = QRect(option.rect)
        option.rect = new_rect
        if column == NAME_COL: # Part Name
            option.displayAlignment = Qt.AlignVCenter
            QStyledItemDelegate.paint(self, painter, option, model_index)
        if column == VISIBLE_COL: # Visibility
            element = _QCOMMONSTYLE.PE_IndicatorCheckBox
            styleoption = QStyleOptionButton()
            styleoption.rect = new_rect
            checked = model_index.model().data(model_index, Qt.EditRole)
            styleoption.state |= QStyle.State_On if checked else QStyle.State_Off
            # make the check box look a little more active by changing the pallete
            styleoption.palette.setBrush(QPalette.Button, Qt.white)
            styleoption.palette.setBrush(QPalette.HighlightedText, Qt.black)
            _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
            if checked:
                element = _QCOMMONSTYLE.PE_IndicatorMenuCheckMark
                _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
        elif column == COLOR_COL: # Color
            color = model_index.model().data(model_index, Qt.EditRole)
            element = _QCOMMONSTYLE.PE_IndicatorCheckBox
            styleoption = QStyleOptionViewItem()
            styleoption.palette.setBrush(QPalette.Button, QBrush(getColorObj(color)))
            top_left = option.rect.topLeft()
            styleoption.rect = new_rect
            # print("color rect", option.rect.height())
            _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
        else:
            QStyledItemDelegate.paint(self, painter, option, model_index)
    # end def

    def itemSelectionChanged(self):
        print("pppppp", self.selectedItems())
    # end def
# end class CustomStyleItemDelegate