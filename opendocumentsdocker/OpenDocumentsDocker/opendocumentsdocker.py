# SPDX-License-Identifier: CC0-1.0

from PyQt5.QtCore import Qt, QByteArray, QBuffer, QPoint, QSize
from PyQt5.QtGui import QPixmap, QScreen, QContextMenuEvent
from PyQt5.QtWidgets import QWidget, QBoxLayout, QVBoxLayout, QHBoxLayout, QListView, QPushButton, QMenu, QAbstractItemView, QListWidgetItem, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QSizePolicy
from krita import *
from time import *
import uuid
from pathlib import Path
from .opendocumentsviewsettings import OpenDocumentsViewSettings as ODVS, convertSettingStringToValue, convertSettingValueToString
from .oddlistwidget import ODDListWidget

class OpenDocumentsDocker(krita.DockWidget):
    ItemDocumentRole = Qt.UserRole
    ItemUpdateDeferredRole = Qt.UserRole+1
    ItemModifiedStatusRole = Qt.UserRole+2
    ItemDocumentSizeRole   = Qt.UserRole+3
    
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
        if doc:
            fPath = doc.fileName()
            fName = Path(fPath).name
            tModi = " *" * doc.modified() * showIfModified
        else:
            fName = "[no document]"
            tModi = ""
        return (fName if fName else "[not saved]") + tModi
    
    def getScreen(self):
        if hasattr(self, "screen"):
            return self.screen()
        if self.windowHandle():
            return self.windowHandle().screen()
        if self.parent() and self.parent().windowHandle():
            return self.parent().windowHandle().screen()
    
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
        
        screen = self.getScreen().availableGeometry()
        screenTopLeft = screen.topLeft()
        screenBottomRight = screen.bottomRight()
        
        # work out which side of the widget has the most space and put the tooltip there.
        screenCenter = (screenTopLeft+screenBottomRight)/2
        if self.list.flow() == QListView.TopToBottom:
            if listCenter.x() < screenCenter.x():
                ttPos = listTopRight + itemRect.topLeft()
            else:
                ttPos = listTopLeft + QPoint(-self.listToolTip.sizeHint().width(), itemRect.top())
        else:
            if listCenter.y() < screenCenter.y():
                ttPos = listTopLeft + QPoint(itemRect.left(), itemRect.top() + itemRect.height())
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
        print("delayedResize: lastSize:", self.lastSize)
        print("               new size:", self.baseWidget.size())
        doRefresh = False
        lastFlow = self.list.flow()
        self.setDockerDirection(self.vs.readSetting("direction"))
        if self.vs.readSetting("display") != "thumbnails":
            print("delayedResize: not in thumbnails mode, nothing to refresh.")
        elif self.lastSize != self.baseWidget.size():
            if (lastFlow == QListView.TopToBottom and self.lastSize.width() == self.baseWidget.size().width()) or \
                    (lastFlow == QListView.LeftToRight and self.lastSize.height() == self.baseWidget.size().height()):
                print("delayedResize: list is longer/shorter, but not narrower/wider - refresh only deferred.")
                self.list.updateScrollBarRange()
                self.processDeferredDocumentThumbnails()
            else:
                print("delayedResize: size changed - refresh.")
                doRefresh = True
        elif self.list.flow() != lastFlow:
            print("delayedResize: direction changed - refresh.")
            doRefresh = True
        elif not checkThumbSizes():
            print("delayedResize: some items are improperly sized - refresh.")
            doRefresh = True
        else:
            print("delayedResize: size did not change - no refresh.")
            
        if doRefresh:
            self.list.invalidateItemRectsCache()
            self.list.itemRects()
            self.list._doNotRecacheItemRects = True
            print(bool(itemsWithBadThumbs), itemsWithBadThumbs)
            if itemsWithBadThumbs:
                print(" refresh", len(itemsWithBadThumbs), "items")
                for i in itemsWithBadThumbs:
                    item = self.list.item(i)
                    self.updateDocumentThumbnail(self.findDocumentWithItem(item))
            else:
                print(" refresh all items")
                self.refreshOpenDocuments(soft=True, force=False)
            self.list._doNotRecacheItemRects = False
            self.list.itemRects()
        
        self.lastSize = self.baseWidget.size()
    
    def imageCreated(self, image):
        print("image created -", image)
        fName = image.fileName()
        print(" name:", (fName if fName else "[not saved]"))
        
        self.documents = Application.documents()
        docIndex = len(self.documents)-1
        
        # assume new image will always be doc at end of documents list.
        doc = self.documents[docIndex]
        print(" #"+str(docIndex)+", id:", doc.rootNode().uniqueId())
        
        self.setDocumentExtraUid(doc)
        self.addDocumentToList(doc)
    
    def isDocumentUniquelyIdentified(self, doc):
        uid = doc.rootNode().uniqueId()
        extraUid = doc.annotation("ODD_extra_uid") or b''
        docCount = len(self.documents)
        for i in range(docCount):
            d = self.documents[i]
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
        docCount = len(self.documents)
        for i in range(docCount):
            d = self.documents[i]
            if d != doc:
                if uid == d.rootNode().uniqueId():
                    canRemoveExtraUid = False
                    if extraUid == d.annotation("ODD_extra_uid"):
                        print("uid clash between this image", doc, "and", d)
                        isUnique = False
                        break
        if not isUnique:
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
        
        self.documents = Application.documents()
        
        print("", self.currentDocumentId)
        print("", self.documentUniqueIdFromLastClosedView)
        if self.currentDocumentId == self.documentUniqueIdFromLastClosedView:
            print(" we've closed the document that was current.")
            if self.imageChangeDetected:
                print(" it was waiting to refresh, cancelling.")
                self.imageChangeDetected = False
                self.refreshTimer.stop()
            
            if len(self.documents) == 0:
                print(" it was the last open document.")
                self.currentDocumentId = None
        
        self.documentUniqueIdFromLastClosedView = None
        print("Image Closed:")
        print(" - SET documentUniqueIdFromLastClosedView =", self.documentUniqueIdFromLastClosedView)
    
    def imageSaved(self, filename):
        # unnecessary? the document just saved should be the active one
        doc = None
        docCount = len(self.documents)
        for i in range(docCount):
            if self.documents[i].fileName() == filename:
                doc = self.documents[i]
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
        
        self.documents = []
        
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
        self.baseWidget.setMinimumWidth(32)
        self.baseWidget.setMinimumHeight(32)
        self.setWidget(self.baseWidget)
        
        self.lastSize = self.baseWidget.size()
        self.resizeDelay = QTimer(self.baseWidget)
        self.resizeDelay.timeout.connect(self.delayedResize)
        
        self.refreshAllDelay = QTimer(self.baseWidget)
        self.refreshAllDelay.setInterval(1000)
        self.refreshAllDelay.setSingleShot(True)
        self.refreshAllDelay.timeout.connect(self.refreshAllDelayTimeout)
        
        self.itemUpdateTimer = QTimer(self.baseWidget)
        self.itemUpdateTimer.setInterval(500)
        self.itemUpdateTimer.timeout.connect(self.itemUpdateTimerTimeout)
        self.itemUpdateTimer.start()
        
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
    
    def itemUpdateTimerTimeout(self):
        if not self.dockVisible:
            return
        
        isSettingDisplayThumbnails = self.vs.readSetting("display") == "thumbnails"
        
        itemCount = self.list.count()
        for i in range(itemCount):
            item = self.list.item(i)
            doc = self.findDocumentWithItem(item)
            if not doc:
                assert False, "ODD:itemUpdateTimerTimeout: can't find document for item."
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
                name = self.documentDisplayName(doc)
                if oldName != name:
                    item.setText(name)
    
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
            else:
                print("refreshTimerTimeout - imageChangeDetected:true, lock:failed - document busy, wait")

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
        
        if (
                (direction == "horizontal" and oldDirection == QListView.LeftToRight) or
                (direction == "vertical"   and oldDirection == QListView.TopToBottom)
            ):
            return
        
        self.list.update()
        self.list.invalidateItemRectsCache()
    
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
        self.restartResizeDelayTimer()
    
    def restartResizeDelayTimer(self):
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
        
        if not doc:
            doc = self.findDocumentWithItem(item)
        
        self.deferredItemThumbnailCount += 1
        print("DEFERRED ITEM COUNT +1, =", self.deferredItemThumbnailCount)
        item.setData(self.ItemUpdateDeferredRole, True)
        print("mark deferred: " + self.documentDisplayName(doc) + " thumbnail update has been deferred.")
    
    def unmarkDocumentThumbnailAsDeferred(self, doc=None, item=None):
        if not item.data(self.ItemUpdateDeferredRole):
            #print("unmark deferred: already not marked.")
            return
        
        if not doc:
            doc = self.findDocumentWithItem(item)
        
        item.setData(self.ItemUpdateDeferredRole, False)
        self.deferredItemThumbnailCount -= 1
        print("DEFERRED ITEM COUNT -1, =", self.deferredItemThumbnailCount)
        print("unmark deferred: " + self.documentDisplayName(doc) + " thumbnail update is no longer deferred.")
    
    def processDeferredDocumentThumbnails(self):
        if not self.dockVisible:
            return
        
        if self.deferredItemThumbnailCount == 0:
            return
        
        assert self.deferredItemThumbnailCount >= 0, "ODD: deferredItemThumbnailCount is negative."
        
        viewRect = QRect(QPoint(0, 0), self.list.viewport().size())
        itemCount = self.list.count()
        for i in range(itemCount):
            item = self.list.item(i)
            if item.data(self.ItemUpdateDeferredRole):
                visRect = self.list.visualItemRect(item)
                if not viewRect.intersected(visRect).isEmpty():
                    doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
                    self.updateDocumentThumbnail(doc)
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
    
    def refreshOpenDocuments(self, soft=False, force=False):
        if soft:
            count = self.list.count()
            for i in range(count):
                item = self.list.item(i)
                self.updateDocumentThumbnail(self.findDocumentWithItem(item), force)
        else:
            self.deferredItemThumbnailCount = 0
            print("DEFERRED ITEM COUNT = 0")
            self.list.clear()
            for i in self.documents:
                self.addDocumentToList(i)
        self.list.invalidateItemRectsCache()
    
    def debugDump(self):
        count = len(self.documents)
        print(" - list of all documents (count:"+str(count)+") - ")
        for i in range(count):
            doc = self.documents[i]
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
        
        viewRect = QRect(QPoint(0, 0), self.list.viewport().size())
        visRect = self.list.visualItemRect(item)
        print("isItemOnScreen:", viewRect, visRect, bool(viewRect.intersected(visRect).isValid()))
        return viewRect.intersected(visRect).isValid()
    
    def updateDocumentThumbnailForced(self):
        self.updateDocumentThumbnail(doc=None, force=True)
    
    def updateDocumentThumbnail(self, doc=None, force=False):
        if not doc:
            doc = Application.activeDocument()
        if not doc:
            print("update thumb: no active document.")
            return
        
        item = self.findItemWithDocument(doc)
        if not item:
            print("update thumb: no list item associated with document.")
            return
        
        if doc == Application.activeDocument() and self.imageChangeDetected:
            print("stop or cancel imageChangeDetected refresh timer.")
            self.imageChangeDetected = False
            self.refreshTimer.stop()
        
        settingDisplayThumbs = self.vs.settingValue("display") == self.vs.SD["display"]["ui"]["btnThumbnails"]
        if not settingDisplayThumbs:
            force = False
        
        if not force:
            if not (settingDisplayThumbs and self.isItemOnScreen(item)):
                self.markDocumentThumbnailAsDeferred(None, item)
                print("update thumb: item not currently visible or docker in text mode, update later.")
                return
        
        self.unmarkDocumentThumbnailAsDeferred(doc, item)
        
        print("update thumb for", doc.fileName())#, end=" - ")
        thumbnail = self.generateThumbnailForItem(item, doc)
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
        item = QListWidgetItem("", self.list)
        item.setData(self.ItemDocumentSizeRole, QSize(doc.width(), doc.height()))
        item.setData(self.ItemModifiedStatusRole, doc.modified())
        if self.vs.settingValue("display") == self.vs.SD["display"]["ui"]["btnThumbnails"]:
            thumbnail = self.generateThumbnailForItem(item, doc)
            item.setData(Qt.DecorationRole, QPixmap.fromImage(thumbnail))
        else:
            item.setText(self.documentDisplayName(doc))
        uid = self.documentUniqueId(doc)
        item.setData(self.ItemDocumentRole, uid)
        
        self.list.invalidateItemRectsCache()
        self.list.update()
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
            self.unmarkDocumentThumbnailAsDeferred(self.findDocumentWithItem(item), item)
            del item
            self.ensureListSelectionIsActiveDocument()
            self.list.invalidateItemRectsCache()
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
        for doc in self.documents:
            if uid == self.documentUniqueId(doc):
                return doc
        print("ODD: could not find document with uid", str(uid))
        if enableFallback:
            print("ODD: falling back to best match")
            uid[1] = QUuid()
            for doc in self.documents:
                if uid == self.documentUniqueId(doc):
                    return doc
        return None
    
    def calculateRenderSizeForItem(self, item):
        return calculateRenderSizeForThumbnail(item.data(self.ItemDocumentSizeRole))
    
    def calculateRenderSizeForThumbnail(self, docSize=None):
        if self.vs.readSetting("thumbUseProjectionMethod"):
            return self.calculateDisplaySizeForThumbnail(docSize)
        else:
            return self.calculateDisplaySizeForThumbnail(docSize) * self.list.settingValue("thumbRenderScale")
    
    def calculateDisplaySizeForItem(self, item):
        return self.calculateDisplaySizeForThumbnail(item.data(self.ItemDocumentSizeRole))
    
    def calculateDisplaySizeForThumbnail(self, docSize=None):
        gutterPixels=2
        if not docSize:
            docSize = QSize(512, 512)
        docRatio = float(docSize.height()) / float(docSize.width())
        size = None
        scale = float(self.vs.readSetting("thumbDisplayScale"))

        # keep size from getting too big and slowing things down
        # (but don't kick in too soon, or many users might wonder why
        # thumb refuses to fill area, even after setting scale to 1.00).
        maxSize = 512
        
        if self.list.flow() == QListView.TopToBottom:
            scrollBarWidth = self.list.verticalScrollBar().sizeHint().width() if self.list.verticalScrollBar().isVisible() else 0
            width = self.list.width() - gutterPixels - scrollBarWidth
            width *= scale
            width = min(width, maxSize)
            height = round(width * docRatio)
            size = QSize(int(width), int(height))
            print("cdsft: Vert", scrollBarWidth, self.list.width(), docRatio, str(size.width())+"x"+str(size.height()))
        else:
            scrollBarHeight = self.list.horizontalScrollBar().sizeHint().height() if self.list.horizontalScrollBar().isVisible() else 0
            height = self.list.height() - gutterPixels - scrollBarHeight
            height *= scale
            height = min(height, maxSize)
            width = round(height / docRatio)
            size = QSize(int(width), int(height))
            print("cdsft: Hori", scrollBarHeight, self.list.height(), docRatio, str(size.width())+"x"+str(size.height()))
        
        if size.isEmpty():
            size = QSize(1, 1)
        
        return size
    
    def generateThumbnailForItem(self, item, doc):
        # ensure the thumbnail will be complete.
        doc.waitForDone()
        
        size = self.calculateDisplaySizeForThumbnail(item.data(self.ItemDocumentSizeRole))
        
        thumbnail = None
        
        settingUseProj = self.vs.readSetting("thumbUseProjectionMethod") == "true"
        
        scaleFactor = (
                self.vs.settingValue("thumbRenderScale") if not settingUseProj else 1
        )
        
        def generator(doc, size):
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
