# SPDX-License-Identifier: CC0-1.0

from PyQt5.QtCore import Qt, QByteArray, QBuffer, QPoint, QSize
from PyQt5.QtGui import QPixmap, QScreen, QContextMenuEvent
from PyQt5.QtWidgets import QWidget, QBoxLayout, QVBoxLayout, QHBoxLayout, QListView, QPushButton, QMenu, QAbstractItemView, QListWidget, QListWidgetItem, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QSizePolicy
from krita import *
from time import *
from pathlib import Path
from .opendocumentsviewsettings import OpenDocumentsViewSettings as ODVS


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
    
    def activated(self, index):
        self.clicked(index)
    
    def clicked(self, index):
        item = self.list.item(index.row())
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if doc:
            self.findAndActivateView(doc)
        else:
            print("ODD: clicked an item that has no doc, or points to a doc that doesn't exist!")
    
    def documentDisplayName(self, doc):
        fPath = doc.fileName()
        fName = Path(fPath).name
        tModi = " *" * doc.modified()
        return (fName if fName else "[not saved]") + tModi
    
    def entered(self, index):        
        item = self.list.item(index.row())
        
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if not doc:
            return
        
        fPath = doc.fileName()
        ttText = ""
        
        ttText += "<table border='0' style='margin:16px; padding:16px'><tr>"
        
        # From answer to "Use a picture or image in a QToolTip": https://stackoverflow.com/a/34300771
        if doc.width() * doc.height() <= ODVS.ThumbnailsTooltipsSliderValues[self.vs.panelThumbnailsTooltipsSlider.value()]:
            img = doc.thumbnail(128, 128)
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
        
        self.listToolTip.setWindowFlags(Qt.ToolTip)
        self.listToolTip.setText(ttText)
        
        ttPos = None
        
        listTopLeft = self.list.mapToGlobal(self.list.frameGeometry().topLeft())
        listBottomRight = self.list.mapToGlobal(self.list.frameGeometry().bottomRight())
        listTopRight = self.list.mapToGlobal(self.list.frameGeometry().topRight())
        listCenter = (listTopLeft+listBottomRight)/2
        itemRect = self.list.visualRect(index)
        
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
        self.listToolTip.show()
    
    def delayedResize(self):
        self.resizeDelay.stop()
        print("delayedResize: lastSize:", self.lastSize)
        print("               new size:", self.baseWidget.size())
        lastFlow = self.list.flow()
        self.setDockerDirection(self.vs.readSetting("viewDirection"))
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
        self.addDocumentToList(image)
    
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
        if self.vs.panelThumbnailsRefreshOnSaveCheckBox.isChecked():
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
        self.list = QListWidget()
        self.listToolTip = QLabel()
        self.buttonLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.loadButton = QPushButton()
        self.loadButton.setIcon(Application.icon('view-refresh'))
        self.viewButton = QPushButton()
        self.viewButton.setIcon(Application.icon('view-choose'))
        
        self.setDockerDirection(self.vs.readSetting("viewDirection"))
        self.list.setMovement(QListView.Free)
        self.list.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.activated.connect(self.clicked)
        self.list.clicked.connect(self.clicked)
        self.list.setMouseTracking(True)
        self.list.entered.connect(self.entered)
        self.list.viewportEntered.connect(self.viewportEntered)
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
        setting = self.vs.readSetting("viewRefreshPeriodicallyChecks")
        self.imageChangeDetectionTimer.setInterval(
            ODVS.ThumbnailsRefreshPeriodicallyChecksValues[ODVS.ThumbnailsRefreshPeriodicallyChecksStrings.index(setting)]
        )
        self.imageChangeDetectionTimer.timeout.connect(self.imageChangeDetectionTimerTimeout)
        self.refreshTimer = QTimer(self.baseWidget)
        setting = self.vs.readSetting("viewRefreshPeriodicallyDelay")
        self.refreshTimer.setInterval(
            ODVS.ThumbnailsRefreshPeriodicallyDelayValues[ODVS.ThumbnailsRefreshPeriodicallyDelayStrings.index(setting)]
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
        
        self.itemTextUpdateTimer = QTimer(self.baseWidget)
        self.itemTextUpdateTimer.setInterval(1000)
        self.itemTextUpdateTimer.timeout.connect(self.itemTextUpdateTimerTimeout)
        if self.vs.readSetting("viewDisplay") == "text":
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
    
    def itemTextUpdateTimerTimeout(self):
        count = self.list.count()
        for i in range(count):
            item = self.list.item(i)
            doc = self.findDocumentWithItem(item)
            item.setText(self.documentDisplayName(doc))
    
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
            if self.vs.readSetting("viewDisplay") == "text":
                self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            else:
                self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
    
    def viewportEntered(self):
        self.listToolTip.hide()
    
    def dockVisibilityChanged(self, visible):
        print("visibilityChanged: visible =", visible)
        self.dockVisible = visible
        self.processDeferredDocumentThumbnails()
        if self.vs.panelThumbnailsRefreshPeriodicallyCheckBox.isChecked():
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
        index = self.list.selectedIndexes()[0]
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
        item = self.list.item(index.row())
        
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if not doc:
            print("ODD: right-clicked an item that has no doc, or points to a doc that doesn't exist!")
            return
        
        print("selected:", index, " -", doc.fileName())
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
        menu.addAction(app.action('file_documentinfo'))
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
        if self.vs.panelDisplayButtonGroup.checkedButton() == self.vs.panelDisplayTextButton:
            print("update thumb: docker list is in text-only mode.")
            return
        
        item = self.findItemWithDocument(doc)
        if not item:
            print("update thumb: no list item associated with document.")
            return
        
        if not force:
            if not self.isItemOnScreen(item):
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
        if self.vs.panelDisplayButtonGroup.checkedButton() == self.vs.panelDisplayThumbnailsButton:
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
        """
        return doc.rootNode().uniqueId()
    
    def findDocumentWithUniqueId(self, uid):
        for doc in Application.documents():
            if uid == self.documentUniqueId(doc):
                return doc
        print("ODD: could not find document with uid", str(uid))
        return None
    
    def generateThumbnailForDocument(self, doc):        
        # ensure the thumbnail will be complete
        doc.waitForDone()
        
        kludgePixels=6
        width = 0
        if self.list.flow() == QListView.TopToBottom:
            scrollBarWidth = self.list.verticalScrollBar().sizeHint().width()
            width = self.list.width() - kludgePixels - scrollBarWidth
        else:
            scrollBarHeight = self.list.horizontalScrollBar().sizeHint().height()
            width = self.list.height() - kludgePixels - scrollBarHeight
        #print("gtfd: calculated width:", width)
        
        # keep size from getting too big and slowing things down
        width = min(width, 256)
        
        thumbnail = None
        
        scaleFactor = ODVS.ThumbnailsScaleSliderValues[self.vs.panelThumbnailsScaleSlider.value()]
        
        def generator(doc, width):
            # new document may briefly exist as qobject type before becoming document,
            # during which projection isn't available but thumbnail is.
            # projection is much faster so prefer it when available.
            if type(doc) == Document:
                return doc.projection(0, 0, doc.width(), doc.height())
            else:
                return doc.thumbnail(width, width)
        
        if scaleFactor == 1:
            thumbnail = generator(doc, width)
        
            if thumbnail.isNull():
                return None
        else:
            scaledWidth = int(width * scaleFactor)
            thumbnail = doc.thumbnail(scaledWidth, scaledWidth)
        
            if thumbnail.isNull():
                return None
            
            thumbSize = QSize(int(width*self.devicePixelRatioF()), int(width*0.75*self.devicePixelRatioF()))
            thumbnail = thumbnail.scaled(thumbSize, Qt.KeepAspectRatio, Qt.FastTransformation)
        
        thumbSize = QSize(int(width*self.devicePixelRatioF()), int(width*self.devicePixelRatioF()))
        #print("desired thumbSize:", thumbSize.width(), "x", thumbSize.height())
        
        if self.list.flow() == QListView.TopToBottom:
            if thumbnail.width() < thumbSize.width():
                thumbnail = thumbnail.scaledToWidth(thumbSize.width(), Qt.FastTransformation)
            else:
                thumbnail = thumbnail.scaledToWidth(thumbSize.width(), Qt.SmoothTransformation)
        else:
            if thumbnail.height() < thumbSize.height():
                thumbnail = thumbnail.scaledToHeight(thumbSize.height(), Qt.FastTransformation)
            else:
                thumbnail = thumbnail.scaledToHeight(thumbSize.height(), Qt.SmoothTransformation)
        thumbnail.setDevicePixelRatio(self.devicePixelRatioF())
        #print("final size:", thumbnail.width(), "x", thumbnail.height())
        
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
        docname = OpenDocumentsDocker.documentDisplayName(self, doc)

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
