from cadnano import util

class XoverItemController(object):
    def __init__(self, xover_item, model_strand5p):
        self._xover_item = xover_item
        self._model_strand5p = model_strand5p
        self._model_oligo = model_strand5p.oligo()
        self.connectSignals()
    # end def

    def reconnectOligoSignals(self):
        """
        use this for whenever a strands oligo changes
        """
        self.disconnectSignals()
        self.connectSignals()
    # end def

    def reconnectSignals(self, strand):
        self.disconnectSignals()
        self._model_strand5p = strand
        self.connectSignals()
    # end def

    def connectSignals(self):
        x_i = self._xover_item
        s5p = self._model_strand5p
        m_o = s5p.oligo()
        self._model_oligo = m_o

        s5p.strand5pHasSwappedSignal.connect(x_i.strandSwapSlot)
        s5p.strandHasNewOligoSignal.connect(x_i.strandHasNewOligoSlot)
        s5p.strandXover5pRemovedSignal.connect(x_i.xover5pRemovedSlot)
    # end def

    def disconnectSignals(self):
        x_i = self._xover_item
        s5p = self._model_strand5p
        m_o = self._model_oligo

        s5p.strand5pHasSwappedSignal.disconnect(x_i.strandSwapSlot)
        s5p.strandHasNewOligoSignal.disconnect(x_i.strandHasNewOligoSlot)
        s5p.strandXover5pRemovedSignal.connect(x_i.xover5pRemovedSlot)
    # end def
