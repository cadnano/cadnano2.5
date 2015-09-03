import sys
import os
from na2pdb import AtomicSequence
import math

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from cadnano.fileio import nnodecode

BASE_LENGTH = 0.3

# 90 degrees from vertical so bases are pointing at 0 degrees when viewed from the 5' end
THETA0 = 3*math.pi/2

if __name__ == "__main__":

    test1 = 'super_barcode_hex.json'
    test2 = 'Nature09_squarenut.json'

    path_out = 'Nature09_squarenut.pdb'

    root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    test_path = os.path.join(root_path, 'tests', test1)
    doc = nnodecode.decodeFile(test_path)
    ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    aseq_list = []
    part = doc.children()[0]
    # print(part.radius())
    radius = part.radius() + 0.1
    aseq = None
    offset = 0
    i = 0
    for oligo in part.oligos():
        oseq = oligo.sequence()
        print("o lenght", oligo.length())
        if oseq is None:
            aseq = AtomicSequence("A"*oligo.length(), theta_offset=THETA0)
        else:
            aseq = AtomicSequence(oseq, theta_offset=THETA0)
        strand5p = oligo.strand5p()
        offset = 0
        for strand in strand5p.generator3pStrand():
            idx_low, idx_high = strand.idxs()
            length = strand.length()

            vh = strand.virtualHelix()
            z,y = part.latticeCoordToPositionXY(*vh.coord(), normalize=True)
            # z, y = 0, i
            # print("z, y:", z,y, vh.coord())
            start = offset
            end = offset + length # non-inclusive
            delta_x = idx_low
            is5to3 = strand.isDrawn5to3()
            aseq.transformBases(start, end, delta_x, y, -z, is5to3)
            # aseq.transformBases(start, end, delta_x, y, z, True)
            print(start, end, delta_x, length, offset, is5to3)
            offset += length
        # end for
        # 1. Get base separation
        aseq.linearize()
        # 2. do all rotations
        aseq.applyReverseQueue()
        aseq.applyTwist()
        # 3. move to position
        aseq.applyTransformQueue()

        aseq.setChainID(ALPHABET[i])
        aseq_list.append(aseq)
        i += 1
        if i == 10:
            break
    # end for
    # concatenate all sequences:
    aseq_out = aseq_list[0]
    # print("length", len(aseq_list))
    # print(aseq_list)
    for aseq in aseq_list[1:]:
        print(aseq_out, aseq)
        aseq_out.concat(aseq)
    print("writing %s..." % (path_out))
    aseq_out.toPDB(path_out)
    
    # filepath, ext = os.path.splitext(path_out)
    # for i, aseq in enumerate(aseq_list):
    #     pout = filepath + "%d" % (i) + ext
    #     print("writing %s..." % (pout))
    #     aseq.toPDB(pout)
