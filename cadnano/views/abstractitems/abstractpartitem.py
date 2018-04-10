# -*- coding: utf-8 -*-
from typing import (
    Set,
    Any,
    List
)

from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem
from cadnano.objectinstance import ObjectInstance
from cadnano.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.cntypes import (
    DocT,
    OligoT,
    ABInfoT,
    PartT,
    VirtualHelixT
)

class AbstractPartItem(object):
    """Use for multiple inheritance
    AbstractPartItem is a base class for partitems in all views.
    It includes slots that get connected in PartItemController which
    can be overridden.  NO ARGUMENTS EXIST IN THE CONSTRUCTOR TO ASSIST THE
    MULTIPLE INHERITANCE

    THE SUBCLASS MUST SET ``self._model_part``

    If you want to add a new signal to the model, adding the slot here
    means it's not necessary to add the same slot to every item across
    all views.
    """

    def __init__(self):
        self._oligo_item_hash = {}
        self._virtual_helix_item_hash = {}
        self.active_virtual_helix_item = None
        self.is_active = False
    # end def

    def part(self) -> PartT:
        return self._model_part
    # end def

    def setProperty(self, key: str, value: Any):
        self._model_part.setProperty(key, value)
    # end def

    def getProperty(self, key: str) -> Any:
        return self._model_part.getProperty(key)
    # end def

    def getModelProperties(self) -> dict:
        """Get the dictionary of model properties

        Returns:
            group properties
        """
        return self._model_part.getModelProperties()
    # end def

    def setMovable(self, is_movable: bool):
        self.setFlag(QGraphicsItem.ItemIsMovable, is_movable)
    # end def

    def document(self) -> DocT:
        """Return a reference to the model's document object"""
        return self._model_part.document()
    # end def

    def scaleFactor(self) -> float:
        return self.scale_factor
    # end def

    def idToVirtualHelixItem(self, id_num: int) -> AbstractVirtualHelixItem:
        return self._virtual_helix_item_hash[id_num]
    # end def

    def setActive(self):
        self._model_part.setActive(True)
    # end def

    def partZDimensionsChangedSlot(self, part: PartT,
                                        min_id_num: int,
                                        max_id_num: int):
        """Accounts for Z translations in parts
        Args:
            part:
            min_id_num: id number of the least Z Virtual Helix
            max_id_num: id number of most Z Virtual Helix
        """

    def partOligoAddedSlot(self, part: PartT, oligo: OligoT):
        pass

    def partParentChangedSlot(self, part: PartT):
        pass

    def partPropertyChangedSlot(part: PartT, key: str, new_value: Any):
        pass

    def partRemovedSlot(self, part: PartT):
        pass

    def partSelectedChangedSlot(self, part: PartT, is_selected: bool):
        pass

    def partWorkplaneChangedSlot(self, start_idx: int, end_idx: int):
        pass

    def partActiveVirtualHelixChangedSlot(self, part: PartT, id_num: int):
        pass

    def partActiveBaseInfoSlot(self, part: PartT, info: ABInfoT):
        pass

    def partActiveChangedSlot(self, part: PartT, is_active: bool):
        pass

    def partInstancePropertySlot(self, part: PartT, view_name: str, key: str, value: Any):
        pass

    def partVirtualHelixAddedSlot(self, part: PartT,
                                        id_num: int,
                                        virtual_helix: VirtualHelixT,
                                        neighbors: List[int],
                                        view: int):
        pass

    def partVirtualHelixRemovingSlot(self,  part: PartT,
                                            id_num: int,
                                            virtual_helix: VirtualHelixT,
                                            neighbors: List[int]):
        pass

    def partVirtualHelixRemovedSlot(self, part: PartT, id_num: int):
        pass

    def partVirtualHelixResizedSlot(self,   part: PartT,
                                            id_num: int,
                                            virtual_helix: VirtualHelixT):
        pass

    def partVirtualHelicesTranslatedSlot(self, part: PartT, vh_set: Set[int]):
        pass

    def partVirtualHelicesSelectedSlot(self, part: PartT, vh_set: Set[int], is_adding: bool):
        """is_adding: adding (``True``) virtual helices to a selection
        or removing (``False``)
        """

    def partVirtualHelixPropertyChangedSlot(self,   part: PartT,
                                                    id_num: int,
                                                    virtual_helix: VirtualHelixT,
                                                    new_value: Any):
        pass

    def partDocumentSettingChangedSlot(self, part: PartT, key: str, value: Any):
        pass
    # end def
# end class

