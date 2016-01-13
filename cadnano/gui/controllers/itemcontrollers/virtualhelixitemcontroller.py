class VirtualHelixItemController(object):
    """ Since there is no model VirtualHelix Object, we need
    a specialized controller for the property view
    """
    def __init__(self, virtualhelix_item, model_part, do_wire_part, do_wire_strands):
        self._virtual_helix_item = virtualhelix_item
        self._model_part = model_part
        self._do_wire_part = do_wire_part
        self._do_wire_strands = do_wire_strands
        self.connectSignals()
    # end def

    def connectSignals(self):
        vh_item = self._virtual_helix_item
        m_p = self._model_part
        if self._do_wire_part:
            m_p.partVirtualHelixPropertyChangedSignal.connect(vh_item.partVirtualHelixPropertyChangedSlot)
            m_p.partVirtualHelixRemovedSignal.connect(vh_item.partVirtualHelixRemovedSlot)
        if self._do_wire_strands:
            for strandset in m_p.virtualHelixGroup().getStrandSets(vh_item.idNum()):
                strandset.strandsetStrandAddedSignal.disconnect(vh_item.strandAddedSlot)
    # end def

    def disconnectSignals(self):
        vh_item = self._virtual_helix_item
        m_p = self._model_part
        if self._do_wire_part:
            m_p.partVirtualHelixPropertyChangedSignal.disconnect(vh_item.partVirtualHelixPropertyChangedSlot)
            m_p.partVirtualHelixRemovedSignal.disconnect(vh_item.partVirtualHelixRemovedSlot)
        if self._do_wire_strands:
            for strandset in m_p.virtualHelixGroup().getStrandSets(vh_item.idNum()):
                strandset.strandsetStrandAddedSignal.disconnect(vh_item.strandAddedSlot)
    # end def
# end class