# SPDX-License-Identifier: CC0-1.0

from PyQt5.QtCore import Qt, QByteArray, QBuffer, QPoint, QSize
from PyQt5.QtGui import QPixmap, QScreen, QContextMenuEvent
from PyQt5.QtWidgets import QWidget, QBoxLayout, QVBoxLayout, QHBoxLayout, QListView, QPushButton, QMenu, QAbstractItemView, QListWidget, QListWidgetItem, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QSizePolicy
from krita import *
from time import *
from pathlib import Path


class OpenDocumentsDocker(krita.DockWidget):
    
    viewThumbnailsScaleSliderStrings = ["1/16", "1/8", "1/4", "1/2", "1"]
    viewThumbnailsScaleSliderValues = [1.0/16.0, 1.0/8.0, 1.0/4.0, 1.0/2.0, 1]
    viewThumbnailsTooltipsSliderStrings = ["never","≤128px²","≤256px²","≤512px²","≤1024px²","≤2048px²","≤4096px²","≤8192px²","≤16384px²","always"]
    viewThumbnailsTooltipsSliderValues = [0, 128*128, 256*256, 512*512, 1024*1024, 2048*2048, 4096*4096, 8192*8192, 16384*16384, float("inf")]
    viewThumbnailsRefreshPeriodicallyChecksStrings = ["1/sec","2/sec","3/sec","4/sec","5/sec","8/sec","10/sec","15/sec","20/sec","30/sec"]
    viewThumbnailsRefreshPeriodicallyChecksValues = [1000, 500, 333, 250, 200, 125, 100, 67, 50, 33]
    viewThumbnailsRefreshPeriodicallyDelayStrings = ["1/2sec", "1sec", "1.5sec", "2sec", "3sec", "4sec", "5sec", "7sec", "10sec", "20sec", "1min"]
    viewThumbnailsRefreshPeriodicallyDelayValues = [500, 1000, 1500, 2000, 3000, 4000, 5000, 7000, 10000, 20000, 60000]
    ItemDocumentRole = Qt.UserRole
    ItemUpdateDeferredRole = Qt.UserRole+1
    
    # https://krita-artists.org/t/scripting-open-an-existing-file/32124/4
    def find_and_activate_view(self, doc):
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
        app = Application
        #print("a", doc, self.documentUniqueId(doc))
        #print("b", exception)
        for win in app.windows():
            #print("c", win)
            for view in win.views():
                #print("d", view, view.visible())
                if view != exception:
                    #print("e", view.document(), self.documentUniqueId(view.document()))
                    if self.documentUniqueId(view.document()) == self.documentUniqueId(doc):
                        #print("f")
                        return True
        return False
    
    def activated(self, index):
        self.clicked(index)
    
    def clicked(self, index):
        #print("clicked index: col", index.column(), ", row", index.row(), ", data", index.data())
        #print(self.listModel.openDocuments[index.row()])
        item = self.listView.item(index.row())
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if doc:
            self.find_and_activate_view(doc)
        else:
            print("ODD: clicked an item that has no doc, or points to a doc that doesn't exist!")
    
    def documentDisplayName(self, doc):
        fPath = doc.fileName()
        fName = Path(fPath).name
        tModi = " *" * doc.modified()
        return (fName if fName else "[not saved]") + tModi
    
    def entered(self, index):
        #print("entered index: col", index.column(), ", row", index.row(), ", data", index.data())      
        
        item = self.listView.item(index.row())
        
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if not doc:
            return
        
        fPath = doc.fileName()
        ttText = ""
        
        ttText += "<table border='0' style='margin:16px; padding:16px'><tr>"
        
        # From answer to "Use a picture or image in a QToolTip": https://stackoverflow.com/a/34300771
        if doc.width() * doc.height() <= self.viewThumbnailsTooltipsSliderValues[self.viewPanelThumbnailsTooltipsSlider.value()]:
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
        
        listTopLeft = self.listView.mapToGlobal(self.listView.frameGeometry().topLeft())
        listBottomRight = self.listView.mapToGlobal(self.listView.frameGeometry().bottomRight())
        listTopRight = self.listView.mapToGlobal(self.listView.frameGeometry().topRight())
        listCenter = (listTopLeft+listBottomRight)/2
        itemRect = self.listView.visualRect(index)
        
        if hasattr(self, "screen"):
            # work out which side of the widget has the most space and put the tooltip there.
            screen = self.screen()            
            screenTopLeft = screen.availableGeometry().topLeft()
            screenBottomRight = screen.availableGeometry().bottomRight()
            screenCenter = (screenTopLeft+screenBottomRight)/2
            if self.listView.flow() == QListView.TopToBottom:
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
            if self.listView.flow() == QListView.TopToBottom:
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
    
    def setViewDisplayToThumbnails(self):
        print("setViewDisplayToThumbnails")
        Application.writeSetting("OpenDocumentsDocker", "viewDisplay", "thumbnails")
        self.refreshOpenDocuments()
        self.updateScrollBarPolicy()
        if self.itemTextUpdateTimer.isActive():
            self.itemTextUpdateTimer.stop()

    def setViewDisplayToText(self):
        print("setViewDisplayToText")
        Application.writeSetting("OpenDocumentsDocker", "viewDisplay", "text")
        self.refreshOpenDocuments()
        self.updateScrollBarPolicy()
        if not self.itemTextUpdateTimer.isActive():
            self.itemTextUpdateTimer.start()

    def setViewDirectionToHorizontal(self):
        print("setViewDirectionToHorizontal")
        Application.writeSetting("OpenDocumentsDocker", "viewDirection", "horizontal")
        #self.listView.setFlow(QListView.LeftToRight)
        self.setDockerDirection("horizontal")

    def setViewDirectionToVertical(self):
        print("setViewDirectionToVertical")
        Application.writeSetting("OpenDocumentsDocker", "viewDirection", "vertical")
        #self.listView.setFlow(QListView.TopToBottom)
        self.setDockerDirection("vertical")

    def setViewDirectionToAuto(self):
        print("setViewDirectionToAuto")
        Application.writeSetting("OpenDocumentsDocker", "viewDirection", "auto")
        self.setDockerDirection("auto")
    
    def convertViewThumbnailsScaleSettingToSlider(self, value):
        if value in self.viewThumbnailsScaleSliderStrings:
            return self.viewThumbnailsScaleSliderStrings.index(value)
        else:
            return self.viewThumbnailsScaleSliderStrings.index("1")
    
    def convertViewThumbnailsScaleSliderToSetting(self, value):
        if value < len(self.viewThumbnailsScaleSliderStrings):
            return self.viewThumbnailsScaleSliderStrings[value] 
        else:
            return "1"
    
    def convertViewThumbnailsTooltipsSettingToSlider(self, value):
        if value in self.viewThumbnailsTooltipsSliderStrings:
            return self.viewThumbnailsTooltipsSliderStrings.index(value)
        else:
            return self.viewThumbnailsTooltipsSliderStrings.index("≤4096px²")
    
    def convertViewThumbnailsTooltipsSliderToSetting(self, value):
        if value < len(self.viewThumbnailsTooltipsSliderStrings):
            return self.viewThumbnailsTooltipsSliderStrings[value] 
        else:
            return "≤4096px²"
    
    def changedViewPanelThumbnailsScaleSlider(self, value):
        setting = self.convertViewThumbnailsScaleSliderToSetting(value)
        self.viewPanelThumbnailsScaleValue.setText(setting)
        Application.writeSetting("OpenDocumentsDocker", "viewThumbnailsScale", setting)
    
    def changedViewPanelThumbnailsTooltipsSlider(self, value):
        setting = self.convertViewThumbnailsTooltipsSliderToSetting(value)
        self.viewPanelThumbnailsTooltipsValue.setText(setting)
        Application.writeSetting("OpenDocumentsDocker", "viewThumbnailsTooltips", setting)
    
    def changedThumbnailsRefreshOnSave(self, state):
        setting = str(state==2).lower()
        print("changedThumbnailsRefreshOnSave to", setting)
        Application.writeSetting("OpenDocumentsDocker", "viewRefreshOnSave", setting)
    
    def changedThumbnailsRefreshPeriodically(self, state):
        setting = str(state==2).lower()
        print("changedThumbnailsRefreshPeriodically to", setting)
        Application.writeSetting("OpenDocumentsDocker", "viewRefreshPeriodically", setting)
        if state == 2:
            if hasattr(self, "viewPanelThumbnailsRefreshPeriodicallyChecksSlider"):
                self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.setEnabled(True)
                self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.setEnabled(True)
            self.imageChangeDetectionTimer.start()
        else:
            if hasattr(self, "viewPanelThumbnailsRefreshPeriodicallyChecksSlider"):
                self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.setEnabled(False)
                self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.setEnabled(False)
            self.imageChangeDetectionTimer.stop()
            self.refreshTimer.stop()
    
    def convertViewThumbnailsRefreshPeriodicallyChecksSettingToSlider(self, value):
        if value in self.viewThumbnailsRefreshPeriodicallyChecksStrings:
            return self.viewThumbnailsRefreshPeriodicallyChecksStrings.index(value)
        else:
            return self.viewThumbnailsRefreshPeriodicallyChecksStrings.index("15/sec")
    
    def convertViewThumbnailsRefreshPeriodicallyChecksSliderToSetting(self, value):
        if value < len(self.viewThumbnailsRefreshPeriodicallyChecksStrings):
            return self.viewThumbnailsRefreshPeriodicallyChecksStrings[value] 
        else:
            return "15/sec"
    
    def convertViewThumbnailsRefreshPeriodicallyDelaySettingToSlider(self, value):
        if value in self.viewThumbnailsRefreshPeriodicallyDelayStrings:
            return self.viewThumbnailsRefreshPeriodicallyDelayStrings.index(value)
        else:
            return self.viewThumbnailsRefreshPeriodicallyDelayStrings.index("2sec")
    
    def convertViewThumbnailsRefreshPeriodicallyDelaySliderToSetting(self, value):
        if value < len(self.viewThumbnailsRefreshPeriodicallyDelayStrings):
            return self.viewThumbnailsRefreshPeriodicallyDelayStrings[value] 
        else:
            return "2sec"
    
    def changedViewPanelThumbnailsRefreshPeriodicallyChecksSlider(self, value):
        setting = self.convertViewThumbnailsRefreshPeriodicallyChecksSliderToSetting(value)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksValue.setText(setting)
        self.imageChangeDetectionTimer.setInterval(
                self.viewThumbnailsRefreshPeriodicallyChecksValues[self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.value()]
        )
        Application.writeSetting("OpenDocumentsDocker", "viewRefreshPeriodicallyChecks", setting)
    
    def changedViewPanelThumbnailsRefreshPeriodicallyDelaySlider(self, value):
        setting = self.convertViewThumbnailsRefreshPeriodicallyDelaySliderToSetting(value)
        self.viewPanelThumbnailsRefreshPeriodicallyDelayValue.setText(setting)
        self.refreshTimer.setInterval(
                self.viewThumbnailsRefreshPeriodicallyDelayValues[self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.value()]
        )
        Application.writeSetting("OpenDocumentsDocker", "viewRefreshPeriodicallyDelay", setting)
        
    def createViewPanel(self):
        app = Application
        
        self.viewPanel = QWidget(self, Qt.Popup)
        self.viewPanelLayout = QVBoxLayout()
        
        self.viewPanelDisplayButtonGroup = QButtonGroup(self.viewPanel)
        self.viewPanelDirectionButtonGroup = QButtonGroup(self.viewPanel)
        
        self.viewPanelDisplayLabel = QLabel("Display", self.viewPanel)
        self.viewPanelDisplayThumbnailsButton = QRadioButton("Thumbnails", self.viewPanel)
        self.viewPanelDisplayTextButton = QRadioButton("Text", self.viewPanel)
        
        self.viewPanelDirectionLabel = QLabel("Direction", self.viewPanel)
        self.viewPanelDirectionHorizontalButton = QRadioButton("Horizontal", self.viewPanel)
        self.viewPanelDirectionVerticalButton = QRadioButton("Vertical", self.viewPanel)
        self.viewPanelDirectionAutoButton = QRadioButton("Auto", self.viewPanel)
        self.viewPanelDirectionAutoButton.setToolTip("The list will be arranged on its longest side.")
        
        self.viewPanelThumbnailsLabel = QLabel("Thumbnails", self.viewPanel)
        self.viewPanelThumbnailsScaleLayout = QHBoxLayout()
        self.viewPanelThumbnailsScaleLabel = QLabel("Scale", self.viewPanel)
        self.viewPanelThumbnailsScaleValue = QLabel(app.readSetting("OpenDocumentsDocker", "viewThumbnailsScale", "1"), self.viewPanel)
        self.viewPanelThumbnailsScaleSlider = QSlider(Qt.Horizontal, self.viewPanel)
        self.viewPanelThumbnailsScaleSlider.setRange(0, 4)
        self.viewPanelThumbnailsScaleSlider.setTickPosition(QSlider.NoTicks)
        self.viewPanelThumbnailsScaleSlider.setTickInterval(1)
        self.viewPanelThumbnailsScaleSlider.setValue(
                self.convertViewThumbnailsScaleSettingToSlider(app.readSetting("OpenDocumentsDocker", "viewThumbnailsScale", "1"))
        )
        self.viewPanelThumbnailsScaleSlider.setToolTip("Thumbnails in the list can be generated at a reduced size then scaled up.")
        
        self.viewPanelThumbnailsTooltipsLayout = QHBoxLayout()
        self.viewPanelThumbnailsTooltipsLabel = QLabel("Tooltips", self.viewPanel)
        self.viewPanelThumbnailsTooltipsValue = QLabel(app.readSetting("OpenDocumentsDocker", "viewThumbnailsTooltips", "≤4096px²"), self.viewPanel)
        self.viewPanelThumbnailsTooltipsSlider = QSlider(Qt.Horizontal, self.viewPanel)
        self.viewPanelThumbnailsTooltipsSlider.setRange(0, 9)
        self.viewPanelThumbnailsTooltipsSlider.setTickPosition(QSlider.NoTicks)
        self.viewPanelThumbnailsTooltipsSlider.setTickInterval(1)
        self.viewPanelThumbnailsTooltipsSlider.setValue(
                self.convertViewThumbnailsTooltipsSettingToSlider(app.readSetting("OpenDocumentsDocker", "viewThumbnailsTooltips", "≤4096px²"))
        )
        self.viewPanelThumbnailsTooltipsSlider.setToolTip("Thumbnails in tooltips will be generated for images up to the chosen size.")
        
        self.viewPanelThumbnailsRefreshOnSaveCheckBox = QCheckBox("Refresh on save")
        self.viewPanelThumbnailsRefreshOnSaveCheckBox.stateChanged.connect(self.changedThumbnailsRefreshOnSave)
        self.viewPanelThumbnailsRefreshOnSaveCheckBox.setChecked(app.readSetting("OpenDocumentsDocker", "viewRefreshOnSave", "false") == "true")
        self.viewPanelThumbnailsRefreshOnSaveCheckBox.setToolTip("When you save an image, refresh its thumbnail automatically.")
        
        self.viewPanelThumbnailsRefreshPeriodicallyCheckBox = QCheckBox("Refresh periodically (experimental)")
        self.viewPanelThumbnailsRefreshPeriodicallyCheckBox.stateChanged.connect(self.changedThumbnailsRefreshPeriodically)
        self.viewPanelThumbnailsRefreshPeriodicallyCheckBox.setChecked(app.readSetting("OpenDocumentsDocker", "viewRefreshPeriodically", "false") == "true")
        self.viewPanelThumbnailsRefreshPeriodicallyCheckBox.setToolTip(
                "Automatically refresh the thumbnail for the active image if a change is detected.\n" + 
                "Checks for changes to the image so-many times each second.\n" +
                "Then tries to refresh the thumbnail every so-many seconds.\n" +
                "May not catch quick changes if they happen between checks.\n" +
                "Aggressive settings may degrade performance."
        )
        
        self.viewPanelThumbnailsRefreshPeriodicallyChecksLayout = QHBoxLayout()
        self.viewPanelThumbnailsRefreshPeriodicallyChecksLabel = QLabel("Check", self.viewPanel)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksValue = QLabel(app.readSetting("OpenDocumentsDocker", "viewRefreshPeriodicallyChecks", "15/sec"), self.viewPanel)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider = QSlider(Qt.Horizontal, self.viewPanel)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.setRange(0, 9)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.setTickPosition(QSlider.NoTicks)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.setTickInterval(1)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.setValue(
                self.convertViewThumbnailsRefreshPeriodicallyChecksSettingToSlider(app.readSetting("OpenDocumentsDocker", "viewRefreshPeriodicallyChecks", "15/sec"))
        )
        self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.setToolTip("Number of times each second the image is checked for activity.")
        self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.setEnabled(self.viewPanelThumbnailsRefreshPeriodicallyCheckBox.isChecked())
        
        self.viewPanelThumbnailsRefreshPeriodicallyDelayLayout = QHBoxLayout()
        self.viewPanelThumbnailsRefreshPeriodicallyDelayLabel = QLabel("Delay by", self.viewPanel)
        self.viewPanelThumbnailsRefreshPeriodicallyDelayValue = QLabel(app.readSetting("OpenDocumentsDocker", "viewRefreshPeriodicallyDelay", "2sec"), self.viewPanel)
        self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider = QSlider(Qt.Horizontal, self.viewPanel)
        self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.setRange(0, 10)
        self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.setTickPosition(QSlider.NoTicks)
        self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.setTickInterval(1)
        self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.setValue(
                self.convertViewThumbnailsRefreshPeriodicallyDelaySettingToSlider(app.readSetting("OpenDocumentsDocker", "viewRefreshPeriodicallyDelay", "2sec"))
        )
        self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.setToolTip("How long after the last detected change to refresh the thumbnail.")
        self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.setEnabled(self.viewPanelThumbnailsRefreshPeriodicallyCheckBox.isChecked())
        
        self.viewPanelDisplayButtonGroup.addButton(self.viewPanelDisplayThumbnailsButton)
        self.viewPanelDisplayButtonGroup.addButton(self.viewPanelDisplayTextButton)
        settingViewDisplay = app.readSetting("OpenDocumentsDocker", "viewDisplay", "thumbnails")
        self.viewPanelDisplayThumbnailsButton.setChecked(settingViewDisplay=="thumbnails")
        self.viewPanelDisplayTextButton.setChecked(settingViewDisplay=="text")
        self.viewPanelDisplayThumbnailsButton.clicked.connect(self.setViewDisplayToThumbnails)
        self.viewPanelDisplayTextButton.clicked.connect(self.setViewDisplayToText)
        settingViewDirection = app.readSetting("OpenDocumentsDocker", "viewDirection", "auto")
        self.viewPanelDirectionButtonGroup.addButton(self.viewPanelDirectionHorizontalButton)
        self.viewPanelDirectionButtonGroup.addButton(self.viewPanelDirectionVerticalButton)
        self.viewPanelDirectionButtonGroup.addButton(self.viewPanelDirectionAutoButton)
        self.viewPanelDirectionHorizontalButton.setChecked(settingViewDirection=="horizontal")
        self.viewPanelDirectionVerticalButton.setChecked(settingViewDirection=="vertical")
        self.viewPanelDirectionAutoButton.setChecked(settingViewDirection=="auto")
        self.viewPanelDirectionHorizontalButton.clicked.connect(self.setViewDirectionToHorizontal)
        self.viewPanelDirectionVerticalButton.clicked.connect(self.setViewDirectionToVertical)
        self.viewPanelDirectionAutoButton.clicked.connect(self.setViewDirectionToAuto)
        
        self.viewPanelLayout.addWidget(self.viewPanelDisplayLabel)
        self.viewPanelLayout.addWidget(self.viewPanelDisplayThumbnailsButton)
        self.viewPanelLayout.addWidget(self.viewPanelDisplayTextButton)
        self.viewPanelLayout.addWidget(self.viewPanelDirectionLabel)
        self.viewPanelLayout.addWidget(self.viewPanelDirectionHorizontalButton)
        self.viewPanelLayout.addWidget(self.viewPanelDirectionVerticalButton)
        self.viewPanelLayout.addWidget(self.viewPanelDirectionAutoButton)
        self.viewPanelLayout.addWidget(self.viewPanelThumbnailsLabel)
        self.viewPanelThumbnailsScaleLayout.addWidget(self.viewPanelThumbnailsScaleLabel)
        self.viewPanelThumbnailsScaleLayout.addWidget(self.viewPanelThumbnailsScaleValue)
        self.viewPanelThumbnailsScaleLayout.addWidget(self.viewPanelThumbnailsScaleSlider)
        self.viewPanelThumbnailsScaleLayout.setStretch(0, 2)
        self.viewPanelThumbnailsScaleLayout.setStretch(1, 2)
        self.viewPanelThumbnailsScaleLayout.setStretch(2, 5)
        self.viewPanelLayout.addLayout(self.viewPanelThumbnailsScaleLayout)
        self.viewPanelThumbnailsTooltipsLayout.addWidget(self.viewPanelThumbnailsTooltipsLabel)
        self.viewPanelThumbnailsTooltipsLayout.addWidget(self.viewPanelThumbnailsTooltipsValue)
        self.viewPanelThumbnailsTooltipsLayout.addWidget(self.viewPanelThumbnailsTooltipsSlider)
        self.viewPanelThumbnailsTooltipsLayout.setStretch(0, 2)
        self.viewPanelThumbnailsTooltipsLayout.setStretch(1, 2)
        self.viewPanelThumbnailsTooltipsLayout.setStretch(2, 5)
        self.viewPanelLayout.addLayout(self.viewPanelThumbnailsTooltipsLayout)
        self.viewPanelLayout.addWidget(self.viewPanelThumbnailsRefreshOnSaveCheckBox)
        self.viewPanelLayout.addWidget(self.viewPanelThumbnailsRefreshPeriodicallyCheckBox)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.viewPanelThumbnailsRefreshPeriodicallyChecksLabel)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.viewPanelThumbnailsRefreshPeriodicallyChecksValue)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(0, 2)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(1, 2)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(2, 5)
        self.viewPanelLayout.addLayout(self.viewPanelThumbnailsRefreshPeriodicallyChecksLayout)
        self.viewPanelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.viewPanelThumbnailsRefreshPeriodicallyDelayLabel)
        self.viewPanelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.viewPanelThumbnailsRefreshPeriodicallyDelayValue)
        self.viewPanelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider)
        self.viewPanelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(0, 2)
        self.viewPanelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(1, 2)
        self.viewPanelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(2, 5)
        self.viewPanelLayout.addLayout(self.viewPanelThumbnailsRefreshPeriodicallyDelayLayout)
        self.viewPanel.setLayout(self.viewPanelLayout)
        self.viewPanel.setMinimumWidth(384)
        #viewPanel.setMinimumHeight(200)
        #viewPanel.setWindowFlags(Qt.Popup)
        
        self.viewPanelThumbnailsScaleSlider.valueChanged.connect(self.changedViewPanelThumbnailsScaleSlider)
        self.viewPanelThumbnailsTooltipsSlider.valueChanged.connect(self.changedViewPanelThumbnailsTooltipsSlider)
        self.viewPanelThumbnailsRefreshPeriodicallyChecksSlider.valueChanged.connect(self.changedViewPanelThumbnailsRefreshPeriodicallyChecksSlider)
        self.viewPanelThumbnailsRefreshPeriodicallyDelaySlider.valueChanged.connect(self.changedViewPanelThumbnailsRefreshPeriodicallyDelaySlider)

    def clickedViewButton(self):
        kludgePixels = 14
        # self.mapToGlobal or self.viewButton.mapToGlobal?
        self.viewPanel.move(
                self.mapToGlobal(self.viewButton.frameGeometry().topLeft()) + QPoint(0, -self.viewPanel.sizeHint().height() + kludgePixels))
        self.viewPanel.show()
    
    def delayedResize(self):
        self.resizeDelay.stop()
        print("delayedResize: lastSize:", self.lastSize)
        print("               new size:", self.baseWidget.size())
        lastFlow = self.listView.flow()
        self.setDockerDirection(Application.readSetting("OpenDocumentsDocker", "viewDirection", "auto"))
        if self.lastSize == self.baseWidget.size():
            print("delayedResize: size did not change - no refresh.")
        elif self.listView.flow() == lastFlow and (
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
        #print("document remains open." if self.documentHasViews(view.document(), view) else "document has no views left, will close.")
        
        self.documentUniqueIdFromLastClosedView = self.documentUniqueId(view.document())
    
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
    
    def imageSaved(self, filename):
        # unnecessary? the document just saved should be the active one
        app = Application
        doc = None
        for i in range(len(app.documents())):
            if app.documents()[i].fileName() == filename:
                doc = app.documents()[i]
                break
        print("image saved -", filename, "(doc", str(doc) + ")")
        if self.viewPanelThumbnailsRefreshOnSaveCheckBox.isChecked():
            if self.imageChangeDetected:
                self.imageChangeDetected = False
                self.refreshTimer.stop()
            self.updateDocumentThumbnail()
    
#    def applicationClosing(self):
#        print("application closing")
    
    def dockMoved(self, area):
        print("dockMoved:", area)
        self.dockLocation = area
        self.listToolTip.hide()
    
    def __init__(self):
        print("OpenDocumentsDocker: begin init")
        super(OpenDocumentsDocker, self).__init__()
        
        self.dockLocation = None
        self.dockLocationChanged.connect(self.dockMoved)
        self.dockVisible = True
        self.visibilityChanged.connect(self.dockVisibilityChanged)
        self.deferredItemThumbnailCount = 0
        
        self.baseWidget = QWidget()
        self.layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.listView = QListWidget()
        self.listToolTip = QLabel()
        self.buttonLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.loadButton = QPushButton() #i18n("Refresh"))
        self.loadButton.setIcon(Application.icon('view-refresh'))
        self.viewButton = QPushButton()
        self.viewButton.setIcon(Application.icon('view-choose'))
        #self.listModel = opendocumentslistmodel.OpenDocumentsListModel(self.devicePixelRatioF())
        
        self.setDockerDirection(Application.readSetting("OpenDocumentsDocker", "viewDirection", "auto"))
        self.listView.setMovement(QListView.Free)
        self.listView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.listView.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.listView.activated.connect(self.clicked)
        self.listView.clicked.connect(self.clicked)
        self.listView.setMouseTracking(True)
        self.listView.entered.connect(self.entered)
        self.listView.viewportEntered.connect(self.viewportEntered)
        if False:
            self.listView.setAcceptDrops(True)
            self.listView.setDragEnabled(True)
            self.listView.setDropIndicatorShown(True)
            print("qaiv.im:", QAbstractItemView.InternalMove)
            self.listView.setDragDropMode(QAbstractItemView.InternalMove)
            self.listView.setDefaultDropAction(Qt.MoveAction)
            self.listView.setDragDropOverwriteMode(False)
        else:
            self.listView.setAcceptDrops(False)
            self.listView.setDragEnabled(False)
        
        self.layout.addWidget(self.listView)
        
        self.imageChangeDetected = False
        self.imageOldSize = QSize(0, 0)
        self.imageChangeDetectionTimer = QTimer(self.baseWidget)
        setting = Application.readSetting("OpenDocumentsDocker", "viewRefreshPeriodicallyChecks", "15/sec")
        self.imageChangeDetectionTimer.setInterval(
            self.viewThumbnailsRefreshPeriodicallyChecksValues[self.viewThumbnailsRefreshPeriodicallyChecksStrings.index(setting)]
        )
        self.imageChangeDetectionTimer.timeout.connect(self.imageChangeDetectionTimerTimeout)
        self.refreshTimer = QTimer(self.baseWidget)
        setting = Application.readSetting("OpenDocumentsDocker", "viewRefreshPeriodicallyDelay", "2sec")
        self.refreshTimer.setInterval(
            self.viewThumbnailsRefreshPeriodicallyDelayValues[self.viewThumbnailsRefreshPeriodicallyDelayStrings.index(setting)]
        )
        self.refreshTimer.timeout.connect(self.refreshTimerTimeout)
        
        #menu = QMenu("Menu Title", None)
        #menu.aboutToShow.connect(self.viewmenuabouttoshow)
        #self.viewButton.setMenu(menu)
        self.createViewPanel()
        self.viewButton.clicked.connect(self.clickedViewButton)
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
        if Application.readSetting("OpenDocumentsDocker", "viewDisplay", "thumbnails") == "text":
            self.itemTextUpdateTimer.start()
        
        #self.loadButton.clicked.connect(self.refreshOpenDocuments)
        self.loadButton.clicked.connect(self.updateDocumentThumbnailForced)
        self.setWindowTitle(i18n("Open Documents Docker"))
        
        # used for doing things with the document that was current before active view changed
        self.currentDocumentId = None
        
        appNotifier = Application.notifier()
        appNotifier.setActive(True)
        #appNotifier.viewCreated.connect(self.refreshOpenDocuments)
        appNotifier.viewClosed.connect(self.viewClosed)
        appNotifier.imageCreated.connect(self.imageCreated)
        appNotifier.imageClosed.connect(self.imageClosed)
        appNotifier.imageSaved.connect(self.imageSaved)
        #appNotifier.applicationClosing.connect(self.applicationClosing)
        
        appNotifier.windowCreated.connect(self.windowCreated)
    
    def itemTextUpdateTimerTimeout(self):
        count = self.listView.count()
        for i in range(count):
            item = self.listView.item(i)
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
                    print(self.imageOldSize)
                    print(doc.bounds().size())
                    print("imageChangeDetectionTimerTimeout - size changed")
                    changed = True
            else:
                print("imageChangeDetectionTimerTimeout - barrier lock failed")
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
        #return
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
            self.listView.setFlow(QListView.LeftToRight)
            self.buttonLayout.setDirection(QBoxLayout.TopToBottom)
            self.loadButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.viewButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            try:
                self.listView.verticalScrollBar().valueChanged.disconnect(self.listScrolled)
            except TypeError:
                print("couldn't disconnect vscoll")
                pass
            self.listView.horizontalScrollBar().valueChanged.connect(self.listScrolled)
        else:
            self.layout.setDirection(QBoxLayout.TopToBottom)
            self.listView.setFlow(QListView.TopToBottom)
            self.buttonLayout.setDirection(QBoxLayout.LeftToRight)
            self.loadButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.viewButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            try:
                self.listView.horizontalScrollBar().valueChanged.disconnect(self.listScrolled)
            except TypeError:
                print("couldn't disconnect hscoll")
                pass
            self.listView.verticalScrollBar().valueChanged.connect(self.listScrolled)
        self.updateScrollBarPolicy()
    
    def updateScrollBarPolicy(self):
        if self.listView.flow() == QListView.LeftToRight:
            self.listView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.listView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            if Application.readSetting("OpenDocumentsDocker", "viewDisplay", "thumbnails") == "text":
                self.listView.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            else:
                self.listView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.listView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    
    def listScrolled(self, value):
        #print("listScrolled by", value)
        self.processDeferredDocumentThumbnails()
    
    def windowCreated(self):
        # TODO: is it ok to repeatedly connect same window?
        # (that is, each new window, all windows get connected again.)
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
            self.currentDocumentId = Application.activeDocument().rootNode().uniqueId()
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
        print("leave event!")
        self.listToolTip.hide()
    
    def viewportEntered(self):
        print("viewport entered!")
        self.listToolTip.hide()
    
    def dockVisibilityChanged(self, visible):
        print("visibilityChanged: visible =", visible)
        self.dockVisible = visible
        self.processDeferredDocumentThumbnails()
        if self.viewPanelThumbnailsRefreshPeriodicallyCheckBox.isChecked():
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
        
        listRect = self.listView.childrenRect()
        itemCount = self.listView.count()
        for i in range(itemCount):
            item = self.listView.item(i)
            if item.data(self.ItemUpdateDeferredRole):
                visRect = self.listView.visualItemRect(item)
                if not listRect.intersected(visRect).isEmpty():
                    item.setData(self.ItemUpdateDeferredRole, False)
                    self.deferredItemThumbnailCount -= 1
                    print("DEFERRED ITEM COUNT -1, =", self.deferredItemThumbnailCount)
                    self.updateDocumentThumbnail(self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole)))
                else:
                    #print("item", i, "is scrolled out of view")
                    pass
    
    def contextMenuEvent(self, event):
        print("ctx menu event -", event.globalPos(), event.reason())
        self.listToolTip.hide()
        if len(self.listView.selectedIndexes()) == 0:
            print("ctx menu cancelled (no selection)")
            return
        
        app = Application
        index = self.listView.selectedIndexes()[0]
        item = self.listView.selectedItems()[0]
        listTopLeft = self.listView.mapToGlobal(self.listView.frameGeometry().topLeft())
        itemRect = self.listView.visualItemRect(item)
        itemRect.translate(listTopLeft)
        print("itemRect:", itemRect)
        
        pos = QPoint(0, 0)
        if event.reason() == QContextMenuEvent.Mouse:
            if not itemRect.contains(event.globalPos()):
                print("ctx menu cancelled (mouse not over item)")
                return
            pos = event.globalPos()
        else:
            pos = (itemRect.topLeft() + itemRect.bottomRight()) / 2
        item = self.listView.item(index.row())
        
        doc = self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
        if not doc:
            print("ODD: right-clicked an item that has no doc, or points to a doc that doesn't exist!")
            return
        
        print("selected:", index, " -", doc.fileName())
        app.activeDocument().waitForDone()
        self.find_and_activate_view(doc)
        app.setActiveDocument(doc)
        doc.waitForDone()
        menu = QMenu(self)
        menu.addAction(app.action('file_save'))
        menu.addAction(app.action('file_save_as'))
        menu.addAction(app.action('file_export_file'))
        menu.addAction(app.action('create_copy'))
        menu.addAction(app.action('file_documentinfo'))
        # seperator
        # new file
        menu.addAction(app.action('file_close'))
        menu.exec(pos)
    
