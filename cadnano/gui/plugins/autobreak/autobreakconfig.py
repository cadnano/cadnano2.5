# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

"""
config
Created by Jonathan deWerd on 2012-01-19.
"""
import util, cadnano
import autobreakconfig_ui
import autobreak
util.qtWrapImport('QtGui', globals(), ['QDialog', 'QKeySequence', 'QDialogButtonBox'])
util.qtWrapImport('QtCore', globals(), ['Qt'])

class AutobreakConfig(QDialog, autobreakconfig_ui.Ui_Dialog):
    def __init__(self, parent, handler):
        QDialog.__init__(self, parent, Qt.Sheet)
        self.setupUi(self)
        self.handler = handler
        fb = self.buttonBox.button(QDialogButtonBox.Cancel)
        fb.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_R ))

    def keyPressEvent(self, e):
        return QDialog.keyPressEvent(self, e)

    def closeDialog(self):
        self.close()

    def accept(self):
        part = self.handler.doc.controller().activePart()
        if part != None:
            settings = {\
                'stapleScorer'    : autobreak.tgtLengthStapleScorer,\
                'minStapleLegLen' : self.minLegLengthSpinBox.value(),\
                'minStapleLen'    : self.minLengthSpinBox.value(),\
                'maxStapleLen'    : self.maxLengthSpinBox.value(),\
            }
            self.handler.win.path_graphics_view.setViewportUpdateOn(False)
            # print "pre verify"
            # part.verifyOligos()
            # print "breakStaples"
            autobreak.breakStaples(part, settings)
            # print "post break verify"
            # part.verifyOligos()
            self.handler.win.path_graphics_view.setViewportUpdateOn(True)
        self.close()
