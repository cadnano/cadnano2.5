#!/usr/bin/env python3
# export_legacy_json.py
# Shawn M Douglas, April 2017
# BSD-3 open-source license

import argparse
from datetime import datetime
from os import path
import sys
from termcolor import colored

import cadnano
from cadnano.document import Document
from cadnano.data.dnasequences import sequences


def colorBool(b):
    if b:
        return colored(b, 'green')
    else:
        return colored(b, 'red', attrs=['reverse'])


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Convert cadnano2.5 file into legacy json format, if possible.')
parser.add_argument("-i", "--input", help="source cadnano file", metavar='FILENAME', required=True)
parser.add_argument("-o", "--output", help="destination json file", metavar='FILENAME')
args = parser.parse_args()

# Check input file exists
src_file = args.input
if not path.exists(src_file):
    sys.exit("Input file {0} not found".format(src_file))

# Determine output filename
if args.output:
    dest_file = args.output
else:
    # Use a timestamped derivative of input filename
    timestamp = "{:%y%m%d.%H%M%S}".format(datetime.now())
    src_ext = path.splitext(src_file)
    dest_file = '.'.join([src_ext[0], timestamp, 'json'])

if (src_file == dest_file):
    sys.exit("Please choose an output that doesn't match the input filename")

print("Reading {0}, will export to {1}".format(colored(src_file, 'yellow'),
                                               colored(dest_file, 'yellow')))

# Basic init
app = cadnano.app()
doc = app.document = Document()

# Read input design
doc.readFile(src_file)
part = doc.activePart()
oligos = part.oligos()

# We want to perform some operations on the scaffold and staples.
# First, we need references to the corresponding oligos within the data model.

# We can just hard-code a location we know is in the scaffold
start_vh = 0
start_strandset = 0  # 0 is forward (drawn 5->3 on top), 1 is reverse (3'<-5' on bottom)
start_idx = 22
scaf_start = (start_vh, start_strandset, start_idx)
scaf_oligo = part.getOligoAt(*scaf_start)  # unpack the tuple with *

# For fun we might guess that the scaffold is simply the longest oligo
oligos_sorted_by_length = sorted(oligos, key=lambda x: x.length(), reverse=True)
longest_oligo = oligos_sorted_by_length[0]
staple_oligos = oligos_sorted_by_length[1:]
print("> Does the longest oligo contain %s?" % str(scaf_start), 'green',
      colorBool(longest_oligo == scaf_oligo))

# print(scaffold, scaffold.length(), scaffold.sequence())
p7560 = sequences['p7560']

# for staple in staple_oligos:
#     print(staple, staple.dump())

# circular_oligos = part.getCircularOligos()
# if circular_oligos:
#     print("Warning: cannot export circular oligos:")
#     for circ_oligo in circular_oligos:
#         print("\t", circ_oligo.dump())
#     sys.exit("Please break these oligos before proceeding.")

# for staple in staples:
#     if staple.isCircular():
#         print(staple)
#         for strand in staple.strand5p().generator3pStrand():
#             print ("\t", strand, strand.idxs(), strand.length())

# print(staple, staple.dump())

# split


# break every staple at midpoint

# print staples

# save modified file

# part.getSequences()


