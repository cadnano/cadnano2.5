class StrandItemController():
    def __init__(self, model_strand, strand_item):
        self._model_strand = model_strand
        self._model_oligo = model_strand.oligo()
        self._strand_item = strand_item
        self.connectSignals()
    # end def

    connections = [
        ('strandHasNewOligoSignal', 'strandHasNewOligoSlot'),
        ('strandRemovedSignal', 'strandRemovedSlot'),
        ('strandResizedSignal', 'strandResizedSlot'),
        # ('strandXover5pRemovedSignal', 'strandXover5pRemovedSlot'),
        ('strandConnectionChangedSignal', 'strandConnectionChangedSlot'),
        ('strandInsertionAddedSignal', 'strandInsertionAddedSlot'),
        ('strandInsertionChangedSignal', 'strandInsertionChangedSlot'),
        ('strandInsertionRemovedSignal', 'strandInsertionRemovedSlot'),
        ('strandModsAddedSignal', 'strandModsAddedSlot'),
        ('strandModsChangedSignal', 'strandModsChangedSlot'),
        ('strandModsRemovedSignal', 'strandModsRemovedSlot'),
        ('strandSelectedChangedSignal', 'strandSelectedChangedSlot'),
    ]

    oligoconnections = [
        ('oligoPropertyChangedSignal', 'oligoPropertyChangedSlot'),
        ('oligoSelectedChangedSignal', 'oligoSelectedChangedSlot'),
        # ('oligoRemovedSignal', 'oligoRemovedSlot'),
        ('oligoSequenceAddedSignal', 'oligoSequenceAddedSlot'),
        ('oligoSequenceClearedSignal', 'oligoSequenceClearedSlot')
    ]

    def connectSignals(self):
        StrandItemController.connectOligoSignals(self)
        m_s = self._model_strand
        s_i = self._strand_item
        for signal, slot in self.connections:
            getattr(m_s, signal).connect(getattr(s_i, slot))
    # end def

    def disconnectSignals(self):
        StrandItemController.disconnectOligoSignals(self)
        m_s = self._model_strand
        s_i = self._strand_item
        for signal, slot in self.connections:
            getattr(m_s, signal).disconnect(getattr(s_i, slot))
    # end def

    def connectOligoSignals(self):
        m_o = self._model_strand.oligo()
        s_i = self._strand_item
        self._model_oligo = m_o
        for signal, slot in self.oligoconnections:
            getattr(m_o, signal).connect(getattr(s_i, slot))
    # end def

    def disconnectOligoSignals(self):
        m_o = self._model_oligo
        s_i = self._strand_item
        for signal, slot in self.oligoconnections:
            getattr(m_o, signal).disconnect(getattr(s_i, slot))
    # end def

    def reconnectOligoSignals(self):
        self.disconnectOligoSignals()
        self.connectOligoSignals()
    # end def
# end class
