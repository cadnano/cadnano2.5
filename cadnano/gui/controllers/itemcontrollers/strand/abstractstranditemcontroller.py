from cadnano import util
# from controllers.itemcontrollers.abstractitemcontroller import AbstractItemController


class AbstractStrandItemController(object):
    def __init__(self, strand_item, model_strand):
        """
        Do not call connectSignals here.  subclasses
        will install two sets of signals.
        """
        if self.__class__ == AbstractStrandItemController:
            e = "AbstractStrandItemController should be subclassed."
            raise NotImplementedError(e)
        self._strand_item = strand_item
        self._model_strand = model_strand
        self._model_oligo = model_strand.oligo()
    # end def

    def reconnectOligoSignals(self):
        self.disconnectOligoSignals()
        self.connectOligoSignals()
    # end def

    def connectSignals(self):
        """Connects modelStrant signals to strandItem slots."""
        m_s = self._model_strand
        s_i = self._strand_item

        AbstractStrandItemController.connectOligoSignals(self)
        m_s.strandHasNewOligoSignal.connect(s_i.strandHasNewOligoSlot)
        m_s.strandRemovedSignal.connect(s_i.strandRemovedSlot)

        m_s.strandInsertionAddedSignal.connect(s_i.strandInsertionAddedSlot)
        m_s.strandInsertionChangedSignal.connect(s_i.strandInsertionChangedSlot)
        m_s.strandInsertionRemovedSignal.connect(s_i.strandInsertionRemovedSlot)
        m_s.strandModsAddedSignal.connect(s_i.strandModsAddedSlot)
        m_s.strandModsChangedSignal.connect(s_i.strandModsChangedSlot)
        m_s.strandModsRemovedSignal.connect(s_i.strandModsRemovedSlot)

        m_s.strandSelectedChangedSignal.connect(s_i.strandSelectedChangedSlot)
    # end def

    def connectOligoSignals(self):
        s_i = self._strand_item
        m_o = self._model_strand.oligo()
        self._model_oligo = m_o
        m_o.oligoPropertyChangedSignal.connect(s_i.oligoPropertyChangedSlot)
    # end def

    def disconnectSignals(self):
        m_s = self._model_strand
        s_i = self._strand_item

        AbstractStrandItemController.disconnectOligoSignals(self)
        m_s.strandHasNewOligoSignal.disconnect(s_i.strandHasNewOligoSlot)
        m_s.strandRemovedSignal.disconnect(s_i.strandRemovedSlot)

        m_s.strandInsertionAddedSignal.disconnect(s_i.strandInsertionAddedSlot)
        m_s.strandInsertionChangedSignal.disconnect(s_i.strandInsertionChangedSlot)
        m_s.strandInsertionRemovedSignal.disconnect(s_i.strandInsertionRemovedSlot)
        m_s.strandModsAddedSignal.disconnect(s_i.strandModsAddedSlot)
        m_s.strandModsChangedSignal.disconnect(s_i.strandModsChangedSlot)
        m_s.strandModsRemovedSignal.disconnect(s_i.strandModsRemovedSlot)

        m_s.strandSelectedChangedSignal.disconnect(s_i.strandSelectedChangedSlot)
    # end def

    def disconnectOligoSignals(self):
        s_i = self._strand_item
        m_o = self._model_oligo
        m_o.oligoPropertyChangedSignal.disconnect(s_i.oligoPropertyChangedSlot)
    # end def
