from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidgetItem

NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2


LEAF_FLAGS = (Qt.ItemIsSelectable | Qt.ItemIsEnabled |
                Qt.ItemIsDragEnabled | Qt.ItemIsEditable |
                Qt.ItemIsUserCheckable)

class CNOutlinerItem(QTreeWidgetItem):

    PROPERTIES = {'name':NAME_COL, 'is_visible': VISIBLE_COL, 'color':COLOR_COL}
    CAN_NAME_EDIT = True

    def __init__(self, cn_model, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._cn_model = cn_model
        name = cn_model.getName()
        color = cn_model.getColor()
        self.setData(NAME_COL, Qt.EditRole, name)
        self.setData(VISIBLE_COL, Qt.EditRole, True) # is_visible
        self.setData(COLOR_COL, Qt.EditRole, color)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def __hash__(self):
        """ necessary as CNOutlinerItem as a base class is unhashable
        but necessary due to __init__ arg differences for whatever reason
        """
        return hash(self._cn_model)

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        pass
    # end def

    def cnModel(self):
        return self._cn_model
    # end def

    def createRootPartItem(self, item_name, parent):
        """ use this for sub-lists for part items
        """
        twi = QTreeWidgetItem(parent, QTreeWidgetItem.UserType)
        twi.setData(NAME_COL, Qt.EditRole, item_name)
        twi.setData(VISIBLE_COL, Qt.EditRole, True) # is_visible
        twi.setData(COLOR_COL, Qt.EditRole, "#ffffff") # color
        twi.setFlags(twi.flags() & ~Qt.ItemIsSelectable)
        twi.setExpanded(True)
        twi.part = lambda : self._cn_model
        return twi
    # end def

    def updateCNModel(self):
        # this works only for color. uncomment below to generalize to properties
        # print("outliner %s - updateCNModel" % (str(type(self))))
        cn_model = self._cn_model
        name = self.data(NAME_COL, Qt.DisplayRole)
        color = self.data(COLOR_COL, Qt.DisplayRole)
        if name != cn_model.getName():
            cn_model.setProperty('name', name)
        if color != cn_model.getColor():
            cn_model.setProperty('color', color)
    # end def

    def setValue(self, key, value):
        # cn_model = self._cn_model
        if key == 'name':
            name = self.data(NAME_COL, Qt.DisplayRole)
            if name != value:
                self.setData(NAME_COL, Qt.EditRole, value)
        elif key == 'color':
            color = self.data(COLOR_COL, Qt.DisplayRole)
            if color != value:
                self.setData(COLOR_COL, Qt.EditRole, value)
        else:
            "property not supported"
            # pass
            # raise KeyError("No property %s in cn_model" % (key))
    # end def

# end class
