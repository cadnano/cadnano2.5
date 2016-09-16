class PartItemController():
    def __init__(self, part_item, model_part):
        self._part_item = part_item
        self._model_part = model_part
    # end def

    connections = [
    ('partZDimensionsChangedSignal',        'partZDimensionsChangedSlot'),
    ('partParentChangedSignal',             'partParentChangedSlot'),
    ('partRemovedSignal',                   'partRemovedSlot'),
    ('partPropertyChangedSignal',           'partPropertyChangedSlot'),
    ('partSelectedChangedSignal',           'partSelectedChangedSlot'),

    ('partDocumentSettingChangedSignal',    'partDocumentSettingChangedSlot')
    ]

    def connectSignals(self):
        m_p = self._model_part
        p_i = self._part_item
        for signal, slot in self.connections:
            getattr(m_p, signal).connect(getattr(p_i, slot))
    # end def

    def disconnectSignals(self):
        m_p = self._model_part
        p_i = self._part_item
        for signal, slot in self.connections:
            getattr(m_p, signal).disconnect(getattr(p_i, slot))
    # end def
