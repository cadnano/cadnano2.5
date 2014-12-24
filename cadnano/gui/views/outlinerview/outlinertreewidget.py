from cadnano.gui.views.pathview import pathstyles as styles

from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .dnapartitem import DnaPartItem
from .origamipartitem import OrigamiPartItem

from cadnano.enum import PartType
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


class OutlinerTreeWidget(QTreeWidget):
    """
    """
    def __init__(self, parent=None):
        super(OutlinerTreeWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect,0) # no mac focus halo

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

        custom_delegate = CustomDelegate()
        self.setItemDelegate(custom_delegate)
        # self.connect(custom_delegate, QtCore.SIGNAL('requestNewPath'), self.getNewPath)

        # Add some dummy items
        # p1 = self.addDummyRow("Part0", True, "#cc0000")
        # a1 = self.addDummyRow("Asm0",  True, "#00cc00")
        # self.expandItem(a1)
        # p2 = self.addDummyRow("Part1", True, "#0000cc", a1)
        # p3 = self.addDummyRow("Part2", True, "#cc6600", a1)
    # end def

    def addDummyRow(self, part_name, visible, color, parentQTreeWidgetItem = None):
        if parentQTreeWidgetItem == None:
            parentQTreeWidgetItem = self.invisibleRootItem()
        tw_item = QTreeWidgetItem(parentQTreeWidgetItem)
        tw_item.setData(0, Qt.EditRole, part_name)
        tw_item.setData(1, Qt.EditRole, visible)
        tw_item.setData(2, Qt.EditRole, color)
        tw_item.setFlags(tw_item.flags() | Qt.ItemIsEditable)
        return tw_item
    # end def

    def getInstanceCount(self):
        return len(self._instance_items)

    # def getNewPath(self, indexQModelIndex):
    #     tw_item = self.itemFromIndex(indexQModelIndex)
    #     pathQStringList = QFileDialog.getOpenFileNames()
    #     if pathQStringList.count() > 0:
    #         textQString = pathQStringList.first()
    #         tw_item.setData(indexQModelIndex.column(), Qt.EditRole, textQString)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    # def itemClicked(self, item, column):
    #     print("itemClicked", item, column)
    # 
    # def itemDoubleClicked(self, item, column):
    #     print("itemDoubleClicked", item, column)


    def partAddedSlot(self, sender, model_part_instance):
        """
        Receives notification from the model that a part has been added.
        Parts should add themselves to the QTreeWidget by passing parent=self.
        """
        model_part = model_part_instance.object()
        part_type = model_part_instance.object().partType()
        if part_type == PartType.DNAPART:
            dna_part_item = DnaPartItem(model_part, parent=self)
            # self.itemDoubleClicked.connect(dna_part_item.doubleClickedSlot)
            self._instance_items[model_part_instance] = dna_part_item
        elif part_type == PartType.ORIGAMIPART:
            origami_part_item = OrigamiPartItem(model_part, parent=self)
            self._instance_items[model_part_instance] = origami_part_item
            # self.setModifyState(self._window.action_modify.isChecked())
        else:
            print(part_type)
            raise NotImplementedError

    # end def

    def clearSelectionsSlot(self, doc):
        pass
    # end def

    def selectedChangedSlot(self, item_dict):
        """docstring for selectedChangedSlot"""
        print("outliner: selectedChangedSlot")
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
    def removeDnaPartItem(self, dna_part_item):
        index = self.indexOfTopLevelItem(dna_part_item)
        self.takeTopLevelItem(index)
        # del self._instance_items[dna_part_item]
    # end def

    def removeOrigamiPartItem(self, origami_part_item):
        index = self.indexOfTopLevelItem(origami_part_item)
        self.takeTopLevelItem(index)
        # del self._instance_items[origami_part_item]
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
        for origami_part_item in self._instance_items:
            origami_part_item.setModifyState(bool)
    # end def
# end class OutlinerTreeWidget


