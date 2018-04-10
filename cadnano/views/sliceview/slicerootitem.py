# -*- coding: utf-8 -*-
from typing import Set

from PyQt5.QtCore import (
    Qt,
    QRectF
)
from PyQt5.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsItem
)
from PyQt5.QtGui import QKeyEvent

from cadnano.objectinstance import ObjectInstance
from cadnano.proxies.cnenum import (
    PartEnum,
    ViewReceiveEnum
)
from cadnano.controllers import ViewRootController
from .nucleicacidpartitem import SliceNucleicAcidPartItem

from cadnano.views.sliceview import SliceToolManagerT
from cadnano.cntypes import (
    WindowT,
    DocT,
    NucleicAcidPartT
)

class SliceRootItem(QGraphicsRectItem):
    """SliceRootItem is the root item in the SliceView. It gets added directly
    to the slicescene by DocumentWindow. It receives two signals::

        partAddedSignal and selectedPartChangedSignal

    via its ``ViewRootController``.

    ``SliceRootItem`` must instantiate its own controller to receive signals
    from the model.

    Attributes:
        instance_items (dict): Description
        manager (TYPE): Description
        name (str): Description
        select_tool (TYPE): Description
    """
    name = 'slice'
    view_type = ViewReceiveEnum.SLICE

    def __init__(self,  rect: QRectF,
                        parent: QGraphicsItem,
                        window: WindowT,
                        document: DocT):
        """
        Args:
            rect: Rectangle of this item
            parent: parent object
            window: DocumentWindow
            document: Document
        """
        super(SliceRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self.instance_items = {}
        self.manager = None
        self.select_tool = None
        self.are_signals_on = True
        self.setFlag(QGraphicsItem.ItemHasNoContents)
    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender: NucleicAcidPartT,
                            part_instance: ObjectInstance):
        """Receives notification from the model that a part has been added.
        Views that subclass AbstractView should override this method.

        Args:
            sender: Model object that emitted the signal.
            part_instance: Description

        Raises:
            NotImplementedError: unknown ``part_type``
        """
        if self.are_signals_on:
            part_type = part_instance.reference().partType()
            if part_type == PartEnum.NUCLEICACIDPART:
                na_part_item = SliceNucleicAcidPartItem(part_instance,
                                                        viewroot=self)
                self.instance_items[na_part_item] = na_part_item
                self.select_tool.setPartItem(na_part_item)
                na_part_item.zoomToFit()
            else:
                raise NotImplementedError("Unknown part type %s" % part_type)
    # end def

    def documentChangeViewSignalingSlot(self, view_types: int):
        self.are_signals_on = True if view_types & self.view_type else False
    # end def

    def selectedChangedSlot(self, item_dict: dict):
        """
        Args:
            item_dict: Description
        """
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_set: Set[str]):
        """Update active tool to respond to active filters.

        Args:
            filter_name_set (set): list of active filters
        """
        # if 'virtual_helix' not in filter_name_set:
        #     self.manager.chooseCreateTool()
        tool = self.manager.activeToolGetter()
        tool.setSelectionFilter(filter_name_set)
        # for nucleicacid_part_item in self.instance_items:
        #     nucleicacid_part_item.setSelectionFilter(filter_name_set)
    # end def

    def preXoverFilterChangedSlot(self, filter_name: str):
        """
        Args:
            filter_name: Description
        """
        pass
    # end def

    def clearSelectionsSlot(self, doc: DocT):
        """
        Args:
            doc (TYPE): Description
        """
        self.select_tool.deselectItems()
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def resetRootItemSlot(self, doc: DocT):
        """
        Args:
            doc: Description
        """
        self.select_tool.deselectItems()
        self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def window(self) -> WindowT:
        """
        Returns:
            the :class:`DocumentWindow`
        """
        return self._window
    # end def

    ### METHODS ###
    def destroyViewItems(self):
        print("destroying slice view")
        for item in self.instance_items.values():
            item.destroyItem()
    # end def

    def removePartItem(self, part_item: SliceNucleicAcidPartItem):
        """
        Args:
            part_item: Description
        """
        del self.instance_items[part_item]
    # end def

    def resetDocumentAndController(self, document: DocT):
        """
        Args:
            document: Document

        Raises:
            ImportError: Description
        """
        self._document = document
        self._controller = ViewRootController(self, document)
        if len(self.instance_items) > 0:
            raise ImportError
    # end def

    def setModifyState(self, is_on: bool):
        """
        Args:
            is_on: Description
        """
        for nucleicacid_part_item in self.instance_items.values():
            nucleicacid_part_item.setModifyState(is_on)
    # end def

    def setManager(self, manager: SliceToolManagerT):
        """Set the ``manager``, and the ``select_tool``

        Args:
            manager: the Slice tool manager
        """
        self.manager = manager
        self.select_tool = manager.select_tool
    # end def

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_F:
            self.scene().views()[0].zoomToFit()

        for na_part_item in self.instance_items.values():
            if hasattr(na_part_item, 'keyPressEvent'):
                getattr(na_part_item, 'keyPressEvent')(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        for na_part_item in self.instance_items.values():
            if hasattr(na_part_item, 'keyReleaseEvent'):
                getattr(na_part_item, 'keyReleaseEvent')(event)
