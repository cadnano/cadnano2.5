class DnaPartItemController():
    def __init__(self, dna_part_item, model_dna_part):
        self._dna_part_item = dna_part_item
        self._model_dna_part = model_dna_part
        self.connectSignals()
    # end def

    def connectSignals(self):
        dna_item = self._dna_part_item
        model_dna = self._model_dna_part

        model_dna.partRemovedSignal.connect(dna_item.partRemovedSlot)
    # end def

    def disconnectSignals(self):
        dna_item = self._dna_part_item
        model_dna = self._model_dna_part

        model_dna.partRemovedSignal.disconnect(dna_item.partRemovedSlot)
    # end def
