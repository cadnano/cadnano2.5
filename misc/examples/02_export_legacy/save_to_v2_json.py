#!/usr/bin/env python3
# bare_bones_example.py
# Shawn M Douglas, April 2017
# BSD-3 open-source license
# Run from terminal: python3 print_info.py
# Reads a design, prints oligo info, then some strand info.
# No sequence gets applied, so oligo.sequence() should return None.

import cadnano
from cadnano.document import Document

# Read design
app = cadnano.app()
doc = app.document = Document()
doc.readFile('design02.json')
part = doc.activePart()

doc.writeToFile('export.json')
doc.writeToFile('legacy.json', legacy=True)
