import json
# from .legacydecoder import import_legacy_dict
from .legacydecoder import import_legacy_dict

from cadnano.gui.ui.dialogs.ui_latticetype import Ui_LatticeType
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

def decode(document, string):
    # from ui.dialogs.ui_latticetype import Ui_LatticeType
    # util.qtWrapImport('QtGui', globals(),  ['QDialog', 'QDialogButtonBox'])
    dialog = QDialog()
    dialogLT = Ui_LatticeType()  # reusing this dialog, should rename
    dialogLT.setupUi(dialog)

    # try:  # try to do it fast
    #     try:
    #         import cjson
    #         packageObject = cjson.decode(string)
    #     except:  # fall back to if cjson not available or on decode error
    #         packageObject = json.loads(string)
    # except ValueError:
    #     dialogLT.label.setText("Error decoding JSON object.")
    #     dialogLT.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
    #     dialog.exec_()
    #     return
    package_object = json.loads(string)

    if package_object.get('.format', None) != 'caDNAno2':
        import_legacy_dict(document, package_object)