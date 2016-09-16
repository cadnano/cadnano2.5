class VirtualHelixItemController(object):
    """ Since there is no model VirtualHelix Object, we need
    a specialized controller for the property view
    """
    def __init__(self, virtualhelix_item, model_part, do_wire_part, do_wire_strands):
        """
        Args:
            virtualhelix_item (AbstractVirtualHelixItem):
            model_part (NucleicAcidPart):
            do_wire_part (bool):    Signals used in property view
            do_wire_strands:        Signals used in path view
        """
        self._virtual_helix_item = virtualhelix_item
        self._model_part = model_part
        self._do_wire_part = do_wire_part
        self._do_wire_strands = do_wire_strands
        self.connectSignals()
    # end def

    part_connections = [
    ('partVirtualHelixPropertyChangedSignal',   'partVirtualHelixPropertyChangedSlot'),
    ('partVirtualHelixRemovedSignal',           'partVirtualHelixRemovedSlot'),
    ('partVirtualHelixResizedSignal',           'partVirtualHelixResizedSlot')
    ]

    strand_connections = [
        ('strandsetStrandAddedSignal', 'strandAddedSlot')
    ]

    def connectSignals(self):
        vh_item = self._virtual_helix_item
        m_p = self._model_part
        if self._do_wire_part:
            for signal, slot in self.part_connections:
                getattr(m_p, signal).connect(getattr(vh_item, slot))
        if self._do_wire_strands:
            for strandset in m_p.getStrandSets(vh_item.idNum()):
                for signal, slot in self.strand_connections:
                    getattr(strandset, signal).connect(getattr(vh_item, slot))
    # end def

    def disconnectSignals(self):
        vh_item = self._virtual_helix_item
        m_p = self._model_part
        if self._do_wire_part:
            for signal, slot in self.part_connections:
                getattr(m_p, signal).disconnect(getattr(vh_item, slot))
        if self._do_wire_strands:
            for strandset in m_p.getStrandSets(vh_item.idNum()):
                for signal, slot in self.strand_connections:
                    getattr(strandset, signal).disconnect(getattr(vh_item, slot))
    # end def
# end class
