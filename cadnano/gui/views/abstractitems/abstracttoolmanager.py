from PyQt5.QtCore import pyqtSignal, QObject

class DummyTool(object):
    """ For use in place of None checks in the code
    reduces boilerplate
    """
    action_name = 'action_dummy_tool'

    def methodPrefix(self):
        return "dummyTool"  # first letter should be lowercase

    def setActive(self, bool):
        pass

    def lastLocation(self):
        return None

dummy_tool = DummyTool()


class AbstractToolManager(QObject):
    """Manages interactions between the slice widgets/UI and the model."""
    def __init__(self, tool_group_name, window, viewroot):
        """
        We store mainWindow because a controller's got to have
        references to both the layer above (UI) and the layer below (model)
        """
        super(AbstractToolManager, self).__init__()
        self.window = window
        self.viewroot = viewroot
        self.document = window.document()
        self.tool_group_name = tool_group_name
        self._active_tool = dummy_tool
        self._active_part = None
        self.tool_names = None
    # end def

    ### SIGNALS ###
    activeToolChangedSignal = pyqtSignal(str)

    def installTools(self):
        if self.viewroot.manager is None:
            raise ValueError("Please call viewroot.setManager before calling installTools")
        # Call installTool on every tool
        tnames = self.tool_names
        if tnames is None:
            raise ValueError("Please define tools_names of AbstractToolManager subclass")
        for tool_name in tnames:
            self.installTool(tool_name)
    # end def

    def installTool(self, tool_name):
        window = self.window
        tgn = self.tool_group_name

        l_tool_name = tool_name.lower()
        action_name = 'action_%s_%s' % (tgn, l_tool_name)
        if hasattr(window, action_name):
            tool_widget = getattr(window, action_name)
        else:
            tool_widget = None
        tool = getattr(self, l_tool_name + '_tool')
        tool.action_name = action_name

        set_active_tool_method_name = 'choose%sTool' % (tool_name)

        def clickHandler(self):
            if tool_widget is not None:
                tool_widget.setChecked(True)
            self.setActiveTool(tool)
            if hasattr(tool, 'widgetClicked'):
                tool.widgetClicked()
        # end def

        setattr(self.__class__, set_active_tool_method_name, clickHandler)
        handler = getattr(self, set_active_tool_method_name)
        if tool_widget is not None:
            tool_widget.triggered.connect(handler)
        return tool_widget
    # end def

    def deactivateAllTools(self):
        """ uncheck all tools in this group and set the active tool to None
        """
        window = self.window
        tgn = self.tool_group_name
        if self._active_tool is not None:
            self._active_tool.setActive(False)
        for tool_name in self.tool_names:
            l_tool_name = tool_name.lower()
            action_name = 'action_%s_%s' % (tgn, l_tool_name)
            tool_widget = getattr(window, action_name)
            tool_widget.setChecked(False)
        self._active_tool = dummy_tool
    # end def

    def destroy(self):
        window = self.window
        tgn = self.tool_group_name
        if self._active_tool is not None:
            self._active_tool.setActive(False)
        for tool_name in self.tool_names:
            l_tool_name = tool_name.lower()
            action_name = 'action_%s_%s' % (tgn, l_tool_name)
            tool_widget = getattr(window, action_name)
            set_active_tool_method_name = 'choose%sTool' % (tool_name)
            handler = getattr(self, set_active_tool_method_name)
            tool_widget.triggered.disconnect(handler)
            tool_widget.setChecked(False)
        self._active_tool = dummy_tool
        self.window = None
    # end def

    def activeToolGetter(self):
        return self._active_tool
    # end def

    def setActiveTool(self, new_active_tool):
        if new_active_tool == self._active_tool:
            return
        if new_active_tool is None:
            new_active_tool = dummy_tool

        if self._active_tool is not None:
            self._active_tool.setActive(False)

        self._active_tool = new_active_tool
        self._active_tool.setActive(True)
        self.activeToolChangedSignal.emit(self._active_tool.action_name)
    # end def

    def getFilterList(self):
        return self.document.filter_list
# end class
