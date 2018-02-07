# This file may be used under the terms of the GNU General Public License
# version 3.0 as published by the Free Software Foundation and appearing in
# the file LICENSE included in the packaging of this file.  Please review the
# following information to ensure the GNU General Public License version 3.0
# requirements will be met: http://www.gnu.org/copyleft/gpl.html.
#
# This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
# WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

from PyQt5.QtCore import QDataStream
from PyQt5.QtCore import Qt, QRect, QVariant
from PyQt5.QtCore import QItemSelectionModel, QItemSelection
from PyQt5.QtCore import QPersistentModelIndex
from PyQt5.QtGui import QColor, QFont, QPalette, QPixmap
from PyQt5.QtWidgets import QAbstractItemView, QAction
from PyQt5.QtWidgets import QColorDialog, QHeaderView
from PyQt5.QtWidgets import QLineEdit, QMenu
from PyQt5.QtWidgets import QTreeWidget, QTreeView, QTreeWidgetItemIterator
from PyQt5.QtWidgets import QStyle, QCommonStyle
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtWidgets import QStyleOptionButton, QStyleOptionViewItem
from PyQt5.QtWidgets import QToolTip

from cadnano.proxies.cnenum import PartType
from cadnano.gui.palette import getBrushObj
from cadnano.views.pathview import pathstyles as styles
from cadnano.controllers.viewrootcontroller import ViewRootController
from cadnano import util

from .cnoutlineritem import NAME_COL, LOCKED_COL, VISIBLE_COL, COLOR_COL
from .cnoutlineritem import LEAF_FLAGS, DISABLE_FLAGS, ROOT_FLAGS
from .nucleicacidpartitem import OutlineNucleicAcidPartItem
from .virtualhelixitem import OutlineVirtualHelixItem
from .oligoitem import OutlineOligoItem

_FONT = QFont(styles.THE_FONT, 12)
_QCOMMONSTYLE = QCommonStyle()

_LOCK_ICON = QPixmap(":/outlinericons/lock")
_EYE_ICON = QPixmap(":/outlinericons/eye")


