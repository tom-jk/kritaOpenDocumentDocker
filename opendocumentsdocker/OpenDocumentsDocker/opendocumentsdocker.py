# SPDX-License-Identifier: CC0-1.0

from PyQt5.QtCore import Qt, QByteArray, QBuffer, QPoint, QSize
from PyQt5.QtGui import QPixmap, QScreen, QContextMenuEvent
from PyQt5.QtWidgets import QWidget, QBoxLayout, QVBoxLayout, QHBoxLayout, QListView, QPushButton, QMenu, QAbstractItemView, QListWidget, QListWidgetItem, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QSizePolicy, QScroller
from krita import *
from time import *
import uuid
from pathlib import Path
from .opendocumentsviewsettings import OpenDocumentsViewSettings as ODVS, convertSettingStringToValue, convertSettingValueToString

class ODDListWidget(QListWidget):
    def __init__(self, odd):
        self.odd = odd
        self.mouseEntered = False
        self.itemHovered = None
        super(ODDListWidget, self).__init__()
        self.horizontalScrollBar().installEventFilter(self)
        self.verticalScrollBar().installEventFilter(self)
        
        QScroller.grabGesture(self, QScroller.MiddleMouseButtonGesture)
        self.setupScroller(QScroller.scroller(self))
    
    def setupScroller(self, scroller):
        """
        basically a direct copy of Krita's
        KisKineticScroller::createPreconfiguredScroller.
        """
        scrProp = scroller.scrollerProperties()
        
        sensitivity                   =     int(Application.readSetting("", "KineticScrollingSensitivity", "75"))
        enabled                       = True if Application.readSetting("", "KineticScrollingEnabled", "true") == "true" else False
        hideScrollBars                = True if Application.readSetting("", "KineticScrollingHideScrollbar", "false") == "true" else False
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
    
    def itemPositions(self):
        # TODO: remake item pos cache only if dirty
        self._itemPositions = []
        if self.odd.vs.readSetting("display") == "thumbnails":
            scrollSize = 0
            if self.flow() == QListView.TopToBottom:
                x = 0
                y = -self.verticalScrollBar().value()
                xExt = 0
                yExt = 2
            else:
                x = -self.horizontalScrollBar().value()
                y = 0
                xExt = 2
                yExt = 0
            count = self.count()
            for i in range(count):
                item = self.item(i)
                size = item.data(Qt.DecorationRole).size()
                self._itemPositions.append(QRect(x, y, size.width() + xExt, size.height() + yExt))
                if self.flow() == QListView.TopToBottom:
                    y += size.height() + yExt
                    scrollSize += size.height() + yExt
                else:
                    x += size.width() + xExt
                    scrollSize += size.width() + xExt
            if self.flow() == QListView.TopToBottom:
                self.verticalScrollBar().setRange(0, scrollSize - self.viewport().height())
            else:
                self.horizontalScrollBar().setRange(0, scrollSize - self.viewport().width())
    
    def indexAt(self, point):
        print("indexAt:", point)
        self.itemPositions()
        count = self.count()
        for i in range(0, count):
            if self._itemPositions[i].contains(point):
                print(" ->", i)
                return self.indexFromItem(self.item(i))
        return self.indexFromItem(None)
    
    def paintEvent(self, event):
        activeDoc = Application.activeDocument()
        activeUid = self.odd.documentUniqueId(activeDoc) if activeDoc else None
        #print("paintEvent:", event.rect())
        if self.odd.vs.readSetting("display") == "thumbnails":
            option = self.viewOptions()
            painter = QPainter(self.viewport())
            self.itemPositions()
            count = self.count()
            setting = self.odd.vs.settingValue("thumbFadeAmount")
            baseOpacity = 1.0 - setting
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
                option.rect = self._itemPositions[i]
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
                idel = self.itemDelegate(self.indexFromItem(item))
                #size = idel.sizeHint(option, self.indexFromItem(item))
                size = option.rect.size()
                inView = (not (option.rect.bottom() < 0 or option.rect.y() > self.viewport().height())) if self.flow() == QListView.TopToBottom \
                        else (not (option.rect.right() < 0 or option.rect.x() > self.viewport().width()))
                if inView:
                    #idel.paint(painter, option, self.indexFromItem(item))
                    pm = item.data(Qt.DecorationRole)
                    x = option.rect.x()
                    y = option.rect.y()
                    painter.drawPixmap(QPoint(x, y), pm)
                    if isItemActiveDoc:
                        painter.setPen(QColor(255,255,255,127))
                        painter.drawRect(x, y, pm.width(), pm.height())
                        painter.setPen(QColor(0,0,0,127))
                        painter.drawRect(x+1, y+1, pm.width()-2, pm.height()-2)
                    # TODO: How do we get doc modified status without incurring Application.documents() memory leak?
                    if False:#self.odd.findDocumentWithItem(item).modified():
                        rect = QRect(x, y, pm.width()-2, pm.height()-2)
                        font = painter.font()
                        font.setPointSize(16)
                        painter.setFont(font)
                        painter.setPen(QColor(0,0,0))
                        painter.drawText(rect.translated(-1,-1), Qt.AlignRight | Qt.AlignTop, "*")
                        painter.drawText(rect.translated(1,-1), Qt.AlignRight | Qt.AlignTop, "*")
                        painter.drawText(rect.translated(-1,1), Qt.AlignRight | Qt.AlignTop, "*")
                        painter.drawText(rect.translated(1,1), Qt.AlignRight | Qt.AlignTop, "*")
                        painter.setPen(QColor(255,255,255))
                        painter.drawText(rect, Qt.AlignRight | Qt.AlignTop, "*")
            painter.end()
        else:
            super().paintEvent(event)


