"""
derived from MIT licensed
https://github.com/mdrasmus/compbio/blob/master/rasmus/quadtree.py
adds in joins and ability to remove nodes
"""

def allClose(a, b):
    for x, y in zip(a, b):
        if abs(x - y) > 0.001:
            return False
    return True

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

    def rect(self):
        x, y = self.center
        half_size = self.size / 2
        return x - half_size, y - half_size, x + half_size, y + half_size

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
        rect = node.rect()
        x1, y1, x2, y2 = rect
        x_center, y_center = self.center
        children = self.children
        if (x1 <= x_center and x2 > x_center) and \
                (y1 <= y_center and y2 > y_center):
            self.nodes.append(node)
            return node
        else:
            # try to insert into children
            if x1 <= x_center:
                if y1 <= y_center:
                    return children[0].insertNode(node)
                if y2 > y_center:
                    return children[1].insertNode(node)
            if x2 > x_center:
                if y1 <= y_center:
                    return children[2].insertNode(node)
                if y2 > y_center:
                    return children[3].insertNode(node)
                else:
                    raise ValueError("could not insert", rect)
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

    def query(self, rect, node_results):
        # search children
        x1, y1, x2, y2 = rect
        x_center, y_center = self.center
        if len(self.children) > 0:
            if x1 <= x_center:
                if y1 <= y_center:
                    self.children[0].query(rect, node_results)
                if y2 > y_center:
                    self.children[1].query(rect, node_results)
            if x2 > x_center:
                if y1 <= y_center:
                    self.children[2].query(rect, node_results)
                if y2 > y_center:
                    self.children[3].query(rect, node_results)

        # search node at this level
        for node in self.nodes:
            # check overlap
            nx1, ny1, nx2, ny2 = node.rect()
            if nx2 > x1 and nx1 <= x2 and \
                    ny2 > y1 and ny1 <= y2:
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
        x1, y1, x2, y2 = query_node.rect()
        x_center, y_center = self.center
        if len(self.children) > 0:
            if x1 <= x_center:
                if y1 <= y_center:
                    res = self.children[0].findNodeByNode(query_node)
                    if res is not None:
                        return res
                if y2 > y_center:
                    res = self.children[1].findNodeByNode(query_node)
                    if res is not None:
                        return res
            if x2 > x_center:
                if y1 <= y_center:
                    res = self.children[2].findNodeByNode(query_node)
                    if res is not None:
                        return res
                if y2 > y_center:
                    res = self.children[3].findNodeByNode(query_node)
                    if res is not None:
                        return res
        return None
    # end def

    def findNodeByRect(self, rect):
        """ look for the exact node
        assumes same node doesn't exist more than once in Quadtree
        return the Node and the nodes parent
        """
        # search node at this level
        for node in self.nodes:
            # check overlap
            if allClose(node.rect(), rect):
                return node, self
        # search children
        x1, y1, x2, y2 = rect
        x_center, y_center = self.center
        if len(self.children) > 0:
            if x1 <= x_center:
                if y1 <= y_center:
                    res = self.children[0].findNodeByRect(rect)
                    if res is not None:
                        return res
                if y2 > y_center:
                    res = self.children[1].findNodeByRect(rect)
                    if res is not None:
                        return res
            if x2 > x_center:
                if y1 <= y_center:
                    res = self.children[2].findNodeByRect(rect)
                    if res is not None:
                        return res
                if y2 > y_center:
                    res = self.children[3].findNodeByRect(rect)
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

    def queryNode(self, node, scale_factor=1.0):
        qc = self._query_cache
        rect = node.rect()
        res = qc.get(rect)
        if node in qc:
            return qc.get(rect)
        else:
            node_results = set()
            res = QuadtreeBase.query(self,
                                    node.rect(scale_factor=scale_factor),
                                    node_results)
            qc[rect] =  res
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
            self.location = (x, y)
            self.radius = radius
        def rect(self):
            radius = self.radius
            x, y = self.location
            return x - radius, y - radius, x + radius, y + radius

    qt = Quadtree(0, 0, 120)
    items = []

    for i in range(100):
        node = DummyNode(i, i, 1)
        items.append(node)
        qt.insertNode(node)
    print("Size of quadtree:", qt.getSize(), qt.getDepth())
    print([x.rect() for x in qt.queryNode(items[50])])
    for item in items:
        did_remove = qt.removeNode(item)
        if not did_remove:
            print("Did not remove", item.location)
    # did_remove = qt.removeNode(items[1])
    print("Size of quadtree:", qt.getSize(), qt.getDepth())
