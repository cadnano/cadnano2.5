from .partitemcontroller import PartItemController

class OrigamiPartItemController(PartItemController):
    def __init__(self, dna_part_item, model_dna_part):
        super(OrigamiPartItemController, self).__init__(dna_part_item, model_dna_part)
        self.connectSignals()
    # end def

    def connectSignals(self):
        PartItemController.connectSignals(self)
        # OrigamiPart-specific signals go here
        m_p = self._model_part
        p_i = self._part_item
        m_p.partActiveVirtualHelixChangedSignal.connect(p_i.partActiveVirtualHelixChangedSlot)
        m_p.partPreDecoratorSelectedSignal.connect(p_i.partPreDecoratorSelectedSlot)
        m_p.partVirtualHelixAddedSignal.connect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRenumberedSignal.connect(p_i.partVirtualHelixRenumberedSlot)
        m_p.partVirtualHelixResizedSignal.connect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelicesReorderedSignal.connect(p_i.partVirtualHelicesReorderedSlot)
    # end def

    def disconnectSignals(self):
        PartItemController.disconnectSignals(self)
        # OrigamiPart-specific signals go here
        m_p = self._model_part
        p_i = self._origami_part_item

        if hasattr(p_i, "partHideSlot"):
            m_p.partHideSignal.disconnect(p_i.partHideSlot)
        if hasattr(p_i, "partActiveVirtualHelixChangedSlot"):
            m_p.partActiveVirtualHelixChangedSignal.disconnect(p_i.partActiveVirtualHelixChangedSlot)

        m_p.partDimensionsChangedSignal.disconnect(p_i.partDimensionsChangedSlot)
        m_p.partParentChangedSignal.disconnect(p_i.partParentChangedSlot)
        m_p.partPreDecoratorSelectedSignal.disconnect(p_i.partPreDecoratorSelectedSlot)
        m_p.partVirtualHelixAddedSignal.disconnect(p_i.partVirtualHelixAddedSlot)
        m_p.partVirtualHelixRenumberedSignal.disconnect(p_i.partVirtualHelixRenumberedSlot)
        m_p.partVirtualHelixResizedSignal.disconnect(p_i.partVirtualHelixResizedSlot)
        m_p.partVirtualHelicesReorderedSignal.disconnect(p_i.partVirtualHelicesReorderedSlot)
    # end def
# end class
