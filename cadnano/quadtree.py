# dericed from MIT licensed
# https://github.com/mdrasmus/compbio/blob/master/rasmus/quadtree.py
# adds in joins

class Quadtree:
    MAX = 10
    MAX_DEPTH = 20

    def __init__(self, x, y, size, depth=0):
        self.nodes = []     # if this is a leaf then len(nodes) > 0
        self.children = []  # if this is not a leaf then len(children) >= 0
        self.center = [x, y]
        self.size = size
        self.depth = depth

    def insert(self, item):
        if len(self.children) == 0:
            self.nodes.append(item)

            if len(self.nodes) > self.MAX and self.depth < self.MAX_DEPTH:
                self.split()
                return item
        else:
            return self.insert_into_children(item)
    # end def

    def remove(self, item, update=True):
        items, parents = self.query(item.rect)
        for i in range(len(parents)):
            found_item = items[i]
            if found_item == item:
                parent = parents[i]
                parent.nodes.remove(item)
                if update:
                    parent.update()
    # end def

    def update(self):
        total_nodes = 0

        if len(self.children) > 0:
            for child in self.children:
                total_nodes += child.update()

            if total_nodes <= self.join_threshold:
                self.join()
        else:
            total_nodes = len(self.nodes)

            if total_nodes >= self.split_threshold:
                if self.split():
                    # If it split successfully, see if we can do it again
                    self.update()
        return total_nodes
    # end def

    def insert_into_children(self, item):

        # if rect spans center then insert here
        rect = item.rect()
        if ((rect[0] <= self.center[0] and rect[2] > self.center[0]) and
                (rect[1] <= self.center[1] and rect[3] > self.center[1])):
            self.nodes.append(item)
            return item
        else:

            # try to insert into children
            if rect[0] <= self.center[0]:
                if rect[1] <= self.center[1]:
                    return self.children[0].insert(item, rect)
                if rect[3] > self.center[1]:
                    return self.children[1].insert(item, rect)
            if rect[2] > self.center[0]:
                if rect[1] <= self.center[1]:
                    return self.children[2].insert(item, rect)
                if rect[3] > self.center[1]:
                    return self.children[3].insert(item, rect)
            for child in self.children:
                if child.box.containsPoint

    def split(self):
        self.children = [QuadTree(self.center[0] - self.size/2,
                                  self.center[1] - self.size/2,
                                  self.size/2, self.depth + 1),
                         QuadTree(self.center[0] - self.size/2,
                                  self.center[1] + self.size/2,
                                  self.size/2, self.depth + 1),
                         QuadTree(self.center[0] + self.size/2,
                                  self.center[1] - self.size/2,
                                  self.size/2, self.depth + 1),
                         QuadTree(self.center[0] + self.size/2,
                                  self.center[1] + self.size/2,
                                  self.size/2, self.depth + 1)]

        nodes = self.nodes
        self.nodes = []
        for node in nodes:
            self.insert_into_children(item)
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

    def query(self, rect, item_results=None, parent_results=None):

        if item_results is None:
            item_results = []
            parent_results = []     # keep track of parents for deletion

        # search children
        if len(self.children) > 0:
            if rect[0] <= self.center[0]:
                if rect[1] <= self.center[1]:
                    self.children[0].query(rect, item_results, parent_results)
                if rect[3] > self.center[1]:
                    self.children[1].query(rect, item_results, parent_results)
            if rect[2] > self.center[0]:
                if rect[1] <= self.center[1]:
                    self.children[2].query(rect, item_results, parent_results)
                if rect[3] > self.center[1]:
                    self.children[3].query(rect, item_results, parent_results)
        else:
            # search node at this level
            for item in self.nodes:
                if item.rect[2] > rect[0] and item.rect[0] <= rect[2] and
                        item.rect[3] > rect[1] and item.rect[1] <= rect[3]:
                    item_parent = self
                    item_results.append(item)
                    parent_results.append(item_parent)
        return (item_results, parent_results)
    # end def

    def get_size(self):
        size = 0
        for child in self.children:
            size += child.get_size()
        size += len(self.nodes)
        return size
    # end def