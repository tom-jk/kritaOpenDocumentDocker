# SPDX-License-Identifier: GPL-3.0-or-later

from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtWidgets import QListWidget, QScroller, QAbstractItemView
from krita import *
from .odd import ODD
from .oddviewprocessor import ODDViewProcessor

import logging
logger = logging.getLogger("odd")


class ODDListWidget(QListWidget):
    def __init__(self, odd, oddDocker):
        self.odd = odd
        self.oddDocker = oddDocker
        self.mouseEntered = False
        self.itemHovered = None
        self._itemRects = None
        self._itemRectsValid = False
        self._itemRectsRecaching = False
        self._doNotRecacheItemRects = False
        self._childrenExtent = 0
        self._childrenRect = QRect(0, 0, 0, 0)
        self._itemsToDraw = []
        self._isItemsToDrawDirty = True
        super(ODDListWidget, self).__init__()
        self.horizontalScrollBar().installEventFilter(self)
        self.verticalScrollBar().installEventFilter(self)
        
        self.unfadeDelayTimer = QTimer(self)
        self.unfadeDelayTimer.setInterval(100)
        self.unfadeDelayTimer.setSingleShot(True)
        self.unfadeDelayTimer.timeout.connect(self.unfadeDelayTimerTimeout)
        
        self.hideScrollBars = False
        if Application.readSetting("", "KineticScrollingEnabled", "true") == "true":
            self.setupScroller(QScroller.scroller(self))
            gestureType = self.getConfiguredGestureType()
            QScroller.grabGesture(self, gestureType)
    
    def getConfiguredGestureType(self):
        """
        basically a direct copy (but no different default for android)
        of Krita's KisKineticScroller::getConfiguredGestureType.
        """
        gesture = int(Application.readSetting("", "KineticScrollingGesture", "0"))
        
        if gesture == 0:
            return QScroller.TouchGesture
        elif gesture == 1:
            return QScroller.LeftMouseButtonGesture
        elif gesture == 2:
            return QScroller.MiddleMouseButtonGesture
        elif gesture == 3:
            return QScroller.RightMouseButtonGesture
        else:
            return QScroller.MiddleMouseButtonGesture
    
    def setupScroller(self, scroller):
        """
        basically a direct copy of Krita's
        KisKineticScroller::createPreconfiguredScroller.
        """
        scrProp = scroller.scrollerProperties()
        
        self.hideScrollBars           = True if Application.readSetting("", "KineticScrollingHideScrollbar", "false") == "true" else False
        sensitivity                   =     int(Application.readSetting("", "KineticScrollingSensitivity", "75"))
        resistanceCoefficient         =   float(Application.readSetting("", "KineticScrollingResistanceCoefficient", "10.0"))
        dragVelocitySmoothFactor      =   float(Application.readSetting("", "KineticScrollingDragVelocitySmoothingFactor", "1.0"))
        minimumVelocity               =   float(Application.readSetting("", "KineticScrollingMinimumVelocity", "0.0"))
        axisLockThresh                =   float(Application.readSetting("", "KineticScrollingAxisLockThreshold", "1.0"))
        maximumClickThroughVelocity   =   float(Application.readSetting("", "KineticScrollingMaxClickThroughVelocity", "0.0"))
        flickAccelerationFactor       =   float(Application.readSetting("", "KineticScrollingFlickAccelerationFactor", "1.5"))
        overshootDragResistanceFactor =   float(Application.readSetting("", "KineticScrollingOvershotDragResistanceFactor", "0.1"))
        overshootDragDistanceFactor   =   float(Application.readSetting("", "KineticScrollingOvershootDragDistanceFactor", "0.3"))
        overshootScrollDistanceFactor =   float(Application.readSetting("", "KineticScrollingOvershootScrollDistanceFactor", "0.1"))
        overshootScrollTime           =   float(Application.readSetting("", "KineticScrollingOvershootScrollTime", "0.4"))
        
        mm = 0.001
        resistance = 1.0 - (sensitivity / 100.0)
        mousePressEventDelay = float(Application.readSetting("", "KineticScrollingMousePressDelay", str(1.0 - 0.75 * resistance)))
        
        scrProp.setScrollMetric(QScrollerProperties.DragStartDistance, resistance * resistanceCoefficient * mm)
        scrProp.setScrollMetric(QScrollerProperties.DragVelocitySmoothingFactor, dragVelocitySmoothFactor)
        scrProp.setScrollMetric(QScrollerProperties.MinimumVelocity, minimumVelocity)
        scrProp.setScrollMetric(QScrollerProperties.AxisLockThreshold, axisLockThresh)
        scrProp.setScrollMetric(QScrollerProperties.MaximumClickThroughVelocity, maximumClickThroughVelocity)
        scrProp.setScrollMetric(QScrollerProperties.MousePressEventDelay, mousePressEventDelay)
        scrProp.setScrollMetric(QScrollerProperties.AcceleratingFlickSpeedupFactor, flickAccelerationFactor)
        scrProp.setScrollMetric(QScrollerProperties.OvershootDragResistanceFactor, overshootDragResistanceFactor)
        scrProp.setScrollMetric(QScrollerProperties.OvershootDragDistanceFactor, overshootDragDistanceFactor)
        scrProp.setScrollMetric(QScrollerProperties.OvershootScrollDistanceFactor, overshootScrollDistanceFactor)
        scrProp.setScrollMetric(QScrollerProperties.OvershootScrollTime, overshootScrollTime)
                
        scroller.setScrollerProperties(scrProp)
    
    def eventFilter(self, obj, event):
        if obj in (self.horizontalScrollBar(), self.verticalScrollBar()):
            if event.type() == QEvent.Enter:
                if self.itemHovered:
                    self.itemHovered = None
                    self._isItemsToDrawDirty = True
                self.oddDocker.listToolTip.hide()
                self.viewport().update()
        return False
    
    def resizeEvent(self, event):
        #logger.debug("ODDListWidget:resizeEvent: %s %s", event.size().width(), event.size().height())
        self.oddDocker.restartResizeDelayTimer()
    
    def enterEvent(self, event):
        self.mouseEntered = True
        self.unfadeDelayTimer.start()
        self.viewport().update()
    
    def unfadeDelayTimerTimeout(self):
        self.viewport().update()
    
    def leaveEvent(self, event):
        if self.itemHovered:
            self.itemHovered = None
            self._isItemsToDrawDirty = True
            self.oddDocker.listToolTip.hide()
        self.mouseEntered = False
        self.viewport().update()
    
    def mouseMoveEvent(self, event):
        oldItemHovered = self.itemHovered
        self.itemHovered = self.itemAt(event.x(), event.y())
        if not self.itemHovered:
            if oldItemHovered:
                self.oddDocker.listToolTip.hide()
                self._isItemsToDrawDirty = True
                self.viewport().update()
        else:
            if self.itemHovered != oldItemHovered:
                self.oddDocker.itemEntered(self.itemHovered)
                self._isItemsToDrawDirty = True
                self.viewport().update()
    
    def invalidateItemRectsCache(self):
        #logger.debug("itemRects cache invalidated")
        self._isItemsToDrawDirty = True
        self._itemRectsValid = False
    
    def itemRects(self):
        if self._itemRectsValid:
            if len(self._itemRects) == self.count():
                return self._itemRects
            else:
                logger.info("itemRectsValid but wrong count!")
        
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            return None
        
        if self._doNotRecacheItemRects:
            #logger.info("ODDListWidget.itemRects: tried to recache, but was told doNotRecache, aborting...")
            return self._itemRects
        
        assert not self._itemRectsRecaching, "ODDListWidget.itemRects: started recaching while already recaching!"
        
        count = self.count()
        if count == 0:
            return None
        
        logger.debug("regenerate itemRects cache")
        self._itemRectsRecaching = True
        itemRects = []
        
        isListVertical = self.flow() == QListView.TopToBottom
        
        if self.oddDocker.vs.readSetting("grid") == "true":
            # in vertical grid mode, go right until can't fit, then go down and back left.
            # in horizontal grid mode, go down until can't fit, then go right and back up.
            gridMode = self.oddDocker.vs.readSetting("gridMode")
            
            idealSize = self.oddDocker.calculateDisplaySizeForThumbnail(None, True)
            checkExt = 1.0 * float(self.oddDocker.vs.readSetting("thumbDisplayScale"))
            stackCount = int(self.oddDocker.vs.readSetting("thumbDisplayScaleGrid"))
            if stackCount == 0:
                logger.info("note: stackCount == 0")
                stackCount = 1
            
            if gridMode == "masonry":
                self._itemRectsMasonryLayout(itemRects, count, isListVertical, idealSize, stackCount)
            else:
                self._itemRectsGridLayout(itemRects, count, isListVertical, idealSize, stackCount, gridMode in ["stretchToFit", "cropToFit"])
        else:
            self._itemRectsBasicLayout(itemRects, count, isListVertical)
        
        self._childrenExtent = 0
        for i in range(count):
            r = itemRects[i]
            pos = r.y() + r.height() if isListVertical else r.x() + r.width()
            if pos > self._childrenExtent:
                self._childrenExtent = pos
        
        self._itemRects = itemRects
        self._itemRectsValid = True
        self._itemRectsRecaching = False
        return self._itemRects
            
    def _itemRectsBasicLayout(self, itemRects, count, isListVertical):
        if isListVertical:
            x = y = xExt = 0
            yExt = 2
        else:
            x = y = yExt = 0
            xExt = 2
        for i in range(count):
            item = self.item(i)
            if item.isHidden():
                itemRects.append(QRect(0,0,0,0))
                continue
            size = self.oddDocker.calculateDisplaySizeForThumbnail(item.data(self.oddDocker.ItemDocumentSizeRole), False, True)
            itemRects.append(QRect(x, y, size.width(), size.height()))
            if isListVertical:
                y += size.height() + yExt
            else:
                x += size.width() + xExt
    
    def _itemRectsGridLayout(self, itemRects, count, isListVertical, idealSize, stackCount, isEveryItemSquare):
        x = y = stack = 0
        previousSize = QSize(0, 0)
        
        for i in range(count):
            item = self.item(i)
            if item.isHidden():
                itemRects.append(QRect(0,0,0,0))
                continue
            if stack == stackCount:
                if isListVertical:
                    x = 0
                    y += previousSize.height()
                else:
                    y = 0
                    x += previousSize.width()
                stack = 0
                previousSize = QSize(0, 0)
            if isEveryItemSquare:
                size = idealSize
                previousSize = size
            else:
                size = self.oddDocker.calculateDisplaySizeForThumbnail(item.data(self.oddDocker.ItemDocumentSizeRole))
                previousSize = QSize(max(previousSize.width(), size.width()), max(previousSize.height(), size.height()))
            itemRects.append(QRectF(x, y, size.width(), size.height()).toRect())
            if isListVertical:
                x += size.width()
            else:
                y += size.height()
            stack += 1
    
    def _itemRectsMasonryLayout(self, itemRects, count, isListVertical, idealSize, stackCount):
        stacksPos = []
        stacksEnd = []
        pos = stack = 0
        
        for s in range(stackCount):
            stacksPos.append(pos)
            stacksEnd.append(0)
            pos += idealSize.width() if self.flow() == QListView.TopToBottom else idealSize.height()
        
        for i in range(count):
            item = self.item(i)
            if item.isHidden():
                itemRects.append(QRect(0,0,0,0))
                continue
            docSize = item.data(self.oddDocker.ItemDocumentSizeRole)
            itemSize = self.oddDocker.calculateDisplaySizeForThumbnail(docSize, True, True)
            
            if isListVertical:
                x = stacksPos[stack]
                y = stacksEnd[stack]
                stacksEnd[stack] += itemSize.height()
            else:
                y = stacksPos[stack]
                x = stacksEnd[stack]
                stacksEnd[stack] += itemSize.width()
            
            itemRects.append(QRectF(x, y, itemSize.width(), itemSize.height()).toRect())
            
            stack = stacksEnd.index(min(stacksEnd))
    
    def updateScrollBarRange(self):
        itemRects = self.itemRects()
        if not itemRects:
            return
        if self.flow() == QListView.TopToBottom:
            #logger.debug("vscroll max = %s - %s = %s", self._childrenExtent, self.viewport().height(), self._childrenExtent-self.viewport().height())
            self.verticalScrollBar().setRange(0, self._childrenExtent - self.viewport().height())
            self._childrenRect = QRect(0, 0, self.viewport().width(), self._childrenExtent)
            self.horizontalScrollBar().setRange(0, 0)
        else:
            #logger.debug("hscroll max = %s - %s = %s", self._childrenExtent, self.viewport().width(), self._childrenExtent-self.viewport().width())
            self.horizontalScrollBar().setRange(0, self._childrenExtent - self.viewport().width())
            self._childrenRect = QRect(0, 0, self._childrenExtent, self.viewport().height())
            self.verticalScrollBar().setRange(0, 0)
    
    def indexAt(self, point):
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            return super().indexAt(point)
        
        itemRects = self.itemRects()
        count = self.count()
        point += QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
        for i in range(0, count):
            if itemRects[i].contains(point):
                return self.indexFromItem(self.item(i))
        return self.indexFromItem(None)
    
    def visualItemRect(self, item):
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            return super().visualItemRect(item)
        
        itemRects = self.itemRects()
        count = self.count()
        for i in range(0, count):
            if self.item(i) == item:
                return itemRects[i].translated(-self.horizontalScrollBar().value(), -self.verticalScrollBar().value())
    
    def childrenRect(self):
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            return super().childrenRect()
        
        self.itemRects()
        return self._childrenRect
    
    def scrollTo(self, index, hint=QAbstractItemView.EnsureVisible):
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            super().scrollTo(index, hint)
            return
        
        #logger.debug("scrollTo: %s %s %s %s %s", index, index.row(), index.column(), index.data(), self.itemFromIndex(index))
        item = self.itemFromIndex(index)
        if not item:
            return
        viewRect = self.viewport().rect()
        itemRect = self.visualItemRect(item)
        right  = itemRect.x() + itemRect.width()
        bottom = itemRect.y() + itemRect.height()
        
        if itemRect.left() < 0:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()+itemRect.left())
        elif right > viewRect.width():
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()+right-viewRect.width())
        if itemRect.top() < 0:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()+itemRect.top())
        elif bottom > viewRect.height():
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()+bottom-viewRect.height())
        self.viewport().update()
    
    def updateGeometries(self):
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            return super().updateGeometries()
        #logger.debug("ODDListWidget: updateGeometries")
        self.updateScrollBarRange()
        self.horizontalScrollBar().setSingleStep(32)
        self.verticalScrollBar().setSingleStep(32)
        self.horizontalScrollBar().setPageStep(128)
        self.verticalScrollBar().setPageStep(128)
    
    def paintEvent(self, event):
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            super().paintEvent(event)
            return
        
        count = self.count()
        if count == 0:
            return
        
        qwin = self.oddDocker.parent()
        activeDoc = ODD.activeDocument
        #logger.debug("paintEvent: %s", event.rect())
        option = self.viewOptions()
        painter = QPainter(self.viewport())
        fadeAmount = self.oddDocker.vs.settingValue("thumbFadeAmount")
        
        modIconPreview = self.oddDocker.vs.previewThumbsShowModified
        modIconTypeSetting = self.oddDocker.vs.readSetting("thumbShowModified")
        modIconType = modIconTypeSetting if modIconPreview == "" else modIconPreview
        canShowModIcon = modIconType != "none"
        if canShowModIcon:
            padding = 3
            isModIconTypeText = modIconType in ["asterisk", "asteriskBig"]
            isModIconTypeBig = modIconType in ["cornerBig", "squareBig", "circleBig", "asteriskBig"]
            if isModIconTypeText:
                modIconSize = 24 if isModIconTypeBig else 16
                o = 2 if isModIconTypeBig else 1
                font = painter.font()
                font.setPointSize(modIconSize)
                painter.setFont(font)
                fm = QFontMetrics(font)
                chRect = fm.boundingRectChar("*")
                dropShadowOffset = QPoint(o, o)
                posOffset = QPoint(0 - padding - chRect.x() - chRect.width(), padding - chRect.y())
            else:
                colorModIconFill = QColor(255, 180, 150)
                colorModIconLine = QColor(16, 16, 16)
                isModIconTypeCorner = modIconType in ["corner", "cornerBig"]
                isModIconTypeSquare = modIconType in ["square", "squareBig"]
                isModIconTypeCircle = modIconType in ["circle", "circleBig"]
                modIconSize = 14 if isModIconTypeBig else 8
                if isModIconTypeCorner:
                    cornerPoly = QPolygon([
                            0 - modIconSize, 0,
                            0,               0,
                            0,               0 + modIconSize
                    ])
        
        baseOpacity = 1.0 - fadeAmount
        opacityNotHoveredNotActive  = 0.05 + 0.95 * baseOpacity
        opacityNotHoveredActive     = 0.10 + 0.90 * baseOpacity
        opacityListHoveredNotActive = 0.70 + 0.30 * baseOpacity
        opacityListHoveredActive    = 0.75 + 0.25 * baseOpacity
        opacityItemHoveredNotActive = 0.95 + 0.05 * baseOpacity
        opacityItemHoveredActive    = 1.00
        if self.unfadeDelayTimer.isActive() or not self.oddDocker.vs.settingValue("thumbFadeUnfade"):
            opacityListHoveredNotActive = opacityItemHoveredNotActive = opacityNotHoveredNotActive
            opacityListHoveredActive = opacityItemHoveredActive = opacityNotHoveredActive
        
        isGrid = self.oddDocker.vs.readSetting("grid") == "true"
        if isGrid:
            colorGridLine = self.palette().color(self.backgroundRole())
            isStretchToFit = self.oddDocker.vs.readSetting("gridMode") == "stretchToFit"
        else:
            isStretchToFit = False
        
        aspectLimit = float(self.oddDocker.vs.readSetting("thumbAspectLimit"))
        
        noViewsIconPolyBox = [
            QPointF(2/30, 0.2), QPointF(28/30, 0.2), QPointF(28/30, 1/3),   QPointF(1.0, 1/3),
            QPointF(1.0, 0.0),  QPointF(0.0, 0.0),   QPointF(0.0, 0.8),     QPointF(1.0, 0.8),
            QPointF(1.0, 0.6),  QPointF(28/30, 0.6), QPointF(28/30, 22/30), QPointF(2/30, 22/30),
        ]
        noViewsIconPolyArrow = [
            QPointF(32/30, 0.4),   QPointF(26/30, 0.4),   QPointF(26/30, 8/30),  QPointF(16/30, 14/30),
            QPointF(26/30, 20/30), QPointF(26/30, 16/30), QPointF(32/30, 16/30),
        ]
        
        # make list of (item, itemRect, doc, isActive, isHovered, viewsThisWindowCount, viewsOtherWindowsCount) tuples.
        # include only those that will be visible (not isHidden, not scrolled out of view).
        # the list is ordered as follows: active item, hovered inactive item (if any), remaining items.
        # the first three (active, hovered, first of remainder) will be drawn with their respective painter settings.
        # then all the rest will be drawn with no further changes.
        
        hscroll = self.horizontalScrollBar().value()
        vscroll = self.verticalScrollBar().value()
        vpwidth = self.viewport().width()
        vpheight= self.viewport().height()
        
        if self._isItemsToDrawDirty:
            self._isItemsToDrawDirty = False
            
            viewCountPerWindow = [
                    self.odd.docDataFromDocument(self.item(i).data(self.oddDocker.ItemDocumentRole))["viewCountPerWindow"]
                    for i in range(count)
            ]
            
            self.itemRects()
            self._itemsToDraw = [
                    (
                            self.item(i),
                            self._itemRects[i],
                            self.item(i).data(self.oddDocker.ItemDocumentRole),
                            self.item(i).data(self.oddDocker.ItemDocumentRole) == activeDoc,
                            self.item(i) == self.itemHovered,
                            (self.item(i) in self.selectedItems()),
                            viewCountPerWindow[i][qwin] if qwin in viewCountPerWindow[i] else 0,
                            sum(0 if k == qwin else v for k,v in viewCountPerWindow[i].items()),
                    )
                    for i in range(count)
                    if not self.item(i).isHidden()
            ]
            self._itemsToDraw = sorted(self._itemsToDraw, key = lambda d: not d[4]) # sort by is itemHovered
            self._itemsToDraw = sorted(self._itemsToDraw, key = lambda d: not d[3]) # sort by is activeDoc
            
        # translate item rects and remove out-of-view items.
        itemsToDraw = [
                (i[0], i[1].translated(-hscroll, -vscroll), i[2], i[3], i[4], i[5], i[6], i[7])
                for i in self._itemsToDraw
        ]
        
        itemsToDraw = list(filter(
                lambda v: (not (v[1].bottom() < 0 or v[1].y() > vpheight)) if self.flow() == QListView.TopToBottom \
                          else (not (v[1].right() < 0 or v[1].x() > vpwidth)),
                itemsToDraw
        ))
        
        if len(itemsToDraw) == 0:
            return
        
        # ~ for i in enumerate(itemsToDraw):
            # ~ # print(i[0], i[1])
            # ~ print("#{}: pos in doc list: {}, doc: {}, itemrect: {}, isActive: {}, isHovered: {}, in selectedItems: {}, views this/other wins: {}/{}".format(
                    # ~ i[0],
                    # ~ ODD.documents.index(ODD.docDataFromDocument(i[1][0].data(self.oddDocker.ItemDocumentRole))),
                    # ~ ODD.documentDisplayName(i[1][2]),
                    # ~ i[1][1], i[1][3], i[1][4], i[1][5], i[1][6], i[1][7]
            # ~ ))
        
        # begin main draw loop.
        
        for i in range(3):
            
            # (s for special.)
            s_item = itemsToDraw[i][0]
            s_itemRect = itemsToDraw[i][1]
            s_isItemActiveDoc = itemsToDraw[i][3]
            s_isItemHovered = itemsToDraw[i][4]
            
            if i <= 3:
                painter.setOpacity(
                        opacityItemHoveredActive if (s_item == self.itemHovered and s_isItemActiveDoc) else (
                                opacityItemHoveredNotActive if (s_item == self.itemHovered) else (
                                        opacityListHoveredActive if (self.mouseEntered and s_isItemActiveDoc) else (
                                                opacityListHoveredNotActive if (self.mouseEntered) else (
                                                        opacityNotHoveredActive if s_isItemActiveDoc else opacityNotHoveredNotActive
                                                )
                                        )
                                )
                        )
                )
            
            rStart = i
            rEnd = len(itemsToDraw) if not (s_isItemActiveDoc or s_isItemHovered) else rStart+1
            # ~ print("i:{}, range:{}-{}, opacity:{}".format(i, rStart, rEnd, painter.opacity()))
            
            # draw pixmap.
            for itemToDraw in range(rStart, rEnd):
                item, itemRect = itemsToDraw[itemToDraw][0], itemsToDraw[itemToDraw][1]
                #option.rect, option.showDecorationSelected = itemRect, itemsToDraw[itemToDraw][5]
                option.showDecorationSelected = itemsToDraw[itemToDraw][5]
                pm, x, y, w, h = item.data(Qt.DecorationRole), itemRect.x(), itemRect.y(), itemRect.width(), itemRect.height()
                
                if pm:
                    if isStretchToFit:
                        painter.drawPixmap(itemRect, pm)
                    else:
                        cropRect = pm.rect()
                        itemRatio = h/w
                        pmRatio = pm.height()/pm.width()
                        if pmRatio < 1.0:
                            itemToPmScale = pm.height() / h
                            cropWidth = w * itemToPmScale
                            cropRect.setWidth(round(cropWidth))
                            cropRect.moveLeft(round((pm.width() - cropWidth) / 2))
                            #logger.debug("%s %s %s %s", itemRect, pm.rect(), itemToPmScale, cropRect)
                        elif pmRatio > 1.0:
                            itemToPmScale = pm.width() / w
                            cropHeight = h * itemToPmScale
                            cropRect.setHeight(round(cropHeight))
                            cropRect.moveTop(round((pm.height() - cropHeight) / 2))
                            #logger.debug("%s %s %s %s", itemRect, pm.rect(), itemToPmScale, cropRect)
                        cropRect.moveLeft(max(0, cropRect.left()))
                        cropRect.moveTop(max(0, cropRect.top()))
                        cropRect.setWidth(min(pm.width(), cropRect.width()))
                        cropRect.setHeight(min(pm.height(), cropRect.height()))
                        #logger.debug("#"+str(i)+": %s %s %s", itemRect, QRect(0,0,pm.width(),pm.height()), cropRect)
                        painter.drawPixmap(itemRect, pm, cropRect)
            
            # draw active item border.
            if s_isItemActiveDoc:
                item, itemRect = s_item, s_itemRect
                option.rect, option.showDecorationSelected = itemRect, itemsToDraw[i][5]
                x, y, w, h = itemRect.x(), itemRect.y(), itemRect.width(), itemRect.height()
                
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QColor(255,255,255,127))
                o = int(isGrid)
                painter.drawRect(x, y, w-1-o, h-1-o)
                painter.setPen(QColor(0,0,0,127))
                painter.drawRect(x+1, y+1, w-3-o, h-3-o)
            
            # draw icons.
            if canShowModIcon:
                if isModIconTypeText:
                    for itemToDraw in range(rStart, rEnd):
                        item, itemRect = itemsToDraw[itemToDraw][0], itemsToDraw[itemToDraw][1]
                        #option.rect, option.showDecorationSelected = itemRect, itemsToDraw[itemToDraw][5]
                        option.showDecorationSelected = itemsToDraw[itemToDraw][5]
                        x, y, w, h = itemRect.x(), itemRect.y(), itemRect.width(), itemRect.height()
                        
                        if item.data(self.oddDocker.ItemModifiedStatusRole) or modIconPreview != "":
                            topRight = QPoint(x + w-1, y)
                            font = painter.font()
                            font.setWeight(QFont.ExtraBold)
                            painter.setFont(font)
                            pos = topRight + posOffset
                            painter.setPen(QColor(16,16,16))
                            painter.drawText(pos + dropShadowOffset, "*")
                            font.setWeight(QFont.Normal)
                            painter.setFont(font)
                            painter.setPen(QColor(239,239,239))
                            painter.drawText(pos, "*")
                            
                else:
                    brush = painter.brush()
                    brush.setStyle(Qt.SolidPattern)
                    brush.setColor(colorModIconFill)
                    painter.setBrush(brush)
                    painter.setPen(colorModIconLine)
                    for itemToDraw in range(rStart, rEnd):
                        item, itemRect = itemsToDraw[itemToDraw][0], itemsToDraw[itemToDraw][1]
                        #option.rect, option.showDecorationSelected = itemRect, itemsToDraw[itemToDraw][5]
                        option.showDecorationSelected = itemsToDraw[itemToDraw][5]
                        x, y, w, h = itemRect.x(), itemRect.y(), itemRect.width(), itemRect.height()
                        
                        if item.data(self.oddDocker.ItemModifiedStatusRole) or modIconPreview != "":
                            topRight = QPoint(x + w-1, y)
                            if isModIconTypeCorner:
                                painter.drawConvexPolygon(cornerPoly.translated(topRight))
                            elif isModIconTypeSquare:
                                painter.drawRect(topRight.x() - modIconSize - padding, topRight.y() + padding, modIconSize, modIconSize)
                            elif isModIconTypeCircle:
                                painter.drawEllipse(topRight.x() - modIconSize - padding, topRight.y() + padding, modIconSize, modIconSize)
            
            # draw grid lines.
            if isGrid:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(colorGridLine)
                
                for itemToDraw in range(rStart, rEnd):
                    item, itemRect = itemsToDraw[itemToDraw][0], itemsToDraw[itemToDraw][1]
                    #option.rect, option.showDecorationSelected = itemRect, itemsToDraw[itemToDraw][5]
                    option.showDecorationSelected = itemsToDraw[itemToDraw][5]
                    x, y, w, h = itemRect.x(), itemRect.y(), itemRect.width(), itemRect.height()
                    
                    painter.drawLine(x, y+h-1, x+w-1, y+h-1)
                    painter.drawLine(x+w-1, y, x+w-1, y+h-1)
            
            # draw no views in window indicator.
            brush = painter.brush()
            brush.setStyle(Qt.SolidPattern)
            brush.setColor(QColor(239,239,239,80))
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setCompositionMode(QPainter.CompositionMode_Difference)
            
            for itemToDraw in range(rStart, rEnd):
                viewsThisWindowCount = itemsToDraw[itemToDraw][6]
                if viewsThisWindowCount == 0:
                    item, itemRect = itemsToDraw[itemToDraw][0], itemsToDraw[itemToDraw][1]
                    #option.rect, option.showDecorationSelected = itemRect, itemsToDraw[itemToDraw][5]
                    option.showDecorationSelected = itemsToDraw[itemToDraw][5]
                    x, y, w, h = itemRect.x(), itemRect.y(), itemRect.width(), itemRect.height()
                    
                    s = min(24, min(w, h))
                    
                    painter.save()
                    painter.scale(s, s)
                    sInv = 1.0/s
                    painter.translate((x+2)*sInv, (y+2)*sInv)
                    painter.drawPolygon(noViewsIconPolyBox, len(noViewsIconPolyBox))
                    painter.translate(0, (-0.2)*sInv)
                    painter.drawPolygon(noViewsIconPolyArrow, len(noViewsIconPolyArrow))
                    painter.restore()
                    
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setRenderHint(QPainter.Antialiasing, False)
                
            if rEnd == len(itemsToDraw):
                break
            
        painter.end()

    def contextMenuEvent(self, event, viewOptionsOnly=False):
        logger.debug("ctx menu event - %s %s", event.globalPos(), event.reason())
        self.oddDocker.listToolTip.hide()
        
        if not self.mouseEntered:
            logger.debug("ctx menu cancelled (mouse not over list)")
            return
        
        app = Application
        listTopLeft = self.mapToGlobal(self.frameGeometry().topLeft())

        pos = QPoint(0, 0)
        if event.reason() == QContextMenuEvent.Mouse:
            item = self.itemFromIndex(self.indexAt(event.globalPos() - listTopLeft))
            if not item:
                logger.debug("ctx menu cancelled (mouse not over item)")
                return
            pos = event.globalPos()
        else:
            # TODO: keyboard support
            #pos = (itemRect.topLeft() + itemRect.bottomRight()) / 2
            return
        
        doc = item.data(self.oddDocker.ItemDocumentRole)
        if not doc:
            logger.warning("ODD: right-clicked an item that has no doc, or points to a doc that doesn't exist!")
            return
        
        docData = ODD.docDataFromDocument(doc)
        activeWin = Application.activeWindow()
        
        views = []
        for view in self.odd.views:
            if view.document() == doc:
                views.append(view)
        wins = []
        for view in views:
            win = view.window()
            if win not in wins:
                wins.append(win)
        
        clickedActionName = None
        
        def setClickedActionName(actionName):
            nonlocal clickedActionName
            clickedActionName = actionName
        
        def addDeferredAction(menu, actionName):
            menu.addAction(app.action(actionName).text(), lambda : setClickedActionName(actionName), app.action(actionName).shortcut())
        
        logger.debug("selected: %s - %s", item, doc.fileName())
        
        menu = QMenu(self)
        menu.addAction(ODD.documentDisplayName(doc))
        menu.actions()[0].setEnabled(False)
        menu.addSeparator()
        viewMenu = menu#menu.addMenu("Views")
        for win in wins:
            a = viewMenu.addAction("View in " + win.qwindow().objectName())
            if win == activeWin and win.activeView().document() == doc:
                a.setEnabled(False)
            a.setData(("goToViewInWin", win))
        a = viewMenu.addAction("New View in This Window")
        a.setData(("newViewInWin", activeWin))
        a = viewMenu.addAction("New View in a New Window")
        a.setData(("newViewInNewWin", None))
        if not viewOptionsOnly:
            menu.addSeparator()
            a = menu.addAction("Close Views in This Window")
            if docData["viewCountPerWindow"][activeWin.qwindow()] == 0 or len(wins) == 1:
                a.setEnabled(False)
            a.setData(("closeViewsInThisWin", None))
            a = menu.addAction("Close Views in All Other Windows")
            if docData["viewCountPerWindow"][activeWin.qwindow()] == 0 or len(wins) == 1:
                a.setEnabled(False)
            a.setData(("closeViewsInOtherWins", None))
            menu.addSeparator()
            addDeferredAction(menu, 'file_save')
            addDeferredAction(menu, 'file_save_as')
            addDeferredAction(menu, 'file_export_file')
            addDeferredAction(menu, 'create_copy')
            menu.addSeparator()
            addDeferredAction(menu, 'file_documentinfo')
            addDeferredAction(menu, 'image_properties')
            menu.addSeparator()
            addDeferredAction(menu, 'ODDQuickCopyMergedAction')
            menu.addSeparator()
            if doc.fileName():
                addDeferredAction(menu, 'ODDFileRevertAction')
            else:
                menu.addAction("Revert")
                menu.actions()[-1].setEnabled(False)
            a = menu.addAction("Close")
            a.setData(("closeDocument", None))
        
        action = menu.exec(pos)
        
        if not action:
            logger.debug("ctx menu exited without selection")
            menu.deleteLater()
            return
        
        aData = action.data()
        if aData:
            if aData[0] == "goToViewInWin":
                logger.info("go to view on doc %s in win %s", doc.fileName(), aData[1].qwindow().objectName())
                win = aData[1]
                win.activate()
                qwin = win.qwindow()
                toView = None
                if qwin in docData["lastViewInWindow"]:
                    toView = docData["lastViewInWindow"][qwin]
                else:
                    logger.warning("ctx menu: tried to go to view in win on doc with no lastViewInWindow for that win.\n" \
                                   "          you might have asked for a window that was still being created?")
                if not toView:
                    if win.activeView().document() != doc:
                        for view in win.views():
                            if view.document() == doc:
                                toView = view
                                break
                if toView:
                    win.showView(toView)
                    toView.setVisible()
            elif aData[0] == "newViewInWin":
                logger.info("new view in win %s", aData[1].qwindow().objectName())
                newview = Application.activeWindow().addView(doc)
                pass
            elif aData[0] == "newViewInNewWin":
                logger.info("new view in new win")
                newwin = Application.openWindow()
                newwin.qwindow().show()
                newview = newwin.addView(doc)
                newwin.activate()
                newwin.showView(newview)
                newview.setVisible()
            elif aData[0] == "closeViewsInThisWin":
                logger.info("close views in this window")
                viewCount = docData["viewCountPerWindow"][activeWin.qwindow()]
                self.viewCloser = ODDViewProcessor(
                    operation = lambda : Application.action('file_close').trigger(),
                    selectionCondition = lambda view : view.document() == doc and view.window() == activeWin,
                    preprocessCallback = lambda: self.prepareToCloseViews(doc, inThisWin=True, count=viewCount),
                    finishedCallback = lambda: self.viewCloserFinished(doc)
                )
                self.viewCloser.targetDoc = doc
                self.viewCloser.start()
            elif aData[0] == "closeViewsInOtherWins":
                logger.info("close views in other windows")
                qwin = activeWin.qwindow()
                viewCount = sum(0 if k == qwin else v for k,v in docData["viewCountPerWindow"].items())
                self.viewCloser = ODDViewProcessor(
                    operation = lambda : Application.action('file_close').trigger(),
                    selectionCondition = lambda view : view.document() == doc and view.window() != activeWin,
                    preprocessCallback = lambda: self.prepareToCloseViews(doc, inThisWin=False, count=viewCount),
                    finishedCallback = lambda: self.viewCloserFinished(doc)
                )
                self.viewCloser.targetDoc = doc
                self.viewCloser.start()
            elif aData[0] == "closeDocument":
                self.docCloser = ODDViewProcessor(
                    operation = lambda : Application.action('file_close').trigger(),
                    selectionCondition = lambda view : view.document() == doc,
                    finishedCallback = lambda: self.docCloserFinished(),
                    preprocessCallbackForMultipleViews = lambda : self.closeDocWithManyViewsPrompt(doc),
                    preprocessCallback = lambda: self.prepareToCloseDoc(doc),
                    lastViewPreProcessCallback = lambda: self.prepareToCloseLastViewOnDoc(doc)
                )
                self.docCloser.targetDoc = doc
                self.docCloser.start()
        else:
            # switch to view on document before running actions on it.
            if app.activeDocument():
                app.activeDocument().waitForDone()
            self.oddDocker.itemClicked(item)
            #app.setActiveDocument(doc)
            doc.waitForDone()
            
            logger.debug("do action %s", clickedActionName)
            app.action(clickedActionName).trigger()
        
        menu.deleteLater()
    
    def closeViewsPrompt(self, doc, inThisWin, count):
        msgBox = QMessageBox(
                QMessageBox.Question,
                "Krita",
                "All views {}on the document <b>'{}'</b> {} will be closed.<br/><br/>Are you sure?".format(
                        "({}) ".format(count) if count else "",
                        self.odd.__class__.documentDisplayName(doc, False, 'Untitled'),
                        "in the current window" if inThisWin else "in all other windows"
                ),
                parent = Application.activeWindow().qwindow()
        )
        btnCancel = msgBox.addButton(QMessageBox.Cancel)
        btnYes    = msgBox.addButton(QMessageBox.Yes)
        msgBox.setDefaultButton(QMessageBox.Yes)
        logger.debug("prompt to close views %s", str(doc)[-15:-1])
        msgBox.exec()
        return msgBox.clickedButton() == btnYes
    
    def prepareToCloseViews(self, doc, inThisWin, count):
        if not self.closeViewsPrompt(doc, inThisWin, count):
            logger.debug("close views cancelled for %s", str(doc)[-15:-1])
            return False
        
        Application.setBatchmode(True)
        doc.setBatchmode(True)
        
        oddDocker = self.odd.dockers[0].__class__
        if oddDocker.imageChangeDetected:
            oddDocker.imageChangeDetected = False
            oddDocker.refreshTimer.stop()
        return True
    
    def viewCloserFinished(self, doc):
        Application.setBatchmode(False)
        doc.setBatchmode(False)
        logger.debug("deleting viewCloser")
        self.viewCloser.deleteLater()
        del self.viewCloser
    
    def closeDocWithManyViewsPrompt(self, doc):
        msgBox = QMessageBox(
                QMessageBox.Warning,
                "Krita",
                "All {} on the document <b>'{}'</b> will be closed{}<br/><br/>Are you sure?".format(
                        "but one view" if doc.modified() else "views",
                        self.odd.__class__.documentDisplayName(doc, False, 'Untitled'),
                        ", then you'll be asked if you wish to save." if doc.modified() else "."
                ),
                parent = Application.activeWindow().qwindow()
        )
        btnCancel = msgBox.addButton(QMessageBox.Cancel)
        btnYes    = msgBox.addButton(QMessageBox.Yes)
        msgBox.setDefaultButton(QMessageBox.Yes)
        logger.debug("prompt to close views %s", str(doc)[-15:-1])
        msgBox.exec()
        if msgBox.clickedButton() == btnCancel:
            logger.debug("close cancelled for %s", str(doc)[-15:-1])
            return False
        return True
    
    def prepareToCloseDoc(self, doc):
        Application.setBatchmode(True)
        doc.setBatchmode(True)
        self.docCloser.wasModified = doc.modified()
        doc.setModified(False)
        
        oddDocker = self.odd.dockers[0].__class__
        if oddDocker.imageChangeDetected:
            oddDocker.imageChangeDetected = False
            oddDocker.refreshTimer.stop()
        return True
    
    def prepareToCloseLastViewOnDoc(self, doc):
        if self.docCloser.wasModified:
            # prompt user to save/cancel before closing last view on doc.
            doc.setModified(True)
            Application.setBatchmode(False)
            doc.setBatchmode(False)
        return True
    
    def docCloserFinished(self):
        logger.debug("deleting docCloser")
        self.docCloser.deleteLater()
        del self.docCloser
