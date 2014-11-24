from cadnano.gui.views.styles import *
from PyQt5.QtGui import QColor, QFont, QFontMetricsF

# Path Sizing
VIRTUALHELIXHANDLEITEM_RADIUS = 30
VIRTUALHELIXHANDLEITEM_STROKE_WIDTH = 2
PATH_BASE_WIDTH = 20  # used to size bases (grid squares, handles, etc)
PATH_HELIX_HEIGHT = 2 * PATH_BASE_WIDTH  # staple + scaffold
PATH_HELIX_PADDING = 50 # gap between PathHelix objects in path view
PATH_GRID_STROKE_WIDTH = 0.5
SLICE_HANDLE_STROKE_WIDTH = 1
PATH_STRAND_STROKE_WIDTH = 3
PATH_STRAND_HIGHLIGHT_STROKE_WIDTH = 8
PATH_SELECTBOX_STROKE_WIDTH = 1.5
PCH_BORDER_PADDING = 1
PATH_BASE_HL_STROKE_WIDTH = 2  # PathTool highlight box
MINOR_GRID_STROKE_WIDTH = 0.5
MAJOR_GRID_STROKE_WIDTH = 0.5
OLIGO_LEN_BELOW_WHICH_HIGHLIGHT = 20
OLIGO_LEN_ABOVE_WHICH_HIGHLIGHT = 49

# Path Drawing
PATH_XOVER_LINE_SCALE_X = 0.035
PATH_XOVER_LINE_SCALE_Y = 0.035

# Path Colors
SCAFFOLD_BKG_FILL = QColor(230, 230, 230)
ACTIVE_SLICE_HANDLE_FILL = QColor(255, 204, 153, 128)  # ffcc99
ACTIVE_SLICE_HANDLE_STROKE = QColor(204, 102, 51, 128)  # cc6633
MINOR_GRID_STROKE = QColor(204, 204, 204)  # 999999
MAJOR_GRID_STROKE = QColor(153, 153, 153)  # 333333
SCAF_STROKE = QColor(0, 102, 204)  # 0066cc
HANDLE_FILL = QColor(0, 102, 204)  # 0066cc
PXI_SCAF_STROKE = QColor(0, 102, 204, 153)
PXI_STAP_STROKE = QColor(204, 0, 0, 153)
PXI_DISAB_STROKE = QColor(204, 204, 204, 255)
RED_STROKE = QColor(204, 0, 0)
ERASE_FILL = QColor(204, 0, 0, 63)
FORCE_FILL = QColor(0, 255, 255, 63)
BREAK_FILL = QColor(204, 0, 0, 255)
COLORBOX_FILL = QColor(204, 0, 0)
COLORBOX_STROKE = QColor(102, 102, 102)
STAP_COLORS = [QColor(204, 0, 0),
              QColor(247, 67, 8),
              QColor(247, 147, 30),
              QColor(170, 170, 0),
              QColor(87, 187, 0),
              QColor(0, 114, 0),
              QColor(3, 182, 162),
              QColor(23, 0, 222),
              QColor(115, 0, 222),
              QColor(184, 5, 108),
              QColor(51, 51, 51),
              QColor(136, 136, 136)]
SCAF_COLORS = [QColor(0, 102, 204)]
              # QColor(64, 138, 212),
              # QColor(0, 38, 76),
              # QColor(23, 50, 76),
              # QColor(0, 76, 153)]
DEFAULT_STAP_COLOR = "#888888"
DEFAULT_SCAF_COLOR = "#0066cc"
SELECTED_COLOR = QColor(255, 51, 51)

# brightColors = [QColor() for i in range(10)]
# for i in range(len(brightColors)):
#     brightColors[i].setHsvF(i/12.0, 1.0, 1.0)
# bright_palette = Palette(brightColors)
# cadnn1_palette = Palette(cadnn1Colors)
# default_palette = cadnn1_palette

SELECTIONBOX_PEN_WIDTH = 2.5

# Loop/Insertion path details
INSERTWIDTH = 2
SKIPWIDTH = 2

# Add Sequence Tool
INVALID_DNA_COLOR = QColor(204, 0, 0)
UNDERLINE_INVALID_DNA = True

#Z values
#bottom
ZACTIVESLICEHANDLE = 10
ZPATHHELIXGROUP = 20
ZPATHHELIX = 30
ZPATHSELECTION = 40

ZXOVERITEM = 90

ZPATHTOOL = 130
ZSTRANDITEM = 140
ZENDPOINTITEM = 150
ZINSERTHANDLE = 160
#top

# sequence stuff Font stuff
SEQUENCEFONT = None
SEQUENCEFONTH = 15
SEQUENCEFONTCHARWIDTH = 12
SEQUENCEFONTCHARHEIGHT = 12
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
    SEQUENCEFONTCHARHEIGHT = SEQUENCEFONTMETRICS.height()
    SEQUENCEFONTEXTRAWIDTH = PATH_BASE_WIDTH - SEQUENCEFONTCHARWIDTH
    SEQUENCEFONT.setLetterSpacing(QFont.AbsoluteSpacing,
                                 SEQUENCEFONTEXTRAWIDTH)
    SEQUENCETEXTXCENTERINGOFFSET = SEQUENCEFONTEXTRAWIDTH / 4.
    SEQUENCETEXTYCENTERINGOFFSET = PATH_BASE_WIDTH * 0.6
#end def

XOVER_LABEL_FONT = QFont(THE_FONT, THE_FONT_SIZE, QFont.Bold)
VIRTUALHELIXHANDLEITEM_FONT = QFont(THE_FONT, 3*THE_FONT_SIZE, QFont.Bold)
XOVER_LABEL_COLOR = QColor(0,0,0) 