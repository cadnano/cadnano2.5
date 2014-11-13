import util, cadnano
import heapq
from model.strandset import StrandSet
from model.enum import StrandType
from model.parts.part import Part
from model.oligo import Oligo
from multiprocessing import Pool, cpu_count
from operator import itemgetter

try:
    import staplegraph
    nx = True
except:
    nx = False

token_cache = {}

def breakStaples(part, settings):
    clearTokenCache()
    break_oligos = part.document().selectedOligos()
    if break_oligos is None:
        break_oligos = part.oligos()
    else:
        part.document().clearAllSelected()
    for o in list(break_oligos):
        if not o.isStaple():
            continue
        if nx:
            nxBreakStaple(o, settings)
        else:
            print("Not breaking")
            # breakStaple(o, settings)
# end def

def nxBreakStaple(oligo, settings):
    stapleScorer = settings.get('stapleScorer', tgtLengthStapleScorer)
    min_staple_leg_len = settings.get('minStapleLegLen', 3)
    min_staple_len = settings.get('minStapleLen', 30)
    min_staple_len_minus_one = min_staple_len-1
    max_staple_len = settings.get('maxStapleLen', 40)
    max_staple_len_plus_one = max_staple_len+1
    tgtStapleLen = settings.get('tgtStapleLen', 35)
    
    token_list = tokenizeOligo(oligo, settings)

    # print "tkList", token_list, oligo.length(), oligo.color()
    if len(token_list) == 0:
        return
    cache_string = stringifyToken(oligo, token_list)
    if cache_string in token_cache:
        # print "cacheHit!"
        break_items, shortest_score_idx = token_cache[cache_string]
        nxPerformBreaks(oligo, break_items, token_list, shortest_score_idx, min_staple_leg_len)
    else:
        staple_limits = [min_staple_len, max_staple_len, tgtStapleLen] 
        token_lists = [(token_list, staple_limits,0)]
        tokenCount = token_list[0]
        if oligo.isLoop():
            lenList = len(token_list)
            for i in range(1, lenList):
                if tokenCount > 2*max_staple_len:
                    break
                tL = token_lists[i-1][0]
                rotatedList =  tL[1:-1] + tL[0:1]   # assumes lenList > 1
                tokenCount += rotatedList[0]
                token_lists.append((rotatedList, staple_limits, i))
            # end for
        # end if
        # p = Pool(cpu_count() * 2)
        # p = Pool(4)
        # returns ( [breakStart, [breakLengths, ], score], tokenIdx)
        # results = p.map(staplegraph.minimumPath, token_lists)
        results = list(map(staplegraph.minimumPath, token_lists))

        f = itemgetter(0)   # get the graph results
        g = itemgetter(2)    # get the score
        # so this is
        score_tuple = min(results, key=lambda x: g(f(x)) if x else 10000)
        # ensure there's at least one result
        if score_tuple:
            shortest_score, shortest_score_idx = score_tuple
            break_items = results[shortest_score_idx][0][1]
            addToTokenCache(cache_string, break_items, shortest_score_idx)
            nxPerformBreaks(oligo, break_items, token_list, shortest_score_idx, min_staple_leg_len)
        else:
            if oligo.isLoop():
                print("unbroken Loop", oligo, oligo.length())
# end def

def addToTokenCache(cache_string, break_items, shortest_score_idx):
    token_cache[cache_string] = (break_items, shortest_score_idx)
# end def

def clearTokenCache():
    token_cache = {}
# end def

def stringifyToken(oligo, token_list):
    cache_string = str(token_list)
    if oligo.isLoop():
        cache_string = 'L' + cache_string
    return cache_string
# end def

