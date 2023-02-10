from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QScreen
from PyQt5.QtWidgets import QWidget, QBoxLayout, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QFrame
from krita import *

class OpenDocumentsViewSettings:
    Settings = {
            "viewDirection": {
                    "default":"auto",
            },
            "viewDisplay": {
                    "default":"thumbnails",
            },
            "viewRefreshOnSave": {
                    "default":"true",
            },
            "viewRefreshPeriodically": {
                    "default":"false",
            },
            "viewRefreshPeriodicallyChecks": {
                    "default":"15/sec",
                    "strings":["1/sec","2/sec","3/sec","4/sec","5/sec","8/sec","10/sec","15/sec","20/sec","30/sec"],
                    "values" :[1000, 500, 333, 250, 200, 125, 100, 67, 50, 33],
            },
            "viewRefreshPeriodicallyDelay": {
                    "default":"2sec",
                    "strings":["1/2sec", "1sec", "1.5sec", "2sec", "3sec", "4sec", "5sec", "7sec", "10sec", "20sec", "1min"],
                    "values" :[500, 1000, 1500, 2000, 3000, 4000, 5000, 7000, 10000, 20000, 60000],
            },
            "viewThumbnailsDisplayScale": {
                    "default":"1.00",
            },
            "viewThumbnailsRenderScale": {
                    "default":"1",
                    "strings":["1/16", "1/8", "1/4", "1/2", "1"],
                    "values" :[1.0/16.0, 1.0/8.0, 1.0/4.0, 1.0/2.0, 1],
            },
            "viewTooltipThumbnailLimit": {
                    "default":"≤4096px²",
                    "strings":["never","≤128px²","≤256px²","≤512px²","≤1024px²","≤2048px²","≤4096px²","≤8192px²","≤16384px²","always"],
                    "values" :[0, 128*128, 256*256, 512*512, 1024*1024, 2048*2048, 4096*4096, 8192*8192, 16384*16384, float("inf")],
            },
            "viewTooltipThumbnailSize": {
                    "default":"128px",
                    "strings":["64px", "96px", "128px", "160px", "192px", "256px", "384px", "512px"],
                    "values" :[64, 96, 128, 160, 192, 256, 384, 512],
            },
            "idAutoDisambiguateCopies": {
                    "default":"false",
            },
            "thumbnailUseProjectionMethod": {
                    "default":"true",
            },
    }
    
    def __init__(self, odd):
        self.odd = odd
    
    def readSetting(self, setting):
        if not setting in self.Settings:
            return
        return Application.readSetting("OpenDocumentsDocker", setting, self.Settings[setting]["default"])
    
    def writeSetting(self, setting, value):
        if not setting in self.Settings:
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
    
    def convertSettingStringToValue(self, settingName, string):
        setting = self.Settings[settingName]
        if string in setting["strings"]:
            return setting["strings"].index(string)
        else:
            return setting["strings"].index(setting["default"])
    
    def convertSettingValueToString(self, settingName, value):
        setting = self.Settings[settingName]
        if value >= 0 and value < len(setting["strings"]):
            return setting["strings"][value]
        else:
            return setting["default"]
    
    def convertThumbnailsRenderScaleStringToValue(self, string):
        return self.convertSettingStringToValue("viewThumbnailsRenderScale", string)
    
    def convertThumbnailsRenderScaleValueToString(self, value):
        return self.convertSettingValueToString("viewThumbnailsRenderScale", value)
    
    def convertTooltipThumbnailLimitStringToValue(self, string):
        return self.convertSettingStringToValue("viewTooltipThumbnailLimit", string)
    
    def convertTooltipThumbnailLimitValueToString(self, value):
        return self.convertSettingValueToString("viewTooltipThumbnailLimit", value)
    
    def convertTooltipThumbnailSizeStringToValue(self, string):
        return self.convertSettingStringToValue("viewTooltipThumbnailSize", string)
    
    def convertTooltipThumbnailSizeValueToString(self, value):
        return self.convertSettingValueToString("viewTooltipThumbnailSize", value)
    
    def changedPanelThumbnailsDisplayScaleSlider(self, value):
        setting = "{:4.2f}".format(value * 0.05)
        self.panelThumbnailsDisplayScaleValue.setText(setting)
        self.writeSetting("viewThumbnailsDisplayScale", setting)
        # quick resize thumbs for visual feedback
        l = self.odd.list
        w = self.odd.calculateWidthForThumbnail()
        itemCount = l.count()
        for i in range(itemCount):
            item = l.item(i)
            t = item.data(Qt.DecorationRole)
            item.setData(Qt.DecorationRole, t.scaledToWidth(w))
        
        self.startRefreshAllDelayTimer()
    
    def changedPanelThumbnailsRenderScaleSlider(self, value):
        setting = self.convertThumbnailsRenderScaleValueToString(value)
        self.panelThumbnailsRenderScaleValue.setText(setting)
        self.writeSetting("viewThumbnailsRenderScale", setting)
        
        self.startRefreshAllDelayTimer()
    
    def changedPanelTooltipThumbnailLimitSlider(self, value):
        setting = self.convertTooltipThumbnailLimitValueToString(value)
        self.panelTooltipThumbnailLimitValue.setText(setting)
        self.writeSetting("viewTooltipThumbnailLimit", setting)
        if value != 0:
            if hasattr(self, "panelTooltipThumbnailSizeSlider"):
                self.panelTooltipThumbnailSizeSlider.setEnabled(True)
        else:
            if hasattr(self, "panelTooltipThumbnailSizeSlider"):
                self.panelTooltipThumbnailSizeSlider.setEnabled(False)
    
    def changedPanelTooltipThumbnailSizeSlider(self, value):
        setting = self.convertTooltipThumbnailSizeValueToString(value)
        self.panelTooltipThumbnailSizeValue.setText(setting)
        self.writeSetting("viewTooltipThumbnailSize", setting)
    
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
    
    def changedThumbnailUseProjectionMethod(self, state):
        setting = str(state==2).lower()
        print("changedThumbnailUseProjectionMethod to", setting)
        self.writeSetting("thumbnailUseProjectionMethod", setting)
        if state == 2:
            if hasattr(self, "panelThumbnailsRenderScaleSlider"):
                self.panelThumbnailsRenderScaleSlider.setEnabled(False)
        else:
            if hasattr(self, "panelThumbnailsRenderScaleSlider"):
                self.panelThumbnailsRenderScaleSlider.setEnabled(True)
        
        self.startRefreshAllDelayTimer()
        
    def startRefreshAllDelayTimer(self):
        if not hasattr(self.odd, "refreshAllDelay"):
            return
        delay = self.odd.refreshAllDelay
        if delay.isActive():
            delay.stop()
        delay.start()
    
    def convertThumbnailsRefreshPeriodicallyChecksStringToValue(self, string):
        return self.convertSettingStringToValue("viewRefreshPeriodicallyChecks", string)
    
    def convertThumbnailsRefreshPeriodicallyChecksValueToString(self, value):
        return self.convertSettingValueToString("viewRefreshPeriodicallyChecks", value)
    
    def convertThumbnailsRefreshPeriodicallyDelayStringToValue(self, string):
        return self.convertSettingStringToValue("viewRefreshPeriodicallyDelay", string)
    
    def convertThumbnailsRefreshPeriodicallyDelayValueToString(self, value):
        return self.convertSettingValueToString("viewRefreshPeriodicallyDelay", value)
    
    def changedPanelThumbnailsRefreshPeriodicallyChecksSlider(self, value):
        setting = self.convertThumbnailsRefreshPeriodicallyChecksValueToString(value)
        self.panelThumbnailsRefreshPeriodicallyChecksValue.setText(setting)
        self.odd.imageChangeDetectionTimer.setInterval(
                self.Settings["viewRefreshPeriodicallyChecks"]["values"][self.panelThumbnailsRefreshPeriodicallyChecksSlider.value()]
        )
        self.writeSetting("viewRefreshPeriodicallyChecks", setting)
    
    def changedPanelThumbnailsRefreshPeriodicallyDelaySlider(self, value):
        setting = self.convertThumbnailsRefreshPeriodicallyDelayValueToString(value)
        self.panelThumbnailsRefreshPeriodicallyDelayValue.setText(setting)
        self.odd.refreshTimer.setInterval(
                self.Settings["viewRefreshPeriodicallyDelay"]["values"][self.panelThumbnailsRefreshPeriodicallyDelaySlider.value()]
        )
        self.writeSetting("viewRefreshPeriodicallyDelay", setting)
        
    def createPanel(self):
        app = Application
        
        self.panel = QWidget(self.odd, Qt.Popup)
        self.panelLayout = QVBoxLayout()
        
        self.panelDisplayButtonGroup = QButtonGroup(self.panel)
        self.panelDirectionButtonGroup = QButtonGroup(self.panel)
        
        self.panelListHeading = QHBoxLayout()
        self.panelListHeadingLabel = QLabel("List", self.panel)
        self.panelListHeadingLine = QLabel("", self.panel)
        self.panelListHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.panelDisplayLabel = QLabel("Display", self.panel)
        self.panelDisplayThumbnailsButton = QRadioButton("Thumbnails", self.panel)
        self.panelDisplayTextButton = QRadioButton("Text", self.panel)
        
        self.panelDirectionLabel = QLabel("Direction", self.panel)
        self.panelDirectionHorizontalButton = QRadioButton("Horizontal", self.panel)
        self.panelDirectionVerticalButton = QRadioButton("Vertical", self.panel)
        self.panelDirectionAutoButton = QRadioButton("Auto", self.panel)
        self.panelDirectionAutoButton.setToolTip("The list will be arranged on its longest side.")
        
        self.panelThumbnailsLabel = QLabel("Thumbnails", self.panel)
        
        self.panelThumbnailUseProjectionMethodCheckBox = QCheckBox("Use projection method")
        self.panelThumbnailUseProjectionMethodCheckBox.stateChanged.connect(self.changedThumbnailUseProjectionMethod)
        self.panelThumbnailUseProjectionMethodCheckBox.setChecked(self.readSetting("thumbnailUseProjectionMethod") == "true")
        self.panelThumbnailUseProjectionMethodCheckBox.setToolTip(
                "If enabled, ODD will generate thumbnails with the projection method.\n" +
                "If disabled, ODD will use the thumbnail method.\n" +
                "Projection should be faster. If there are no issues, leave this enabled."
        )
        
        setting = self.readSetting("viewThumbnailsDisplayScale")
        self.panelThumbnailsDisplayScaleLayout = QHBoxLayout()
        self.panelThumbnailsDisplayScaleLabel = QLabel("Display scale", self.panel)
        self.panelThumbnailsDisplayScaleValue = QLabel(setting, self.panel)
        self.panelThumbnailsDisplayScaleSlider = QSlider(Qt.Horizontal, self.panel)
        self.panelThumbnailsDisplayScaleSlider.setRange(1, 20)
        self.panelThumbnailsDisplayScaleSlider.setTickPosition(QSlider.NoTicks)
        self.panelThumbnailsDisplayScaleSlider.setTickInterval(1)
        self.panelThumbnailsDisplayScaleSlider.setValue(round(float(setting)*20))
        
        setting = self.readSetting("viewThumbnailsRenderScale")
        self.panelThumbnailsRenderScaleLayout = QHBoxLayout()
        self.panelThumbnailsRenderScaleLabel = QLabel("Render scale", self.panel)
        self.panelThumbnailsRenderScaleValue = QLabel(setting, self.panel)
        self.panelThumbnailsRenderScaleSlider = QSlider(Qt.Horizontal, self.panel)
        self.panelThumbnailsRenderScaleSlider.setRange(0, len(self.Settings["viewThumbnailsRenderScale"]["values"])-1)
        self.panelThumbnailsRenderScaleSlider.setTickPosition(QSlider.NoTicks)
        self.panelThumbnailsRenderScaleSlider.setTickInterval(1)
        self.panelThumbnailsRenderScaleSlider.setValue(
                self.convertThumbnailsRenderScaleStringToValue(setting)
        )
        self.panelThumbnailsRenderScaleSlider.setToolTip(
                "Thumbnails in the list can be generated at a reduced size then scaled up.\n" +
                "This can improve performance when using the thumbnail method."
        )
        self.panelThumbnailsRenderScaleSlider.setEnabled(not self.panelThumbnailUseProjectionMethodCheckBox.isChecked())
        
        self.panelTooltipsHeading = QHBoxLayout()
        self.panelTooltipsHeadingLabel = QLabel("Tooltips", self.panel)
        self.panelTooltipsHeadingLine = QLabel("", self.panel)
        self.panelTooltipsHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        setting = self.readSetting("viewTooltipThumbnailLimit")
        self.panelTooltipThumbnailLimitLayout = QHBoxLayout()
        self.panelTooltipThumbnailLimitLabel = QLabel("Limit", self.panel)
        self.panelTooltipThumbnailLimitValue = QLabel(setting, self.panel)
        self.panelTooltipThumbnailLimitSlider = QSlider(Qt.Horizontal, self.panel)
        self.panelTooltipThumbnailLimitSlider.setRange(0, len(self.Settings["viewTooltipThumbnailLimit"]["values"])-1)
        self.panelTooltipThumbnailLimitSlider.setTickPosition(QSlider.NoTicks)
        self.panelTooltipThumbnailLimitSlider.setTickInterval(1)
        self.panelTooltipThumbnailLimitSlider.setValue(
                self.convertTooltipThumbnailLimitStringToValue(setting)
        )
        self.panelTooltipThumbnailLimitSlider.setToolTip("Thumbnails in tooltips will be generated for images up to the chosen size.")
        
        setting = self.readSetting("viewTooltipThumbnailSize")
        self.panelTooltipThumbnailSizeLayout = QHBoxLayout()
        self.panelTooltipThumbnailSizeLabel = QLabel("Size", self.panel)
        self.panelTooltipThumbnailSizeValue = QLabel(setting, self.panel)
        self.panelTooltipThumbnailSizeSlider = QSlider(Qt.Horizontal, self.panel)
        self.panelTooltipThumbnailSizeSlider.setRange(0, len(self.Settings["viewTooltipThumbnailSize"]["values"])-1)
        self.panelTooltipThumbnailSizeSlider.setTickPosition(QSlider.NoTicks)
        self.panelTooltipThumbnailSizeSlider.setTickInterval(1)
        self.panelTooltipThumbnailSizeSlider.setValue(
                self.convertTooltipThumbnailSizeStringToValue(setting)
        )
        self.panelTooltipThumbnailSizeSlider.setEnabled(self.panelTooltipThumbnailLimitSlider.value() != 0)
        
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
        self.panelThumbnailsRefreshPeriodicallyChecksLabel = QLabel("Checks", self.panel)
        self.panelThumbnailsRefreshPeriodicallyChecksValue = QLabel(setting, self.panel)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider = QSlider(Qt.Horizontal, self.panel)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setRange(0, len(self.Settings["viewRefreshPeriodicallyChecks"]["values"])-1)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setTickPosition(QSlider.NoTicks)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setTickInterval(1)
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setValue(
                self.convertThumbnailsRefreshPeriodicallyChecksStringToValue(setting)
        )
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setToolTip("Number of times each second the image is checked for activity.")
        self.panelThumbnailsRefreshPeriodicallyChecksSlider.setEnabled(self.panelThumbnailsRefreshPeriodicallyCheckBox.isChecked())
        
        setting = self.readSetting("viewRefreshPeriodicallyDelay")
        self.panelThumbnailsRefreshPeriodicallyDelayLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyDelayLabel = QLabel("Delay by", self.panel)
        self.panelThumbnailsRefreshPeriodicallyDelayValue = QLabel(setting, self.panel)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider = QSlider(Qt.Horizontal, self.panel)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setRange(0, len(self.Settings["viewRefreshPeriodicallyDelay"]["values"])-1)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setTickPosition(QSlider.NoTicks)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setTickInterval(1)
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setValue(
                self.convertThumbnailsRefreshPeriodicallyDelayStringToValue(setting)
        )
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setToolTip("How long after the last detected change to refresh the thumbnail.")
        self.panelThumbnailsRefreshPeriodicallyDelaySlider.setEnabled(self.panelThumbnailsRefreshPeriodicallyCheckBox.isChecked())
        
        self.panelMiscHeading = QHBoxLayout()
        self.panelMiscHeadingLabel = QLabel("Miscellaneous", self.panel)
        self.panelMiscHeadingLine = QLabel("", self.panel)
        self.panelMiscHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
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
        
        self.panelListHeading.addWidget(self.panelListHeadingLabel)
        self.panelListHeading.addWidget(self.panelListHeadingLine)
        self.panelListHeading.setStretch(0, 1)
        self.panelListHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelListHeading)
        self.panelLayout.addWidget(self.panelDisplayLabel)
        self.panelLayout.addWidget(self.panelDisplayThumbnailsButton)
        self.panelLayout.addWidget(self.panelDisplayTextButton)
        self.panelLayout.addWidget(self.panelDirectionLabel)
        self.panelLayout.addWidget(self.panelDirectionHorizontalButton)
        self.panelLayout.addWidget(self.panelDirectionVerticalButton)
        self.panelLayout.addWidget(self.panelDirectionAutoButton)
        self.panelLayout.addWidget(self.panelThumbnailsLabel)
        self.panelLayout.addWidget(self.panelThumbnailUseProjectionMethodCheckBox)
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.panelThumbnailsDisplayScaleLabel)
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.panelThumbnailsDisplayScaleValue)
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.panelThumbnailsDisplayScaleSlider)
        self.panelThumbnailsDisplayScaleLayout.setStretch(0, 2)
        self.panelThumbnailsDisplayScaleLayout.setStretch(1, 2)
        self.panelThumbnailsDisplayScaleLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsDisplayScaleLayout)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.panelThumbnailsRenderScaleLabel)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.panelThumbnailsRenderScaleValue)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.panelThumbnailsRenderScaleSlider)
        self.panelThumbnailsRenderScaleLayout.setStretch(0, 2)
        self.panelThumbnailsRenderScaleLayout.setStretch(1, 2)
        self.panelThumbnailsRenderScaleLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsRenderScaleLayout)
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
        self.panelTooltipsHeading.addWidget(self.panelTooltipsHeadingLabel)
        self.panelTooltipsHeading.addWidget(self.panelTooltipsHeadingLine)
        self.panelTooltipsHeading.setStretch(0, 1)
        self.panelTooltipsHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelTooltipsHeading)
        self.panelTooltipThumbnailLimitLayout.addWidget(self.panelTooltipThumbnailLimitLabel)
        self.panelTooltipThumbnailLimitLayout.addWidget(self.panelTooltipThumbnailLimitValue)
        self.panelTooltipThumbnailLimitLayout.addWidget(self.panelTooltipThumbnailLimitSlider)
        self.panelTooltipThumbnailLimitLayout.setStretch(0, 2)
        self.panelTooltipThumbnailLimitLayout.setStretch(1, 2)
        self.panelTooltipThumbnailLimitLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelTooltipThumbnailLimitLayout)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.panelTooltipThumbnailSizeLabel)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.panelTooltipThumbnailSizeValue)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.panelTooltipThumbnailSizeSlider)
        self.panelTooltipThumbnailSizeLayout.setStretch(0, 2)
        self.panelTooltipThumbnailSizeLayout.setStretch(1, 2)
        self.panelTooltipThumbnailSizeLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelTooltipThumbnailSizeLayout)
        self.panelMiscHeading.addWidget(self.panelMiscHeadingLabel)
        self.panelMiscHeading.addWidget(self.panelMiscHeadingLine)
        self.panelMiscHeading.setStretch(0, 1)
        self.panelMiscHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelMiscHeading)
        self.panelLayout.addWidget(self.panelIdAutoDisambiguateCopiesCheckBox)
        self.panel.setLayout(self.panelLayout)
        self.panel.setMinimumWidth(384)
        
        self.panelThumbnailsDisplayScaleSlider.valueChanged.connect(self.changedPanelThumbnailsDisplayScaleSlider)
        self.panelThumbnailsRenderScaleSlider.valueChanged.connect(self.changedPanelThumbnailsRenderScaleSlider)
        self.panelTooltipThumbnailLimitSlider.valueChanged.connect(self.changedPanelTooltipThumbnailLimitSlider)
        self.panelTooltipThumbnailSizeSlider.valueChanged.connect(self.changedPanelTooltipThumbnailSizeSlider)
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
        
        if hasattr(self.odd, "screen"):
            # work out which side of the widget has the most space and put the view panel there.
            screen = self.odd.screen()
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
