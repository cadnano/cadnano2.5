from .partitemcontroller import PartItemController

class DnaPartItemController(PartItemController):
    def __init__(self, dna_part_item, model_dna_part):
        super(DnaPartItemController, self).__init__(dna_part_item, model_dna_part)
        self.connectSignals()
    # end def

    def connectSignals(self):
        PartItemController.connectSignals(self)
        # DnaPart-specific signals go here
        # m_p = self._model_part
        # p_i = self._part_item
    # end def

    def disconnectSignals(self):
        PartItemController.disconnectSignals(self)
        # DnaPart-specific signals go here
        # m_p = self._model_part
        # p_i = self._part_item
    # end def
