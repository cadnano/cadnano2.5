# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

'''
staplegraph.py
Created by Nick Conway on Mar 1, 2010

For use as a plugin solver in cadnano

Dependencies:

Graphviz
pydot
matplotlib
networkx
pywin32 (maybe not)
pyparsing
ipython
numpy 

A token_list === list of sequencial lengths between potential break points

Given a token_list : 
[V0, V1,V2,...,VN-1] 

corresponding to predefined staple lengths 'V' in a staple strand (or staple 
loop) leads to....
  
<-A1><--E0=V0--><A2><-A2><--E1=V1--><A3><-A3><--E2=V2-->....<AN><-AN><--EN=VN--><A1>

in linear graph form and we filter paths meeting certain edge length criterion 
and then weight the graph relative to an optimum edge length criterion.

In order to have a positive and negative version of each node we eliminate '0'
 (zero) from the list of possible node names

The graph need be directed to enforce the visitation of all nodes

Dijkstra's algorithm and Floyd Warshall are supported solutions
'''
try:
    import networkx as nx
    print "successs on nx"
except:
    print "trying embedded nx"
    import include.networkx as nx
    print "got embedded"

# the DEFINE parameters address the staple_limits argument parameters
MIN_IND = 0     # minimum length index
MAX_IND = 1     # maximum length index
OPT_IND = 2     # optimum length index

def minimumPath(tokenlist_and_staple_limits):
    tokenList, staple_limits, idx = tokenlist_and_staple_limits
    sg = StapleGraph(token_list_in=tokenList, \
                    staple_limits=staple_limits)
    # print sg.graph().nodes(), sg.graph().edges()
    # if len(sg.graph().nodes()) > 1:
        # print "total nodes:", len(sg.graph().nodes())
    try:
        output = sg.minPathDijkstra()
        return (output, idx)
        # print "Solved!"
    except:
        print "Oligo is unsolvable at current settings for length"
        return None
    # else: 
    #     return None
# end def

