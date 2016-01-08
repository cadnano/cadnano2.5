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
        m_p.partPreDecoratorSelectedSignal.connect(p_i.partPreDecoratorSelectedSlot)
        m_p.partStrandChangedSignal.connect(p_i.updatePreXoverItemsSlot)
        m_p.partVirtualHelixAddedSignal.connect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRemovedSignal.connect(p_i.partVirtualHelixRemovedSlot)
        m_p.partVirtualHelixRenumberedSignal.connect(p_i.partVirtualHelixRenumberedSlot)
        m_p.partVirtualHelixResizedSignal.connect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelixTransformedSignal.connect(p_i.partVirtualHelixTransformedSlot)
        m_p.partVirtualHelicesReorderedSignal.connect(p_i.partVirtualHelicesReorderedSlot)
        m_p.partVirtualHelicesTranslatedSignal.connect(p_i.partVirtualHelicesTranslatedSlot)
    # end def

    def disconnectSignals(self):
        PartItemController.disconnectSignals(self)
        # NucleicAcidPart-specific signals go here
        m_p = self._model_part
        p_i = self._part_item
        m_p.partActiveVirtualHelixChangedSignal.disconnect(p_i.partActiveVirtualHelixChangedSlot)
        m_p.partPreDecoratorSelectedSignal.disconnect(p_i.partPreDecoratorSelectedSlot)
        m_p.partStrandChangedSignal.disconnect(p_i.updatePreXoverItemsSlot)
        m_p.partVirtualHelixAddedSignal.disconnect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRemovedSignal.disconnect(p_i.partVirtualHelixRemovedSlot)
        m_p.partVirtualHelixRenumberedSignal.disconnect(p_i.partVirtualHelixRenumberedSlot)
        m_p.partVirtualHelixResizedSignal.disconnect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelixTransformedSignal.disconnect(p_i.partVirtualHelixTransformedSlot)
        m_p.partVirtualHelicesReorderedSignal.disconnect(p_i.partVirtualHelicesReorderedSlot)
        m_p.partVirtualHelicesTranslatedSignal.disconnect(p_i.partVirtualHelicesTranslatedSlot)
    # end def
# end class
