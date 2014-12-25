
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem


class PropertyItem(QTreeWidgetItem):
    """
    The point of subclassing QTreeWidgetItem is to clean up some of the
    repetitive code in the propertyview *item classes.

    PropertyItem sets some default flags like ItemIsEditable.
    """
    def __init__(self, model_part, key, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self._model_part = model_part
        self._key = key
    # end def

    def setPartProperty(self, key, value):
        key = self.data(0, Qt.DisplayRole)
        value = self.data(1, Qt.DisplayRole)
        self._model_part.setProperty(key, value)
    # end def
# end class

class SelectionItem(QTreeWidgetItem):
    """
    SelectionItem is a custom item for grouping editable
    properties of an individual selection.
    """
    def __init__(self, model_part, selection_name, start, end, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self._model_part = m_p = model_part
        self._name = selection_name
        self._start = start
        self._end = end

        self.setData(0, Qt.EditRole, "name")
        self.setData(1, Qt.EditRole, selection_name)

        start_item = SelectionPropertyItem(m_p, selection_name, self)
        start_item.setData(0, Qt.EditRole, "start")
        start_item.setData(1, Qt.EditRole, start)
        start_item.setProperty = start_item.setSelectionStart

        end_item = SelectionPropertyItem(m_p, selection_name, self)
        end_item.setData(0, Qt.EditRole, "end")
        end_item.setData(1, Qt.EditRole, end)
        end_item.setProperty = end_item.setSelectionEnd
    # end def

    def setProperty(self, value):
        value = self.data(1, Qt.DisplayRole)
        self._model_part.setSelectionName(_model_selection, value)
    # end def

    # def setPartProperty(self, key, value):
    #     key = self.data(0, Qt.DisplayRole)
    #     value = self.data(1, Qt.DisplayRole)
    #     self._model_part.setProperty(key, value)
    # # end def
# end class


class SelectionPropertyItem(QTreeWidgetItem):
    """
    The point of subclassing QTreeWidgetItem is to clean up some of the
    repetitive code in the propertyview *item classes.

    PropertyItem sets some default flags like ItemIsEditable.
    """
    def __init__(self, model_part, model_selection, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self._model_part = model_part
        self._model_selection = model_selection
    # end def

    def setProperty(self, value):
        pass
    # end def

    def setSelectionName(self, value):
        value = self.data(1, Qt.DisplayRole)
        self._model_part.setSelectionName(_model_selection, value)
    # end def

    def setSelectionStart(self, value):
        value = self.data(1, Qt.DisplayRole)
        self._model_part.setSelectionStart(_model_selection, value)
    # end def

    def setSelectionEnd(self, value):
        value = self.data(1, Qt.DisplayRole)
        self._model_part.setSelectionEnd(_model_selection, value)
    # end def
# end class