class StapleGraph(object):
    """
    
    """
    def __init__(self,token_list_in=[4,7,6,5,7,8,3], staple_limits=[3,18,10]):
        """
        Constructor  takes a
        
        token_list: list of sequential lengths between potential breaks 
            points in a staple
        staple_limits: min staple length, max staple length, optimum 
            staple length 
        """
            
        self.token_list = token_list_in
        self.token_list_length = len(self.token_list)
        self.G = nx.DiGraph()       # initialize a directed graph data structure from networkx module
        self.min_staple_length = staple_limits[MIN_IND]
        self.max_staple_length = staple_limits[MAX_IND]
        self.optimum_staple = staple_limits[OPT_IND]
        self.min_path_dict = []
        self.the_min_path = []
        self.createGraph()          # create the graph
    # end def
    
    def graph(self):
        return self.G
    
    def createGraph(self):
        """
        constructs a directed, weighted graph of nodes [-A_n,A_n] such that
        A_n is a non-zero integer
        the n ranges [0, self.token_list_length]
        A_n therefore ranges [1, self.token_list_length+1] 
        
        -A_n is always the start of a potential loop and A_n is the end of a loop
        for a circular staple strand loop.  Similarly, A_n is always the end of a 
        token and -A_n is the beginning of the next token, if you will
        
        for non_circular staple strand loops the strands run from -1 to 1
        
        edges are limited by a minimum and maximum staple length, and are weighted by
        the difference from the staple length from the optimum staple length
        """
        
        from_node_index = 0
        
        # corresponds to the node we are going to
        to_node_index = 0   
        
        # this is the index of the "edge" in the token list, 
        # corresponds to the token value
        
        edge_index = 0      
        visit_node_counter = 0
        current_staple_length = 0
        index_to_build = 0
        token_sum = 0
        
        for ind in range(self.token_list_length):
            from_node_index = ind + 1 # no '0' node all non-zero
            to_node_index = from_node_index + 1
            edge_index = from_node_index - 1
            from_node_index = -from_node_index
            current_staple_length = 0
            visited_edge_counter = 1
            self.G.add_weighted_edges_from([(ind+1, from_node_index,0)])
            
            """
            We limit the size of the graph by using the cutoffs of max_staple_length
            and min_staple_length
            """
            while current_staple_length < self.max_staple_length:
                if to_node_index == self.token_list_length+1:    # if we've exceeded the limit
                    to_node_index = 1;  # wrap around to first non-zero
                # end if
                elif edge_index == self.token_list_length:
                    break
                # end elif
                if visited_edge_counter == self.token_list_length:
                    break
                # end if
                current_staple_length += self.token_list[edge_index]
                if (current_staple_length > self.min_staple_length):
                    root_mean_sq = abs(current_staple_length-self.optimum_staple)
                    self.G.add_weighted_edges_from([(from_node_index, to_node_index, root_mean_sq)])
                # end if
                to_node_index += 1
                edge_index += 1
                visited_edge_counter +=1
            # end while
        # end for
    #end def

    def draw(self):
        """
        returns a list sorted by weight formatted [(weigth, start_index, end_index) ...]
        """
        import matplotlib.pyplot as plt
        try:
            from networkx import graphviz_layout
        except ImportError:
            raise ImportError("This module needs Graphiz and either PyGraphiz or Pydot")
            
        # pos = nx.graphviz_layout(self.G,prog = 'twopi')
        plt.figure(figsize=(8,8))
        nx.draw_circular(self.G,node_Size=240,alpha=0.7,node_color="blue")
        #nx.draw(self.G,pos, node_Size=240,alpha=0.7,node_color="blue")
        plt.axis('equal')
        plt.show()
    #end def
    
    def showEdgeWeight(self):
        edges = self.G.edges()
        for edge in edges:
            print "Edge ", edge, ": ", self.G.get_edge_data(edge[0],edge[1])
        # end for
    # end def
    
    def floydWarshall(self):
        """
        This finds all-pairs of shortest path lengths using Floyd's algorithm 
        and sets self.min_path_dict to [predecessor_dict, distance_dict] where 
        the two dictionaries 2D dictionaries keyed on node index.
        predecessor is the ordered list of visited nodes when going from node
        A to node B along a shortest path.
        """
        # self.min_path_dict = nx.floyd_warshall(self.G)
        self.min_path_dict = nx.floyd_warshall_predecessor_and_distance(self.G)
        # self.truncatePathDict() # for ASCII debugging
    #end def
    
    def getMinPathsFW(self):
        """
        Finds all of the minimum path start and end nodes after a Floyd-Warshall
        
        """
        out_paths = []
        min_paths = self.min_path_dict[0] # gets the list of shortest path start and end nodes and the path length
        keys = min_paths.keys()
        for key in keys:
            start_n = key
            end_n = -key
            if (start_n > end_n):
                pass # we only care about paths from -A_n to +A_n
            # end if
            else:
                weight = min_paths[key][end_n]
                out_paths.append([weight, start_n, end_n])
            # end else
        # end for
        out_paths.sort() # sort by weight
        return out_paths
    #end def

    def getShortestPathFW(self,a,b):
        """
        Retraces the shortest path from a calculated Floyd-Warshall 
        predecessor list.
        """
        intermediate = self.min_path_dict[0][a][b]
        path = [b]
        while intermediate != a:
            # print path
            path.append(intermediate)
            intermediate = self.min_path_dict[0][a][intermediate]
        #end while
        path.append(a)
        path.reverse()   # need to reverse because the loopup table gives the edges in reverse order
        return path
    # end def
    
    def minPathFW(self):
        """
        Returns the shortest path using Floyd-Warshall algorithm.
        """
        self.floydWarshall()
        the_path = [0,-1,1]
        path = self.getShortestPathFW(the_path[1],the_path[2])
        return self.formatOutput(path)
    #end def
    
    def getShortestPathDijkstra(self,a,b):
        out_node_list = nx.dijkstra_path(self.G,a,b)
        return out_node_list
    # end def
    
    def minPathDijkstra(self):
        """
        This finds the minimum path length starting at each node.   
        """
        min_length = sum(self.token_list)
        temp = 0
        path = []
        token_sum = 0   # keeps track of the staple break points to look at
        ind_min = 1 # just go from -1 to 1
        # end else 
        path = self.getShortestPathDijkstra(-ind_min,ind_min)
        # print "the path", path
        return self.formatOutput(path)
    #end def
    
    def formatOutput(self,path):
        """
        takes a path either from Dijkstra or Floyd-Warshall processing and formats
        it for adding to a the set of a scaffold structure staples 
        returns a list of [start_index,[L1,L2,...LN]]
        where start_index is the first token index into the 
        token_list and
        L are a list of lengths of proper tokens from self.token_list

        this is translated from a list whose indices correspond to plus 1 from indices in
        """
        
        path_start = abs(path[0])-1
        output = [path_start,[], 0]
        
        # print "test 1"
        path_length = len(path)
        for ind in range(0,path_length,2):
            #print ind
            edge_length = 0
            token_idx = abs(path[ind]) - 1
            
            while token_idx != (path[ind+1]-1):
                edge_length += self.token_list[token_idx]
                token_idx += 1
                if token_idx == self.token_list_length:
                    token_idx = 0
                # end if
            #end while
            output[1].append(edge_length)
        # end for
        # print "test 2"
        ost = self.optimum_staple
        finalScore = sum([abs(ost-x) for x in output[1]])
        # print "test 3"
        output[2] = finalScore
        # print "test 4"
        return output 
    #end def
    
    def truncatePathDict(self):
        """
        strictly to help visualize the output data set by removing nodes from the list
        not use in the end
        """
        temp0  = self.min_path_dict[0]
        temp1 = self.min_path_dict[1]
        for ind in range (1,self.token_list_length+1):
            # get rid of positive indices construed as starting nodes
            del(temp0[ind])
            del(temp1[ind])
            # now get rid of the negative indices since they are only starting nodes
            for jnd in range (1,self.token_list_length+1):
                del(temp0[-ind][-jnd])
                del(temp1[-ind][-jnd])
                temp1[-ind][jnd] = abs(temp1[-ind][jnd])
            # end for
        # end for
        self.min_path_dict = (temp0,temp1)
    # end def
    
# end def class


def testMe():
    """
    Testing the above code
    """
    # testlist = [21, 7, 7, 7, 7, 7, 7, 7, 7, 7, 14, 7, 7, 7, 7, 21, 7, 7, 7, 7, 7, 7, 7, 7, 7, 14, 7, 7, 7, 7]
    testlist = [1,7,1,1,1,1,1,1,7,1,7,1,7,1,1,7,7,7,1,7,1,1,7,1,1,1,1,1]
    b = StapleGraph(token_list_in=testlist, staple_limits=[20,50,35])
    # b.floydWarshall()
    print "input ", b.token_list
    print "sum lengths of of tokens: ", sum(b.token_list)
    print "\ndijkstra"
    print b.minPathDijkstra()
    print "\nfloyd-warshall"
    print b.minPathFW()
    b.draw()
#end def

if __name__=='__main__':
    print "Creating tree:"
    testMe()