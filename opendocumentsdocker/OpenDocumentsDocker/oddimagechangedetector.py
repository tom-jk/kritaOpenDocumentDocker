# SPDX-License-Identifier: GPL-3.0-or-later

from PyQt5.QtCore import QTimer, QSize
from krita import *
from .odd import ODD
from time import *

import logging
logger = logging.getLogger("odd")


class ODDImageChangeDetector(QObject):
    StopReasonUser = 1
    StopReasonBlur = 2
    StopReasonCooldown = 4
    StopReasonNoDoc = 8
    StopReasonNoChanges = 16
    checkTimer = None
    refreshCheckTimer = None
    refreshDelay = 0
    cooldownTimer = None
    stopReasons = StopReasonBlur
    instance = None
    changedDocs = []
    changedDoc = None
    pendingCount = 0
    
    def __init__(self):
        logger.debug("ODDImageChangeDetector:__init__")
        super(ODDImageChangeDetector, self).__init__()
        cls = self.__class__
        cls.instance = self
        
        cls.checkTimer = QTimer(self)
        setting = ODDSettings.readSettingFromConfig("refreshPeriodicallyChecks")
        checkInterval = ODDSettings.SD["refreshPeriodicallyChecks"]["values"][convertSettingStringToValue("refreshPeriodicallyChecks", setting)]
        cls.checkTimer.setInterval(checkInterval)
        cls.checkTimer.timeout.connect(cls.checkTimerTimeout)
        
        setting = ODDSettings.readSettingFromConfig("refreshPeriodicallyDelay")
        cls.refreshDelay = ODDSettings.SD["refreshPeriodicallyDelay"]["values"][convertSettingStringToValue("refreshPeriodicallyDelay", setting)]
        
        cls.refreshCheckTimer = QTimer(self)
        cls.refreshCheckTimer.setInterval(125)
        cls.refreshCheckTimer.timeout.connect(cls.refreshCheckTimerTimeout)
        
        cls.cooldownTimer = QTimer(self)
        cls.cooldownTimer.setInterval(1000)
        cls.cooldownTimer.setSingleShot(True)
        cls.cooldownTimer.timeout.connect(cls.cooldownTimerTimeout)
        
        if not ODDSettings.readSettingFromConfig("refreshPeriodically") == "true":
            cls.stopReasons |= cls.StopReasonUser
    
    @classmethod
    def addStopper(cls, stopReason):
        if stopReason not in [cls.StopReasonUser, cls.StopReasonBlur, cls.StopReasonCooldown, cls.StopReasonNoDoc, cls.StopReasonNoChanges]:
            return
        
        cls.stopReasons |= stopReason
        
        if cls.refreshCheckTimer.isActive():
            if stopReason & (cls.StopReasonUser | cls.StopReasonBlur | cls.StopReasonNoChanges):
                logger.info("ODDImageChangeDetector: stopping refreshCheckTimer. (reason=%s)", stopReason)
                cls.refreshCheckTimer.stop()
        
        if cls.checkTimer.isActive():
            if stopReason & (cls.StopReasonUser | cls.StopReasonBlur | cls.StopReasonCooldown | cls.StopReasonNoDoc):
                logger.info("ODDImageChangeDetector: stopping checkTimer. (reason=%s)", stopReason)
                cls.checkTimer.stop()
    
    @classmethod
    def removeStopper(cls, stopReason):
        if stopReason not in [cls.StopReasonUser, cls.StopReasonBlur, cls.StopReasonCooldown, cls.StopReasonNoDoc, cls.StopReasonNoChanges]:
            return
        if not cls.stopReasons:
            return
        
        cls.stopReasons &= ~stopReason
        
        if not cls.checkTimer.isActive():
            if not (cls.stopReasons & (cls.StopReasonUser | cls.StopReasonBlur | cls.StopReasonCooldown | cls.StopReasonNoDoc)):
                logger.info("ODDImageChangeDetector: restarting checkTimer.")
                cls.checkTimer.start()
        
        if not cls.refreshCheckTimer.isActive():
            if not (cls.stopReasons & (cls.StopReasonUser | cls.StopReasonBlur | cls.StopReasonNoChanges)):
                logger.info("ODDImageChangeDetector: restarting refreshCheckTimer.")
                cls.refreshCheckTimer.start()
    
    @classmethod
    def startCooldown(cls):
        logger.info("ODDImageChangeDetector: cooldown starting...")
        cls.cooldownTimer.start()
        cls.addStopper(cls.StopReasonCooldown)
    
    @classmethod
    def cooldownTimerTimeout(cls):
        logger.info("ODDImageChangeDetector: ...cooldown finished.")
        cls.removeStopper(cls.StopReasonCooldown)
    
    @classmethod
    def activeDocumentChanged(cls):
        doc = ODD.activeDocument
        
        if not cls.changedDoc or doc != cls.changedDoc["docData"]["document"]:
            if cls.changedDoc:
                if not cls.changedDoc["hasChanged"]:
                    # remove inactive and unchanged doc.
                    del cls.changedDocs[cls.changedDocs.index(cls.changedDoc)]
            if doc:
                cdWasNone = not cls.changedDoc
                found = False
                logger.debug("checking if doc in changedDocs")
                for cd in cls.changedDocs:
                    if cd["docData"]["document"] == doc:
                        cls.changedDoc = cd
                        found = True
                        break
                if not found:
                    cls.changedDocs.append({
                        "docData":      ODD.docDataFromDocument(doc),
                        "size":         QSize(doc.width(), doc.height()),
                        "busyLastCheck":False,
                        "hasChanged":   False,
                        "changeTime":   0,
                        "refreshDelay": 0,
                    })
                    cls.changedDoc = cls.changedDocs[-1]
                if cdWasNone:
                    cls.removeStopper(cls.StopReasonNoDoc)
            else:
                cls.changedDoc = None
                cls.addStopper(cls.StopReasonNoDoc)
    
    @classmethod
    def checkTimerTimeout(cls):
        #logger.debug("checkTimerTimeout")
        doc = ODD.activeDocument
        
        if doc:
            if doc.tryBarrierLock():
                # doc was not busy.
                doc.unlock()
                if cls.changedDoc["busyLastCheck"]:
                    # doc has just finished being busy.
                    # invalidate thumbs again at end (less costly than
                    # invalidating constantly while busy). ditto time.
                    cls.changedDoc["changeTime"] = process_time_ns()
                    ODD.invalidateThumbnails(doc)
                cls.changedDoc["busyLastCheck"] = False
            else:
                if not any(dd["document"] == doc for dd in ODD.documents):
                    # couldn't acquire lock for a document that was closed.
                    logger.error("tried to acquire lock for a document that was closed. this shouldn't happen.")
                    return 
                # doc was busy.
                if cls.changedDoc["hasChanged"]:
                    # doc already known to be changed.
                    pass
                else:
                    # doc has newly become busy, a change has begun.
                    logger.debug("ODDImageChangeDetector: detected change in %s", cls.changedDoc["docData"]["document"].fileName())
                    cls.changedDoc["hasChanged"] = True
                    cls.changedDoc["changeTime"] = process_time_ns()
                    if cls.pendingCount == 0:
                        cls.pendingCount = 1
                        cls.removeStopper(cls.StopReasonNoChanges)
                    ODD.invalidateThumbnails(doc)
                
                # reset refresh delay so long as doc being changed.
                cls.changedDoc["refreshDelay"] = cls.refreshDelay
                
                cls.changedDoc["busyLastCheck"] = True
    
    @classmethod
    def refreshCheckTimerTimeout(cls):
        pendingCount = 0
        for cd in cls.changedDocs:
            if cd["refreshDelay"] > 0:
                cd["refreshDelay"] -= cls.refreshCheckTimer.interval()
                if cd["refreshDelay"] <= 0:
                    cdDoc = cd["docData"]["document"]
                    if not cdDoc.tryBarrierLock():
                        # go around.
                        cd["refreshDelay"] = cls.refreshDelay
                        pendingCount += 1
                        continue
                    cdDoc.unlock()
                    cd["refreshDelay"] = 0
                    cd["hasChanged"] = False
                    # let everyone who needs to know, know it's time to refresh.
                    logger.debug("ODDImageChangeDetector: time to refresh %s", cdDoc.fileName())
                    for docker in ODD.dockers:
                        docker.updateDocumentThumbnail(cdDoc, ignoreThumbsMoreRecentThan=cd["changeTime"])
                else:
                    pendingCount += 1
        
        i = 0
        while i < len(cls.changedDocs):
            cd = cls.changedDocs[i]
            if not (cd == cls.changedDoc or cd["hasChanged"]):
                del cls.changedDocs[i]
            else:
                i += 1
        
        cls.pendingCount = pendingCount
        if cls.pendingCount == 0:
            cls.addStopper(cls.StopReasonNoChanges)


from .odddocker import ODDDocker
from .oddsettings import ODDSettings, convertSettingStringToValue
