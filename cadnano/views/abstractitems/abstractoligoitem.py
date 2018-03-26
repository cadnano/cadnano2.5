# -*- coding: utf-8 -*-
class AbstractOligoItem(object):
    """
    AbstractOligoItem is a base class for oligoitems in all views.
    It includes slots that get connected in OligoController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def oligo(self):
        return self._model_oligo
    # end def

    def setProperty(self, key: str, value):
        self._model_oligo.setProperty(key, value)
    # end def

    def getModelProperties(self) -> dict:
        """ Get the dictionary of model properties

        Returns:
            group properties
        """
        return self._model_oligo.getModelProperties()
    # end def

    def getProperty(self, key: str):
        self._model_oligo.getProperty(key)
    # end def

    def oligoSequenceAddedSlot(self, oligo):
        pass

    def oligoSequenceClearedSlot(self, oligo):
        pass

    def oligoPropertyChangedSlot(self, property_key, new_value):
        pass

    def oligoSelectedChangedSlot(self, oligo, new_value):
        pass
# end class
