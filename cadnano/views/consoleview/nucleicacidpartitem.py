from cadnano.proxies.cnenum import ItemType
from cadnano.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from cadnano.views.abstractitems.abstractpartitem import AbstractPartItem
#from cadnano.views.abstractitems.abstractpartitem import QAbstractPartItem


#class ConsoleNucleicAcidPartItem(QAbstractPartItem):
class ConsoleNucleicAcidPartItem(AbstractPartItem):
    FILTER_NAME = 'part'

    def __init__(self, model_part, viewroot, parent):
        super(ConsoleNucleicAcidPartItem, self).__init__()
#        super(ConsoleNucleicAcidPartItem, self).__init__(model_part, viewroot, parent)
        self._controller = NucleicAcidPartItemController(self, model_part)
        self._model_part = model_part
        self._parent = parent

        self._virtual_helix_item_hash = dict()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def __repr__(self):
        _id = str(id(self))[-4:]
        _name  = self.__class__.__name__
        try:
            return '%s_%s_%s' % (_name, self._model_part.getProperty('name'), _id)
        except AttributeError:
            return '%s_%s_%s' % (_name, '', _id)

    ### PUBLIC SUPPORT METHODS ###
    def log(self, message):
        self._parent.log(message)

    def part(self):
        return self._model_part
    # end def

    def itemType(self):
        return ItemType.NUCLEICACID
    # end def

    def isModelSelected(self, document):
        '''Make sure the item is selected in the model
        TODO implement Part selection

        Args:
            document (Document): reference the the model :class:`Document`
        '''
        return False
    # end def

    ### SLOTS ###
    def partRemovedSlot(self, sender):
        self.log('%s removed' % self._model_part)
        self._controller.disconnectSignals()
        self._model_part = None
        self._controller = None
    # end def

    def partOligoAddedSlot(self, model_part, model_oligo):
        model_oligo.oligoRemovedSignal.connect(self.partOligoRemovedSlot)
        self.log('%s added' % model_oligo)
    # end def

    def partOligoRemovedSlot(self, model_part, model_oligo):
        self.log('%s removed' % model_oligo)
    # end def

    def partVirtualHelixAddedSlot(self, model_part, id_num, virtual_helix, neighbors):
        self._virtual_helix_item_hash[id_num] = virtual_helix
        self.log('%s added' % virtual_helix)
    # end def

    def partVirtualHelixRemovingSlot(self, model_part, id_num, virtual_helix, neigbors):
        print(type(virtual_helix))
        self.log('%s removed' % virtual_helix)

        if self._virtual_helix_item_hash.get(id_num) is not None:
            del self._virtual_helix_item_hash[id_num]
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            print('partPropertyChanged', model_part, property_key, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        self.log('%s selected' % model_part) if is_selected else self.log('%s is deselected' % model_part)
    # end def

    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, virtual_helix, keys, values):
        print(self._model_part)
        print(sender)
        if self._model_part == sender:
            vh_i = self._virtual_helix_item_hash[id_num]
            for key, val in zip(keys, values):
                self.log('%s changed %s-%s' % (vh_i, key, val))
#                if key in CNConsoleItem.PROPERTIES:
#                    vh_i.setValue(key, val)
    # end def

    def partVirtualHelicesSelectedSlot(self, sender, vh_set, is_adding):
        self.log('Selected %s' % str(vh_set) if is_adding else 'Deselected %s' % str(vh_set))
    # end def

    def partActiveVirtualHelixChangedSlot(self, part, id_num):
        vhi = self._virtual_helix_item_hash.get(id_num)
#        self.setActiveVirtualHelixItem(vhi)
    # end def

    def partActiveChangedSlot(self, part, is_active):
        pass
        # if part == self._model_part:
        #     self.activate() if is_active else self.deactivate()
    # end def

    def setActiveVirtualHelixItem(self, new_active_vhi):
        current_vhi = self.active_virtual_helix_item
        if new_active_vhi != current_vhi:
            if current_vhi is not None:
                current_vhi.deactivate()
            if new_active_vhi is not None:
                new_active_vhi.activate()
            self.active_virtual_helix_item = new_active_vhi
    # end def
# end class
