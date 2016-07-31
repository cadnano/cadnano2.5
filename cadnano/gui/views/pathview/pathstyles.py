"""Summary

Attributes:
    DEFAULT_ALPHA (int): Description
    DEFAULT_BRUSH_COLOR (str): Description
    INSERTWIDTH (int): Description
    INVALID_DNA_COLOR (str): Description
    MINOR_GRID_STROKE (str): Description
    MINOR_GRID_STROKE_ACTIVE (str): Description
    MINOR_GRID_STROKE_WIDTH (float): Description
    OLIGO_LEN_ABOVE_WHICH_HIGHLIGHT (int): Description
    OLIGO_LEN_BELOW_WHICH_HIGHLIGHT (int): Description
    PATH_BASE_HL_STROKE_WIDTH (int): Description
    PATH_BASE_WIDTH (int): Description
    PATH_HELIX_HEIGHT (TYPE): Description
    PATH_HELIX_PADDING (TYPE): Description
    PATH_SELECTBOX_STROKE_WIDTH (float): Description
    PATH_STRAND_HIGHLIGHT_STROKE_WIDTH (int): Description
    PATH_STRAND_STROKE_WIDTH (int): Description
    PATH_XOVER_LINE_SCALE_X (float): Description
    PATH_XOVER_LINE_SCALE_Y (float): Description
    PREXOVER_STROKE_WIDTH (float): Description
    RED_STROKE (str): Description
    SCAF_COLORS (list): Description
    SELECTED_ALPHA (int): Description
    SELECTED_BRUSH_COLOR (str): Description
    SELECTED_COLOR (str): Description
    SELECTED_PEN_WIDTH (int): Description
    SELECTIONBOX_PEN_WIDTH (float): Description
    SEQUENCEFONT (TYPE): Description
    SEQUENCEFONTCHARWIDTH (int): Description
    SEQUENCEFONTCOLOR (str): Description
    SEQUENCEFONTEXTRAWIDTH (int): Description
    SEQUENCEFONTH (int): Description
    SEQUENCETEXTXCENTERINGOFFSET (int): Description
    SKIPWIDTH (int): Description
    STAP_COLORS (TYPE): Description
    UNDERLINE_INVALID_DNA (bool): Description
    VH_XOFFSET (TYPE): Description
    VIRTUALHELIXHANDLEITEM_FONT (TYPE): Description
    VIRTUALHELIXHANDLEITEM_RADIUS (int): Description
    VIRTUALHELIXHANDLEITEM_STROKE_WIDTH (int): Description
    XOVER_LABEL_FONT (TYPE): Description
    XOVER_LABEL_FONT_BOLD (TYPE): Description
    ZENDPOINTITEM (int): Description
    ZINSERTHANDLE (int): Description
    ZPATHHELIX (int): Description
    ZPATHSELECTION (int): Description
    ZPATHTOOL (int): Description
    ZSTRANDITEM (int): Description
    ZXOVERITEM (int): Description
"""
from PyQt5.QtGui import QFont, QFontMetricsF
from cadnano.gui.views.styles import THE_FONT, THE_FONT_SIZE
from cadnano.gui.views.styles import BLUE_FILL, BLUE_STROKE  # noqa
from cadnano.gui.views.styles import GRAY_FILL, GRAY_STROKE  # noqa

# Path Sizing
VIRTUALHELIXHANDLEITEM_RADIUS = 15
VIRTUALHELIXHANDLEITEM_STROKE_WIDTH = 1
PATH_BASE_WIDTH = 10  # used to size bases (grid squares, handles, etc)
PATH_HELIX_HEIGHT = 2 * PATH_BASE_WIDTH  # staple + scaffold
PATH_HELIX_PADDING = 3 * PATH_BASE_WIDTH  # gap between PathHelix objects in path view
PATH_STRAND_STROKE_WIDTH = 1
PATH_STRAND_HIGHLIGHT_STROKE_WIDTH = 3
PATH_SELECTBOX_STROKE_WIDTH = 0.5
PATH_BASE_HL_STROKE_WIDTH = 1  # PathTool highlight box
MINOR_GRID_STROKE_WIDTH = 0.5
OLIGO_LEN_BELOW_WHICH_HIGHLIGHT = 5
OLIGO_LEN_ABOVE_WHICH_HIGHLIGHT = 500

