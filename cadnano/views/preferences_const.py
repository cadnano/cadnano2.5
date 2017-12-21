class PreferencesConst(object):
    PREFERENCES = 'Preferences'
    GRID_APPEARANCE_TYPE_INDEX = 'grid_appearance_type_index'
    SLICE_APPEARANCE_TYPE_INDEX = 'slice_appearance_type_index'

    ZOOM_SPEED = 'zoom_speed'
    UI_ICONS_LABELS = 'ui_icons_labels'

    # Slice Views
    LEGACY = 'legacy'
    GRID = 'grid'
    DUAL = 'dual'

    SLICE_SIGNAL_KEY = 'slice'
    SLICE_VIEWS = (LEGACY, GRID, DUAL)

    # Grid Views
    POINTS = 'points'
    LINES_AND_POINTS = 'lines and points'
    CIRCLES = 'circles'

    GRID_SIGNAL_KEY = 'grid'
    GRID_VIEWS = (POINTS, LINES_AND_POINTS)
