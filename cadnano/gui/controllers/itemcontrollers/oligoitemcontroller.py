class OligoItemController():
    def __init__(self, oligo_item, model_oligo):
        self._oligo_item = oligo_item
        self._model_oligo = model_oligo
        self.connectSignals()
    # end def

    connections = [
    ('oligoSequenceAddedSignal',    'oligoSequenceAddedSlot'),
    ('oligoSequenceClearedSignal',  'oligoSequenceClearedSlot'),
    ('oligoPropertyChangedSignal',  'oligoPropertyChangedSlot')
    ]

    def connectSignals(self):
        m_o = self._model_oligo
        o_i = self._oligo_item
        for signal, slot in self.connections:
            getattr(m_o, signal).connect(getattr(o_i, slot))
    # end def

    def disconnectSignals(self):
        m_o = self._model_oligo
        o_i = self._oligo_item
        for signal, slot in self.connections:
            getattr(m_o, signal).disconnect(getattr(o_i, slot))
    # end def
