class PartItemController(object):
    def __init__(self, part_item, model_part):
        self._part_item = part_item
        self._model_part = model_part
        self.connectSignals()

    def connectSignals(self):
        m_p = self._model_part
        p_i = self._part_item

        if hasattr(p_i, "partHideSlot"):
            m_p.partHideSignal.connect(p_i.partHideSlot)
        if hasattr(p_i, "partActiveVirtualHelixChangedSlot"):
            m_p.partActiveVirtualHelixChangedSignal.connect(p_i.partActiveVirtualHelixChangedSlot)

        m_p.partDimensionsChangedSignal.connect(p_i.partDimensionsChangedSlot)
        m_p.partParentChangedSignal.connect(p_i.partParentChangedSlot)
        m_p.partPreDecoratorSelectedSignal.connect(p_i.partPreDecoratorSelectedSlot)
        m_p.partRemovedSignal.connect(p_i.partRemovedSlot)
        m_p.partStrandChangedSignal.connect(p_i.updatePreXoverItemsSlot)
        m_p.partVirtualHelixAddedSignal.connect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRenumberedSignal.connect(p_i.partVirtualHelixRenumberedSlot)
        m_p.partVirtualHelixResizedSignal.connect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelicesReorderedSignal.connect(p_i.partVirtualHelicesReorderedSlot)
    # end def

    def disconnectSignals(self):
        m_p = self._model_part
        p_i = self._part_item
        
        if hasattr(p_i, "partHideSlot"):
            m_p.partHideSignal.disconnect(p_i.partHideSlot)
        if hasattr(p_i, "partActiveVirtualHelixChangedSlot"):
            m_p.partActiveVirtualHelixChangedSignal.disconnect(p_i.partActiveVirtualHelixChangedSlot)

        m_p.partDimensionsChangedSignal.disconnect(p_i.partDimensionsChangedSlot)
        m_p.partParentChangedSignal.disconnect(p_i.partParentChangedSlot)
        m_p.partPreDecoratorSelectedSignal.disconnect(p_i.partPreDecoratorSelectedSlot)
        m_p.partRemovedSignal.disconnect(p_i.partRemovedSlot)
        m_p.partStrandChangedSignal.disconnect(p_i.updatePreXoverItemsSlot)
        m_p.partVirtualHelixAddedSignal.disconnect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRenumberedSignal.disconnect(p_i.partVirtualHelixRenumberedSlot)
        m_p.partVirtualHelixResizedSignal.disconnect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelicesReorderedSignal.disconnect(p_i.partVirtualHelicesReorderedSlot)
    # end def
# end class
