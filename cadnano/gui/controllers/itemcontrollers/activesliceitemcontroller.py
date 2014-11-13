class ActiveSliceItemController(object):
    def __init__(self, active_slice_item, model_part):
        self._active_slice_item = active_slice_item
        self._model_part = model_part
        self.connectSignals()

    def connectSignals(self):
        a_s_i = self._active_slice_item
        m_p = self._model_part

        m_p.partActiveSliceResizeSignal.connect(a_s_i.updateRectSlot)
        m_p.partActiveSliceIndexSignal.connect(a_s_i.updateIndexSlot)
        m_p.partStrandChangedSignal.connect(a_s_i.strandChangedSlot)
    # end def

    def disconnectSignals(self):
        a_s_i = self._active_slice_item
        m_p = self._model_part

        m_p.partActiveSliceResizeSignal.disconnect(a_s_i.updateRectSlot)
        m_p.partActiveSliceIndexSignal.disconnect(a_s_i.updateIndexSlot)
        m_p.partStrandChangedSignal.disconnect(a_s_i.strandChangedSlot)
    # end def
# end class