#!/usr/bin/env python3
# bare_bones_example.py
# Shawn M Douglas, April 2017
# BSD-3 open-source license
# Run from terminal: python3 print_info.py
# Reads a design, prints oligo info, then some strand info.
# No sequence gets applied, so oligo.sequence() should return None.

import cadnano
from cadnano.document import Document

# design_name = 'a'
# design_name = 'b'
design_name = 'Nature09_monolith'

# Read design
app = cadnano.app()
doc = app.document = Document()
doc.readFile(design_name + '.json')
part = doc.activePart()

doc.writeToFile(design_name + '_c25.json')
doc.writeToFile(design_name + '_legacy.json', legacy=True)
