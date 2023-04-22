from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtWidgets import QListWidget, QScroller, QAbstractItemView
from krita import *
from .odd import ODD
from .oddviewprocessor import ODDViewProcessor

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
                self.itemHovered = None
                self.oddDocker.listToolTip.hide()
                self.viewport().update()
        return False
    
    def resizeEvent(self, event):
        #print("ODDListWidget:resizeEvent:", event.size().width(), event.size().height())
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
            self.oddDocker.listToolTip.hide()
        self.mouseEntered = False
        self.viewport().update()
    
    def mouseMoveEvent(self, event):
        oldItemHovered = self.itemHovered
        self.itemHovered = self.itemAt(event.x(), event.y())
        if not self.itemHovered:
            if oldItemHovered:
                self.oddDocker.listToolTip.hide()
                self.viewport().update()
        else:
            if self.itemHovered != oldItemHovered:
                self.oddDocker.itemEntered(self.itemHovered)
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
        
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
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
        
        isListVertical = self.flow() == QListView.TopToBottom
        
        if self.oddDocker.vs.readSetting("grid") == "true":
            # in vertical grid mode, go right until can't fit, then go down and back left.
            # in horizontal grid mode, go down until can't fit, then go right and back up.
            gridMode = self.oddDocker.vs.readSetting("gridMode")
            
            idealSize = self.oddDocker.calculateDisplaySizeForThumbnail(None, True)
            checkExt = 1.0 * float(self.oddDocker.vs.readSetting("thumbDisplayScale"))
            stackCount = int(self.oddDocker.vs.readSetting("thumbDisplayScaleGrid"))
            if stackCount == 0:
                print("note: stackCount == 0")
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
            #print("vscroll max =", self._childrenExtent, "-", self.viewport().height(), "=", self._childrenExtent-self.viewport().height())
            self.verticalScrollBar().setRange(0, self._childrenExtent - self.viewport().height())
            self._childrenRect = QRect(0, 0, self.viewport().width(), self._childrenExtent)
            self.horizontalScrollBar().setRange(0, 0)
        else:
            #print("hscroll max =", self._childrenExtent, "-", self.viewport().width(), "=", self._childrenExtent-self.viewport().width())
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
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            return super().updateGeometries()
        #print("ODDListWidget: updateGeometries")
        self.updateScrollBarRange()
        self.horizontalScrollBar().setSingleStep(32)
        self.verticalScrollBar().setSingleStep(32)
        self.horizontalScrollBar().setPageStep(128)
        self.verticalScrollBar().setPageStep(128)
    
    def paintEvent(self, event):
        if not self.oddDocker.vs.readSetting("display") == "thumbnails":
            super().paintEvent(event)
            return
        
        qwin = self.oddDocker.parent()
        activeDoc = Application.activeDocument()
        #print("paintEvent:", event.rect())
        option = self.viewOptions()
        painter = QPainter(self.viewport())
        count = self.count()
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
        
        noViewsIconPolyBox = [
            QPointF(2/30, 0.2), QPointF(28/30, 0.2), QPointF(28/30, 1/3),   QPointF(1.0, 1/3),
            QPointF(1.0, 0.0),  QPointF(0.0, 0.0),   QPointF(0.0, 0.8),     QPointF(1.0, 0.8),
            QPointF(1.0, 0.6),  QPointF(28/30, 0.6), QPointF(28/30, 22/30), QPointF(2/30, 22/30),
        ]
        noViewsIconPolyArrow = [
            QPointF(32/30, 0.4),   QPointF(26/30, 0.4),   QPointF(26/30, 8/30),  QPointF(16/30, 14/30),
            QPointF(26/30, 20/30), QPointF(26/30, 16/30), QPointF(32/30, 16/30),
        ]
        
        for i in range(count):
            item = self.item(i)
            isItemActiveDoc = item.data(self.oddDocker.ItemDocumentRole) == activeDoc
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
            
            if not inView:
                continue
            
            doc = item.data(self.oddDocker.ItemDocumentRole)
            viewCountPerWindow = self.odd.docDataFromDocument(doc)["viewCountPerWindow"]
            viewsThisWindowCount = viewCountPerWindow[qwin] if qwin in viewCountPerWindow else 0
            viewsOtherWindowsCount = sum(0 if k == qwin else v for k,v in viewCountPerWindow.items())
            
            pm = item.data(Qt.DecorationRole)
            x = itemRect.x()
            y = itemRect.y()
            w = itemRect.width()
            h = itemRect.height()
            
            if pm:
                if isStretchToFit:
                    painter.drawPixmap(itemRect, pm)
                else:
                    aspectLimit = float(self.oddDocker.vs.readSetting("thumbAspectLimit"))
                    cropRect = pm.rect()
                    itemRatio = h/w
                    pmRatio = pm.height()/pm.width()
                    if pmRatio < 1.0:
                        itemToPmScale = pm.height() / h
                        cropWidth = w * itemToPmScale
                        cropRect.setWidth(round(cropWidth))
                        cropRect.moveLeft(round((pm.width() - cropWidth) / 2))
                        #print(itemRect, pm.rect(), itemToPmScale, cropRect)
                    elif pmRatio > 1.0:
                        itemToPmScale = pm.width() / w
                        cropHeight = h * itemToPmScale
                        cropRect.setHeight(round(cropHeight))
                        cropRect.moveTop(round((pm.height() - cropHeight) / 2))
                        #print(itemRect, pm.rect(), itemToPmScale, cropRect)
                    cropRect.moveLeft(max(0, cropRect.left()))
                    cropRect.moveTop(max(0, cropRect.top()))
                    cropRect.setWidth(min(pm.width(), cropRect.width()))
                    cropRect.setHeight(min(pm.height(), cropRect.height()))
                    #print("#"+str(i)+":", itemRect, QRect(0,0,pm.width(),pm.height()), cropRect)
                    painter.drawPixmap(itemRect, pm, cropRect)
            
            if isItemActiveDoc:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QColor(255,255,255,127))
                o = int(isGrid)
                painter.drawRect(x, y, w-1-o, h-1-o)
                painter.setPen(QColor(0,0,0,127))
                painter.drawRect(x+1, y+1, w-3-o, h-3-o)
            if (item.data(self.oddDocker.ItemModifiedStatusRole) or modIconPreview != "") and canShowModIcon:
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
                    brush.setColor(colorModIconFill)
                    painter.setBrush(brush)
                    painter.setPen(colorModIconLine)
                    if isModIconTypeCorner:
                        painter.drawConvexPolygon(cornerPoly.translated(topRight))
                    elif isModIconTypeSquare:
                        painter.drawRect(topRight.x() - modIconSize - padding, topRight.y() + padding, modIconSize, modIconSize)
                    elif isModIconTypeCircle:
                        painter.drawEllipse(topRight.x() - modIconSize - padding, topRight.y() + padding, modIconSize, modIconSize)
            if isGrid:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(colorGridLine)
                painter.drawLine(x, y+h-1, x+w-1, y+h-1)
                painter.drawLine(x+w-1, y, x+w-1, y+h-1)
            
            if viewsThisWindowCount == 0:
                
                brush = painter.brush()
                brush.setStyle(Qt.SolidPattern)
                brush.setColor(QColor(239,239,239,80))
                painter.setBrush(brush)
                painter.setPen(Qt.NoPen)
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setCompositionMode(QPainter.CompositionMode_Difference)
                
                s = min(24, min(w, h))
                
                poly = [i*s + QPointF(x+2, y+2) for i in noViewsIconPolyBox]
                painter.drawPolygon(poly, len(poly))
                
                poly = [i*s + QPointF(x+2, y+1.8) for i in noViewsIconPolyArrow]
                painter.drawPolygon(poly, len(poly))
                
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setRenderHint(QPainter.Antialiasing, False)
        
        painter.end()

    def contextMenuEvent(self, event, viewOptionsOnly=False):
        print("ctx menu event -", event.globalPos(), event.reason())
        self.oddDocker.listToolTip.hide()
        
        if not self.mouseEntered:
            print("ctx menu cancelled (mouse not over list)")
            return
        
        app = Application
        listTopLeft = self.mapToGlobal(self.frameGeometry().topLeft())

        pos = QPoint(0, 0)
        if event.reason() == QContextMenuEvent.Mouse:
            item = self.itemFromIndex(self.indexAt(event.globalPos() - listTopLeft))
            if not item:
                print("ctx menu cancelled (mouse not over item)")
                return
            pos = event.globalPos()
        else:
            # TODO: keyboard support
            #pos = (itemRect.topLeft() + itemRect.bottomRight()) / 2
            return
        
        doc = item.data(self.oddDocker.ItemDocumentRole)
        if not doc:
            print("ODD: right-clicked an item that has no doc, or points to a doc that doesn't exist!")
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
        
        print("selected:", item, " -", doc.fileName())
        
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
            addDeferredAction(menu, 'file_close')
        
        action = menu.exec(pos)
        
        if not action:
            print("ctx menu exited without selection")
            menu.deleteLater()
            return
        
        aData = action.data()
        if aData:
            if aData[0] == "goToViewInWin":
                print("go to view in win", aData[1].qwindow().objectName())
                win = aData[1]
                win.activate()
                qwin = win.qwindow()
                docData = self.odd.docDataFromDocument(doc)
                toView = None
                if qwin in docData["lastViewInWindow"]:
                    toView = docData["lastViewInWindow"][qwin]
                else:
                    print("ctx menu: tried to go to view in win on doc with no lastViewInWindow for that win.\n" \
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
                print("new view in win", aData[1].qwindow().objectName())
                newview = Application.activeWindow().addView(doc)
                pass
            elif aData[0] == "newViewInNewWin":
                print("new view in new win")
                newwin = Application.openWindow()
                newwin.qwindow().show()
                newview = newwin.addView(doc)
                newwin.activate()
                newwin.showView(newview)
                newview.setVisible()
            elif aData[0] == "closeViewsInThisWin":
                print("close views in this window")
                self.viewCloser = ODDViewProcessor(
                    operation = lambda : Application.action('file_close').trigger(),
                    selectionCondition = lambda view : view.document() == doc and view.window() == activeWin,
                    preprocessCallback = lambda: self.prepareToCloseViews(doc, inThisWin=True),
                    finishedCallback = lambda: self.viewCloserFinished(doc)
                )
                self.viewCloser.targetDoc = doc
                self.viewCloser.start()
            elif aData[0] == "closeViewsInOtherWins":
                print("close views in other windows")
                self.viewCloser = ODDViewProcessor(
                    operation = lambda : Application.action('file_close').trigger(),
                    selectionCondition = lambda view : view.document() == doc and view.window() != activeWin,
                    preprocessCallback = lambda: self.prepareToCloseViews(doc, inThisWin=False),
                    finishedCallback = lambda: self.viewCloserFinished(doc)
                )
                self.viewCloser.targetDoc = doc
                self.viewCloser.start()
        elif clickedActionName  == "file_close":
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
            
            print("do action", clickedActionName)
            app.action(clickedActionName).trigger()
        
        menu.deleteLater()
    
    def closeViewsPrompt(self, doc, inThisWin):
        msgBox = QMessageBox(
                QMessageBox.Question,
                "Krita",
                "All {} on the document <b>'{}'</b> {} will be closed.<br/><br/>Are you sure?".format(
                        "but one view" if doc.modified() else "views",
                        self.odd.__class__.documentDisplayName(doc, False, 'Untitled'),
                        "in the current window" if inThisWin else "in all other windows"
                ),
                parent = Application.activeWindow().qwindow()
        )
        btnCancel = msgBox.addButton(QMessageBox.Cancel)
        btnYes    = msgBox.addButton(QMessageBox.Yes)
        msgBox.setDefaultButton(QMessageBox.Yes)
        print("prompt to close views", str(doc)[-15:-1])
        msgBox.exec()
        return msgBox.clickedButton() == btnYes
    
    def prepareToCloseViews(self, doc, inThisWin):
        if not self.closeViewsPrompt(doc, inThisWin):
            print("close views cancelled for", str(doc)[-15:-1])
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
        print("deleting viewCloser")
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
        print("prompt to close views", str(doc)[-15:-1])
        msgBox.exec()
        if msgBox.clickedButton() == btnCancel:
            print("close cancelled for", str(doc)[-15:-1])
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
        print("deleting docCloser")
        self.docCloser.deleteLater()
        del self.docCloser
