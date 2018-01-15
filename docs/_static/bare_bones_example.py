#!/usr/bin/env python3
# bare_bones_example.py
# Shawn M Douglas, April 2017
# BSD-3 open-source license

import cadnano
from cadnano.document import Document

app = cadnano.app()
doc = app.document = Document()
doc.readFile('myfile.json')
part = doc.activePart()

oligos = part.oligos()
for oligo in oligos:
    print("{0}\t{1}\t\'{2}\'\t{3}".format(oligo,
                                          oligo.length(),
                                          oligo.getColor(),
                                          oligo.sequence()))

vhs = list(part.getIdNums())  # convert set to list
for vh_id in vhs[:3]:         # display first 3 vhs
    fwd_ss, rev_ss = part.getStrandSets(vh_id)
    print('VH{0}'.format(vh_id))
    print('\t', fwd_ss, '\t', [s.idxs() for s in fwd_ss.strands()], '\n\t\t\t\t',
          [s.getColor() for s in fwd_ss.strands()])
    print('\t', rev_ss, '\t', [s.idxs() for s in rev_ss.strands()], '\n\t\t\t\t',
          [s.getColor() for s in rev_ss.strands()])
