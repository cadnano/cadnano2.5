from .abstractslicetool import AbstractSliceTool
from PyQt5.QtCore import QRect, QRectF, QPointF

class SelectSliceTool(AbstractSliceTool):
    """"""
    def __init__(self, controller, parent=None):
        super(SelectSliceTool, self).__init__(controller)
        self.sgv = None
        self.rubberband_rect = QRect()
        self.last_rubberband_vals = (None, None, None)
        self.selection_set = None

    def __repr__(self):
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "selectTool"  # first letter should be lowercase

    def setPartItem(self, part_item):
        if self.sgv is not None:
            self.sgv.rubberBandChanged.disconnect(self.testRB)
            self.sgv = None
        self.part_item = part_item
        self.sgv = part_item.window().slice_graphics_view
        self.sgv.rubberBandChanged.connect(self.testRB)
    # end def

    def testRB(self, rect, from_pt, to_point):
        rbr_last, fp_last, tp_last = self.last_rubberband_vals
        if rect.isNull() and rbr_last.isValid():
            self.rubberband_rect = rbr_last
            print("rubber band released at", rbr_last)
            part_item = self.part_item
            part = part_item.part()
            # from_pt = QPointF(rbr_last.bottomLeft())
            # to_point = QPointF(rbr_last.topRight())

            from_pt = fp_last
            to_point = tp_last
            from_pt_part_item = part_item.mapFromScene(from_pt)
            to_pt_part_item = part_item.mapFromScene(to_point)
            from_model_point = part_item.getModelPos(from_pt_part_item)
            to_model_point = part_item.getModelPos(to_pt_part_item)
            query_rect = (from_model_point[0], from_model_point[1],
                            to_model_point[0], to_model_point[1])
            print(query_rect)
            res = part.getVirtualHelicesInArea(query_rect)
            print(res)
        else:
            self.last_rubberband_vals = (rect, from_pt, to_point)

    # print

    def deactivate(self):
        AbstractSliceTool.deactivate(self)
        if self.sgv is not None:
            self.sgv.rubberBandChanged.disconnect(self.testRB)
            self.sgv = None
    # end def