#    def quickCopyMergedAction(self):
#        app = Application
#        app.action('select_all').trigger()
#        app.action('copy_merged').trigger()
#        app.action('edit_undo').trigger()
#        app.action('edit_undo').trigger()
#
#    def createActions(self, window):
#        action = window.createAction("quickCopyMergedAction", "Quick Copy Merged")
#        action.triggered.connect(self.quickCopyMergedAction)
    
    def dropEvent(self, event):
        print("dropEvent: ", event)
    
    def refreshOpenDocuments(self, soft=False):
        if soft:
            count = self.listView.count()
            for i in range(count):
                item = self.listView.item(i)
                self.updateDocumentThumbnail(self.findDocumentWithItem(item))
        else:
            self.listView.clear()
            for i in Application.documents():
                self.addDocumentToList(i)
        
        self.ensureListSelectionIsActiveDocument()
    
    def debugDump(self):
        count = len(Application.documents())
        print(" - list of all documents (count:"+str(count)+") - ")
        for i in range(count):
            doc = Application.documents()[i]
            print("   #"+str(i)+":", doc)
            print("    - fName:", doc.fileName())
            print("    - uid:  ", self.documentUniqueId(doc))
        count = self.listView.count()
        print(" - list of all list items (count:"+str(count)+") - ")
        print("   selected: ", self.listView.selectedItems())
        for i in range(count):
            item = self.listView.item(i)
            print("   #"+str(i)+":", item)
            print("    - document data:", item.data(self.ItemDocumentRole))
        print(" - end of lists - ")
    
    def ensureListSelectionIsActiveDocument(self):
        doc = Application.activeDocument()
        
        if doc == None:
            #print("ODD:elsiad: no active document")
            return False
        
        uid = self.documentUniqueId(doc)
        
        print("active document:", doc, "-", self.documentDisplayName(doc) + ", uid:", str(uid))
        #print("len self.listView.selectedItems:", len(self.listView.selectedItems()))
        if len(self.listView.selectedItems()) > 0:
            if self.listView.selectedItems()[0].data(self.ItemDocumentRole) == uid:
                print("ODD:elsiad: active document is selected")
                return True
        
        print("ODD:elsiad: list selection was not active document ...", end=" ")
        itemCount = self.listView.count()
        if itemCount == 0:
            print("the list is empty.")
            return False
        
        #print("ODD:elsiad: itemCount: ", itemCount)
        for i in range(itemCount): #-1):
            #print("ODD:elsiad: loop", i)
            #doc.waitForDone()
            item = self.listView.item(i)
            #print("ODD:elsiad: item:", item)
           #print("ODD:elsiad: item doc role:", item.data(self.ItemDocumentRole))
            
            #print("ODD:elsiad: comparing", item.data(self.ItemDocumentRole), " with", uid)
            if item.data(self.ItemDocumentRole) == uid:
                #print("ODD:elsiad: found it")
                self.listView.setCurrentItem(item)
                print("now it is.")
                return True
            else:
                #print("ODD:elsiad: not it")
                pass
        
        print("could not find item for active document!")
        return False
    
    def isItemOnScreen(self, item):
        if not self.dockVisible:
            return False

        listRect = self.listView.childrenRect()
        visRect = self.listView.visualItemRect(item)
        return listRect.intersected(visRect).isValid()
    
    def updateDocumentThumbnailForced(self):
        self.updateDocumentThumbnail(doc=None, force=True)
    
    def updateDocumentThumbnail(self, doc=None, force=False):
        if not doc:
            doc = Application.activeDocument()
        if not doc:
            print("update thumb: no active document.")
            return
        if self.viewPanelDisplayButtonGroup.checkedButton() == self.viewPanelDisplayTextButton:
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
        print("generated:", thumbnail)
        item.setData(Qt.DecorationRole, QPixmap.fromImage(thumbnail))
    
    def findItemWithDocument(self, doc):
        uid = self.documentUniqueId(doc)
        itemCount = self.listView.count()
        for i in range(itemCount):
            searchItem = self.listView.item(i)
            if searchItem.data(self.ItemDocumentRole) == uid:
                return searchItem
        return None
    
    def findDocumentWithItem(self, item):
        return self.findDocumentWithUniqueId(item.data(self.ItemDocumentRole))
    
    def addDocumentToList(self, doc):
        item = None
        # ensure document is ready
        #print("waiting for doc ready ...", end=" ")
        #doc.waitForDone()
        #print("done")
        if self.viewPanelDisplayButtonGroup.checkedButton() == self.viewPanelDisplayThumbnailsButton:
            thumbnail = self.generateThumbnailForDocument(doc)
            item = QListWidgetItem("", self.listView)
            item.setData(Qt.DecorationRole, QPixmap.fromImage(thumbnail))
        else:
            item = QListWidgetItem(self.documentDisplayName(doc), self.listView)
        uid = self.documentUniqueId(doc)
        print("item", item, " will be given data", uid, "...", end=" ")
        item.setData(self.ItemDocumentRole, uid)
        print("done" if (item.data(self.ItemDocumentRole) == uid) else "failed!")
        
        #self.listView.setCurrentItem(item)
        #self.debugDump()
        self.ensureListSelectionIsActiveDocument()
    
    def removeDocumentFromList(self, uid):
        print("try to remove doc from list")
        print("uid:", uid)
        item = None
        itemCount = self.listView.count()
        for i in range(itemCount):
            searchItem = self.listView.item(i)
            print("compare against item with:", searchItem.data(self.ItemDocumentRole))
            if searchItem.data(self.ItemDocumentRole) == uid:
                print("found item, taking...")
                item = self.listView.takeItem(self.listView.row(searchItem))
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
            if uid == doc.rootNode().uniqueId():
                return doc
        print("ODD: could not find document with uid", str(uid))
        return None
    
    def generateThumbnailForDocument(self, doc):
        print("generate thumbnail for doc", doc)
        
        # ensure the thumbnail will be complete
        doc.waitForDone()
        
        kludgePixels=6
        width = 0
        if self.listView.flow() == QListView.TopToBottom:
            scrollBarWidth = self.listView.verticalScrollBar().sizeHint().width()
            width = self.listView.width() - kludgePixels - scrollBarWidth
        else:
            scrollBarHeight = self.listView.horizontalScrollBar().sizeHint().height()
            width = self.listView.height() - kludgePixels - scrollBarHeight
        print("gtfd: calculated width:", width)
        
        # keep size from getting too big and slowing things down
        width = min(width, 256)
        
        thumbnail = None
        
        scaleFactor = self.viewThumbnailsScaleSliderValues[self.viewPanelThumbnailsScaleSlider.value()]
        
        if scaleFactor == 1:
            # new document may briefly exist as qobject type before becoming document,
            # during which projection isn't available but thumbnail is.
            # projection is much faster so prefer it when available.
            if type(doc) == Document:
                print("projection->thumbnail")
                thumbnail = doc.projection(0, 0, doc.width(), doc.height())
            else:
                print("regular thumbnail")
                thumbnail = doc.thumbnail(width, width)
        
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
        
        if self.listView.flow() == QListView.TopToBottom:
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



##BBD's Krita Script Starter Feb 2018
#from krita import DockWidget, DockWidgetFactory, DockWidgetFactoryBase

#DOCKER_NAME = 'OpenDocumentsDocker'
#DOCKER_ID = 'pykrita_opendocumentsdocker'
#
#
#class Opendocumentsdocker(DockWidget):
#
#    def __init__(self):
#        super().__init__()
#        self.setWindowTitle(DOCKER_NAME)
#
#    def canvasChanged(self, canvas):
#        pass
#
#
#instance = Application
#dock_widget_factory = DockWidgetFactory(DOCKER_ID,
#                                        DockWidgetFactoryBase.DockRight,
#                                        Opendocumentsdocker)
#
#instance.addDockWidgetFactory(dock_widget_factory)

class ODDExtension(Extension):

    def __init__(self, parent):
        # This is initialising the parent, always important when subclassing.
        super().__init__(parent)
        #print("myextension init")

    def setup(self):
        pass

    def createActions(self, window):
        #print("myextension createactions")
        #action = window.createAction("myAction", "My Script", "tools/scripts")
        pass

# And add the extension to Krita's list of extensions:
Application.addExtension(ODDExtension(Application))

