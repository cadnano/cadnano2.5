from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QActionGroup
from .selectslicetool import SelectSliceTool
from .createslicetool import CreateSliceTool

from cadnano import util
from cadnano import app

class SliceToolManager(QObject):
    """Manages interactions between the slice widgets/UI and the model."""
    def __init__(self, win):
        """
        We store mainWindow because a controller's got to have
        references to both the layer above (UI) and the layer below (model)
        """
        super(SliceToolManager, self).__init__()
        self.window = win
        self._active_tool = None
        self._active_part = None
        self.select_tool = SelectSliceTool(self)
        self.create_tool = CreateSliceTool(self)

        # def installTool(tool_name, window):
        #     l_tool_name = tool_name.lower()
        #     tool_widget = getattr(window, 'action_slice_' + l_tool_name)
        #     tool = getattr(self, l_tool_name + '_tool')
        #     tool.action_name = 'action_slice_' + tool_name

        #     def clickHandler(self):
        #         tool_widget.setChecked(True)
        #         self.setActiveTool(tool)
        #         if hasattr(tool, 'widgetClicked'):
        #             tool.widgetClicked()
        #     # end def

        #     select_tool_method_name = 'choose' + tool_name + 'SliceTool'
        #     setattr(self.__class__, select_tool_method_name, clickHandler)
        #     handler = getattr(self, select_tool_method_name)
        #     tool_widget.triggered.connect(handler)
        #     return tool_widget
        # # end def

        # tools = ('Select', 'Create')
        # self.ag = QActionGroup(win)
        # # Call installTool on every tool
        # list(map((lambda tool_name: self.ag.addAction(installTool(tool_name, win))), tools))
        # self.ag.setExclusive(True)

        # Select the preferred Startup tool
        startup_tool_name = app().prefs.getStartupToolName()
        # getattr(self, 'choose' + startup_tool_name + 'SliceTool')()
        self._connectWindowSignalsToSelf()
    # end def

    ### SIGNALS ###
    activeToolChangedSignal = pyqtSignal(str)
    activeSliceSetToFirstIndexSignal = pyqtSignal()
    activeSliceSetToLastIndexSignal = pyqtSignal()
    activePartRenumber = pyqtSignal()


    def activeToolGetter(self):
        return self._active_tool
    # end def

    def setActiveTool(self, new_active_tool):
        if new_active_tool == self._active_tool:
            return

        # if self.lastLocation():
        #     new_active_tool.updateLocation(*self.lastLocation())

        if self._active_tool is not None:
            self._active_tool.setActive(False)

        self._active_tool = new_active_tool
        self._active_tool.setActive(True)
        self.activeToolChangedSignal.emit(self._active_tool.action_name)
    # end def

    ### SLOTS ###
    def activeSliceFirstSlot(self):
        """
        Use a signal to notify the ActiveSliceHandle to move. A signal is used
        because the SliceToolManager must be instantiated first, and the
        ActiveSliceHandle can later subscribe.
        """
        part = self.window.selectedInstance()
        if part is not None:
            part.setActiveBaseIndex(0)

    def activeSliceLastSlot(self):
        part = self.window.selectedInstance()
        if part is not None:
            part.setActiveBaseIndex(part.maxBaseIdx()-1)

    ### METHODS ###
    def _connectWindowSignalsToSelf(self):
        """This method serves to group all the signal & slot connections
        made by SliceToolManager"""
        self.window.action_slice_first.triggered.connect(self.activeSliceFirstSlot)
        self.window.action_slice_last.triggered.connect(self.activeSliceLastSlot)