class QAbstractPartItem(QGraphicsRectItem):
    """Use for single inheritance
    :class:`QAbstractPartItem` is a base class for partitems in all views.
    It includes slots that get connected in :class:`PartItemController` which
    can be overridden.

    If you want to add a new signal to the model, adding the slot here
    means it's not necessary to add the same slot to every item across
    all views.
    """

    def __init__(self,  part_instance: ObjectInstance,
                        viewroot: QGraphicsItem):
        super(QAbstractPartItem, self).__init__(parent=viewroot)
        self._model_part = m_p = part_instance.reference()
        self._model_instance: ObjectInstance = part_instance
        self._model_props = m_p.getModelProperties()
        self._viewroot = viewroot
        self._oligo_item_hash = {}
        self._virtual_helix_item_hash = {}
        self.active_virtual_helix_item = None
        self.is_active = False
        self._controller = None
        m_p.setInstanceProperty(part_instance, '%s:position' % (viewroot.name), (0., 0.))
    # end def

    def destroyItem(self):
        '''Remove this object and references to it from the view
        '''
        if self._controller is not None:
            self._controller.disconnectSignals()
            self._controller = None
        self._model_part = None
        self._model_instance = None
        self._model_props = None
        self._viewroot = None
        self._oligo_item_hash = None
        self._virtual_helix_item_hash = None
        self.active_virtual_helix_item = None
        self.parentItem().removePartItem(self)
        scene = self.scene()
        scene.removeItem(self)
    # end def

    def part(self) -> PartT:
        return self._model_part

    def partInstance(self) -> ObjectInstance:
        return self._model_instance

    def viewRoot(self) -> QGraphicsItem:
        return self._viewroot

    def setProperty(self, key: str, value: Any):
        self._model_part.setProperty(key, value)
    # end def

    def getProperty(self, key: str) -> Any:
        self._model_part.getProperty(key)
    # end def

    def getModelProperties(self) -> dict:
        """Get the dictionary of model properties

        Returns:
            group properties
        """
        return self._model_part.getModelProperties()
    # end def

    def getFilterSet(self) -> Set[str]:
        return self._viewroot._document.filter_set
    # end def

    def setMovable(self, is_movable: bool):
        self._viewroot.manager.select_tool.resetSelections()
        self.setFlag(QGraphicsItem.ItemIsMovable, is_movable)
    # end def

    def isMovable(self) -> bool:
        return self.flags() & QGraphicsItem.ItemIsMovable
    # end def

    def finishDrag(self):
        """set the view position in the model
        Does NOT convert to model coordinates, for now
        """
        pos = self.pos()
        position = pos.x(), pos.y()
        view_name = self._viewroot.name
        self._model_part.changeInstanceProperty(self._model_instance,
                                                view_name, 'position', position)
    # end def

    def document(self) -> DocT:
        """Return a reference to the model's document object"""
        return self._model_part.document()
    # end def

    def scaleFactor(self) -> float:
        return self.scale_factor
    # end def

    def idToVirtualHelixItem(self, id_num: int) -> AbstractVirtualHelixItem:
        return self._virtual_helix_item_hash[id_num]
    # end def

    def setActive(self):
        self._model_part.setActive(True)
    # end def

    def partZDimensionsChangedSlot(self, part: PartT, min_id_num: int, max_id_num: int):
        """Accounts for Z translations in parts
        Args:
            part:
            min_id_num: id number of the least Z Virtual Helix
            max_id_num: id number of most Z Virtual Helix
        """

    def partOligoAddedSlot(self, part: PartT, oligo: OligoT):
        pass

    def partParentChangedSlot(self, part: PartT):
        pass

    def partPropertyChangedSlot(part: PartT, key: str, new_value: Any):
        pass

    def partRemovedSlot(self, part: PartT):
        pass

    def partSelectedChangedSlot(self, part: PartT, is_selected: bool):
        pass

    def partActiveVirtualHelixChangedSlot(self, part: PartT, id_num: int):
        pass

    def partActiveBaseInfoSlot(self, part: PartT, info: ABInfoT):
        pass

    def partActiveChangedSlot(self, part: PartT, is_active: bool):
        pass

    def partInstancePropertySlot(self, part: PartT, view_name: str, key: str, value: Any):
        if view_name == self._viewroot.name:
            if key == 'position':
                self.setPos(*value)
    # end def

    def partVirtualHelixAddedSlot(self, part: PartT,
                                        id_num: int,
                                        virtual_helix: VirtualHelixT,
                                        neighbors: List[int],
                                        view: int):
        pass

    def partVirtualHelixRemovingSlot(self,  part: PartT,
                                            id_num: int,
                                            virtual_helix: VirtualHelixT,
                                            neighbors: List[int]):
        pass

    def partVirtualHelixRemovedSlot(self, part: PartT, id_num: int):
        pass

    def partVirtualHelixResizedSlot(self, part: PartT,
                                            id_num: int,
                                            virtual_helix: VirtualHelixT):
        pass

    def partVirtualHelicesTranslatedSlot(self, part: PartT, vh_set: Set[int]):
        pass

    def partVirtualHelicesSelectedSlot(self, part: PartT,
                                            vh_set: Set[int],
                                            is_adding: bool):
        """ is_adding (bool): adding (True) virtual helices to a selection
        or removing (False)
        """

    def partVirtualHelixPropertyChangedSlot(self, part: PartT,
                                                    id_num: int,
                                                    virtual_helix,
                                                    new_value: Any):
        pass

    def partDocumentSettingChangedSlot(self, part: PartT, key: str, value: Any):
        pass
    # end def
# end class