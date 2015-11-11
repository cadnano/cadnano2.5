from cadnano.enum import ItemType, PartType
from cadnano.gui.views import styles

from .cnoutlineritem import CNOutlinerItem
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from .oligoitem import OligoItem
from .virtualhelixitem import VirtualHelixItem

class NucleicAcidPartItem(CNOutlinerItem, AbstractPartItem):
    def __init__(self, model_part, parent):
        super(NucleicAcidPartItem, self).__init__(model_part, parent)
        self._controller = NucleicAcidPartItemController(self, model_part)
        self.setExpanded(True)

        # properties
        temp_color = model_part.getColor()
        # outlinerview takes responsibility of overriding default part color
        if temp_color == "#000000":
            index = len(model_part.document().children()) - 1
            new_color = styles.PARTCOLORS[index % len(styles.PARTCOLORS)]
            model_part.setProperty('color', new_color)

        # item groups
        self._root_items = {}
        self._root_items['VHelixList'] = self.createRootItem('VHelix List', self)
        self._root_items['OligoList'] = self.createRootItem('Oligo List', self)
        # self._root_items['Modifications'] = self._createRootItem('Modifications', self)
        self._items = {} # children
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def rootItems(self):
        return self._root_items
    # end def

    def itemType(self):
        return ItemType.NUCLEICACID
    # end def

    ### SLOTS ###
    def partRemovedSlot(self, sender):
        self._cn_model = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partOligoAddedSlot(self, model_part, model_oligo):
        m_o = model_oligo
        m_o.oligoRemovedSignal.connect(self.partOligoRemovedSlot)
        o_i = OligoItem(m_o, self._root_items['OligoList'])
        self._items[id(m_o)] = o_i
    # end def

    def partOligoRemovedSlot(self, model_part, model_oligo):
        m_o = model_oligo
        m_o.oligoRemovedSignal.disconnect(self.partOligoRemovedSlot)
        o_i = self._items[id(m_o)]
        o_i.parent().removeChild(o_i)
        del self._items[id(m_o)]

    # end def

    def partVirtualHelixAddedSlot(self, model_part, model_virtual_helix):
        m_vh = model_virtual_helix
        m_vh.virtualHelixRemovedSignal.connect(self.partVirtualHelixRemovedSlot)
        vh_i = VirtualHelixItem(m_vh, self._root_items['VHelixList'])
        self._items[id(m_vh)] = vh_i

    def partVirtualHelixRemovedSlot(self, model_part, model_virtual_helix):
        m_vh = model_virtual_helix
        vh_i = self._items[id(m_vh)]
        vh_i.parent().removeChild(vh_i)
        del self._items[id(m_vh)]
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._cn_model == model_part:
            self.setValue(property_key, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        self.setSelected(is_selected)
    # end def
# end class
