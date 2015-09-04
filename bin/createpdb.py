import sys
import os
from na2pdb import AtomicSequence
import math
import random

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from cadnano.fileio import nnodecode

BASE_LENGTH = 0.3

# 90 degrees from vertical so bases are pointing at 0 degrees when viewed from the 5' end
THETA0 = 3*math.pi/2

if __name__ == "__main__":

    test1 = 'super_barcode_hex.json'
    test2 = 'Nature09_squarenut.json'
    test2 = 'monolith.json'

    dir_out = 'file_test'
    path_out = 'Nature09_squarenut'

    root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    test_path = os.path.join(root_path, 'tests', test2)
    doc = nnodecode.decodeFile(test_path)
    ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    aseq_list = []
    part = doc.children()[0]
    # print(part.radius())
    radius = part.radius() + 0.1
    aseq = None
    offset = 0
    i = 0
    oligo_list = part.oligos()
    for oligo in oligo_list:
        oseq = oligo.sequence()
        olen = oligo.length()
        print("o length", olen)
        # if olen < 60:
        #     print("skipping", olen)
        #     continue
        if oseq is None:
            oseq = "".join(random.choice("ACGT") for x in range(olen))
        aseq = AtomicSequence(oseq, theta_offset=THETA0)
        strand5p = oligo.strand5p()
        offset = 0
        for strand in strand5p.generator3pStrand():
            idx_low, idx_high = strand.idxs()
            length = strand.length()

            vh = strand.virtualHelix()
            z,y = part.latticeCoordToPositionXY(*vh.coord(), normalize=True)
            # print("z, y:", z,y, vh.coord())
            start = offset
            end = offset + length # non-inclusive
            delta_x = idx_low
            is5to3 = strand.isDrawn5to3()
            aseq.transformBases(start, end, delta_x, y, -z, is5to3)
            # print(start, end, delta_x, length, offset, is5to3)
            offset += length
        # end for
        # 1. Get base separation
        aseq.linearize()
        # 2. do all rotations
        aseq.applyReverseQueue()
        aseq.applyTwist()
        # 3. move to position
        aseq.applyTransformQueue()

        aseq.setChainID(ALPHABET[i % 25])
        aseq_list.append(aseq)
        i += 1
    # end for

    # concatenate all sequences:
    # aseq_out = aseq_list[0]
    # print("length", len(aseq_list))
    # print(aseq_list)
    # for aseq in aseq_list[1:]:
    #     print(aseq_out, aseq)
    #     aseq_out.concat(aseq)
    # print("writing %s..." % (path_out))
    # aseq_out.toPDB(path_out)
    
    # create a separate file for each oligo
    file_path = os.path.join(os.getcwd(), path_out)
    try:
        os.mkdir(file_path)
    except:
        pass
    for i, aseq in enumerate(aseq_list):
        # pout = os.path.join(file_path, path_out + "%0.3d" % (i) + '.cif')
        pout = os.path.join(file_path, path_out + "%0.3d" % (i) + '.pdb')
        print("writing %s..." % (pout))
        # aseq.toMMCIF(pout)
        aseq.toPDB(pout)