class OutlinerTreeWidget(QTreeWidget):
    """ The there needs to always be a currentItem which defaults
    to row 0, column 0 at the root
    """

    def __init__(self, parent=None):
        super(OutlinerTreeWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)  # no mac focus halo
        self.to_be_activated = None

    def configure(self, window, document):
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._root = self.invisibleRootItem()   # access to top level item
        self._instance_items = {}

        # Appearance
        self.setFont(_FONT)
        # Columns
        self.setColumnCount(3)
        self.setIndentation(14)
        # Header
        self.setHeaderLabels(["Name", "", "", ""])
        h = self.header()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Fixed)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        h.setSectionsMovable(True)
        self.setColumnWidth(0, 120)
        self.setColumnWidth(1, 18)
        self.setColumnWidth(2, 18)
        self.setColumnWidth(3, 18)

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

        '''Temporarily disable the selectionFilter with this so you dont
        get double events
        '''
        self.selection_filter_disabled = False

        self.model().dataChanged.connect(self.dataChangedSlot)

        self.itemClicked.connect(self.itemClickedHandler)
    # end def

    def document(self):
        return self._document
    # end def

    def selectionFilter(self, selected_items, deselected_items):
        """ Disables selections of items not in the active filter set.
        I had issues with segfaults subclassing QItemSelectionModel so
        this is the next best thing I think
        """

        # NOTE: prevent selection when select is not pressed
        is_not_select_tool = not self._window.action_global_select.isChecked()

        document = self._document
        # print("!!!!!!!!filter", len(selected_items), len(deselected_items))
        if self.selection_filter_disabled:
            return
        filter_set = document.filter_set
        filter_set.add('part')
        out_deselection = []
        out_selection = []
        flags = QItemSelectionModel.Current | QItemSelectionModel.Deselect
        for index in selected_items.indexes():
            item = self.itemFromIndex(index)
            if is_not_select_tool or item.FILTER_NAME not in filter_set:
                if index.column() == 0:
                    # print("deselect", item.FILTER_NAME, filter_set,
                    #                     index.row(), index.column())
                    out_deselection.append(index)
            else:
                out_selection.append(index)
        sm = self.selectionModel()
        if len(out_deselection) > 0:
            self.indexFromItem(item)
            deselection = QItemSelection(out_deselection[0], out_deselection[-1])
            sm.blockSignals(True)
            sm.select(deselection, flags)
            sm.blockSignals(False)

        # now group the indices into items in sets
        tbs, tbd = self.model_selection_changes
        # print("sets:", tbs, tbd)
        for idx in out_selection:
            item = self.itemFromIndex(idx)
            # print("did select", item)
            tbs.add(item)
        for idx in deselected_items.indexes():
            # print("could deselect?", self.itemFromIndex(idx))
            item = self.itemFromIndex(idx)
            if item not in tbd and item.isModelSelected(document):
                tbd.add(item)
        self.processSelections(deselect_only=True)
    # end def

    def itemClickedHandler(self, tree_widget_item, column):
        # print("I'm click", tree_widget_item.__class__.__name__,
        #       tree_widget_item.isSelected())
        # print("click column", column)

        # 1. handle clicks on check marks to speed things up over using an editor
        if column == LOCKED_COL or column == VISIBLE_COL:
            self.blockSignals(True)
            if tree_widget_item.data(column, Qt.DisplayRole):
                # print("unchecking", tree_widget_item.__class__.__name__)
                tree_widget_item.setData(column, Qt.EditRole, False)
            else:
                # print("checking", tree_widget_item.__class__.__name__)
                tree_widget_item.setData(column, Qt.EditRole, True)
            self.blockSignals(False)
        # end if

        filter_set = self._document.filter_set
        if hasattr(tree_widget_item, "FILTER_NAME") and\
           tree_widget_item.FILTER_NAME not in filter_set:
            rect = self.visualItemRect(tree_widget_item)
            QToolTip.showText(self.mapToGlobal(rect.center()), "Change filter to select")
            return
        self.processSelections()
    # end def

    def processSelections(self, deselect_only=False):
        """ Process selections.  We need this because itemClicked doesn't get called
        when clicking off of a QTreeWidgetItem in the QTreeWidget and triggers
        a deselection
        we may be able to call this in a mousePressEvent instead of in
        selectionFilter at all.  That is a TODO or a TBD, to figure out signaling
        order

        Args:
            deselect_only (bool, optional): default is False.  Allows a
                deselection to occur when clicking off an item in the outlineview
                since no itemClicked will occur
        """
        document = self._document
        model_to_be_selected, model_to_be_deselected = self.model_selection_changes
        # 2. handle document selection
        # self.blockSignals(True)
        if deselect_only:
            for item in model_to_be_selected:
                if isinstance(item, OutlineNucleicAcidPartItem):
                    pass
                elif isinstance(item, OutlineVirtualHelixItem):
                        id_num, part = item.idNum(), item.part()
                        is_selected = document.isVirtualHelixSelected(part, id_num)
                        # print("select id_num", id_num, is_selected)
                        if not is_selected:
                            # print("selecting vh", id_num)
                            document.addVirtualHelicesToSelection(part, [id_num])
                if isinstance(item, OutlineOligoItem):
                    m_oligo = item.cnModel()
                    is_selected = document.isOligoSelected(m_oligo)
                    if not is_selected:
                        # print("selecting", m_oligo)
                        document.selectOligo(m_oligo)
            model_to_be_selected.clear()
        for item in model_to_be_deselected:
            if isinstance(item, OutlineNucleicAcidPartItem):
                pass
            elif isinstance(item, OutlineVirtualHelixItem):
                id_num, part = item.idNum(), item.part()
                is_selected = document.isVirtualHelixSelected(part, id_num)
                # print("de id_num", id_num, is_selected)
                if is_selected:
                    # print("deselecting vh", id_num)
                    document.removeVirtualHelicesFromSelection(part, [id_num])
            elif isinstance(item, OutlineOligoItem):
                m_oligo = item.cnModel()
                is_selected = document.isOligoSelected(m_oligo)
                if is_selected:
                    # print("deselecting", m_oligo)
                    document.deselectOligo(m_oligo)
        model_to_be_deselected.clear()
        # end if
        # self.blockSignals(False)
    # end def

    def dataChangedSlot(self, top_left, bottom_right):
        if self.is_child_adding == 0:
            if top_left == bottom_right:    # single item
                item = self.itemFromIndex(top_left)
                if isinstance(item, (OutlineVirtualHelixItem, OutlineNucleicAcidPartItem, OutlineOligoItem)):
                    # print("dataChanged", item.__class__.__name__)
                    item.updateCNModel()
            else:
                selection = QItemSelection(top_left, bottom_right)
                for index in selection.indexes():
                    if index.column() == 0:
                        item = self.itemFromIndex(index)
                        # if isinstance(item, OutlineVirtualHelixItem):
                        #     print("slap", item.idNum())
                        if isinstance(item, (OutlineVirtualHelixItem, OutlineNucleicAcidPartItem, OutlineOligoItem)):
                            item.updateCNModel()
    # end def

    def setActiveItem(self):
        tba = self.to_be_activated
        if isinstance(tba, OutlineNucleicAcidPartItem):
            print("trying to activate", tba)
            tba.setActive()
        else:
            tba.setActive(True, 0)
        self.to_be_activated = None
    # end def

    def getCustomContextMenu(self, point):
        """ point (QPoint)
        """
        menu = QMenu(self)

        item = self.itemAt(point)
        if isinstance(item, (OutlineNucleicAcidPartItem, OutlineVirtualHelixItem)):
            if isinstance(item, OutlineNucleicAcidPartItem):
                message = "set active Part"
            else:
                message = "set active Virtual Helix"
            self.to_be_activated = item
            setactive_act = QAction(message, self)
            setactive_act.setStatusTip("set active")
            setactive_act.triggered.connect(self.setActiveItem)
            menu.addAction(setactive_act)

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

        delete_act = QAction("Delete items", self)
        delete_act.setStatusTip("Delete selection")
        delete_act.triggered.connect(self.deleteSelection)
        menu.addAction(delete_act)

        menu.exec_(self.mapToGlobal(point))
    # end def

    def hideSelection(self):
        column = VISIBLE_COL
        for item in self.selectedItems():
            if isinstance(item, (OutlineVirtualHelixItem, OutlineOligoItem)):
                item.setData(column, Qt.EditRole, False)
                # print("hiding", item.__class__.__name__)
            else:
                print("item unhidable", item.__class__.__name__)
    # end def

    def showSelection(self):
        column = VISIBLE_COL
        for item in self.selectedItems():
            if isinstance(item, (OutlineVirtualHelixItem, OutlineOligoItem)):
                item.setData(column, Qt.EditRole, True)
                # print("showing", item.__class__.__name__)
            else:
                print("item unshowable", item.__class__.__name__)
    # end def

    def deleteSelection(self):
        cmds = []
        doc = self._document
        u_s = doc.undoStack()
        do_exec = True
        for item in self.selectedItems():
            if isinstance(item, OutlineOligoItem):
                model = item.cnModel()
                cmds += model.destroy()
            elif isinstance(item, OutlineVirtualHelixItem):
                if do_exec:
                    do_exec = False
                    u_s.beginMacro("delete Virtual Helices")
                part = item.cnModel()
                part.removeVirtualHelix(item.idNum())
            else:
                print("item undeletable", item.__class__.__name__)
        if do_exec:
            util.execCommandList(doc,
                                 cmds,
                                 desc="Clear Items",
                                 use_undostack=True)
        else:
            u_s.endMacro()
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
            if isinstance(item, (OutlineVirtualHelixItem, OutlineOligoItem)):
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

        res = QTreeWidget.dropEvent(self, event)
        if isinstance(dest_item, OutlineVirtualHelixItem):
            part = dest_item.part()
            vhi_list = [dest_parent.child(i) for i in range(dest_parent.childCount())]
            part.setImportedVHelixOrder([vhi.idNum() for vhi in vhi_list], check_batch=False)
    # end def

    def decodeMimeData(self, bytearray):
        """
        see:
        https://wiki.python.org/moin/PyQt/Handling%20Qt's%20internal%20item%20MIME%20type
        http://doc.qt.io/qt-5.5/datastreamformat.html
        """
        data = {}
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
        return data
    # end def

    # def addDummyRow(self, part_name, visible, color, parent_QTreeWidgetItem=None):
    #     if parent_QTreeWidgetItem is None:
    #         parent_QTreeWidgetItem = self.invisibleRootItem()
    #     tw_item = QTreeWidgetItem(parent_QTreeWidgetItem)
    #     tw_item.setData(0, Qt.EditRole, part_name)
    #     tw_item.setData(1, Qt.EditRole, visible)
    #     tw_item.setData(2, Qt.EditRole, color)
    #     tw_item.setFlags(tw_item.flags() | Qt.ItemIsEditable)
    #     return tw_item
    # # end def

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
            na_part_item = OutlineNucleicAcidPartItem(model_part, parent=self)
            self._instance_items[model_part_instance] = na_part_item
            self.setCurrentItem(na_part_item)
            self.is_child_adding -= 1
        else:
            print("part type", part_type)
            raise NotImplementedError
    # end def

    def selectionFilterChangedSlot(self, filter_name_set):
        '''Disable or enable items if their features are represented

        https://stackoverflow.com/questions/8961449/pyqt-qtreewidget-iterating#8961820
        '''
        # print("match")
        root_check = int(ROOT_FLAGS)
        disable_check = int(DISABLE_FLAGS)
        if OutlineVirtualHelixItem.FILTER_NAME in filter_name_set:
            set_vh_on = True
        else:
            set_vh_on = False
        root_A = self.invisibleRootItem()
        child_count_A = root_A.childCount()
        for a in range(child_count_A):
            root_B = root_A.child(a)
            # print(root_B.text(0))
            child_count_B = root_B.childCount()
            for b in range(child_count_B):
                root_C = root_B.child(b)
                root_C_txt = root_C.text(0)
                root_C_flags = int(root_C.flags())
                if root_C_txt == 'Virtual Helices':
                    if not set_vh_on and root_C_flags == root_check:
                        # print("do disable")
                        root_C.setFlags(DISABLE_FLAGS)
                    # else:
                    #     print("ADSAD", int(root_C.flags()), int(ROOT_FLAGS))
                    elif set_vh_on and root_C_flags == disable_check:
                            # print("do enable")
                            root_C.setFlags(ROOT_FLAGS)
                elif root_C_txt == 'Oligos':
                    if set_vh_on and root_C_flags == root_check:
                        root_C.setFlags(DISABLE_FLAGS)
                    elif not set_vh_on and root_C_flags == disable_check:
                        root_C.setFlags(ROOT_FLAGS)

                # child_count_C = root_C.childCount()
                # for c in range(child_count_C):
                #     root_D = root_C.child(c)
                #     print(root_D.text(0))
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        pass
    # end def

    def resetRootItemSlot(self, doc):
        self.clear()
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
        if column == NAME_COL:  # Model name
            item = self.parent().itemFromIndex(model_index)
            if item.CAN_NAME_EDIT:
                editor = QLineEdit(parent_QWidget)
                editor.setAlignment(Qt.AlignVCenter)
                return editor
        elif column == 1:  # Visibility checkbox
            # editor = QCheckBox(parent_QWidget)
            # setAlignment doesn't work https://bugreports.qt-project.org/browse/QTBUG-5368
            # return editor
            return None
        elif column == COLOR_COL:  # Color Picker
            editor = QColorDialog(parent_QWidget)
            return editor
        else:
            return QStyledItemDelegate.createEditor(self,
                                                    parent_QWidget,
                                                    option,
                                                    model_index)
    # end def

    def setEditorData(self, editor, model_index):
        column = model_index.column()
        if column == NAME_COL:  # Part Name
            text_QString = model_index.model().data(model_index, Qt.EditRole)
            editor.setText(text_QString)
        # elif column == VISIBLE_COL: # Visibility
        #     value = model_index.model().data(model_index, Qt.EditRole)
        #     editor.setChecked(value)
        elif column == COLOR_COL:  # Color
            value = model_index.model().data(model_index, Qt.EditRole)
            editor.setCurrentColor(QColor(value))
        else:
            QStyledItemDelegate.setEditorData(self, editor, model_index)
    # end def

    def setModelData(self, editor, model, model_index):
        column = model_index.column()
        if column == NAME_COL:  # Part Name
            text_QString = editor.text()
            model.setData(model_index, text_QString, Qt.EditRole)
        # elif column == VISIBLE_COL: # Visibility
        #     value = editor.isChecked()
        #     model.setData(model_index, value, Qt.EditRole)
        elif column == COLOR_COL:  # Color
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
        if column == NAME_COL:  # Part Name
            option.displayAlignment = Qt.AlignVCenter
            QStyledItemDelegate.paint(self, painter, option, model_index)
        if column == LOCKED_COL:  # Visibility
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
                # element = _QCOMMONSTYLE.PE_IndicatorMenuCheckMark
                # _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
                # _QCOMMONSTYLE.drawItemText(painter, new_rect, Qt.AlignCenter, styleoption.palette, True, 'L')
                icon = QPixmap(":/outlinericons/lock")
                _QCOMMONSTYLE.drawItemPixmap(painter, new_rect, Qt.AlignCenter, icon)
        if column == VISIBLE_COL:  # Visibility
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
                # element = _QCOMMONSTYLE.PE_IndicatorMenuCheckMark
                # _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
                icon = QPixmap(":/outlinericons/eye")
                _QCOMMONSTYLE.drawItemPixmap(painter, new_rect, Qt.AlignCenter, icon)
        elif column == COLOR_COL:  # Color

            # Alternate way to get color
            # outline_tw = self.parent()
            # item = outline_tw.itemFromIndex(model_index)
            # color = item.getColor()
            # print("COLOR_COL", item)

            color = model_index.model().data(model_index, Qt.EditRole)
            element = _QCOMMONSTYLE.PE_IndicatorCheckBox
            styleoption = QStyleOptionViewItem()
            brush = getBrushObj(color)
            styleoption.palette.setBrush(QPalette.Button, brush)
            styleoption.rect = new_rect
            _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
        else:
            QStyledItemDelegate.paint(self, painter, option, model_index)
    # end def

    def itemSelectionChanged(self):
        print("pppppp", self.selectedItems())
    # end def
# end class CustomStyleItemDelegate
