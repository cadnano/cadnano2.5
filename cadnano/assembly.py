from collections import defaultdict
# from operator import attrgetter
from operator import methodcaller

# from cadnano.part import Part
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
# from cadnano.cnproxy import UndoCommand, UndoStack


class Assembly(CNObject):
    """
    An Assembly is a collection of components, comprised recursively of
    various levels of individual parts and sub-assembly modules.

    The purpose of an Assembly object in radnano is to arrange Parts into
    larger groups (which may be connected or constrained in specific ways)
    to facilitate the modeling of more complex designs than a single part.
    """

    def __init__(self, document):
        super(Assembly, self).__init__(document)
        self._document = document
        self._obj_instance_list = []   # This is a list of member parts

        # This is a list of ObjectInstances of this
        # particular assembly ONLY
        # an Assembly can not have an ObjectIntanceList that contains itself
        # that would be a circular reference
        self._assembly_instances = []
    # end def

    # SIGNALS #
    assemblyInstanceAddedSignal = ProxySignal(CNObject, name='assemblyInstanceAddedSignal')
    assemblyDestroyedSignal = ProxySignal(CNObject, name='assemblyDestroyedSignal')

    # SLOTS #

    # METHODS #
    def undoStack(self):
        return self._document.undoStack()

    def destroy(self):
        # QObject also emits a destroyed() Signal
        self.setParent(None)
        self.deleteLater()
    # end def

    def document(self):
        return self._document
    # end def

    def objects(self):
        for obj in self._obj_instance_list:
            yield obj
    # end def

    def instances(self):
        for inst in self._assembly_instances:
            yield inst
    # end def

    def deepCopy(self):
        """
        Deep copy the assembly by cloning the

        This leaves alone assemblyInstances, and only

        To finish the job this deepCopy Assembly should be incorporated into
        a new ObjectInstance and therefore an assemblyInstance
        """
        doc = self._document
        asm = Assembly(doc)
        new_obj_inst_list = asm._obj_instance_list
        obj_instances = self.objects()

        # create a dictionary mapping objects (keys) to lists of
        # ObjectInstances ([value1, value2])
        # this uniquifies the creation of new Assemblies
        object_dict = defaultdict(list)
        f1 = methodcaller('reference')
        for x in obj_instances:
            obj = f1(x)
            object_dict[obj].append(x)
        # end for

        # copy the all the objects
        f2 = methodcaller('deepCopy')
        for key, value in object_dict:
            # create a new object
            newObj = f2(key)
            # copy all of the instances relevant to this new object
            newInsts = [obj_inst.deepCopy(newObj, asm) for obj_inst in value]
            # add these to the list in the assembly
            new_obj_inst_list.extend(newInsts)
            # add Object to the document
            doc.addObject(newObj)
        # end for
        return asm
    # end def

    def addInstance(self, assembly_instance):
        self._assembly_instances.extend(assembly_instance)
    # end def
# end class
