
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem

CUSTOM_ITEM_TYPE = 1300

class CustomTreeWidgetItem(QTreeWidgetItem):
    """
    CustomTreeWidgetItem sets some default flags like ItemIsEditable.

    The point of subclassing QTreeWidgetItem is to clean up some of the
    repetitive code in the propertyview *item classes.
    """
    def __init__(self, parent=None):
        super(QTreeWidgetItem, self).__init__(parent, CUSTOM_ITEM_TYPE)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
    # end def
# end class