class CustomDelegate(QStyledItemDelegate):
    # def initStyleOption(self, option, model_index):
        # pass
        # option.palette.setBrush(QPalette.Text, Qt.red) # doesn't work
        # option.backgroundBrush = QBrush(Qt.black)
        # column = model_index.column()
        # if column == 2:
        #     option.backgroundBrush = QBrush(QColor(204,0,0))

    def createEditor(self, parentQWidget, option, model_index):
        # print("createEditor")
        column = model_index.column()
        if column == 0: # Part Name
            editor = QLineEdit(parentQWidget)
            editor.setAlignment(Qt.AlignVCenter)
            return editor
        elif column == 1: # Visibility checkbox
            editor = QCheckBox(parentQWidget)
            # setAlignment doesn't work https://bugreports.qt-project.org/browse/QTBUG-5368
            return editor
        # elif column == 2: # Color Picker
        #     editor = QPushButton(parentQWidget)
        #     return editor
        # elif column == 3: # SpinBox Example
        #     editor = QSpinBox(parentQWidget)
        #     editor.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        #     editor.setMinimum(0)
        #     editor.setMaximum(100)
        #     return editor
        else:
            return QStyledItemDelegate.createEditor(self, \
                            parentQWidget, option, model_index)
    # end def

    def setEditorData(self, editor, model_index):
        column = model_index.column()
        if column == 0: # Part Name
            textQString = model_index.model().data(model_index, Qt.EditRole)
            editor.setText(textQString)
        elif column == 1: # Visibility
            value = model_index.model().data(model_index, Qt.EditRole)
            editor.setChecked(value)
        elif column == 2: # Color
            value = model_index.model().data(model_index, Qt.EditRole)
            editor.setText(value)
        # elif column == 3: # SpinBox Example
        #     value = model_index.model().data(model_index, Qt.EditRole)
        #     editor.setValue(value)
        else:
            QStyledItemDelegate.setEditorData(self, editor, model_index)
    # end def

    def setModelData(self, editor, model, model_index):
        column = model_index.column()
        if column == 0: # Part Name
            textQString = editor.text()
            model.setData(model_index, textQString, Qt.EditRole)
        elif column == 1: # Visibility
            value = editor.isChecked()
            model.setData(model_index, value, Qt.EditRole)
        elif column == 2: # Color
            color = editor.text()
            # textQString = editor.text()
            model.setData(model_index, color, Qt.EditRole)
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
            delta = option.rect.width()/2 - 9
            rect.setX(option.rect.x() + delta) # Hack to center the checkbox
            editor.setGeometry(rect)
        elif column == 2:
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
            # option.displayAlignment = Qt.AlignHCenter | Qt.AlignVCenter
            # element = _QCOMMONSTYLE.CE_CheckBox
            element = _QCOMMONSTYLE.PE_IndicatorCheckBox
            styleoption = QStyleOptionButton()
            styleoption.rect = QRect(option.rect)
            checked = model_index.model().data(model_index, Qt.EditRole)
            styleoption.state |= QStyle.State_On if checked else QStyle.State_Off
            _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
            if checked:
                element =  _QCOMMONSTYLE.PE_IndicatorMenuCheckMark
                _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)

            # _QCOMMONSTYLE.drawControl(element, styleoption, painter)
            # QStyledItemDelegate.paint(self, painter, option, model_index)
        elif column == 2: # Color
            color = model_index.model().data(model_index, Qt.EditRole)
            element = _QCOMMONSTYLE.PE_IndicatorCheckBox
            styleoption = QStyleOptionViewItem()
            styleoption.palette.setBrush(QPalette.Button, QBrush(QColor(color)))
            styleoption.rect = QRect(option.rect)
            _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)

            # option.displayAlignment = Qt.AlignHCenter | Qt.AlignVCenter
            # option.backgroundBrush = QBrush(QColor(204,0,0, 128))
            # QStyledItemDelegate.paint(self, painter, option, model_index)

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
        #     textQString = model_index.model().data(model_index, Qt.EditRole)
        #     buttonQStyleOptionButton = QStyleOptionButton()
        #     buttonQStyleOptionButton.rect = QRect(option.rect)
        #     buttonQStyleOptionButton.text = textQString
        #     buttonQStyleOptionButton.state = QStyle.State_Active
        #     _QCOMMONSTYLE.drawControl(_QCOMMONSTYLE.CE_PushButton, buttonQStyleOptionButton, painter)
        else:
            QStyledItemDelegate.paint(self, painter, option, model_index)
    # end def
# end class CustomDelegate
