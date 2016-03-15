import unittest
import sys
from os.path import join, abspath, dirname
import math

LOCAL_DIR = abspath(dirname(__file__))
sys.path.append(abspath(join(LOCAL_DIR, '..')))

from cadnano.document import Document
from cadnano.part.nucleicacidpart import NucleicAcidPart

doc = Document()
part = NucleicAcidPart(document=doc)
radius = part.radius()
origin_pt0 = (0, 0, 0)
origin_pt90 = (0, 2*radius, 0)
theta = math.radians(30)
origin_pt60 = (2*radius*math.cos(-theta), 2*radius*math.sin(-theta), 0)
color = part.getColor()
part.createHelix(0, origin_pt0, (0, 0, 1), 42, color)
part.createHelix(1, origin_pt90, (0, 0, 1), 42, color)
part.createHelix(2, origin_pt60, (0, 0, 1), 42, color)

pcm0 = part.potentialCrossoverMap(0)
pcm1 = part.potentialCrossoverMap(1)
pcm2 = part.potentialCrossoverMap(2)

if True:
    print("0 Forward hits to 1 VHelix:", [x for x, y, z in pcm0[1][0]])
    print("1 Reverse hits to 0 VHelix:", [x for x, y, z in pcm1[0][1]])
    # print("0 Forward hits to 2 VHelix:", [x for x, y, z in pcm0[2][0]])
    # print("2 Reverse hits to 0 VHelix:", [x for x, y, z in pcm2[0][1]])

    print("0 Reverse hits to 1 VHelix:", [x for x, y, z in pcm0[1][1]])
    print("1 Forward hits to 0 VHelix:", [x for x, y, z in pcm1[0][0]])
    # print("0 Reverse hits to 2 VHelix:", [x for x, y, z in pcm0[2][1]])
    # print("2 Forward hits to 0 VHelix:", [x for x, y, z in pcm2[0][0]])
# if False:
    print("0 Reverse hits to 1 fwd strand:", set([tuple(y) for x, y, z in pcm0[1][1]]))
    print("1 Forward hits to 0 rev strand:", set([tuple(z) for x, y, z in pcm1[0][0]]))

    print("1 Reverse hits to 0 fwd strand:", set([tuple(y) for x, y, z in pcm1[0][1]]))
    print("1 Reverse hits to 0 rev strand:", set([tuple(z) for x, y, z in pcm1[0][1]]))

    # print("0 Reverse hits to 2 fwd strand:", set([tuple(y) for x, y, z in pcm0[2][1]]))
    # print("2 Forward hits to 0 rev strand:", set([tuple(z) for x, y, z in pcm2[0][0]]))

    print("0 Reverse hits to 1 rev strand:", set([tuple(z) for x, y, z in pcm0[1][1]]))
    print("1 Forward hits to 0 fwd strand:", set([tuple(y) for x, y, z in pcm1[0][0]]))

    # print("0 Reverse hits to 2 rev strand:", set([tuple(z) for x, y, z in pcm0[2][1]]))
    # print("2 Forward hits to 0 fwd strand:", set([tuple(y) for x, y, z in pcm2[0][0]]))

    # fwds = [tuple(y) for x, y, z in pcm[0][1]]
    # print("1 Reverse hits to 0 fwd strand:", set(fwds))

if False:
    angleRangeCheck = NucleicAcidPart.angleRangeCheck

    # tests in degrees
    angle_tests = [ (0, 0, 30),
                    (15, 0, 30),
                    (30, 0, 30),
                    (31, 0, 30),
                    (330, 0, 30),
                    (340, 0, 30),
                    (329, 0, 30),
                    (350, 15, 30),
                    (180, 170, 30),
                    (181, 170, 30),
                    (201, 170, 30),
    ]


    for atest in angle_tests:
        radtest = tuple(map(math.radians, atest))
        print("%0.2f in range %0.2f +/- %0.2f" % atest,
                angleRangeCheck(*radtest))