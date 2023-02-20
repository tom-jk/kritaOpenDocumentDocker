from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QScreen
from PyQt5.QtWidgets import QWidget, QBoxLayout, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QFrame
from krita import *

def convertSettingStringToValue(settingName, string):
    setting = OpenDocumentsViewSettings.SD[settingName]
    if string in setting["strings"]:
        return setting["strings"].index(string)
    else:
        return setting["strings"].index(setting["default"])

def convertSettingValueToString(settingName, value):
    setting = OpenDocumentsViewSettings.SD[settingName]
    if type(value) is not str and value >= 0 and value < len(setting["strings"]):
        return setting["strings"][value]
    elif type(value) is str and value in setting["values"]:
        return setting["strings"][setting["values"].index(value)]
    else:
        return setting["default"]

class OpenDocumentsViewSettings(QObject):
    # Settings Data
    SD = {
            "direction": {
                    "default":"auto",
                    "ui": {
                            "btngrp":None,
                            "btnHorizontal":None,
                            "btnVertical":None,
                            "btnAuto":None,
                    },
            },
            "display": {
                    "default":"thumbnails",
                    "ui": {
                            "btngrp":None,
                            "btnThumbnails":None,
                            "btnText":None,
                    },
            },
            "refreshOnSave": {
                    "default":"true",
                    "ui": {
                            "btn":None,
                    },
            },
            "refreshPeriodically": {
                    "default":"false",
                    "ui": {
                            "btn":None,
                    },
            },
            "refreshPeriodicallyChecks": {
                    "default":"15/sec",
                    "strings":["1/sec","2/sec","3/sec","4/sec","5/sec","8/sec","10/sec","15/sec","20/sec","30/sec"],
                    "values" :[1000, 500, 333, 250, 200, 125, 100, 67, 50, 33],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "refreshPeriodicallyDelay": {
                    "default":"2sec",
                    "strings":["1/2sec", "1sec", "1.5sec", "2sec", "3sec", "4sec", "5sec", "7sec", "10sec", "20sec", "1min"],
                    "values" :[500, 1000, 1500, 2000, 3000, 4000, 5000, 7000, 10000, 20000, 60000],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "thumbDisplayScale": {
                    "default":"1.00",
                    "min":0.05,
                    "max":1.00,
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "thumbRenderScale": {
                    "default":"1",
                    "strings":["1/16", "1/8", "1/4", "1/2", "1"],
                    "values" :[1.0/16.0, 1.0/8.0, 1.0/4.0, 1.0/2.0, 1],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "thumbFadeAmount": {
                    "default":"0.00",
                    "min":0.00,
                    "max":1.00,
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "thumbFadeUnfade": {
                    "default":"false",
                    "ui": {
                            "btn":None,
                    },
            },
            "thumbShowModified": {
                    "default":"none",
                    "strings":["Don't show", "Corner", "Square", "Circle", "Asterisk", "Big Corner", "Big Square", "Big Circle", "Big Asterisk"],
                    "values" :["none", "corner", "square", "circle", "asterisk", "cornerBig", "squareBig", "circleBig", "asteriskBig"],
                    "ui": {
                            "btn":None,
                    },
            },
            "tooltipShow": {
                    "default":"true",
                    "ui": {
                            "btn":None,
                    },
            },
            "tooltipThumbLimit": {
                    "default":"≤4096px²",
                    "strings":["never","≤128px²","≤256px²","≤512px²","≤1024px²","≤2048px²","≤4096px²","≤8192px²","≤16384px²","always"],
                    "values" :[0, 128*128, 256*256, 512*512, 1024*1024, 2048*2048, 4096*4096, 8192*8192, 16384*16384, float("inf")],
                    "ui": {
                            "value":None,
                            "slider":None,
                    },
            },
            "tooltipThumbSize": {
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
            "thumbUseProjectionMethod": {
                    "default":"true",
                    "ui": {
                            "btn":None,
                    },
            },
    }
    
    def __init__(self, odd):
        super(OpenDocumentsViewSettings, self).__init__()
        self.odd = odd
    
    def readSetting(self, setting):
        if not setting in self.SD:
            return
        return Application.readSetting("OpenDocumentsDocker", setting, self.SD[setting]["default"])
    
    def writeSetting(self, setting, value):
        if not setting in self.SD:
            return
        Application.writeSetting("OpenDocumentsDocker", setting, value)
    
    def settingValue(self, setting):
        ui = self.SD[setting]["ui"]
        if "slider" in ui:
            if "values" in self.SD[setting]:
                return self.SD[setting]["values"][ui["slider"].value()]
            elif "max" in self.SD[setting]:
                # map slider value into setting min/max range
                sliderMin = ui["slider"].minimum()
                sliderMax = ui["slider"].maximum()
                sliderRange = sliderMax - sliderMin
                sliderValue = ui["slider"].value()
                sliderNormValue = 1.0 / sliderRange * (sliderValue - sliderMin)
                valueRange = self.SD[setting]["max"] - self.SD[setting]["min"]
                v = self.SD[setting]["min"] + valueRange * sliderNormValue
                #print("settingValue:", sliderMin, sliderMax, sliderRange, sliderValue, sliderNormValue, valueRange, v)
                return v
        elif "btngrp" in ui:
            return ui["btngrp"].checkedButton()
        elif "btn" in ui:
            if "values" in self.SD[setting]:
                return self.SD[setting]["values"][ui["btn"].currentIndex()]
            else:
                return ui["btn"].isChecked()
        return None
    
    def setDisplayToThumbnails(self):
        print("setDisplayToThumbnails")
        self.writeSetting("display", "thumbnails")
        self.odd.setDockerDirection(self.readSetting("direction"))
        self.odd.refreshOpenDocuments()
        self.odd.updateScrollBarPolicy()
    
    def setDisplayToText(self):
        print("setDisplayToText")
        self.writeSetting("display", "text")
        self.odd.setDockerDirection(self.readSetting("direction"))
        self.odd.refreshOpenDocuments()
        self.odd.updateScrollBarPolicy()
        self.odd.deferredItemThumbnailCount = 0
    
    def setDirectionToHorizontal(self):
        print("setDirectionToHorizontal")
        self.writeSetting("direction", "horizontal")
        self.odd.setDockerDirection("horizontal")
    
    def setDirectionToVertical(self):
        print("setDirectionToVertical")
        self.writeSetting("direction", "vertical")
        self.odd.setDockerDirection("vertical")
    
    def setDirectionToAuto(self):
        print("setDirectionToAuto")
        self.writeSetting("direction", "auto")
        self.odd.setDockerDirection("auto")
    
    def changedThumbDisplayScaleSlider(self, value):
        setting = "{:4.2f}".format(self.settingValue("thumbDisplayScale"))
        self.SD["thumbDisplayScale"]["ui"]["value"].setText(setting)
        self.writeSetting("thumbDisplayScale", setting)
        print("changedThumbDisplayScaleSlider to ", setting)
        
        if self.readSetting("display") != "thumbnails":
            return
        
        # quick resize thumbs for visual feedback
        l = self.odd.list
        itemCount = l.count()
        for i in range(itemCount):
            item = l.item(i)
            size = self.odd.calculateSizeForThumbnail(self.odd.findDocumentWithItem(item)) # TODO: no, bad, leaks.
            t = item.data(Qt.DecorationRole)
            item.setData(Qt.DecorationRole, t.scaled(size))
        
        self.startRefreshAllDelayTimer()
        self.odd.list.invalidateItemRectsCache()
    
    def changedThumbRenderScaleSlider(self, value):
        setting = convertSettingValueToString("thumbRenderScale", value)
        self.SD["thumbRenderScale"]["ui"]["value"].setText(setting)
        self.writeSetting("thumbRenderScale", setting)
        
        self.startRefreshAllDelayTimer()
    
    def changedThumbFadeAmountSlider(self, value):
        setting = "{:4.2f}".format(self.settingValue("thumbFadeAmount"))
        self.SD["thumbFadeAmount"]["ui"]["value"].setText(setting)
        self.writeSetting("thumbFadeAmount", setting)
        self.odd.list.viewport().update()
    
    def changedThumbFadeUnfade(self, state):
        setting = str(state==2).lower()
        print("changedThumbFadeUnfade to", setting)
        self.writeSetting("thumbFadeUnfade", setting)
    
    def changedThumbShowModified(self, index):
        setting = self.settingValue("thumbShowModified")
        print("changedThumbShowModified to", setting)
        self.writeSetting("thumbShowModified", setting)
        self.odd.list.viewport().update()
    
    def highlightedThumbShowModified(self, index):
        setting = self.SD["thumbShowModified"]["values"][index]
        print("highlighted", setting)
        self.previewThumbnailsShowModified = setting
        self.odd.list.viewport().update()
    
    def unhighlightedThumbShowModified(self):
        print("unhighlighted")
        self.previewThumbnailsShowModified = ""
        self.odd.list.viewport().update()
    
    def changedTooltipShow(self, state):
        setting = str(state==2).lower()
        print("changedTooltipShow to", setting)
        self.writeSetting("tooltipShow", setting)
        if self.SD["tooltipThumbLimit"]["ui"]["slider"]:
            if state == 2:
                self.SD["tooltipThumbLimit"]["ui"]["slider"].setEnabled(True)
                self.SD["tooltipThumbSize"]["ui"]["slider"].setEnabled(self.SD["tooltipThumbLimit"]["ui"]["slider"].value != 0)
            else:
                self.SD["tooltipThumbLimit"]["ui"]["slider"].setEnabled(False)
                self.SD["tooltipThumbSize"]["ui"]["slider"].setEnabled(False)
    
    def changedTooltipThumbLimitSlider(self, value):
        setting = convertSettingValueToString("tooltipThumbLimit", value)
        self.SD["tooltipThumbLimit"]["ui"]["value"].setText(setting)
        self.writeSetting("tooltipThumbLimit", setting)
        if self.SD["tooltipThumbSize"]["ui"]["slider"]:
            if value != 0:
                self.SD["tooltipThumbSize"]["ui"]["slider"].setEnabled(True)
            else:
                self.SD["tooltipThumbSize"]["ui"]["slider"].setEnabled(False)
    
    def changedTooltipThumbSizeSlider(self, value):
        setting = convertSettingValueToString("tooltipThumbSize", value)
        self.SD["tooltipThumbSize"]["ui"]["value"].setText(setting)
        self.writeSetting("tooltipThumbSize", setting)
    
    def changedRefreshOnSave(self, state):
        setting = str(state==2).lower()
        print("changedRefreshOnSave to", setting)
        self.writeSetting("refreshOnSave", setting)
    
    def changedRefreshPeriodically(self, state):
        setting = str(state==2).lower()
        print("changedRefreshPeriodically to", setting)
        self.writeSetting("refreshPeriodically", setting)
        if state == 2:
            if self.SD["refreshPeriodicallyChecks"]["ui"]["slider"]:
                self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].setEnabled(True)
                self.SD["refreshPeriodicallyDelay" ]["ui"]["slider"].setEnabled(True)
            self.odd.imageChangeDetectionTimer.start()
        else:
            if self.SD["refreshPeriodicallyChecks"]["ui"]["slider"]:
                self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].setEnabled(False)
                self.SD["refreshPeriodicallyDelay" ]["ui"]["slider"].setEnabled(False)
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
        self.writeSetting("thumbUseProjectionMethod", setting)
        if self.SD["thumbRenderScale"]["ui"]["slider"]:
            if state == 2:
                self.SD["thumbRenderScale"]["ui"]["slider"].setEnabled(False)
            else:
                self.SD["thumbRenderScale"]["ui"]["slider"].setEnabled(True)
        
        self.startRefreshAllDelayTimer()
        
    def startRefreshAllDelayTimer(self):
        if not hasattr(self.odd, "refreshAllDelay"):
            return
        delay = self.odd.refreshAllDelay
        if delay.isActive():
            delay.stop()
        delay.start()
    
    def changedRefreshPeriodicallyChecksSlider(self, value):
        setting = convertSettingValueToString("refreshPeriodicallyChecks", value)
        self.SD["refreshPeriodicallyChecks"]["ui"]["value"].setText(setting)
        self.odd.imageChangeDetectionTimer.setInterval(
                self.settingValue("refreshPeriodicallyChecks")
        )
        self.writeSetting("refreshPeriodicallyChecks", setting)
    
    def changedRefreshPeriodicallyDelaySlider(self, value):
        setting = convertSettingValueToString("refreshPeriodicallyDelay", value)
        self.SD["refreshPeriodicallyDelay"]["ui"]["value"].setText(setting)
        self.odd.refreshTimer.setInterval(
                self.settingValue("refreshPeriodicallyDelay")
        )
        self.writeSetting("refreshPeriodicallyDelay", setting)
        
    def createPanel(self):
        app = Application
        
        self.panel = QWidget(self.odd, Qt.Popup)
        self.panelLayout = QVBoxLayout()
        
        self.SD["display"]["ui"]["btngrp"] = QButtonGroup(self.panel)
        self.SD["direction"]["ui"]["btngrp"] = QButtonGroup(self.panel)
        
        self.panelListHeading = QHBoxLayout()
        self.panelListHeadingLabel = QLabel("List", self.panel)
        self.panelListHeadingLine = QLabel("", self.panel)
        self.panelListHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.panelDisplayLabel = QLabel("Display", self.panel)
        self.SD["display"]["ui"]["btnThumbnails"] = QRadioButton("Thumbnails", self.panel)
        self.SD["display"]["ui"]["btnText"      ] = QRadioButton("Text", self.panel)
        
        self.panelDirectionLabel = QLabel("Direction", self.panel)
        self.SD["direction"]["ui"]["btnHorizontal"] = QRadioButton("Horizontal", self.panel)
        self.SD["direction"]["ui"]["btnVertical"  ] = QRadioButton("Vertical", self.panel)
        self.SD["direction"]["ui"]["btnAuto"      ] = QRadioButton("Auto", self.panel)
        self.SD["direction"]["ui"]["btnAuto"      ].setToolTip("The list will be arranged on its longest side.")
        
        self.panelThumbnailsLabel = QLabel("Thumbnails", self.panel)
        
        self.SD["thumbUseProjectionMethod"]["ui"]["btn"] = QCheckBox("Use projection method")
        self.SD["thumbUseProjectionMethod"]["ui"]["btn"].stateChanged.connect(self.changedThumbnailUseProjectionMethod)
        self.SD["thumbUseProjectionMethod"]["ui"]["btn"].setChecked(self.readSetting("thumbUseProjectionMethod") == "true")
        self.SD["thumbUseProjectionMethod"]["ui"]["btn"].setToolTip(
                "If enabled, ODD will generate thumbnails with the projection method.\n" +
                "If disabled, ODD will use the thumbnail method.\n" +
                "Projection should be faster. If there are no issues, leave this enabled."
        )
        
        setting = self.readSetting("thumbDisplayScale")
        self.panelThumbnailsDisplayScaleLayout = QHBoxLayout()
        self.panelThumbnailsDisplayScaleLabel = QLabel("Display scale", self.panel)
        self.SD["thumbDisplayScale"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["thumbDisplayScale"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setRange(0, 19)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setTickInterval(1)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setValue(round(float(setting)*20))
        
        setting = self.readSetting("thumbRenderScale")
        self.panelThumbnailsRenderScaleLayout = QHBoxLayout()
        self.panelThumbnailsRenderScaleLabel = QLabel("Render scale", self.panel)
        self.SD["thumbRenderScale"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["thumbRenderScale"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["thumbRenderScale"]["ui"]["slider"].setRange(0, len(self.SD["thumbRenderScale"]["values"])-1)
        self.SD["thumbRenderScale"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["thumbRenderScale"]["ui"]["slider"].setTickInterval(1)
        self.SD["thumbRenderScale"]["ui"]["slider"].setValue(
                convertSettingStringToValue("thumbRenderScale", setting)
        )
        self.SD["thumbRenderScale"]["ui"]["slider"].setToolTip(
                "Thumbnails in the list can be generated at a reduced size then scaled up.\n" +
                "This can improve performance when using the thumbnail method."
        )
        self.SD["thumbRenderScale"]["ui"]["slider"].setEnabled(not self.settingValue("thumbUseProjectionMethod"))
        
        setting = self.readSetting("thumbFadeAmount")
        self.panelThumbnailsFadeAmountLayout = QHBoxLayout()
        self.panelThumbnailsFadeAmountLabel = QLabel("Fade amount", self.panel)
        self.SD["thumbFadeAmount"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["thumbFadeAmount"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["thumbFadeAmount"]["ui"]["slider"].setRange(0, 100)
        self.SD["thumbFadeAmount"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["thumbFadeAmount"]["ui"]["slider"].setTickInterval(1)
        self.SD["thumbFadeAmount"]["ui"]["slider"].setValue(round(float(setting)*100))
        
        self.panelThumbnailsFadeAmountControlsLayout = QHBoxLayout()
        self.SD["thumbFadeUnfade"]["ui"]["btn"] = QCheckBox(self.panel)
        self.SD["thumbFadeUnfade"]["ui"]["btn"].stateChanged.connect(self.changedThumbFadeUnfade)
        self.SD["thumbFadeUnfade"]["ui"]["btn"].setChecked(self.readSetting("thumbFadeUnfade") == "true")
        self.SD["thumbFadeUnfade"]["ui"]["btn"].setToolTip("Un-fade on mouse hover.")
        
        setting = self.readSetting("thumbShowModified")
        self.panelThumbnailsShowModifiedLayout = QHBoxLayout()
        self.panelThumbnailsShowModifiedLabel = QLabel("Modified indicator", self.panel)
        self.SD["thumbShowModified"]["ui"]["btn"] = QComboBox(self.panel)
        self.SD["thumbShowModified"]["ui"]["btn"].addItems(self.SD["thumbShowModified"]["strings"])
        self.SD["thumbShowModified"]["ui"]["btn"].setCurrentText(convertSettingValueToString("thumbShowModified", setting))
        self.SD["thumbShowModified"]["ui"]["btn"].setToolTip(
                "An icon to show on modified document thumbnails.\n" +
                "A preview will be shown as you highlight options (if there are visible thumbnails)."
        )
        self.previewThumbnailsShowModified = ""
        
        self.panelTooltipsHeading = QHBoxLayout()
        self.SD["tooltipShow"]["ui"]["btn"] = QCheckBox("Tooltips", self.panel)
        self.SD["tooltipShow"]["ui"]["btn"].stateChanged.connect(self.changedTooltipShow)
        self.SD["tooltipShow"]["ui"]["btn"].setChecked(self.readSetting("tooltipShow") == "true")
        self.panelTooltipsHeadingLine = QLabel("", self.panel)
        self.panelTooltipsHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        setting = self.readSetting("tooltipThumbLimit")
        self.panelTooltipThumbnailLimitLayout = QHBoxLayout()
        self.panelTooltipThumbnailLimitLabel = QLabel("Limit", self.panel)
        self.SD["tooltipThumbLimit"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["tooltipThumbLimit"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["tooltipThumbLimit"]["ui"]["slider"].setRange(0, len(self.SD["tooltipThumbLimit"]["values"])-1)
        self.SD["tooltipThumbLimit"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["tooltipThumbLimit"]["ui"]["slider"].setTickInterval(1)
        self.SD["tooltipThumbLimit"]["ui"]["slider"].setValue(
                convertSettingStringToValue("tooltipThumbLimit", setting)
        )
        self.SD["tooltipThumbLimit"]["ui"]["slider"].setToolTip(
                "Thumbnails in tooltips will be generated for images up to the chosen size."
        )
        self.SD["tooltipThumbLimit"]["ui"]["slider"].setEnabled(self.settingValue("tooltipShow"))
        
        setting = self.readSetting("tooltipThumbSize")
        self.panelTooltipThumbnailSizeLayout = QHBoxLayout()
        self.panelTooltipThumbnailSizeLabel = QLabel("Size", self.panel)
        self.SD["tooltipThumbSize"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["tooltipThumbSize"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["tooltipThumbSize"]["ui"]["slider"].setRange(0, len(self.SD["tooltipThumbSize"]["values"])-1)
        self.SD["tooltipThumbSize"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["tooltipThumbSize"]["ui"]["slider"].setTickInterval(1)
        self.SD["tooltipThumbSize"]["ui"]["slider"].setValue(
                convertSettingStringToValue("tooltipThumbSize", setting)
        )
        self.SD["tooltipThumbSize"]["ui"]["slider"].setEnabled(self.settingValue("tooltipShow") and self.settingValue("tooltipThumbLimit") != 0)
        
        self.SD["refreshOnSave"]["ui"]["btn"] = QCheckBox("Refresh on save")
        self.SD["refreshOnSave"]["ui"]["btn"].stateChanged.connect(self.changedRefreshOnSave)
        self.SD["refreshOnSave"]["ui"]["btn"].setChecked(self.readSetting("refreshOnSave") == "true")
        self.SD["refreshOnSave"]["ui"]["btn"].setToolTip("When you save an image, refresh its thumbnail automatically.")
        
        self.SD["refreshPeriodically"]["ui"]["btn"] = QCheckBox("Refresh periodically (experimental)")
        self.SD["refreshPeriodically"]["ui"]["btn"].stateChanged.connect(self.changedRefreshPeriodically)
        self.SD["refreshPeriodically"]["ui"]["btn"].setChecked(self.readSetting("refreshPeriodically") == "true")
        self.SD["refreshPeriodically"]["ui"]["btn"].setToolTip(
                "Automatically refresh the thumbnail for the active image if a change is detected.\n" + 
                "Checks for changes to the image so-many times each second.\n" +
                "Then tries to refresh the thumbnail every so-many seconds.\n" +
                "May not catch quick changes if they happen between checks.\n" +
                "Aggressive settings may degrade performance."
        )
        
        setting = self.readSetting("refreshPeriodicallyChecks")
        self.panelThumbnailsRefreshPeriodicallyChecksLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyChecksLabel = QLabel("Checks", self.panel)
        self.SD["refreshPeriodicallyChecks"]["ui"]["value"]  = QLabel(setting, self.panel)
        self.SD["refreshPeriodicallyChecks"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].setRange(0, len(self.SD["refreshPeriodicallyChecks"]["values"])-1)
        self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].setTickInterval(1)
        self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].setValue(
                convertSettingStringToValue("refreshPeriodicallyChecks", setting)
        )
        self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].setToolTip("Number of times each second the image is checked for activity.")
        self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].setEnabled(self.settingValue("refreshPeriodically"))
        
        setting = self.readSetting("refreshPeriodicallyDelay")
        self.panelThumbnailsRefreshPeriodicallyDelayLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyDelayLabel = QLabel("Delay by", self.panel)
        self.SD["refreshPeriodicallyDelay"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["refreshPeriodicallyDelay"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["refreshPeriodicallyDelay"]["ui"]["slider"].setRange(0, len(self.SD["refreshPeriodicallyDelay"]["values"])-1)
        self.SD["refreshPeriodicallyDelay"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["refreshPeriodicallyDelay"]["ui"]["slider"].setTickInterval(1)
        self.SD["refreshPeriodicallyDelay"]["ui"]["slider"].setValue(
                convertSettingStringToValue("refreshPeriodicallyDelay", setting)
        )
        self.SD["refreshPeriodicallyDelay"]["ui"]["slider"].setToolTip("How long after the last detected change to refresh the thumbnail.")
        self.SD["refreshPeriodicallyDelay"]["ui"]["slider"].setEnabled(self.settingValue("refreshPeriodically"))
        
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
        
        settingDisplay = self.readSetting("display")
        self.SD["display"]["ui"]["btngrp"       ].addButton(self.SD["display"]["ui"]["btnThumbnails"])
        self.SD["display"]["ui"]["btngrp"       ].addButton(self.SD["display"]["ui"]["btnText"      ])
        self.SD["display"]["ui"]["btnThumbnails"].setChecked(settingDisplay=="thumbnails")
        self.SD["display"]["ui"]["btnText"      ].setChecked(settingDisplay=="text")
        self.SD["display"]["ui"]["btnThumbnails"].clicked.connect(self.setDisplayToThumbnails)
        self.SD["display"]["ui"]["btnText"      ].clicked.connect(self.setDisplayToText)
        settingDirection = self.readSetting("direction")
        self.SD["direction"]["ui"]["btngrp"       ].addButton(self.SD["direction"]["ui"]["btnHorizontal"])
        self.SD["direction"]["ui"]["btngrp"       ].addButton(self.SD["direction"]["ui"]["btnVertical"  ])
        self.SD["direction"]["ui"]["btngrp"       ].addButton(self.SD["direction"]["ui"]["btnAuto"      ])
        self.SD["direction"]["ui"]["btnHorizontal"].setChecked(settingDirection=="horizontal")
        self.SD["direction"]["ui"]["btnVertical"  ].setChecked(settingDirection=="vertical")
        self.SD["direction"]["ui"]["btnAuto"      ].setChecked(settingDirection=="auto")
        self.SD["direction"]["ui"]["btnHorizontal"].clicked.connect(self.setDirectionToHorizontal)
        self.SD["direction"]["ui"]["btnVertical"  ].clicked.connect(self.setDirectionToVertical)
        self.SD["direction"]["ui"]["btnAuto"      ].clicked.connect(self.setDirectionToAuto)
        
        self.panelListHeading.addWidget(self.panelListHeadingLabel)
        self.panelListHeading.addWidget(self.panelListHeadingLine)
        self.panelListHeading.setStretch(0, 1)
        self.panelListHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelListHeading)
        self.panelLayout.addWidget(self.panelDisplayLabel)
        self.panelLayout.addWidget(self.SD["display"]["ui"]["btnThumbnails"])
        self.panelLayout.addWidget(self.SD["display"]["ui"]["btnText"])
        self.panelLayout.addWidget(self.panelDirectionLabel)
        self.panelLayout.addWidget(self.SD["direction"]["ui"]["btnHorizontal"])
        self.panelLayout.addWidget(self.SD["direction"]["ui"]["btnVertical"])
        self.panelLayout.addWidget(self.SD["direction"]["ui"]["btnAuto"])
        self.panelLayout.addWidget(self.panelThumbnailsLabel)
        self.panelLayout.addWidget(self.SD["thumbUseProjectionMethod"]["ui"]["btn"])
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.panelThumbnailsDisplayScaleLabel)
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.SD["thumbDisplayScale"]["ui"]["value"])
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.SD["thumbDisplayScale"]["ui"]["slider"])
        self.panelThumbnailsDisplayScaleLayout.setStretch(0, 2)
        self.panelThumbnailsDisplayScaleLayout.setStretch(1, 2)
        self.panelThumbnailsDisplayScaleLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsDisplayScaleLayout)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.panelThumbnailsRenderScaleLabel)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.SD["thumbRenderScale"]["ui"]["value"])
        self.panelThumbnailsRenderScaleLayout.addWidget(self.SD["thumbRenderScale"]["ui"]["slider"])
        self.panelThumbnailsRenderScaleLayout.setStretch(0, 2)
        self.panelThumbnailsRenderScaleLayout.setStretch(1, 2)
        self.panelThumbnailsRenderScaleLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsRenderScaleLayout)
        self.panelThumbnailsFadeAmountLayout.addWidget(self.panelThumbnailsFadeAmountLabel)
        self.panelThumbnailsFadeAmountLayout.addWidget(self.SD["thumbFadeAmount"]["ui"]["value"])
        self.panelThumbnailsFadeAmountControlsLayout.addWidget(self.SD["thumbFadeAmount"]["ui"]["slider"])
        self.panelThumbnailsFadeAmountControlsLayout.addWidget(self.SD["thumbFadeUnfade"]["ui"]["btn"])
        self.panelThumbnailsFadeAmountControlsLayout.setStretch(0, 19)
        self.panelThumbnailsFadeAmountControlsLayout.setStretch(1, 1)
        self.panelThumbnailsFadeAmountLayout.addLayout(self.panelThumbnailsFadeAmountControlsLayout)
        self.panelThumbnailsFadeAmountLayout.setStretch(0, 2)
        self.panelThumbnailsFadeAmountLayout.setStretch(1, 2)
        self.panelThumbnailsFadeAmountLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsFadeAmountLayout)
        self.panelThumbnailsShowModifiedLayout.addWidget(self.panelThumbnailsShowModifiedLabel)
        self.panelThumbnailsShowModifiedLayout.addWidget(self.SD["thumbShowModified"]["ui"]["btn"])
        self.panelThumbnailsShowModifiedLayout.setStretch(0, 4)
        self.panelThumbnailsShowModifiedLayout.setStretch(1, 5)
        self.panelLayout.addLayout(self.panelThumbnailsShowModifiedLayout)
        self.panelLayout.addWidget(self.SD["refreshOnSave"]["ui"]["btn"])
        self.panelLayout.addWidget(self.SD["refreshPeriodically"]["ui"]["btn"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyChecksLabel)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.SD["refreshPeriodicallyChecks"]["ui"]["value"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.SD["refreshPeriodicallyChecks"]["ui"]["slider"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(0, 2)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(1, 2)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsRefreshPeriodicallyChecksLayout)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyDelayLabel)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.SD["refreshPeriodicallyDelay"]["ui"]["value"])
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.SD["refreshPeriodicallyDelay"]["ui"]["slider"])
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(0, 2)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(1, 2)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsRefreshPeriodicallyDelayLayout)
        self.panelTooltipsHeading.addWidget(self.SD["tooltipShow"]["ui"]["btn"])
        self.panelTooltipsHeading.addWidget(self.panelTooltipsHeadingLine)
        self.panelTooltipsHeading.setStretch(0, 1)
        self.panelTooltipsHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelTooltipsHeading)
        self.panelTooltipThumbnailLimitLayout.addWidget(self.panelTooltipThumbnailLimitLabel)
        self.panelTooltipThumbnailLimitLayout.addWidget(self.SD["tooltipThumbLimit"]["ui"]["value"])
        self.panelTooltipThumbnailLimitLayout.addWidget(self.SD["tooltipThumbLimit"]["ui"]["slider"])
        self.panelTooltipThumbnailLimitLayout.setStretch(0, 2)
        self.panelTooltipThumbnailLimitLayout.setStretch(1, 2)
        self.panelTooltipThumbnailLimitLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelTooltipThumbnailLimitLayout)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.panelTooltipThumbnailSizeLabel)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.SD["tooltipThumbSize"]["ui"]["value"])
        self.panelTooltipThumbnailSizeLayout.addWidget(self.SD["tooltipThumbSize"]["ui"]["slider"])
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
        
        self.SD["thumbDisplayScale"        ]["ui"]["slider"].valueChanged.connect(self.changedThumbDisplayScaleSlider)
        self.SD["thumbRenderScale"         ]["ui"]["slider"].valueChanged.connect(self.changedThumbRenderScaleSlider)
        self.SD["thumbFadeAmount"          ]["ui"]["slider"].valueChanged.connect(self.changedThumbFadeAmountSlider)
        self.SD["thumbShowModified"        ]["ui"]["btn"   ].activated.connect(self.changedThumbShowModified)
        self.SD["thumbShowModified"        ]["ui"]["btn"   ].highlighted.connect(self.highlightedThumbShowModified)
        self.SD["thumbShowModified"        ]["ui"]["btn"   ].installEventFilter(self)
        self.SD["tooltipThumbLimit"        ]["ui"]["slider"].valueChanged.connect(self.changedTooltipThumbLimitSlider)
        self.SD["tooltipThumbSize"         ]["ui"]["slider"].valueChanged.connect(self.changedTooltipThumbSizeSlider)
        self.SD["refreshPeriodicallyChecks"]["ui"]["slider"].valueChanged.connect(self.changedRefreshPeriodicallyChecksSlider)
        self.SD["refreshPeriodicallyDelay" ]["ui"]["slider"].valueChanged.connect(self.changedRefreshPeriodicallyDelaySlider)
    
    def eventFilter(self, obj, event):
        if event.type() in [QEvent.FocusIn, QEvent.Hide]:
            self.unhighlightedThumbShowModified()
        return False
    
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
