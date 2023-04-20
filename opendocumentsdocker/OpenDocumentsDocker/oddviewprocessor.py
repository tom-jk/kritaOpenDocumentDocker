from krita import *
from .odd import ODD

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
        print("ODDViewProcessor: init", self)
        # ~ print(" - preprocessCallbackForMultipleViews", preprocessCallbackForMultipleViews)
        # ~ print(" - preprocessCallback", preprocessCallback)
        # ~ print(" - selectionCondition", selectionCondition)
        # ~ print(" - switchToView", switchToView)
        # ~ print(" - operation", operation)
        # ~ print(" - lastViewPreProcessCallback", lastViewPreProcessCallback)
        # ~ print(" - finishedCallback", finishedCallback)
        
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
        #print("ODDViewProcessor: deleting instance", self)
        pass
    
    def start(self):
        print("ODDViewProcessor: start", self)
        self.stepTimer.start()

    def step(self):
        try:
            #print("ODDViewProcessor: step")
            next(self.processor)
            #print("ODDViewProcessor: start timer for next step")
            self.stepTimer.start()
        except StopIteration:
            self.processor = None
            print("ODDViewProcessor: finished")
            if self.finishedCallback:
                self.finishedCallback()
        
    def process(self):
        print("ODDViewProcessor: begin processor")
        
        viewCount = 0
        for v in ODD.views:
            if self.selectionCondition(v):
                viewCount += 1
                if viewCount > 1:
                    break
        
        if viewCount > 1:
            if self.preprocessCallbackForMultipleViews:
                print("ODDViewProcessor: preprocessCallbackForMultipleViews")
                if not self.preprocessCallbackForMultipleViews():
                    print("ODDViewProcessor: processor cancelled.")
                    return
        
        if self.preprocessCallback:
            print("ODDViewProcessor: preprocessCallback")
            if not self.preprocessCallback():
                print("ODDViewProcessor: processor cancelled.")
        
        print("ODDViewProcessor: begin process.")
        
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
                    print("ODDViewProcessor: lastViewPreProcessCallback")
                    forceNoMoreLoops = (self.lastViewPreProcessCallback() == True)
            elif viewCount == 0:
                print("ODDViewProcessor: no more views to process.")
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
            print("ODDViewProcessor: processing view {} ({} after this)".format(str(view)[-15:-1], viewCount-1))
            doc.waitForDone()
            self.operation()
            print("ODDViewProcessor: processed view")
            doc.waitForDone()
            yield
