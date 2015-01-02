class PartItemController():
    def __init__(self, part_item, model_part):
        self._part_item = part_item
        self._model_part = model_part
    # end def

    def connectSignals(self):
        m_p = self._model_part
        p_i = self._part_item

        m_p.partDimensionsChangedSignal.connect(p_i.partDimensionsChangedSlot)
        m_p.partOligoAddedSignal.connect(p_i.partOligoAddedSlot)
        m_p.partParentChangedSignal.connect(p_i.partParentChangedSlot)
        m_p.partPropertyChangedSignal.connect(p_i.partPropertyChangedSlot)
        m_p.partRemovedSignal.connect(p_i.partRemovedSlot)
        m_p.partSelectedChangedSignal.connect(p_i.partSelectedChangedSlot)
    # end def

    def disconnectSignals(self):
        m_p = self._model_part
        p_i = self._part_item

        m_p.partDimensionsChangedSignal.disconnect(p_i.partDimensionsChangedSlot)
        m_p.partOligoAddedSignal.disconnect(p_i.partOligoAddedSlot)
        m_p.partParentChangedSignal.disconnect(p_i.partParentChangedSlot)
        m_p.partPropertyChangedSignal.disconnect(p_i.partPropertyChangedSlot)
        m_p.partRemovedSignal.disconnect(p_i.partRemovedSlot)
        m_p.partSelectedChangedSignal.disconnect(p_i.partSelectedChangedSlot)
    # end def
