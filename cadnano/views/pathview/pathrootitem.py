# -*- coding: utf-8 -*-
from typing import List, Set

from PyQt5.QtCore import (
    Qt,
    QRectF
)
from PyQt5.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsItem,
    QGraphicsSceneMouseEvent
)
from PyQt5.QtGui import QKeyEvent

from cadnano.objectinstance import ObjectInstance
from cadnano import util
from cadnano.proxies.cnenum import PartEnum
from cadnano.controllers import ViewRootController
from .nucleicacidpartitem import PathNucleicAcidPartItem
from .tools.pathselection import SelectionItemGroup
from cadnano.views.pathview import PathToolManagerT
from cadnano.cntypes import (
    WindowT,
    DocT,
    NucleicAcidPartT
)

class PathRootItem(QGraphicsRectItem):
    """``PathRootItem`` is the root item in the PathView. It gets added directly
    to the pathscene by ``DocumentWindow``. It receives two signals::

        partAddedSignal and documentSelectedPartChangedSignal

    via its ``ViewRootController``.

    ``PathRootItem`` must instantiate its own controller to receive signals
    from the model.

    Attributes:
        findChild (TYPE): Description
        manager (TYPE): Description
        name (str): Description
        select_tool (TYPE): Description
    """
    findChild = util.findChild  # for debug
    name = 'path'

    def __init__(self,  rect: QRectF,
                        parent: QGraphicsItem,
                        window: WindowT,
                        document: DocT):
        """Summary

        Args:
            rect: Rectangle of this item
            parent: parent object
            window: DocumentWindow
            document: Document
        """
        super(PathRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._part_item_for_part_instance = {}  # Maps Part -> PartItem
        self._prexover_filter = None
        self.manager = None
        self.select_tool = None
        self.are_signals_on: bool = True
        self.setFlag(QGraphicsItem.ItemHasNoContents)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partItems(self) -> List[ObjectInstance]:
        """
        Returns:
            iterator: of all ``PathNucleicAcidPartItem``s in the view
        """
        return self._part_item_for_part_instance.values()

    def partItemForPart(self, part: NucleicAcidPartT) -> ObjectInstance:
        """
        Args:
            part: The model Part

        Returns:
            The :obj:`ObjectInstance` of the :obj:`NucleicAcidPart`
        """
        return self._part_item_for_part_instance[part]

    def partAddedSlot(self, sender: NucleicAcidPartT,
                            part_instance: ObjectInstance):
        """Receives notification from the model that a part has been added.
        The Pathview doesn't need to do anything on part addition, since
        the Sliceview handles setting up the appropriate lattice.

        Args:
            sender: Model object that emitted the signal.
            part_instance: ``ObjectInstance``

        Raises:
            NotImplementedError: for unknown ``part_type``
        """
        if self.are_signals_on:
            win = self._window
            part_type = part_instance.reference().partType()

            if part_type == PartEnum.PLASMIDPART:
                pass
            elif part_type == PartEnum.NUCLEICACIDPART:
                na_part_item = PathNucleicAcidPartItem(part_instance, viewroot=self)
                self._part_item_for_part_instance[part_instance] = na_part_item
                win.path_tool_manager.setActivePart(na_part_item)
            else:
                raise NotImplementedError("Unknown part type %s" % part_type)
    # end def

    def clearSelectionsSlot(self, doc: DocT):
        """
        Args:
            doc: ``Document``
        """
        self.select_tool.resetSelections()
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def selectionFilterChangedSlot(self, filter_name_set: Set[str]):
        """
        Args:
            filter_name_set: the set of all filters enabled
        """
        self.select_tool.clearSelections(False)
    # end def

    def preXoverFilterChangedSlot(self, filter_name: str):
        """
        Args:
            filter_name: the name of the filter
        """
        # print("path updating preXovers", filter_name)
        self._prexover_filter = filter_name
    # end def

    def resetRootItemSlot(self, doc: DocT):
        """
        Args:
            doc: ``Document``
        """
        self.select_tool.resetSelections()
        self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def window(self) -> WindowT:
        """
        Returns:
            The :obj:`DocumentWindow`
        """
        return self._window
    # end def

    def document(self) -> DocT:
        """
        Returns:
            The :obj:`Document`
        """
        return self._document
    # end def

    ### PUBLIC METHODS ###
    def destroyViewItems(self):
        print("destroying path view")
        items = list(self._part_item_for_part_instance.values())
        for item in items:
            item.destroyItem()
    # end def

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_F:
            self.scene().views()[0].zoomToFit()
    # end def

    def removePartItem(self, part_item: PathNucleicAcidPartItem):
        """
        Args:
            part_item: Remove the ``PartItem`` from the dicitionary
            of instances
        """
        for k in self._part_item_for_part_instance.keys():
            if k == part_item:
                del self._part_item_for_part_instance[k]
                return
    # end def

    def resetDocumentAndController(self, document: DocT):
        """
        Args:
            document: Description
        """
        self._document = document
        self._controller = ViewRootController(self, document)
    # end def

    def setModifyState(self, is_on: bool):
        """
        Args:
            is_on: Description
        """
        for part_item in self._part_item_for_part_instance.values():
            part_item.setModifyState(is_on)
    # end def

    def selectionFilterSet(self) -> Set[str]:
        """
        Returns:
            ``Document`` filter set
        """
        return self._document.filter_set
    # end def

    def vhiHandleSelectionGroup(self) -> SelectionItemGroup:
        """
        Returns:
            the selection group
        """
        return self.select_tool.vhi_h_selection_group
    # end def

    def strandItemSelectionGroup(self) -> SelectionItemGroup:
        """
        Returns:
            the selection group
        """
        return self.select_tool.strand_item_selection_group
    # end def

    def selectionLock(self) -> SelectionItemGroup:
        """
        Returns:
            ``SelectionItemGroup`` or ``None``
        """
        return self.scene().views()[0].selectionLock()
    # end def

    def setSelectionLock(self, locker: SelectionItemGroup):
        """
        Args:
            locker: Description
        """
        self.scene().views()[0].setSelectionLock(locker)
    # end def

    def setManager(self, manager: PathToolManagerT):
        """
        Args:
            manager: The tool manager
        """
        self.manager = manager
        self.select_tool = manager.select_tool
    # end def

    def clearSelectionsIfActiveTool(self):
        """
        """
        if self.manager.isSelectToolActive():
            self.select_tool.clearSelections(False)
    # end def

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handler for user mouse press.

        Args:
            event: Contains item, scene, and screen coordinates of the event,
                and previous event.
        """
        self.clearSelectionsIfActiveTool()
        return QGraphicsRectItem.mousePressEvent(self, event)
# end class
