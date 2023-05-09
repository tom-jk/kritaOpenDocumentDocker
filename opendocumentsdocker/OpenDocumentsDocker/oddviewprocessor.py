# SPDX-License-Identifier: GPL-3.0-or-later

from krita import *
from .odd import ODD

import logging
logger = logging.getLogger("odd")


class ODDViewProcessor(QObject):
    def __init__(
            self,
            operation,
            selectionCondition,
            finishedCallback,
            switchToView=True,
            preprocessCallbackForMultipleViews=None,
            preprocessCallback=None,
            lastViewPreProcessCallback=None
    ):
        super(ODDViewProcessor, self).__init__()
        logger.debug("ODDViewProcessor: init %s", self)
        # ~ logger.debug(" - preprocessCallbackForMultipleViews %s", preprocessCallbackForMultipleViews)
        # ~ logger.debug(" - preprocessCallback %s", preprocessCallback)
        # ~ logger.debug(" - selectionCondition %s", selectionCondition)
        # ~ logger.debug(" - switchToView %s", switchToView)
        # ~ logger.debug(" - operation %s", operation)
        # ~ logger.debug(" - lastViewPreProcessCallback %s", lastViewPreProcessCallback)
        # ~ logger.debug(" - finishedCallback %s", finishedCallback)
        
        self.preprocessCallbackForMultipleViews = preprocessCallbackForMultipleViews
        self.preprocessCallback = preprocessCallback
        self.selectionCondition = selectionCondition
        self.switchToView = switchToView
        self.operation = operation
        self.lastViewPreProcessCallback = lastViewPreProcessCallback
        self.finishedCallback = finishedCallback
        
        self.stepTimer = QTimer(self)
        self.stepTimer.setInterval(0)
        self.stepTimer.setSingleShot(True)
        self.stepTimer.timeout.connect(self.step)
        
        self.processor = self.process()
    
    def __del__(self):
        #logger.debug("ODDViewProcessor: deleting instance %s", self)
        pass
    
    def start(self):
        logger.debug("ODDViewProcessor: start %s", self)
        self.stepTimer.start()

    def step(self):
        try:
            #logger.debug("ODDViewProcessor: step")
            next(self.processor)
            #logger.debug("ODDViewProcessor: start timer for next step")
            self.stepTimer.start()
        except StopIteration:
            self.processor = None
            logger.debug("ODDViewProcessor: finished")
            if self.finishedCallback:
                self.finishedCallback()
        
    def process(self):
        logger.debug("ODDViewProcessor: begin processor")
        
        viewCount = 0
        for v in ODD.views:
            if self.selectionCondition(v):
                viewCount += 1
                if viewCount > 1:
                    break
        
        if viewCount > 1:
            if self.preprocessCallbackForMultipleViews:
                logger.debug("ODDViewProcessor: preprocessCallbackForMultipleViews")
                if not self.preprocessCallbackForMultipleViews():
                    logger.debug("ODDViewProcessor: processor cancelled.")
                    return
        
        if self.preprocessCallback:
            logger.debug("ODDViewProcessor: preprocessCallback")
            if not self.preprocessCallback():
                logger.debug("ODDViewProcessor: processor cancelled.")
                return
        
        logger.debug("ODDViewProcessor: begin process.")
        
        loopCount = 0
        forceNoMoreLoops = False
        while loopCount < 100 and not forceNoMoreLoops:
            loopCount += 1
            
            # TODO: ok to use self.odd.views? (ie. will it be up to date?)
            #       or, is routine stable enough now to get list of
            #       candidate views just once at start?
            viewCount = 0
            views = Application.views()
            view = None
            for v in views:
                if self.selectionCondition(v):
                    if not view:
                        view = v
                    viewCount += 1
            
            if viewCount == 1:
                if self.lastViewPreProcessCallback:
                    logger.debug("ODDViewProcessor: lastViewPreProcessCallback")
                    forceNoMoreLoops = (self.lastViewPreProcessCallback() == True)
            elif viewCount == 0:
                logger.debug("ODDViewProcessor: no more views to process (viewCount == endAtViewCount).")
                return
            
            doc = view.document()
            
            if self.switchToView:
                view.window().activate()
                yield
                view.window().showView(view)
                yield
                view.setVisible()
            
            yield
            
            assert Application.activeWindow().activeView().document() == self.targetDoc if hasattr(self, "targetDoc") else True, \
                    "ODDListWidget:_tryToCloseDocument: sanity check (view doc == doc to close) failed."
            logger.debug("ODDViewProcessor: processing view {} ({} after this)".format(str(view)[-15:-1], viewCount-1))
            doc.waitForDone()
            self.operation()
            logger.debug("ODDViewProcessor: processed view")
            doc.waitForDone()
            yield
