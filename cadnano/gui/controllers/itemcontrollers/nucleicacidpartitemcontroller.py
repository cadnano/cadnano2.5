from .partitemcontroller import PartItemController

class NucleicAcidPartItemController(PartItemController):
    def __init__(self, nucleicacid_part_item, model_na_part):
        super(NucleicAcidPartItemController, self).__init__(nucleicacid_part_item, model_na_part)
        self.connectSignals()
    # end def

    def connectSignals(self):
        PartItemController.connectSignals(self)
        # NucleicAcidPart-specific signals go here
        m_p = self._model_part
        p_i = self._part_item

        m_p.partActiveVirtualHelixChangedSignal.connect(p_i.partActiveVirtualHelixChangedSlot)
        m_p.partActiveBaseInfoSignal.connect(p_i.partActiveBaseInfoSlot)
        m_p.partActiveChangedSignal.connect(p_i.partActiveChangedSlot)
        m_p.partViewPropertySignal.connect(p_i.partViewPropertySlot)

        m_p.partVirtualHelixAddedSignal.connect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRemovingSignal.connect(p_i.partVirtualHelixRemovingSlot)
        m_p.partVirtualHelixRemovedSignal.connect(p_i.partVirtualHelixRemovedSlot)
        m_p.partVirtualHelixResizedSignal.connect(p_i.partVirtualHelixResizedSlot)

        m_p.partVirtualHelicesTranslatedSignal.connect(p_i.partVirtualHelicesTranslatedSlot)
        m_p.partVirtualHelicesSelectedSignal.connect(p_i.partVirtualHelicesSelectedSlot)
        m_p.partVirtualHelixPropertyChangedSignal.connect(p_i.partVirtualHelixPropertyChangedSlot)

        m_p.partOligoAddedSignal.connect(p_i.partOligoAddedSlot)
    # end def

    def disconnectSignals(self):
        PartItemController.disconnectSignals(self)
        # NucleicAcidPart-specific signals go here
        m_p = self._model_part
        p_i = self._part_item

        m_p.partActiveVirtualHelixChangedSignal.disconnect(p_i.partActiveVirtualHelixChangedSlot)
        m_p.partActiveBaseInfoSignal.disconnect(p_i.partActiveBaseInfoSlot)
        m_p.partActiveChangedSignal.disconnect(p_i.partActiveChangedSlot)
        m_p.partViewPropertySignal.disconnect(p_i.partViewPropertySlot)

        m_p.partVirtualHelixAddedSignal.disconnect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRemovingSignal.disconnect(p_i.partVirtualHelixRemovingSlot)
        m_p.partVirtualHelixRemovedSignal.disconnect(p_i.partVirtualHelixRemovedSlot)
        m_p.partVirtualHelixResizedSignal.disconnect(p_i.partVirtualHelixResizedSlot)

        m_p.partVirtualHelicesTranslatedSignal.disconnect(p_i.partVirtualHelicesTranslatedSlot)
        m_p.partVirtualHelicesSelectedSignal.disconnect(p_i.partVirtualHelicesSelectedSlot)
        m_p.partVirtualHelixPropertyChangedSignal.disconnect(p_i.partVirtualHelixPropertyChangedSlot)

        m_p.partOligoAddedSignal.disconnect(p_i.partOligoAddedSlot)
    # end def
# end class
