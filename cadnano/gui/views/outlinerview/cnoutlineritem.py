from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem

NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2

class CNOutlinerItem(QTreeWidgetItem):

    PROPERTIES = {'name':NAME_COL, 'is_visible': VISIBLE_COL, 'color':COLOR_COL}

    def __init__(self, cn_model, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._cn_model = cn_model
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        name = cn_model.getName()
        color = cn_model.getColor()
        self.setData(0, Qt.EditRole, name)
        self.setData(1, Qt.EditRole, True) # is_visible
        self.setData(2, Qt.EditRole, color)
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        pass
    # end def

    def cnModel(self):
        return self._cn_model
    # end def

    def createRootItem(self, item_name, parent):
        twi = QTreeWidgetItem(parent, QTreeWidgetItem.UserType)
        twi.setData(NAME_COL, Qt.EditRole, item_name)
        twi.setData(VISIBLE_COL, Qt.EditRole, True) # is_visible
        twi.setData(COLOR_COL, Qt.EditRole, "#ffffff") # color
        twi.setFlags(twi.flags() & ~Qt.ItemIsSelectable)
        twi.setExpanded(True)
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
        cn_model = self._cn_model
        if key == 'name':
            name = self.data(NAME_COL, Qt.DisplayRole)
            if name != value:
                self.setData(NAME_COL, Qt.EditRole, value)
        elif key == 'color':
            color = self.data(COLOR_COL, Qt.DisplayRole)
            if color != value:
                self.setData(COLOR_COL, Qt.EditRole, value)
        else:
            raise KeyError("No property %s in cn_model" % (key))
    # end def

# end class
