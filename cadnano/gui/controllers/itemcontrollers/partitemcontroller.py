class PartItemController():
    def __init__(self, part_item, model_part):
        self._part_item = part_item
        self._model_part = model_part
    # end def

    def connectSignals(self):
        m_p = self._model_part
        p_i = self._part_item

        m_p.partZDimensionsChangedSignal.connect(p_i.partZDimensionsChangedSlot)
        m_p.partParentChangedSignal.connect(p_i.partParentChangedSlot)
        m_p.partRemovedSignal.connect(p_i.partRemovedSlot)
        m_p.partPropertyChangedSignal.connect(p_i.partPropertyChangedSlot)
        m_p.partSelectedChangedSignal.connect(p_i.partSelectedChangedSlot)

        m_p.partActiveVirtualHelixChangedSignal.connect(p_i.partActiveVirtualHelixChangedSlot)
        m_p.partActiveBaseInfoSignal.connect(p_i.partActiveBaseInfoSlot)
        m_p.partActiveChangedSignal.connect(p_i.partActiveChangedSlot)
        m_p.partViewPropertySignal.connect(p_i.partViewPropertySlot)

        m_p.partVirtualHelixAddedSignal.connect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRemovingSignal.connect(p_i.partVirtualHelixRemovingSlot)
        m_p.partVirtualHelixRemovedSignal.connect(p_i.partVirtualHelixRemovedSlot)
        m_p.partVirtualHelixResizedSignal.connect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelicesReorderedSignal.connect(p_i.partVirtualHelicesReorderedSlot)
        m_p.partVirtualHelicesTranslatedSignal.connect(p_i.partVirtualHelicesTranslatedSlot)
        m_p.partVirtualHelicesSelectedSignal.connect(p_i.partVirtualHelicesSelectedSlot)
        m_p.partVirtualHelixPropertyChangedSignal.connect(p_i.partVirtualHelixPropertyChangedSlot)

        m_p.partOligoAddedSignal.connect(p_i.partOligoAddedSlot)
        m_p.partDocumentSettingChangedSignal.connect(p_i.partDocumentSettingChangedSlot)

    # end def

    def disconnectSignals(self):
        m_p = self._model_part
        p_i = self._part_item

        m_p.partZDimensionsChangedSignal.disconnect(p_i.partZDimensionsChangedSlot)
        m_p.partParentChangedSignal.disconnect(p_i.partParentChangedSlot)
        m_p.partRemovedSignal.disconnect(p_i.partRemovedSlot)
        m_p.partPropertyChangedSignal.disconnect(p_i.partPropertyChangedSlot)
        m_p.partSelectedChangedSignal.disconnect(p_i.partSelectedChangedSlot)

        m_p.partActiveVirtualHelixChangedSignal.disconnect(p_i.partActiveVirtualHelixChangedSlot)
        m_p.partActiveBaseInfoSignal.disconnect(p_i.partActiveBaseInfoSlot)
        m_p.partActiveChangedSignal.disconnect(p_i.partActiveChangedSlot)
        m_p.partViewPropertySignal.disconnect(p_i.partViewPropertySlot)

        m_p.partVirtualHelixAddedSignal.disconnect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRemovingSignal.disconnect(p_i.partVirtualHelixRemovingSlot)
        m_p.partVirtualHelixRemovedSignal.disconnect(p_i.partVirtualHelixRemovedSlot)
        m_p.partVirtualHelixResizedSignal.disconnect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelicesReorderedSignal.disconnect(p_i.partVirtualHelicesReorderedSlot)
        m_p.partVirtualHelicesTranslatedSignal.disconnect(p_i.partVirtualHelicesTranslatedSlot)
        m_p.partVirtualHelicesSelectedSignal.disconnect(p_i.partVirtualHelicesSelectedSlot)
        m_p.partVirtualHelixPropertyChangedSignal.disconnect(p_i.partVirtualHelixPropertyChangedSlot)

        m_p.partOligoAddedSignal.disconnect(p_i.partOligoAddedSlot)
        m_p.partDocumentSettingChangedSignal.disconnect(p_i.partDocumentSettingChangedSlot)
    # end def
