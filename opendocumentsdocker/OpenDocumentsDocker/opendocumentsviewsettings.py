from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QScreen
from PyQt5.QtWidgets import QWidget, QBoxLayout, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QFrame
from krita import *

class OpenDocumentsViewSettings:
    # Settings Data
    SD = {
            "viewDirection": {
                    "default":"auto",
                    "ui": {
                            "btngrp":None,
                            "btnHorizontal":None,
                            "btnVertical":None,
                            "btnAuto":None,
                    },
            },
            "viewDisplay": {
                    "default":"thumbnails",
                    "ui": {
                            "btngrp":None,
                            "btnThumbnails":None,
                            "btnText":None,
                    },
            },
            "viewRefreshOnSave": {
                    "default":"true",
                    "ui": {
                            "btn":None,
                    },
            },
            "viewRefreshPeriodically": {
                    "default":"false",
                    "ui": {
                            "btn":None,
                    },
            },
            "viewRefreshPeriodicallyChecks": {
                    "default":"15/sec",
                    "strings":["1/sec","2/sec","3/sec","4/sec","5/sec","8/sec","10/sec","15/sec","20/sec","30/sec"],
                    "values" :[1000, 500, 333, 250, 200, 125, 100, 67, 50, 33],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "viewRefreshPeriodicallyDelay": {
                    "default":"2sec",
                    "strings":["1/2sec", "1sec", "1.5sec", "2sec", "3sec", "4sec", "5sec", "7sec", "10sec", "20sec", "1min"],
                    "values" :[500, 1000, 1500, 2000, 3000, 4000, 5000, 7000, 10000, 20000, 60000],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "viewThumbnailsDisplayScale": {
                    "default":"1.00",
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "viewThumbnailsRenderScale": {
                    "default":"1",
                    "strings":["1/16", "1/8", "1/4", "1/2", "1"],
                    "values" :[1.0/16.0, 1.0/8.0, 1.0/4.0, 1.0/2.0, 1],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "viewTooltipThumbnailLimit": {
                    "default":"≤4096px²",
                    "strings":["never","≤128px²","≤256px²","≤512px²","≤1024px²","≤2048px²","≤4096px²","≤8192px²","≤16384px²","always"],
                    "values" :[0, 128*128, 256*256, 512*512, 1024*1024, 2048*2048, 4096*4096, 8192*8192, 16384*16384, float("inf")],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "viewTooltipThumbnailSize": {
                    "default":"128px",
                    "strings":["64px", "96px", "128px", "160px", "192px", "256px", "384px", "512px"],
                    "values" :[64, 96, 128, 160, 192, 256, 384, 512],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "idAutoDisambiguateCopies": {
                    "default":"false",
                    "ui": {
                            "btn":None,
                    },
            },
            "thumbnailUseProjectionMethod": {
                    "default":"true",
                    "ui": {
                            "btn":None,
                    },
            },
    }
    
    def __init__(self, odd):
        self.odd = odd
        print(self.SD["viewDirection"])
    
    def readSetting(self, setting):
        if not setting in self.SD:
            return
        return Application.readSetting("OpenDocumentsDocker", setting, self.SD[setting]["default"])
    
    def writeSetting(self, setting, value):
        if not setting in self.SD:
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
        setting = self.SD[settingName]
        if string in setting["strings"]:
            return setting["strings"].index(string)
        else:
            return setting["strings"].index(setting["default"])
    
    def convertSettingValueToString(self, settingName, value):
        setting = self.SD[settingName]
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
        self.SD["viewThumbnailsDisplayScale"]["ui"]["value"].setText(setting)
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
        self.SD["viewThumbnailsRenderScale"]["ui"]["value"].setText(setting)
        self.writeSetting("viewThumbnailsRenderScale", setting)
        
        self.startRefreshAllDelayTimer()
    
    def changedPanelTooltipThumbnailLimitSlider(self, value):
        setting = self.convertTooltipThumbnailLimitValueToString(value)
        self.SD["viewTooltipThumbnailLimit"]["ui"]["value"].setText(setting)
        self.writeSetting("viewTooltipThumbnailLimit", setting)
        if self.SD["viewTooltipThumbnailSize"]["ui"]["slider"]:
            if value != 0:
                self.SD["viewTooltipThumbnailSize"]["ui"]["slider"].setEnabled(True)
            else:
                self.SD["viewTooltipThumbnailSize"]["ui"]["slider"].setEnabled(False)
    
    def changedPanelTooltipThumbnailSizeSlider(self, value):
        setting = self.convertTooltipThumbnailSizeValueToString(value)
        self.SD["viewTooltipThumbnailSize"]["ui"]["value"].setText(setting)
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
            if self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"]:
                self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].setEnabled(True)
                self.SD["viewRefreshPeriodicallyDelay" ]["ui"]["slider"].setEnabled(True)
            self.odd.imageChangeDetectionTimer.start()
        else:
            if self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"]:
                self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].setEnabled(False)
                self.SD["viewRefreshPeriodicallyDelay" ]["ui"]["slider"].setEnabled(False)
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
        if self.SD["viewThumbnailsRenderScale"]["ui"]["slider"]:
            if state == 2:
                self.SD["viewThumbnailsRenderScale"]["ui"]["slider"].setEnabled(False)
            else:
                self.SD["viewThumbnailsRenderScale"]["ui"]["slider"].setEnabled(True)
        
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
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["value"].setText(setting)
        self.odd.imageChangeDetectionTimer.setInterval(
                self.SD["viewRefreshPeriodicallyChecks"]["values"][self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].value()]
        )
        self.writeSetting("viewRefreshPeriodicallyChecks", setting)
    
    def changedPanelThumbnailsRefreshPeriodicallyDelaySlider(self, value):
        setting = self.convertThumbnailsRefreshPeriodicallyDelayValueToString(value)
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["value"].setText(setting)
        self.odd.refreshTimer.setInterval(
                self.SD["viewRefreshPeriodicallyDelay"]["values"][self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"].value()]
        )
        self.writeSetting("viewRefreshPeriodicallyDelay", setting)
        
    def createPanel(self):
        app = Application
        
        self.panel = QWidget(self.odd, Qt.Popup)
        self.panelLayout = QVBoxLayout()
        
        self.SD["viewDisplay"]["ui"]["btngrp"] = QButtonGroup(self.panel)
        self.SD["viewDirection"]["ui"]["btngrp"] = QButtonGroup(self.panel)
        
        self.panelListHeading = QHBoxLayout()
        self.panelListHeadingLabel = QLabel("List", self.panel)
        self.panelListHeadingLine = QLabel("", self.panel)
        self.panelListHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.panelDisplayLabel = QLabel("Display", self.panel)
        self.SD["viewDisplay"]["ui"]["btnThumbnails"] = QRadioButton("Thumbnails", self.panel)
        self.SD["viewDisplay"]["ui"]["btnText"      ] = QRadioButton("Text", self.panel)
        
        self.panelDirectionLabel = QLabel("Direction", self.panel)
        self.SD["viewDirection"]["ui"]["btnHorizontal"] = QRadioButton("Horizontal", self.panel)
        self.SD["viewDirection"]["ui"]["btnVertical"  ] = QRadioButton("Vertical", self.panel)
        self.SD["viewDirection"]["ui"]["btnAuto"      ] = QRadioButton("Auto", self.panel)
        self.SD["viewDirection"]["ui"]["btnAuto"      ].setToolTip("The list will be arranged on its longest side.")
        
        self.panelThumbnailsLabel = QLabel("Thumbnails", self.panel)
        
        self.SD["thumbnailUseProjectionMethod"]["ui"]["btn"] = QCheckBox("Use projection method")
        self.SD["thumbnailUseProjectionMethod"]["ui"]["btn"].stateChanged.connect(self.changedThumbnailUseProjectionMethod)
        self.SD["thumbnailUseProjectionMethod"]["ui"]["btn"].setChecked(self.readSetting("thumbnailUseProjectionMethod") == "true")
        self.SD["thumbnailUseProjectionMethod"]["ui"]["btn"].setToolTip(
                "If enabled, ODD will generate thumbnails with the projection method.\n" +
                "If disabled, ODD will use the thumbnail method.\n" +
                "Projection should be faster. If there are no issues, leave this enabled."
        )
        
        setting = self.readSetting("viewThumbnailsDisplayScale")
        self.panelThumbnailsDisplayScaleLayout = QHBoxLayout()
        self.panelThumbnailsDisplayScaleLabel = QLabel("Display scale", self.panel)
        self.SD["viewThumbnailsDisplayScale"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["viewThumbnailsDisplayScale"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["viewThumbnailsDisplayScale"]["ui"]["slider"].setRange(1, 20)
        self.SD["viewThumbnailsDisplayScale"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["viewThumbnailsDisplayScale"]["ui"]["slider"].setTickInterval(1)
        self.SD["viewThumbnailsDisplayScale"]["ui"]["slider"].setValue(round(float(setting)*20))
        
        setting = self.readSetting("viewThumbnailsRenderScale")
        self.panelThumbnailsRenderScaleLayout = QHBoxLayout()
        self.panelThumbnailsRenderScaleLabel = QLabel("Render scale", self.panel)
        self.SD["viewThumbnailsRenderScale"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["viewThumbnailsRenderScale"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["viewThumbnailsRenderScale"]["ui"]["slider"].setRange(0, len(self.SD["viewThumbnailsRenderScale"]["values"])-1)
        self.SD["viewThumbnailsRenderScale"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["viewThumbnailsRenderScale"]["ui"]["slider"].setTickInterval(1)
        self.SD["viewThumbnailsRenderScale"]["ui"]["slider"].setValue(
                self.convertThumbnailsRenderScaleStringToValue(setting)
        )
        self.SD["viewThumbnailsRenderScale"]["ui"]["slider"].setToolTip(
                "Thumbnails in the list can be generated at a reduced size then scaled up.\n" +
                "This can improve performance when using the thumbnail method."
        )
        self.SD["viewThumbnailsRenderScale"]["ui"]["slider"].setEnabled(not self.SD["thumbnailUseProjectionMethod"]["ui"]["btn"].isChecked())
        
        self.panelTooltipsHeading = QHBoxLayout()
        self.panelTooltipsHeadingLabel = QLabel("Tooltips", self.panel)
        self.panelTooltipsHeadingLine = QLabel("", self.panel)
        self.panelTooltipsHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        setting = self.readSetting("viewTooltipThumbnailLimit")
        self.panelTooltipThumbnailLimitLayout = QHBoxLayout()
        self.panelTooltipThumbnailLimitLabel = QLabel("Limit", self.panel)
        self.SD["viewTooltipThumbnailLimit"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["viewTooltipThumbnailLimit"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["viewTooltipThumbnailLimit"]["ui"]["slider"].setRange(0, len(self.SD["viewTooltipThumbnailLimit"]["values"])-1)
        self.SD["viewTooltipThumbnailLimit"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["viewTooltipThumbnailLimit"]["ui"]["slider"].setTickInterval(1)
        self.SD["viewTooltipThumbnailLimit"]["ui"]["slider"].setValue(
                self.convertTooltipThumbnailLimitStringToValue(setting)
        )
        self.SD["viewTooltipThumbnailLimit"]["ui"]["slider"].setToolTip(
                "Thumbnails in tooltips will be generated for images up to the chosen size."
        )
        
        setting = self.readSetting("viewTooltipThumbnailSize")
        self.panelTooltipThumbnailSizeLayout = QHBoxLayout()
        self.panelTooltipThumbnailSizeLabel = QLabel("Size", self.panel)
        self.SD["viewTooltipThumbnailSize"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["viewTooltipThumbnailSize"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["viewTooltipThumbnailSize"]["ui"]["slider"].setRange(0, len(self.SD["viewTooltipThumbnailSize"]["values"])-1)
        self.SD["viewTooltipThumbnailSize"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["viewTooltipThumbnailSize"]["ui"]["slider"].setTickInterval(1)
        self.SD["viewTooltipThumbnailSize"]["ui"]["slider"].setValue(
                self.convertTooltipThumbnailSizeStringToValue(setting)
        )
        self.SD["viewTooltipThumbnailSize"]["ui"]["slider"].setEnabled(self.SD["viewTooltipThumbnailLimit"]["ui"]["slider"].value() != 0)
        
        self.SD["viewRefreshOnSave"]["ui"]["btn"] = QCheckBox("Refresh on save")
        self.SD["viewRefreshOnSave"]["ui"]["btn"].stateChanged.connect(self.changedThumbnailsRefreshOnSave)
        self.SD["viewRefreshOnSave"]["ui"]["btn"].setChecked(self.readSetting("viewRefreshOnSave") == "true")
        self.SD["viewRefreshOnSave"]["ui"]["btn"].setToolTip("When you save an image, refresh its thumbnail automatically.")
        
        self.SD["viewRefreshPeriodically"]["ui"]["btn"] = QCheckBox("Refresh periodically (experimental)")
        self.SD["viewRefreshPeriodically"]["ui"]["btn"].stateChanged.connect(self.changedThumbnailsRefreshPeriodically)
        self.SD["viewRefreshPeriodically"]["ui"]["btn"].setChecked(self.readSetting("viewRefreshPeriodically") == "true")
        self.SD["viewRefreshPeriodically"]["ui"]["btn"].setToolTip(
                "Automatically refresh the thumbnail for the active image if a change is detected.\n" + 
                "Checks for changes to the image so-many times each second.\n" +
                "Then tries to refresh the thumbnail every so-many seconds.\n" +
                "May not catch quick changes if they happen between checks.\n" +
                "Aggressive settings may degrade performance."
        )
        
        setting = self.readSetting("viewRefreshPeriodicallyChecks")
        self.panelThumbnailsRefreshPeriodicallyChecksLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyChecksLabel = QLabel("Checks", self.panel)
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["value"]  = QLabel(setting, self.panel)
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].setRange(0, len(self.SD["viewRefreshPeriodicallyChecks"]["values"])-1)
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].setTickInterval(1)
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].setValue(
                self.convertThumbnailsRefreshPeriodicallyChecksStringToValue(setting)
        )
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].setToolTip("Number of times each second the image is checked for activity.")
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].setEnabled(self.SD["viewRefreshPeriodically"]["ui"]["btn"].isChecked())
        
        setting = self.readSetting("viewRefreshPeriodicallyDelay")
        self.panelThumbnailsRefreshPeriodicallyDelayLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyDelayLabel = QLabel("Delay by", self.panel)
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"].setRange(0, len(self.SD["viewRefreshPeriodicallyDelay"]["values"])-1)
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"].setTickInterval(1)
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"].setValue(
                self.convertThumbnailsRefreshPeriodicallyDelayStringToValue(setting)
        )
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"].setToolTip("How long after the last detected change to refresh the thumbnail.")
        self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"].setEnabled(self.SD["viewRefreshPeriodically"]["ui"]["btn"].isChecked())
        
        self.panelMiscHeading = QHBoxLayout()
        self.panelMiscHeadingLabel = QLabel("Miscellaneous", self.panel)
        self.panelMiscHeadingLine = QLabel("", self.panel)
        self.panelMiscHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.SD["idAutoDisambiguateCopies"]["ui"]["btn"] = QCheckBox("Auto disambiguate document ID's (modifies file)")
        self.SD["idAutoDisambiguateCopies"]["ui"]["btn"].stateChanged.connect(self.changedIdAutoDisambiguateCopies)
        self.SD["idAutoDisambiguateCopies"]["ui"]["btn"].setChecked(self.readSetting("idAutoDisambiguateCopies") == "true")
        self.SD["idAutoDisambiguateCopies"]["ui"]["btn"].setToolTip(
                "ODD uses a unique ID supplied by Krita to identify documents.\n" +
                "When you 'create copy from current image', This copy does not receive a new ID.\n" +
                "This means ODD can't distinguish the original from the copy.\n" +
                "This setting permits ODD to annotate documents with an additional unique identifier.\n" +
                "If you save the image as a krita document, this data is also saved.\n" +
                "If you open it again at a later time, krita will provide it a new unique ID,\n" +
                "and ODD will remove the redudant annotation. You can then save the image again to remove it from the file."
        )
        
        settingDisplay = self.readSetting("viewDisplay")
        self.SD["viewDisplay"]["ui"]["btngrp"       ].addButton(self.SD["viewDisplay"]["ui"]["btnThumbnails"])
        self.SD["viewDisplay"]["ui"]["btngrp"       ].addButton(self.SD["viewDisplay"]["ui"]["btnText"      ])
        self.SD["viewDisplay"]["ui"]["btnThumbnails"].setChecked(settingDisplay=="thumbnails")
        self.SD["viewDisplay"]["ui"]["btnText"      ].setChecked(settingDisplay=="text")
        self.SD["viewDisplay"]["ui"]["btnThumbnails"].clicked.connect(self.setDisplayToThumbnails)
        self.SD["viewDisplay"]["ui"]["btnText"      ].clicked.connect(self.setDisplayToText)
        settingDirection = self.readSetting("viewDirection")
        self.SD["viewDirection"]["ui"]["btngrp"       ].addButton(self.SD["viewDirection"]["ui"]["btnHorizontal"])
        self.SD["viewDirection"]["ui"]["btngrp"       ].addButton(self.SD["viewDirection"]["ui"]["btnVertical"  ])
        self.SD["viewDirection"]["ui"]["btngrp"       ].addButton(self.SD["viewDirection"]["ui"]["btnAuto"      ])
        self.SD["viewDirection"]["ui"]["btnHorizontal"].setChecked(settingDirection=="horizontal")
        self.SD["viewDirection"]["ui"]["btnVertical"  ].setChecked(settingDirection=="vertical")
        self.SD["viewDirection"]["ui"]["btnAuto"      ].setChecked(settingDirection=="auto")
        self.SD["viewDirection"]["ui"]["btnHorizontal"].clicked.connect(self.setDirectionToHorizontal)
        self.SD["viewDirection"]["ui"]["btnVertical"  ].clicked.connect(self.setDirectionToVertical)
        self.SD["viewDirection"]["ui"]["btnAuto"      ].clicked.connect(self.setDirectionToAuto)
        
        self.panelListHeading.addWidget(self.panelListHeadingLabel)
        self.panelListHeading.addWidget(self.panelListHeadingLine)
        self.panelListHeading.setStretch(0, 1)
        self.panelListHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelListHeading)
        self.panelLayout.addWidget(self.panelDisplayLabel)
        self.panelLayout.addWidget(self.SD["viewDisplay"]["ui"]["btnThumbnails"])
        self.panelLayout.addWidget(self.SD["viewDisplay"]["ui"]["btnText"])
        self.panelLayout.addWidget(self.panelDirectionLabel)
        self.panelLayout.addWidget(self.SD["viewDirection"]["ui"]["btnHorizontal"])
        self.panelLayout.addWidget(self.SD["viewDirection"]["ui"]["btnVertical"])
        self.panelLayout.addWidget(self.SD["viewDirection"]["ui"]["btnAuto"])
        self.panelLayout.addWidget(self.panelThumbnailsLabel)
        self.panelLayout.addWidget(self.SD["thumbnailUseProjectionMethod"]["ui"]["btn"])
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.panelThumbnailsDisplayScaleLabel)
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.SD["viewThumbnailsDisplayScale"]["ui"]["value"])
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.SD["viewThumbnailsDisplayScale"]["ui"]["slider"])
        self.panelThumbnailsDisplayScaleLayout.setStretch(0, 2)
        self.panelThumbnailsDisplayScaleLayout.setStretch(1, 2)
        self.panelThumbnailsDisplayScaleLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsDisplayScaleLayout)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.panelThumbnailsRenderScaleLabel)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.SD["viewThumbnailsRenderScale"]["ui"]["value"])
        self.panelThumbnailsRenderScaleLayout.addWidget(self.SD["viewThumbnailsRenderScale"]["ui"]["slider"])
        self.panelThumbnailsRenderScaleLayout.setStretch(0, 2)
        self.panelThumbnailsRenderScaleLayout.setStretch(1, 2)
        self.panelThumbnailsRenderScaleLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsRenderScaleLayout)
        self.panelLayout.addWidget(self.SD["viewRefreshOnSave"]["ui"]["btn"])
        self.panelLayout.addWidget(self.SD["viewRefreshPeriodically"]["ui"]["btn"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyChecksLabel)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.SD["viewRefreshPeriodicallyChecks"]["ui"]["value"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(0, 2)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(1, 2)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsRefreshPeriodicallyChecksLayout)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyDelayLabel)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.SD["viewRefreshPeriodicallyDelay"]["ui"]["value"])
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.SD["viewRefreshPeriodicallyDelay"]["ui"]["slider"])
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
        self.panelTooltipThumbnailLimitLayout.addWidget(self.SD["viewTooltipThumbnailLimit"]["ui"]["value"])
        self.panelTooltipThumbnailLimitLayout.addWidget(self.SD["viewTooltipThumbnailLimit"]["ui"]["slider"])
        self.panelTooltipThumbnailLimitLayout.setStretch(0, 2)
        self.panelTooltipThumbnailLimitLayout.setStretch(1, 2)
        self.panelTooltipThumbnailLimitLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelTooltipThumbnailLimitLayout)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.panelTooltipThumbnailSizeLabel)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.SD["viewTooltipThumbnailSize"]["ui"]["value"])
        self.panelTooltipThumbnailSizeLayout.addWidget(self.SD["viewTooltipThumbnailSize"]["ui"]["slider"])
        self.panelTooltipThumbnailSizeLayout.setStretch(0, 2)
        self.panelTooltipThumbnailSizeLayout.setStretch(1, 2)
        self.panelTooltipThumbnailSizeLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelTooltipThumbnailSizeLayout)
        self.panelMiscHeading.addWidget(self.panelMiscHeadingLabel)
        self.panelMiscHeading.addWidget(self.panelMiscHeadingLine)
        self.panelMiscHeading.setStretch(0, 1)
        self.panelMiscHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelMiscHeading)
        self.panelLayout.addWidget(self.SD["idAutoDisambiguateCopies"]["ui"]["btn"])
        self.panel.setLayout(self.panelLayout)
        self.panel.setMinimumWidth(384)
        
        self.SD["viewThumbnailsDisplayScale"   ]["ui"]["slider"].valueChanged.connect(self.changedPanelThumbnailsDisplayScaleSlider)
        self.SD["viewThumbnailsRenderScale"    ]["ui"]["slider"].valueChanged.connect(self.changedPanelThumbnailsRenderScaleSlider)
        self.SD["viewTooltipThumbnailLimit"    ]["ui"]["slider"].valueChanged.connect(self.changedPanelTooltipThumbnailLimitSlider)
        self.SD["viewTooltipThumbnailSize"     ]["ui"]["slider"].valueChanged.connect(self.changedPanelTooltipThumbnailSizeSlider)
        self.SD["viewRefreshPeriodicallyChecks"]["ui"]["slider"].valueChanged.connect(self.changedPanelThumbnailsRefreshPeriodicallyChecksSlider)
        self.SD["viewRefreshPeriodicallyDelay" ]["ui"]["slider"].valueChanged.connect(self.changedPanelThumbnailsRefreshPeriodicallyDelaySlider)

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
