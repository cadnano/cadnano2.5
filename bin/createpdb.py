import sys
import os
from na2pdb import AtomicSequence

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from cadnano.fileio import nnodecode

BASE_LENGTH = 0.3

if __name__ == "__main__":

    test1 = 'super_barcode_hex.json'
    test2 = 'Nature09_squarenut.json'

    path_out = 'Nature09_squarenut.pdb'

    root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    test_path = os.path.join(root_path, 'tests', test1)
    doc = nnodecode.decodeFile(test_path)

    solids = []
    part = doc.children()[0]
    # print(part.radius())
    radius = part.radius() + 0.1
    aseq = None
    offset = 0
    i = 0
    for oligo in part.oligos():
        oseq = oligo.sequence()
        if oseq is None:
            aseq = AtomicSequence("A"*oligo.length())
        else:
            aseq = AtomicSequence(oseq)
        strand5p = oligo.strand5p()
        offset = 0
        for strand in strand5p.generator3pStrand():
            idx_low, idx_high = strand.idxs()
            length = strand.length()

            vh = strand.virtualHelix()
            # z,y = part.latticeCoordToPositionXY(*vh.coord())
            z, y = 0, i
            i += 2
            # print(z,y)
            start = offset
            end = offset + length # non-inclusive
            delta_x = idx_low
            is5to3 = strand.isDrawn5to3()
            aseq.transformBases(start, end, delta_x, y, z, is5to3)
            # aseq.transformBases(start, end, delta_x, y, z, True)
            print(start, end, delta_x, length, offset, is5to3)
            offset += length
        break
    print("writing %s..." % (path_out))
    # 1. Get base separation
    aseq.linearize()
    # 2. do all rotations
    aseq.applyReverseQueue()
    aseq.applyTwist()
    # 3. move to position
    aseq.applyTransformQueue()
    aseq.toPDB(path_out)