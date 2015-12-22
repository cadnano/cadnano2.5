from cadnano import util
from cadnano.cnproxy import ProxyObject, ProxySignal
from cadnano.cnproxy import UndoStack, UndoCommand
from cadnano.enum import StrandType
from cadnano.strandset import StrandSet
from .removevhelixcmd import RemoveVirtualHelixCommand
from .resizevhelixcmd import ResizeVirtualHelixCommand


class VirtualHelix(ProxyObject):
    """
    VirtualHelix is a container class for two StrandSet objects (one scaffold
    and one staple). The Strands all share the same helix axis. It is called
    "virtual" because many different Strands (i.e. sub-oligos) combine to
    form the "helix", just as many fibers may be braided together to
    form a length of rope.
    """

    def __init__(self, part, row, col, idnum=0):
        self._doc = part.document()
        super(VirtualHelix, self).__init__(part)
        self._coord = (row, col) # col, row
        self._part = part
        # If self._part exists, it owns self._number
        # in that only it may modify it through the
        # private interface. The public interface for
        # setNumber just routes the call to the parent
        # PlasmidPart if one is present. If self._part is None
        # the virtualhelix owns self._number and may modify it.
        self._number = None
        self.setNumber(idnum)
        self._properties = {'eulerZ':0,
                            'scamZ':0, 
                            'active_phos':None,
                            'neighbor_active_angle':'',
                            'neighbors':'',
                            'z':0,
                            'bases_per_repeat':21,
                            'turns_per_repeat':2,
                            'repeats':8,
                            '_bases_per_turn':10.5, # bases_per_repeat/turns_per_repeat
                            '_twist_per_base':360/10.5, # 360/_bases_per_turn
                            '_max_length':21*8
                            }
        self._min_base = 0
        self._max_base = self._properties['_max_length']-1
        self._scaf_strandset = StrandSet(StrandType.SCAFFOLD, self)
        self._stap_strandset = StrandSet(StrandType.STAPLE, self)
    # end def

    def __repr__(self):
        return "<%s(%d)>" % (self.__class__.__name__, self._number)

    ### SIGNALS ###
    virtualHelixRemovedSignal = ProxySignal(ProxyObject, ProxyObject,
                                            name='virtualHelixRemovedSignal')  # self
    virtualHelixNumberChangedSignal = ProxySignal(ProxyObject, int,
                                            name='virtualHelixNumberChangedSignal')  # self, num
    virtualHelixPropertyChangedSignal = ProxySignal(ProxyObject, object, object,
                                            name='virtualHelixPropertyChangedSignal')  # self, transform

    ### SLOTS ###

    ### ACCESSORS ###
    def scaf(self, idx):
        """ Returns the strand at idx in self's scaffold, if any """
        return self._scaf_strandset.getStrand(idx)

    def stap(self, idx):
        """ Returns the strand at idx in self's scaffold, if any """
        return self._stap_strandset.getStrand(idx)

    def coord(self):
        return self._coord
    # end def

    def number(self):
        return self._number
    # end def

    def part(self):
        return self._part
    # end def

    def document(self):
        return self._doc
    # end def

    def getProperty(self, key):
        return self._properties[key]
    # end def

    def getReadOnlyProperty(self, key):
        return self._read_only_properties[key]
    # end def

    def getColor(self):
        return "#ffffff" #self._properties['color']

    def setViewProperty(self, key, value):
        self.view_properties[key] = value
    # end def

    def getViewProperty(self, key):
        return self.view_properties[key]
    # end def

    def getName(self):
        name = self._properties.get('name')
        if name is None:
            return "vh%d" % (self._number)
        else:
            return name
    # end def

    def minBaseIdx(self):
        return 0

    def maxBaseIdx(self):
        return self.getMaxLength()-1

    def getMaxLength(self):
        bpr = int(self._properties['bases_per_repeat'])
        r = int(self._properties['repeats'])
        return bpr*r

    def getPropertyDict(self):
        return self._properties
    # end def

    def setProperty(self, key, value):
        # use ModifyPropertyCommand here
        if key in self._properties:
            if self._properties[key] == value:
                return
        self._properties[key] = value
        self.virtualHelixPropertyChangedSignal.emit(self, key, value)
        if key in ['bases_per_repeat', 'turns_per_repeat', 'repeats']:
            old_max_length = self._properties['_max_length']
            bpr = int(self._properties['bases_per_repeat'])
            tpr = int(self._properties['turns_per_repeat'])
            r = int(self._properties['repeats'])
            self._properties['_bases_per_turn'] = bpt = round(bpr/tpr,3)
            self._properties['_twist_per_base'] = tpb = 360/bpt
            self._properties['_max_length'] = ml = bpr*r
            self.virtualHelixPropertyChangedSignal.emit(self, '_bases_per_turn', bpt)
            self.virtualHelixPropertyChangedSignal.emit(self, '_twist_per_base', tpb)
            self.virtualHelixPropertyChangedSignal.emit(self, '_max_length', ml)

            delta = ml-old_max_length
            if delta:
                self.resize(delta)
    # end def

    def setNumber(self, number):
        if self._number != number:
            num_to_vh_dict = self._part._number_to_virtual_helix
            # if self._number is not None:
            num_to_vh_dict[self._number] = None
            self._number = number
            self.virtualHelixNumberChangedSignal.emit(self, number)
            num_to_vh_dict[number] = self
    # end def

    def setPart(self, new_part):
        self._part = new_part
        self.setParent(new_part)
    # end def

    def fwdStrandSet(self):
        return self._scaf_strandset
    # end def

    def scaffoldStrandSet(self):
        return self._scaf_strandset
    # end def

    def revStrandSet(self):
        return self._stap_strandset
    # end def

    def stapleStrandSet(self):
        return self._stap_strandset
    # end def

    def undoStack(self):
        return self._part.undoStack()
    # end def

    ### METHODS FOR QUERYING THE MODEL ###
    def scaffoldIsOnTop(self):
        return True
        # return self.isEvenParity()

    def getStrandSetByIdx(self, idx):
        """
        This is a path-view-specific accessor
        idx == 0 means top strand
        idx == 1 means bottom strand
        """
        if idx == 0:
            return self._scaf_strandset
        else:
            return self._stap_strandset
    # end def

    def getStrandSetByType(self, strand_type):
        if strand_type is StrandType.SCAFFOLD:
            return self._scaf_strandset
        else:
            return self._stap_strandset
    # end def

    def getStrandSets(self):
        """Return a tuple of the scaffold and staple StrandSets."""
        return self._scaf_strandset, self._stap_strandset
    # end def

    def hasStrandAtIdx(self, idx):
        """Return a tuple for (Scaffold, Staple). True if
           a strand is present at idx, False otherwise."""
        return (self._scaf_strandset.hasStrandAt(idx, idx),\
                self._stap_strandset.hasStrandAt(idx, idx))
    # end def

    def indexOfRightmostNonemptyBase(self):
        """Returns the rightmost nonempty base in either scaf of stap."""
        return max(self._scaf_strandset.indexOfRightmostNonemptyBase(),\
                   self._stap_strandset.indexOfRightmostNonemptyBase())
    # end def

    def isDrawn5to3(self, strandset):
        return strandset is self._scaf_strandset
        # is_scaf = strandset == self._scaf_strandset
        # is_even = self.isEvenParity()
        # return is_even == is_scaf
    # end def

    # may need new method that doesn't rely on strandype
    # this doesn't generalize but is copied from old px branch
    def newIsDrawn5to3(self, strandset):
        is_scaf = strandset == self._scaf_strandset
        return is_scaf # "scaf" always on top for parallel xovers
    # end def

    def isEvenParity(self):
        return self._part.isEvenParity(*self._coord)
    # end def

    def strandSetBounds(self, idx_helix, idx_type):
        """
        forwards the query to the strandset
        """
        return self.strandSet(idx_helix, idx_type).bounds()
    # end def

    ### METHODS FOR EDITING THE MODEL ###
    def moveBy(self, dx, dy, dz):
        if dx:
            x = self.getProperty('x')
            self.setProperty('x', x+dx)
        if dy:
            y = self.getProperty('y')
            self.setProperty('y', y+dy)
        if dz:
            z = self.getProperty('z')
            self.setProperty('z', z+dz)
    # end def

    def destroy(self):
        # QObject also emits a destroyed() Signal
        self.setParent(None)
        self.deleteLater()
    # end def

    def remove(self, use_undostack=True):
        """
        Removes a VirtualHelix from the model. Accepts a reference to the
        VirtualHelix, or a (row,col) lattice coordinate to perform a lookup.
        """
        if use_undostack:
            self.undoStack().beginMacro("Delete VirtualHelix")
        self._scaf_strandset.remove(use_undostack)
        self._stap_strandset.remove(use_undostack)
        c = RemoveVirtualHelixCommand(self.part(), self)
        if use_undostack:
            self.undoStack().push(c)
            self.undoStack().endMacro()
        else:
            c.redo()
    # end def

    def resize(self, max_delta, use_undostack=True):
        c = ResizeVirtualHelixCommand(self.part(), self, max_delta)
        util.execCommandList(self, [c], desc="Resize VHelix", \
                                                    use_undostack=use_undostack)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def deepCopy(self, part):
        """
        This only copies as deep as the VirtualHelix
        strands get copied at the oligo and added to the Virtual Helix
        """
        vh = VirtualHelix(part, self._number)
        vh._coords = (self._coord[0], self._coord[1])
        vh._theta = self._theta
        # If self._part exists, it owns self._number
        # in that only it may modify it through the
        # private interface. The public interface for
        # setNumber just routes the call to the parent
        # PlasmidPart if one is present. If self._part is None
        # the virtualhelix owns self._number and may modify it.
        self._number = idnum
    # end def

    def getLegacyStrandSetArray(self, strand_type):
        """Called by legacyencoder."""
        if strand_type == StrandType.SCAFFOLD:
            return self._scaf_strandset.getLegacyArray()
        else:
            return self._stap_strandset.getLegacyArray()

    def shallowCopy(self):
        pass
    # end def

    # def translateCoords(self, deltaCoords):
    #     """
    #     for expanding a helix
    #     """
    #     deltaRow, deltaCol = deltaCoords
    #     row, col = self._coord
    #     self._coord = row + deltaRow, col + deltaCol
    # # end def
# end class
