from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem
from cadnano.gui.palette import getBrushObj
from . import outlinerstyles as styles

NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2


LEAF_FLAGS = (Qt.ItemIsSelectable | Qt.ItemIsEnabled |
              Qt.ItemIsDragEnabled | Qt.ItemIsEditable |
              Qt.ItemIsUserCheckable)


class CNOutlinerItem(QTreeWidgetItem):

    PROPERTIES = {'name': NAME_COL, 'is_visible': VISIBLE_COL, 'color': COLOR_COL}
    CAN_NAME_EDIT = True

    def __init__(self, cn_model, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._cn_model = cn_model
        name = cn_model.getName()
        color = cn_model.getColor()
        self.setData(NAME_COL, Qt.EditRole, name)
        self.setData(VISIBLE_COL, Qt.EditRole, True)  # is_visible
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

    def getColor(self):
        return self._cn_model.getProperty('color')
    # end def

    def createRootPartItem(self, item_name, parent):
        """ use this for sub-lists for part items
        """
        return RootPartItem(self._cn_model, item_name, parent)
    # end def

    def updateCNModel(self):
        # this works only for color. uncomment below to generalize to properties
        # print("outliner %s - updateCNModel" % (str(type(self))))
        cn_model = self._cn_model
        name = self.data(NAME_COL, Qt.DisplayRole)
        color = self.data(COLOR_COL, Qt.DisplayRole)
        is_visible = self.data(VISIBLE_COL, Qt.DisplayRole)
        mname, mcolor, mvisible = cn_model.getOutlineProperties()
        if name is not None and name != mname:
            cn_model.setProperty('name', name)
        if color is not None and color != mcolor:
            cn_model.setProperty('color', color)
        if is_visible is not None and is_visible != mvisible:
            cn_model.setProperty('is_visible', is_visible)
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
        elif key == 'is_visible':
            is_visible = self.data(VISIBLE_COL, Qt.DisplayRole)
            if is_visible != value:
                self.setData(VISIBLE_COL, Qt.EditRole, value)
        else:
            "property not supported"
            # pass
            # raise KeyError("No property %s in cn_model" % (key))
    # end def

    def activate(self):
        self.setBackground(NAME_COL, getBrushObj(styles.ACTIVE_COLOR))
        self.is_active = True
    # end def

    def deactivate(self):
        # print("should deactivate outliner Part")
        self.setBackground(NAME_COL, getBrushObj(styles.INACTIVE_COLOR))
        self.is_active = False
    # end def
# end class

class RootPartItem(QTreeWidgetItem):
    def __init__(self, model_part, item_name, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._cn_model = model_part
        self.item_name = item_name
        self.setData(NAME_COL, Qt.EditRole, item_name)
        self.setData(VISIBLE_COL, Qt.EditRole, True)  # is_visible
        self.setData(COLOR_COL, Qt.EditRole, "#ffffff")  # color
        self.setFlags(self.flags() & ~Qt.ItemIsSelectable)
        self.setExpanded(True)
    # end def

    def __repr__(self):
        return "RootPartItem %s: for %s" %  (  self.item_name,
                                            self._cn_model.getProperty('name'))
    # end def

    def part(self):
        return self._cn_model

    def getColor(self):
        return "#ffffff"