def tokenizeOligo(oligo, settings):
    """
    Split the oligo into sub-tokens. Strands with insertions are not tokenized
    and their full length is added.
    """
    token_list = []
    min_staple_leg_len = settings.get('minStapleLegLen', 2)
    min_staple_len = settings.get('minStapleLen', 30)
    min_staple_len_minus_one = min_staple_len - 1
    max_staple_len = settings.get('maxStapleLen', 40)
    max_staple_len_plus_one = max_staple_len + 1
    oligo_len = oligo.length()
    if oligo_len < 2*min_staple_len + 1 or oligo_len < min_staple_len:
        return token_list

    totalL = 0
    strandGen = oligo.strand5p().generator3pStrand()
    for strand in strandGen:
        a = strand.totalLength()
        totalL += a
        # check length, and also for insertions
        if a > 2*min_staple_leg_len-1 and not strand.hasInsertion():
            if len(token_list) == 0:
                token_list.append(min_staple_leg_len)
            else:
                token_list[-1] = token_list[-1] + min_staple_leg_len
            a -= min_staple_leg_len
            while a > min_staple_leg_len:
                token_list.append(1)
                a -= 1
            # end while
            token_list.append(min_staple_leg_len)
        else:
            token_list.append(a)
        # end if
    # end for

    if oligo.isLoop():
        loop_token = token_list.pop(-1)
        token_list[0] += loop_token

    # print "check", sum(token_list), "==", oligo_len, totalL
    if sum(token_list) != oligo_len:
        oligo.applyColor("#ff3333", use_undostack=False)
        return []
    assert(sum(token_list) == oligo_len)
    return token_list
# end def

def nxPerformBreaks(oligo, break_items, token_list, starting_token, min_staple_leg_len):
    """ fullBreakptSoln is in the format of an IBS (see breakStrands).
    This function performs the breaks proposed by the solution. """
    part = oligo.part()
    if break_items:
        util.beginSuperMacro(part, desc="Auto-Break")

        # temp = []
        # for s in oligo.strand5p().generator3pStrand():
        #     temp.append(s.length())
        # print "the segments", sum(temp), temp

        # print "the sum is ", sum(break_list[1]), "==", oligo.length(), "isLoop", oligo.isLoop()
        # print "the break_items", break_items

        strand = oligo.strand5p()
        if oligo.isLoop():
            # start things off make first cut
            length0 = sum(token_list[0:starting_token+1])
            strand, idx, is5to3 = getStrandAtLengthInOligo(strand, length0 - min_staple_leg_len)
            ss = strand.strandSet()
            found, ss_idx = ss.getStrandIndex(strand)
            # found, overlap, ssIdx = ss._findIndexOfRangeFor(strand)
            strand.split(idx, update_sequence=False)
            strand = ss._strandList[ss_idx + 1] if is5to3 else ss._strandList[ssIdx]

        # now iterate through all the breaks
        for b in break_items[0:-1]:
            if strand.oligo().length() > b:
                strand, idx, is5to3 = getStrandAtLengthInOligo(strand, b)
                ss = strand.strandSet()
                found, ss_idx = ss.getStrandIndex(strand)
                # found, overlap, ssIdx = ss._findIndexOfRangeFor(strand)
                strand.split(idx, update_sequence=False)
                strand = ss._strandList[ss_idx+1] if is5to3 else ss._strandList[ss_idx]
            else:
                raise Exception("Oligo length %d is shorter than break length %d" % (strand.oligo().length(), b))
        util.endSuperMacro(part)
# end def

def getStrandAtLengthInOligo(strand_in, length):
    strandGen = strand_in.generator3pStrand()
    strand = strandGen.next()
    assert(strand == strand_in)
    # find the starting strand
    strand_counter = strand.totalLength()
    while strand_counter < length:
        try:
            strand = strandGen.next()
        except:
            print("yikes: ", 
                strand.connection3p(), strand_counter, 
                length, strand.oligo().isLoop(), strand_in.oligo().length())
            raise Exception
        strand_counter += strand.totalLength()
    # end while
    is5to3 = strand.isDrawn5to3()
    delta = strand.totalLength() - (strand_counter - length) - 1
    idx5p = strand.idx5Prime()
    # print "diff", delta, "idx5p", idx5p, "5to3", is5to3, "sCount", strand_counter, "L", length
    out_idx = idx5p + delta if is5to3 else idx5p - delta
    return (strand, out_idx, is5to3)
# end def

