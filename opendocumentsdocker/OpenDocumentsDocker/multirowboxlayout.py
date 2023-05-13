# SPDX-License-Identifier: GPL-3.0-or-later

from PyQt5.QtCore import QRect, QRectF, QSize
from PyQt5.QtWidgets import QBoxLayout

# layout as normal, allow widgets to expand as desired
# but if all widgets reach their minimum desired size, break at allowed breakpoint.

class MultiRowBoxLayout(QBoxLayout):
    def __init__(self, direction):
        super(MultiRowBoxLayout, self).__init__(direction)
        #print("MultiRowBoxLayout:", self)
        self.breakPoints = {}
        self.itemsHeight = 0
    
    def setBreakPoint(self, i, condition="lessThanMin"):
        self.breakPoints[i] = condition
        self.breakPoints = dict(sorted(self.breakPoints.items()))
    
    def removeBreakPoint(self, i):
        if i not in self.breakPoints:
            return
        del self.breakPoints[i]
    
    def setGeometry(self, r):
        wgt = self.parent()
        wgtGeo = wgt.geometry()
        isHorizontal = self.direction() in [QBoxLayout.LeftToRight, QBoxLayout.RightToLeft]
        #print("setGeometry (length={})".format(wgtGeo.width() if isHorizontal else wgtGeo.height()))
        pos = 0
        lines = []
        lines.append([])
        bpi = 0
        bpIndices = list(self.breakPoints.keys())
        bpConditions = list(self.breakPoints.values())
        bp = bpIndices[bpi] if len(bpIndices) > 0 else -1
        bcon = bpConditions[bpi] if len(bpConditions) > 0 else ""
        lastbp = 0
        #print("itemMinWidth=", self.itemAt(0).widget().minimumWidth())
        
        # break layout down into lines of items.
        # from start, add items to line until no more fit, then start a new line.
        # breakpoints are custom positions to break at. if going to break line
        # somewhere between breakpoints, go back to last breakpoint and push all
        # items after it to next line, too.
        for i in range(self.count()):
            item = self.itemAt(i)
            iWidget = item.widget()
            if not iWidget.isVisible():
                minWidth = minHeight = 0
            else:
                minSizeHint = iWidget.minimumSizeHint()
                minWidth = iWidget.minimumWidth() or min(minSizeHint.width(), minSizeHint.height())
                minHeight = iWidget.minimumHeight() or min(minSizeHint.width(), minSizeHint.height())
            item.setGeometry(QRect(0, 0, minWidth, minHeight))
            itemGeo = item.geometry()
            if not iWidget.isVisible():
                w = 0
            else:
                if bcon=="lessThanDefault":
                    w = iWidget.sizeHint().width() if isHorizontal else iWidget.sizeHint().height()
                else:
                    w = iWidget.minimumWidth() if isHorizontal else iWidget.minimumHeight()
            if pos + w >= (wgtGeo.width() if isHorizontal else wgtGeo.height()) and len(lines[-1])>1:
                lines.append([])
                pos = 0
                if bp != -1:
                    newbpi = bpIndices.index(bp)
                    if i < bp:
                        bp = i
                    else:
                        newbpi += 1
                    if bp < i:
                        for j in range(bp-lastbp, i-lastbp):
                            mitem = lines[-2].pop(bp-lastbp)
                            lines[-1].append(mitem)
                            if not mitem.widget().isVisible():
                                pos += 0
                            else:
                                pos += mitem.widget().minimumWidth() if isHorizontal else mitem.widget().minimumHeight()
                    lastbp = bp
                    if newbpi < len(bpIndices):
                        bpi = newbpi
                        bp = bpIndices[bpi]
                        bcon = bpConditions[bpi]
                    else:
                        bp = -1
            lines[-1].append(item)
            pos += w
        if len(lines[-1]) == 0:
            del lines[-1]
        
        # expand items to fill their line.
        y = 0
        for line in lines:
            pos = 0
            lineHeight = 0
            availableSpace = wgtGeo.width() if isHorizontal else wgtGeo.height()
            growables = []
            itemsTotalWidth = 0
            for item in line:
                iWidget = item.widget()
                if not iWidget.isVisible():
                    continue
                growables.append({
                        "item":item,
                        "length":iWidget.minimumWidth() if isHorizontal else iWidget.minimumHeight(),
                        "maxlength":iWidget.maximumWidth() if isHorizontal else iWidget.maximumHeight()
                })
                itemsTotalWidth += iWidget.minimumWidth() if isHorizontal else iWidget.minimumHeight()
            growables = sorted(growables, key = lambda d: d["maxlength"]-d["length"])
            roomToGrow = availableSpace - itemsTotalWidth
            while roomToGrow >= 1:
                # get ungrowables in reverse order (so can delete safely).
                for ungrowable in filter(lambda d: d[1]["maxlength"]-d[1]["length"] == 0, reversed(list(enumerate(growables)))):
                    if isHorizontal:
                        ungrowable[1]["item"].fGeometry = QRectF(0, 0, ungrowable[1]["length"], ungrowable[1]["item"].geometry().height())
                    else:
                        ungrowable[1]["item"].fGeometry = QRectF(0, 0, ungrowable[1]["item"].geometry().width(), ungrowable[1]["length"])
                    del growables[ungrowable[0]]
                if len(growables) == 0:
                    break
                growAmount = min((growables[0]["maxlength"]-growables[0]["length"]), roomToGrow / len(growables))
                for growable in growables:
                    growable["length"] += growAmount
                    roomToGrow -= growAmount
            # clean up remaining growables.
            for growable in growables:
                if isHorizontal:
                    growable["item"].fGeometry = QRectF(0, 0, growable["length"], growable["item"].geometry().height())
                else:
                    growable["item"].fGeometry = QRectF(0, 0, growable["item"].geometry().width(), growable["length"])
            # finally, position and size line items.
            for item in line:
                if not item.widget().isVisible():
                    continue
                itemGeo = item.fGeometry
                w = itemGeo.width() if isHorizontal else itemGeo.height()
                if isHorizontal:
                    item.setGeometry(QRectF(pos, y, w, itemGeo.height()).toRect())
                else:
                    item.setGeometry(QRectF(y, pos, itemGeo.width(), w).toRect())
                pos += w
                lineHeight = max(lineHeight, itemGeo.height() if isHorizontal else itemGeo.width())
            y += lineHeight
        
        y = int(y)
        if not wgt.parent():
            # (not tested) size widget directly if top-level.
            if isHorizontal:
                wgt.setGeometry(QRect(wgtGeo.x(), wgtGeo.y(), wgtGeo.width(), max(y,24)))
            else:
                wgt.setGeometry(QRect(wgtGeo.x(), wgtGeo.y(), max(y,24), wgtGeo.height()))
        if y != self.itemsHeight:
            self.itemsHeight = y
            self.invalidate()
    
    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        isHorizontal = self.direction() in [QBoxLayout.LeftToRight, QBoxLayout.RightToLeft]
        return QSize(
                self.itemsHeight if not isHorizontal else 0,
                self.itemsHeight if isHorizontal else 0
        )
