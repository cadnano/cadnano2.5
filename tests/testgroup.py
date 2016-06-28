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

    # def itemChange(self, change, value):
    #     print("\nChange %s\n" % self, change, value)
    #     return QGraphicsItem.itemChange(self, change, value)
    # # end def


class MyRectItem(QGraphicsRectItem):
    Type = QGraphicsItem.UserType + 1

    def __init__(self, parent=None):
        super(MyRectItem, self).__init__(parent)

    # def __repr__(self):
    #     return str(type(self).__name__)

    def itemChange(self, change, value):
        print("\nChange %s\n" % self, change, value)
        return super(MyRectItem, self).itemChange(change, value)
        # return QGraphicsItem.itemChange(self, change, value)
    # end def

if __name__ == '__main__':
    a = MyRectItemNOIC()
    b = MyRectItem(a)
    item_group = MyItemGroup()

    print("parent:", b.parentItem())
    print(a.childItems())
    item_group.addToGroup(b)
    print(item_group.childItems(), b.parentItem())

    e = MyRectItem()
    c = MyRectItemNOIC(e)
    print("\nparent NOIC:", c.parentItem())
    item_group.addToGroup(c)
    print(item_group.childItems(), c.parentItem())