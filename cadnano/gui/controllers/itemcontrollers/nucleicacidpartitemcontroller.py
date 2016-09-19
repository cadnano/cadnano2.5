from .partitemcontroller import PartItemController

class NucleicAcidPartItemController(PartItemController):
    def __init__(self, nucleicacid_part_item, model_na_part):
        super(NucleicAcidPartItemController, self).__init__(nucleicacid_part_item, model_na_part)
        self.connectSignals()
    # end def

    connections = PartItemController.connections + [
    ('partActiveVirtualHelixChangedSignal',     'partActiveVirtualHelixChangedSlot'),
    ('partActiveBaseInfoSignal',                'partActiveBaseInfoSlot'),
    ('partActiveChangedSignal',                 'partActiveChangedSlot'),
    ('partInstancePropertySignal',              'partInstancePropertySlot'),

    ('partVirtualHelixAddedSignal',             'partVirtualHelixAddedSlot'),
    ('partVirtualHelixRemovingSignal',          'partVirtualHelixRemovingSlot'),
    ('partVirtualHelixRemovedSignal',           'partVirtualHelixRemovedSlot'),
    ('partVirtualHelixResizedSignal',           'partVirtualHelixResizedSlot'),

    ('partVirtualHelicesTranslatedSignal',      'partVirtualHelicesTranslatedSlot'),
    ('partVirtualHelicesSelectedSignal',        'partVirtualHelicesSelectedSlot'),
    ('partVirtualHelixPropertyChangedSignal',   'partVirtualHelixPropertyChangedSlot'),

    ('partOligoAddedSignal',                    'partOligoAddedSlot')
    ]
# end class