# Scoring functions takes an incremental breaking solution (IBS, see below)
# which is a linked list of breakpoints (nodes) and calculates the score
# (edge weight) of the staple that would lie between the last break in
# current_ibs and proposedNextNode. Lower is better.
def tgtLengthStapleScorer(current_ibs, proposed_next_break_node, settings):
    """ Gives staples a better score for being
    closer to settings['tgtStapleLen'] """
    tgt_staple_len = settings.get('tgtStapleLen', 35)
    last_break_pos_in_oligo = current_ibs[2][0]
    proposed_next_break_pos = proposed_next_break_node[0]
    staple_len = proposed_next_break_pos - last_break_pos_in_oligo
    # Note the exponent. This allows Djikstra to try solutions
    # with fewer length deviations first. If you don't include
    # it, most paths that never touch a leaf get visited, decreasing
    # efficiency for long proto-staples. Also, we want to favor solutions
    # with several small deviations from tgtStapleLen over solutions with
    # a single larger deviation.
    return abs(staple_len - tgt_staple_len)**3

def breakStaple(oligo, settings):
    # We were passed a super-long, highly suboptimal staple in the
    # oligo parameter. Our task is to break it into more reasonable staples.
    # We create a conceptual graph which represents breakpoints as
    # nodes. Each edge then represents a staple (bounded by two breakpoints
    # = nodes). The weight of each edge is an optimality score, lower is
    # better. Then we use Djikstra to find the most optimal way to break
    # the super-long staple passed in the oligo parameter into smaller staples
    # by finding the minimum-weight path from "starting" nodes to "terminal"
    # nodes.

    # The minimum number of bases after a crossover
    stapleScorer = settings.get('stapleScorer', tgtLengthStapleScorer)
    min_staple_leg_len = settings.get('minStapleLegLen', 2)
    min_staple_len = settings.get('minStapleLen', 30)
    min_staple_len_minus_one = min_staple_len - 1
    max_staple_len = settings.get('max_staple_len', 40)
    max_staple_len_plus_one = max_staple_len + 1

    # First, we generate a list of valid breakpoints = nodes. This amortizes
    # the search for children in the inner loop of Djikstra later. Format:
    # node in nodes := (
    #   pos,        position of this break in oligo
    #   strand,     strand where the break occurs
    #   idx,        the index on strand where the break occurs
    #   isTerminal) True if this node can represent the last break in oligo
    nodes = possibleBreakpoints(oligo, settings)
    lengthOfNodesArr = len(nodes)
    if lengthOfNodesArr == 0:
        print("nada", min_staple_leg_len, oligo.length())
        return

    # Each element of heap represents an incremental breakpoint solution (IBS)
    # which is a linked list of nodes taking the following form:
    # (totalWeight,   # the total weight of this list is first for automaic sorting
    #  prevIBS,       # the tuple representing the break before this (or None)
    #  node,          # the tuple from nodes representing this break
    #  nodeIdxInNodeArray)
    # An IBS becomes a full breakpoint solution iff
    #    Its first node is an initial node (got added during "add initial nodes")
    #    Its last node is a terminal node (got flagged as such in possibleBreakpoints)
    # Djikstra says: the first full breakpoint solution to be visited will be the optimal one
    heap = []
    first_strand = oligo.strand5p()

    # Add everything on the first_strand as an initial break
    # for i in xrange(len(nodes)):
    #     node = nodes[i]
    #     pos, strand, idx, isTerminal = node
    #     if strand != first_strand:
    #         break
    #     newIBS = (0, None, node, i)
    #     heapq.heappush(heap, newIBS)

    # Just add the existing endpoint as an initial break
    # print "the nodes", nodes
    newIBS = (0, None, nodes[0], 0)
    heap.append(newIBS)

    # nodePosLog = []
    while heap:
        # Pop the min-weight node off the heap
        curIBS = heapq.heappop(heap)
        curTotalScore, prevIBS, node, nodeIdxInNodeArr = curIBS
        if node[3]:  # If we popped a terminal node, we win
            # print "Full Breakpt Solution Found"
            return performBreaks(oligo.part(), curIBS)
        # Add its children (set of possible next breaks) to the heap
        nodePos = node[0]
        nextNodeIdx = nodeIdxInNodeArr + 1
        while nextNodeIdx < lengthOfNodesArr:
            nextNode = nodes[nextNodeIdx]
            nextNodePos = nextNode[0]
            proposedStrandLen = nextNodePos - nodePos
            if min_staple_lenMinusOne < proposedStrandLen < max_staple_len_plus_one:
                # nodePosLog.append(nextNodePos)
                nextStapleScore = tgtLengthStapleScorer(curIBS, nextNode, settings)
                newChildIBS = (curTotalScore + nextStapleScore,
                               curIBS,
                               nextNode,
                               nextNodeIdx)
                heapq.heappush(heap, newChildIBS)
            elif proposedStrandLen > max_staple_len:
                break
            nextNodeIdx += 1
    # print nodePosLog
    # print "No Breakpt Solution Found"

