from math import ceil
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import QPoint, QPointF, QSize, QRectF
from krita import *
from .odd import ODD
from .oddsettings import ODDSettings


def mapValue(fromMin, fromMax, toMin, toMax, value):
    fromRange = fromMax - fromMin
    normValue = 1.0 / fromRange * (value - fromMin)
    toRange = toMax - toMin
    return toMin + toRange * normValue


class ODDThumbGenerator(QObject):
    def __init__(
            self,
            doc,
            thumbWidth,
            thumbHeight,
            finishedCallback,
            blockWidth = None,
            blockHeight = None,
            interval = None,
    ):
        super(ODDThumbGenerator, self).__init__()
        print("ODDThumbGenerator: init", self)
        print(" - doc", doc, doc.fileName())
        print(" - thumb size",  thumbWidth, "x", thumbHeight)
        print(" - finishedCallback", finishedCallback)
        
        if not (blockWidth and blockHeight):
            blockWidth = ODDSettings.globalSettingValue("progressiveThumbsWidth")
            blockHeight = ODDSettings.globalSettingValue("progressiveThumbsHeight")
        
        docWidth = doc.width()
        docHeight = doc.height()
        isDocTall = docWidth <= blockWidth // 2
        isDocWide = docHeight <= blockHeight // 2
        if isDocTall ^ isDocWide:
            print(" - block size: ", end="")
            print("{}x{}".format(blockWidth, blockHeight), end="")
            if isDocTall:
                while docWidth <= blockWidth // 2 and blockWidth > 2:
                    blockWidth = blockWidth // 2
                    blockHeight = blockHeight * 2
                    print(" -> {}x{}".format(blockWidth, blockHeight), end="")
            else:
                while docHeight <= blockHeight // 2 and blockHeight > 2:
                    blockHeight = blockHeight // 2
                    blockWidth = blockWidth * 2
                    print(" -> {}x{}".format(blockWidth, blockHeight), end="")
            print()
        else:
            print(" - block size",  blockWidth, "x", blockHeight)
        
        if not interval:
            interval = ODDSettings.globalSettingValue("progressiveThumbsSpeed")
            
        print(" - interval",  interval, "ms")
        
        self.doc = doc
        self.thumbWidth = thumbWidth
        self.thumbHeight = thumbHeight
        self.blockWidth = blockWidth
        self.blockHeight = blockHeight
        self.finishedCallback = finishedCallback
        
        self.thumb = None
        
        self.stepTimer = QTimer(self)
        self.stepTimer.setInterval(interval)
        self.stepTimer.setSingleShot(True)
        self.stepTimer.timeout.connect(self.step)
        
        self.docPixelCount = doc.width() * doc.height()
        self.progressPixelCount = 0
        
        self.processor = self.process()
    
    def __del__(self):
        #print("ODDThumbGenerator: deleting instance", self)
        pass
    
    def progress(self):
        return self.progressPixelCount / self.docPixelCount
    
    def start(self):
        print("ODDThumbGenerator: start", self)
        
        # make blank image for thumbnail
        self.thumb = QImage(self.thumbWidth, self.thumbHeight, QImage.Format_RGB32)
        
        self.stepTimer.start()
    
    def stop(self):
        print("ODDThumbGenerator: stop", self.doc.fileName() if type(self.doc)==Document else "(no doc)")
        self.processor.close()
    
    def step(self):
        try:
            #print("ODDThumbGenerator: step")
            next(self.processor)
            #print("ODDThumbGenerator: start timer for next step")
            self.stepTimer.start()
        except StopIteration:
            self.processor = None
            print("ODDThumbGenerator: finished", self.doc.fileName() if type(self.doc)==Document else "(no doc)")
            if self.finishedCallback:
                self.finishedCallback(QPixmap.fromImage(self.thumb))
        
    def process(self):
        print("ODDThumbGenerator: begin process.")
        
        doc = self.doc
        docWidth = doc.width()
        docHeight = doc.height()
        
        posInDoc = QPoint(0, 0)
        posInThumb = QPointF(0, 0)
        blockWidth = self.blockWidth
        blockHeight = self.blockHeight
        blockWidthInThumb  = mapValue(0, docWidth,  0, self.thumbWidth,  blockWidth )
        blockHeightInThumb = mapValue(0, docHeight, 0, self.thumbHeight, blockHeight)
        
        loopCount = 0
        while loopCount < 10000:
            loopCount += 1
            
            if loopCount <= 3:
                print("ODDThumbGenerator: processing block {},{} {}".format(posInDoc.x(), posInDoc.y(), "..." if loopCount==3 else ""))
            
            # grab some of the doc image.
            block = doc.projection(
                posInDoc.x(),
                posInDoc.y(),
                min(blockWidth, docWidth - posInDoc.x()),
                min(blockHeight, docHeight - posInDoc.y())
            )
            
            self.progressPixelCount += block.width() * block.height()
            
            # scale to size in thumb.
            img = block.scaled(
                QSize(
                    ceil(min(blockWidthInThumb, self.thumbWidth - posInThumb.x())),
                    ceil(min(blockHeightInThumb, self.thumbHeight - posInThumb.y()))
                ),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            
            # copy into thumb.
            qp = QPainter(self.thumb)
            qp.setRenderHint(QPainter.SmoothPixmapTransform)
            qp.setRenderHint(QPainter.Antialiasing)
            qp.drawImage(
                QPointF(
                    posInThumb.x(),
                    posInThumb.y()
                ),
                img
            )
            qp.end()
            
            # advance position.
            posInDoc.setX(posInDoc.x() + blockWidth)
            posInThumb.setX(posInThumb.x() + blockWidthInThumb)
            if posInDoc.x() >= docWidth:
                posInDoc.setX(0)
                posInThumb.setX(0)
                posInDoc.setY(posInDoc.y() + blockHeight)
                posInThumb.setY(posInThumb.y() + blockHeightInThumb)
                if posInDoc.y() >= docHeight:
                    #print("Done")
                    return
            
            #print("ODDThumbGenerator: processed block")
            yield
