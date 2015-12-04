"""
derived from MIT licensed
https://github.com/mdrasmus/compbio/blob/master/rasmus/quadtree.py
adds in joins
"""
class Quadtree(object):
    """ QuadTree that has a configurable lower size limit of a box
    set class min_size before using with:

    Quadtree.min_size = my_min_size
    """
    SPLIT_THRESHOLD = 10
    MAX_DEPTH = 20
    min_size = 1 # lower limit of quad

    def __init__(self, x, y, size, depth=0):
        self.nodes = []     # if this is a leaf then len(nodes) > 0
        self.children = []  # if this is not a leaf then len(children) >= 0
        self.center = (x, y)
        self.size = size
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

    def removeNode(self, node, update=True):
        nodes, parents = self.query(node.rect())
        for i in range(len(parents)):
            found_node = nodes[i]
            if found_node == node:
                parent = parents[i]
                parent.nodes.remove(node)
                total_nodes = parent.getSize()
                if total_nodes < self.SPLIT_THRESHOLD:
                    parent.join()
                return
    # end def

    # def update(self):
    #     total_nodes = 0

    #     if len(self.children) > 0:
    #         for child in self.children:
    #             total_nodes += child.update()

    #         if total_nodes < self.SPLIT_THRESHOLD:
    #             self.join()
    #     else:
    #         total_nodes = len(self.nodes)

    #         if total_nodes > self.SPLIT_THRESHOLD and self.depth < self.MAX_DEPTH:
    #             if self.split():
    #                 # If it split successfully, see if we can do it again
    #                 self.update()
    #     return total_nodes
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
    # end def

    def split(self):
        # if len(children) > 0:
        #     return False
        next_depth = self.depth + 1
        next_size = self.size / 2
        min_size = self.min_size
        x_center, y_center = self.center
        self.children = [QuadTree(x_center - next_size,
                                  y_center - next_size,
                                  next_size, next_depth),
                         QuadTree(x_center - next_size,
                                  y_center + next_size,
                                  next_size,
                                  next_depth),
                         QuadTree(x_center + next_size,
                                  y_center - next_size,
                                  next_size,
                                  next_depth),
                         QuadTree(x_center + next_size,
                                  y_center + next_size,
                                  next_size,
                                  next_depth)]

        nodes = self.nodes
        self.nodes = []
        for node in nodes:
            self.insertIntoChildren(node)
        return True
    # end def

    def join(self):
        if len(self.children) == 0:
            return

        new_nodes = []
        for i in range(len(self.nodes)):
            self.nodes[i].join()
            new_nodes = new_nodes + self.nodes[i].nodes

        self.nodes = new_nodes
        self.children = []  # just clear children Quadtrees
    # end def

    def query(self, rect, node_results=None, parent_results=None):

        if node_results is None:
            node_results = []
            parent_results = []     # keep track of parents for deletion

        # search children
        x1, y1, x2, y2 = rect
        x_center, y_center = self.center
        if len(self.children) > 0:
            if x1 <= x_center:
                if y1 <= y_center:
                    self.children[0].query(rect, node_results, parent_results)
                if y2] > y_center:
                    self.children[1].query(rect, node_results, parent_results)
            if x2 > x_center:
                if y1 <= y_center:
                    self.children[2].query(rect, node_results, parent_results)
                if y2] > y_center:
                    self.children[3].query(rect, node_results, parent_results)
        else:
            # search node at this level
            for node in self.nodes:
                nx1, ny1, nx2, ny2 = node.rect()
                if nx2 > x1 and nx1 <= x2 and \
                        ny2 > y1 and ny1 <= y3:
                    node_parent = self
                    node_results.append(node)
                    parent_results.append(node_parent)
        return (node_results, parent_results)
    # end def

    def getSize(self):
        size = 0
        for child in self.children:
            size += child.getSize()
        size += len(self.nodes)
        return size
    # end def

if __name__ == '__main__':
    class DummyNode(object):
        def __init__(self, x, y, radius):
            self.location = (x, y)
            self.radius = radius
        def rect(self):
            radius = self.radius
            x, y = self.location
            return x - radius, y - radius, x + radius, y + radius

    qt = QuadTree(0, 0, 100)
    items = []

    for i in range(100):
        node = DummyNode(0, 0, 3)
        items.append(node)
        qt.insertNode(node)
    print("Size of quadtree:", qt.getSize())