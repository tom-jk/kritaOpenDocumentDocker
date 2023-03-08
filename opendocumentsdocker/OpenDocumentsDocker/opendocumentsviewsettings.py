from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QScreen
from PyQt5.QtWidgets import QWidget, QBoxLayout, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QFrame, QToolButton
from krita import *
import math

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
            "grid": {
                    "default":"false",
                    "ui": {
                            "btn":None
                    },
            },
            "gridMode": {
                    "default":"stretchToFit",
                    "strings":["Stretch to fit", "Keep aspect ratio", "Crop to fit", "Masonry"],
                    "values" :["stretchToFit", "keepAspectRatio", "cropToFit", "masonry"],
                    "tooltips":[
                            "list items are square and thumbnails are stretched to fit with no regard to aspect ratio.",
                            "thumbnails show the full image at the correct aspect ratio.",
                            "list items are square and thumbnails are cropped to fit to maintain pixel aspect ratio.",
                            "thumbnails are cropped according to aspect limit setting and stacked end-to-end.",
                    ],
                    "ui": {
                            "btn":None,
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
            "thumbAspectLimit": {
                    "default":"1",
                    "min": 1.0,
                    "max": 10.0,
                    "pow":10,
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
            "showCommonControlsInDocker": {
                    "default":"true",
                    "ui": {
                            "btn":None,
                    },
            },
            "dockerAlignButtonsToSettingsPanel": {
                    "default":"true",
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
        self.panelSize = QSize()
        self.panelPosition = QPoint()
    
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
                if "pow" in self.SD[setting]:
                    v = pow(setting["pow"], v)
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
    
    def changedDisplay(self, checked):
        if checked:
            self.SD["display"]["ui"]["btnThumbnails"].click()
        else:
            self.SD["display"]["ui"]["btnText"].click()
    
    def setDisplayToThumbnails(self):
        print("setDisplayToThumbnails")
        self.writeSetting("display", "thumbnails")
        self.odd.setDockerDirection(self.readSetting("direction"))
        self.odd.refreshOpenDocuments()
        self.odd.updateScrollBarPolicy()
        
        self.dockerDisplayToggleButton.setChecked(True)
    
    def setDisplayToText(self):
        print("setDisplayToText")
        self.writeSetting("display", "text")
        self.odd.setDockerDirection(self.readSetting("direction"))
        self.odd.refreshOpenDocuments()
        self.odd.updateScrollBarPolicy()
        
        self.dockerDisplayToggleButton.setChecked(False)
    
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
    
    def changedGrid(self, state):
        setting = str(state==2).lower()
        print("changedGrid to", setting)
        self.writeSetting("grid", setting)
        
        if self.readSetting("display") != "thumbnails":
            return
        
        self.odd.list.invalidateItemRectsCache()
        self.odd.list.updateGeometries()
        self.odd.list.viewport().update()
        self.startRefreshAllDelayTimer()
    
    def changedGridMode(self, index):
        setting = self.settingValue("gridMode")
        print("changedGridMode to", setting)
        self.writeSetting("gridMode", setting)
        
        if self.readSetting("display") != "thumbnails":
            return
        
        self.odd.list.invalidateItemRectsCache()
        self.odd.list.updateGeometries()
        self.odd.list.viewport().update()
        self.startRefreshAllDelayTimer()
    
    def changedThumbAspectLimitSlider(self, value):
        setting = "{:1.6g}".format(pow(10, value/200.0))
        self.SD["thumbAspectLimit"]["ui"]["value"].setText("1:{:1.3g}".format(float(setting)))
        self.writeSetting("thumbAspectLimit", setting)
        print("changedThumbAspectLimitSlider: value, setting: ", value, setting)
        
        if self.readSetting("display") != "thumbnails":
            return
        
        self.odd.list.invalidateItemRectsCache()
        self.odd.list.updateGeometries()
        self.odd.list.viewport().update()
        self.startRefreshAllDelayTimer()
    
    def changedThumbDisplayScaleSlider(self, value):
        if self.sender() == self.dockerThumbnailsDisplayScaleSlider:
            self.SD["thumbDisplayScale"]["ui"]["slider"].setValue(value)
            return
        setting = "{:4.2f}".format(self.settingValue("thumbDisplayScale"))
        self.SD["thumbDisplayScale"]["ui"]["value"].setText(setting)
        self.writeSetting("thumbDisplayScale", setting)
        print("changedThumbDisplayScaleSlider to ", setting)
        
        if self.readSetting("display") != "thumbnails":
            return
        
        self.odd.list.invalidateItemRectsCache()
        self.odd.list.updateGeometries()
        self.odd.list.viewport().update()
        self.startRefreshAllDelayTimer()
        
        self.dockerThumbnailsDisplayScaleSlider.setValue(value)
    
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
        self.previewThumbnailsShowModified = setting
        self.odd.list.viewport().update()
    
    def unhighlightedThumbShowModified(self):
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
        if (
                hasattr(self, "dockerRefreshPeriodicallyToggleButton") and
                self.sender() == self.dockerRefreshPeriodicallyToggleButton
        ):
            self.SD["refreshPeriodically"]["ui"]["btn"].setChecked(state==1)
        else:
            self._changedRefreshPeriodically(state)
        
    def _changedRefreshPeriodically(self, state):
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
        
        if hasattr(self, "dockerRefreshPeriodicallyToggleButton"):
            self.dockerRefreshPeriodicallyToggleButton.setChecked(state==2)
    
    def changedIdAutoDisambiguateCopies(self, state):
        setting = str(state==2).lower()
        print("changedIdAutoDisambiguateCopies to", setting)
        self.writeSetting("idAutoDisambiguateCopies", setting)
        
        if state == 2:
            # turned on, scan current open documents for ambiguous id's.
            # if detected, ask user if they would like to add the annotations now.
            
            isAnyDocAmbiguous = False
            for i in self.odd.documents:
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
                docCount = len(self.odd.documents)
                for i in range(docCount-1, -1, -1):
                    self.odd.setDocumentExtraUid(self.odd.documents[i])
                self.odd.refreshOpenDocuments()
            else:
                print("Cancel")
        else:
            # turned off, scan current open documents for disambiguated id's.
            # if detected, ask user if they would like to delete the annotations now.
            
            isAnyDocWithExtraUid = False
            for i in self.odd.documents:
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
                for i in self.odd.documents:
                    i.removeAnnotation("ODD_extra_uid")
                self.odd.currentDocumentId = self.odd.findDocumentWithUniqueId(self.odd.currentDocumentId, enableFallback=True)
                self.odd.refreshOpenDocuments()

            else:
                print("Cancel")
    
    def changedShowCommonControlsInDocker(self, state):
        setting = str(state==2).lower()
        print("changedShowCommonControlsInDocker to", setting)
        self.writeSetting("showCommonControlsInDocker", setting)
        
        if state == 2:
            self.dockerThumbnailsDisplayScaleSlider.show()
            self.dockerDisplayToggleButton.show()
            self.dockerRefreshPeriodicallyToggleButton.show()
        else:
            self.dockerThumbnailsDisplayScaleSlider.hide()
            self.dockerDisplayToggleButton.hide()
            self.dockerRefreshPeriodicallyToggleButton.hide()
    
    def changedDockerAlignButtonsToSettingsPanel(self, state):
        setting = str(state==2).lower()
        print("changedDockerAlignButtonsToSettingsPanel to", setting)
        self.writeSetting("dockerAlignButtonsToSettingsPanel", setting)
        
        self.updatePanelPosition()
    
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
        
        self.panel = QFrame(self.odd, Qt.Popup)
        self.panel.setFrameShape(QFrame.StyledPanel)
        self.panelLayout = QVBoxLayout()
        
        self.SD["display"]["ui"]["btngrp"] = QButtonGroup(self.panel)
        self.SD["direction"]["ui"]["btngrp"] = QButtonGroup(self.panel)
        
        self.panelListHeading = QHBoxLayout()
        self.panelListHeadingLabel = QLabel("List", self.panel)
        self.panelListHeadingLine = QLabel("", self.panel)
        self.panelListHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.panelDirectionLayout = QVBoxLayout()
        self.panelDirectionLabel = QLabel("Direction", self.panel)
        self.SD["direction"]["ui"]["btnHorizontal"] = QRadioButton("Horizontal", self.panel)
        self.SD["direction"]["ui"]["btnVertical"  ] = QRadioButton("Vertical", self.panel)
        self.SD["direction"]["ui"]["btnAuto"      ] = QRadioButton("Auto", self.panel)
        self.SD["direction"]["ui"]["btnAuto"      ].setToolTip("The list will be arranged on its longest side.")
        
        self.panelDisplayAndDirectionLayout = QHBoxLayout()
        self.panelDisplayLayout = QVBoxLayout()
        self.panelDisplayLabel = QLabel("Display", self.panel)
        self.SD["display"]["ui"]["btnThumbnails"] = QRadioButton("Thumbnails", self.panel)
        self.SD["display"]["ui"]["btnText"      ] = QRadioButton("Text", self.panel)
        
        self.dockerDisplayToggleButton = QToolButton()
        self.dockerDisplayToggleButton.clicked.connect(self.changedDisplay)
        self.dockerDisplayToggleButton.setCheckable(True)
        self.dockerDisplayToggleButton.setIcon(Application.icon('folder-pictures'))
        self.dockerDisplayToggleButton.setChecked(self.readSetting("display") == "thumbnails")
        
        self.panelGridLayout = QHBoxLayout()
        self.SD["grid"]["ui"]["btn"] = QCheckBox("Grid", self.panel)
        self.SD["grid"]["ui"]["btn"].stateChanged.connect(self.changedGrid)
        self.SD["grid"]["ui"]["btn"].setChecked(self.readSetting("grid") == "true")
        self.SD["grid"]["ui"]["btn"].setToolTip(
                "Lay thumbnails out in a grid if possible.\n" +
                "Thumbnail display scale must be 0.5 or less.\n" +
                "When the list is vertical, items are arranged left-to-right, row-by-row.\n" +
                "When the list is horizontal, items are arranged top-to-bottom, column-by-column."
        )
        
        setting = self.readSetting("gridMode")
        self.SD["gridMode"]["ui"]["btn"] = QComboBox()
        self.SD["gridMode"]["ui"]["btn"].addItems(self.SD["gridMode"]["strings"])
        self.SD["gridMode"]["ui"]["btn"].setCurrentText(convertSettingValueToString("gridMode", setting))
        for i in range(len(self.SD["gridMode"]["tooltips"])):
            self.SD["gridMode"]["ui"]["btn"].setItemData(i, self.SD["gridMode"]["tooltips"][i], Qt.ToolTipRole)
        self.SD["gridMode"]["ui"]["btn"].activated.connect(self.changedGridMode)
        
        self.panelThumbnailsLabel = QLabel("Thumbnails", self.panel)
        
        self.SD["thumbUseProjectionMethod"]["ui"]["btn"] = QCheckBox("Use projection method", self.panel)
        self.SD["thumbUseProjectionMethod"]["ui"]["btn"].stateChanged.connect(self.changedThumbnailUseProjectionMethod)
        self.SD["thumbUseProjectionMethod"]["ui"]["btn"].setChecked(self.readSetting("thumbUseProjectionMethod") == "true")
        self.SD["thumbUseProjectionMethod"]["ui"]["btn"].setToolTip(
                "If enabled, ODD will generate thumbnails with the projection method.\n" +
                "If disabled, ODD will use the thumbnail method.\n" +
                "Projection should be faster. If there are no issues, leave this enabled."
        )
        
        setting = self.readSetting("thumbAspectLimit")
        self.panelThumbnailsAspectLimitLayout = QHBoxLayout()
        self.panelThumbnailsAspectLimitLabel = QLabel("Aspect limit", self.panel)
        self.SD["thumbAspectLimit"]["ui"]["value" ] = QLabel("1:{:1.3g}".format(float(setting)), self.panel)
        self.SD["thumbAspectLimit"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["thumbAspectLimit"]["ui"]["slider"].setRange(0, 200)
        self.SD["thumbAspectLimit"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["thumbAspectLimit"]["ui"]["slider"].setTickInterval(1)
        self.SD["thumbAspectLimit"]["ui"]["slider"].setValue(int(math.log10(float(setting))*200.0))
        self.SD["thumbAspectLimit"]["ui"]["slider"].setToolTip(
                "The maximum deviation a document size can be from square before its thumbnail is shrunk.\n" +
                "For example, 1:1 forces all thumbnails to be square, 1:2 allows thumbnails to be up to twice as long as their width.\n" +
                "Higher values give better representation of wide/tall documents, at the cost of ease of list navigation."
        )
        
        setting = self.readSetting("thumbDisplayScale")
        self.panelThumbnailsDisplayScaleLayout = QHBoxLayout()
        self.panelThumbnailsDisplayScaleLabel = QLabel("Display scale", self.panel)
        self.SD["thumbDisplayScale"]["ui"]["value" ] = QLabel(setting, self.panel)
        self.SD["thumbDisplayScale"]["ui"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setRange(0, 95)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setTickPosition(QSlider.NoTicks)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setTickInterval(1)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setPageStep(5)
        self.SD["thumbDisplayScale"]["ui"]["slider"].setValue(round((float(setting)-0.05)*100.0))
        
        self.dockerThumbnailsDisplayScaleSlider = QSlider(Qt.Horizontal)
        self.dockerThumbnailsDisplayScaleSlider.setRange(       self.SD["thumbDisplayScale"]["ui"]["slider"].minimum(),
                                                                self.SD["thumbDisplayScale"]["ui"]["slider"].maximum())
        self.dockerThumbnailsDisplayScaleSlider.setTickPosition(self.SD["thumbDisplayScale"]["ui"]["slider"].tickPosition())
        self.dockerThumbnailsDisplayScaleSlider.setTickInterval(self.SD["thumbDisplayScale"]["ui"]["slider"].tickInterval())
        self.dockerThumbnailsDisplayScaleSlider.setPageStep(    self.SD["thumbDisplayScale"]["ui"]["slider"].pageStep())
        self.dockerThumbnailsDisplayScaleSlider.setValue(       self.SD["thumbDisplayScale"]["ui"]["slider"].value())
        
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
        
        self.SD["refreshOnSave"]["ui"]["btn"] = QCheckBox("Refresh on save", self.panel)
        self.SD["refreshOnSave"]["ui"]["btn"].stateChanged.connect(self.changedRefreshOnSave)
        self.SD["refreshOnSave"]["ui"]["btn"].setChecked(self.readSetting("refreshOnSave") == "true")
        self.SD["refreshOnSave"]["ui"]["btn"].setToolTip("When you save an image, refresh its thumbnail automatically.")
        
        self.SD["refreshPeriodically"]["ui"]["btn"] = QCheckBox("Refresh periodically (experimental)", self.panel)
        self.SD["refreshPeriodically"]["ui"]["btn"].stateChanged.connect(self.changedRefreshPeriodically)
        self.SD["refreshPeriodically"]["ui"]["btn"].setChecked(self.readSetting("refreshPeriodically") == "true")
        self.SD["refreshPeriodically"]["ui"]["btn"].setToolTip(
                "Automatically refresh the thumbnail for the active image if a change is detected.\n" + 
                "Checks for changes to the image so-many times each second.\n" +
                "Then tries to refresh the thumbnail every so-many seconds.\n" +
                "May not catch quick changes if they happen between checks.\n" +
                "Aggressive settings may degrade performance."
        )
        
        self.dockerRefreshPeriodicallyToggleButton = QToolButton()
        self.dockerRefreshPeriodicallyToggleButton.clicked.connect(self.changedRefreshPeriodically)
        self.dockerRefreshPeriodicallyToggleButton.setCheckable(True)
        self.dockerRefreshPeriodicallyToggleButton.setIcon(Application.icon('animation_play'))
        self.dockerRefreshPeriodicallyToggleButton.setChecked(self.SD["refreshPeriodically"]["ui"]["btn"].isChecked())
        
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
        
        self.panelMiscHeading = QHBoxLayout()
        self.panelMiscHeadingLabel = QLabel("Miscellaneous", self.panel)
        self.panelMiscHeadingLine = QLabel("", self.panel)
        self.panelMiscHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.SD["idAutoDisambiguateCopies"]["ui"]["btn"] = QCheckBox("Auto disambiguate document ID's (modifies file)", self.panel)
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
        
        self.SD["showCommonControlsInDocker"]["ui"]["btn"] = QCheckBox("Show commonly used settings in the docker", self.panel)
        self.SD["showCommonControlsInDocker"]["ui"]["btn"].stateChanged.connect(self.changedShowCommonControlsInDocker)
        self.SD["showCommonControlsInDocker"]["ui"]["btn"].setChecked(self.readSetting("showCommonControlsInDocker") == "true")
        self.SD["showCommonControlsInDocker"]["ui"]["btn"].setToolTip(
                "Make some of the most-used of these settings adjustable in the docker itself.\n" +
                "Included are a slider for the list thumbnail display scale,\n" +
                "and toggle buttons for changing display mode and enabling periodic thumbnail refresh."
        )
        
        self.SD["dockerAlignButtonsToSettingsPanel"]["ui"]["btn"] = QCheckBox("Move docker buttons to align with settings panel", self.panel)
        self.SD["dockerAlignButtonsToSettingsPanel"]["ui"]["btn"].setChecked(self.readSetting("dockerAlignButtonsToSettingsPanel") == "true")
        self.SD["dockerAlignButtonsToSettingsPanel"]["ui"]["btn"].stateChanged.connect(self.changedDockerAlignButtonsToSettingsPanel)
        self.SD["dockerAlignButtonsToSettingsPanel"]["ui"]["btn"].setToolTip(
                "This panel will try to appear in a place that obscures the docker list as little as possible.\n" +
                "This means it may appear on the other side of the docker, far from the default position of the settings button.\n" +
                "This setting allows the docker buttons to move to the side of the docker where the settings button will be closest.\n" +
                "The refresh and settings buttons may also switch position."
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
        self.panelDirectionLayout.addWidget(self.panelDirectionLabel)
        self.panelDirectionLayout.addWidget(self.SD["direction"]["ui"]["btnHorizontal"])
        self.panelDirectionLayout.addWidget(self.SD["direction"]["ui"]["btnVertical"])
        self.panelDirectionLayout.addWidget(self.SD["direction"]["ui"]["btnAuto"])
        self.panelDisplayAndDirectionLayout.addLayout(self.panelDirectionLayout)
        self.panelDisplayLayout.addWidget(self.panelDisplayLabel)
        self.panelDisplayLayout.addWidget(self.SD["display"]["ui"]["btnThumbnails"])
        self.panelDisplayLayout.addWidget(self.SD["display"]["ui"]["btnText"])
        self.panelGridLayout.addWidget(self.SD["grid"]["ui"]["btn"])
        self.panelGridLayout.addWidget(self.SD["gridMode"]["ui"]["btn"])
        self.panelDisplayLayout.addLayout(self.panelGridLayout)
        self.panelDisplayAndDirectionLayout.addLayout(self.panelDisplayLayout)
        self.panelLayout.addLayout(self.panelDisplayAndDirectionLayout)
        self.panelLayout.addWidget(self.panelThumbnailsLabel)
        self.panelLayout.addWidget(self.SD["thumbUseProjectionMethod"]["ui"]["btn"])
        self.panelThumbnailsAspectLimitLayout.addWidget(self.panelThumbnailsAspectLimitLabel)
        self.panelThumbnailsAspectLimitLayout.addWidget(self.SD["thumbAspectLimit"]["ui"]["value"])
        self.panelThumbnailsAspectLimitLayout.addWidget(self.SD["thumbAspectLimit"]["ui"]["slider"])
        self.panelThumbnailsAspectLimitLayout.setStretch(0, 2)
        self.panelThumbnailsAspectLimitLayout.setStretch(1, 2)
        self.panelThumbnailsAspectLimitLayout.setStretch(2, 5)
        self.panelLayout.addLayout(self.panelThumbnailsAspectLimitLayout)
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
        self.panelLayout.addWidget(self.SD["showCommonControlsInDocker"]["ui"]["btn"])
        self.panelLayout.addWidget(self.SD["dockerAlignButtonsToSettingsPanel"]["ui"]["btn"])
        self.panel.setLayout(self.panelLayout)
        self.panel.setMinimumWidth(384)
        
        self.odd.layout.insertWidget(1, self.dockerThumbnailsDisplayScaleSlider)
        self.dockerCommonControlsLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.dockerCommonControlsLayout.setSpacing(0)
        self.dockerCommonControlsLayout.addWidget(self.dockerDisplayToggleButton)
        self.dockerCommonControlsLayout.addWidget(self.dockerRefreshPeriodicallyToggleButton)
        self.odd.buttonLayout.insertLayout(1, self.dockerCommonControlsLayout)
        
        self.SD["thumbAspectLimit"         ]["ui"]["slider"].valueChanged.connect(self.changedThumbAspectLimitSlider)
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
        
        self.dockerThumbnailsDisplayScaleSlider.valueChanged.connect(self.changedThumbDisplayScaleSlider)
    
    def eventFilter(self, obj, event):
        if event.type() in [QEvent.FocusIn, QEvent.Hide]:
            self.unhighlightedThumbShowModified()
        return False
    
    def clickedViewButton(self):
        self.panel.move(self.panelPosition)
        self.panel.show()
    
    def updatePanelPosition(self):
        direction = self._updatePanelPosition()
        if self.readSetting("dockerAlignButtonsToSettingsPanel") == "false":
            direction = 0
        print("updatePanelPosition: direction =", direction)
        if self.odd.list.flow() == QListView.TopToBottom:
            self.odd.layout.setDirection(QBoxLayout.TopToBottom if not direction == 1 else QBoxLayout.BottomToTop)
            self.odd.buttonLayout.setDirection(QBoxLayout.LeftToRight if not direction == 3 else QBoxLayout.RightToLeft)
        else:
            self.odd.layout.setDirection(QBoxLayout.LeftToRight if not direction == 3 else QBoxLayout.RightToLeft)
            self.odd.buttonLayout.setDirection(QBoxLayout.TopToBottom if not direction == 1 else QBoxLayout.BottomToTop)
    
    def _updatePanelPosition(self):
        baseGeo = QRect(self.odd.mapToGlobal(self.odd.baseWidget.frameGeometry().topLeft()), self.odd.baseWidget.frameGeometry().size())
        baseTopLeft = baseGeo.topLeft()
        baseTopRight = baseGeo.topRight() + QPoint(1,0)
        baseBottomRight = baseGeo.bottomRight() + QPoint(1,1)
        
        listTopLeft = self.odd.mapToGlobal(self.odd.list.frameGeometry().topLeft())
        listRect = QRect(listTopLeft, self.odd.list.size())
        
        screen = self.odd.getScreen().availableGeometry()
        screenTopLeft = screen.topLeft()
        screenBottomRight = screen.bottomRight() + QPoint(1,1)
        
        if not self.panelSize.isValid():
            self.panel.show()
            self.panel.layout().invalidate()
            self.panel.hide()
            self.panelSize = self.panel.size()
                
        posRight = baseBottomRight + QPoint(1, 1-self.panelSize.height())
        posRight.setY(min(max(posRight.y(), screenTopLeft.y()), screenBottomRight.y()-self.panelSize.height()))
        
        if posRight.x() + self.panelSize.width() < screenBottomRight.x():
            self.panelPosition = posRight
            return 0
        
        posAbove = QPoint(baseTopRight.x(), baseTopRight.y()) - QPoint(self.panelSize.width(), self.panelSize.height())
        if posAbove.y() > screenTopLeft.y():
            self.panelPosition = posAbove
            return 1
        
        posBelow = baseBottomRight - QPoint(self.panelSize.width(), 0)
        if posBelow.y() + self.panelSize.height() < screenBottomRight.y():
            self.panelPosition = posBelow
            return 2
        
        posLeft = QPoint(baseTopLeft.x() - self.panelSize.width(), posRight.y())
        if posLeft.x() > screenTopLeft.x():
            self.panelPosition = posLeft
            return 3
        
        # no perfect position for panel, so find which was the least-worst instead.
        # this would be the position where it least obscures the list.
        posRight.setX(screenBottomRight.x() - self.panelSize.width())
        posAbove.setY(screenTopLeft.y())
        posBelow.setY(screenBottomRight.y() - self.panelSize.height())
        posLeft.setX(screenTopLeft.x())
        coverageRight = QRect(posRight, self.panelSize).intersected(listRect).size()
        coverageAbove = QRect(posAbove, self.panelSize).intersected(listRect).size()
        coverageBelow = QRect(posBelow, self.panelSize).intersected(listRect).size()
        coverageLeft  = QRect(posLeft,  self.panelSize).intersected(listRect).size()
        coverageArea = []
        coverageArea.append({"r":0, "pos":posRight, "area":coverageRight.width() * coverageRight.height()})
        coverageArea.append({"r":1, "pos":posAbove, "area":coverageAbove.width() * coverageAbove.height()})
        coverageArea.append({"r":2, "pos":posBelow, "area":coverageBelow.width() * coverageBelow.height()})
        coverageArea.append({"r":3, "pos":posLeft,  "area":coverageLeft.width()  * coverageLeft.height() })
        coverageAreaSorted = sorted(coverageArea, key = lambda d: d['area'])
        self.panelPosition = coverageAreaSorted[0]['pos']
        return coverageAreaSorted[0]["r"]
