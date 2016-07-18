# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import count
from uuid import uuid4

from cadnano import util
from cadnano import preferences as prefs
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.cnproxy import UndoCommand
from cadnano.enum import StrandType

from cadnano.part.virtualhelixgroup import VirtualHelixGroup, Z_PROP_INDEX

class Part(VirtualHelixGroup):
    """
    A Part is a group of VirtualHelix items that are on the same lattice.
    Parts are the model component that most directly corresponds to a
    DNA origami design.

    Parts are always parented to the document.
    Parts know about their oligos, and the internal geometry of a part
    Copying a part recursively copies all elements in a part:
        VirtualHelices, Strands, etc

    PartInstances are parented to either the document or an assembly
    PartInstances know global position of the part
    Copying a PartInstance only creates a new PartInstance with the same
    Part(), with a mutable parent and position field.
    """
    editable_properties = ['name', 'color', 'grid_type']
    _STEP_SIZE = 21  # this is the period (in bases) of the part lattice
    _RADIUS = 1.125  # nanometers
    _TURNS_PER_STEP = 2
    _HELICAL_PITCH = _STEP_SIZE / _TURNS_PER_STEP
    _TWIST_PER_BASE = 360 / _HELICAL_PITCH  # degrees
    _BASE_WIDTH = 0.34 # nanometers, distance between bases, pith

    def __init__(self, *args, **kwargs):
        """
        Sets the parent document, sets bounds for part dimensions, and sets up
        bookkeeping for partInstances, Oligos, VirtualHelix's, and helix ID
        number assignment.
        """
        super(Part, self).__init__(*args, **kwargs)
        self._instance_count = 0
        # Data structure
        self._insertions = defaultdict(dict)  # dict of insertions per virtualhelix
        self._mods = {  'int_instances':{},
                        'ext_instances':{}}
        self._oligos = set()
        # Properties
        self.view_properties = {}

        self._group_properties = {  'name':         "Part%d" % len(self._document.children()),
                                    'color':        "#000000", # outlinerview will override from styles
                                    'is_visible':   True
                                }

        self.uuid = kwargs['uuid'] if 'uuid' in kwargs else uuid4().hex

        # Selections
        self._selections = {}

        # Runtime state
        self._active_base_index = self._STEP_SIZE
        self._active_id_num = None
        self.active_base_info = ()
        self._selected = False
        self.is_active = False

        self._abstract_segment_id = None
        self._current_base_count = None

        if self.__class__ == Part:
            e = "This class is abstract. Perhaps you want HoneycombPart."
            raise NotImplementedError(e)
    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<%s %s>" % (cls_name, str(id(self))[-4:])

    ### SIGNALS ###
    # A. Part
    partDimensionsChangedSignal = ProxySignal(CNObject, int, int, bool, # self, id_min, id_max, zoom to fit
                        name='partDimensionsChangedSignal')     # self
    partInstanceAddedSignal = ProxySignal(CNObject,
                        name='partInstanceAddedSignal')         # self
    partParentChangedSignal = ProxySignal(CNObject,
                        name='partParentChangedSignal')         # self
    partRemovedSignal = ProxySignal(CNObject,
                        name='partRemovedSignal')               # self
    partPropertyChangedSignal = ProxySignal(CNObject, object, object,
                        name='partPropertyChangedSignal')       # self, property_name, new_value
    partSelectedChangedSignal = ProxySignal(CNObject, object,
                        name='partSelectedChangedSignal')       # self, is_selected
    partActiveChangedSignal = ProxySignal(CNObject, bool,       # self, is_active
                        name='partActiveChangedSignal')
    partViewPropertySignal = ProxySignal(CNObject, str, str, object,    # self, view, key, val
                                name='partViewPropertySignal')

    # B. Virtual Helix
    partActiveVirtualHelixChangedSignal = ProxySignal(CNObject, int,   # id_num
                        name='partActiveVirtualHelixChangedSignal')
    partActiveBaseInfoSignal = ProxySignal(CNObject, object,   # self.active_base_info (tuple or None)
                        name='partActiveBaseInfoSignal')
    partVirtualHelixAddedSignal = ProxySignal(object, int, object,
                        name='partVirtualHelixAddedSignal')     # self, virtual_helix id_num, neighbor list
    partVirtualHelixRemovedSignal = ProxySignal(object, int, object,
                        name='partVirtualHelixRemovedSignal')     # self, virtual_helix id_num, neighbor list
    partVirtualHelixResizedSignal = ProxySignal(CNObject, int,
                        name='partVirtualHelixResizedSignal')   # self, virtual_helix id_num
    partVirtualHelicesReorderedSignal = ProxySignal(object, object, bool,
                        name='partVirtualHelicesReorderedSignal') # self, list of id_nums

    partVirtualHelicesTranslatedSignal = ProxySignal(CNObject, object, object, bool,
                        name='partVirtualHelicesTranslatedSignal')  # self, list of id_nums, transform
    partVirtualHelicesSelectedSignal = ProxySignal(CNObject, object, bool,
                        name='partVirtualHelicesSelectedSignal')  # self, iterable of id_nums to select, transform
    partVirtualHelixPropertyChangedSignal = ProxySignal(CNObject, int, object, object,
                                            name='partVirtualHelixPropertyChangedSignal')  # self, id_num, value

    # C. Oligo
    partOligoAddedSignal = ProxySignal(CNObject, object,
                        name='partOligoAddedSignal')            # self, oligo
    # D. Strand
    partStrandChangedSignal = ProxySignal(object, int,
                        name='partStrandChangedSignal')         # self, virtual_helix

    # E.
    partDocumentSettingChangedSignal = ProxySignal(object, str, object, # self, key, value
                                    name='partDocumentSettingChangedSignal')

    ### SLOTS ###

    ### ACCESSORS ###
    def document(self):
        return self._document
    # end def

    def setDocument(self, document):
        self._document = document
    # end def

    def incrementInstance(self, document):
        self._instance_count += 1
        if self._instance_count == 1:
            self._document = document
            document.addChild(self)
    # end def

    def decrementInstance(self):
        ic = self._instance_count
        if ic == 0:
            raise IndexError("Can't have less than zero instance of a Part")
        ic -= 1
        if ic == 0:
            self._document = None
            self._document.removeChild(self)
        self._instance_count = ic
    # end def

    def getProperty(self, key):
        return self._group_properties[key]
    # end def

    def getOutlineProperties(self):
        props = self._group_properties
        return props['name'], props['color'], props['is_visible']
    # end def

    def getColor(self):
        return self._group_properties['color']

    def setViewProperty(self, key, value):
        self.view_properties[key] = value
    # end def

    def getViewProperty(self, key):
        return self.view_properties[key]
    # end def

    def getName(self):
        return self._group_properties['name']
    # end def

    def getPropertyDict(self):
        return self._group_properties
    # end def

    def setProperty(self, key, value):
        # use ModifyPropertyCommand here
        self._group_properties[key] = value
        self.partPropertyChangedSignal.emit(self, key, value)
    # end def

    def getSelectionDict(self):
        return self._selections
    # end def

    def oligos(self):
        return self._oligos
    # end def

    def stepSize(self):
        return self._STEP_SIZE
    # end def

    def baseWidth(self):
        return self._BASE_WIDTH
    # end def

    def radius(self):
        return self._RADIUS
    # end def

    def helicalPitch(self):
        return self._HELICAL_PITCH
    # end def

    def twistPerBase(self):
        return self._TWIST_PER_BASE
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
    # end def

    def getNewAbstractSegmentId(self, segment):
        low_idx, high_idx = segment
        seg_id = next(self._abstract_segment_id)
        offset = self._current_base_count
        segment_length = (high_idx - low_idx + 1)
        self._current_base_count = offset + segment_length
        return seg_id, offset, segment_length
    # end def

    def initializeAbstractSegmentId(self):
        self._abstract_segment_id = count(0)
        self._current_base_count = 0
    # end def

    def setAbstractSequences(self):
        """Reset, assign, and display abstract sequence numbers."""
        # reset all sequence numbers
        print("setting abstract sequence")
        for oligo in self._oligos:
            oligo.clearAbstractSequences()

        self.initializeAbstractSegmentId()

        for oligo in self._oligos:
            oligo.applyAbstractSequences()

        # display new sequence numbers
        for oligo in self._oligos:
            oligo.displayAbstractSequences()
            oligo.oligoSequenceAddedSignal.emit(oligo)
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def activeIdNum(self):
        return self._active_id_num
    # end def

    def setActive(self, is_active):
        dc = self._document._controller
        current_active_part = dc.activePart()
        if is_active:
            if current_active_part == self:
                return
            dc.setActivePart(self)
            if current_active_part is not None:
                current_active_part.setActive(False)
        elif current_active_part == self:   # there always needs to be an active
                return
        self.is_active = is_active
        self.partActiveChangedSignal.emit(self, is_active)
    # end def

    def activeBaseIndex(self):
        return self._active_base_index
    # end def

    def clearActiveVirtualHelix(self):
        self.active_base_info = active_base_info = ()
        self._active_id_num = id_num = -1
        self.partActiveVirtualHelixChangedSignal.emit(self, id_num)
        self.partActiveBaseInfoSignal.emit(self, active_base_info)
    # end def

    def setActiveVirtualHelix(self, id_num, is_fwd, idx=None):
        abi = (id_num, is_fwd, idx, -1)
        if self.active_base_info == abi:
            return
        else:
            self._active_id_num = id_num
            self.active_base_info  = abi
        self.partActiveVirtualHelixChangedSignal.emit(self, id_num)
        self.partActiveBaseInfoSignal.emit(self, abi)
    # end def

    def setActiveBaseInfo(self, info):
        """ to_vh_num is not use as of now and may change
        Args:
            info (Tuple): id_num, is_fwd, idx, to_vh_num

        """
        if info != self.active_base_info:
            # keep the info the same but let views know it's not fresh
            if info is not None:
                self.active_base_info = info
            self.partActiveBaseInfoSignal.emit(self, info)
    # end def

    def isVirtualHelixActive(self, id_num):
        return id_num == self._active_id_num
    # end def

    def insertions(self):
        """Return dictionary of insertions."""
        return self._insertions
    # end def

    def dumpInsertions(self):
        for id_num, id_dict in self._insertions.items():
            for idx, insertion in id_dict.items():
                yield (id_num, idx, insertion.length())
    # end def

    def isSelected(self):
        return self.is_selected
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def setSelected(self, is_selected):
        if is_selected != self._selected:
            self._selected = is_selected
            self.partSelectedChangedSignal.emit(self, is_selected)
    # end def

    def getModID(self, strand, idx):
        id_num = strand.idNum()
        strandtype = strand.strandType()
        key =  "{},{},{}".format(id_num, strandtype, idx)
        mods_strand  = self._mods['ext_instances']
        if key in mods_strand:
            return mods_strand[key]
    # end def

    def getStrandModSequence(self, strand, idx, mod_type):
        """
        Args:
            strand (Strand):
            idx (int):
            mod_type (int): 0, 1, or 2
        """
        mid = self.getModID(strand, idx)
        return self._document.getModSequence(mid, mod_type)

    def getModKeyTokens(self, key):
        keylist = key.split(',')
        id_num = int(keylist[0])
        is_fwd = int(keylist[1])    # enumeration of StrandType.FWD or StrandType.REV
        idx = int(keylist[2])
        return id_num, is_fwd, idx
    # end def

    def getModStrandIdx(self, key):
        """ Convert a key of a mod instance relative to a part
        to a strand and an index
        """
        keylist = key.split(',')
        id_num = int(keylist[0])
        is_fwd = int(keylist[1])    # enumeration of StrandType.FWD or StrandType.REV
        idx = int(keylist[2])
        strand = self.getStrand(is_fwd, id_num, idx)
        return strand, idx
    # end def

    def addModInstance(self, id_num, idx, is_rev, is_internal, mid):
        key =  "{},{},{}".format(id_num, is_rev, idx)
        mods_strands = self._mods['int_instances'] if is_internal else self._mods['ext_instances']
        if key in mods_strands:
            self.removeModInstance(id_num, idx, is_rev, is_internal, mid)
        self._document.addModInstance(mid, is_internal, self, key)
        self.addModInstanceKey(key, mods_strands, mid)
    # end def

    def addModInstanceKey(self, key, mods_strands, mid):
        mods_strands[key] = mid # add to strand lookup
    # end def

    def addModStrandInstance(self, strand, idx, mid, is_internal=False):
        id_num = strand.idNum()
        strandtype = strand.strandType()
        if mid is not None:
            self.addModInstance(id_num, idx, strandtype, False, mid)
    # end def

    def removeModInstance(self, id_num, idx, is_rev, is_internal, mid):
        key =  "{},{},{}".format(id_num, is_rev, idx)
        mods_strands = self._mods['int_instances'] if is_internal else self._mods['ext_instances']
        self._document.removeModInstance(mid, is_internal, self, key)
        if key in mods_strands:
            del mods_strands[key]
    # end def

    def removeModStrandInstance(self, strand, idx, mid, is_internal=False):
        id_num = strand.idNum()
        strandtype = strand.strandType()
        if mid is not None:
            self.removeModInstance(id_num, idx, strandtype, is_internal, mid)
    # end def

    def dumpModInstances(self, is_internal):
        mods = self._mods['int_instances'] if is_internal else self._mods['ext_instances']
        for key, mid in mods:
            id_num, is_fwd, idx = self.getModKeyTokens(key)
            yield (id_num, is_fwd, idx, mid)
    # end def

    # def changeModInstance(self, id_num, idx, is_rev, is_internal, mid_old, mid_new):
    #     if mid_new != mid_old:
    #         mods = self._mods
    #         if mid_old in mods and mid_new in mods:
    #             self.removeModInstance(id_num, idx, is_rev, is_internal, mid_old)
    #             self.addModInstance(id_num, idx, is_rev, is_internal, mid_new)
    # # end def

    # def changeModLocation(self, id_num, idx_old, idx, is_rev, is_internal, mid):
    #     if idx_old != idx:
    #         self.removeModInstance(id_num, idx_old, is_rev, is_internal, mid)
    #         self.addModInstance(id_num, idx, is_rev, is_internal, mid)
    # # end def

    # def changeModStrandLocation(self, strand, idxs_old, idxs):
    #     """ Only supports external modifications (3' or 5' end for now)
    #     """
    #     id_num = strand.idNum()
    #     is_rev = strand.isReverse()
    #     mods_strands = self._mods['ext_instances']
    #     document = self._document
    #     is_internal = False
    #     for i in [0, 1]:
    #         idx_old = idxs_old[i]
    #         idx = idxs[i]
    #         if idx_old != idx:
    #             key_old =  "{},{},{}".format(id_num, is_rev, idx_old)
    #             if key_old in mods_strands:
    #                 mid = mods_strands[key_old]
    #                 document.removeModInstance(mid, is_internal, self, key_old)
    #                 del mods_strands[key_old]
    #                 key =  "{},{},{}".format(id_num, is_rev, idx)
    #                 self.addModInstanceKey(key, mods_strands, mid)
    #     # end for
    # # end def
# end class
