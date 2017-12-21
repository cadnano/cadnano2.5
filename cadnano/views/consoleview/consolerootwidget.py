"""Summary
"""
from PyQt5.QtWidgets import QWidget

from cadnano.proxies.cnenum import PartType
from cadnano.controllers.viewrootcontroller import ViewRootController
from cadnano.views.consoleview.nucleicacidpartitem import ConsoleNucleicAcidPartItem


class ConsoleRootWidget(QWidget):
    """
    ConsoleRootWidget is the root item in the ConsoleView. It receives two signals
    (partAddedSignal and selectedPartChangedSignal) via its ViewRootController.

    ConsoleRootWidget must instantiate its own controller to receive signals
    from the model.

    Attributes:
        instance_items (dict): Description
        manager (TYPE): Description
        name (str): Description
    """
    name = 'console'

    def __init__(self):
        """Summary

        Args:
            rect (TYPE): Description
            parent (TYPE): Description
            window (TYPE): Description
            document (TYPE): Description
        """
        super(ConsoleRootWidget, self).__init__()
        self.instance_items = {}
        self._last_msg = ''
        # self.manager = None
        # self.select_tool = None
    # end def

    def finishInit(self, window, document, input_textedit, output_textedit):
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._input_textedit = input_textedit
        self._output_textedit = output_textedit
    # end def

    def log(self, msg):
        self._output_textedit.append(msg)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender, model_part_instance):
        """
        Receives notification from the model that a part has been added.
        Views that subclass AbstractView should override this method.

        Args:
            sender (obj): Model object that emitted the signal.
            model_part_instance (Part): Description

        Raises:
            NotImplementedError: partAddedSlot should always be overridden.
        """
        part_type = model_part_instance.reference().partType()
        if part_type == PartType.NUCLEICACIDPART:
            self.log('%s added' % model_part_instance.reference())

            na_part_item = ConsoleNucleicAcidPartItem(model_part_instance.reference(),
                                                      viewroot=self,
                                                      parent=self)
            self.instance_items[na_part_item] = na_part_item
        else:
            raise NotImplementedError
    # end def

    def selectedChangedSlot(self, item_dict):
        """docstring for selectedChangedSlot

        Args:
            item_dict (TYPE): Description
        """
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        """Update active tool to respond to active filters.

        Args:
            filter_name_list (list): list of active filters
        """
        if 'virtual_helix' in filter_name_list:
            msg = "Selection filter: virtual helices"
            if msg != self._last_msg:
                self._last_msg = msg
                self.log(msg)
        elif 'oligo' in filter_name_list:
            oligo_features = []
            if 'endpoint' in filter_name_list:
                oligo_features.append('endpoints')
            if 'xover' in filter_name_list:
                oligo_features.append('crossovers')
            oligo_str = '|'.join(oligo_features)
            strand_features = []
            if 'scaffold' in filter_name_list:
                strand_features.append('scaffold')
            if 'staple' in filter_name_list:
                strand_features.append('staple')
            strand_str = '|'.join(strand_features)
            parity_features = []
            if 'forward' in filter_name_list:
                parity_features.append('fwd')
            if 'reverse' in filter_name_list:
                parity_features.append('rev')
            parity_str = '|'.join(parity_features)
            msg = "Selection filter: oligo ({}) & ({}) & ({})".format(oligo_str, strand_str, parity_str)
            if msg != self._last_msg:
                self._last_msg = msg
                self.log(msg)
        # if 'virtual_helix' not in filter_name_list:
        #     self.manager.chooseCreateTool()
        # tool = self.manager.activeToolGetter()
        # tool.setSelectionFilter(filter_name_list)
        # for nucleicacid_part_item in self.instance_items:
        #     nucleicacid_part_item.setSelectionFilter(filter_name_list)
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        """Summary

        Args:
            filter_name (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def clearSelectionsSlot(self, doc):
        """Summary

        Args:
            doc (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def resetRootItemSlot(self, doc):
        """Summary

        Args:
            doc (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    ### ACCESSORS ###
    def window(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._window
    # end def

    ### METHODS ###
    def removePartItem(self, part_item):
        """Summary

        Args:
            part_item (TYPE): Description

        Returns:
            TYPE: Description
        """
        del self.instance_items[part_item]
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController

        Args:
            document (TYPE): Description

        Raises:
            ImportError: Description
        """
        self._document = document
        self._controller = ViewRootController(self, document)
        if len(self.instance_items) > 0:
            raise ImportError
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState

        Args:
            bool (TYPE): Description
        """
        for nucleicacid_part_item in self.instance_items:
            nucleicacid_part_item.setModifyState(bool)
    # end def

    def setManager(self, manager):
        """Summary

        Args:
            manager (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
        # self.manager = manager
        # self.select_tool = manager.select_tool
    # end def
