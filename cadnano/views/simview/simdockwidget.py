from PyQt5.QtWidgets import QDockWidget, QWidget
from PyQt5.QtWidgets import QHBoxLayout  # QVBoxLayout
from .customqt3dwindow import CustomQt3DWindow


class SimDockWidget(QDockWidget):
    """
    SimDockWidget is the SimView's equivalent of CustomQGraphicsView.
    It gets added to the Dock area directly by DocumentWindow, and maintains
    a QWidget container for the CustomQt3DWindow.

    Attributes:
        root_entity (QEntity): Description
    """
    name = 'sim'

    def __init__(self, flags):
        """Instantiates PyQt3D objects for the Sim view.
        Sets up the 2D layout, and then the 3D window.
        """
        super(SimDockWidget, self).__init__(flags)

    def setup(self, root_entity):
        self.widget = QWidget()
        self.setWidget(self.widget)
        self._3dwindow = CustomQt3DWindow(root_entity)
        self._container = QWidget.createWindowContainer(self._3dwindow)
        self._h_layout = h_layout = QHBoxLayout(self.widget)
        h_layout.addWidget(self._container, 1)
        h_layout.setContentsMargins(0, 1, 0, 1)

        # Use v_layout for buttons
        # self._v_layout = v_layout = QVBoxLayout()
        # v_layout.setAlignment(Qt.AlignTop)
        # v_layout.setContentsMargins(0, 0, 0, 0)
        # h_layout.addLayout(v_layout)
    # end def
# end class
