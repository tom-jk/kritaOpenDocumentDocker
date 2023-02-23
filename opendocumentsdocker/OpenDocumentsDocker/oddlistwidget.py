from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QListWidget, QScroller, QAbstractItemView
from krita import *

class ODDListWidget(QListWidget):
    def __init__(self, odd):
        self.odd = odd
        self.mouseEntered = False
        self.itemHovered = None
        self._itemRects = None
        self._itemRectsValid = False
        self._itemRectsRecaching = False
        self._doNotRecacheItemRects = False
        self._childrenRect = QRect(0, 0, 0, 0)
        super(ODDListWidget, self).__init__()
        self.horizontalScrollBar().installEventFilter(self)
        self.verticalScrollBar().installEventFilter(self)
        
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
                self.itemHovered = None
                self.odd.listToolTip.hide()
                self.viewport().update()
        return False
    
    def resizeEvent(self, event):
        print("ODDListWidget:resizeEvent:", event.size().width(), event.size().height())
        self.odd.restartResizeDelayTimer()
    
    def enterEvent(self, event):
        self.mouseEntered = True
        self.viewport().update()
    
    def leaveEvent(self, event):
        if self.itemHovered:
            self.itemHovered = None
            self.odd.listToolTip.hide()
        self.mouseEntered = False
        self.viewport().update()
    
    def mouseMoveEvent(self, event):
        oldItemHovered = self.itemHovered
        self.itemHovered = self.itemAt(event.x(), event.y())
        if not self.itemHovered:
            if oldItemHovered:
                self.odd.listToolTip.hide()
                self.viewport().update()
        else:
            if self.itemHovered != oldItemHovered:
                self.odd.itemEntered(self.itemHovered)
                self.viewport().update()
    
    def invalidateItemRectsCache(self):
        #print("itemRects cache invalidated")
        self._itemRectsValid = False
    
    def itemRects(self):
        if self._itemRectsValid:
            if len(self._itemRects) == self.count():
                return self._itemRects
            else:
                print("itemRectsValid but wrong count!")
        
        if not self.odd.vs.readSetting("display") == "thumbnails":
            return None
        
        if self._doNotRecacheItemRects:
            #print("ODDListWidget.itemRects: tried to recache, but was told doNotRecache, aborting...")
            return self._itemRects
        
        assert not self._itemRectsRecaching, "ODDListWidget.itemRects: started recaching while already recaching!"
        
        count = self.count()
        if count == 0:
            return None
        
        print("regenerate itemRects cache")
        self._itemRectsRecaching = True
        itemRects = []
        
        if self.flow() == QListView.TopToBottom:
            x = y = xExt = 0
            yExt = 2
        else:
            x = y = yExt = 0
            xExt = 2
        #print("count:", count)
        for i in range(count):
            item = self.item(i)
            size = self.odd.calculateDisplaySizeForThumbnail(item.data(self.odd.ItemDocumentSizeRole))
            itemRects.append(QRect(x, y, size.width(), size.height()))
            #print("appended ", itemRects[i])
            if self.flow() == QListView.TopToBottom:
                y += size.height() + yExt
            else:
                x += size.width() + xExt
        self._itemRects = itemRects
        self._itemRectsValid = True
        self._itemRectsRecaching = False
        return self._itemRects
    
    def updateScrollBarRange(self):
        itemRects = self.itemRects()
        if not itemRects:
            return
        rect = itemRects[-1]
        right  = rect.x() + rect.width()
        bottom = rect.y() + rect.height()
        if self.flow() == QListView.TopToBottom:
            #print("vscroll max =", bottom, "-", self.viewport().height(), "=", bottom-self.viewport().height())
            self.verticalScrollBar().setRange(0, bottom - self.viewport().height())
            self._childrenRect = QRect(0, 0, self.viewport().width(), bottom)
            self.horizontalScrollBar().setRange(0, 0)
        else:
            #print("hscroll max =", right, "-", self.viewport().width(), "=", right-self.viewport().width())
            self.horizontalScrollBar().setRange(0, right - self.viewport().width())
            self._childrenRect = QRect(0, 0, right, self.viewport().height())
            self.verticalScrollBar().setRange(0, 0)
    
    def indexAt(self, point):
        if not self.odd.vs.readSetting("display") == "thumbnails":
            return super().indexAt(point)
        
        itemRects = self.itemRects()
        count = self.count()
        point += QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
        for i in range(0, count):
            if itemRects[i].contains(point):
                return self.indexFromItem(self.item(i))
        return self.indexFromItem(None)
    
    def visualItemRect(self, item):
        if not self.odd.vs.readSetting("display") == "thumbnails":
            return super().visualItemRect(item)
        
        itemRects = self.itemRects()
        count = self.count()
        for i in range(0, count):
            if self.item(i) == item:
                return itemRects[i].translated(-self.horizontalScrollBar().value(), -self.verticalScrollBar().value())
    
    def childrenRect(self):
        if not self.odd.vs.readSetting("display") == "thumbnails":
            return super().childrenRect()
        
        self.itemRects()
        return self._childrenRect
    
    def scrollTo(self, index, hint=QAbstractItemView.EnsureVisible):
        if not self.odd.vs.readSetting("display") == "thumbnails":
            super().scrollTo(index, hint)
            return
        
        #print("scrollTo: ", index, index.row(), index.column(), index.data(), self.itemFromIndex(index))
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
        if not self.odd.vs.readSetting("display") == "thumbnails":
            return super().updateGeometries()
        #print("ODDListWidget: updateGeometries")
        self.updateScrollBarRange()
        self.horizontalScrollBar().setSingleStep(32)
        self.verticalScrollBar().setSingleStep(32)
        self.horizontalScrollBar().setPageStep(128)
        self.verticalScrollBar().setPageStep(128)
    
    def paintEvent(self, event):
        if not self.odd.vs.readSetting("display") == "thumbnails":
            super().paintEvent(event)
            return
        
        activeDoc = Application.activeDocument()
        activeUid = self.odd.documentUniqueId(activeDoc) if activeDoc else None
        #print("paintEvent:", event.rect())
        option = self.viewOptions()
        painter = QPainter(self.viewport())
        count = self.count()
        fadeAmount = self.odd.vs.settingValue("thumbFadeAmount")
        
        modIconPreview = self.odd.vs.previewThumbnailsShowModified
        modIconTypeSetting = self.odd.vs.readSetting("thumbShowModified")
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
        if not self.odd.vs.settingValue("thumbFadeUnfade"):
            opacityListHoveredNotActive = opacityItemHoveredNotActive = opacityNotHoveredNotActive
            opacityListHoveredActive = opacityItemHoveredActive = opacityNotHoveredActive
        
        for i in range(count):
            item = self.item(i)
            isItemActiveDoc = item.data(self.odd.ItemDocumentRole) == activeUid
            itemRect = self.itemRects()[i].translated(-self.horizontalScrollBar().value(), -self.verticalScrollBar().value())
            option.rect = itemRect
            option.showDecorationSelected = (item in self.selectedItems())
            painter.setOpacity(
                    opacityItemHoveredActive if (item == self.itemHovered and isItemActiveDoc) else (
                            opacityItemHoveredNotActive if (item == self.itemHovered) else (
                                    opacityListHoveredActive if (self.mouseEntered and isItemActiveDoc) else (
                                            opacityListHoveredNotActive if (self.mouseEntered) else (
                                                    opacityNotHoveredActive if isItemActiveDoc else opacityNotHoveredNotActive
                                            )
                                    )
                            )
                    )
            )
            inView = (not (itemRect.bottom() < 0 or itemRect.y() > self.viewport().height())) if self.flow() == QListView.TopToBottom \
                    else (not (itemRect.right() < 0 or itemRect.x() > self.viewport().width()))
            
            if inView:
                pm = item.data(Qt.DecorationRole)
                x = itemRect.x()
                y = itemRect.y()
                w = itemRect.width()
                h = itemRect.height()
                painter.drawPixmap(itemRect, pm)
                if isItemActiveDoc:
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QColor(255,255,255,127))
                    painter.drawRect(x, y, w-1, h-1)
                    painter.setPen(QColor(0,0,0,127))
                    painter.drawRect(x+1, y+1, w-3, h-3)
                if (item.data(self.odd.ItemModifiedStatusRole) or modIconPreview != "") and canShowModIcon:
                    topRight = QPoint(x + w-1, y)
                    if isModIconTypeText:
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
                        brush.setColor(QColor(255,180,150))
                        painter.setBrush(brush)
                        painter.setPen(QColor(16,16,16))
                        if isModIconTypeCorner:
                            painter.drawConvexPolygon(cornerPoly.translated(topRight))
                        elif isModIconTypeSquare:
                            painter.drawRect(topRight.x() - modIconSize - padding, topRight.y() + padding, modIconSize, modIconSize)
                        elif isModIconTypeCircle:
                            painter.drawEllipse(topRight.x() - modIconSize - padding, topRight.y() + padding, modIconSize, modIconSize)
        painter.end()
