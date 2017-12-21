# QGraphicsScene-event-dispatching-overview

Here is a brief overview of the functions through which a mouse press event will descend until it finally reaches a QGraphicsItem.

## Run loop sends a mouse press 

```
bool QGraphicsScene::event(QEvent *event)  //Returns true
void QGraphicsScene::mousePressEvent(QGraphicsSceneMouseEvent *mouseEvent)
void QGraphicsScenePrivate::mousePressEventHandler(QGraphicsSceneMouseEvent *mouseEvent)
    mouseEvent->ignore()
    cachedItemsUnderMouse = QGraphicsScenePrivate::itemsAtPosition(...)
    activate window, widget (modal panel can intercept)
    go in order through cachedItemsUnderMouse, try to setFocusItem on them
    foreach thru cachedItemsUnderMouse again
      check the item's acceptedMouseButtons, skip if required
      grab the mouse
      *** ACCEPT THE EVENT ***
      void QGraphicsScenePrivate::sendMouseEvent(QGraphicsSceneMouseEvent *mouseEvent)
        bool QGraphicsScenePrivate::sendEvent(QGraphicsItem *item, QEvent *event)
          return item->sceneEvent(event)
        ignore retval of sendEvent
      *** if mouseEvent->isAccepted() return ***
      ungrab
    propagate to view
```

## QGraphicsItem receives a mouse press
```
The only default event->accept()ing that goes on is for popup widget closing
bool QGraphicsItem::sceneEvent(QEvent *event)
  void QGraphicsItem::mousePressEvent(QGraphicsSceneMouseEvent *event)
  ignore mousePressEvent retval and return true
```

## Rubber Banding
```
void QGraphicsView::mouseMoveEvent(QMouseEvent *event)
  If dragMode is QGraphicsView::RubberBandDrag and scene interaction allowed, proceed.
  If rubberBanding, proceed
  Dirty the viewport
  void QGraphicsScene::setSelectionArea(const QPainterPath &path, Qt::ItemSelectionMode mode,
                                        const QTransform &deviceTransform)
    foreach item in QGraphicsScene::items(selection rect, descending order)
      if (item->flags() & QGraphicsItem::ItemIsSelectable)
        item->setSelected(true)
    foreach unselectedItem
      item->setSelected(false)
    emit selectionChanged()
```