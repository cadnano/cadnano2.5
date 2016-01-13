class PartItemController():
    def __init__(self, part_item, model_part):
        self._part_item = part_item
        self._model_part = model_part
    # end def

    def connectSignals(self):
        m_p = self._model_part
        p_i = self._part_item

        m_p.partDimensionsChangedSignal.connect(p_i.partDimensionsChangedSlot)
        m_p.partParentChangedSignal.connect(p_i.partParentChangedSlot)
        m_p.partRemovedSignal.connect(p_i.partRemovedSlot)
        m_p.partPropertyChangedSignal.connect(p_i.partPropertyChangedSlot)
        m_p.partSelectedChangedSignal.connect(p_i.partSelectedChangedSlot)

        m_p.partActiveVirtualHelixChangedSignal.connect(p_i.partActiveVirtualHelixChangedSlot)

        m_p.partVirtualHelixAddedSignal.connect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRemovedSignal.connect(p_i.partVirtualHelixRemovedSlot)
        m_p.partVirtualHelixRenumberedSignal.connect(p_i.partVirtualHelixRenumberedSlot)
        m_p.partVirtualHelixResizedSignal.connect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelicesReorderedSignal.connect(p_i.partVirtualHelicesReorderedSlot)
        m_p.partVirtualHelixTransformedSignal.connect(p_i.partVirtualHelixTransformedSlot)
        m_p.partVirtualHelicesTranslatedSignal.connect(p_i.partVirtualHelicesTranslatedSlot)
        m_p.partVirtualHelixPropertyChangedSignal.connect(p_i.partVirtualHelixPropertyChangedSlot)

        m_p.partOligoAddedSignal.connect(p_i.partOligoAddedSlot)
        m_p.partStrandChangedSignal.connect(p_i.updatePreXoverItemsSlot)
    # end def

    def disconnectSignals(self):
        m_p = self._model_part
        p_i = self._part_item

        m_p.partDimensionsChangedSignal.disconnect(p_i.partDimensionsChangedSlot)
        m_p.partParentChangedSignal.disconnect(p_i.partParentChangedSlot)
        m_p.partRemovedSignal.disconnect(p_i.partRemovedSlot)
        m_p.partPropertyChangedSignal.disconnect(p_i.partPropertyChangedSlot)
        m_p.partSelectedChangedSignal.disconnect(p_i.partSelectedChangedSlot)

        m_p.partActiveVirtualHelixChangedSignal.disconnect(p_i.partActiveVirtualHelixChangedSlot)

        m_p.partVirtualHelixAddedSignal.disconnect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRemovedSignal.disconnect(p_i.partVirtualHelixRemovedSlot)
        m_p.partVirtualHelixRenumberedSignal.disconnect(p_i.partVirtualHelixRenumberedSlot)
        m_p.partVirtualHelixResizedSignal.disconnect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelicesReorderedSignal.disconnect(p_i.partVirtualHelicesReorderedSlot)
        m_p.partVirtualHelixTransformedSignal.disconnect(p_i.partVirtualHelixTransformedSlot)
        m_p.partVirtualHelicesTranslatedSignal.disconnect(p_i.partVirtualHelicesTranslatedSlot)
        m_p.partVirtualHelixPropertyChangedSignal.disconnect(p_i.partVirtualHelixPropertyChangedSlot)

        m_p.partOligoAddedSignal.disconnect(p_i.partOligoAddedSlot)
        m_p.partStrandChangedSignal.disconnect(p_i.updatePreXoverItemsSlot)
    # end def
