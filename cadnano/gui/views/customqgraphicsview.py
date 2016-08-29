#!/usr/bin/env python
# encoding: utf-8

"""
CustomQGraphicsView

Platform:
    Unix, Windows, Mac OS X

Synopsis:
    A Custom QGraphicsView module to allow focus input events like mouse clicks,
    panning, and zooming.
"""

from cadnano import app
from cadnano.gui.views.pathview import pathstyles as styles
from cadnano import util
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QPaintEngine
from PyQt5.QtWidgets import qApp, QGraphicsView

# for OpenGL mode
try:
    # from OpenGL import GL
    from PyQt5.QtWidgets import QOpenGLWidget
except:
    GL = False

GL = False


class CustomQGraphicsView(QGraphicsView):
    """
    Base class for QGraphicsViews with Mouse Zoom and Pan support via the
    Control/Command shortcut key.

    A QGraphics View stores info on the view and handles mouse events for
    zooming and panning

    Ctrl-MidMouseButton = Pan
    Ctrl-RightMouseButton = Dolly Zoom
    MouseWheel = Zoom

    Args:
        parent(QWidget): type of QWidget such as QWidget.main_splitter() for the type of
                         View its has

    For details on these and other miscellaneous methods, see below.
    """
    def __init__(self, parent=None):
        """
        On initialization, we need to bind the Ctrl/command key to
        enable manipulation of the view.
        """
        QGraphicsView.__init__(self, parent)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        self._no_drag = QGraphicsView.RubberBandDrag
        self._yes_drag = QGraphicsView.ScrollHandDrag

        # reset things that are state dependent
        self.clearGraphicsView()

        self._x0 = 0
        self._y0 = 0
        self._scale_size = 1.0
        self._scale_limit_max = 24.0  # OLD 3.0
        self._scale_limit_min = 0.21
        self._scale_up_rate = 0.01
        self._scale_down_rate = 0.01
        self._scale_fit_factor = .5  # sets initial zoom level
        self._show_details = True
        self._last_scale_factor = 0.0
        self.scene_root_item = None  # the item to transform
        # Keyboard panning
        self._key_pan_delta_x = styles.PATH_BASE_WIDTH * 21
        self._key_pan_delta_y = styles.PATH_HELIX_HEIGHT + styles.PATH_HELIX_PADDING/2
        # Modifier keys and buttons
        self._key_mod = Qt.Key_Control
        self._button_pan = Qt.LeftButton
        self._button_pan_alt = Qt.MidButton
        self._button_zoom = Qt.RightButton

        self.toolbar = None  # custom hack for the paint tool palette
        self._name = None

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        if GL:
            self.is_GL = True
            # self.glwidget = QGLWidget(QGLFormat(QGL.SampleBuffers))
            self.glwidget = QOpenGLWidget()
            # self.setupGL()
            self.gl = self.glwidget.context().versionFunctions()
            self.setViewport(self.glwidget)
            self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
            # self.resetGL()
        else:
            self.is_GL = False
            self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
            # self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        # self.setFocusPolicy(Qt.ClickFocus)
    # end def

    levelOfDetailChangedSignal = pyqtSignal(bool)

    def __repr__(self):
        clsName = self.__class__.__name__
        objId = self._name if self._name else str(id(self))[-4:]
        return "<%s %s>" % (clsName, objId)

    def setName(self, name):
        self._name = name
    # end def

    def setViewportUpdateOn(self, is_enabled):
        if is_enabled:
            self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        else:
            self.setViewportUpdateMode(QGraphicsView.NoViewportUpdate)
    # end def

    def activateSelection(self, is_active):
        if self._selection_lock:
            self._selection_lock.clearSelection(False)
        self.clearSelectionLockAndCallbacks()
        if is_active:
            self._no_drag = QGraphicsView.RubberBandDrag
        else:
            self._no_drag = QGraphicsView.NoDrag
        if self.dragMode() != self._yes_drag:
            self.setDragMode(self._no_drag)
    # end def

    def clearGraphicsView(self):
        # Event handling
        self._has_focus = False
        # Misc
        self.clearSelectionLockAndCallbacks()
        # Pan and dolly defaults
        self._transform_enable = False
        self._dolly_zoom_enable = False
        self.setDragMode(self._no_drag)
    # end def

    def clearSelectionLockAndCallbacks(self):
        self._selection_lock = None # a selection group to limit types of items selected
        self._press_list = [] # bookkeeping to handle passing mouseReleaseEvents to QGraphicsItems that don't get them
    # end def

    def _setGLView(self, boolval):
        scene = self.scene()
        if boolval and self.is_GL is False:
            self.is_GL = True
            # scene.drawBackground = self._drawBackgroundGL
            # self.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
            # self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        elif not boolval and self.is_GL is True:
            self.is_GL = False
            # scene.drawBackground = self.drawBackgroundNonGL
            # self.setViewport(QWidget())
            # self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
    # end def

    def setupGL(self):
        scene = self.scene()
        # win = self.scene_root_item.window()
        self.is_GL = True
        self.is_GL_switch_allowed = True
        self.qTimer = QTimer()
        # self.drawBackgroundNonGL = scene.drawBackground
        # scene.drawBackground = self._drawBackgroundGL
        # format = QGLFormat(QGL.SampleBuffers)
        # format.setSamples(16)
        # print "# of samples", format.samples(), format.sampleBuffers()
        # self.setViewport(QGLWidget(format))
        # self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
    # end def

    def _resetLOD(self):
        scale_factor = self.transform().m11()
        # print("scale_factor", scale_factor)
        self.scene_root_item.window().statusBar().showMessage("%0.2f" % scale_factor)
        if scale_factor < 0.75:
            self._show_details = False
            self.levelOfDetailChangedSignal.emit(False) # zoomed out
        elif scale_factor > 0.8:
            self._show_details = True
            self.levelOfDetailChangedSignal.emit(True) # zoomed in
    # end def

    def _resetGL(self):
        scale_factor = self.transform().m11()
        # print("scale_factor", scale_factor)
        self.scene_root_item.window().statusBar().showMessage("%0.2f" % scale_factor)

        if scale_factor < .15:# and self.is_GL_switch_allowed:
            # self.is_GL_switch_allowed = False
            self._setGLView(True)
            self._show_details = False
            self.levelOfDetailChangedSignal.emit(False) # zoomed out
            self.qTimer.singleShot(500, self._allowGLSwitch)
        elif scale_factor > .2:# and self.is_GL_switch_allowed:
            # self.is_GL_switch_allowed = False
            self._setGLView(False)
            self._show_details = True
            self.levelOfDetailChangedSignal.emit(True) # zoomed in
            self.qTimer.singleShot(500, self._allowGLSwitch)
    # end def

    def shouldShowDetails(self):
        return self._show_details
    # end def

    def _allowGLSwitch(self):
        self.is_GL_switch_allowed = True
    # end def

    def _drawBackgroundGL(self, painter, rect):
        """
        This method is for overloading the QGraphicsScene.
        """
        if painter.paintEngine().type() != QPaintEngine.OpenGL and \
            painter.paintEngine().type() != QPaintEngine.OpenGL2:

            qWarning("OpenGLScene: drawBackground needs a QGLWidget to be set as viewport on the graphics view");
            return
        # end if
        painter.beginNativePainting()
        GL.glDisable(GL.GL_DEPTH_TEST) # disable for 2D drawing
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        painter.endNativePainting()
    # end def

    def focusInEvent(self, event):
        self._has_focus = True

    def focusOutEvent(self, event):
        self._transform_enable = False
        self._dolly_zoom_enable = False
        self._has_focus = False
        self._transform_enable = False
    # end def

    def setSelectionLock(self, selection_lock):
        self._selection_lock = selection_lock
    # end def

    def selectionLock(self):
        return self._selection_lock
    # end def

    def setScaleFitFactor(self, value):
        """docstring for setScaleFitFactor"""
        self._scale_fit_factor = value
    # end def

    def setKeyPan(self, button):
        """Set the class pan button remotely"""
        self._button_pan = button
    # end def

    def addToPressList(self, item):
        """docstring for addToPressList"""
        # self._press_list[self._press_list_idx].append(item)
        self._press_list.append(item)
    # end def

    def keyPanDeltaX(self):
        """Returns the distance in scene space to move the scene_root_item when
        panning left or right."""
        # PyQt isn't aware that QGraphicsObject isa QGraphicsItem and so
        # it returns a separate python object if, say, childItems() returns
        # a QGraphicsObject casted to a QGraphicsItem. If this is the case,
        # we can still find the QGraphicsObject thusly:
        candidateDxDeciders = list(self.scene_root_item.childItems())
        candidateDxDeciders = candidateDxDeciders +\
                           [cd.toGraphicsObject() for cd in candidateDxDeciders]
        for cd in candidateDxDeciders:
            if cd is None:
                continue
            keyPanDXMethod = getattr(cd, 'keyPanDeltaX', None)
            if keyPanDXMethod is not None:
                return keyPanDXMethod()
        return 100

    def keyPanDeltaY(self):
        """Returns the distance in scene space to move the scene_root_item when
        panning left or right."""
        candidateDyDeciders = list(self.scene_root_item.childItems())
        candidateDyDeciders = candidateDyDeciders +\
                           [cd.toGraphicsObject() for cd in candidateDyDeciders]
        for cd in candidateDyDeciders:
            if cd is None:
                continue
            keyPanDYMethod = getattr(cd, 'keyPanDeltaY', None)
            if keyPanDYMethod is not None:
                return keyPanDYMethod()
        return 100

    def keyPressEvent(self, event):
        """
        Handle key presses for mouse-drag transforms and arrow-key panning.
        """
        if not self._has_focus:  # we don't have focus -> ignore keypress
            return
        if event.key() == self._key_mod:
            self._transform_enable = True
            QGraphicsView.keyPressEvent(self, event)
        elif event.key() == Qt.Key_Left:
            transform = self.scene_root_item.transform()
            transform.translate(self.keyPanDeltaX(), 0)
            self.scene_root_item.setTransform(transform)
        elif event.key() == Qt.Key_Up:
            transform = self.scene_root_item.transform()
            transform.translate(0, self.keyPanDeltaY())
            self.scene_root_item.setTransform(transform)
        elif event.key() == Qt.Key_Right:
            transform = self.scene_root_item.transform()
            transform.translate(-self.keyPanDeltaX(), 0)
            self.scene_root_item.setTransform(transform)
        elif event.key() == Qt.Key_Down:
            transform = self.scene_root_item.transform()
            transform.translate(0, -self.keyPanDeltaY())
            self.scene_root_item.setTransform(transform)
        elif event.key() == Qt.Key_Plus:
            self.zoomIn(0.3)
        elif event.key() == Qt.Key_Minus:
            self.zoomIn(0.03)
        else:
            return QGraphicsView.keyPressEvent(self, event)
        # end else
    # end def

    def keyReleaseEvent(self, event):
        """docstring for keyReleaseEvent"""
        if event.key() == self._key_mod:
            self._transform_enable = False
            self._dolly_zoom_enable = False
            self._panDisable()
        # end if
        else:
            QGraphicsView.keyReleaseEvent(self, event)
        # end else
    # end def

    def enterEvent(self, event):
        # self.setFocus() # this call robs selection from key focus
        self.setDragMode(self._no_drag)
        QGraphicsView.enterEvent(self, event)

    def leaveEvent(self, event):
        self.clearFocus()
        QGraphicsView.leaveEvent(self, event)

    def mouseMoveEvent(self, event):
        """
        Must reimplement mouseMoveEvent of QGraphicsView to allow
        ScrollHandDrag due to the fact that events are intercepted
        breaks this feature.
        """
        if self._transform_enable == True:
            if self.dragMode() == self._yes_drag:
                # Add stuff to handle the pan event
                posf = event.localPos()
                xf = posf.x()
                yf = posf.y()

                factor = self.transform().m11()

                transform = self.scene_root_item.transform()
                transform.translate((xf - self._x0)/factor,\
                                             (yf - self._y0)/factor)
                self.scene_root_item.setTransform(transform)

                self._x0 = xf
                self._y0 = yf
            elif self._dolly_zoom_enable == True:
                self.dollyZoom(event)
        # adding this allows events to be passed to items underneath
        QGraphicsView.mouseMoveEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        """docstring for mousePressEvent"""
        if self._transform_enable == True and qApp.keyboardModifiers():
            which_buttons = event.buttons()
            if which_buttons in [self._button_pan, self._button_pan_alt]:
                self._panEnable()
                posf = event.localPos()
                self._x0 = posf.x()
                self._y0 = posf.y()
            elif which_buttons == self._button_zoom:
                self._dolly_zoom_enable = True
                self._last_scale_factor = 0
                # QMouseEvent.y() returns the position of the mouse cursor
                # relative to the widget
                self._y0 = event.localPos().y()
            else:
                QGraphicsView.mousePressEvent(self, event)
        else:
            QGraphicsView.mousePressEvent(self, event)
    # end def

    def mouseReleaseEvent(self, event):
        """If panning, stop. If handles were pressed, release them."""
        if self._transform_enable == True:
            # QMouseEvent.button() returns the button that triggered the event
            which_button = event.button()
            if which_button in [self._button_pan, self._button_pan_alt]:
                self._panDisable()
            elif which_button == self._button_zoom:
                self._dolly_zoom_enable = False
            else:
                return QGraphicsView.mouseReleaseEvent(self, event)
        # end if
        else:
            if len(self._press_list):  # Notify any pressed items to release
                event_pos = event.pos()
                for item in self._press_list:
                    #try:
                    # print("item release", item)
                    item.customMouseRelease(event)
                    #except:
                    #    item.mouseReleaseEvent(event)
                #end for
                self._press_list = []
            # end if
            if self._selection_lock:
                self._selection_lock.processPendingToAddList()
            return QGraphicsView.mouseReleaseEvent(self, event)

    # end def

    def _panEnable(self):
        """Enable ScrollHandDrag Mode in QGraphicsView (displays a hand
        pointer)"""
        self.setDragMode(self._yes_drag)
    # end def

    def _panDisable(self):
        """Disable ScrollHandDrag Mode in QGraphicsView (displays a hand
        pointer)"""
        self.setDragMode(self._no_drag)
    # end def

    def fname(self):
        """docstring for fname"""
        pass

    def wheelEvent(self, event):
        self.safeScale(event.angleDelta().y())
    # end def

    def safeScale(self, delta):
        current_scale_level = self.transform().m11()
        scale_factor = 1 + delta * \
           (self._scale_down_rate if delta < 0 else self._scale_up_rate) * \
           (app().prefs.zoom_speed/100.)
        new_scale_level = current_scale_level * scale_factor
        new_scale_level = util.clamp(current_scale_level * scale_factor,\
                              self._scale_limit_min,\
                              self._scale_limit_max)
        scale_change = new_scale_level / current_scale_level
        self.scale(scale_change, scale_change)

        self._resetLOD()
    # end def

    def zoomIn(self, fraction_of_max=0.5):
        current_scale_level = self.transform().m11()
        scale_change = (fraction_of_max * self._scale_limit_max) / current_scale_level
        self.scale(scale_change, scale_change)
    # end def

    def zoomOut(self, fraction_of_min=1):
        current_scale_level = self.transform().m11()
        scale_change = (fraction_of_min * self._scale_limit_min) / current_scale_level
        self.scale(scale_change, scale_change)
    # end def

    def dollyZoom(self, event):
        """docstring for dollyZoom"""
        # QMouseEvent.y() returns the position of the mouse cursor relative
        # to the widget
        yf = event.y()
        denom = abs(yf - self._y0)
        if denom > 0:
            scale_factor = (self.height() / 2) % denom
            if self._last_scale_factor != scale_factor:
                self._last_scale_factor = scale_factor
                # zoom in if mouse y position is getting bigger
                if yf - self._y0 > 0:
                    self.safeScale(yf - self._y0)
                # end else
                else:  # else id smaller zoom out
                    self.safeScale(yf - self._y0)
                # end else
        # end if
    # end def

    def _resetScale(self):
        """reset the scale to 1"""
        # use the transform value if you want to get how much the view
        # has been scaled
        self._scale_size = self.transform().m11()

        # self._scale_limit_min = 0.41*self._scale_size
        # make it so fitting in view is zoomed minimum
        # still gives you one zoom level out before violates limit
        self._scale_limit_min = self._scale_size*self._scale_fit_factor

        # use this if you want to reset the zoom in limit
        # self._scale_limit_max = 3.0*self._scale_size

        self._last_scale_factor = 0.0
    # end def

    def zoomToFit(self):
        # print("zoom to fit", self._name)
        # Auto zoom to center the scene
        thescene = self.scene_root_item.scene()
        # order matters?
        self.scene_root_item.resetTransform() # zero out translations
        self.resetTransform() # zero out scaling
        if self.toolbar:  # HACK: move toolbar so it doesn't affect sceneRect
            self.toolbar.setPos(0, 0)
        thescene.setSceneRect(thescene.itemsBoundingRect())
        scene_rect = thescene.sceneRect()
        if self.toolbar:  # HACK, pt2: move toolbar back
            self.toolbar.setPos(self.mapToScene(0, 0))
        self.fitInView(scene_rect, Qt.KeepAspectRatio) # fit in view
        self._resetScale() # adjust scaling so that translation works
        # adjust scaling so that the items don't fill 100% of the view
        # this is good for selection
        self.scale(self._scale_fit_factor, self._scale_fit_factor)
        self._scale_size *= self._scale_fit_factor
        self._resetLOD()
    # end def

    def paintEvent(self, event):
        if self.toolbar:
            self.toolbar.setPos(self.mapToScene(0, 0))
        QGraphicsView.paintEvent(self, event)
#end class
