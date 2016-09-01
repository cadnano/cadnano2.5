from cadnano.cnobject import CNObject

class VirtualHelix(CNObject):
    """lightweight convenience class whose properties are still stored in the
    `NucleicAcidPart`.  Having this makes it easier to write views.
    """
    def __init__(self, id_num, part):
        super(VirtualHelix, self).__init__(part)
        self._id_num = id_num
        self._part = part
    # end def

    @property
    def editable_properties(self):
        return self._part.vh_editable_properties

    def part(self):
        return self._part
    # end def

    def idNum(self):
        return self._id_num
    # end def

    def getProperty(self, keys):
        return self._part.getVirtualHelixProperties(self._id_num, keys)
    # end def

    def setProperty(self, keys, values, id_nums=None):
        if id_nums:
            part = self._part
            for id_num in id_nums:
                part.setVirtualHelixProperties(id_num, keys, values)
        else:
            return self._part.setVirtualHelixProperties(self._id_num, keys, values)
    # end def

    def getModelProperties(self):
        return self._part.getAllVirtualHelixProperties(self._id_num)
    # end def

    def getAllPropertiesForIdNum(self, id_num):
        return self._part.getAllVirtualHelixProperties(id_num)
    # end def

    def getName(self):
        return self._part.getVirtualHelixProperties(self._id_num, 'name')
    # end def

    def getColor(self):
        return self._part.getVirtualHelixProperties(self._id_num, 'color')
    # end def

    def getSize(self):
        offset, size = self._part.getOffsetAndSize(self._id_num)
        return int(size)
    # end def

    def setSize(self, new_size, id_nums=None):
        if id_nums:
            for id_num in id_nums:
                self._part.setVirtualHelixSize(id_num, new_size)
        else:
            return self._part.setVirtualHelixSize(self._id_num, new_size)
    # end def

    def fwdStrand(self, idx):
        self._part.fwd_strandsets[self._id_num].getStrand(idx)
    # end def

    def revStrand(self, idx):
        self._part.rev_strandsets[self._id_num].getStrand(idx)
    # end def

    def getTwistPerBase(self):
        """
        Returns:
            Tuple: twist per base in degrees, eulerZ
        """
        bpr, tpr, eulerZ = self._part.getVirtualHelixProperties(self._id_num,
                        ['bases_per_repeat', 'turns_per_repeat', 'eulerZ'])
        return tpr*360./bpr, eulerZ

    def getAngularProperties(self):
        """
        Returns:
            Tuple: 'bases_per_repeat, 'bases_per_turn',
                    'twist_per_base', 'minor_groove_angle'
        """
        bpr, tpr, mga = self._part.getVirtualHelixProperties(self._id_num,
                ['bases_per_repeat', 'turns_per_repeat', 'minor_groove_angle'])
        bases_per_turn = bpr / tpr
        return bpr, bases_per_turn, tpr*360./bpr, mga
    # end def

    def setZ(self, new_z, id_nums=None):
        m_p = self._part
        if id_nums is None:
            id_nums = self._id_num

        for id_num in id_nums:
            old_z = m_p.getVirtualHelixProperties(id_num, 'z')
            if new_z != old_z:
                dz = new_z - old_z
                m_p.translateVirtualHelices([id_num], 0, 0, dz, finalize=False, use_undostack=True)
    # end def

    def getAxisPoint(self, idx):
        return self._part.getCoordinate(self._id_num, idx)
    # end def

    def setActive(self, is_fwd, idx):
        """Makes active the virtual helix associated with this item."""
        self._part.setActiveVirtualHelix(self._id_num, is_fwd, idx)
    # end def

    def isActive(self):
        return self._part.isVirtualHelixActive(self._id_num)
    # end def
# end class