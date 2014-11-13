import sys
import os
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from cadnano.fileio import nnodecode
from nno2stl import stlwriter
from nno2stl.cylinder import Cylinder

from nno2stl.halfcylinder import HalfCylinder

from nno2stl.matrix4 import makeTranslation

BASE_LENGTH = 0.3

if __name__ == "__main__":

    test1 = 'super_barcode_hex.json'
    test2 = 'Nature09_squarenut.json'

    path_out = 'Nature09_squarenut.stl'
 
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    test_path = os.path.join(root_path, 'tests', test2)
    doc = nnodecode.decodeFile(test_path)

    solids = []
    part = doc.parts()[0]
    # print(part.radius())
    radius = part.radius() + 0.1
    # for coord, vh in part.iterVHs():
    #     x,y = part.latticeCoordToPositionXY(*coord)
    #     m4 = makeTranslation(x, y, 0)
    #     cylinder = Cylinder("%s" % str(coord), radius, 10)
    #     cylinder.applyMatrix(m4)
    #     solids.append(cylinder)     
    for oligo in part.oligos():
        if not oligo.isStaple():
            strand5p = oligo.strand5p()
            for strand in strand5p.generator3pStrand():
                length = BASE_LENGTH*strand.length()

                idx_low, idx_high = strand.idxs()
                z = BASE_LENGTH*((idx_high + idx_low) / 2.0)

                vh = strand.virtualHelix()
                x,y = part.latticeCoordToPositionXY(*vh.coord())
                m4 = makeTranslation(x, y, z)
                cylinder = Cylinder("%s" % str(vh.coord()), radius, length)
                # cylinder = HalfCylinder("%s" % str(vh.coord()), 
                #         radius, length, strand.length(),
                #         twist_per_segment=part._twist_per_base)
                cylinder.applyMatrix(m4)
                solids.append(cylinder)
                print("length:", strand.length())
    # stlwriter.write(path_out, solids, format="ascii")
    print("writing %s..." % (path_out))
    stlwriter.write(path_out, solids, format="binary") 