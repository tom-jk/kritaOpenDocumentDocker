# SPDX-License-Identifier: CC0-1.0

from PyQt5.QtCore import Qt, QByteArray, QBuffer, QPoint, QSize
from PyQt5.QtGui import QPixmap, QScreen, QContextMenuEvent
from PyQt5.QtWidgets import QWidget, QBoxLayout, QVBoxLayout, QHBoxLayout, QListView, QPushButton, QMenu, QAbstractItemView, QListWidgetItem, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QSizePolicy, QStackedLayout, QScrollArea
from krita import *
from time import *
import uuid
from pathlib import Path
from .odd import ODD
from .oddsettings import ODDSettings, convertSettingStringToValue, convertSettingValueToString
from .oddlistwidget import ODDListWidget

import logging
logger = logging.getLogger("odd")


class ODDDocker(krita.DockWidget):
    ItemDocumentRole = Qt.UserRole
    ItemUpdateDeferredRole = Qt.UserRole+1
    ItemModifiedStatusRole = Qt.UserRole+2
    ItemDocumentSizeRole   = Qt.UserRole+3
    ItemThumbnailKeyRole   = Qt.UserRole+4
    
    imageChangeDetected = False # todo: make instance attribute, not class?
    
    def __init__(self):
        logger.debug("ODDDocker: begin init %s", self)
        super(ODDDocker, self).__init__()
        
        ODD.dockers.append(self)
        self._window = None
        self.vs = ODDSettings(ODD.instance, self)
        
        self.dockLocation = None
        self.dockLocationChanged.connect(self.dockMoved)
        self.dockVisible = True
        self.visibilityChanged.connect(self.dockVisibilityChanged)
        self.deferredItemThumbnailCount = 0
        
        self.baseWidget = QWidget(self)
        self.layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.list = ODDListWidget(ODD.instance, self)
        self.listToolTip = QLabel(self)
        self.listToolTip.setWindowFlags(Qt.ToolTip)
        self.buttonLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.loadButton = QPushButton(self.baseWidget)
        self.loadButton.setIcon(Application.icon('view-refresh'))
        self.viewButton = QPushButton(self.baseWidget)
        self.viewButton.setIcon(Application.icon('view-choose'))
        self.infoButton = QPushButton(self.baseWidget)
        self.infoButton.setIcon(Application.icon('selection-info'))
        self.infoButton.setCheckable(True)
        self.filtButton = QPushButton(self.baseWidget)
        self.filtButton.setIcon(Application.icon('view-filter'))
        self.filtButton.setCheckable(True)
        self.filtButton.setToolTip("Filter out documents with no views in this window.")
        
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
            logger.debug("qaiv.im: %s", QAbstractItemView.InternalMove)
            self.list.setDragDropMode(QAbstractItemView.InternalMove)
            self.list.setDefaultDropAction(Qt.MoveAction)
            self.list.setDragDropOverwriteMode(False)
        else:
            self.list.setAcceptDrops(False)
            self.list.setDragEnabled(False)
        
        self.dockerStack = QStackedLayout()
        
        self.infoScrollArea = QScrollArea()
        self.infoContainer = QWidget()
        self.infoLayout = QVBoxLayout()
        self.infoLayout.setAlignment(Qt.AlignTop)
        self.infoLabel = QLabel("info.")
        self.infoLayout.addWidget(self.infoLabel)
        self.infoContainer.setLayout(self.infoLayout)
        self.infoScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.infoScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.infoScrollArea.setWidgetResizable(True)
        self.infoScrollArea.setWidget(self.infoContainer)
        
        self.dockerStack.addWidget(self.list)
        self.dockerStack.addWidget(self.infoScrollArea)
        self.layout.addLayout(self.dockerStack)
        self.layout.setStretch(0, 1)
        
        self.viewButton.clicked.connect(self.vs.clickedViewButton)
        self.buttonLayout.setSpacing(0)
        self.buttonLayout.addWidget(self.loadButton)
        self.buttonLayout.addWidget(self.viewButton)
        self.buttonLayout.addWidget(self.infoButton)
        self.buttonLayout.addWidget(self.filtButton)
        self.buttonLayout.setStretch(0, 1)
        self.buttonLayout.setStretch(1, 1)
        self.layout.addLayout(self.buttonLayout)
        self.vs.createPanel()
        
        self.layout.setSpacing(3)
        self.baseWidget.setLayout(self.layout)
        self.baseWidget.setMinimumWidth(32)
        self.baseWidget.setMinimumHeight(32)
        self.setWidget(self.baseWidget)
        
        self.lastSize = self.baseWidget.size()
        self.resizeDelay = QTimer(self.baseWidget)
        self.resizeDelay.timeout.connect(self.delayedResize)
        
        self.winGeoChangeResponseDelay = QTimer(self.baseWidget)
        self.winGeoChangeResponseDelay.setInterval(500)
        self.winGeoChangeResponseDelay.setSingleShot(True)
        self.winGeoChangeResponseDelay.timeout.connect(self.vs.updatePanelPosition)
        
        self.refreshAllDelay = QTimer(self.baseWidget)
        self.refreshAllDelay.setInterval(1000)
        self.refreshAllDelay.setSingleShot(True)
        self.refreshAllDelay.timeout.connect(self.refreshAllDelayTimeout)
        
        self.itemUpdateTimer = QTimer(self.baseWidget)
        self.itemUpdateTimer.setInterval(500)
        self.itemUpdateTimer.timeout.connect(self.itemUpdateTimerTimeout)
        self.itemUpdateTimer.start()
        
        self.loadButton.clicked.connect(self.updateDocumentThumbnailForced)
        self.infoButton.clicked.connect(self.toggleDockerInfoView)
        self.filtButton.clicked.connect(self.toggleDockerFiltering)
        self.setWindowTitle(i18n("Open Documents Docker"))
        
        # used for doing things with the document that was current before active view changed
        self.currentDocument = None
        
        self.refreshOpenDocuments()
        
        appNotifier = Application.notifier()
        appNotifier.setActive(True)
        
        appNotifier.imageSaved.connect(self.imageSaved)
        
        appNotifier.windowCreated.connect(self.windowCreated)
    
    def window(self):
        if not self._window:
            self._window = ODD.windowFromQWindow(self.parent())
        return self._window
    
    def itemClicked(self, item):
        doc = item.data(self.ItemDocumentRole)
        if not doc:
            logger.warning("ODD: clicked an item that has no doc, or points to a doc that doesn't exist!")
            return
        
        qwin = self.parent()
        activeViewThisWindow = None
        viewsThisWindow = []
        viewsThisWindowCount = 0
        viewsOtherWindowsCount = 0
        for v in ODD.views:
            vdoc = v.document()
            if vdoc == doc:
                if v.window().qwindow() == qwin:
                    viewsThisWindow.append(v)
                    viewsThisWindowCount += 1
                    if v.window().activeView() == v:
                        activeViewThisWindow = v
                else:
                    viewsOtherWindowsCount += 1
        
        if viewsThisWindowCount == 0:
            self.list.contextMenuEvent(
                    QContextMenuEvent(QContextMenuEvent.Mouse, self.list.mapFromGlobal(QCursor.pos())),
                    viewOptionsOnly=True
            )
        else:
            if activeViewThisWindow is not None:
                view = viewsThisWindow[
                        (viewsThisWindow.index(activeViewThisWindow) + 1) % len(viewsThisWindow)
                ]
            else:
                docData = ODD.docDataFromDocument(doc)
                if qwin in docData["lastViewInWindow"]:
                    view = docData["lastViewInWindow"][qwin]
                if not view:
                    view = viewsThisWindow[0]
            
            win = view.window()
            win.activate()
            win.showView(view)
            view.setVisible()
    
    def itemEntered(self, item):
        if not self.vs.settingValue("tooltipShow"):
            return
        
        doc = item.data(self.ItemDocumentRole)
        if not doc:
            return

        fPath = doc.fileName()
        
        sizeMode = self.vs.settingValue("tooltipSizeMode", True)
        isSmall = sizeMode == "small"
        isLarge = sizeMode == "large"
        pad = 0 if isSmall else 16 if isLarge else 4
        
        ttText = "<table border='0' style='margin:{}px; padding:{}px'><tr>\n".format(pad, pad)
        
        # From answer to "Use a picture or image in a QToolTip": https://stackoverflow.com/a/34300771
        imgHtml = ""
        pxCount = doc.width() * doc.height()
        if pxCount <= self.vs.settingValue("tooltipThumbLimit"):
            settingSize = self.vs.settingValue("tooltipThumbSize")
            w = doc.width()
            h = doc.height()
            if w > h:
                size = QSize(settingSize, int(settingSize * (doc.height() / doc.width())))
            else:
                size = QSize(int(settingSize * (doc.width() / doc.height())), settingSize)
            logger.debug("itemEntered: requesting thumbnail...")
            img = ODD.requestThumbnail(doc, (size.width(), size.height(), doc.width(), doc.height()), forceNotProgressive=True)
            data = QByteArray()
            buffer = QBuffer(data)
            img.save(buffer, "PNG", 100)
            imgHtml = "<img src='data:image/png;base64, " + str(data.toBase64()).split("'")[1] + "'>"
        
        if imgHtml:
            s = " style='margin:0px; padding:0px'" if not isLarge else ""
            ttText += "<td{}>\n<table border='{}'><tr><td{}>{}</td></tr></table>\n</td>\n".format(s, "0" if isSmall else "1", s, imgHtml)
        if isSmall:
            ttText += "<td valign=middle>"
            ttText += "<b>{}</b>{}\n".format(ODD.documentDisplayName(doc), "&nbsp;"*3)
            ttText += "<small>{}</small>{}\n".format(fPath, "&nbsp;"*3)
            ttText += "<small>{} x {}</small>\n".format(doc.width(), doc.height())
            ttText += "</td></tr></table>\n"
        else:
            h = "h2" if isLarge else "h3"
            ttText += "<td style='padding-left:{}px'>\n<{} style='margin:0px'>{}</{}>\n".format(
                    pad//2, h, ODD.documentDisplayName(doc), h
            )
            ttText += "<p style='white-space:pre; margin:0px'><small>{}</small></p>\n".format(fPath)
            ttText += "<p style='margin:0px'><small>{} x {}</small></p>\n".format(doc.width(), doc.height())
            ttText += "</td></tr></table>"
        
        self.listToolTip.setText(ttText)
        
        ttPos = None
        
        listTopLeft = self.baseWidget.mapToGlobal(self.list.frameGeometry().topLeft())
        listBottomLeft = self.baseWidget.mapToGlobal(self.list.frameGeometry().bottomLeft())
        listBottomRight = self.baseWidget.mapToGlobal(self.list.frameGeometry().bottomRight())
        listTopRight = self.baseWidget.mapToGlobal(self.list.frameGeometry().topRight())
        listCenter = (listTopLeft+listBottomRight)/2
        itemRect = self.list.visualItemRect(item)
        
        screen = ODD.instance.getScreen(self).availableGeometry()
        screenTopLeft = screen.topLeft()
        screenBottomRight = screen.bottomRight()
        
        # work out which side of the widget has the most space and put the tooltip there.
        screenCenter = (screenTopLeft+screenBottomRight)/2
        if self.list.flow() == QListView.TopToBottom:
            if listCenter.x() < screenCenter.x():
                ttPos = listTopRight + QPoint(0, itemRect.top())
            else:
                ttPos = listTopLeft + QPoint(-self.listToolTip.sizeHint().width(), itemRect.top())
        else:
            if listCenter.y() < screenCenter.y():
                ttPos = listBottomLeft + QPoint(itemRect.left(), 0)
            else:
                ttPos = listTopLeft + QPoint(itemRect.left(), -self.listToolTip.sizeHint().height())
        
        self.listToolTip.adjustSize()
        ttRect = QRect(ttPos, self.listToolTip.size())
        
        # keep tooltip top-left from going outside list extents, and bottom-right from going outside the screen.
        if self.list.flow() == QListView.TopToBottom:
            ttRect.moveTop(max(listTopLeft.y(), min(ttRect.top(), listBottomRight.y())))
        else:
            ttRect.moveLeft(max(listTopLeft.x(), min(ttRect.left(), listBottomRight.x())))
        ttRect.moveBottom(min(ttRect.bottom(), screenBottomRight.y()))
        ttRect.moveRight(min(ttRect.right(), screenBottomRight.x()))
        
        self.listToolTip.move(ttRect.topLeft())
        self.listToolTip.show()
    
    def delayedResize(self):
        itemsWithBadThumbs = []
        def checkThumbSizes():
            itemRects = self.list.itemRects()
            if not itemRects:
                return True
            count = len(itemRects)
            if count == 0:
                return True
            compareSize = self.calculateRenderSizeForThumbnail()
            if self.list.flow() == QListView.TopToBottom:
                for i in range(0, count):
                    if self.list.item(i).data(Qt.DecorationRole).size().width() != compareSize.width():
                        itemsWithBadThumbs.append(i)
            else:
                for i in range(0, count):
                    if self.list.item(i).data(Qt.DecorationRole).size().height() != compareSize.width():
                        itemsWithBadThumbs.append(i)
            if itemsWithBadThumbs:
                return False
            return True
        
        self.resizeDelay.stop()
        logger.debug("delayedResize: lastSize: %s", self.lastSize)
        logger.debug("               new size: %s", self.baseWidget.size())
        doRefresh = False
        lastFlow = self.list.flow()
        self.setDockerDirection(self.vs.readSetting("direction"))
        if self.vs.readSetting("display") != "thumbnails":
            logger.debug("delayedResize: not in thumbnails mode, nothing to refresh.")
        elif self.lastSize != self.baseWidget.size():
            if (lastFlow == QListView.TopToBottom and self.lastSize.width() == self.baseWidget.size().width()) or \
                    (lastFlow == QListView.LeftToRight and self.lastSize.height() == self.baseWidget.size().height()):
                logger.debug("delayedResize: list is longer/shorter, but not narrower/wider - refresh only deferred.")
                self.list.updateScrollBarRange()
                self.processDeferredDocumentThumbnails()
            else:
                logger.debug("delayedResize: size changed - refresh.")
                doRefresh = True
        elif self.list.flow() != lastFlow:
            logger.debug("delayedResize: direction changed - refresh.")
            doRefresh = True
        elif not checkThumbSizes():
            logger.debug("delayedResize: some items are improperly sized - refresh.")
            doRefresh = True
        else:
            logger.debug("delayedResize: size did not change - no refresh.")
            
        if doRefresh:
            self.list.invalidateItemRectsCache()
            self.list.itemRects()
            self.list._doNotRecacheItemRects = True
            logger.debug("%s %s", bool(itemsWithBadThumbs), itemsWithBadThumbs)
            if itemsWithBadThumbs:
                logger.debug(" refresh %s items", len(itemsWithBadThumbs))
                for i in itemsWithBadThumbs:
                    item = self.list.item(i)
                    self.updateDocumentThumbnail(item.data(self.ItemDocumentRole))
            else:
                logger.debug(" refresh all items")
                self.refreshOpenDocuments(soft=True, force=False)
            self.list._doNotRecacheItemRects = False
            self.list.itemRects()
        
        self.lastSize = self.baseWidget.size()
        
        self.vs.updatePanelPosition()
    
    def documentCreated(self, doc):
        logger.debug("document created - %s", doc)
        fName = doc.fileName()
        logger.debug(" name: %s", (fName if fName else "[not saved]"))
        
        if not hasattr(self, "docCreatedDelay"):
            self.docCreatedDelay = QTimer(self.baseWidget)
            self.docCreatedDelay.setSingleShot(True)
            self.docCreatedDelay.setInterval(0)
            self.docCreatedDelay.timeout.connect(self._documentCreated)
        self.createdDoc = doc
        self.docCreatedDelay.start()
        
    def _documentCreated(self):
        doc = self.createdDoc
        self.createdDoc = None
        logger.debug("_documentCreated - %s", doc)
        self.addDocumentToList(doc)
    
    def documentClosed(self, doc):
        logger.debug("document closed - %s %s", doc, doc.fileName())
        
        self.removeDocumentFromList(doc)
        
        logger.debug(" %s", self.currentDocument)
        if self.currentDocument == doc:
            logger.debug(" we've closed the document that was current.")
            
            if len(ODD.documents) == 1: # (entry in ODD.documents is not deleted yet, will in a moment, so length 1 'means' empty.)
                logger.debug(" it was the last open document.")
                self.currentDocument = None
    
    def imageSaved(self, filename):
        # TODO: most (all?) of this should probably be moved to ODD main.
        candidates = []
        for d in ODD.documents:
            doc = d["document"]
            item = self.findItemWithDocument(doc)
            if item.data(self.ItemModifiedStatusRole) == True and doc.modified() == False:
                candidates.append(doc)
        if len(candidates) != 1:
            # couldn't work out which doc saved for whatever reason, so active doc is best guess.
            doc = ODD.activeDocument
        else:
            doc = candidates[0]
        logger.info("image saved - %s (doc %s)", filename, str(doc))
        if self.vs.settingValue("refreshOnSave"):
            self.updateDocumentThumbnail(doc=doc, force=True)
        
        ODDImageChangeDetector.startCooldown()
    
    def moveEvent(self, event):
        #logger.debug("moveEvent: %s %s %s", event.pos(), self.pos(), self.baseWidget.mapToGlobal(self.baseWidget.pos()))
        self.vs.updatePanelPosition()
    
    def dockMoved(self, area):
        self.vs.updatePanelPosition()
        self.dockLocation = area
        self.listToolTip.hide()
    
    def refreshAllDelayTimeout(self):
        self.refreshOpenDocuments(soft=True)
    
    def itemUpdateTimerTimeout(self):
        if not self.dockVisible:
            return
        
        isSettingDisplayThumbnails = self.vs.readSetting("display") == "thumbnails"
        
        if hasattr(ODD.instance, "fileReverter"):
            logger.debug("reverting, skip")
            return
        
        itemCount = self.list.count()
        for i in range(itemCount):
            item = self.list.item(i)
            doc = item.data(self.ItemDocumentRole)
            if not doc:
                logger.warning("ODDDocker:itemUpdateTimerTimeout: can't find document for item.")
                continue
            if doc.width() == 0 or doc.height() == 0:
                logger.info("ODDDocker:itemUpdateTimerTimeout: closed document still in list at item %s/%s, skip.", i+1, itemCount)
                continue
            if isSettingDisplayThumbnails:
                oldModified = item.data(self.ItemModifiedStatusRole)
                modified = doc.modified()
                if oldModified != modified:
                    item.setData(self.ItemModifiedStatusRole, doc.modified())
                    if self.vs.readSetting("thumbShowModified") != "none":
                        self.list.update()
                oldDocSize = item.data(self.ItemDocumentSizeRole)
                docSize = QSize(doc.width(), doc.height())
                if oldDocSize != docSize:
                    item.setData(self.ItemDocumentSizeRole, docSize)
                    self.list.invalidateItemRectsCache()
                    self.updateDocumentThumbnail(doc)
                    self.list.update()
            else:
                oldName = item.text()
                name = ODD.documentDisplayName(doc)
                if oldName != name:
                    item.setText(name)
        
        if self.dockerStack.currentIndex() == 1:
            self.updateLabel()

    def longestDockerSide(self):
        dockrect = self.layout.geometry()
        return ("horizontal" if dockrect.width() > dockrect.height() else "vertical")
    
    def setDockerDirection(self, direction):
        if direction == "auto":
            if self.vs.readSetting("display") != "thumbnails":
                direction == "vertical"
            else:
                direction = self.longestDockerSide()
        
        oldDirection = self.list.flow()
        
        if direction == "horizontal":
            self.layout.setDirection(QBoxLayout.LeftToRight)
            self.list.setFlow(QListView.LeftToRight)
            if hasattr(self.vs, "dockerThumbsDisplayScaleSlider"):
                self.vs.dockerThumbsDisplayScaleSlider.setOrientation(Qt.Vertical)
                self.vs.dockerThumbsDisplayScaleGridSlider.setOrientation(Qt.Vertical)
                self.vs.dockerCommonControlsLayout.setDirection(QBoxLayout.TopToBottom)
                self.vs.dockerDisplayToggleButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
                self.vs.dockerRefreshPeriodicallyToggleButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
                if self.baseWidget.height() >= 110:
                    self.layout.removeItem(self.vs.dockerCommonControlsLayout)
                    self.buttonLayout.insertLayout(1, self.vs.dockerCommonControlsLayout)
                    self.buttonLayout.setStretch(1, 2)
                else:
                    self.buttonLayout.removeItem(self.vs.dockerCommonControlsLayout)
                    self.layout.insertLayout(2, self.vs.dockerCommonControlsLayout)
            self.buttonLayout.setDirection(QBoxLayout.TopToBottom)
            self.loadButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.viewButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.infoButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            try:
                self.list.verticalScrollBar().valueChanged.disconnect(self.listScrolled)
            except TypeError:
                logger.debug("couldn't disconnect vscroll")
                pass
            self.list.horizontalScrollBar().valueChanged.connect(self.listScrolled)
        else:
            self.layout.setDirection(QBoxLayout.TopToBottom)
            self.list.setFlow(QListView.TopToBottom)
            if hasattr(self.vs, "dockerThumbsDisplayScaleSlider"):
                self.vs.dockerThumbsDisplayScaleSlider.setOrientation(Qt.Horizontal)
                self.vs.dockerThumbsDisplayScaleGridSlider.setOrientation(Qt.Horizontal)
                self.vs.dockerCommonControlsLayout.setDirection(QBoxLayout.LeftToRight)
                self.vs.dockerDisplayToggleButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                self.vs.dockerRefreshPeriodicallyToggleButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                if self.baseWidget.width() >= 110:
                    self.layout.removeItem(self.vs.dockerCommonControlsLayout)
                    self.buttonLayout.insertLayout(1, self.vs.dockerCommonControlsLayout)
                    self.buttonLayout.setStretch(1, 2)
                else:
                    self.buttonLayout.removeItem(self.vs.dockerCommonControlsLayout)
                    self.layout.insertLayout(2, self.vs.dockerCommonControlsLayout)
            self.buttonLayout.setDirection(QBoxLayout.LeftToRight)
            self.loadButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.viewButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.infoButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            try:
                self.list.horizontalScrollBar().valueChanged.disconnect(self.listScrolled)
            except TypeError:
                logger.debug("couldn't disconnect hscroll")
                pass
            self.list.verticalScrollBar().valueChanged.connect(self.listScrolled)
        self.updateScrollBarPolicy()
        
        if (
                (direction == "horizontal" and oldDirection == QListView.LeftToRight) or
                (direction == "vertical"   and oldDirection == QListView.TopToBottom)
            ):
            return
        
        self.list.update()
        self.list.invalidateItemRectsCache()
        self.vs.updatePanelPosition()
    
    def updateScrollBarPolicy(self):
        if self.list.hideScrollBars:
            self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            if self.list.flow() == QListView.TopToBottom and self.vs.readSetting("display") == "thumbnails":
                self.list.horizontalScrollBar().setValue(0)
        else:
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
        pass
    
    def activeViewChanged(self):
        logger.info("active view changed - %s", self)
        ODD.updateActiveDocument()
        doc = ODD.activeDocument
        if doc:
            self.currentDocument = doc
            logger.debug(" set currentDocument: %s", self.currentDocument)
            docData = ODD.docDataFromDocument(doc)
            qwin = self.parent()
            win = ODD.windowFromQWindow(qwin)
            activeView = win.activeView()
            if activeView.document() == doc:
                docData["lastViewInWindow"][qwin] = activeView
                logger.debug("last view on {} in {} set to {}".format(doc, qwin.objectName(), activeView))
            else:
                logger.warning("ODDDocker.activeViewChanged: mismatch of active doc and view doc, don't set lastViewInWindow.")
        self.ensureListSelectionIsActiveDocument()
        ODDImageChangeDetector.startCooldown()
    
    def canvasChanged(self, canvas):
        pass
    
    def resizeEvent(self, event):
        self.restartResizeDelayTimer()
    
    def restartResizeDelayTimer(self):
        # TODO: change init order so check not necessary
        if not hasattr(self, "resizeDelay"):
            return
        self.resizeDelay.stop()
        self.resizeDelay.setSingleShot(True)
        self.resizeDelay.setInterval(100)
        self.resizeDelay.start()
    
    def leaveEvent(self, event):
        self.listToolTip.hide()
    
    def dockVisibilityChanged(self, visible):
        logger.debug("visibilityChanged: visible = %s", visible)
        self.dockVisible = visible
        self.processDeferredDocumentThumbnails()
    
    def markDocumentThumbnailAsDeferred(self, doc=None, item=None):
        """
        can specify document or list item.
        if item not specified, find from doc.
        if both specified, doc is ignored.
        """
        if not item:
            if not doc:
                logger.warning("mark deferred: no doc or item specified.")
                return
            item = self.findItemWithDocument(doc)
            if not item:
                logger.warning("mark deferred: no list item associated with document.")
                return
        
        if item.data(self.ItemUpdateDeferredRole):
            logger.info("mark deferred: already marked.")
            return
        
        if not doc:
            doc = item.data(self.ItemDocumentRole)
        
        self.deferredItemThumbnailCount += 1
        logger.debug("DEFERRED ITEM COUNT +1, = %s", self.deferredItemThumbnailCount)
        item.setData(self.ItemUpdateDeferredRole, True)
        logger.debug("mark deferred: %s thumbnail update has been deferred.", ODD.documentDisplayName(doc))
    
    def unmarkDocumentThumbnailAsDeferred(self, doc=None, item=None):
        if not item.data(self.ItemUpdateDeferredRole):
            #logger.info("unmark deferred: already not marked.")
            return
        
        if not doc:
            doc = self.findDocumentWithItem(item)
        
        item.setData(self.ItemUpdateDeferredRole, False)
        self.deferredItemThumbnailCount -= 1
        logger.debug("DEFERRED ITEM COUNT -1, = %s", self.deferredItemThumbnailCount)
        logger.debug("unmark deferred: %s thumbnail update is no longer deferred.", ODD.documentDisplayName(doc))
    
    def processDeferredDocumentThumbnails(self):
        if not self.dockVisible:
            return
        
        if self.deferredItemThumbnailCount == 0:
            return
        
        itemCount = self.list.count()
        
        if self.deferredItemThumbnailCount < 0:
            logger.error("deferredItemThumbnailCount is negative.")
            # correct the count.
            self.deferredItemThumbnailCount = 0
            for i in range(itemCount):
                if self.list.item(i).data(self.ItemUpdateDeferredRole):
                    self.deferredItemThumbnailCount += 1
            logger.info("DEFERRED ITEM COUNT = %s", self.deferredItemThumbnailCount)
        
        viewRect = QRect(QPoint(0, 0), self.list.viewport().size())
        for i in range(itemCount):
            item = self.list.item(i)
            if item.data(self.ItemUpdateDeferredRole):
                visRect = self.list.visualItemRect(item)
                if not viewRect.intersected(visRect).isEmpty():
                    doc = item.data(self.ItemDocumentRole)
                    self.updateDocumentThumbnail(doc)
                else:
                    pass
    
    def dropEvent(self, event):
        logger.debug("dropEvent: %s", event)
    
    def refreshOpenDocuments(self, soft=False, force=False):
        if soft:
            count = self.list.count()
            for i in range(count):
                item = self.list.item(i)
                self.updateDocumentThumbnail(item.data(self.ItemDocumentRole), force)
        else:
            self.deferredItemThumbnailCount = 0
            logger.debug("DEFERRED ITEM COUNT = 0")
            count = self.list.count()
            for i in range(count):
                item = self.list.item(i)
                thumbKey = item.data(self.ItemThumbnailKeyRole)
                if thumbKey:
                    ODD.removeThumbnailUser(self, item.data(self.ItemDocumentRole), thumbKey)
            self.list.clear()
            for docData in ODD.documents:
                self.addDocumentToList(docData["document"])
        self.list.invalidateItemRectsCache()
    
    def ensureListSelectionIsActiveDocument(self):
        doc = ODD.activeDocument
        
        if doc == None:
            return False
        
        itemCount = self.list.count()
        if itemCount == 0:
            return False
        
        if len(self.list.selectedItems()) > 0:
            if self.list.selectedItems()[0].data(self.ItemDocumentRole) == doc:
                return True
        
        for i in range(itemCount):
            item = self.list.item(i)
            if item.data(self.ItemDocumentRole) == doc:
                self.list.setCurrentItem(item)
                return True
        return False
    
    def isItemOnScreen(self, item):
        if not self.dockVisible:
            return False
        
        if item.isHidden():
            return False
        
        viewRect = QRect(QPoint(0, 0), self.list.viewport().size())
        visRect = self.list.visualItemRect(item)
        logger.debug("isItemOnScreen: %s %s %s", viewRect, visRect, bool(viewRect.intersected(visRect).isValid()))
        return viewRect.intersected(visRect).isValid()
    
    def updateDocumentThumbnailForced(self):
        self.updateDocumentThumbnail(doc=None, force=True)
    
    def toggleDockerInfoView(self):
        toIndex = 1-self.dockerStack.currentIndex()
        self.dockerStack.setCurrentIndex(toIndex)
        if toIndex == 1:
            self.updateLabel()
    
    def toggleDockerFiltering(self):
        enabled = self.filtButton.isChecked()
        count = self.list.count()
        if enabled:
            win = ODD.windowFromQWindow(self.parent())
            for i in range(count):
                item = self.list.item(i)
                doc = item.data(self.ItemDocumentRole)
                item.setHidden(not ODD.documentHasViewsInWindow(doc, win))
        else:
            for i in range(count):
                item = self.list.item(i)
                item.setHidden(False)
        self.list.invalidateItemRectsCache()
        self.processDeferredDocumentThumbnails()
    
    def updateDocumentThumbnail(self, doc=None, force=False, ignoreThumbsMoreRecentThan=None):
        if not doc:
            doc = ODD.activeDocument
        if not doc:
            logger.warning("update thumb: no active document.")
            return
        
        item = self.findItemWithDocument(doc)
        if not item:
            logger.warning("update thumb: no list item associated with document.")
            return
        
        if ignoreThumbsMoreRecentThan:
            docData = ODD.docDataFromDocument(doc)
            thKey = item.data(self.ItemThumbnailKeyRole)
            if thKey:
                thTime = docData["thumbnails"][thKey]["lastUsed"]
                logger.debug("update thumb: doc:{}, thKey:{}, thTime:{:n}, requiredTime:{:n}".format(ODD.documentDisplayName(doc), thKey, thTime, ignoreThumbsMoreRecentThan))
                if thTime >= ignoreThumbsMoreRecentThan:
                    logger.debug("update thumb: thumb already more recent than required, cancel.")
                    return
        
        settingDisplayThumbs = self.vs.settingValue("display", True) == "thumbnails"
        if not settingDisplayThumbs:
            force = False
        
        if force:
            ODD.invalidateThumbnails(doc)
        
        if not (settingDisplayThumbs and self.isItemOnScreen(item)):
            self.markDocumentThumbnailAsDeferred(None, item)
            logger.debug("update thumb: item not currently visible or docker in text mode, update later.")
            return
        
        self.unmarkDocumentThumbnailAsDeferred(doc, item)
        
        logger.debug("update thumb for %s", doc.fileName())
        self.updateItemThumbnail(item, doc)
    
    def updateItemThumbnail(self, item, doc):
        if result := self.generateThumbnailForItem(item, doc):
            logger.debug("updateItemThumbnail: result: pixmap={}, thumbKey={}".format(result[0], result[1]))
            oldThumbKey = item.data(self.ItemThumbnailKeyRole)
            if oldThumbKey != result[1]:
                if result[0]:
                    item.setData(Qt.DecorationRole, result[0])
                item.setData(self.ItemThumbnailKeyRole, result[1])
                logger.debug("oldThumbKey: %s, result[1]: %s", oldThumbKey, result[1])
                ODD.addThumbnailUser(self, doc, result[1])
                if oldThumbKey:
                    ODD.removeThumbnailUser(self, doc, oldThumbKey)
    
    def findItemWithDocument(self, doc):
        itemCount = self.list.count()
        for i in range(itemCount):
            searchItem = self.list.item(i)
            if searchItem.data(self.ItemDocumentRole) == doc:
                return searchItem
        return None
    
    def addDocumentToList(self, doc):
        logger.debug("addDocumentToList: %s", doc)
        item = QListWidgetItem("", self.list)
        item.setData(self.ItemDocumentRole, doc)
        item.setData(self.ItemDocumentSizeRole, QSize(doc.width(), doc.height()))
        item.setData(self.ItemModifiedStatusRole, doc.modified())
        if self.vs.settingValue("display") == self.vs.UI["display"]["btnThumbnails"]:
            self.updateItemThumbnail(item, doc)
        else:
            item.setText(ODD.documentDisplayName(doc))
        
        self.toggleDockerFiltering()
        self.list.invalidateItemRectsCache()
        self.list.update()
        self.ensureListSelectionIsActiveDocument()
    
    def removeDocumentFromList(self, doc):
        item = None
        itemCount = self.list.count()
        for i in range(itemCount):
            searchItem = self.list.item(i)
            if searchItem.data(self.ItemDocumentRole) == doc:
                item = self.list.takeItem(self.list.row(searchItem))
                break
        if item:
            logger.debug("deleting item")
            self.unmarkDocumentThumbnailAsDeferred(item.data(self.ItemDocumentRole), item)
            if item.data(Qt.DecorationRole):
                ODD.removeThumbnailUser(self, doc, item.data(self.ItemThumbnailKeyRole))
            del item
            self.ensureListSelectionIsActiveDocument()
            self.list.invalidateItemRectsCache()
        else:
            logger.warning("did not find item to delete!")
    
    def calculateRenderSizeForItem(self, item):
        return calculateRenderSizeForThumbnail(item.data(self.ItemDocumentSizeRole))
    
    def calculateRenderSizeForThumbnail(self, docSize=None):
        if self.vs.settingValue("thumbUseProjectionMethod"):
            return self.calculateDisplaySizeForThumbnail(docSize)
        else:
            return self.calculateDisplaySizeForThumbnail(docSize) * self.vs.settingValue("thumbRenderScale")
    
    def calculateDisplaySizeForItem(self, item):
        return self.calculateDisplaySizeForThumbnail(item.data(self.ItemDocumentSizeRole))
    
    def calculateDisplaySizeForThumbnail(self, docSize=None, asFloat=False, applyAspectLimit=False):
        gutterPixels=2
        if not docSize:
            docSize = QSize(512, 512)
        
        docRatio = float(docSize.height()) / float(docSize.width())
        
        if applyAspectLimit:
            aspectLimit = float(self.vs.readSetting("thumbAspectLimit"))
            if docRatio > aspectLimit:
                docRatio = aspectLimit
            elif 1.0/docRatio > aspectLimit:
                docRatio = 1.0/aspectLimit
        
        size = None
        isGrid = self.vs.readSetting("grid") == "true"
        scale = float(1/int(self.vs.readSetting("thumbDisplayScaleGrid"))) if isGrid else float(self.vs.readSetting("thumbDisplayScale"))
        
        # keep size from getting too big and slowing things down
        # (but don't kick in too soon, or many users might wonder why
        # thumb refuses to fill area, even after setting scale to 1.00).
        maxSize = 512
        
        if self.list.flow() == QListView.TopToBottom:
            scrollBarWidth = self.list.verticalScrollBar().sizeHint().width() if self.list.verticalScrollBar().isVisible() else 0
            width = self.list.width() - gutterPixels - scrollBarWidth
            width *= scale
            width = min(width, maxSize)
            height = width * docRatio
            size = QSizeF(width, height)
            #logger.debug("cdsft: Vert %s %s %s %s", scrollBarWidth, self.list.width(), docRatio, str(size.width())+"x"+str(size.height()))
        else:
            scrollBarHeight = self.list.horizontalScrollBar().sizeHint().height() if self.list.horizontalScrollBar().isVisible() else 0
            height = self.list.height() - gutterPixels - scrollBarHeight
            height *= scale
            height = min(height, maxSize)
            width = height / docRatio
            size = QSizeF(width, height)
            #logger.debug("cdsft: Hori %s %s %s %s", scrollBarHeight, self.list.height(), docRatio, str(size.width())+"x"+str(size.height()))
        
        if asFloat:
            if size.width() < 1.0:
                size.setWidth(1.0)
            if size.height() < 1.0:
                size.setHeight(1.0)
        else:
            size = size.toSize()
            if size.width() < 1:
                size.setWidth(1)
            if size.height() < 1:
                size.setHeight(1)
        
        return size
    
    def generateThumbnailForItem(self, item, doc):
        # ensure the thumbnail will be complete.
        doc.waitForDone()
        
        size = self.calculateDisplaySizeForThumbnail(item.data(self.ItemDocumentSizeRole))
        
        thumbnail = None
        thumbKey = None
        
        settingUseProj = self.vs.readSetting("thumbUseProjectionMethod") == "true"
        
        scaleFactor = (
                self.vs.settingValue("thumbRenderScale") if not settingUseProj else 1
        )
        
        if scaleFactor == 1:
            # force immediate generation if item currently has no thumbnail at all.
            thumbKey = (size.width(), size.height(), doc.width(), doc.height())
            thumbnail = ODD.requestThumbnail(doc, thumbKey, not item.data(Qt.DecorationRole))
            
            if type(thumbnail) is QPixmap:
                if thumbnail.isNull():
                    return None
            else:
                # progressive thumbnail with no fallback, keep current thumbnail.
                thumbnail = item.data(Qt.DecorationRole)
        else:
            scaledSize = QSize(int(size.width() * scaleFactor), int(size.height() * scaleFactor))
            thumbKey = (scaledSize.width(), scaledSize.height(), doc.width(), doc.height())
            thumbnail = ODD.requestThumbnail(doc, thumbKey)
        
            if thumbnail.isNull():
                return None
        
        if type(thumbnail) is QPixmap:
            thumbnail.setDevicePixelRatio(self.devicePixelRatioF())
        
        return (thumbnail, thumbKey)

    def updateLabel(self):
        app = Application
        newLine = "<br/>"
        newText = ""
        
        if not self:
            return
        
        qwin = self.parent()
        
        wins = ODD.windows
        thisWin = ODD.windowFromQWindow(self.parent()) if self.parent() else None
        for w in wins:
            newText += "WINDOW {} ({}) {}{}\n".format(
                    str(w),
                    w.qwindow().objectName(),
                    "&lt;--" if w == thisWin else "",
                    newLine if w != wins[-1] else ""
            )
        
        views = ODD.views
        docs = ODD.documents
        bitCountAll = 0
        for doc in docs:
            d = doc["document"]
            newText += \
                    "<div>\n" \
                    " <ul type=none style='margin-left:-32px; -qt-list-indent:1'>\n" \
                    "  <li style='font-weight:bold;'>DOC: {}</li>\n".format(Path(d.fileName()).name or "[not saved]")
            newText += "  <ul type=none style='margin-left:8px; -qt-list-indent:1'>\n"
            newText += "   <li><b>Opened</b>: {}</li>\n".format(doc["created"])
            viewsThisWindowCount = doc["viewCountPerWindow"][qwin] if qwin in doc["viewCountPerWindow"] else 0
            viewsOtherWindowsCount = sum(0 if k == qwin else v for k,v in doc["viewCountPerWindow"].items())
            newText += "   <li><b>Views: {}</b> ({} in this window, {} in others)</li>\n".format(
                    viewsThisWindowCount + viewsOtherWindowsCount,
                    viewsThisWindowCount,
                    viewsOtherWindowsCount
            )
            thumbCount = len(doc["thumbnails"])
            if thumbCount > 0:
                bitCount = 0
                usedThumbText = ""
                unusedThumbTexts = []
                for thumbKey,thumbData in doc["thumbnails"].items():
                    pm = thumbData["pixmap"]
                    userCount = len(thumbData["users"])
                    thumbBitCount = thumbData["size"]
                    bitCount += thumbBitCount
                    valid = thumbData["valid"]
                    lastUsedMs = thumbData["lastUsed"]//1000000
                    gen = thumbData["generator"]
                    if userCount == 0:
                        unusedThumbTexts.append((
                                lastUsedMs,
                                thumbBitCount,
                                "    <li>{}: 0 users, {:1.2f}kb, last use: {}ms {}</li>\n".format(
                                        thumbKey,
                                        thumbBitCount/8/1024,
                                        lastUsedMs,
                                        "({:1.2f}%)".format(gen.progress()*100) if gen else ""
                                ),
                        ))
                    else:
                        usedThumbText += "    <li><b>{}</b>: {} user{}, {:1.2f}kb{} {}</li>\n".format(
                                thumbKey,
                                userCount,
                                "" if userCount==1 else "s",
                                thumbBitCount/8/1024,
                                "" if valid else "<i>, outdated</i>",
                                "({:1.2f}%)".format(gen.progress()*100) if gen else ""
                        )
                
                unusedThumbText = ""
                unusedThumbCount = 0
                unusedThumbOverflowBitCount = 0
                unusedThumbTexts.sort(key=lambda textItem : textItem[0], reverse=True)
                for textItem in unusedThumbTexts:
                    if unusedThumbCount < 3:
                        unusedThumbText += textItem[2]
                    else:
                        unusedThumbOverflowBitCount += textItem[1]
                    unusedThumbCount += 1
                
                newText += "   <li><b>Thumbs: {}</b> ({:1.2f}kb)</li>\n".format(thumbCount, bitCount/8/1024)
                newText += "   <ul type=none style='margin-left:8px; -qt-list-indent:1; font-size:small;'>\n"
                newText += usedThumbText + unusedThumbText
                if unusedThumbCount >= 4:
                    newText += "    <li><i>...and {} less recently used, total {:1.2f}kb</i></li>\n".format(
                            unusedThumbCount - 3, unusedThumbOverflowBitCount/8/1024
                    )
                newText += "   </ul>\n"
                bitCountAll += bitCount
            newText += "  </ul>\n </ul>\n</div>\n"
        
        self.infoLabel.setText(
                "<html>" + \
                "all thumbs: " + "{:1.3f}".format(bitCountAll/8/1048576) + \
                "mb, of which unused: " + "{:1.3f}".format(ODD.unusedCacheSize/8/1048576) + \
                "mb<br/>" + newText + \
                "</html>"
        )


from .oddimagechangedetector import ODDImageChangeDetector