class OpenDocumentsDocker(krita.DockWidget):
    ItemDocumentRole = Qt.UserRole
    ItemUpdateDeferredRole = Qt.UserRole+1
    
    imageChangeDetected = False
    
    # https://krita-artists.org/t/scripting-open-an-existing-file/32124/4
    def findAndActivateView(self, doc):
        app = Application
        for win in app.windows():
            for view in win.views():
                if view.document() == doc:
                    win.activate()
                    win.showView(view)
                    view.setVisible()
                    return
    
    def documentHasViews(self, doc, exception):
        """
        returns true if at least one open view shows this document
        (any view besides exception, if provided).
        """
        for win in Application.windows():
            for view in win.views():
                if view != exception:
                    if self.documentUniqueId(view.document()) == self.documentUniqueId(doc):
                        return True
        return False
    
    def itemClicked(self, item):
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if doc:
            self.findAndActivateView(doc)
        else:
            print("ODD: clicked an item that has no doc, or points to a doc that doesn't exist!")
    
    def documentDisplayName(self, doc, showIfModified=True):
        fPath = doc.fileName()
        fName = Path(fPath).name
        tModi = " *" * doc.modified() * showIfModified
        return (fName if fName else "[not saved]") + tModi
    
    def itemEntered(self, item):
        if not self.vs.settingValue("tooltipShow"):
            return
        
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if not doc:
            return
        
        fPath = doc.fileName()
        ttText = ""
        
        ttText += "<table border='0' style='margin:16px; padding:16px'><tr>"
        
        # From answer to "Use a picture or image in a QToolTip": https://stackoverflow.com/a/34300771
        pxCount = doc.width() * doc.height()
        if pxCount <= self.vs.settingValue("tooltipThumbLimit"):
            size = self.vs.settingValue("tooltipThumbSize")
            img = doc.thumbnail(size, size)
            data = QByteArray()
            buffer = QBuffer(data)
            img.save(buffer, "PNG", 100)
            imgHtml = "<img src='data:image/png;base64, " + str(data.toBase64()).split("'")[1] + "'>"
        else:
            imgHtml = "(image too big)"
        
        ttText += "<td><table border='1'><tr><td>" + imgHtml + "</td></tr></table></td>"
        ttText += "<td style='padding-left: 8px'><h2 style='margin-bottom:0px'>" + self.documentDisplayName(doc) + "</h2>"
        ttText += "<p style='white-space:pre; margin-top:0px'><small>" + fPath + "</small></p>"
        ttText += "<p style='margin-top:0px'><small>" + str(doc.width()) + " x " + str(doc.height()) + "</small></p>"
        ttText += "</td>"
        ttText += "</tr></table>"
        
        self.listToolTip.setText(ttText)
        
        ttPos = None
        
        listTopLeft = self.list.mapToGlobal(self.list.frameGeometry().topLeft())
        listBottomRight = self.list.mapToGlobal(self.list.frameGeometry().bottomRight())
        listTopRight = self.list.mapToGlobal(self.list.frameGeometry().topRight())
        listCenter = (listTopLeft+listBottomRight)/2
        itemRect = self.list.visualItemRect(item)
        
        if hasattr(self, "screen"):
            # work out which side of the widget has the most space and put the tooltip there.
            screen = self.screen()            
            screenTopLeft = screen.availableGeometry().topLeft()
            screenBottomRight = screen.availableGeometry().bottomRight()
            screenCenter = (screenTopLeft+screenBottomRight)/2
            if self.list.flow() == QListView.TopToBottom:
                if listCenter.x() < screenCenter.x():
                    ttPos = listTopRight + itemRect.topLeft()
                else:
                    ttPos = listTopLeft + QPoint(-self.listToolTip.sizeHint().width(), itemRect.top())
            else:
                if listCenter.y() < screenCenter.y():
                    ttPos = listTopLeft + itemRect.bottomLeft()
                else:
                    ttPos = listTopLeft + QPoint(itemRect.left(), -self.listToolTip.sizeHint().height())
        else:
            # fallback to using dock area
            if self.list.flow() == QListView.TopToBottom:
                if self.dockLocation == Qt.LeftDockWidgetArea or self.dockLocation == Qt.TopDockWidgetArea:
                    ttPos = listTopRight + itemRect.topLeft()
                else:
                    ttPos = listTopLeft + QPoint(-self.listToolTip.sizeHint().width(), itemRect.top())
            else:
                if self.dockLocation == Qt.LeftDockWidgetArea or self.dockLocation == Qt.TopDockWidgetArea:
                    ttPos = listTopLeft + itemRect.bottomLeft()
                else:
                    ttPos = listTopLeft + QPoint(itemRect.left(), -self.listToolTip.sizeHint().height())
        
        self.listToolTip.move(ttPos)
        self.listToolTip.adjustSize()
        self.listToolTip.show()
    
    def delayedResize(self):
        self.resizeDelay.stop()
        print("delayedResize: lastSize:", self.lastSize)
        print("               new size:", self.baseWidget.size())
        lastFlow = self.list.flow()
        self.setDockerDirection(self.vs.readSetting("direction"))
        if self.lastSize == self.baseWidget.size():
            print("delayedResize: size did not change - no refresh.")
        elif self.list.flow() == lastFlow and (
                (lastFlow == QListView.TopToBottom and self.lastSize.width() == self.baseWidget.size().width()) or
                (lastFlow == QListView.LeftToRight and self.lastSize.height() == self.baseWidget.size().height())
        ):
            print("delayedResize: list is longer/shorter, but not narrower/wider - no refresh.")
        else:
            print("delayedResize: size changed - refresh.")
            self.refreshOpenDocuments(soft=True)
        self.lastSize = self.baseWidget.size()
    
    def imageCreated(self, image):
        print("image created -", image, end=" ")
        fName = image.fileName()
        print("name:", (fName if fName else "[not saved]"))
        
        docCount = len(Application.documents())
        for i in range(docCount):
            d = Application.documents()[i]
            print("#"+str(i)+":", d, "-", d.rootNode().uniqueId())
        
        # assume new image will always doc at end of documents list.
        doc = Application.documents()[docCount-1]
        self.setDocumentExtraUid(doc)
        self.addDocumentToList(doc)
    
    def isDocumentUniquelyIdentified(self, doc):
        uid = doc.rootNode().uniqueId()
        extraUid = doc.annotation("ODD_extra_uid") or b''
        docCount = len(Application.documents())
        for i in range(docCount):
            d = Application.documents()[i]
            if d != doc:
                if uid == d.rootNode().uniqueId():
                    if extraUid == d.annotation("ODD_extra_uid"):
                        return False
        return True
        
    def setDocumentExtraUid(self, doc):
        """
        Compares a document's uid/extraUid against all other open documents, and:
         If any share both uid and extraUid (ie. both have empty extraUid's):
          assign this document a new extraUid.
         If any share uid but not extraUid:
          do nothing, document is satisfactorily disambiguated.
         If none share uid:
          remove extraUid from document if it has one, it no longer needs it.
        """
        isUnique = True
        canRemoveExtraUid = True
        uid = doc.rootNode().uniqueId()
        extraUid = doc.annotation("ODD_extra_uid") or b''
        #print("doc:      ", doc)
        #print("uid:      ", uid)
        #print("extraUid: ", extraUid)
        docCount = len(Application.documents())
        for i in range(docCount):
            d = Application.documents()[i]
            if d != doc:
                if uid == d.rootNode().uniqueId():
                    canRemoveExtraUid = False
                    if extraUid == d.annotation("ODD_extra_uid"):
                        print("uid clash between this image", doc, "and", d)
                        isUnique = False
                        break
        if not isUnique:
            if True:#not extraUid:
                if self.vs.readSetting("idAutoDisambiguateCopies") == "true":
                    print("setting extra uid for document", doc, "with uid", uid)
                    doc.setAnnotation(
                            "ODD_extra_uid",
                            "An extra id used by Open Documents Docker to distinguish copied images from their origin during a krita session.",
                            QByteArray(str(uuid.uuid4()).encode())
                    )
        else:
            if canRemoveExtraUid:
                if extraUid:
                    print("remove redundant extra uid from document", doc, "with uid", uid, "and extra uid", extraUid)
                    doc.removeAnnotation("ODD_extra_uid")
    
    def viewClosed(self, view):
        print("view closed - doc name:", self.documentDisplayName(view.document()), "id:", self.documentUniqueId(view.document()))
        
        self.documentUniqueIdFromLastClosedView = self.documentUniqueId(view.document())
        print("View Closed:")
        print(" - SET documentUniqueIdFromLastClosedView =", self.documentUniqueIdFromLastClosedView)
    
    def imageClosed(self, filename):
        print("image closed -", filename)
        
        # a view just closed, and now an image just closed.
        # so this image must be the document from that view.
        assert self.documentUniqueIdFromLastClosedView != None, "ODD: imageClosed: an image closed without a view closing first?"
        
        self.removeDocumentFromList(self.documentUniqueIdFromLastClosedView)
        
        print("", self.currentDocumentId)
        print("", self.documentUniqueIdFromLastClosedView)
        if self.currentDocumentId == self.documentUniqueIdFromLastClosedView:
            print(" we've closed the document that was current.")
            if self.imageChangeDetected:
                print(" it was waiting to refresh, cancelling.")
                self.imageChangeDetected = False
                self.refreshTimer.stop()
            
            if len(Application.documents()) == 0:
                print(" it was the last open document.")
                self.currentDocumentId = None
        
        self.documentUniqueIdFromLastClosedView = None
        print("Image Closed:")
        print(" - SET documentUniqueIdFromLastClosedView =", self.documentUniqueIdFromLastClosedView)
    
    def imageSaved(self, filename):
        # unnecessary? the document just saved should be the active one
        app = Application
        doc = None
        for i in range(len(app.documents())):
            if app.documents()[i].fileName() == filename:
                doc = app.documents()[i]
                break
        print("image saved -", filename, "(doc", str(doc) + ")")
        if self.vs.settingValue("refreshOnSave"):
            if self.imageChangeDetected:
                self.imageChangeDetected = False
                self.refreshTimer.stop()
            self.updateDocumentThumbnail()
    
    def dockMoved(self, area):
        self.dockLocation = area
        self.listToolTip.hide()
    
    def __init__(self):
        print("OpenDocumentsDocker: begin init")
        super(OpenDocumentsDocker, self).__init__()
        
        self.vs = ODVS(self)
        
        self.dockLocation = None
        self.dockLocationChanged.connect(self.dockMoved)
        self.dockVisible = True
        self.visibilityChanged.connect(self.dockVisibilityChanged)
        self.deferredItemThumbnailCount = 0
        
        self.baseWidget = QWidget()
        self.layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.list = ODDListWidget(self)
        self.listToolTip = QLabel()
        self.listToolTip.setWindowFlags(Qt.ToolTip)
        self.buttonLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.loadButton = QPushButton()
        self.loadButton.setIcon(Application.icon('view-refresh'))
        self.viewButton = QPushButton()
        self.viewButton.setIcon(Application.icon('view-choose'))
        
        self.setDockerDirection(self.vs.readSetting("direction"))
        self.list.setMovement(QListView.Free)
        self.list.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.itemActivated.connect(self.itemClicked)
        self.list.itemClicked.connect(self.itemClicked)
        self.list.setMouseTracking(True)
        if False:
            self.list.setAcceptDrops(True)
            self.list.setDragEnabled(True)
            self.list.setDropIndicatorShown(True)
            print("qaiv.im:", QAbstractItemView.InternalMove)
            self.list.setDragDropMode(QAbstractItemView.InternalMove)
            self.list.setDefaultDropAction(Qt.MoveAction)
            self.list.setDragDropOverwriteMode(False)
        else:
            self.list.setAcceptDrops(False)
            self.list.setDragEnabled(False)
        
        self.layout.addWidget(self.list)
        
        self.imageChangeDetected = False
        self.imageOldSize = QSize(0, 0)
        self.imageChangeDetectionTimer = QTimer(self.baseWidget)
        setting = self.vs.readSetting("refreshPeriodicallyChecks")
        self.imageChangeDetectionTimer.setInterval(
            ODVS.SD["refreshPeriodicallyChecks"]["values"][convertSettingStringToValue("refreshPeriodicallyChecks", setting)]
        )
        self.imageChangeDetectionTimer.timeout.connect(self.imageChangeDetectionTimerTimeout)
        self.refreshTimer = QTimer(self.baseWidget)
        setting = self.vs.readSetting("refreshPeriodicallyDelay")
        self.refreshTimer.setInterval(
            ODVS.SD["refreshPeriodicallyDelay"]["values"][convertSettingStringToValue("refreshPeriodicallyDelay", setting)]
        )
        self.refreshTimer.timeout.connect(self.refreshTimerTimeout)
        
        self.vs.createPanel()
        self.viewButton.clicked.connect(self.vs.clickedViewButton)
        self.buttonLayout.addWidget(self.loadButton)
        self.buttonLayout.addWidget(self.viewButton)
        self.layout.addLayout(self.buttonLayout)
        
        self.baseWidget.setLayout(self.layout)
        self.baseWidget.setMinimumWidth(56)
        self.baseWidget.setMinimumHeight(56)
        self.setWidget(self.baseWidget)
        
        self.lastSize = self.baseWidget.size()
        self.resizeDelay = QTimer(self.baseWidget)
        self.resizeDelay.timeout.connect(self.delayedResize)
        
        self.refreshAllDelay = QTimer(self.baseWidget)
        self.refreshAllDelay.setInterval(1000)
        self.refreshAllDelay.setSingleShot(True)
        self.refreshAllDelay.timeout.connect(self.refreshAllDelayTimeout)
        
        self.itemTextUpdateTimer = QTimer(self.baseWidget)
        self.itemTextUpdateTimer.setInterval(500)
        self.itemTextUpdateTimer.timeout.connect(self.itemTextUpdateTimerTimeout)
        if self.vs.readSetting("display") == "text":
            self.itemTextUpdateTimer.start()
        
        self.loadButton.clicked.connect(self.updateDocumentThumbnailForced)
        self.setWindowTitle(i18n("Open Documents Docker"))
        
        # used for doing things with the document that was current before active view changed
        self.currentDocumentId = None
        
        appNotifier = Application.notifier()
        appNotifier.setActive(True)
        appNotifier.viewClosed.connect(self.viewClosed)
        appNotifier.imageCreated.connect(self.imageCreated)
        appNotifier.imageClosed.connect(self.imageClosed)
        appNotifier.imageSaved.connect(self.imageSaved)
        
        appNotifier.windowCreated.connect(self.windowCreated)
    
    def refreshAllDelayTimeout(self):
        self.refreshOpenDocuments(soft=True)
    
    ituttCallsUntilNextMassUpdate = 0
    def itemTextUpdateTimerTimeout(self):
        if not self.dockVisible:
            return
        
        if self.ituttCallsUntilNextMassUpdate > 0:
            doc = Application.activeDocument()
            if not doc:
                return
            item = self.findItemWithDocument(doc)
            item.setText(self.documentDisplayName(doc))
            self.ituttCallsUntilNextMassUpdate -= 1
            return
        
        count = self.list.count()
        openDocs = Application.documents()
        for i in range(count):
            item = self.list.item(i)
            doc = None
            for i in openDocs:
                if item.data(self.ItemDocumentRole) == self.documentUniqueId(i):
                    doc = i
                    break
            if not doc:
                continue
            item.setText(self.documentDisplayName(doc))
        self.ituttCallsUntilNextMassUpdate = 10
    
    tavg = 0
    def imageChangeDetectionTimerTimeout(self):
        t0 = process_time_ns()
        doc = Application.activeDocument()
        if doc == None:
            return
        if not self.findItemWithDocument(doc):
            print("imageChangeDetectionTimerTimeout - image has not been formally created yet, bail.")
            return
        if self.imageChangeDetected:
            if doc.tryBarrierLock():
                #print("imageChangeDetectionTimerTimeout - imageChangeDetected:false, lock:success - no refresh needed")
                doc.unlock()
                if not self.refreshTimer.isActive():
                    self.refreshTimer.start()
            else:
                if self.refreshTimer.isActive():
                    self.refreshTimer.stop()
        else:
            changed = False
            if doc.tryBarrierLock():
                doc.unlock()
                if self.imageOldSize != doc.bounds().size():
                    #print("imageChangeDetectionTimerTimeout - size changed")
                    changed = True
            else:
                #print("imageChangeDetectionTimerTimeout - barrier lock failed")
                changed = True
            if changed:
                print("imageChangeDetectionTimerTimeout - imageChangeDetected:false, lock:failed - document busy, it is being changed")
                self.imageChangeDetected = True
        
        self.imageOldSize = doc.bounds().size()
        t1 = process_time_ns()
        tdiff = (t1-t0)
        self.tavg = self.tavg + (tdiff - self.tavg) * 0.125
        tps =  1000.0/50.0
        #print(float(self.tavg)/1000000.0*tps, "ms/sec")
    
    def refreshTimerTimeout(self):
        doc = Application.activeDocument()
        if doc == None:
            return
        if self.imageChangeDetected:
            if doc.tryBarrierLock():
                print("refreshTimerTimeout - imageChangeDetected:true, lock:success - refresh")
                doc.unlock()
                self.updateDocumentThumbnail()
                self.imageChangeDetected = False
                self.refreshTimer.stop()
            else:
                print("refreshTimerTimeout - imageChangeDetected:true, lock:failed - document busy, wait")

    def longestDockerSide(self):
        dockrect = self.layout.geometry()
        return ("horizontal" if dockrect.width() > dockrect.height() else "vertical")
    
    def setDockerDirection(self, direction):
        if direction == "auto":
            direction = self.longestDockerSide()
        
        oldDirection = self.list.flow()
        if (
                (direction == "horizontal" and oldDirection == QListView.LeftToRight) or
                (direction == "vertical"   and oldDirection == QListView.TopToBottom)
            ):
            return
                
        if direction == "horizontal":
            self.layout.setDirection(QBoxLayout.LeftToRight)
            self.list.setFlow(QListView.LeftToRight)
            self.buttonLayout.setDirection(QBoxLayout.TopToBottom)
            self.loadButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.viewButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            try:
                self.list.verticalScrollBar().valueChanged.disconnect(self.listScrolled)
            except TypeError:
                print("couldn't disconnect vscoll")
                pass
            self.list.horizontalScrollBar().valueChanged.connect(self.listScrolled)
        else:
            self.layout.setDirection(QBoxLayout.TopToBottom)
            self.list.setFlow(QListView.TopToBottom)
            self.buttonLayout.setDirection(QBoxLayout.LeftToRight)
            self.loadButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.viewButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            try:
                self.list.horizontalScrollBar().valueChanged.disconnect(self.listScrolled)
            except TypeError:
                print("couldn't disconnect hscoll")
                pass
            self.list.verticalScrollBar().valueChanged.connect(self.listScrolled)
        self.updateScrollBarPolicy()
    
    def updateScrollBarPolicy(self):
        if self.list.flow() == QListView.LeftToRight:
            self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            if self.vs.readSetting("display") == "text":
                self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            else:
                self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.list.horizontalScrollBar().setValue(0)
            self.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    
    def listScrolled(self, value):
        self.processDeferredDocumentThumbnails()
    
    def windowCreated(self):
        print("windowCreated", end=" ")
        winlist = Application.windows()
        print("(count:", str(len(winlist)) + str(")"))
        for win in winlist:
            print("window:", win)
            win.activeViewChanged.connect(self.activeViewChanged)
    
    def activeViewChanged(self):
        print("active view changed")
        #print("active doc:", Application.activeDocument())
        if self.imageChangeDetected:
            # flush thumbnail update for now-previous doc
            print(" currdocid:", self.currentDocumentId)
            if self.currentDocumentId:
                doc = self.findDocumentWithUniqueId(self.currentDocumentId)
                if doc:
                    print(" flush thumbnail update for", self.currentDocumentId, "-", self.documentDisplayName(doc))
                    self.updateDocumentThumbnail(doc)
            self.imageChangeDetected = False
            self.refreshTimer.stop()
        if Application.activeDocument():
            self.currentDocumentId = self.documentUniqueId(Application.activeDocument())
            print(" set currentDocumentId:", self.currentDocumentId)
            self.imageOldSize = Application.activeDocument().bounds().size()
        self.ensureListSelectionIsActiveDocument()
    
    def canvasChanged(self, canvas):
        pass
    
    def resizeEvent(self, event):
        if self.resizeDelay.isActive():
            self.resizeDelay.stop()
        self.resizeDelay.setSingleShot(True)
        self.resizeDelay.setInterval(100)
        self.resizeDelay.start()
    
    def leaveEvent(self, event):
        self.listToolTip.hide()
    
    def dockVisibilityChanged(self, visible):
        print("visibilityChanged: visible =", visible)
        self.dockVisible = visible
        self.processDeferredDocumentThumbnails()
        if self.vs.settingValue("refreshPeriodically"):
            if visible:
                self.imageChangeDetectionTimer.start()
            else:
                self.imageChangeDetectionTimer.stop()
                self.refreshTimer.stop()
                if self.imageChangeDetected:
                    self.markDocumentThumbnailAsDeferred(Application.activeDocument())
                    self.imageChangeDetected = False
    
    def markDocumentThumbnailAsDeferred(self, doc=None, item=None):
        """
        can specify document or list item.
        if item not specified, find from doc.
        if both specified, doc is ignored.
        """
        if not item:
            if not doc:
                print("mark deferred: no doc or item specified.")
                return
            item = self.findItemWithDocument(doc)
            if not item:
                print("mark deferred: no list item associated with document.")
                return
        
        if item.data(self.ItemUpdateDeferredRole):
            print("mark deferred: already marked.")
            return
            
        self.deferredItemThumbnailCount += 1
        print("DEFERRED ITEM COUNT +1, =", self.deferredItemThumbnailCount)
        item.setData(self.ItemUpdateDeferredRole, True)
        print("mark deferred: " + self.documentDisplayName(self.findDocumentWithItem(item)) + " thumbnail update has been deferred.")
    
    def processDeferredDocumentThumbnails(self):
        if not self.dockVisible:
            return
        
        if self.deferredItemThumbnailCount == 0:
            return
        
        assert self.deferredItemThumbnailCount >= 0, "ODD: deferredItemThumbnailCount is negative."
        
        listRect = self.list.childrenRect()
        itemCount = self.list.count()
        for i in range(itemCount):
            item = self.list.item(i)
            if item.data(self.ItemUpdateDeferredRole):
                visRect = self.list.visualItemRect(item)
                if not listRect.intersected(visRect).isEmpty():
                    item.setData(self.ItemUpdateDeferredRole, False)
                    self.deferredItemThumbnailCount -= 1
                    print("DEFERRED ITEM COUNT -1, =", self.deferredItemThumbnailCount)
                    self.updateDocumentThumbnail(self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole)))
                else:
                    pass
    
    def contextMenuEvent(self, event):
        print("ctx menu event -", event.globalPos(), event.reason())
        self.listToolTip.hide()
        if len(self.list.selectedIndexes()) == 0:
            print("ctx menu cancelled (no selection)")
            return
        
        app = Application
        item = self.list.selectedItems()[0]
        listTopLeft = self.list.mapToGlobal(self.list.frameGeometry().topLeft())
        itemRect = self.list.visualItemRect(item)
        itemRect.translate(listTopLeft)
        
        pos = QPoint(0, 0)
        if event.reason() == QContextMenuEvent.Mouse:
            if not itemRect.contains(event.globalPos()):
                print("ctx menu cancelled (mouse not over item)")
                return
            pos = event.globalPos()
        else:
            pos = (itemRect.topLeft() + itemRect.bottomRight()) / 2
        
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if not doc:
            print("ODD: right-clicked an item that has no doc, or points to a doc that doesn't exist!")
            return
        
        print("selected:", item, " -", doc.fileName())
        app.activeDocument().waitForDone()
        self.findAndActivateView(doc)
        app.setActiveDocument(doc)
        doc.waitForDone()
        menu = QMenu(self)
        menu.addAction(self.documentDisplayName(doc))
        menu.actions()[0].setEnabled(False)
        menu.addSeparator()
        menu.addAction(app.action('file_save'))
        menu.addAction(app.action('file_save_as'))
        menu.addAction(app.action('file_export_file'))
        menu.addAction(app.action('create_copy'))
        menu.addSeparator()
        menu.addAction(app.action('file_documentinfo'))
        menu.addAction(app.action('image_properties'))
        menu.addSeparator()
        menu.addAction(app.action('ODDQuickCopyMergedAction'))
        menu.addSeparator()
        if doc.fileName():
            menu.addAction(app.action('ODDFileRevertAction'))
        else:
            print("disable revert")
            menu.addAction("Revert")
            menu.actions()[-1].setEnabled(False)
        menu.addAction(app.action('file_close'))
        
        menu.exec(pos)
    
    def dropEvent(self, event):
        print("dropEvent: ", event)
    
    def refreshOpenDocuments(self, soft=False):
        if soft:
            count = self.list.count()
            for i in range(count):
                item = self.list.item(i)
                self.updateDocumentThumbnail(self.findDocumentWithItem(item))
        else:
            self.list.clear()
            for i in Application.documents():
                self.addDocumentToList(i)
    
    def debugDump(self):
        count = len(Application.documents())
        print(" - list of all documents (count:"+str(count)+") - ")
        for i in range(count):
            doc = Application.documents()[i]
            print("   #"+str(i)+":", doc)
            print("    - fName:", doc.fileName())
            print("    - uid:  ", self.documentUniqueId(doc))
        count = self.list.count()
        print(" - list of all list items (count:"+str(count)+") - ")
        print("   selected: ", self.list.selectedItems())
        for i in range(count):
            item = self.list.item(i)
            print("   #"+str(i)+":", item)
            print("    - document data:", item.data(self.ItemDocumentRole))
        print(" - end of lists - ")
    
    def ensureListSelectionIsActiveDocument(self):
        doc = Application.activeDocument()
        
        if doc == None:
            return False
        
        itemCount = self.list.count()
        if itemCount == 0:
            return False
        
        uid = self.documentUniqueId(doc)
        
        if len(self.list.selectedItems()) > 0:
            if self.list.selectedItems()[0].data(self.ItemDocumentRole) == uid:
                return True
        
        for i in range(itemCount):
            item = self.list.item(i)
            if item.data(self.ItemDocumentRole) == uid:
                self.list.setCurrentItem(item)
                return True
        return False
    
    def isItemOnScreen(self, item):
        if not self.dockVisible:
            return False

        listRect = self.list.childrenRect()
        visRect = self.list.visualItemRect(item)
        return listRect.intersected(visRect).isValid()
    
    def updateDocumentThumbnailForced(self):
        self.updateDocumentThumbnail(doc=None, force=True)
    
    def updateDocumentThumbnail(self, doc=None, force=False):
        if not doc:
            doc = Application.activeDocument()
        if not doc:
            print("update thumb: no active document.")
            return
        if self.vs.settingValue("display") == self.vs.SD["display"]["ui"]["btnText"]:
            print("update thumb: docker list is in text-only mode.")
            return
        
        item = self.findItemWithDocument(doc)
        if not item:
            print("update thumb: no list item associated with document.")
            return
        
        t = item.data(Qt.DecorationRole)
        tOldSize = QSize(t.width(), t.height())
        
        if not force:
            if not self.isItemOnScreen(item):
                # quickly resize thumbnail to keep list rects correct.
                size = self.calculateSizeForThumbnail(doc)
                if size != tOldSize:
                    item.setData(Qt.DecorationRole, t.scaled(size))
                
                self.markDocumentThumbnailAsDeferred(None, item)
                print("update thumb: item not currently visible, update later.")
                return
        
        print("update thumb for", doc, " -", doc.fileName())
        thumbnail = self.generateThumbnailForDocument(doc)
        item.setData(Qt.DecorationRole, QPixmap.fromImage(thumbnail))
    
    def findItemWithDocument(self, doc):
        uid = self.documentUniqueId(doc)
        itemCount = self.list.count()
        for i in range(itemCount):
            searchItem = self.list.item(i)
            if searchItem.data(self.ItemDocumentRole) == uid:
                return searchItem
        return None
    
    def findDocumentWithItem(self, item):
        return self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
    
    def addDocumentToList(self, doc):
        item = None
        if self.vs.settingValue("display") == self.vs.SD["display"]["ui"]["btnThumbnails"]:
            thumbnail = self.generateThumbnailForDocument(doc)
            item = QListWidgetItem("", self.list)
            item.setData(Qt.DecorationRole, QPixmap.fromImage(thumbnail))
        else:
            item = QListWidgetItem(self.documentDisplayName(doc), self.list)
        uid = self.documentUniqueId(doc)
        item.setData(self.ItemDocumentRole, uid)
        
        self.ensureListSelectionIsActiveDocument()
    
    def removeDocumentFromList(self, uid):
        item = None
        itemCount = self.list.count()
        for i in range(itemCount):
            searchItem = self.list.item(i)
            if searchItem.data(self.ItemDocumentRole) == uid:
                item = self.list.takeItem(self.list.row(searchItem))
                break
        if item:
            print("deleting item")
            del item
            self.ensureListSelectionIsActiveDocument()
        else:
            print("did not find item to delete!")
    
    def documentUniqueId(self, doc):
        """
        return some value that uniquely identifies this document
        and that can be used to retrieve the document later in
        the session.
        Currently this is the unique id of the image root node,
        which is unique most of the time but is known to not always
        be (eg. an image made with "create copy from current image"
        will have a root node with the same id as the source image 
        for that session).
        This method wraps this implementation detail so it can more
        easily be swapped out with something better in the future.
        Update: an option allows additional identifying data to be
        stored in the image as an annotation, which we read here.
        """
        #return doc.rootNode().uniqueId()
        return [doc.rootNode().uniqueId(), QUuid(doc.annotation("ODD_extra_uid"))]
    
    def findDocumentWithUniqueId(self, uid, enableFallback=False):
        for doc in Application.documents():
            if uid == self.documentUniqueId(doc):
                return doc
        print("ODD: could not find document with uid", str(uid))
        if enableFallback:
            print("ODD: falling back to best match")
            uid[1] = QUuid()
            for doc in Application.documents():
                if uid == self.documentUniqueId(doc):
                    return doc
        return None
    
    def calculateSizeForThumbnail(self, doc):
        kludgePixels=3
        docSize = QSize(doc.width(), doc.height())
        docRatio = float(docSize.height()) / float(docSize.width())
        size = None
        scale = float(self.vs.readSetting("thumbDisplayScale"))

        # keep size from getting too big and slowing things down
        # (but don't kick in too soon, or many users might wonder why
        # thumb refuses to fill area, even after setting scale to 1.00).
        maxSize = 512
        
        if self.list.flow() == QListView.TopToBottom:
            scrollBarWidth = self.list.verticalScrollBar().sizeHint().width()
            width = self.list.width() - kludgePixels - scrollBarWidth
            width *= scale
            width = min(width, maxSize)
            height = round(width * docRatio)
            size = QSize(int(width), int(height))
        else:
            scrollBarHeight = self.list.horizontalScrollBar().sizeHint().height()
            height = self.list.height() - kludgePixels - scrollBarHeight
            height *= scale
            height = min(height, maxSize)
            width = round(height / docRatio)
            size = QSize(int(width), int(height))
        print("cwft: calculated size:", size)
        
        return size
    
    def generateThumbnailForDocument(self, doc):
        # ensure the thumbnail will be complete
        doc.waitForDone()
        
        size = self.calculateSizeForThumbnail(doc)
        
        thumbnail = None
        
        settingUseProj = self.vs.readSetting("thumbUseProjectionMethod") == "true"
        
        scaleFactor = (
                self.vs.settingValue("thumbRenderScale") if not settingUseProj else 1
        )
        
        def generator(doc, size):
            # new document may briefly exist as qobject type before becoming document,
            # during which projection isn't available but thumbnail is.
            # projection is much faster so prefer it when available.
            if type(doc) == Document and settingUseProj:
                i = doc.projection(0, 0, doc.width(), doc.height())
                if i:
                    if size.width() < doc.width():
                        return i.scaled(size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                    else:
                        return i.scaled(size, Qt.IgnoreAspectRatio, Qt.FastTransformation)
                return i
            else:
                return doc.thumbnail(size.width(), size.height())
        
        if scaleFactor == 1:
            thumbnail = generator(doc, size)
        
            if thumbnail.isNull():
                return None
        else:
            scaledSize = QSize(int(size.width() * scaleFactor), int(size.height() * scaleFactor))
            thumbnail = doc.thumbnail(scaledSize.width(), scaledSize.height())
        
            if thumbnail.isNull():
                return None
            
            thumbnail = thumbnail.scaled(size)
        
        thumbnail.setDevicePixelRatio(self.devicePixelRatioF())
        print("final size:", thumbnail.width(), "x", thumbnail.height())
        
        return thumbnail



class ODDExtension(Extension):

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        actionCopyMerged = window.createAction("ODDQuickCopyMergedAction", "Quick Copy Merged", "")
        actionCopyMerged.triggered.connect(self.quickCopyMergedAction)
        
        actionFileRevert = window.createAction("ODDFileRevertAction", "Revert", "")
        actionFileRevert.triggered.connect(self.fileRevertAction)
    
    def quickCopyMergedAction(self):
        print("perform ODDQuickCopyMergedAction")
        app = Application
        app.action('select_all').trigger()
        app.action('copy_merged').trigger()
        app.action('edit_undo').trigger()
        app.action('edit_undo').trigger()
    
    def fileRevertAction(self):
        doc = Application.activeDocument()
        fname = doc.fileName()
        docname = OpenDocumentsDocker.documentDisplayName(self, doc, showIfModified=False)

        msgBox = QMessageBox(
                QMessageBox.Warning,
                "Krita",
                "Revert unsaved changes to the document <b>'"+docname+"'</b>?<br/><br/>" \
                "Any unsaved changes will be permanently lost."
        )
        btnCancel = msgBox.addButton(QMessageBox.Cancel)
        btnRevert = msgBox.addButton("Revert", QMessageBox.DestructiveRole)
        btnRevert.setIcon(Application.icon('warning'))
        msgBox.setDefaultButton(QMessageBox.Cancel)
        msgBox.exec()
        
        if msgBox.clickedButton() == btnRevert:
            print("Revert")
            # suppress save prompt by telling Krita the document wasn't modified.
            doc.setBatchmode(True)
            doc.setModified(False)
            
            if OpenDocumentsDocker.imageChangeDetected:
                OpenDocumentsDocker.imageChangeDetected = False
                OpenDocumentsDocker.refreshTimer.stop()
            
            Application.action('file_close').trigger()
            newdoc = Application.openDocument(fname)
            Application.activeWindow().addView(newdoc)

        else:
            print("Cancel")

# And add the extension to Krita's list of extensions:
Application.addExtension(ODDExtension(Application))
