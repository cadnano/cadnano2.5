from .partitemcontroller import PartItemController

class PlasmidPartItemController(PartItemController):
    def __init__(self, plasmid_part_item, model_na_part):
        super(PlasmidPartItemController, self).__init__(plasmid_part_item, model_na_part)
        self.connectSignals()
    # end def

    def connectSignals(self):
        PartItemController.connectSignals(self)
        # PlasmidPart-specific signals go here
        # m_p = self._model_part
        # p_i = self._part_item
    # end def

    def disconnectSignals(self):
        PartItemController.disconnectSignals(self)
        # PlasmidPart-specific signals go here
        # m_p = self._model_part
        # p_i = self._part_item
    # end def
