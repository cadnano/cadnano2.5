from PyQt5.QtCore import pyqtSignal, QObject, QDataStream
from PyQt5.QtCore import Qt, QRect, QSize, QVariant
from PyQt5.QtGui import QBrush, QColor, QFont, QPalette, QPen
from PyQt5.QtWidgets import QTreeWidget, QHeaderView, QMenu, QAction, QTreeView
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate
from PyQt5.QtWidgets import QSpinBox, QLineEdit, QPushButton
from PyQt5.QtWidgets import QStyleOptionButton, QStyleOptionViewItem
from PyQt5.QtWidgets import QAbstractItemView, QCheckBox
from PyQt5.QtWidgets import QStyle, QCommonStyle
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QItemSelection, QPersistentModelIndex

from cadnano.enum import PartType
from cadnano.gui.palette import getColorObj, getPenObj, getBrushObj
from cadnano.gui.views.pathview import pathstyles as styles
from cadnano.gui.controllers.viewrootcontroller import ViewRootController

from .cnoutlineritem import NAME_COL, VISIBLE_COL, COLOR_COL
from .nucleicacidpartitem import NucleicAcidPartItem
from .virtualhelixitem import VirtualHelixItem
from .oligoitem import OligoItem
import struct

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

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.getCustomContextMenu)

        # Dragging
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.model_selection_changes = (set(), set())
        self.is_child_adding = 0

        custom_delegate = CustomStyleItemDelegate(self)
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
            if item.FILTER_NAME not in filter_set:
                if index.column() == 0:
                    # print("deselect", item.FILTER_NAME,
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
            # print("did select", item)
            tbs.add(item)
        for idx in deselected_items.indexes():
            item = self.itemFromIndex(idx)
            # print("did deselect", item)
            tbd.add(item)
    # end def

    def itemClickedHandler(self, tree_widget_item, column):
        # print("I'm click", tree_widget_item.__class__.__name__,
        #    tree_widget_item.isSelected())
        document = self._document
        model_to_be_selected, model_to_be_deselected = self.model_selection_changes
        # print("click column", column)
        # 1. handle clicks on check marks to speed things up over using an editor
        if column == VISIBLE_COL:
            self.blockSignals(True)
            if tree_widget_item.data(column, Qt.DisplayRole):
                # print("unchecking", tree_widget_item.__class__.__name__)
                tree_widget_item.setData(column, Qt.EditRole, False)
            else:
                # print("checking", tree_widget_item.__class__.__name__)
                tree_widget_item.setData(column, Qt.EditRole, True)
            self.blockSignals(False)
        # end if


        # 2. handle document selection
        if isinstance(tree_widget_item, NucleicAcidPartItem):
            pass
            # print("&&&&&&&&&&&&&&&&&&&")
            # print(tree_widget_item)
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
            print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
            # for item in model_to_be_selected:
            #     id_num, part = item.idNum(), item.part()
            #     is_selected = document.isVirtualHelixSelected(part, id_num)
            #     # print("select id_num", id_num, is_selected)
            #     if not is_selected:
            #         document.addVirtualHelicesToSelection(part, [id_num])
            model_to_be_selected.clear()
            for item in model_to_be_deselected:
                if isinstance(item, OligoItem):
                    # id_num, part = item.idNum(), item.part()
                    # is_selected = document.isVirtualHelixSelected(part, id_num)
                    # # print("de id_num", id_num, is_selected)
                    # if is_selected:
                    #     document.removeVirtualHelicesFromSelection(part, [id_num])
                    pass
            model_to_be_deselected.clear()
        # end def
    # end def

    def dataChangedSlot(self, top_left, bottom_right):
        if self.is_child_adding == 0:
            if top_left == bottom_right:    # single item
                item = self.itemFromIndex(top_left)
                if isinstance(item, (VirtualHelixItem, NucleicAcidPartItem, OligoItem)):
                    # print("dataChanged", item.__class__.__name__)
                    item.updateCNModel()
            else:
                selection = QItemSelection(top_left, bottom_right)
                for index in selection.indexes():
                    if index.column() == 0:
                        item = self.itemFromIndex(index)
                        # if isinstance(item, VirtualHelixItem):
                        #     print("slap", item.idNum())
                        if isinstance(item, (VirtualHelixItem, NucleicAcidPartItem, OligoItem)):
                            item.updateCNModel()
    # end def

    def getCustomContextMenu(self, point):
        """ point (QPoint)
        """
        menu = QMenu(self)

        hide_act = QAction("Hide selection", self)
        hide_act.setStatusTip("Hide selection")
        hide_act.triggered.connect(self.hideSelection)
        menu.addAction(hide_act)

        show_act = QAction("Show selection", self)
        show_act.setStatusTip("Show selection")
        show_act.triggered.connect(self.showSelection)
        menu.addAction(show_act)

        color_act = QAction("Change colors", self)
        color_act.setStatusTip("Change selection colors")
        color_act.triggered.connect(self.colorSelection)
        menu.addAction(color_act)

        menu.exec_(self.mapToGlobal(point))
    # end def

    def hideSelection(self):
        column = VISIBLE_COL
        for item in self.selectedItems():
            if isinstance(item, (VirtualHelixItem)):
                item.setData(column, Qt.EditRole, False)
                # print("hiding", item.__class__.__name__, item.idNum())
            else:
                print("item unhidable", item.__class__.__name__)
    # end def

    def showSelection(self):
        column = VISIBLE_COL
        for item in self.selectedItems():
            if isinstance(item, (VirtualHelixItem)):
                item.setData(column, Qt.EditRole, True)
                # print("showing", item.__class__.__name__, item.idNum())
            else:
                print("item unshowable", item.__class__.__name__)
    # end def

    def colorSelection(self):
        dialog = QColorDialog(self)
        dialog.colorSelected.connect(self.colorSelectionSlot)
        dialog.open()
    # end def

    def colorSelectionSlot(self, color):
        column = COLOR_COL
        color_name = color.name()
        for item in self.selectedItems():
            if isinstance(item, (VirtualHelixItem)):
                item.setData(column, Qt.EditRole, color_name)
                # print("coloring", item.__class__.__name__, item.idNum())
            else:
                print("item uncolorable", item.__class__.__name__)
    # end def

    def dropEvent(self, event):
        """ custom drop event to prevent reparenting
        """
        # data = event.mimeData()
        # if data.hasFormat('application/x-qabstractitemmodeldatalist'):
        #     bytearray = data.data('application/x-qabstractitemmodeldatalist')
        #     data_item = self.decodeMimeData(bytearray)
        #     print("got a drop event", data_item)

        # item Drop above
        pos = event.pos()
        dest_item = self.itemAt(pos)
        if dest_item is None:
            return
        dest_parent = dest_item.parent()
        selected_items = self.selectedItems()
        for x in selected_items:
            if x.parent() != dest_parent:
                return
        # print("VH:", dest_item.idNum()) # dropped above this item
        # print("selected", [x.idNum() for x in selected_items])
        res = self.myDropEvent(event, dest_item)
        if isinstance(dest_item, VirtualHelixItem):
            part = dest_item.part()
            vhi_list = [dest_parent.child(i) for i in range(dest_parent.childCount())]
            part.setImportedVHelixOrder([vhi.idNum() for vhi in vhi_list], check_batch=False)
        # return QTreeWidget.dropEvent(self, event)
    # end def

    def myDropEvent(self, event, drop_item):
        """ workaround for broken QTreeWidget::dropEvent
        per https://bugreports.qt.io/browse/QTBUG-45320
        doing reverse ordering of items on dropping.  reimplementation in python
        from C++
        """
        if event.source() == self and (event.dropAction() == Qt.MoveAction or
                                        self.dragDropMode() == QAbstractItemView.InternalMove):
            droptuple = self.dropOn(event, drop_item)
            if droptuple is not None:
                (row, col, drop_index) = droptuple
                # print("droptuple", droptuple[2].row())
                idxs = self.selectedIndexes()
                indexes = []
                for idx in idxs:
                    if idx.column() == 0:
                        indexes.append(idx)
                if drop_index in indexes:
                    return
                # When removing items the drop location could shift
                new_drop_index = QPersistentModelIndex(self.model().index(row, col, drop_index))
                # print("updatated drop_row", new_drop_index.row())
                # Remove the items
                taken = []
                for i in range(len(indexes) - 1, -1, -1):
                    # print("idx", indexes[i].row(), indexes[i].column())
                    parent = self.itemFromIndex(indexes[i]);
                    if parent is None or parent.parent() is None:
                        t_item = self.takeTopLevelItem(indexes[i].row())
                        taken.append(t_item)
                    else:
                        t_item = parent.parent().takeChild(indexes[i].row())
                        taken.append(t_item)
                # end for
                # insert them back in at their new positions
                for i in range(len(indexes)):
                    # Either at a specific point or appended
                    if row == -1:
                        if drop_index.isValid():
                            parent = self.itemFromIndex(drop_index)
                            parent.insertChild(parent.childCount(), taken.pop())
                        else:
                            self.insertTopLevelItem(self.topLevelItemCount(), taken.pop())
                    else:
                        r = new_drop_index.row() if new_drop_index.row() >= 0 else row
                        if drop_index.isValid():
                            parent = self.itemFromIndex(drop_index)
                            parent.insertChild(min(r, parent.childCount()), taken.pop())
                        else:
                            self.insertTopLevelItem(min(r, self.topLevelItemCount()), taken.pop())
                # end for

                event.accept()
                # Don't want QAbstractItemView to delete it because it was "moved" we already did it
                event.setDropAction(Qt.CopyAction)
        QTreeView.dropEvent(self, event)
    # end def

    def dropOn(self, event, drop_item):
        """ reimplementation of QAbstractItemViewPrivate::dropOn
        """
        if event.isAccepted():
            return False

        index = self.indexFromItem(drop_item)
        root = self.rootIndex()
        # If we are allowed to do the drop
        if self.model().supportedDropActions() and event.dropAction():
            row = -1
            col = -1
            if index != root:
                dip = self.dropPosition(event.pos(),
                            QTreeView.visualRect(self, index), index)
                if dip is QAbstractItemView.AboveItem:
                    row = index.row()
                    col = index.column()
                    index = index.parent()
                elif dip is QAbstractItemView.BelowItem:
                    row = index.row() + 1
                    col = index.column()
                    index = index.parent()
            else:
                dip = QAbstractItemView.OnViewport

            drop_index = index
            drop_row = row
            drop_col = col
            self.drop_indicator_position = dip
            if not self.isDroppingOnItself(event, index, root):
                return (drop_row, drop_col, drop_index)
        return None
    # end def

    def dropPosition(self, pos, rect, index):
        """ reimplementation of QAbstractItemViewPrivate::position
        """
        r = QAbstractItemView.OnViewport
        margin = 2
        if pos.y() - rect.top() < margin:
            r = QAbstractItemView.AboveItem
        elif rect.bottom() - pos.y() < margin:
            r = QAbstractItemView.BelowItem
        elif rect.contains(pos, True):
            r = QAbstractItemView.OnItem

        if r == QAbstractItemView.OnItem and (not (self.model().flags(index) & Qt.ItemIsDropEnabled)):
            r = QAbstractItemView.AboveItem if pos.y() < rect.center().y() else QAbstractItemView.BelowItem
        return r
    # end def

    def isDroppingOnItself(self, event, index, root_index):
        """ reimplementation of QAbstractItemViewPrivate::droppingOnItself
        """
        drop_action = event.dropAction()
        if self.dragDropMode() == QAbstractItemView.InternalMove:
            drop_action = Qt.MoveAction
        if (event.source() == self
            and event.possibleActions() & Qt.MoveAction
            and drop_action == Qt.MoveAction):
            selected_indexes = self.selectedIndexes()
            child = index
            while child.isValid() and child != root_index:
                if child in selected_indexes:
                    return True
                child = child.parent()
        # end if
        return False
    # end def

    def decodeMimeData(self, bytearray):
        """
        see:
        https://wiki.python.org/moin/PyQt/Handling%20Qt's%20internal%20item%20MIME%20type
        http://doc.qt.io/qt-5.5/datastreamformat.html
        """
        data = {}
        data_list = []
        ds = QDataStream(bytearray)
        while not ds.atEnd():
            item = []
            row = ds.readInt32()
            column = ds.readInt32()
            number_of_items = ds.readInt32()
            print("rc:", row, column, number_of_items)
            for i in range(number_of_items):
                key = ds.readInt32()
                value = QVariant()
                ds >> value
                item.append((value.value(), Qt.ItemDataRole(key)))
            data[(row, column)] = item
            # data_list.append(((row, column), item))
        return data
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
            print("part type", part_type)
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
        self.clear()
    # end def

    def clearSelectionsSlot(self, doc):
        # print("clearSelection")
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
            item = self.parent().itemFromIndex(model_index)
            if item.CAN_NAME_EDIT:
                editor = QLineEdit(parent_QWidget)
                editor.setAlignment(Qt.AlignVCenter)
                return editor
        elif column == 1: # Visibility checkbox
            # editor = QCheckBox(parent_QWidget)
            # setAlignment doesn't work https://bugreports.qt-project.org/browse/QTBUG-5368
            # return editor
            return None
        elif column == COLOR_COL: # Color Picker
            editor = QColorDialog(parent_QWidget)
            return editor
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
            editor.setCurrentColor(QColor(value))
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
            color = editor.currentColor()
            model.setData(model_index, color.name(), Qt.EditRole)
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
        # elif column == COLOR_COL:
        #     editor.setGeometry(option.rect)
        else:
            QStyledItemDelegate.updateEditorGeometry(self, editor, option, model_index)
    # end def

    def paint(self, painter, option, model_index):
        column = model_index.column()
        new_rect = QRect(option.rect)
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