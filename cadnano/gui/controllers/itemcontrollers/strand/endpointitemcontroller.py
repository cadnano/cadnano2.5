from .abstractstranditemcontroller import AbstractStrandItemController


class EndpointItemController(AbstractStrandItemController):
    def __init__(self, strandItem, modelOligo, modelStrand):
        super(EndpointItemController, self).__init__(strandItem, modelStrand)
        self.connectSignals()
    # end def