PREXOVER_STROKE_WIDTH = 0.5

VH_XOFFSET = VIRTUALHELIXHANDLEITEM_RADIUS*3

# Path Drawing
PATH_XOVER_LINE_SCALE_X = 0.035
PATH_XOVER_LINE_SCALE_Y = 0.035

# Path Colors
MINOR_GRID_STROKE = '#aaaaaa'
MINOR_GRID_STROKE_ACTIVE = '#cccc00'
RED_STROKE = '#cc0000'
STAP_COLORS = ['#cc0000',
               '#f74308',
               '#f7931e',
               '#aaaa00',
               '#57bb00',
               '#007200',
               '#03b6a2',
               '#1700de',
               '#7300de',
               '#b8056c',
               '#333333',
               '#888888']
SCAF_COLORS = ['#0066cc']

SELECTED_COLOR = '#ff3333'  # item color
SELECTED_BRUSH_COLOR = '#ffffff'
SELECTED_PEN_WIDTH = 2
DEFAULT_BRUSH_COLOR = '#ffffff'
SELECTED_ALPHA = 0
DEFAULT_ALPHA = 2


SELECTIONBOX_PEN_WIDTH = 2.5

# Loop/Insertion path details
INSERTWIDTH = 2
SKIPWIDTH = 2

# Add Sequence Tool
INVALID_DNA_COLOR = '#ff0000'
UNDERLINE_INVALID_DNA = True

# Z values
# bottom
ZPATHHELIX = 30
ZPATHSELECTION = 40

ZXOVERITEM = 90

ZPATHTOOL = 130
ZSTRANDITEM = 140
ZENDPOINTITEM = 150
ZINSERTHANDLE = 160
# top

# sequence stuff Font stuff
SEQUENCEFONT = None
SEQUENCEFONTCOLOR = '#666666'
SEQUENCEFONTH = 15
SEQUENCEFONTCHARWIDTH = 12
SEQUENCEFONTEXTRAWIDTH = 3
SEQUENCETEXTXCENTERINGOFFSET = 0


def setFontMetrics():
    """ Application must be running before you mess
    too much with Fonts in Qt5
    """
    global SEQUENCEFONT
    global SEQUENCEFONTMETRICS
    global SEQUENCEFONTCHARWIDTH
    global SEQUENCEFONTCHARHEIGHT
    global SEQUENCEFONTEXTRAWIDTH
    global SEQUENCETEXTXCENTERINGOFFSET
    global SEQUENCETEXTYCENTERINGOFFSET
    SEQUENCEFONT = QFont("Monaco")
    if hasattr(QFont, 'Monospace'):
        SEQUENCEFONT.setStyleHint(QFont.Monospace)
    SEQUENCEFONT.setFixedPitch(True)
    SEQUENCEFONTH = int(PATH_BASE_WIDTH / 3.)
    SEQUENCEFONT.setPixelSize(SEQUENCEFONTH)
    SEQUENCEFONTMETRICS = QFontMetricsF(SEQUENCEFONT)
    SEQUENCEFONTCHARWIDTH = SEQUENCEFONTMETRICS.width("A")
    SEQUENCEFONTEXTRAWIDTH = PATH_BASE_WIDTH - SEQUENCEFONTCHARWIDTH
    SEQUENCEFONT.setLetterSpacing(QFont.AbsoluteSpacing,
                                  SEQUENCEFONTEXTRAWIDTH)
    SEQUENCETEXTXCENTERINGOFFSET = SEQUENCEFONTEXTRAWIDTH / 3.5
    SEQUENCETEXTYCENTERINGOFFSET = PATH_BASE_WIDTH * 0.6
# end def

XOVER_LABEL_FONT = QFont(THE_FONT, THE_FONT_SIZE/2, QFont.Light)
XOVER_LABEL_FONT_BOLD = QFont(THE_FONT, THE_FONT_SIZE/2, QFont.Bold)
VIRTUALHELIXHANDLEITEM_FONT = QFont(THE_FONT, THE_FONT_SIZE, QFont.Bold)
