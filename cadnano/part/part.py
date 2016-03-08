import random
from collections import defaultdict
from heapq import heapify, heappush, heappop
from itertools import product, islice
from uuid import uuid4
izip = zip

from cadnano import util
from cadnano import preferences as prefs
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.cnproxy import UndoCommand
from cadnano.enum import StrandType
from cadnano.virtualhelix.virtualhelixgroup import VirtualHelixGroup

from .pmodscmd import AddModCommand, RemoveModCommand, ModifyModCommand

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
    editable_properties = ['name', 'color']
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
        self._mods = defaultdict(dict)
        self._oligos = set()
        # Properties
        self.view_properties = {} #self._document.newViewProperties()

        self._group_properties["name"] = "Part%d" % len(self._document.children())
        self._group_properties["color"] = "#000000" # outlinerview will override from styles
        self._group_properties["visible"] = True

        # Selections
        self._selections = {}

        # Runtime state
        self._active_base_index = self._STEP_SIZE
        self._active_id_num = None
        self.active_base_info = None
        self._selected = False

        if self.__class__ == Part:
            e = "This class is abstract. Perhaps you want HoneycombPart."
            raise NotImplementedError(e)
    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<%s %s>" % (cls_name, str(id(self))[-4:])

    ### SIGNALS ###
    # A. Part
    partActiveSliceIndexSignal = ProxySignal(CNObject, int,
                        name='partActiveSliceIndexSignal')      #(self, index)
    partActiveSliceResizeSignal = ProxySignal(CNObject,
                        name='partActiveSliceResizeSignal')     # self
    partDimensionsChangedSignal = ProxySignal(CNObject,
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

    # B. Virtual Helix
    partActiveVirtualHelixChangedSignal = ProxySignal(CNObject, int,   # id_num
                        name='partActiveVirtualHelixChangedSignal')
    partActiveBaseInfoSignal = ProxySignal(CNObject, object,   # self.active_base_info (tuple or None)
                        name='partActiveBaseInfoSignal')
    partVirtualHelixAddedSignal = ProxySignal(object, int,
                        name='partVirtualHelixAddedSignal')     # self, virtual_helix id_num
    partVirtualHelixRemovedSignal = ProxySignal(object, int,
                        name='partVirtualHelixRemovedSignal')     # self, virtual_helix id_num
    partVirtualHelixRenumberedSignal = ProxySignal(CNObject, int,
                        name='partVirtualHelixRenumberedSignal')# self, virtual_helix id_num
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
    # E. Mod
    partModAddedSignal = ProxySignal(object, object, object,
                        name='partModAddedSignal')
    partModRemovedSignal = ProxySignal(object, object,
                        name='partModRemovedSignal')
    partModChangedSignal = ProxySignal(object, object, object,
                        name='partModChangedSignal')

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

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def getImportVirtualHelixOrder(self):
        """ the order of VirtualHelix items in the path view
        each element is the coord of the virtual helix
        """
        return self.getViewProperty('path', 'virtual_helix_order')
    # end def

    def activeIdNum(self):
        return self._active_id_num
     # end def

    def activeBaseIndex(self):
        return self._active_base_index
    # end def

    def setActiveBaseIndex(self, idx):
        self._active_base_index = idx
        self.partActiveSliceIndexSignal.emit(self, idx)
    # end def

    def setActiveVirtualHelix(self, id_num, is_fwd, idx=None):
        self._active_id_num = id_num
        self.active_base_info = abi = (id_num, is_fwd, idx, -1)
        self.partActiveVirtualHelixChangedSignal.emit(self, id_num)
        self.partActiveBaseInfoSignal.emit(self, abi)
    # end def

    def setActiveBaseInfo(self, info):
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

    def isSelected(self):
        return self.is_selected
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def setSelected(self, is_selected):
        self._selected = is_selected
        self.partSelectedChangedSignal.emit(self, is_selected)
    # end def

    def createMod(self, params, mid=None, use_undostack=True):
        if mid is None:
            mid =  str(uuid4())
        elif mid in self._mods:
            raise KeyError("createMod: Duplicate mod id: {}".format(mid))

        name = params.get('name', mid)
        color = params.get('color', '#00FF00')
        seq5p = params.get('seq5p', '')
        seq3p = params.get('seq3p', '')
        seqInt = params.get('seqInt', '')
        note = params.get('note', '')

        cmdparams = {
            'name': name,
            'color': color,
            'note': note,
            'seq5p': seq5p,
            'seq3p': seq3p,
            'seqInt': seqInt,
            'ext_locations': set(), # external mods, mod belongs to idx outside of strand
            'int_locations': set()  # internal mods, mod belongs between idx and idx + 1
        }

        item = { 'name': name,
            'color': color,
            'note': note,
            'seq5p': seq5p,
            'seq3p': seq3p,
            'seqInt': seqInt
        }
        cmds = []
        c = AddModCommand(self, cmdparams, mid)
        cmds.append(c)
        util.execCommandList(self, cmds, desc="Create Mod", \
                                                use_undostack=use_undostack)
        return item, mid
    # end def

    def modifyMod(self, params, mid, use_undostack=True):
        if mid in self._mods:
            cmds = []
            c = ModifyModCommand(self, params, mid)
            cmds.append(c)
            util.execCommandList(self, cmds, desc="Modify Mod", \
                                                use_undostack=use_undostack)
    # end def

    def destroyMod(self, mid):
        if mid in self._mods:
            cmds = []
            c = RemoveModCommand(self, mid)
            cmds.append(c)
            util.execCommandList(self, cmds, desc="Remove Mod", \
                                                use_undostack=use_undostack)
    # end def

    def getMod(self, mid):
        return self._mods.get(mid)
    # end def

    def mods(self):
        """
        """
        mods = self._mods
        res = {}
        for mid in mods.keys():
            if mid != 'int_instances' and mid != 'ext_instances':
                res[mid] = mods[mid].copy()
                del res[mid]['int_locations']
                del res[mid]['ext_locations']
        res['int_instances'] = self._mods['int_instances']
        res['ext_instances'] = self._mods['ext_instances']
        return res
    #end def

    def getModID(self, strand, idx):
        id_num = strand.idNum()
        strandtype = strand.strandType()
        key =  "{},{},{}".format(id_num, strandtype, idx)
        mods_strand  = self._mods['ext_instances']
        if key in mods_strand:
            return mods_strand[key]
    # end def

    def getModSequence(self, strand, idx, modtype):
        mid = self.getModID(strand, idx)
        name = '' if mid is None else self._mods[mid]['name']
        if modtype == 0:
            seq = '' if mid is None else self._mods[mid]['seq5p']
        elif modtype == 1:
            seq = '' if mid is None else self._mods[mid]['seq3p']
        else:
            seq = '' if mid is None else self._mods[mid]['seqInt']
        return seq, name

    def getModStrandIdx(self, key):
        keylist = key.split(',')
        id_num = int(keylist[0])
        is_fwd = int(keylist[1])    # enumeration of StrandType.FWD or StrandType.REV
        idx = int(keylist[2])
        strand = self.getStrand(is_fwd, id_num, idx)
        return strand, idx
    # end def

    def addModInstance(self, id_num, idx, is_rev, isinternal, mid):
        key =  "{},{},{}".format(id_num, is_rev, idx)
        mods_strands = self._mods['int_instances'] if isinternal else self._mods['ext_instances']
        try:
            locations = self._mods[mid]['int_locations'] if isinternal else self._mods[mid]['ext_locations']
        except:
            print(mid, self._mods[mid])
            raise
        if key in mods_strands:
            self.removeModInstance(id_num, idx, is_rev, isinternal, mid)
        self.addModInstanceKey(key, mods_strands, locations, mid)
    # end def

    def addModInstanceKey(self, key, mods_strands, locations, mid):
        mods_strands[key] = mid # add to strand lookup
        # add to set of locations
        locations.add(key)
    # end def

    def addModStrandInstance(self, strand, idx, mid):
        id_num = strand.idNum()
        strandtype = strand.strandType()
        if mid is not None:
            self.addModInstance(id_num, idx, strandtype, False, mid)
    # end def

    def removeModInstance(self, id_num, idx, is_rev, isinternal, mid):
        key =  "{},{},{}".format(id_num, is_rev, idx)
        mods_strands = self._mods['int_instances'] if isinternal else self._mods['ext_instances']
        locations = self._mods[mid]['int_locations'] if isinternal else self._mods[mid]['ext_locations']
        if key in mods_strands:
            self.removeModInstanceKey(key, mods_strands, locations)
    # end def

    def removeModInstanceKey(self, key, mods_strands, locations):
        del mods_strands[key]
        locations.remove(key)
    # end def

    def removeModStrandInstance(self, strand, idx, mid):
        id_num = strand.idNum()
        is_rev = strand.isReverse()
        if mid is not None:
            self.removeModInstance(id_num, idx, is_rev, False, mid)
    # end def

    def changeModInstance(self, id_num, idx, is_rev, isinternal, mid_old, mid_new):
        if mid_new != mid_old:
            mods = self._mods
            if mid_old in mods and mid_new in mods:
                self.removeModInstance(id_num, idx, is_rev, isinternal, mid_old)
                self.addModInstance(id_num, idx, is_rev, isinternal, mid_new)
    # end def

    def changeModLocation(self, id_num, idx_old, idx, is_rev, isinternal, mid):
        if idx_old != idx:
            self.removeModInstance(id_num, idx_old, is_rev, isinternal, mid)
            self.addModInstance(id_num, idx, is_rev, isinternal, mid)
    # end def

    def changeModStrandLocation(self, strand, idxs_old, idxs):
        id_num = strand.idNum()
        is_rev = strand.isReverse()
        mods_strands = self._mods['ext_instances']
        for i in [0,1]:
            idx_old = idxs_old[i]
            idx = idxs[i]
            if idx_old != idx:
                key_old =  "{},{},{}".format(id_num, is_rev, idx_old)
                if key_old in mods_strands:
                    mid = mods_strands[key_old]
                    locations = self._mods[mid]['ext_locations']
                    self.removeModInstanceKey(key_old, mods_strands, locations)
                    key =  "{},{},{}".format(id_num, is_rev, idx)
                    self.addModInstanceKey(key, mods_strands, locations, mid)
        # end for
    # end def
# end class
