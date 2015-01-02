from PyQt5.QtGui import QColor

from cadnano import util

# Additional Prefs
PREF_AUTOSCAF_INDEX = 0
PREF_STARTUP_TOOL_INDEX = 0
PREF_ZOOM_SPEED = 20#50
PREF_ZOOM_AFTER_HELIX_ADD = True
PREF_SHOW_ICON_LABELS = True

THE_FONT = None
THE_FONT_SIZE = None
if util.isMac():
    THE_FONT = "Times"
    THE_FONT = "Arial"
    THE_FONT_SIZE = 10
elif util.isWindows():
    THE_FONT = "Segoe UI"
    THE_FONT = "Calibri"
    THE_FONT = "Arial"
    THE_FONT_SIZE = 9
else: # linux
    THE_FONT = "DejaVu Sans"
    THE_FONT_SIZE = 9

BLUE_FILL = QColor(153, 204, 255)  # 99ccff
BLUE_STROKE = QColor(0, 102, 204)  # 0066cc
BLUISH_STROKE = QColor(0, 182, 250)  # 
ORANGE_FILL = QColor(255, 204, 153)  # ffcc99
ORANGE_STROKE = QColor(204, 102, 51)  # cc6633
LIGHT_ORANGE_FILL = QColor(255, 234, 183)
LIGHT_ORANGE_STROKE = QColor(234, 132, 81)
GRAY_FILL = QColor(238, 238, 238)  # eeeeee (was a1a1a1)
GRAY_STROKE = QColor(102, 102, 102)  # 666666 (was 424242)


# PARTCOLORS = [QColor() for i in range(12)]
# for i in range(len(PARTCOLORS)):
#     PARTCOLORS[i].setHsvF(i/12.0, 0.75, 1.0)
QUALITATIVE_PAIRED_N12 = [QColor(166,206,227), QColor(31,120,180), QColor(178,223,138),
                          QColor(51,160,44), QColor(251,154,153), QColor(227,26,28),
                          QColor(253,191,111), QColor(255,127,0), QColor(202,178,214),
                          QColor(106,61,154), QColor(255,255,153), QColor(177,89,40)]
QUALITATIVE_PAIRED_N10 =  [QColor(166,206,227),
                           QColor(31,120,180),
                           QColor(178,223,138),
                           QColor(51,160,44),
                           QColor(251,154,153),
                           QColor(227,26,28),
                           QColor(253,191,111),
                           QColor(255,127,0),
                           QColor(202,178,214),
                           QColor(106,61,154)]
CADNANO1_COLORS = [QColor(204, 0, 0),
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

PARTCOLORS = CADNANO1_COLORS
