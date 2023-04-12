from time import *
from datetime import datetime
from krita import *
from pathlib import Path
from .oddsettings import ODDSettings

class ODD(Extension):
    dockers = []
    windows = []
    views = []
    documents = []
    unusedCacheSize = 0
    instance = None
    
    def __init__(self, parent):
        print("ODD:__init__")
        super().__init__(parent)
        cls = self.__class__
        
        if len(Application.windows()) > 0:
            if len(self.dockers) > 0:
                print("ODD: reactivated.\n     should be safe to continue.")
            else:
                print("ODD: activated mid-krita session.\n     please restart krita.")
            return
        
        if not cls.instance:
            cls.viewClosedDelay = QTimer(None)
            cls.viewClosedDelay.setInterval(0)
            cls.viewClosedDelay.setSingleShot(True)
            cls.viewClosedDelay.timeout.connect(cls._viewClosed)
            cls.instance = self
        
        #ODDSettings.debugDump()
        
        appNotifier = Application.notifier()
        appNotifier.setActive(True)
        
        appNotifier.viewClosed.connect(cls.viewClosed)
        appNotifier.viewCreated.connect(cls.viewCreated)
        appNotifier.windowCreated.connect(self.windowCreated)
        appNotifier.windowIsBeingCreated.connect(self.windowIsBeingCreated)

    def setup(self):
        print("ODD:__setup__")
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
        if not doc:
            return
        
        fname = doc.fileName()
        docname = ODD.documentDisplayName(doc, showIfModified=False)

        msgBox = QMessageBox(
                QMessageBox.Warning,
                "Krita",
                "Revert unsaved changes to the document <b>'"+docname+"'</b>?<br/><br/>" \
                "Any unsaved changes will be permanently lost.",
                parent = Application.activeWindow().qwindow()
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
            
            oddDocker = self.dockers[0].__class__
            if oddDocker.imageChangeDetected:
                oddDocker.imageChangeDetected = False
                oddDocker.refreshTimer.stop()
            
            self.revertedDocFileName = fname
            if not hasattr(self, "revertDelay"):
                self.revertDelay = QTimer(self)
                self.revertDelay.setInterval(0)
                self.revertDelay.setSingleShot(True)
                self.revertDelay.timeout.connect(self.postRevert)
            
            doc.close()
            self.revertDelay.start()
        else:
            print("Cancel")
    
    def postRevert(self):
        fname = self.revertedDocFileName
        if fname is None:
            assert False, "ODD:PostRevert: called without a filename."
            return
        self.revertedDocFileName = None
        print("postRevert for", fname)
        newdoc = Application.openDocument(fname)
        newdoc.waitForDone()
        newview = Application.activeWindow().addView(newdoc)
        print("postRevert finished.")
    
    @classmethod
    def viewCreated(cls):
        print("ODD:viewCreated")
        
        appViews = Application.views()
        for view in appViews:
            if view in cls.views:
                print("existing view", view)
            else:
                print("new view:", view)
                cls.views.append(view)
        print(" - views - ")
        for i in enumerate(cls.views):
            print(i[0], ":", i[1])
        
        cls.updateDocsAndWins()
    
    @classmethod
    def viewClosed(cls, view):
        # must wait a little for krita to remove closed view from it's list of views.
        d = view.document()
        print("viewClosed", view, (str(d) + Path(d.fileName()).name) if d else "")
        cls.viewClosedDelay.start()
    
    @classmethod
    def _viewClosed(cls):
        print("_viewClosed")
        
        closedViews = []
        appViews = Application.views()
        for view in cls.views:
            if view in appViews:
                #print("kept view", view)
                pass
            else:
                print("closed view:", view)
                closedViews.append(view)
        for view in closedViews:
            cls.views.remove(view)
        print(" - views - ")
        for i in enumerate(cls.views):
            print(i[0], ":", i[1])
        
        cls.updateDocsAndWins()
    
    @classmethod
    def updateDocsAndWins(cls):
        docStillExists = [False] * len(cls.documents)
        
        for view in cls.views:
            doc = view.document()
            if not doc:
                print("UpdateDocsAndWins: no doc for view")
                continue
            if matchList := [i for i in enumerate(cls.documents) if i[1]["document"] == doc]:
                knownDoc = matchList[0]
                print("existing doc:", knownDoc[1]["document"])
                docStillExists[knownDoc[0]] = True
            else:
                print("new doc:", doc)
                cls.documents.append({
                    "document": doc,
                    "thumbnails": {},
                    "created": datetime.now(),
                })
                for docker in cls.dockers:
                    docker.documentCreated(doc)
        
        print("docStillExists:")
        for i in enumerate(docStillExists):
            print(i[0], ":", i[1])
        
        i = 0
        while i < len(docStillExists):
            if not docStillExists[i]:
                print("doc removed:", cls.documents[i])
                for docker in cls.dockers:
                    docker.documentClosed(cls.documents[i]["document"])
                del cls.documents[i]
                del docStillExists[i]
            else:
                i += 1
    
    @classmethod
    def docDataFromDocument(cls, doc):
        if matchList := [i for i in enumerate(cls.documents) if i[1]["document"] == doc]:
            return matchList[0][1]
        else:
            return None
    
    @classmethod
    def requestThumbnail(cls, docData, thumbKey):
        if not docData:
            return None
        if type(docData) == Document:
            if (docData := cls.docDataFromDocument(docData)) is None:
                return None
        
        isNew = False
        if not thumbKey in docData["thumbnails"]:
            isNew = True
            docData["thumbnails"][thumbKey] = {"pixmap":None, "valid":False, "users":[], "lastUsed":0}
        
        thumb = docData["thumbnails"][thumbKey]
        
        if thumb["valid"]:
            return thumb["pixmap"]
        
        pm = QPixmap.fromImage(cls.generateThumbnail(docData["document"], thumbKey[0], thumbKey[1], thumbKey[2], thumbKey[3]))
        thumb["pixmap"] = pm
        thumb["valid"] = True
        thumb["lastUsed"] = process_time_ns()
        
        cls.evictExcessUnusedCache()
        
        if isNew:
            cls.unusedCacheSize += pm.width() * pm.height() * pm.depth()
        
        # tell docker instances to redraw with new thumbnail?
        
        return thumb["pixmap"]
    
    def generateThumbnail(doc, thumbWidth, thumbHeight, regionWidth, regionHeight):
        if type(doc) == Document and ODDSettings.readSettingFromConfig("thumbUseProjectionMethod") == "true":
            i = doc.projection(0, 0, regionWidth, regionHeight)
            if i:
                if thumbWidth < regionWidth:
                    return i.scaled(thumbWidth, thumbHeight, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                else:
                    return i.scaled(thumbWidth, thumbHeight, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            return i
        else:
            return doc.thumbnail(thumbWidth, thumbHeight)
    
    @classmethod
    def invalidateThumbnails(cls, docData):
        print("ODD:invalidateThumbnails")
        if type(docData) == Document:
            if (docData := cls.docDataFromDocument(docData)) is None:
                return
        for thumbData in docData["thumbnails"].values():
            thumbData["valid"] = False
        
        cls.cleanupUnusedInvalidatedThumbnails(docData)
        
    @classmethod
    def cleanupUnusedInvalidatedThumbnails(cls, docData):
        thumbs = docData["thumbnails"]
        for thumbData in thumbs.values():
            if not thumbData["valid"] and len(thumbData["users"]) == 0:
                pm = thumbData["pixmap"]
                cls.unusedCacheSize -= pm.width() * pm.height() * pm.depth()
        [thumbs.pop(t, None) for t in [t[0] for t in thumbs.items() if t[1]["valid"] == False and len(t[1]["users"]) == 0]]
    
    @classmethod
    def addThumbnailUser(cls, who, docData, thumbKey):
        print("ODD:addThumbnailUser")
        if type(docData) == Document:
            if (docData := cls.docDataFromDocument(docData)) is None:
                return
        thumbData = docData["thumbnails"][thumbKey]
        if not who in thumbData["users"]:
            thumbData["users"].append(who)
            if len(thumbData["users"]) == 1:
                pm = thumbData["pixmap"]
                cls.unusedCacheSize -= pm.width() * pm.height() * pm.depth()
    
    @classmethod
    def removeThumbnailUser(cls, who, docData, thumbKey):
        print("ODD:removeThumbnailUser")
        if type(docData) == Document:
            if (docData := cls.docDataFromDocument(docData)) is None:
                return
        thumbData = docData["thumbnails"][thumbKey]
        if not who in thumbData["users"]:
            return
        thumbData["users"].remove(who)
        if len(thumbData["users"]) == 0:
            if thumbData["valid"]:
                pm = thumbData["pixmap"]
                cls.unusedCacheSize += pm.width() * pm.height() * pm.depth()
                thumbData["lastUsed"] = process_time_ns()
                cls.evictExcessUnusedCache()
            else:
                print("removed last user of invalidated thumb, deleting thumb.")
                del docData["thumbnails"][thumbKey]
        
    
    @classmethod
    def evictExcessUnusedCache(cls, maxSize=-1):
        if maxSize == -1:
            maxSize = int(ODDSettings.globalSettings["excessThumbCacheLimit"]) * 8192 #1024*8
        if cls.unusedCacheSize-maxSize <= 0:
            return
        
        print(" - evictExcessUnusedCache - ")
        print("before: unused cache size:", cls.unusedCacheSize, ", max allowed:", maxSize, ", excess:", cls.unusedCacheSize-maxSize)
        evictableThumbs = []
        for d in cls.documents:
            for t in d["thumbnails"].items():
                if len(t[1]["users"]) == 0:
                    evictableThumbs.append((d, t[0], t[1]))
        if len(evictableThumbs) == 0:
            print(" - nothing to evict - ")
            return
        evictableThumbsSorted = sorted(evictableThumbs, key = lambda e: e[2]["lastUsed"])
        print("evictable thumbs:")
        i = 1
        for e in evictableThumbsSorted:
            print("#"+str(i)+":doc", e[0]["document"], ", tKey:", e[1], "(lu:", e[2]["lastUsed"], ")")
            i += 1
        while cls.unusedCacheSize > maxSize:
            e = evictableThumbsSorted[0]
            pm = e[2]["pixmap"]
            size = pm.width() * pm.height() * pm.depth()
            print("evicting:", e[0]["document"], e[1], end="... ")
            del e[0]["thumbnails"][e[1]]
            del evictableThumbsSorted[0]
            cls.unusedCacheSize -= size
            print("removed", size, "- excess remaining:", cls.unusedCacheSize-maxSize)
        print("result: unused cache size:", cls.unusedCacheSize, ", max allowed:", maxSize, ", excess:", cls.unusedCacheSize-(maxSize))
        print(" - evict finished - ")
    
    @classmethod
    def findAndActivateView(cls, doc):
        # TODO ...
        for win in Application.windows():
            for view in win.views():
                if view.document() == doc:
                    win.activate()
                    win.showView(view)
                    view.setVisible()
                    return
    
    def documentHasViewsInWindow(doc, win):
        for view in win.views():
                if view.document() == doc:
                    return True
        return False
    
    @classmethod
    def windowFromQWindow(cls, qwin):
        for win in cls.windows:
            if win.qwindow() == qwin:
                return win
        return None
    
    def thumbnailKey(thumbWidth, thumbHeight, regionWidth, regionHeight):
        return (thumbWidth, thumbHeight, regionWidth, regionHeight)
    
    def documentDisplayName(doc, showIfModified=True, unsavedName="[not saved]"):
        if doc:
            fPath = doc.fileName()
            fName = Path(fPath).name
            tModi = " *" * doc.modified() * showIfModified
        else:
            fName = "[no document]"
            tModi = ""
        return (fName if fName else unsavedName) + tModi
    
    def windowIsBeingCreated(self, window):
        cls = self.__class__
        print("window being created:", window, "(" + window.qwindow().objectName() + ")")
        window.qwindow().installEventFilter(self)
        window.qwindow().destroyed.connect(cls.windowDestroyed)
    
    def windowCreated(self):
        cls = self.__class__
        
        appWins = Application.windows()
        for win in appWins:
            if win in cls.windows:
                print("existing win:", win)
            else:
                print("new win:", win)
                cls.windows.append(win)
        window = cls.windows[-1]
        print("window created:", window)
        docker = cls.dockers[-1]
        print("connect window", window, "activeViewChanged to", docker)
        window.activeViewChanged.connect(docker.activeViewChanged)
    
    @classmethod
    def eventFilter(cls, obj, event):
        if type(obj) == QMainWindow:
            if event.type() in (QEvent.Resize, QEvent.Move):
                for d in cls.dockers:
                    if d.parent() == obj:
                        d.winGeoChangeResponseDelay.start()
        return False
    
    @classmethod
    def windowDestroyed(cls, obj):
        print("window destroyed:", obj)
        
        closedWins = []
        appWins = Application.windows()
        for win in cls.windows:
            if win in appWins:
                print("kept win", win)
                pass
            else:
                print("closed win:", win)
                closedWins.append(win)
        for win in closedWins:
            cls.windows.remove(win)
            
        print(" - wins - ")
        for i in enumerate(cls.windows):
            print(i[0], ":", i[1])
        
        # ~ print("-pre-")
        # ~ for i in range(len(cls.dockers)):
            # ~ print("docker", i, ":", cls.dockers[i], cls.dockers[i].parent() if cls.dockers[i] else "")
            
        for i in range(len(cls.dockers)):
            docker = cls.dockers[i]
            if type(docker.parent()) != QMainWindow: #QMainWindow becomes QObject when closed/destroyed
                print("delete ref to docker", docker)
                removeUserBuffer = []
                for d in cls.documents:
                    for t in d["thumbnails"].items():
                        if docker in t[1]["users"]:
                            removeUserBuffer.append((d, t[0]))
                for ru in removeUserBuffer:
                    cls.removeThumbnailUser(docker, ru[0], ru[1])
                    
                cls.dockers[i] = None
                
        # ~ print("-mid-")
        # ~ for i in range(len(cls.dockers)):
            # ~ print("docker", i, ":", cls.dockers[i], cls.dockers[i].parent() if cls.dockers[i] else "")
            
        for i in range(len(cls.dockers)-1, -1, -1):
            if cls.dockers[i] == None:
                #print("deleting ref to docker", i, ":", cls.dockers[i])
                del cls.dockers[i]
                
        # ~ print("-post-")
        # ~ for i in range(len(cls.dockers)):
            # ~ print("docker", i, ":", cls.dockers[i], cls.dockers[i].parent() if cls.dockers[i] else "")
    
    def getScreen(self, who):
        if hasattr(who, "screen"):
            return who.screen()
        if who.windowHandle():
            return who.windowHandle().screen()
        if who.parent() and who.parent().windowHandle():
            return who.parent().windowHandle().screen()
