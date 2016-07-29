from cadnano import util
from .abstractstranditemcontroller import AbstractStrandItemController


class StrandItemController(AbstractStrandItemController):
    def __init__(self, strand_item, model_strand):
        super(StrandItemController, self).__init__(strand_item, model_strand)
        self.connectSignals()
    # end def

    def reconnectOligoSignals(self):
        """
        use this for whenever a strands oligo changes
        """
        AbstractStrandItemController.disconnectOligoSignals(self)
        self.disconnectOligoSignals()
        AbstractStrandItemController.connectOligoSignals(self)
        self.connectOligoSignals()
    # end def

    def connectSignals(self):
        AbstractStrandItemController.connectSignals(self)
        m_s = self._model_strand
        s_i = self._strand_item
        m_s.strandResizedSignal.connect(s_i.strandResizedSlot)
        m_s.strandUpdateSignal.connect(s_i.strandUpdateSlot)
        self.connectOligoSignals()
    # end def

    def connectOligoSignals(self):
        m_o = self._model_strand.oligo()
        self._model_oligo = m_o
        s_i = self._strand_item
        m_o.oligoSequenceAddedSignal.connect(s_i.oligoSequenceAddedSlot)
        m_o.oligoSequenceClearedSignal.connect(s_i.oligoSequenceClearedSlot)
    # end def

    def disconnectSignals(self):
        AbstractStrandItemController.disconnectSignals(self)
        m_s = self._model_strand
        s_i = self._strand_item
        m_s.strandResizedSignal.disconnect(s_i.strandResizedSlot)
        m_s.strandUpdateSignal.disconnect(s_i.strandUpdateSlot)
        self.disconnectOligoSignals()
    # end def

    def disconnectOligoSignals(self):
        m_o = self._model_oligo
        s_i = self._strand_item
        m_o.oligoSequenceAddedSignal.disconnect(s_i.oligoSequenceAddedSlot)
        m_o.oligoSequenceClearedSignal.disconnect(s_i.oligoSequenceClearedSlot)
    # end def
