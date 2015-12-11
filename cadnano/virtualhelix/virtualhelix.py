from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.cnproxy import UndoStack, UndoCommand
from cadnano.enum import StrandType
from cadnano.strandset import StrandSet
from cadnano.math.vector import Vector3
from .removevhelixcmd import RemoveVirtualHelixCommand


class VirtualHelix(CNObject):
    """
    VirtualHelix is a container class for two StrandSet objects (one scaffold
    and one staple). The Strands all share the same helix axis. It is called
    "virtual" because many different Strands (i.e. sub-oligos) combine to
    form the "helix", just as many fibers may be braided together to
    form a length of rope.
    """
    editable_properties = ['name', 'color']
    def __init__(self, part, x, y, idnum=0):
        self._doc = part.document()
        super(VirtualHelix, self).__init__(part)
        self._location = Vector3(x, y, 0.)

        self._part = part
        self._scaf_strandset = StrandSet(StrandType.SCAFFOLD, self)
        self._stap_strandset = StrandSet(StrandType.STAPLE, self)
        # If self._part exists, it owns self._number
        # in that only it may modify it through the
        # private interface. The public interface for
        # setNumber just routes the call to the parent
        # PlasmidPart if one is present. If self._part is None
        # the virtualhelix owns self._number and may modify it.
        self._number = None
        self.setNumber(idnum)

        self._properties = {'eulerZ':0, 'scamZ':0, 'neighbors':'[]'}

        # rotate to honeycomb defaults
        self._properties['eulerZ'] = 10
        self._properties['scamZ'] = 10
    # end def

    def __repr__(self):
        return "<%s(%d)>" % (self.__class__.__name__, self._number)

    ### SIGNALS ###
    virtualHelixRemovedSignal = ProxySignal(CNObject, CNObject,
                                            name='virtualHelixRemovedSignal')  # self
    virtualHelixNumberChangedSignal = ProxySignal(CNObject, int,
                                            name='virtualHelixNumberChangedSignal')  # self, num
    virtualHelixPropertyChangedSignal = ProxySignal(CNObject, object, object,
                                            name='virtualHelixPropertyChangedSignal')  # self, transform

    ### SLOTS ###

    ### ACCESSORS ###
    def scaf(self, idx):
        """ Returns the strand at idx in self's scaffold, if any """
        return self._scaf_strandset.getStrand(idx)

    def stap(self, idx):
        """ Returns the strand at idx in self's scaffold, if any """
        return self._stap_strandset.getStrand(idx)

    def rect(self, scale_factor=1.0):
        """ return tuple of:
        (x_lower_left, y_lower_left, x_upper_right, y_upper_right)

        scale_factor allows creating a larger bounding box
        """
        # increase bounding box to
        # collide with neighbors
        radius = scale_factor*self._part.radius()
        x, y, z = self._location
        x *= scale_factor
        y *= scale_factor
        return x - radius, y - radius, x + radius, y + radius
    # end def

    def location(self, scale_factor=1.0):
        x, y, z = self._location
        return scale_factor*x, scale_factor*y
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

    def getPropertyDict(self):
        return self._properties
    # end def

    def setProperty(self, key, value):
        # use ModifyPropertyCommand here
        self._properties[key] = value
        self.virtualHelixPropertyChangedSignal.emit(self, key, value)
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

    def scaffoldStrandSet(self):
        return self._scaf_strandset
    # end def

    def stapleStrandSet(self):
        return self._stap_strandset
    # end def

    def undoStack(self):
        return self._part.undoStack()
    # end def

    ### METHODS FOR QUERYING THE MODEL ###
    def scaffoldIsOnTop(self):
        # return True
        return self.isEvenParity()

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
        # return strandset is self._scaf_strandset
        is_scaf = strandset == self._scaf_strandset
        is_even = self.isEvenParity()
        return is_even == is_scaf
    # end def

    # may need new method that doesn't rely on strandype
    # this doesn't generalize but is copied from old px branch
    def newIsDrawn5to3(self, strandset):
        is_scaf = strandset == self._scaf_strandset
        return is_scaf # "scaf" always on top for parallel xovers
    # end def

    def strandSetBounds(self, idx_helix, idx_type):
        """
        forwards the query to the strandset
        """
        return self.strandSet(idx_helix, idx_type).bounds()
    # end def

    ### METHODS FOR EDITING THE MODEL ###
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

    ### PUBLIC SUPPORT METHODS ###
    def deepCopy(self, part):
        """
        This only copies as deep as the VirtualHelix
        strands get copied at the oligo and added to the Virtual Helix
        """
        vh = VirtualHelix(part, self._number)
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

# end class
