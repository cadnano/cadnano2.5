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

    # end def

    def disconnectSignals(self):
        PartItemController.disconnectSignals(self)
        # NucleicAcidPart-specific signals go here
        m_p = self._model_part
        p_i = self._part_item
    # end def
# end class
