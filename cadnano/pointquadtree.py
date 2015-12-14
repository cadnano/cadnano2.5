"""
derived from MIT licensed
https://github.com/mdrasmus/compbio/blob/master/rasmus/quadtree.py
adds in joins and ability to remove nodes
"""
from math import sqrt
def allClose(a, b):
    for x, y in zip(a, b):
        if abs(x - y) > 0.001:
            return False
    return True

def v2Distance(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return sqrt(dx*dx + dy*dy)

class QuadtreeBase(object):
    """ QuadTreeBase that has a configurable lower size limit of a box
    set class min_size before using with:

    Quadtree.min_size = my_min_size

    QuadTrees can have both nodes and children Quadtrees if a node's
    rect spans a given Quadtree's center
    """
    SPLIT_THRESHOLD = 10
    MAX_DEPTH = 20

    def __init__(self, x, y, size, min_size, parent=None, depth=0):
        self.nodes = []     # if this is a leaf then len(nodes) > 0
        self.children = []  # if this is not a leaf then len(children) >= 0
        self.center = (x, y)
        self.size = size
        self.min_size = min_size # lower limit of quadtree
        self.parent = parent
        self.depth = depth
    # end def

    def insertNode(self, node):
        """
        """
        nodes = self.nodes
        if len(self.children) == 0:
            nodes.append(node)
            if len(nodes) > self.SPLIT_THRESHOLD and \
                    self.size > self.min_size:
                self.split()
                return node
        else:
            return self.insertIntoChildren(node)
    # end def

    def rect(self, scale_factor=1.0):
        x, y = self.center
        x *= scale_factor
        y *= scale_factor
        half_size = scale_factor*(self.size / 2)
        return x - half_size, y - half_size, x + half_size, y + half_size
    # end def

    def removeNode(self, node):
        res = self.findNodeByNode(node)
        if res is not None:
            node, parent = res
            parent.nodes.remove(node)
            parent_parent = parent.parent
            if parent_parent is not None:
                total_nodes = parent_parent.getSize()
                if total_nodes < self.SPLIT_THRESHOLD:
                    parent_parent.join()
            return True
        return False
    # end def

    def insertIntoChildren(self, node):

        # if rect spans center then insert here
        xn, yn  = node.location()
        x_center, y_center = self.center
        # x1, y1, x2, y2 = self.rect()
        children = self.children
        # try to insert into children
        if xn <= x_center:
            if yn <= y_center:
                return children[0].insertNode(node)
            else:
                return children[1].insertNode(node)
        else:
            if yn <= y_center:
                return children[2].insertNode(node)
            else:
                return children[3].insertNode(node)
    # end def

    def split(self):
        if len(self.children) > 0:
            return False
        # print("Splitting")
        next_depth = self.depth + 1
        next_size = self.size / 2
        quarter_size = next_size / 2
        min_size = self.min_size
        x_center, y_center = self.center
        self.children = [QuadtreeBase(x_center - quarter_size,
                                  y_center - quarter_size,
                                  next_size,
                                  min_size,
                                  self,
                                  next_depth),
                         QuadtreeBase(x_center - quarter_size,
                                  y_center + quarter_size,
                                  next_size,
                                  min_size,
                                  self,
                                  next_depth),
                         QuadtreeBase(x_center + quarter_size,
                                  y_center - quarter_size,
                                  next_size,
                                  min_size,
                                  self,
                                  next_depth),
                         QuadtreeBase(x_center + quarter_size,
                                  y_center + quarter_size,
                                  next_size,
                                  min_size,
                                  self,
                                  next_depth)]

        nodes = self.nodes
        self.nodes = []
        for node in nodes:
            self.insertIntoChildren(node)
        return True
    # end def

    def join(self):
        if len(self.children) == 0:
            return False
        # print("joining", self.depth)
        new_nodes = []
        for i in range(len(self.children)):
            self.children[i].join()
            new_nodes = new_nodes + self.children[i].nodes
        self.nodes += new_nodes
        self.children = []  # just clear children Quadtrees
        return True
    # end def

    def query(self, point, distance, node_results):
        # search children
        x, y = point
        x_center, y_center = self.center
        if len(self.children) > 0:
            if x <= x_center:
                if y <= y_center:
                    self.children[0].query(point, distance, node_results)
                else:
                    self.children[1].query(point, distance, node_results)
            else:
                if y <= y_center:
                    self.children[2].query(point, distance, node_results)
                else:
                    self.children[3].query(point, distance, node_results)

        # search node at this level
        for node in self.nodes:
            # check overlap
            nloc = node.location()
            mdistance = v2Distance(nloc, point)
            if mdistance < distance:
                node_results.add(node)
        return node_results
    # end def

    def findNodeByNode(self, query_node):
        """ look for the exact node
        assumes same node doesn't exist more than once in Quadtree
        return the Node and the nodes parent
        """
        # search node at this level
        for node in self.nodes:
            # check overlap
            if node == query_node:
                return node, self
        # search children
        x, y = query_node.location()
        x_center, y_center = self.center
        if len(self.children) > 0:
            if x <= x_center:
                if y <= y_center:
                    res = self.children[0].findNodeByNode(query_node)
                    if res is not None:
                        return res
                else:
                    res = self.children[1].findNodeByNode(query_node)
                    if res is not None:
                        return res
            else:
                if y <= y_center:
                    res = self.children[2].findNodeByNode(query_node)
                    if res is not None:
                        return res
                else:
                    res = self.children[3].findNodeByNode(query_node)
                    if res is not None:
                        return res
        return None
    # end def

    def findNodeByPoint(self, query_point):
        """ look for the exact node
        assumes same node doesn't exist more than once in Quadtree
        return the Node and the nodes parent
        """
        # search node at this level
        for node in self.nodes:
            # check overlap
            if allClose(node.location(), query_point):
                return node, self
        # search children
        x, y = query_point
        x_center, y_center = self.center
        if len(self.children) > 0:
            if x <= x_center:
                if y <= y_center:
                    res = self.children[0].findNodeByPoint(query_point)
                    if res is not None:
                        return res
                else:
                    res = self.children[1].findNodeByPoint(query_point)
                    if res is not None:
                        return res
            else:
                if y <= y_center:
                    res = self.children[2].findNodeByPoint(query_point)
                    if res is not None:
                        return res
                else:
                    res = self.children[3].findNodeByPoint(query_point)
                    if res is not None:
                        return res
        return None
    # end def


    def getSize(self):
        size = 0
        for child in self.children:
            size += child.getSize()
        size += len(self.nodes)
        return size
    # end def

    def getDepth(self):
        depth = self.depth
        for child in self.children:
            new_depth = child.getDepth()
            if new_depth > depth:
                depth = new_depth
        return depth
    # end def
# end class

class Quadtree(QuadtreeBase):
    def __init__(self, x, y, size, min_size=4):
        super(Quadtree, self).__init__(x, y, size, min_size)
        self._query_cache = {}
        self._all_nodes = []
    # end def

    def queryNode(self, node, distance, scale_factor=1.0):
        qc = self._query_cache
        location = node.location(scale_factor=scale_factor)
        if location in qc:
            return qc.get(location)
        else:
            node_results = set()
            res = QuadtreeBase.query(self,
                                    location,
                                    distance,
                                    node_results)
            qc[location] =  res
            return res
    # end def

    def queryPoint(self, query_point, distance):
        node_results = set()
        res = QuadtreeBase.query(self,
                                query_point,
                                distance,
                                node_results)
        return res
    # end def

    def removeNode(self, node):
        self._query_cache = {} # clear cache
        self._all_nodes.remove(node)
        return QuadtreeBase.removeNode(self, node)
    # end def

    def insertNode(self, node):
        self._query_cache = {} # clear cache
        self._all_nodes.append(node)
        return QuadtreeBase.insertNode(self, node)
    # end def

    def getSize(self):
        return len(self._all_nodes)
    # end def

    def __iter__(self):
        for item in self._all_nodes:
            yield item
    # end def
# end class

if __name__ == '__main__':
    class DummyNode(object):
        def __init__(self, x, y, radius):
            self._location = (x, y)
            self.radius = radius

        def location(self, scale_factor=1.0):
            return self._location

        def rect(self):
            radius = self.radius
            x, y = self._location
            return x - radius, y - radius, x + radius, y + radius

    qt = Quadtree(0, 0, 120)
    items = []

    for i in range(100):
        node = DummyNode(i, i, 1)
        items.append(node)
        qt.insertNode(node)
    print("Size of quadtree:", qt.getSize(), qt.getDepth())
    print([x.rect() for x in qt.queryNode(items[50], 1)])
    for item in items:
        did_remove = qt.removeNode(item)
        if not did_remove:
            print("Did not remove", item.location)
    # did_remove = qt.removeNode(items[1])
    print("Size of quadtree:", qt.getSize(), qt.getDepth())
