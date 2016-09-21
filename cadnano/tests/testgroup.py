# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsItemGroup
from PyQt5.QtCore import pyqtSlot


class MyItemGroup(QGraphicsItemGroup):
    Type = QGraphicsItem.UserType + 3
    def __init__(self, parent=None):
        super(MyItemGroup, self).__init__(parent)

    def __repr__(self):
        return str(type(self).__name__)

class MyRectItemNOIC(QGraphicsRectItem):
    Type = QGraphicsItem.UserType + 2
    def __init__(self, parent=None):
        super(MyRectItemNOIC, self).__init__(parent)

    def __repr__(self):
        return str(type(self).__name__)

# end class


class MyRectItem(QGraphicsRectItem):
    Type = QGraphicsItem.UserType + 1

    def __init__(self, parent=None):
        super(MyRectItem, self).__init__(parent)

    # def __repr__(self):
    #     return str(type(self).__name__)

    def itemChange(self, change, value):
        assert isinstance(self, MyRectItem)
        # print("\nChange %s\n" % self, change, value)
        return super(MyRectItem, self).itemChange(change, value)
    # end def

def testItemChangeRegression():
    """Make sure PyQt5 handles QGraphicsItem.itemChange correctly
    as there was a regression in PyQt5 v 5.6 that was fixed in v 5.7
    """
    a = MyRectItemNOIC()
    b = MyRectItem(a)
    item_group = MyItemGroup()
    assert b.parentItem() is a
    assert a.childItems()[0] is b
    item_group.addToGroup(b)
    assert item_group.childItems()[0] is b
    assert b.parentItem() is item_group
    e = MyRectItem()
    c = MyRectItemNOIC(e)
    assert c.parentItem() is e
    item_group.addToGroup(c)
    assert c.parentItem() is item_group
# end def