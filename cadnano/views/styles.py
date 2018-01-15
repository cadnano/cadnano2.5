# -*- coding: utf-8 -*-
from PyQt5.QtGui import QFont
from cadnano import util

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
else:  # linux
    THE_FONT = "DejaVu Sans"
    THE_FONT_SIZE = 9

VIEW_BG_COLOR = '#f6f6f6'

BLUE_FILL = '#99ccff'
BLUE_STROKE = '#0066cc'
# BLUISH_STROKE = '#00b6fa'
ORANGE_FILL = '#ffcc99'
ORANGE_STROKE = '#cc6633'
# PINK_STROKE = '#cc00cc'
# LIGHT_ORANGE_FILL = '#ffeab7'
# LIGHT_ORANGE_STROKE = '#ea8451'
GRAY_FILL = '#eeeeee'  # (was #a1a1a1)
# MIDGRAY_FILL = '#9a9a9a'
GRAY_STROKE = '#666666'  # (was 424242)
BLACK_STROKE = '#000000'

CADNANO1_COLORS = ['#cc0000',
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

PARTCOLORS = CADNANO1_COLORS

RESIZEHANDLE_FILL_COLOR = '#ffffff'
RESIZEHANDLE_LABEL_COLOR = '#666666'
RESIZEHANDLE_LABEL_FONT = QFont(THE_FONT, THE_FONT_SIZE, QFont.Light)
