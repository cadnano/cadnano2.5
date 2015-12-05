from math import ceil

from PyQt5.QtGui import QValidator, QIntValidator
from PyQt5.QtWidgets import QSpinBox


class StepwiseSpinBox(QSpinBox):
    def __init__(self, min_value, max_value, step_size, parent=None):
        super(StepwiseSpinBox, self).__init__(parent)
        self.validator = StepIntValidator(0, max_value, step_size, self)
        self._step_size = step_size
        self.setSingleStep(step_size)
        self.setRange(min_value, max_value)
    # end def

    def validate(self, text, pos):
        return self.validator.validate(text, pos)
    # end def

    def fixup(self, text):
        return self.validator.fixup(text)
    # end def
# end class

class StepIntValidator(QValidator):
    def __init__(self, min_value, max_value, step_size, parent=None):
        super(StepIntValidator, self).__init__(parent=None)
        self._step_size = step_size
        self.int_validator = QIntValidator(min_value, max_value, self)
    # end def

    def validate(self, text, pos):
        # first check for valid int with QIntValidator
        is_valid_int, _text, _pos = self.int_validator.validate(text, pos)
        if is_valid_int == QValidator.Acceptable:
            modulus = int(text) % self._step_size
            if modulus == 0: # all done
                return (QValidator.Acceptable, text, pos)
            else: # will try to fixup
                return (QValidator.Intermediate, text, pos)
        else:
            # reject without fixup attempt
            return (QValidator.Invalid, text, pos)
    # end def

    def fixup(self, text):
        idx = int(text)
        return str(ceil((idx+1)/self._step_size)*self._step_size)
    # end def
# end class