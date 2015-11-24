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

from cadnano.enum import PartType
from cadnano.gui.palette import getColorObj, getPenObj, getBrushObj
from cadnano.gui.views.pathview import pathstyles as styles
from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .nucleicacidpartitem import NucleicAcidPartItem
from .plasmidpartitem import PlasmidPartItem

_FONT = QFont(styles.THE_FONT, 12)
_QCOMMONSTYLE = QCommonStyle()


class OutlinerTreeWidget(QTreeWidget):
    """
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
        # Dragging
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        custom_delegate = CustomStyleItemDelegate()
        self.setItemDelegate(custom_delegate)

        self.model().dataChanged.connect(self.dataChangedSlot)
        self.itemSelectionChanged.connect(self.selectedChangedSlot)
        # Add some dummy items
        # p1 = self.addDummyRow("Part0", True, "#cc0000")
        # a1 = self.addDummyRow("Asm0",  True, "#00cc00")
        # self.expandItem(a1)
        # p2 = self.addDummyRow("Part1", True, "#0000cc", a1)
        # p3 = self.addDummyRow("Part2", True, "#cc6600", a1)
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
        if part_type == PartType.PLASMIDPART:
            plasmid_part_item = PlasmidPartItem(model_part, parent=self)
            self._instance_items[model_part_instance] = plasmid_part_item
        elif part_type == PartType.NUCLEICACIDPART:
            na_part_item = NucleicAcidPartItem(model_part, parent=self)
            self._instance_items[model_part_instance] = na_part_item
        else:
            print(part_type)
            raise NotImplementedError
    # end def

    def clearSelectionsSlot(self, doc):
        pass
    # end def

    def selectedChangedSlot(self):
        for mpi in self._instance_items:
            if self._instance_items[mpi] in self.selectedItems():
                mpi.reference().setSelected(True)
            else:
                mpi.reference().setSelected(False)
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

    def dataChangedSlot(self, top_left, bot_right):
        c_i = self.currentItem()
        if c_i is None:
            return
        if c_i == self.itemFromIndex(top_left):
            c_i.updateCNModel()
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
        if column == 0: # Model name
            editor = QLineEdit(parent_QWidget)
            editor.setAlignment(Qt.AlignVCenter)
            return editor
        elif column == 1: # Visibility checkbox
            editor = QCheckBox(parent_QWidget)
            # setAlignment doesn't work https://bugreports.qt-project.org/browse/QTBUG-5368
            return editor
        elif column == 2: # Color Picker
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
        if column == 0: # Part Name
            text_QString = model_index.model().data(model_index, Qt.EditRole)
            editor.setText(text_QString)
        elif column == 1: # Visibility
            value = model_index.model().data(model_index, Qt.EditRole)
            editor.setChecked(value)
        elif column == 2: # Color
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
        if column == 0: # Part Name
            text_QString = editor.text()
            model.setData(model_index, text_QString, Qt.EditRole)
        elif column == 1: # Visibility
            value = editor.isChecked()
            model.setData(model_index, value, Qt.EditRole)
        elif column == 2: # Color
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
        if column == 0:
            editor.setGeometry(option.rect)
        elif column == 1:
            rect = QRect(option.rect)
            delta = option.rect.width() / 2 - 9
            rect.setX(option.rect.x() + delta) # Hack to center the checkbox
            editor.setGeometry(rect)
        elif column == 2:
            pass
            # editor.setGeometry(option.rect)
        else:
            QStyledItemDelegate.updateEditorGeometry(self, editor, option, model_index)
    # end def

    def paint(self, painter, option, model_index):
        column = model_index.column()
        if column == 0: # Part Name
            option.displayAlignment = Qt.AlignVCenter
            QStyledItemDelegate.paint(self, painter, option, model_index)
        if column == 1: # Visibility
            element = _QCOMMONSTYLE.PE_IndicatorCheckBox
            styleoption = QStyleOptionButton()
            styleoption.rect = QRect(option.rect)
            checked = model_index.model().data(model_index, Qt.EditRole)
            styleoption.state |= QStyle.State_On if checked else QStyle.State_Off
            _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
            if checked:
                element =  _QCOMMONSTYLE.PE_IndicatorMenuCheckMark
                _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)

        elif column == 2: # Color
            color = model_index.model().data(model_index, Qt.EditRole)
            element = _QCOMMONSTYLE.PE_IndicatorCheckBox
            styleoption = QStyleOptionViewItem()
            styleoption.palette.setBrush(QPalette.Button, QBrush(getColorObj(color)))
            styleoption.rect = QRect(option.rect)
            _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)

        # elif column == 3: # SpinBox Example
        #     value = model_index.model().data(model_index, Qt.EditRole)
        #     option.displayAlignment = Qt.AlignHCenter | Qt.AlignVCenter
        #     currentQRect = QRect(option.rect)
        #     # currentQRect.setWidth(currentQRect.width() - 22)
        #     currentQRect.setWidth(20)
        #     # self.drawDisplay(painter, option, currentQRect, value)
        #     spinBoxQStyleOptionSpinBox = QStyleOptionSpinBox()
        #     spinBoxQStyleOptionSpinBox.rect = QRect(option.rect)
        #     _QCOMMONSTYLE.drawComplexControl(_QCOMMONSTYLE.CC_SpinBox, \
        #                                             spinBoxQStyleOptionSpinBox, \
        #                                             painter)
        # elif column == 4: # PushButton example
        #     text_QString = model_index.model().data(model_index, Qt.EditRole)
        #     buttonQStyleOptionButton = QStyleOptionButton()
        #     buttonQStyleOptionButton.rect = QRect(option.rect)
        #     buttonQStyleOptionButton.text = text_QString
        #     buttonQStyleOptionButton.state = QStyle.State_Active
        #     _QCOMMONSTYLE.drawControl(_QCOMMONSTYLE.CE_PushButton, buttonQStyleOptionButton, painter)
        else:
            QStyledItemDelegate.paint(self, painter, option, model_index)
    # end def
# end class CustomStyleItemDelegate


class OutlineRootItem(QTreeWidget):
    """
    OutlineRootItem is the root item in the OutlineView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and selectedPartChangedSignal) via its ViewRootController.

    OutlineRootItem must instantiate its own controller to receive signals
    from the model.
    """
    def __init__(self, parent, window, document):
        super(OutlineRootItem, self).__init__(parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._root = self.invisibleRootItem()
        self._instance_items = {}

        self._configure() # setup header and drag mode

        custom_delegate = CustomStyleItemDelegate()
        self.setItemDelegate(custom_delegate)

        # Add some dummy items
        p1 = self.addDummyRow("Part0", True, "#cc0000")
        a1 = self.addDummyRow("Asm0",  True, "#00cc00")
        self.expandItem(a1)
        p2 = self.addDummyRow("Part1", True, "#0000cc", a1)
        p3 = self.addDummyRow("Part2", True, "#cc6600", a1)

    def _configure(self):
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
        # Dragging
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
    # end def

    def addDummyRow(self, part_name, visible, color, parent_QTreeWidgetItem=None):
        if parent_QTreeWidgetItem == None:
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
    def partAddedSlot(self, sender, model_part):
        """
        Receives notification from the model that a part has been added.
        Parts should add themselves to the QTreeWidget by passing parent=self.
        """
        part_type = model_part.__class__.__name__
        if part_type == "PlasmidPart":
            plasmid_part_item = PlasmidPartItem(model_part, parent=self)
        elif part_type in ["HoneycombPart", "SquarePart"]:
            nucleicacid_part_item = OrigamiPartItem(model_part, parent=self)
            self.addTopLevelItem(nucleicacid_part_item)
        else:
            print(part_type)
            raise NotImplementedError

    # end def

    def clearSelectionsSlot(self, doc):
        pass
    # end def

    # def selectionFilterChangedSlot(self, filter_name_list):
    #     pass
    # # end def

    # def preXoverFilterChangedSlot(self, filter_name):
    #     pass
    # # end def

    # def resetRootItemSlot(self, doc):
    #     pass
    # # end def

    ### ACCESSORS ###
    # def OutlineToolManager(self):
    #     """docstring for OutlineToolManager"""
    #     return self._window.OutlineToolManager
    # # end def

    def window(self):
        return self._window
    # end def

    ### METHODS ###
    def removePartItem(self, part_item):
        index = self.indexOfTopLevelItem(part_item)
        self.takeTopLevelItem(index)
        # del self._instance_items[plasmid_part_item]
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController"""
        self._document = document
        self._controller = ViewRootController(self, document)
        if len(self._instance_items) > 0:
            raise ImportError("resetDocumentAndController no _instance_items")
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState"""
        for nucleicacid_part_item in self._instance_items:
            nucleicacid_part_item.setModifyState(bool)
    # end def
