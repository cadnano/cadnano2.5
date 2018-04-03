# -*- coding: utf-8 -*-
from cadnano.cntypes import (
    OligoT,
    ValueT
)

class AbstractOligoItem(object):
    """
    AbstractOligoItem is a base class for oligoitems in all views.
    It includes slots that get connected in OligoController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def oligo(self) -> OligoT:
        return self._model_oligo
    # end def

    def setProperty(self, key: str, value: ValueT):
        self._model_oligo.setProperty(key, value)
    # end def

    def getModelProperties(self) -> dict:
        """ Get the dictionary of model properties

        Returns:
            group properties
        """
        return self._model_oligo.getModelProperties()
    # end def

    def getProperty(self, key: str) -> ValueT:
        return self._model_oligo.getProperty(key)
    # end def

    def oligoSequenceAddedSlot(self, oligo: OligoT):
        pass

    def oligoSequenceClearedSlot(self, oligo: OligoT):
        pass

    def oligoPropertyChangedSlot(self, key: str, new_value):
        pass

    def oligoSelectedChangedSlot(self, oligo: OligoT, new_value):
        pass
# end class
