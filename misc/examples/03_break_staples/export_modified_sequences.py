#!/usr/bin/env python3
# export_legacy_json.py
# Shawn M Douglas, April 2017
# BSD-3 open-source license

import argparse
from datetime import datetime
from os import path
import sys
# sys.path.append(getcwd())  # temporary
import cadnano
from cadnano.document import Document
from cadnano.extras.dnasequences import sequences
# from cadnano.views.styles import CADNANO1_COLORS


try:
    from termcolor import colored
except ImportError:
    print("pip3 install termcolor")

    def colored(s, color=None, **kwargs):
        return s

OLIGO_LEN_BELOW_WHICH_HIGHLIGHT = 20


def main():
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

    printInfo("Splitting circular oligos...")
    circular_oligos = part.getCircularOligos()
    if circular_oligos:
        printInfo("Breaking circular oligos...")
        for circ_oligo in circular_oligos:
            strand5p = circ_oligo.strand5p()
            strand3p = strand5p.connection3p()
            part.removeXover(strand5p, strand3p)

    printInfo("Splitting long oligos...")
    # Naively break staples at xovers using greedy algorithm
    min_split_len = 35  # break oligos longer than this
    for staple in staple_oligos:
        unbroken_length = staple.length()
        strand_lengths = staple.getStrandLengths()
        split_idxs = []
        next_strand_len = 0
        num_bases_used = 0
        for nbases in strand_lengths:
            next_strand_len += nbases
            num_bases_used += nbases
            if min_split_len < next_strand_len and num_bases_used < unbroken_length:
                split_idxs.append(num_bases_used)
                next_strand_len = 0
        if split_idxs:
            staple.splitAtAbsoluteLengths(split_idxs)

    # print(scaffold, scaffold.length(), scaffold.sequence())
    p7560 = sequences['p7560']
    scaf_oligo.applySequence(p7560)

    # seqs = part.getSequences()
    # print(seqs)

    # oligos = part.oligos()
    # oligos_sorted_by_color = sorted(oligos, key=lambda x: x.getColor())
    # for oligo in oligos_sorted_by_color:
    #     if oligo == scaf_oligo:
    #         print("Scaffold {0} has length {1}".format(oligo, oligo.length()))
    #     else:
    #         # oligo_props = oligo.dump()
    #         printOligo(oligo)

    print("Saving modified document as", colored("{0}".format(dest_file), 'yellow'))
    # printInfo("{0}".format(dest_file))
    doc.writeToFile(dest_file)


# color_dict = dict((color, 'white', []) for color in CADNANO1_COLORS)
color_dict = {'#cc0000': ('red', None, []),
              '#007200': ('green', None, ['bold']),
              '#cc0000': ('red', None, []),
              '#57bb00': ('green', None, []),
              '#aaaa00': ('yellow', None, []),
              '#1700de': ('blue', None, []),
              '#b8056c': ('magenta', None, []),
              '#03b6a2': ('cyan', None, []),
              '#333333': ('white', None, ['reverse']),
              }


def printInfo(s):
    print(colored(s, 'green'))


def printWarning(s):
    print(colored(s, 'yellow', attrs=['reverse']))


def printOligo(oligo):
    oligo_col = oligo.getColor()
    oligo_props = oligo.dump()

    if oligo_col in color_dict:
        text_color = color_dict[oligo_col][0]
        highlight = color_dict[oligo_col][1]
        style = color_dict[oligo_col][2]
        # print (color_dict[oligo_col])
        if oligo.length() < OLIGO_LEN_BELOW_WHICH_HIGHLIGHT:
            style = style + ['underline']
        oligo_seq = colored(oligo_props['sequence'], text_color, highlight, attrs=style)
    else:
        oligo_seq = oligo_props['sequence']

    print(oligo, '\t[', oligo_col, ']\t', oligo_seq, '\t', oligo.length())


def colorBool(b):
    """Given boolean argument, return stylized string"""
    if b:
        return colored(b, 'green')
    else:
        return colored(b, 'red', attrs=['reverse'])


if __name__ == '__main__':
    sys.exit(main())