def performBreaks(part, fullBreakptSoln):
    """ fullBreakptSoln is in the format of an IBS (see breakStrands).
    This function performs the breaks proposed by the solution. """
    util.beginSuperMacro(part, desc="Auto-Break")
    break_list, oligo = [], None  # Only for logging purposes
    if fullBreakptSoln != None:  # Skip the first breakpoint
        fullBreakptSoln = fullBreakptSoln[1]
    while fullBreakptSoln != None:
        curNode = fullBreakptSoln[2]
        fullBreakptSoln = fullBreakptSoln[1]  # Walk up the linked list
        if fullBreakptSoln == None:  # Skip last breakpoint
            break
        pos, strand, idx, isTerminal = curNode
        if strand.isDrawn5to3():
            idx -= 1 # Our indices correspond to the left side of the base
        strand.split(idx, update_sequence=False)
        break_list.append(curNode)  # Logging purposes only
    # print 'Breaks for %s at: %s'%(oligo, ' '.join(str(p) for p in break_list))
    util.endSuperMacro(part)

def possibleBreakpoints(oligo, settings):
    """ Returns a list of possible breakpoints (nodes) in the format:
    node in nodes := (             // YOU CANNOT UNSEE THE SADFACE :P
      pos,        position of this break in oligo
      strand,     strand where the break occurs
      idx,        the index on strand where the break occurs
      isTerminal) True if this node can represent the last break in oligo"""

    # The minimum number of bases after a crossover
    min_staple_leg_len = settings.get('minStapleLegLen', 2)
    min_staple_len = settings.get('min_staple_len', 30)
    max_staple_len = settings.get('maxStapleLen', 40)

    nodes = []
    strand = first_strand = oligo.strand5p()
    isLoop = strand.connection5p() != None
    pos, idx = 0, 0  # correspond to pos, idx above
    while True:
        next_strand = strand.connection3p()
        is_terminal_strand = next_strand in (None, first_strand)
        if strand.isDrawn5to3():
            idx, max_idx = strand.lowIdx(), strand.highIdx() + 1
            if strand != first_strand:
                idx += min_staple_leg_len
                pos += min_staple_leg_len
            if not is_terminal_strand:
                max_idx -= min_staple_leg_len
            while idx <= max_idx:
                is_terminal_node = is_terminal_strand and idx == max_idx
                nodes.append((pos, strand, idx, is_terminal_node))
                idx += 1
                pos += 1
            pos += min_staple_leg_len - 1
        else:
            min_idx, idx = strand.lowIdx(), strand.highIdx() + 1
            if strand != first_strand:
                idx -= min_staple_leg_len
                pos += min_staple_leg_len
            if not is_terminal_strand:
                min_idx += min_staple_leg_len
            while idx >= min_idx:
                is_terminal_node = is_terminal_strand and idx == min_idx
                nodes.append((pos, strand, idx, is_terminal_node))
                idx -= 1
                pos += 1
            pos += min_staple_leg_len - 1
        strand = next_strand
        if is_terminal_strand:
            break
    # if nodes:  # dump the node array to stdout
    #     print ' '.join(str(n[0])+':'+str(n[2]) for n in nodes) + (' :: %i'%oligo.length()) + repr(nodes[-1])
    return nodes

cadnano.app().breakStaples = breakStaples
