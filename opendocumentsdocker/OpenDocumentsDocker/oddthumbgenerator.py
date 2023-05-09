# SPDX-License-Identifier: GPL-3.0-or-later

from math import ceil
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import QPoint, QPointF, QSize, QRectF
from krita import *
from .odd import ODD
from .oddsettings import ODDSettings

import logging
logger = logging.getLogger("odd")


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
        logger.debug("ODDThumbGenerator: init %s", self)
        logger.debug(" - doc %s %s", doc, doc.fileName())
        logger.debug(" - thumb size %sx%s",  thumbWidth, thumbHeight)
        logger.debug(" - finishedCallback %s", finishedCallback)
        
        if not (blockWidth and blockHeight):
            blockWidth = ODDSettings.globalSettingValue("progressiveThumbsWidth")
            blockHeight = ODDSettings.globalSettingValue("progressiveThumbsHeight")
        
        docWidth = doc.width()
        docHeight = doc.height()
        isDocTall = docWidth <= blockWidth // 2
        isDocWide = docHeight <= blockHeight // 2
        if isDocTall ^ isDocWide:
            # ~ logger.debug(" - block size: {}x{}".format(blockWidth, blockHeight))
            if isDocTall:
                while docWidth <= blockWidth // 2 and blockWidth > 2:
                    blockWidth = blockWidth // 2
                    blockHeight = blockHeight * 2
                    # ~ logger.debug(" -> {}x{}".format(blockWidth, blockHeight))
            else:
                while docHeight <= blockHeight // 2 and blockHeight > 2:
                    blockHeight = blockHeight // 2
                    blockWidth = blockWidth * 2
                    # ~ logger.debug(" -> {}x{}".format(blockWidth, blockHeight))
        else:
            logger.debug(" - block size %sx%s",  blockWidth, blockHeight)
        
        if not interval:
            interval = ODDSettings.globalSettingValue("progressiveThumbsSpeed")
            
        logger.debug(" - interval %s ms",  interval)
        
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
        #logger.debug("ODDThumbGenerator: deleting instance %s", self)
        pass
    
    def progress(self):
        return self.progressPixelCount / self.docPixelCount
    
    def start(self):
        logger.debug("ODDThumbGenerator: start %s", self)
        
        # make blank image for thumbnail
        self.thumb = QImage(self.thumbWidth, self.thumbHeight, QImage.Format_ARGB32_Premultiplied)
        self.thumb.fill(Qt.transparent)
        
        self.stepTimer.start()
    
    def stop(self):
        logger.debug("ODDThumbGenerator: stop %s", self.doc.fileName() if type(self.doc)==Document else "(no doc)")
        self.processor.close()
    
    def step(self):
        try:
            #logger.debug("ODDThumbGenerator: step")
            next(self.processor)
            #logger.debug("ODDThumbGenerator: start timer for next step")
            self.stepTimer.start()
        except StopIteration:
            self.processor = None
            logger.debug("ODDThumbGenerator: finished %s", self.doc.fileName() if type(self.doc)==Document else "(no doc)")
            if self.finishedCallback:
                self.finishedCallback(QPixmap.fromImage(self.thumb))
        
    def process(self):
        logger.debug("ODDThumbGenerator: begin process.")
        
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
                logger.debug("ODDThumbGenerator: processing block {},{} {}".format(posInDoc.x(), posInDoc.y(), "..." if loopCount==3 else ""))
            
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
                    #logger.debug("Done")
                    return
            
            #logger.debug("ODDThumbGenerator: processed block")
            yield
