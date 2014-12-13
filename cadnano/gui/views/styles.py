import cadnano.util as util
from PyQt5.QtGui import QColor

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
