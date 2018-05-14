# -*- coding: utf-8 -*-
import os

from cadnano import app

from cadnano.cntypes import (
    DocT
)

class DocumentController(object):
    '''Connects UI buttons to their corresponding actions in the model.'''
    '''list: String names of enabled filter types.'''

    ### INIT METHODS ###

    def __init__(self, document_item, document: DocT):
        ''''''
        # initialize variables
        self._document_item = document_item
        self._document = document
        self._document.setController(self)

        self.self_signals = []

        # call other init methods
        app().document_controllers.add(self)
    # end def

    def destroyDC(self):
        self.disconnectSignalsToSelf()
        if self.win is not None:
            self.win.destroyWin()
            self.win = None
        self.settings = None
    # end def

    def disconnectSignalsToSelf(self):
        win = self.win
        if win is not None:
            o = win.outliner_widget
            p_e = win.property_widget
            o.itemSelectionChanged.disconnect(p_e.outlinerItemSelectionChanged)
        for signal_obj, slot_method in self.self_signals:
            signal_obj.disconnect(slot_method)
        self.self_signals = []
    # end def

    def _connectWindowSignalsToSelf(self):
        '''This method serves to group all the signal & slot connections
        made by DocumentController'''
        win = self.win
        self.self_signals = [
            (win.action_new.triggered, self.actionNewSlot),
            (win.action_open.triggered, self.actionOpenSlot),
            (win.action_close.triggered, self.actionCloseSlot),
            (win.action_save.triggered, self.actionSaveSlot),
            (win.action_save_as.triggered, self.actionSaveAsSlot),
            (win.action_SVG.triggered, self.actionSVGSlot),
            (win.action_export_staples.triggered, self.actionExportSequencesSlot),
            (win.action_preferences.triggered, self.actionPrefsSlot),
            (win.action_new_dnapart_honeycomb.triggered, self.actionCreateNucleicAcidPartHoneycomb),
            (win.action_new_dnapart_honeycomb.triggered, lambda: win.action_global_create.trigger()),
            (win.action_new_dnapart_square.triggered, self.actionCreateNucleicAcidPartSquare),
            (win.action_new_dnapart_square.triggered, lambda: win.action_global_create.trigger()),
            (win.action_about.triggered, self.actionAboutSlot),
            (win.action_cadnano_website.triggered, self.actionCadnanoWebsiteSlot),
            (win.action_feedback.triggered, self.actionFeedbackSlot),

            # make it so select tool in slice view activation turns on vh filter
            (win.action_global_select.triggered, self.actionSelectForkSlot),
            (win.action_global_create.triggered, self.actionCreateForkSlot),

            (win.action_filter_helix.triggered, self.actionFilterVirtualHelixSlot),
            (win.action_filter_endpoint.triggered, self.actionFilterEndpointSlot),
            (win.action_filter_strand.triggered, self.actionFilterStrandSlot),
            (win.action_filter_xover.triggered, self.actionFilterXoverSlot),
            (win.action_filter_fwd.triggered, self.actionFilterFwdSlot),
            (win.action_filter_rev.triggered, self.actionFilterRevSlot),
            (win.action_filter_scaf.triggered, self.actionFilterScafSlot),
            (win.action_filter_stap.triggered, self.actionFilterStapSlot),
            (win.action_copy.triggered, self.actionCopySlot),
            (win.action_paste.triggered, self.actionPasteSlot),

            (win.action_inspector.triggered, self.actionToggleInspectorViewSlot),
            (win.action_path.triggered, self.actionTogglePathViewSlot),
            (win.action_slice.triggered, self.actionToggleSliceViewSlot),

            (win.action_path_add_seq.triggered, self.actionPathAddSeqSlot),

            (win.action_vhelix_snap.triggered, self.actionVhelixSnapSlot)
        ]
        for signal_obj, slot_method in self.self_signals:
            signal_obj.connect(slot_method)

        # NOTE ADDED NC TO GET PROPER SLICE VIEW BEHAVIOR checking of slice view
        # box not preserved for some reason
        win.action_slice.setChecked(True)
        self.actionToggleSliceViewSlot()
    # end def

    ### SLOTS ###
