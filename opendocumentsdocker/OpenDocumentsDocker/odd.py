# SPDX-License-Identifier: GPL-3.0-or-later

from PyQt5.QtWidgets import QApplication
from time import *
from datetime import datetime
from krita import *
from pathlib import Path

import logging
logger = logging.getLogger("odd")


class ODD(Extension):
    dockers = []
    windows = []
    views = []
    documents = []
    unusedCacheSize = 0
    instance = None
    kritaHasFocus = False
    activeDocument = None
    
    def __init__(self, parent):
        logger.debug("ODD:__init__")
        super().__init__(parent)
        cls = self.__class__
        
        if len(Application.windows()) > 0:
            if len(self.dockers) > 0:
                logger.warning("ODD: reactivated.\n     should be safe to continue.")
            else:
                logger.warning("ODD: activated mid-krita session.\n     please restart krita.")
            return
        
        cls.winForQWin = {}
        
        if not cls.instance:
            cls.viewClosedDelay = QTimer(self)
            cls.viewClosedDelay.setInterval(0)
            cls.viewClosedDelay.setSingleShot(True)
            cls.viewClosedDelay.timeout.connect(cls._viewClosed)
            cls.instance = self
        
        ODDImageChangeDetector()
        
        QApplication.instance().focusWindowChanged.connect(self.focusWindowChanged)
        
        #ODDSettings.debugDump()
        
        appNotifier = Application.notifier()
        appNotifier.setActive(True)
        
        appNotifier.viewClosed.connect(cls.viewClosed)
        appNotifier.viewCreated.connect(cls.viewCreated)
        appNotifier.windowCreated.connect(self.windowCreated)
        appNotifier.windowIsBeingCreated.connect(self.windowIsBeingCreated)

    def setup(self):
        logger.debug("ODD:__setup__")
        pass

    def createActions(self, window):
        actionCopyMerged = window.createAction("ODDQuickCopyMergedAction", "Quick Copy Merged", "")
        actionCopyMerged.triggered.connect(self.quickCopyMergedAction)
        
        actionFileRevert = window.createAction("ODDFileRevertAction", "Revert", "")
        actionFileRevert.triggered.connect(self.fileRevertAction)
    
    def quickCopyMergedAction(self):
        logger.info("perform ODDQuickCopyMergedAction")
        app = Application
        app.action('select_all').trigger()
        app.action('copy_merged').trigger()
        app.action('edit_undo').trigger()
        app.action('edit_undo').trigger()
    
    def fileRevertInPlaceCondition(self, view, doc):
        if not self.fileReverter.cleanupPhase:
            return view.document() == doc
        else:
            return view == self.fileReverter.tempView
    
    def fileRevertInPlaceOperation(self):
        if not self.fileReverter.cleanupPhase:
            logger.debug("fileRevertInPlaceOperation: %s %s -> %s", self.fileReverter, self.fileReverter.targetDoc, self.fileReverter.newDoc)
            view = Application.activeWindow().activeView()
            
            canvas = view.canvas()
            canvasMirror = canvas.mirror()
            canvasRotation = canvas.rotation()
            canvasWrapAroundMode = canvas.wrapAroundMode()
            canvasLevelOfDetailMode = canvas.levelOfDetailMode()
            
            view.setDocument(self.fileReverter.newDoc)
            
            canvas = view.canvas()
            canvas.setMirror(canvasMirror)
            canvas.setRotation(canvasRotation)
            canvas.setWrapAroundMode(canvasWrapAroundMode)
            canvas.setLevelOfDetailMode(canvasLevelOfDetailMode)
            
            if self.fileReverter.aboutToEnterCleanupPhase:
                self.fileReverter.cleanupPhase = True
        else:
            logger.debug("fileRevertInPlaceOperation (cleanup temp view): %s", self.fileReverter)
            Application.action('file_close').trigger()
    
    def fileRevertInPlaceLastViewPreProcess(self):
        if not self.fileReverter.cleanupPhase:
            self.fileReverter.aboutToEnterCleanupPhase = True
            return False
        else:
            self.fileReverter.targetDoc = self.fileReverter.newDoc
            return True
    
    def fileRevertInPlaceFinished(self):
        logger.debug("fileRevertInPlaceFinished: deleting fileReverter")
        self.fileReverter.deleteLater()
        del self.fileReverter
        Application.setBatchmode(False)
    
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
        btnDoInPlace = QCheckBox("Reuse current views", msgBox)
        btnDoInPlace.setChecked(True)
        msgBox.setCheckBox(btnDoInPlace)
        btnRevert.setIcon(Application.icon('warning'))
        msgBox.setDefaultButton(QMessageBox.Cancel)
        msgBox.exec()
        
        if msgBox.clickedButton() == btnRevert:
            if btnDoInPlace.isChecked():
                logger.info("Revert (place into current views)")
                newDoc = Application.openDocument(fname)
                if not newDoc:
                    logger.info("cancel: the revert-to document was not opened.")
                    return
                newDoc.waitForDone()
                newView = Application.activeWindow().addView(newDoc)
                logger.debug("newDoc ready. newView = %s", newView)
                self.fileReverter = ODDViewProcessor(
                    operation = lambda: self.fileRevertInPlaceOperation(),
                    selectionCondition = lambda v: self.fileRevertInPlaceCondition(v, doc),
                    finishedCallback = lambda: self.fileRevertInPlaceFinished(),
                    lastViewPreProcessCallback = lambda: self.fileRevertInPlaceLastViewPreProcess()
                )
                self.fileReverter.targetDoc = doc
                self.fileReverter.oldDoc = doc
                self.fileReverter.newDoc = newDoc
                self.fileReverter.tempView = newView
                self.fileReverter.aboutToEnterCleanupPhase = False
                self.fileReverter.cleanupPhase = False
                logger.debug("old: %s, new: %s", doc, newDoc)
                Application.setBatchmode(True)
                doc.setBatchmode(True)
                doc.setModified(False)
                self.fileReverter.start()
            else:
                logger.info("Revert (open in single view)")
                
                # suppress save prompt by telling Krita the document wasn't modified.
                # --> set Application batch mode here?
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
            logger.info("Cancel")
    
    def postRevert(self):
        fname = self.revertedDocFileName
        if fname is None:
            logger.error("ODD:PostRevert: called without a filename.")
            return
        self.revertedDocFileName = None
        logger.debug("postRevert for %s", fname)
        newdoc = Application.openDocument(fname)
        newdoc.waitForDone()
        newview = Application.activeWindow().addView(newdoc)
        logger.debug("postRevert finished.")
    
    def focusWindowChanged(self, focusWindow):
        cls = self.__class__
        hadFocus = cls.kritaHasFocus
        cls.kritaHasFocus = bool(focusWindow)
        #logger.debug("krita has {} focus.".format(("already got" if hadFocus else "regained") if cls.kritaHasFocus else "lost"))
        
        cls.updateActiveDocument()
        
        if hadFocus != cls.kritaHasFocus:
            if cls.kritaHasFocus:
                ODDImageChangeDetector.removeStopper(ODDImageChangeDetector.StopReasonBlur)
                for docker in cls.dockers:
                        docker.processDeferredDocumentThumbnails()
                ODDImageChangeDetector.startCooldown()
            else:
                ODDImageChangeDetector.addStopper(ODDImageChangeDetector.StopReasonBlur)
    
    @classmethod
    def viewCreated(cls):
        logger.info("ODD:viewCreated")
        
        appViews = Application.views()
        for view in appViews:
            if view in cls.views:
                #logger.debug("existing view %s", view)
                pass
            else:
                logger.debug("new view: %s", view)
                cls.views.append(view)
        # ~ logger.debug(" - views - ")
        # ~ for i in enumerate(cls.views):
            # ~ logger.debug("%s: %s", i[0], i[1])
        
        cls.updateDocumentsFromViews()
        
        for docker in cls.dockers:
            # ensure list shows no-win-in-view icons as appropriate.
            docker.list._isItemsToDrawDirty = True
            docker.list.viewport().update()
    
    @classmethod
    def viewClosed(cls, view):
        # must wait a little for krita to remove closed view from it's list of views.
        d = view.document()
        logger.info("viewClosed %s %s", view, (str(d) + Path(d.fileName()).name) if d else "")
        cls.viewClosedDelay.start()
    
    @classmethod
    def _viewClosed(cls):
        logger.debug("_viewClosed")
        
        closedViews = []
        appViews = Application.views()
        for view in cls.views:
            if view in appViews:
                #logger.debug("kept view %s", view)
                pass
            else:
                logger.debug("closed view: %s", view)
                closedViews.append(view)
        for view in closedViews:
            cls.views.remove(view)
        # ~ logger.debug(" - views - ")
        # ~ for i in enumerate(cls.views):
            # ~ logger.debug("%s: %s", i[0], i[1])
        
        for docData in cls.documents:
            for k,v in docData["lastViewInWindow"].items():
                logger.debug(v)
                if v not in cls.views:
                    logger.debug("a closed view was latest active view on doc %s in its window.", docData["document"])
                    docData["lastViewInWindow"][k] = None
        
        cls.updateDocumentsFromViews()
        
        for docker in cls.dockers:
            if docker.filtButton.isChecked():
                docker.toggleDockerFiltering()
            # ensure list shows no-win-in-view icons as appropriate.
            docker.list._isItemsToDrawDirty = True
            docker.list.viewport().update()
    
    @classmethod
    def updateDocumentsFromViews(cls):
        docStillExists = [False] * len(cls.documents)
        
        for docData in cls.documents:
            for w in docData["viewCountPerWindow"]:
                docData["viewCountPerWindow"][w] = 0
        
        for view in cls.views:
            doc = view.document()
            win = view.window()
            if not win:
                continue
            qwin = win.qwindow()
            if not doc:
                logger.debug("UpdateDocsAndWins: no doc for view")
                continue
            if matchList := [i for i in enumerate(cls.documents) if i[1]["document"] == doc]:
                knownDoc = matchList[0]
                docStillExists[knownDoc[0]] = True
                docData = knownDoc[1]
                if qwin in docData["viewCountPerWindow"]:
                    docData["viewCountPerWindow"][qwin] += 1
                else:
                    docData["viewCountPerWindow"][qwin] = 1
                #logger.debug("existing doc {} has {} views in {}".format(docData["document"], docData["viewCountPerWindow"][qwin], qwin.objectName()))
            else:
                logger.info("new doc: %s", doc)
                cls.documents.append({
                    "document": doc,
                    "thumbnails": {},
                    "created": datetime.now(),
                    "lastViewInWindow": {win.qwindow():None for win in cls.windows},
                    "viewCountPerWindow": {win.qwindow():0 for win in cls.windows},
                })
                cls.documents[-1]["lastViewInWindow"  ][qwin] = view
                cls.documents[-1]["viewCountPerWindow"][qwin] = 1
                logger.debug("\n".join("  {}: {}".format(k, v) for k,v in cls.documents[-1].items()))
                for docker in cls.dockers:
                    docker.documentCreated(doc)
        
        # ~ logger.debug("docStillExists:")
        # ~ for i in enumerate(docStillExists):
            # ~ logger.debug("%s: %s", i[0], i[1])
        
        i = 0
        while i < len(docStillExists):
            if not docStillExists[i]:
                logger.info("doc removed: %s (%s)", cls.documents[i]["document"], cls.documents[i]["document"].fileName())
                for docker in cls.dockers:
                    docker.documentClosed(cls.documents[i]["document"])
                # ensure it will be removed from ODDImageChangeDetector list of changed docs.
                if matchList := [cd for cd in enumerate(ODDImageChangeDetector.changedDocs) if cd[1]["docData"]["document"] == cls.documents[i]["document"]]:
                    logger.debug("Deleting entry of ODDImageChangeDetector.changedDocs at index %s", matchList[0][0])
                    if ODDImageChangeDetector.changedDoc == matchList[0][1]:
                        logger.debug("and remove as current changedDoc")
                        ODDImageChangeDetector.changedDoc = None
                    del ODDImageChangeDetector.changedDocs[matchList[0][0]]
                # account for any leftover thumbs.
                for thumbKey,thumbData in cls.documents[i]["thumbnails"].items():
                    pm = thumbData["pixmap"]
                    logger.debug("doc {}: removing thumb {} with size {}".format(
                        cls.documents[i]["document"], thumbKey, thumbData["size"]
                    ))
                    cls.unusedCacheSize -= thumbData["size"]
                del cls.documents[i]
                del docStillExists[i]
                if len(cls.documents) == 0:
                    cls.updateActiveDocument()
            else:
                i += 1
    
    @classmethod
    def updateActiveDocument(cls):
        cls.activeDocument = Application.activeDocument()
        logger.debug("ODD.activeDocument -> %s", cls.activeDocument.fileName() if type(cls.activeDocument) is Document else "None")
        ODDImageChangeDetector.activeDocumentChanged()
    
    @classmethod
    def docDataFromDocument(cls, doc):
        return next(
                filter(lambda docData: docData["document"] == doc, cls.documents), None
        )
    
    @classmethod
    def requestThumbnail(cls, docData, thumbKey, forceNotProgressive=False):
        if not docData:
            return None
        if type(docData) == Document:
            if (docData := cls.docDataFromDocument(docData)) is None:
                return None
        
        logger.debug("requestThumbnail: doc: %s", docData["document"].fileName())
        logger.debug("                  thKey: %s", thumbKey)
        logger.debug("                  fnPrg: %s", forceNotProgressive)
        
        isNew = False
        if not thumbKey in docData["thumbnails"]:
            isNew = True
            docData["thumbnails"][thumbKey] = {"pixmap":None, "valid":False, "users":[], "lastUsed":0, "generator":None, "size":0}
        
        thumb = docData["thumbnails"][thumbKey]
        
        if thumb["valid"]:
            if thumb["pixmap"] and not thumb["generator"]:
                logger.debug("requestThumbnail: existing thumb is valid, returning pixmap %s", thumb["pixmap"])
                return thumb["pixmap"]
            else:
                logger.debug("requestThumbnail: existing thumb is valid but pixmap is blank or still being generated, returning closest valid pixmap.")
                candidatePm = cls.closestValidThumbnailPixmap(docData["thumbnails"], thumbKey)
                if candidatePm:
                    return QPixmap(candidatePm)
                else:
                    return None
        
        oldPm = thumb["pixmap"]
        
        # check if should generate thumb progressively.
        # (checks include if thumb would only require one block, in which case prog' gen' is unnecessary.)
        progressive = (
                ODDSettings.globalSettingValue("thumbUseProjectionMethod")
                and ODDSettings.globalSettingValue("progressiveThumbs")
                and not forceNotProgressive
                and docData["document"].width() * docData["document"].height() > (
                    ODDSettings.globalSettingValue("progressiveThumbsWidth") * ODDSettings.globalSettingValue("progressiveThumbsHeight")
                )
        )
        
        if progressive:
            thumb["generator"] = ODDThumbGenerator(
                docData["document"], thumbKey[0], thumbKey[1],
                finishedCallback = lambda otgPixmap: cls.thumbGeneratorFinished(thumb, thumbKey, otgPixmap)
            )
            thumb["generator"].start()
            if oldPm:
                pm = oldPm
            else:
                # try to find the nearest-size valid pixmap, if there is one, before falling back to blank.
                candidatePm = cls.closestValidThumbnailPixmap(docData["thumbnails"], thumbKey)
                if candidatePm:
                    pm = QPixmap(candidatePm)
                else:
                    pm = None
            thumb["size"] = thumbKey[0] * thumbKey[1] * QPixmap.defaultDepth()
        else:
            img = cls.generateThumbnail(docData["document"], thumbKey[0], thumbKey[1], thumbKey[2], thumbKey[3])
            pm = QPixmap.fromImage(img)
            thumb["size"] =  pm.width() * pm.height() * QPixmap.defaultDepth()
        
        thumb["pixmap"] = pm
        thumb["valid"] = True
        thumb["lastUsed"] = process_time_ns()
        
        cls.evictExcessUnusedCache()
        
        if isNew:
            cls.unusedCacheSize += thumb["size"]
        
        if not progressive:
            cls.updatePixmapInDockers(docData["document"], thumbKey, oldPm, pm)
        return thumb["pixmap"]
    
    @classmethod
    def closestValidThumbnailPixmap(cls, thumbs, thumbKey):
        # ~ logger.debug("find closestValidThumbnail: for thumbKey %s...", thumbKey)
        candidatePm = None
        candidateWidthDiff = 2**32 # really big number.
        candidateIsLarger = False # prefer too-big valid thumbnails to too-small.
        for k,v in thumbs.items():
            if k != thumbKey:
                if v["valid"] and v["pixmap"] and not v["generator"]:
                    wdiff = thumbKey[0]-k[0]
                    if abs(wdiff) < candidateWidthDiff:
                        if wdiff < 0 or not candidateIsLarger:
                            candidatePm = v["pixmap"]
                            candidateWidthDiff = wdiff
                            candidateIsLarger = wdiff < 0
        logger.debug("found (error in width = {} px).".format(candidateWidthDiff) if candidatePm else "not found.")
        return candidatePm
    
    @classmethod
    def updatePixmapInDockers(cls, doc, thumbKey, oldPixmap, newPixmap):
        """tell docker instances to use new pixmap if using old one."""
        logger.debug("updatePixmapInDockers: doc: %s", doc.fileName())
        logger.debug("                       thKey: %s", thumbKey)
        # ~ logger.debug("                       oldPm: %s", oldPixmap)
        # ~ logger.debug("                       newPm: %s", newPixmap)
        if oldPixmap:
            logger.debug("updatePixmapInDockers: oldPixmap exists")
            oldPixmapCacheKey = oldPixmap.cacheKey()
        for docker in cls.dockers:
            if docker.vs.settingValue("display", True) != "thumbnails":
                continue
            for i in range(docker.list.count()):
                item = docker.list.item(i)
                itemDoc = item.data(docker.ItemDocumentRole)
                itemKey = item.data(docker.ItemThumbnailKeyRole)
                if not (itemDoc == doc and itemKey == thumbKey):
                    continue
                logger.debug("updatePixmapInDockers: itemDoc==doc and itemKey==thumbKey")
                if oldPixmap:
                    itemPm = item.data(Qt.DecorationRole)
                    logger.debug("updatePixmapInDockers: itemPm: %s", itemPm)
                    if itemPm:
                        itemPmCacheKey = itemPm.cacheKey()
                        logger.debug("%s %s: compare %s with %s", i, item, itemPmCacheKey, oldPixmapCacheKey)
                        if not itemPmCacheKey == oldPixmapCacheKey:
                            continue
                logger.debug("update docker of %s item %s with updated thumb.", docker.parent().objectName(), item)
                item.setData(Qt.DecorationRole, newPixmap)
    
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
    def thumbGeneratorFinished(cls, thumbData, thumbKey, thumbPixmap):
        oldPm = thumbData["pixmap"]
        logger.debug("thumbGeneratorFinished: %s %s", thumbData["generator"].doc.fileName(), thumbKey)
        thumbPixmap.setDevicePixelRatio(cls.dockers[0].devicePixelRatioF())
        thumbData["pixmap"] = thumbPixmap
        cls.updatePixmapInDockers(thumbData["generator"].doc, thumbKey, oldPm, thumbPixmap)
        thumbData["generator"] = None
    
    @classmethod
    def invalidateThumbnails(cls, docData):
        logger.debug("ODD:invalidateThumbnails")
        if type(docData) == Document:
            if (docData := cls.docDataFromDocument(docData)) is None:
                return
        for thumbData in docData["thumbnails"].values():
            if thumbData["generator"]:
                thumbData["generator"].stop()
                thumbData["generator"] = None
            thumbData["valid"] = False
        
        cls.cleanupUnusedInvalidatedThumbnails(docData)
        
    @classmethod
    def cleanupUnusedInvalidatedThumbnails(cls, docData):
        thumbs = docData["thumbnails"]
        for thumbData in thumbs.values():
            if not thumbData["valid"] and len(thumbData["users"]) == 0:
                pm = thumbData["pixmap"]
                cls.unusedCacheSize -= thumbData["size"]
        [thumbs.pop(t, None) for t in [t[0] for t in thumbs.items() if t[1]["valid"] == False and len(t[1]["users"]) == 0]]
    
    @classmethod
    def addThumbnailUser(cls, who, docData, thumbKey):
        logger.debug("ODD:addThumbnailUser")
        if type(docData) == Document:
            if (docData := cls.docDataFromDocument(docData)) is None:
                return
        thumbData = docData["thumbnails"][thumbKey]
        if not who in thumbData["users"]:
            thumbData["users"].append(who)
            if len(thumbData["users"]) == 1:
                pm = thumbData["pixmap"]
                cls.unusedCacheSize -= thumbData["size"]
    
    @classmethod
    def removeThumbnailUser(cls, who, docData, thumbKey):
        logger.debug("ODD:removeThumbnailUser")
        if type(docData) == Document:
            if (docData := cls.docDataFromDocument(docData)) is None:
                return
        thumbData = docData["thumbnails"][thumbKey]
        if not who in thumbData["users"]:
            return
        thumbData["users"].remove(who)
        if len(thumbData["users"]) == 0:
            if thumbData["generator"]:
                thumbData["generator"].stop()
                thumbData["generator"] = None
            if thumbData["valid"]:
                pm = thumbData["pixmap"]
                cls.unusedCacheSize += thumbData["size"]
                thumbData["lastUsed"] = process_time_ns()
                cls.evictExcessUnusedCache()
            else:
                logger.debug("removed last user of invalidated thumb, deleting thumb.")
                del docData["thumbnails"][thumbKey]
        
    
    @classmethod
    def evictExcessUnusedCache(cls, maxSize=-1):
        if maxSize == -1:
            maxSize = int(ODDSettings.globalSettings["excessThumbCacheLimit"]) * 8192 #1024*8
        if cls.unusedCacheSize-maxSize <= 0:
            return
        
        logger.debug(" - evictExcessUnusedCache - ")
        logger.debug("before: unused cache size: %s, max allowed: %s, excess: %s", cls.unusedCacheSize, maxSize, cls.unusedCacheSize-maxSize)
        evictableThumbs = []
        for d in cls.documents:
            for t in d["thumbnails"].items():
                if len(t[1]["users"]) == 0:
                    evictableThumbs.append((d, t[0], t[1]))
        if len(evictableThumbs) == 0:
            logger.debug(" - nothing to evict - ")
            return
        evictableThumbsSorted = sorted(evictableThumbs, key = lambda e: e[2]["lastUsed"])
        logger.debug("evictable thumbs:")
        i = 1
        for e in evictableThumbsSorted:
            logger.debug("#%s: doc %s, tKey: %s (lu: %s)", i, e[0]["document"], e[1], e[2]["lastUsed"])
            i += 1
        while cls.unusedCacheSize > maxSize:
            e = evictableThumbsSorted[0]
            pm = e[2]["pixmap"]
            size = e[2]["size"]
            logger.debug("evicting: %s %s...", e[0]["document"], e[1])
            del e[0]["thumbnails"][e[1]]
            del evictableThumbsSorted[0]
            cls.unusedCacheSize -= size
            logger.debug("removed %s - excess remaining: %s", size, cls.unusedCacheSize-maxSize)
        logger.debug("result: unused cache size: %s, max allowed: %s, excess: %s", cls.unusedCacheSize, maxSize, cls.unusedCacheSize-maxSize)
        logger.debug(" - evict finished - ")
    
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
        docData = ODD.docDataFromDocument(doc)
        return docData["viewCountPerWindow"][win.qwindow()] > 0
    
    @classmethod
    def windowFromQWindow(cls, qwin):
        if qwin in cls.winForQWin:
            return cls.winForQWin[qwin]
        logger.warning("warning: windowFromQWindow called before window ready.")
        return None
    
    @classmethod
    def findDockerWithWindow(cls, win):
        qwin = win.qwindow()
        for docker in cls.dockers:
            if docker.parent() == qwin:
                return docker
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
        logger.info("window being created: %s (%s)", window, window.qwindow().objectName())
        window.qwindow().installEventFilter(self)
        window.qwindow().destroyed.connect(cls.windowDestroyed)
    
    def windowCreated(self):
        cls = self.__class__
        
        appWins = Application.windows()
        for win in appWins:
            if win in cls.windows:
                logger.debug("existing win: %s", win)
            else:
                logger.debug("new win: %s", win)
                cls.windows.append(win)
                qwin = win.qwindow()
                logger.debug("add winForQWin entry %s -> %s", qwin, win)
                cls.winForQWin[qwin] = win
                dockercls = cls.dockers[0].__class__
                docker = qwin.findChild(dockercls)
                logger.debug("connect window %s activeViewChanged to %s", win, docker)
                win.activeViewChanged.connect(docker.activeViewChanged)
                for docData in cls.documents:
                    if not qwin in docData["lastViewInWindow"]:
                        #logger.debug("{} was missing lastViewInWindow   for {}".format(docData["document"], qwin.objectName()))
                        docData["lastViewInWindow"][qwin] = None
                    if not qwin in docData["viewCountPerWindow"]:
                        #logger.debug("{} was missing viewCountPerWindow for {}".format(docData["document"], qwin.objectName()))
                        docData["viewCountPerWindow"][qwin] = sum(v.document()==docData["document"] for v in win.views())
    
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
        logger.info("window destroyed: %s", obj)
        
        closedWins = []
        appWins = Application.windows()
        for win in cls.windows:
            if win in appWins:
                logger.debug("kept win %s", win)
                pass
            else:
                logger.debug("closed win: %s", win)
                closedWins.append(win)
        for win in closedWins:
            for k,v in cls.winForQWin.items():
                if v == win:
                    qwin = k
            logger.debug("remove winForQWin entry %s -> %s", qwin, win)
            del cls.winForQWin[qwin]
            cls.windows.remove(win)
        
        logger.debug(" - wins - ")
        for i in enumerate(cls.windows):
            logger.debug("%s: %s", i[0], i[1])
        
        # ~ logger.debug("-pre-")
        # ~ for i in range(len(cls.dockers)):
            # ~ logger.debug("docker %s: %s %s", i, cls.dockers[i], cls.dockers[i].parent() if cls.dockers[i] else "")
            
        for i in range(len(cls.dockers)):
            docker = cls.dockers[i]
            if type(docker.parent()) != QMainWindow: #QMainWindow becomes QObject when closed/destroyed
                logger.info("delete ref to docker %s", docker)
                removeUserBuffer = []
                for d in cls.documents:
                    for t in d["thumbnails"].items():
                        if docker in t[1]["users"]:
                            removeUserBuffer.append((d, t[0]))
                for ru in removeUserBuffer:
                    cls.removeThumbnailUser(docker, ru[0], ru[1])
                
                ODDSettings.instances.remove(docker.vs)
                
                cls.dockers[i] = None
                
        # ~ logger.debug("-mid-")
        # ~ for i in range(len(cls.dockers)):
            # ~ logger.debug("docker %s: %s %s", i, cls.dockers[i], cls.dockers[i].parent() if cls.dockers[i] else "")
            
        for i in range(len(cls.dockers)-1, -1, -1):
            if cls.dockers[i] == None:
                #logger.debug("deleting ref to docker %s: %s", i, cls.dockers[i])
                del cls.dockers[i]
        
        for docData in cls.documents:
            for win in closedWins:
                qwin = win.qwindow()
                logger.debug("remove closed qwin %s data from docData of %s", qwin, docData["document"])
                if qwin in docData["lastViewInWindow"]:
                    del docData["lastViewInWindow"][qwin]
                if qwin in docData["viewCountPerWindow"]:
                    del docData["viewCountPerWindow"][qwin]
        
        # ~ logger.debug("-post-")
        # ~ for i in range(len(cls.dockers)):
            # ~ logger.debug("docker %s: %s %s", i, cls.dockers[i], cls.dockers[i].parent() if cls.dockers[i] else "")
    
    def getScreen(self, who):
        if hasattr(who, "screen"):
            return who.screen()
        if who.windowHandle():
            return who.windowHandle().screen()
        if who.parent() and who.parent().windowHandle():
            return who.parent().windowHandle().screen()


from .oddsettings import ODDSettings
from .oddviewprocessor import ODDViewProcessor
from .oddthumbgenerator import ODDThumbGenerator
from .oddimagechangedetector import ODDImageChangeDetector
