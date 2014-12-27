class DnaPartItemController():
    def __init__(self, dna_part_item, model_dna_part):
        self._dna_part_item = dna_part_item
        self._model_dna_part = model_dna_part
        self.connectSignals()
    # end def

    def connectSignals(self):
        m_p = self._model_dna_part
        p_i = self._dna_part_item

        if hasattr(p_i, "partHideSlot"):
            m_p.partHideSignal.connect(p_i.partHideSlot)
        if hasattr(p_i, "partActiveVirtualHelixChangedSlot"):
            m_p.partActiveVirtualHelixChangedSignal.connect(p_i.partActiveVirtualHelixChangedSlot)

        m_p.partDimensionsChangedSignal.connect(p_i.partDimensionsChangedSlot)
        m_p.partParentChangedSignal.connect(p_i.partParentChangedSlot)
        m_p.partRemovedSignal.connect(p_i.partRemovedSlot)

        m_p.partPropertyChangedSignal.connect(p_i.partPropertyChangedSlot)
        m_p.partSelectedChangedSignal.connect(p_i.partSelectedChangedSlot)
    # end def

    def disconnectSignals(self):
        m_p = self._model_dna_part
        p_i = self._dna_part_item

        if hasattr(p_i, "partHideSlot"):
            m_p.partHideSignal.disconnect(p_i.partHideSlot)
        if hasattr(p_i, "partActiveVirtualHelixChangedSlot"):
            m_p.partActiveVirtualHelixChangedSignal.disconnect(p_i.partActiveVirtualHelixChangedSlot)

        m_p.partDimensionsChangedSignal.disconnect(p_i.partDimensionsChangedSlot)
        m_p.partParentChangedSignal.disconnect(p_i.partParentChangedSlot)
        m_p.partRemovedSignal.disconnect(p_i.partRemovedSlot)

        m_p.partPropertyChangedSignal.disconnect(p_i.partPropertyChangedSlot)
        m_p.partSelectedChangedSignal.disconnect(p_i.partSelectedChangedSlot)
    # end def
