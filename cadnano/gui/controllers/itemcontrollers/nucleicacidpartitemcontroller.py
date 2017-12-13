from .partitemcontroller import PartItemController


class NucleicAcidPartItemController(PartItemController):
    def __init__(self, nucleicacid_part_item, model_na_part):
        super(NucleicAcidPartItemController, self).__init__(nucleicacid_part_item, model_na_part)
        self.connectSignals()
    # end def

    connections = PartItemController.connections + [
    ('partActiveVirtualHelixChangedSignal',    'partActiveVirtualHelixChangedSlot'),   # noqa
    ('partActiveBaseInfoSignal',               'partActiveBaseInfoSlot'),              # noqa
    ('partActiveChangedSignal',                'partActiveChangedSlot'),               # noqa
    ('partInstancePropertySignal',             'partInstancePropertySlot'),            # noqa

    ('partVirtualHelixAddedSignal',            'partVirtualHelixAddedSlot'),           # noqa
    ('partVirtualHelixRemovingSignal',         'partVirtualHelixRemovingSlot'),        # noqa
    ('partVirtualHelixRemovedSignal',          'partVirtualHelixRemovedSlot'),         # noqa
    ('partVirtualHelixResizedSignal',          'partVirtualHelixResizedSlot'),         # noqa

    ('partVirtualHelicesTranslatedSignal',     'partVirtualHelicesTranslatedSlot'),    # noqa
    ('partVirtualHelicesSelectedSignal',       'partVirtualHelicesSelectedSlot'),      # noqa
    ('partVirtualHelixPropertyChangedSignal',  'partVirtualHelixPropertyChangedSlot'), # noqa

    ('partOligoAddedSignal',                   'partOligoAddedSlot')                   # noqa
    ]
# end class
