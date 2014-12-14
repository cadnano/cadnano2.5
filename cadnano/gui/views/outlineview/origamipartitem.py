from cadnano.gui.controllers.itemcontrollers.origamipartitemcontroller import OrigamiPartItemController

import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

ORIGAMI_ITEM_TYPE = 1200

class OrigamiPartItem(QTreeWidgetItem):
    def __init__(self, model_part, parent):
        super(QTreeWidgetItem, self).__init__(parent, ORIGAMI_ITEM_TYPE)
        self._part = model_part
        self._parent_tree = parent
        self._controller = OrigamiPartItemController(self, model_part)
        self.setText(0, model_part.__class__.__name__)
    # end def

    def partRemovedSlot(self, sender):
        self._parent_tree.removeOrigamiPartItem(self)
        self._part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partDimensionsChangedSlot(self, sender):
        pass
    # end def

    def partParentChangedSlot(self, sender):
        pass
    # end def

    def partPreDecoratorSelectedSlot(self, sender):
        pass
    # end def

    def updatePreXoverItemsSlot(self, sender):
        pass
    # end def

    def partVirtualHelixAddedSlot(self, sender):
        pass
    # end def

    def partVirtualHelixRenumberedSlot(self, sender):
        pass
    # end def

    def partVirtualHelixResizedSlot(self, sender):
        pass
    # end def

    def partVirtualHelicesReorderedSlot(self, sender):
        pass
    # end def
# end class
