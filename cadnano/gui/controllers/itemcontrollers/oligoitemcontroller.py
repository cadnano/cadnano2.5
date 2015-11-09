class OligoItemController():
    def __init__(self, oligo_item, model_oligo):
        self._oligo_item = oligo_item
        self._model_oligo = model_oligo
        self.connectSignals()
    # end def

    def connectSignals(self):
        m_o = self._model_oligo
        o_i = self._oligo_item
        m_o.oligoAppearanceChangedSignal.connect(o_i.oligoAppearanceChangedSlot)
        m_o.oligoSequenceAddedSignal.connect(o_i.oligoSequenceAddedSlot)
        m_o.oligoSequenceClearedSignal.connect(o_i.oligoSequenceClearedSlot)
        m_o.oligoPropertyChangedSignal.connect(o_i.oligoPropertyChangedSlot)
    # end def

    def disconnectSignals(self):
        m_o = self._model_oligo
        o_i = self._oligo_item
        m_o.oligoAppearanceChangedSignal.disconnect(o_i.oligoAppearanceChangedSlot)
        m_o.oligoSequenceAddedSignal.disconnect(o_i.oligoSequenceAddedSlot)
        m_o.oligoSequenceClearedSignal.disconnect(o_i.oligoSequenceClearedSlot)
        m_o.oligoPropertyChangedSignal.connect(o_i.oligoPropertyChangedSlot)
    # end def
