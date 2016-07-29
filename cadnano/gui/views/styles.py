# -*- coding: utf-8 -*-
from cadnano import util

# Additional Prefs
PREF_GRID_APPEARANCE_TYPE_INDEX = 1
PREF_ZOOM_SPEED = 20
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
else:  # linux
    THE_FONT = "DejaVu Sans"
    THE_FONT_SIZE = 9

BLUE_FILL = '#99ccff'
BLUE_STROKE = '#0066cc'
# BLUISH_STROKE = '#00b6fa'
# ORANGE_FILL = '#ffcc99'
# ORANGE_STROKE = '#cc6633'
# PINK_STROKE = '#cc6633'
# LIGHT_ORANGE_FILL = '#ffeab7'
# LIGHT_ORANGE_STROKE = '#ea8451'
GRAY_FILL = '#eeeeee'  # (was #a1a1a1)
# MIDGRAY_FILL = '#9a9a9a'
GRAY_STROKE = '#666666'  # (was 424242)


# PARTCOLORS = [QColor() for i in range(12)]
# for i in range(len(PARTCOLORS)):
#     PARTCOLORS[i].setHsvF(i/12.0, 0.75, 1.0)
# QUALITATIVE_PAIRED_N12 = ['#6acee3',
#                           '#1f78b4',
#                           '#b2df8a',
#                           '#33a02c',
#                           '#fb9a99',
#                           '#e31a1c',
#                           '#fdbf6f',
#                           '#ff7f00',
#                           '#cab2d6',
#                           '#6a3d9a',
#                           '#ffff99',
#                           '#b15928']
# QUALITATIVE_PAIRED_N10 =  ['#6acee3',
#                            '#1f78b4',
#                            '#b2df8a',
#                            '#33a02c',
#                            '#fb9a99',
#                            '#e31a1c',
#                            '#fdbf6f',
#                            '#ff7f00',
#                            '#cab2d6',
#                            '#6a3d9a']
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
