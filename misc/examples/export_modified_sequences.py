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

    # print(scaffold, scaffold.length(), scaffold.sequence())
    p7560 = sequences['p7560']
    scaf_oligo.applySequence(p7560)

    # Naive breaking algorithm
    min_break_len = 35  # break oligos longer than this
    for staple in staple_oligos:
        break_positions = []  # pre-calculate breaks to avoid oligo changes
        if staple.length() > min_break_len:
            i = 0
            for strand in staple.strand5p().generator3pStrand():
                s_len = strand.totalLength()
                if s_len > min_break_len:  # just add
                    # segments = s_len//min_break_len-1
                    step = min_break_len if strand.isForward() else -min_break_len
                    break_positions.append([[strand.idNum(), strand.strandType(), idx]
                                           for idx in range(strand.idx5Prime(),
                                                            strand.idx3Prime(),
                                                            step)])
                elif strand != staple.strand3p():
                    i = i + strand.totalLength()
                    if i > min_break_len:
                        break_positions.append([strand.idNum(), strand.strandType(), strand.idx3Prime()])
                        i = 0
        if break_positions:
            for id_num, ss_type, idx in break_positions:
                # look up the strand
                ss = part.getStrandSets(id_num)[ss_type]
                strand = ss.getStrand(idx)
                # simple break
                if ss.strandCanBeSplit(strand, idx):
                    print("Splitting at <VH{0}.{1}>[{2}]".format(strand.idNum(), strand.strandType(), idx))
                    ss.splitStrand(strand, idx)
                # xover break
                elif strand.hasXoverAt(idx):
                    if idx == strand.idx3Prime():
                        strand5p = strand
                        strand3p = strand5p.connection3p()
                    else:
                        strand3p = strand
                        strand5p = strand.connection5p()
                    print("Removing xover at <VH{0}.{1}>[{2}]".format(strand5p.idNum(), strand5p.strandType(), idx))
                    part.removeXover(strand5p, strand3p)
                else:
                    print("Couldn't split strand at <VH{0}.{1}>[{2}]".format(id_num, ss_type, idx))

    circular_oligos = part.getCircularOligos()
    if circular_oligos:
        print("Breaking circular oligos...")
        for circ_oligo in circular_oligos:
            strand5p = circ_oligo.strand5p()
            strand3p = strand5p.connection3p()
            part.removeXover(strand5p, strand3p)

    # seqs = part.getSequences()
    # print(seqs)

    oligos = part.oligos()
    oligos_sorted_by_color = sorted(oligos, key=lambda x: x.getColor())

    for oligo in oligos_sorted_by_color:
        if oligo == scaf_oligo:
            print("Scaffold {0} has length {1}".format(oligo, oligo.length()))
        else:
            oligo_props = oligo.dump()
            print(oligo, oligo_props['sequence'])

    print("Saving modified file as", dest_file)
    doc.writeToFile(dest_file)


def colorBool(b):
    """Given boolean argument, return stylized string"""
    if b:
        return colored(b, 'green')
    else:
        return colored(b, 'red', attrs=['reverse'])


if __name__ == '__main__':
    sys.exit(main())
