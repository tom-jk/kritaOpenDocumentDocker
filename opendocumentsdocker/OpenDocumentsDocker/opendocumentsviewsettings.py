from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QScreen
from PyQt5.QtWidgets import QWidget, QBoxLayout, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider
from krita import *

class OpenDocumentsViewSettings:
    ThumbnailsScaleSliderStrings = ["1/16", "1/8", "1/4", "1/2", "1"]
    ThumbnailsScaleSliderValues = [1.0/16.0, 1.0/8.0, 1.0/4.0, 1.0/2.0, 1]
    ThumbnailsTooltipsSliderStrings = ["never","≤128px²","≤256px²","≤512px²","≤1024px²","≤2048px²","≤4096px²","≤8192px²","≤16384px²","always"]
    ThumbnailsTooltipsSliderValues = [0, 128*128, 256*256, 512*512, 1024*1024, 2048*2048, 4096*4096, 8192*8192, 16384*16384, float("inf")]
    ThumbnailsRefreshPeriodicallyChecksStrings = ["1/sec","2/sec","3/sec","4/sec","5/sec","8/sec","10/sec","15/sec","20/sec","30/sec"]
    ThumbnailsRefreshPeriodicallyChecksValues = [1000, 500, 333, 250, 200, 125, 100, 67, 50, 33]
    ThumbnailsRefreshPeriodicallyDelayStrings = ["1/2sec", "1sec", "1.5sec", "2sec", "3sec", "4sec", "5sec", "7sec", "10sec", "20sec", "1min"]
    ThumbnailsRefreshPeriodicallyDelayValues = [500, 1000, 1500, 2000, 3000, 4000, 5000, 7000, 10000, 20000, 60000]
    
    Defaults = {
            "viewDirection":"auto",
            "viewDisplay":"thumbnails",
            "viewRefreshOnSave":"true",
            "viewRefreshPeriodically":"false",
            "viewRefreshPeriodicallyChecks":"15/sec",
            "viewRefreshPeriodicallyDelay":"2sec",
            "viewThumbnailsScale":"1",
            "viewThumbnailsTooltips":"≤4096px²",
            "idAutoDisambiguateCopies":"false",
    }
    
    def __init__(self, odd):
        self.odd = odd
    
    def readSetting(self, setting):
        if not setting in self.Defaults:
            return
        return Application.readSetting("OpenDocumentsDocker", setting, self.Defaults[setting])
    
    def writeSetting(self, setting, value):
        if not setting in self.Defaults:
            return
        Application.writeSetting("OpenDocumentsDocker", setting, value)
    
    def setDisplayToThumbnails(self):
        print("setDisplayToThumbnails")
        self.writeSetting("viewDisplay", "thumbnails")
        self.odd.refreshOpenDocuments()
        self.odd.updateScrollBarPolicy()
        if self.odd.itemTextUpdateTimer.isActive():
            self.odd.itemTextUpdateTimer.stop()

    def setDisplayToText(self):
        print("setDisplayToText")
        self.writeSetting("viewDisplay", "text")
        self.odd.refreshOpenDocuments()
        self.odd.updateScrollBarPolicy()
        if not self.odd.itemTextUpdateTimer.isActive():
            self.odd.itemTextUpdateTimer.start()

    def setDirectionToHorizontal(self):
        print("setDirectionToHorizontal")
        self.writeSetting("viewDirection", "horizontal")
        self.odd.setDockerDirection("horizontal")

    def setDirectionToVertical(self):
        print("setDirectionToVertical")
        self.writeSetting("viewDirection", "vertical")
        self.odd.setDockerDirection("vertical")

    def setDirectionToAuto(self):
        print("setDirectionToAuto")
        self.writeSetting("viewDirection", "auto")
        self.odd.setDockerDirection("auto")
    
    def convertThumbnailsScaleSettingToSlider(self, value):
        if value in self.ThumbnailsScaleSliderStrings:
            return self.ThumbnailsScaleSliderStrings.index(value)
        else:
            return self.ThumbnailsScaleSliderStrings.index("1")
    
    def convertThumbnailsScaleSliderToSetting(self, value):
        if value < len(self.ThumbnailsScaleSliderStrings):
            return self.ThumbnailsScaleSliderStrings[value] 
        else:
            return "1"
    
    def convertThumbnailsTooltipsSettingToSlider(self, value):
        if value in self.ThumbnailsTooltipsSliderStrings:
            return self.ThumbnailsTooltipsSliderStrings.index(value)
        else:
            return self.ThumbnailsTooltipsSliderStrings.index("≤4096px²")
    
    def convertThumbnailsTooltipsSliderToSetting(self, value):
        if value < len(self.ThumbnailsTooltipsSliderStrings):
            return self.ThumbnailsTooltipsSliderStrings[value] 
        else:
            return "≤4096px²"
    
    def changedPanelThumbnailsScaleSlider(self, value):
        setting = self.convertThumbnailsScaleSliderToSetting(value)
        self.panelThumbnailsScaleValue.setText(setting)
        self.writeSetting("viewThumbnailsScale", setting)
    
    def changedPanelThumbnailsTooltipsSlider(self, value):
        setting = self.convertThumbnailsTooltipsSliderToSetting(value)
        self.panelThumbnailsTooltipsValue.setText(setting)
        self.writeSetting("viewThumbnailsTooltips", setting)
    
    def changedThumbnailsRefreshOnSave(self, state):
        setting = str(state==2).lower()
        print("changedThumbnailsRefreshOnSave to", setting)
        self.writeSetting("viewRefreshOnSave", setting)
    
    def changedThumbnailsRefreshPeriodically(self, state):
        setting = str(state==2).lower()
        print("changedThumbnailsRefreshPeriodically to", setting)
        self.writeSetting("viewRefreshPeriodically", setting)
        if state == 2:
            if hasattr(self, "panelThumbnailsRefreshPeriodicallyChecksSlider"):
                self.panelThumbnailsRefreshPeriodicallyChecksSlider.setEnabled(True)
                self.panelThumbnailsRefreshPeriodicallyDelaySlider.setEnabled(True)
            self.odd.imageChangeDetectionTimer.start()
        else:
            if hasattr(self, "panelThumbnailsRefreshPeriodicallyChecksSlider"):
                self.panelThumbnailsRefreshPeriodicallyChecksSlider.setEnabled(False)
                self.panelThumbnailsRefreshPeriodicallyDelaySlider.setEnabled(False)
            self.odd.imageChangeDetectionTimer.stop()
            self.odd.refreshTimer.stop()
    
    def changedIdAutoDisambiguateCopies(self, state):
        setting = str(state==2).lower()
        print("changedIdAutoDisambiguateCopies to", setting)
        self.writeSetting("idAutoDisambiguateCopies", setting)
        
        if state == 2:
            # turned on, scan current open documents for ambiguous id's.
            # if detected, ask user if they would like to add the annotations now.
            
            isAnyDocAmbiguous = False
            for i in Application.documents():
                if not self.odd.isDocumentUniquelyIdentified(i):
                    isAnyDocAmbiguous = True
            
            if not isAnyDocAmbiguous:
                return
            
            msgBox = QMessageBox(
                    QMessageBox.Question,
                    "Krita",
                    "ODD would like to add ID annotations to some open documents."
            )
            btnCancel = msgBox.addButton(QMessageBox.Cancel)
            btnOk = msgBox.addButton(QMessageBox.Ok)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            msgBox.exec()
            
            if msgBox.clickedButton() == btnOk:
                print("Ok")
                # for every open document, check ambiguity and add extraUid as required.
                # iterate backwards over doc list, because we want to only add extraUid's
                # to the documents that are copies, and they will(? presumably) always be
                # later in the list than their source doc.
                docCount = len(Application.documents())
                for i in range(docCount-1, -1, -1):
                    self.odd.setDocumentExtraUid(Application.documents()[i])
                self.odd.refreshOpenDocuments()
            else:
                print("Cancel")
        else:
            # turned off, scan current open documents for disambiguated id's.
            # if detected, ask user if they would like to delete the annotations now.
            
            isAnyDocWithExtraUid = False
            for i in Application.documents():
                if i.annotation("ODD_extra_uid"):
                    isAnyDocWithExtraUid = True
            
            if not isAnyDocWithExtraUid:
                return
            
            msgBox = QMessageBox(
                    QMessageBox.Question,
                    "Krita",
                    "ODD has added ID annotations to some open documents.<br/><br/>" \
                    "Would you like to remove these immediately?"
            )
            btnCancel = msgBox.addButton(QMessageBox.Cancel)
            btnOk = msgBox.addButton(QMessageBox.Ok)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            msgBox.exec()
            
            if msgBox.clickedButton() == btnOk:
                print("Ok")
                for i in Application.documents():
                    i.removeAnnotation("ODD_extra_uid")
                self.odd.currentDocumentId = self.odd.findDocumentWithUniqueId(self.odd.currentDocumentId, enableFallback=True)
                self.odd.refreshOpenDocuments()

            else:
                print("Cancel")
    
    def convertThumbnailsRefreshPeriodicallyChecksSettingToSlider(self, value):
        if value in self.ThumbnailsRefreshPeriodicallyChecksStrings:
            return self.ThumbnailsRefreshPeriodicallyChecksStrings.index(value)
        else:
            return self.ThumbnailsRefreshPeriodicallyChecksStrings.index("15/sec")
    
    def convertThumbnailsRefreshPeriodicallyChecksSliderToSetting(self, value):
        if value < len(self.ThumbnailsRefreshPeriodicallyChecksStrings):
            return self.ThumbnailsRefreshPeriodicallyChecksStrings[value] 
        else:
            return "15/sec"
    
    def convertThumbnailsRefreshPeriodicallyDelaySettingToSlider(self, value):
        if value in self.ThumbnailsRefreshPeriodicallyDelayStrings:
            return self.ThumbnailsRefreshPeriodicallyDelayStrings.index(value)
        else:
            return self.ThumbnailsRefreshPeriodicallyDelayStrings.index("2sec")
    
    def convertThumbnailsRefreshPeriodicallyDelaySliderToSetting(self, value):
        if value < len(self.ThumbnailsRefreshPeriodicallyDelayStrings):
            return self.ThumbnailsRefreshPeriodicallyDelayStrings[value] 
        else:
            return "2sec"
    
    def changedPanelThumbnailsRefreshPeriodicallyChecksSlider(self, value):
        setting = self.convertThumbnailsRefreshPeriodicallyChecksSliderToSetting(value)
        self.panelThumbnailsRefreshPeriodicallyChecksValue.setText(setting)
        self.odd.imageChangeDetectionTimer.setInterval(
                self.ThumbnailsRefreshPeriodicallyChecksValues[self.panelThumbnailsRefreshPeriodicallyChecksSlider.value()]
        )
        self.writeSetting("viewRefreshPeriodicallyChecks", setting)
    
    def changedPanelThumbnailsRefreshPeriodicallyDelaySlider(self, value):
        setting = self.convertThumbnailsRefreshPeriodicallyDelaySliderToSetting(value)
        self.panelThumbnailsRefreshPeriodicallyDelayValue.setText(setting)
        self.odd.refreshTimer.setInterval(
                self.ThumbnailsRefreshPeriodicallyDelayValues[self.panelThumbnailsRefreshPeriodicallyDelaySlider.value()]
        )
        self.writeSetting("viewRefreshPeriodicallyDelay", setting)
        
    def createPanel(self):
        app = Application
        
        self.panel = QWidget(self.odd, Qt.Popup)
        self.panelLayout = QVBoxLayout()
        
        self.panelDisplayButtonGroup = QButtonGroup(self.panel)
        self.panelDirectionButtonGroup = QButtonGroup(self.panel)
        
        self.panelDisplayLabel = QLabel("Display", self.panel)
        self.panelDisplayThumbnailsButton = QRadioButton("Thumbnails", self.panel)
        self.panelDisplayTextButton = QRadioButton("Text", self.panel)
        
        self.panelDirectionLabel = QLabel("Direction", self.panel)
        self.panelDirectionHorizontalButton = QRadioButton("Horizontal", self.panel)
        self.panelDirectionVerticalButton = QRadioButton("Vertical", self.panel)
        self.panelDirectionAutoButton = QRadioButton("Auto", self.panel)
        self.panelDirectionAutoButton.setToolTip("The list will be arranged on its longest side.")
        
        setting = self.readSetting("viewThumbnailsScale")
        self.panelThumbnailsLabel = QLabel("Thumbnails", self.panel)
        self.panelThumbnailsScaleLayout = QHBoxLayout()
        self.panelThumbnailsScaleLabel = QLabel("Scale", self.panel)
        self.panelThumbnailsScaleValue = QLabel(setting, self.panel)
        self.panelThumbnailsScaleSlider = QSlider(Qt.Horizontal, self.panel)
        self.panelThumbnailsScaleSlider.setRange(0, 4)
        self.panelThumbnailsScaleSlider.setTickPosition(QSlider.NoTicks)
        self.panelThumbnailsScaleSlider.setTickInterval(1)
        self.panelThumbnailsScaleSlider.setValue(
                self.convertThumbnailsScaleSettingToSlider(setting)
        )
        self.panelThumbnailsScaleSlider.setToolTip("Thumbnails in the list can be generated at a reduced size then scaled up.")
        
        setting = self.readSetting("viewThumbnailsTooltips")
        self.panelThumbnailsTooltipsLayout = QHBoxLayout()
        self.panelThumbnailsTooltipsLabel = QLabel("Tooltips", self.panel)
        self.panelThumbnailsTooltipsValue = QLabel(setting, self.panel)
        self.panelThumbnailsTooltipsSlider = QSlider(Qt.Horizontal, self.panel)
        self.panelThumbnailsTooltipsSlider.setRange(0, 9)
        self.panelThumbnailsTooltipsSlider.setTickPosition(QSlider.NoTicks)
        self.panelThumbnailsTooltipsSlider.setTickInterval(1)
        self.panelThumbnailsTooltipsSlider.setValue(
                self.convertThumbnailsTooltipsSettingToSlider(setting)
        )
        self.panelThumbnailsTooltipsSlider.setToolTip("Thumbnails in tooltips will be generated for images up to the chosen size.")
        
        self.panelThumbnailsRefreshOnSaveCheckBox = QCheckBox("Refresh on save")
        self.panelThumbnailsRefreshOnSaveCheckBox.stateChanged.connect(self.changedThumbnailsRefreshOnSave)
        self.panelThumbnailsRefreshOnSaveCheckBox.setChecked(self.readSetting("viewRefreshOnSave") == "true")
        self.panelThumbnailsRefreshOnSaveCheckBox.setToolTip("When you save an image, refresh its thumbnail automatically.")
        
        self.panelThumbnailsRefreshPeriodicallyCheckBox = QCheckBox("Refresh periodically (experimental)")
        self.panelThumbnailsRefreshPeriodicallyCheckBox.stateChanged.connect(self.changedThumbnailsRefreshPeriodically)
        self.panelThumbnailsRefreshPeriodicallyCheckBox.setChecked(self.readSetting("viewRefreshPeriodically") == "true")
        self.panelThumbnailsRefreshPeriodicallyCheckBox.setToolTip(
                "Automatically refresh the thumbnail for the active image if a change is detected.\n" + 
                "Checks for changes to the image so-many times each second.\n" +
                "Then tries to refresh the thumbnail every so-many seconds.\n" +
                "May not catch quick changes if they happen between checks.\n" +
                "Aggressive settings may degrade performance."
        )
        
        setting = self.readSetting("viewRefreshPeriodicallyChecks")
        self.panelThumbnailsRefreshPeriodicallyChecksLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyChecksLabel = QLabel("Check", self.panel)
        self.panelThumbnailsRefreshPeriodicallyChecksValue = QLabel(setting, self.panel)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider = QSlider(Qt.Horizontal, self.panel)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setRange(0, 9)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setTickPosition(QSlider.NoTicks)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setTickInterval(1)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setValue(
                self.convertThumbnailsRefreshPeriodicallyChecksSettingToSlider(setting)
        )
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setToolTip("Number of times each second the image is checked for activity.")
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setEnabled(self.panelThumbnailsRefreshPeriodicallyCheckBox.isChecked())
        
        setting = self.readSetting("viewRefreshPeriodicallyDelay")
        self.panelThumbnailsRefreshPeriodicallyDelayLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyDelayLabel = QLabel("Delay by", self.panel)
        self.panelThumbnailsRefreshPeriodicallyDelayValue = QLabel(setting, self.panel)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider = QSlider(Qt.Horizontal, self.panel)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setRange(0, 10)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setTickPosition(QSlider.NoTicks)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setTickInterval(1)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setValue(
                self.convertThumbnailsRefreshPeriodicallyDelaySettingToSlider(setting)
        )
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setToolTip("How long after the last detected change to refresh the thumbnail.")
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setEnabled(self.panelThumbnailsRefreshPeriodicallyCheckBox.isChecked())
        
        self.panelMiscLabel = QLabel("Miscellaneous", self.panel)
        self.panelIdAutoDisambiguateCopiesCheckBox = QCheckBox("Auto disambiguate document ID's (modifies file)")
        self.panelIdAutoDisambiguateCopiesCheckBox.stateChanged.connect(self.changedIdAutoDisambiguateCopies)
        self.panelIdAutoDisambiguateCopiesCheckBox.setChecked(self.readSetting("idAutoDisambiguateCopies") == "true")
        self.panelIdAutoDisambiguateCopiesCheckBox.setToolTip(
                "ODD uses a unique ID supplied by Krita to identify documents.\n" +
                "When you 'create copy from current image', This copy does not receive a new ID.\n" +
                "This means ODD can't distinguish the original from the copy.\n" +
                "This setting permits ODD to annotate documents with an additional unique identifier.\n" +
                "If you save the image as a krita document, this data is also saved.\n" +
                "If you open it again at a later time, krita will provide it a new unique ID,\n" +
                "and ODD will remove the redudant annotation. You can then save the image again to remove it from the file."
        )
        
        self.panelDisplayButtonGroup.addButton(self.panelDisplayThumbnailsButton)
        self.panelDisplayButtonGroup.addButton(self.panelDisplayTextButton)
        settingDisplay = self.readSetting("viewDisplay")
        self.panelDisplayThumbnailsButton.setChecked(settingDisplay=="thumbnails")
        self.panelDisplayTextButton.setChecked(settingDisplay=="text")
        self.panelDisplayThumbnailsButton.clicked.connect(self.setDisplayToThumbnails)
        self.panelDisplayTextButton.clicked.connect(self.setDisplayToText)
        settingDirection = self.readSetting("viewDirection")
        self.panelDirectionButtonGroup.addButton(self.panelDirectionHorizontalButton)
        self.panelDirectionButtonGroup.addButton(self.panelDirectionVerticalButton)
        self.panelDirectionButtonGroup.addButton(self.panelDirectionAutoButton)
        self.panelDirectionHorizontalButton.setChecked(settingDirection=="horizontal")
        self.panelDirectionVerticalButton.setChecked(settingDirection=="vertical")
        self.panelDirectionAutoButton.setChecked(settingDirection=="auto")
        self.panelDirectionHorizontalButton.clicked.connect(self.setDirectionToHorizontal)
        self.panelDirectionVerticalButton.clicked.connect(self.setDirectionToVertical)
        self.panelDirectionAutoButton.clicked.connect(self.setDirectionToAuto)
        
        self.panelLayout.addWidget(self.panelDisplayLabel)
        self.panelLayout.addWidget(self.panelDisplayThumbnailsButton)
        self.panelLayout.addWidget(self.panelDisplayTextButton)
        self.panelLayout.addWidget(self.panelDirectionLabel)
        self.panelLayout.addWidget(self.panelDirectionHorizontalButton)
        self.panelLayout.addWidget(self.panelDirectionVerticalButton)
        self.panelLayout.addWidget(self.panelDirectionAutoButton)
        self.panelLayout.addWidget(self.panelThumbnailsLabel)
        self.panelThumbnailsScaleLayout.addWidget(self.panelThumbnailsScaleLabel)
        self.panelThumbnailsScaleLayout.addWidget(self.panelThumbnailsScaleValue)
        self.panelThumbnailsScaleLayout.addWidget(self.panelThumbnailsScaleSlider)
        self.panelThumbnailsScaleLayout.setStretch(0, 2)
        self.panelThumbnailsScaleLayout.setStretch(1, 2)
        self.panelThumbnailsScaleLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsScaleLayout)
        self.panelThumbnailsTooltipsLayout.addWidget(self.panelThumbnailsTooltipsLabel)
        self.panelThumbnailsTooltipsLayout.addWidget(self.panelThumbnailsTooltipsValue)
        self.panelThumbnailsTooltipsLayout.addWidget(self.panelThumbnailsTooltipsSlider)
        self.panelThumbnailsTooltipsLayout.setStretch(0, 2)
        self.panelThumbnailsTooltipsLayout.setStretch(1, 2)
        self.panelThumbnailsTooltipsLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsTooltipsLayout)
        self.panelLayout.addWidget(self.panelThumbnailsRefreshOnSaveCheckBox)
        self.panelLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyCheckBox)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyChecksLabel)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyChecksValue)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyChecksSlider)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(0, 2)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(1, 2)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsRefreshPeriodicallyChecksLayout)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyDelayLabel)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyDelayValue)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyDelaySlider)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(0, 2)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(1, 2)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsRefreshPeriodicallyDelayLayout)
        self.panelLayout.addWidget(self.panelMiscLabel)
        self.panelLayout.addWidget(self.panelIdAutoDisambiguateCopiesCheckBox)
        self.panel.setLayout(self.panelLayout)
        self.panel.setMinimumWidth(384)
        
        self.panelThumbnailsScaleSlider.valueChanged.connect(self.changedPanelThumbnailsScaleSlider)
        self.panelThumbnailsTooltipsSlider.valueChanged.connect(self.changedPanelThumbnailsTooltipsSlider)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.valueChanged.connect(self.changedPanelThumbnailsRefreshPeriodicallyChecksSlider)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.valueChanged.connect(self.changedPanelThumbnailsRefreshPeriodicallyDelaySlider)

    def clickedViewButton(self):
        btnTopLeft = self.odd.baseWidget.mapToGlobal(self.odd.viewButton.frameGeometry().topLeft())
        btnBottomLeft = self.odd.baseWidget.mapToGlobal(self.odd.viewButton.frameGeometry().bottomLeft())
        btnBottomRight = self.odd.baseWidget.mapToGlobal(self.odd.viewButton.frameGeometry().bottomRight())
        btnTopRight = self.odd.baseWidget.mapToGlobal(self.odd.viewButton.frameGeometry().topRight())
        btnCenter = (btnTopLeft+btnBottomRight)/2
        
        self.panel.show()
        self.panel.layout().invalidate()
        self.panel.hide()
        panelSize = self.panel.size()
        
        pos = QPoint(0, 0)
        
        if hasattr(self, "screen"):
            # work out which side of the widget has the most space and put the view panel there.
            screen = self.screen()
            screenTopLeft = screen.availableGeometry().topLeft()
            screenBottomRight = screen.availableGeometry().bottomRight()
            screenCenter = (screenTopLeft+screenBottomRight)/2
            if btnCenter.x() < screenCenter.x():
                if btnCenter.y() < screenCenter.y():
                    # top left
                    pos = btnBottomLeft
                else:
                    # bottom left
                    pos = btnTopLeft - QPoint(0, panelSize.height())
            else:
                if btnCenter.y() < screenCenter.y():
                    # top right
                    pos = btnBottomRight - QPoint(panelSize.width(), 0)
                else:
                    # bottom right
                    pos = btnTopRight - QPoint(panelSize.width(), panelSize.height())
        else:
            # fallback to using dock area
            if self.odd.dockLocation == Qt.LeftDockWidgetArea:
                # bottom left
                pos = btnTopLeft - QPoint(0, panelSize.height())
            elif self.odd.dockLocation == Qt.TopDockWidgetArea:
                # top right
                pos = btnBottomRight - QPoint(panelSize.width(), 0)
            else:
                # bottom right
                pos = btnTopRight - QPoint(panelSize.width(), panelSize.height())
        
        self.panel.move(pos)
        self.panel.show()
