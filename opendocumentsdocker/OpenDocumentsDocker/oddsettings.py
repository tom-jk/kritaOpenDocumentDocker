from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QScreen
from PyQt5.QtWidgets import QWidget, QBoxLayout, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QFrame, QToolButton
from krita import *
import math
from ast import literal_eval

def convertSettingStringToValue(settingName, string):
    setting = ODDSettings.SD[settingName]
    strings = setting["strings"]
    if type(strings) == list:
        if string in strings:
            return strings.index(string)
        else:
            return strings.index(setting["default"])
    else:
        string = ''.join(i for i in string if i.isdigit() or i in '-./\\')
        value = literal_eval(string)
        values = setting["values"]
        if value in values:
            return values.index(value)
        else:
            return values.index(setting["default"])

def convertSettingValueToString(settingName, value):
    setting = ODDSettings.SD[settingName]
    strings = setting["strings"]
    if type(strings) == list:
        if type(value) is not str and value >= 0 and value < len(setting["strings"]):
            # value is index into strings list.
            return setting["strings"][value]
        elif type(value) is str and value in setting["values"]:
            # index of value in values list is index into strings list.
            return setting["strings"][setting["values"].index(value)]
        else:
            return setting["default"]
    else:
        # value is index into values list.
        values = setting["values"]
        return strings(values[value])

class ODDSettings(QObject):
    # Settings Data
    isFirstRun = True
    instances = []
    SD = {
            "direction": {
                    "default":"auto",
                    "flags"  :["perInstance"],
                    "initial":lambda self: self.setUiValuesForDirection(self.readSetting("direction")),
            },
            "display": {
                    "default":"thumbnails",
                    "flags"  :["perInstance"],
                    "initial":lambda self: self.setUiValuesForDisplay(self.readSetting("display")),
            },
            "grid": {
                    "default":"false",
                    "depends": {
                        "dependsOn":["display"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "flags"  :["perInstance"],
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
                    "depends": {
                        "dependsOn":["grid", "display"],
                        "evaluator":lambda self: self.settingValue("grid") and self.settingValue("display", True) == "thumbnails",
                    },
                    "flags"  :["perInstance"],
            },
            "refreshOnSave": {
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "refreshPeriodically": {
                    "default":"false",
                    "flags"  :["perInstance"],
            },
            "refreshPeriodicallyChecks": {
                    "default":"15",
                    "strings":["1","2","3","4","5","6","8","10","12","15","20","25","30"],
                    "suffix" :"/sec",
                    "values" :[1000, 500, 333, 250, 200, 167, 125, 100, 83, 67, 50, 40, 33],
                    "depends": {
                            "dependsOn":["refreshPeriodically"],
                            "evaluator": lambda self: self.settingValue("refreshPeriodically"),
                    },
                    "flags"  :["perInstance"],
            },
            "refreshPeriodicallyDelay": {
                    "default":2000,
                    "strings" :lambda msec: ODDSettings.millisecondsToString(msec),
                    "values" :[500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 15000, 20000, 30000, 45000, 60000, 120000],
                    "depends": {
                            "dependsOn":["refreshPeriodically"],
                            "evaluator": lambda self: self.settingValue("refreshPeriodically"),
                    },
                    "flags"  :["perInstance"],
            },
            "thumbAspectLimit": {
                    "default":"1",
                    "min": 1.0,
                    "max": 10.0,
                    "pow":10,
                    "depends": {
                        "dependsOn":["display"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "flags"  :["perInstance"],
            },
            "thumbDisplayScale": {
                    "default":"1.00",
                    "min":0.05,
                    "max":1.00,
                    "depends": {
                        "dependsOn":["display"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "flags"  :["perInstance"],
            },
            "thumbRenderScale": {
                    "default":"1",
                    "strings":["1/16", "1/8", "1/4", "1/2", "1"],
                    "values" :[1.0/16.0, 1.0/8.0, 1.0/4.0, 1.0/2.0, 1],
                    "depends": {
                            "dependsOn":["thumbUseProjectionMethod"],
                            "evaluator": lambda self: self.settingValue("display", True) == "thumbnails" and \
                                                      not self.settingValue("thumbUseProjectionMethod"),
                    },
                    "flags"  :["perInstance"],
            },
            "thumbFadeAmount": {
                    "default":"0.00",
                    "min":0.00,
                    "max":1.00,
                    "depends": {
                        "dependsOn":["display"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "flags"  :["perInstance"],
            },
            "thumbFadeUnfade": {
                    "default":"false",
                    "depends": {
                        "dependsOn":["display"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "flags"  :["perInstance"],
            },
            "thumbShowModified": {
                    "default":"none",
                    "strings":["Don't show", "Corner", "Square", "Circle", "Asterisk", "Big Corner", "Big Square", "Big Circle", "Big Asterisk"],
                    "values" :["none", "corner", "square", "circle", "asterisk", "cornerBig", "squareBig", "circleBig", "asteriskBig"],
                    "depends": {
                        "dependsOn":["display"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "initial":lambda self: self.setUiValuesForThumbShowModified(self.readSetting("thumbShowModified")),
            },
            "tooltipShow": {
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "tooltipThumbLimit": {
                    "default":"4096",
                    "strings":["never","128","256","512","1024","2048","4096","8192","16384","always"],
                    "prefix" :"≤",
                    "suffix" :"px²",
                    "noDeco" :("never", "always"),
                    "values" :[0, 128*128, 256*256, 512*512, 1024*1024, 2048*2048, 4096*4096, 8192*8192, 16384*16384, float("inf")],
                    "depends": {
                            "dependsOn":["tooltipShow"],
                            "evaluator": lambda self: self.settingValue("tooltipShow"),
                    },
                    "initial":lambda self: self.setUiValuesForTooltipThumbLimit(self.readSetting("tooltipThumbLimit")),
            },
            "tooltipThumbSize": {
                    "default":"128",
                    "strings":["64", "96", "128", "160", "192", "256", "384", "512"],
                    "suffix" :"px",
                    "values" :[64, 96, 128, 160, 192, 256, 384, 512],
                    "depends": {
                            "dependsOn":["tooltipShow", "tooltipThumbLimit"],
                            "evaluator": lambda self: self.settingValue("tooltipShow") and self.settingValue("tooltipThumbLimit") != 0,
                    },
                    "initial":lambda self: self.setUiValuesForTooltipThumbSize(self.readSetting("tooltipThumbSize")),
            },
            "showCommonControlsInDocker": {
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "dockerAlignButtonsToSettingsPanel": {
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "thumbUseProjectionMethod": {
                    "default":"true",
                    "initial":lambda self: self.setUiValuesForThumbUseProjectionMethod(self.readSetting("thumbUseProjectionMethod")),
            },
            "excessThumbCacheLimit": {
                    "default":"10",
                    "min":0,
                    "max":1024,
                    #"values":[0,0.25,0.5,1,2,4,8,12,16,24,32,48,64,96,128,192,256,384,512,640,768,1024,1280,1536,2048],
                    "initial":lambda self: self.setUiValuesForExcessThumbCacheLimit(self.readSetting("excessThumbCacheLimit")),
            },
    }
    
    def __init__(self, odd, oddDocker):
        super(ODDSettings, self).__init__()
        print("ODDSettings: init")
        #print(self.SD)
        self.odd = odd
        self.oddDocker = oddDocker
        self.panelSize = QSize()
        self.panelPosition = QPoint()
        
        ODDSettings.instances.append(self)
        print("instances:")
        for i in ODDSettings.instances:
            print(i)
        
        self.setupInstanceSettings()
        
        self.configFlushBuffer = []
        self.configFlushDelay = QTimer(self)
        self.configFlushDelay.setInterval(1000)
        self.configFlushDelay.setSingleShot(True)
        self.configFlushDelay.timeout.connect(self.flushSettingsToConfig)
        
        self.UI = {
                "direction": {
                        "btngrp":None,
                        "btnHorizontal":None,
                        "btnVertical":None,
                        "btnAuto":None,
                },
                "display": {
                        "btngrp":None,
                        "btnThumbnails":None,
                        "btnText":None,
                },
                "grid": {
                        "btn":None
                },
                "gridMode": {
                        "btn":None,
                },
                "refreshOnSave": {
                        "btn":None,
                },
                "refreshPeriodically": {
                        "btn":None,
                },
                "refreshPeriodicallyChecks": {
                        "value":None,
                        "slider":None,
                },
                "refreshPeriodicallyDelay": {
                        "value":None,
                        "slider":None,
                },
                "thumbAspectLimit": {
                        "value":None,
                        "slider":None,
                },
                "thumbDisplayScale": {
                        "value":None,
                        "slider":None,
                },
                "thumbRenderScale": {
                        "value":None,
                        "slider":None,
                },
                "thumbFadeAmount": {
                        "value":None,
                        "slider":None,
                },
                "thumbFadeUnfade": {
                        "btn":None,
                },
                "thumbShowModified": {
                        "btn":None,
                },
                "tooltipShow": {
                        "btn":None,
                },
                "tooltipThumbLimit": {
                        "value":None,
                        "slider":None,
                },
                "tooltipThumbSize": {
                        "value":None,
                        "slider":None,
                },
                "showCommonControlsInDocker": {
                        "btn":None,
                },
                "dockerAlignButtonsToSettingsPanel": {
                        "btn":None,
                },
                "thumbUseProjectionMethod": {
                        "btn":None,
                },
                "excessThumbCacheLimit": {
                        "value":None,
                        "slider":None,
                },
        }
    
    @classmethod
    def cacheSettingsDataDependencies(cls):
        for setting in cls.SD.items():
            sName = setting[0]
            sData = setting[1]
            #print(sName, sData)
            if "depends" in sData:
                depends = sData["depends"]
                if "dependsOn" in depends:
                    dependsOn = depends["dependsOn"]
                    for i in dependsOn:
                        s = cls.SD[i]
                        if not "depends" in s:
                            s["depends"] = {"dependedOnBy":[]}
                        elif not "dependedOnBy" in s["depends"]:
                            s["depends"]["dependedOnBy"] = []
                        cls.SD[i]["depends"]["dependedOnBy"].append(sName)
                        #print(sName, "depends on", i)
        #print(cls.SD)
    
    @classmethod
    def setupGlobalSettings(cls):
        cls.globalSettings = {}
        for setting in cls.SD:
            cls.globalSettings[setting] = cls.readSettingFromConfig(setting)
            #print("setting", setting, "=", cls.globalSettings[setting])
    
    def setupInstanceSettings(self):
        self.settings = {}
        for setting in self.SD:
            if self.settingFlag(setting, "perInstance"):
                self.settings[setting] = self.globalSettings[setting]
                #print("setting", setting, "overriden in instance.")
    
    def settingFlag(self, setting, flag):
        if not "flags" in self.SD[setting]:
            return False
        return flag in self.SD[setting]["flags"]
    
    @classmethod
    def readSettingFromConfig(cls, setting):
        if not setting in cls.SD:
            return None
        return Application.readSetting("OpenDocumentsDocker", setting, str(cls.SD[setting]["default"]))
    
    def readSetting(self, setting):
        if not setting in self.SD:
            return None
        if setting in self.settings:
            return self.settings[setting]
        else:
            return self.globalSettings[setting]
    
    isUpdatingControlsInInstances = False
    def writeSetting(self, setting, value):
        if not setting in self.SD:
            return
            
        if setting in self.settings:
            print("writeSetting for local setting", setting, "with value", value)
            self.settings[setting] = value
            
        else:
            cls = type(self)
            print("writeSetting for global setting", setting, "with value", value)#, end=" ")
            if not cls.isUpdatingControlsInInstances:
                cls.globalSettings[setting] = value
                #print("... done, start updating control in other dockers.")
                if not "initial" in cls.SD[setting]:
                    print("warning: setting", setting, "does not have an 'initial' item.")
                    return
                cls.isUpdatingControlsInInstances = True
                for inst in cls.instances:
                    if inst != self:
                        #print("updating controls for", setting, "in other docker settings", inst)
                        cls.SD[setting]["initial"](inst)
                cls.isUpdatingControlsInInstances = False
            #else:
                #print("... stop, we're just being updated by another docker.")
        
        if not setting in self.configFlushBuffer:
            self.configFlushBuffer.append(setting)
        self.startConfigFlushDelayTimer()
        self.updateControlsEnabledState(setting)
    
    def startConfigFlushDelayTimer(self):
        delay = self.configFlushDelay
        if delay.isActive():
            delay.stop()
        delay.start()
    
    def flushSettingsToConfig(self):
        print("flush")
        for i in self.configFlushBuffer:
            self.writeSettingToConfig(i, self.readSetting(i))
        self.configFlushBuffer.clear()
    
    def writeSettingToConfig(self, setting, value):
        print("write", setting, "=", value)
        if not setting in self.SD:
            return
        Application.writeSetting("OpenDocumentsDocker", setting, str(value))
    
    def updateControlsEnabledState(self, setting):
        if "depends" in self.SD[setting] and "dependedOnBy" in self.SD[setting]["depends"]:
            for i in self.SD[setting]["depends"]["dependedOnBy"]:
                enable = self.SD[i]["depends"]["evaluator"](self)
                if "btn" in self.UI[i]:
                    self.UI[i]["btn"].setEnabled(enable)
                elif "slider" in self.UI[i]:
                    self.UI[i]["slider"].setEnabled(enable)
    
    def settingValue(self, setting, asName=False):
        ui = self.UI[setting]
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
            btn = ui["btngrp"].checkedButton()
            return btn.objectName() if asName else btn
        elif "btn" in ui:
            if "values" in self.SD[setting]:
                return self.SD[setting]["values"][ui["btn"].currentIndex()]
            else:
                return ui["btn"].isChecked()
        return None
    
    def decoratedSettingText(self, setting, text, exceptions=None):
        sd = self.SD[setting]
        if exceptions == None and "noDeco" in sd:
            exceptions = sd["noDeco"]
        if type(exceptions) is str:
            if text == exceptions:
                return text
        elif type(exceptions) is tuple:
            if any(text == x for x in exceptions):
                return text
        prefix = sd["prefix"] if "prefix" in sd else ""
        suffix = sd["suffix"] if "suffix" in sd else ""
        return prefix + text + suffix
    
    def setUiValuesForDisplay(self, setting):
        self.UI["display"]["btnThumbnails"].setChecked(setting=="thumbnails")
        self.UI["display"]["btnText"      ].setChecked(setting=="text")
    
    def changedDisplay(self, checked):
        if checked:
            self.UI["display"]["btnThumbnails"].click()
        else:
            self.UI["display"]["btnText"].click()
    
    def setDisplayToThumbnails(self):
        print("setDisplayToThumbnails")
        self.writeSetting("display", "thumbnails")
        self.oddDocker.setDockerDirection(self.readSetting("direction"))
        self.oddDocker.refreshOpenDocuments()
        self.oddDocker.updateScrollBarPolicy()
        
        self.dockerDisplayToggleButton.setChecked(True)
    
    def setDisplayToText(self):
        print("setDisplayToText")
        self.writeSetting("display", "text")
        self.oddDocker.setDockerDirection(self.readSetting("direction"))
        self.oddDocker.refreshOpenDocuments()
        self.oddDocker.updateScrollBarPolicy()
        
        self.dockerDisplayToggleButton.setChecked(False)
    
    def setUiValuesForDirection(self, setting):
        self.UI["direction"]["btnHorizontal"].setChecked(setting=="horizontal")
        self.UI["direction"]["btnVertical"  ].setChecked(setting=="vertical")
        self.UI["direction"]["btnAuto"      ].setChecked(setting=="auto")
    
    def setDirectionToHorizontal(self):
        print("setDirectionToHorizontal")
        self.writeSetting("direction", "horizontal")
        self.oddDocker.setDockerDirection("horizontal")
    
    def setDirectionToVertical(self):
        print("setDirectionToVertical")
        self.writeSetting("direction", "vertical")
        self.oddDocker.setDockerDirection("vertical")
    
    def setDirectionToAuto(self):
        print("setDirectionToAuto")
        self.writeSetting("direction", "auto")
        self.oddDocker.setDockerDirection("auto")
    
    def changedGrid(self, state):
        setting = str(state==2).lower()
        print("changedGrid to", setting)
        self.writeSetting("grid", setting)
        
        if self.readSetting("display") != "thumbnails":
            return
        
        self.oddDocker.list.invalidateItemRectsCache()
        self.oddDocker.list.updateGeometries()
        self.oddDocker.list.viewport().update()
        self.startRefreshAllDelayTimer()
    
    def changedGridMode(self, index):
        setting = self.settingValue("gridMode")
        print("changedGridMode to", setting)
        self.writeSetting("gridMode", setting)
        
        if self.readSetting("display") != "thumbnails":
            return
        
        self.oddDocker.list.invalidateItemRectsCache()
        self.oddDocker.list.updateGeometries()
        self.oddDocker.list.viewport().update()
        self.startRefreshAllDelayTimer()
    
    def changedThumbAspectLimitSlider(self, value):
        setting = "{:1.6g}".format(pow(10, value/200.0))
        self.UI["thumbAspectLimit"]["value"].setText("1:{:1.3g}".format(float(setting)))
        self.writeSetting("thumbAspectLimit", setting)
        print("changedThumbAspectLimitSlider: value, setting: ", value, setting)
        #print("find original value:", value/200.0, "->", setting, "->", "{:1.3g}".format(math.log10(float(setting))))
        
        if self.readSetting("display") != "thumbnails":
            return
        
        self.oddDocker.list.invalidateItemRectsCache()
        self.oddDocker.list.updateGeometries()
        self.oddDocker.list.viewport().update()
        self.startRefreshAllDelayTimer()
    
    def changedThumbDisplayScaleSlider(self, value):
        if self.sender() == self.dockerThumbnailsDisplayScaleSlider:
            self.UI["thumbDisplayScale"]["slider"].setValue(value)
            return
        setting = "{:4.2f}".format(self.settingValue("thumbDisplayScale"))
        self.UI["thumbDisplayScale"]["value"].setText(setting)
        self.writeSetting("thumbDisplayScale", setting)
        print("changedThumbDisplayScaleSlider to ", setting)
        
        if self.readSetting("display") != "thumbnails":
            return
        
        self.oddDocker.list.invalidateItemRectsCache()
        self.oddDocker.list.updateGeometries()
        self.oddDocker.list.viewport().update()
        self.startRefreshAllDelayTimer()
        
        self.dockerThumbnailsDisplayScaleSlider.setValue(value)
    
    def changedThumbRenderScaleSlider(self, value):
        setting = convertSettingValueToString("thumbRenderScale", value)
        self.UI["thumbRenderScale"]["value"].setText(setting)
        self.writeSetting("thumbRenderScale", setting)
        
        self.startRefreshAllDelayTimer()
    
    def changedThumbFadeAmountSlider(self, value):
        setting = "{:4.2f}".format(self.settingValue("thumbFadeAmount"))
        self.UI["thumbFadeAmount"]["value"].setText(setting)
        self.writeSetting("thumbFadeAmount", setting)
        self.oddDocker.list.viewport().update()
    
    def changedThumbFadeUnfade(self, state):
        setting = str(state==2).lower()
        print("changedThumbFadeUnfade to", setting)
        self.writeSetting("thumbFadeUnfade", setting)
    
    def setUiValuesForThumbShowModified(self, setting):
        self.UI["thumbShowModified"]["btn"].setCurrentText(convertSettingValueToString("thumbShowModified", setting))

    def changedThumbShowModified(self, index):
        setting = self.settingValue("thumbShowModified")
        print("changedThumbShowModified to", setting)
        self.writeSetting("thumbShowModified", setting)
        self.oddDocker.list.viewport().update()
    
    def highlightedThumbShowModified(self, index):
        setting = self.SD["thumbShowModified"]["values"][index]
        self.previewThumbnailsShowModified = setting
        self.oddDocker.list.viewport().update()
    
    def unhighlightedThumbShowModified(self):
        self.previewThumbnailsShowModified = ""
        self.oddDocker.list.viewport().update()
    
    def changedTooltipShow(self, state):
        setting = str(state==2).lower()
        print("changedTooltipShow to", setting)
        self.writeSetting("tooltipShow", setting)
    
    def setUiValuesForTooltipThumbLimit(self, setting):
        self.UI["tooltipThumbLimit"]["slider"].setValue(
                convertSettingStringToValue("tooltipThumbLimit", setting)
        )
    
    def changedTooltipThumbLimitSlider(self, value):
        setting = convertSettingValueToString("tooltipThumbLimit", value)
        self.UI["tooltipThumbLimit"]["value"].setText(
                self.decoratedSettingText("tooltipThumbLimit", setting)
        )
        self.writeSetting("tooltipThumbLimit", setting)
    
    def setUiValuesForTooltipThumbSize(self, setting):
        self.UI["tooltipThumbSize"]["slider"].setValue(
                convertSettingStringToValue("tooltipThumbSize", setting)
        )
    
    def changedTooltipThumbSizeSlider(self, value):
        setting = convertSettingValueToString("tooltipThumbSize", value)
        self.UI["tooltipThumbSize"]["value"].setText(
                self.decoratedSettingText("tooltipThumbSize", setting)
        )
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
            self.UI["refreshPeriodically"]["btn"].setChecked(state==1)
        else:
            self._changedRefreshPeriodically(state)
        
    def _changedRefreshPeriodically(self, state):
        setting = str(state==2).lower()
        print("changedRefreshPeriodically to", setting)
        self.writeSetting("refreshPeriodically", setting)
        if state == 2:
            self.oddDocker.imageChangeDetectionTimer.start()
        else:
            self.oddDocker.imageChangeDetectionTimer.stop()
            self.oddDocker.refreshTimer.stop()
        
        self.dockerRefreshPeriodicallyToggleButton.setChecked(state==2)
    
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
    
    def setUiValuesForThumbUseProjectionMethod(self, setting):
        self.UI["thumbUseProjectionMethod"]["btn"].setChecked(setting == "true")
    
    def changedThumbnailUseProjectionMethod(self, state):
        setting = str(state==2).lower()
        print("changedThumbnailUseProjectionMethod to", setting)
        self.writeSetting("thumbUseProjectionMethod", setting)
        
        self.startRefreshAllDelayTimer()
        
    def startRefreshAllDelayTimer(self):
        if not hasattr(self.oddDocker, "refreshAllDelay"):
            return
        delay = self.oddDocker.refreshAllDelay
        if delay.isActive():
            delay.stop()
        delay.start()
    
    def changedRefreshPeriodicallyChecksSlider(self, value):
        setting = convertSettingValueToString("refreshPeriodicallyChecks", value)
        self.UI["refreshPeriodicallyChecks"]["value"].setText(
            self.decoratedSettingText("refreshPeriodicallyChecks", setting)
        )
        self.oddDocker.imageChangeDetectionTimer.setInterval(
                self.settingValue("refreshPeriodicallyChecks")
        )
        self.writeSetting("refreshPeriodicallyChecks", setting)
    
    def changedRefreshPeriodicallyDelaySlider(self, value):
        setting = convertSettingValueToString("refreshPeriodicallyDelay", value)
        self.UI["refreshPeriodicallyDelay"]["value"].setText(
            self.decoratedSettingText("refreshPeriodicallyDelay", setting)
        )
        self.oddDocker.refreshTimer.setInterval(
                self.settingValue("refreshPeriodicallyDelay")
        )
        self.writeSetting("refreshPeriodicallyDelay", str(self.SD["refreshPeriodicallyDelay"]["values"][value]))
    
    def setUiValuesForExcessThumbCacheLimit(self, setting):
        self.UI["excessThumbCacheLimit"]["slider"].setValue(
                int(setting)
        )
    
    def changedExcessThumbCacheLimitSlider(self, value):
        setting = str(value)
        self.UI["excessThumbCacheLimit"]["value"].setText(setting + "mb")
        self.writeSetting("excessThumbCacheLimit", setting)
        self.odd.evictExcessUnusedCache()
        
    def createPanel(self):
        app = Application
        
        self.panel = QFrame(self.oddDocker, Qt.Popup)
        self.panel.setFrameShape(QFrame.StyledPanel)
        self.panelLayout = QVBoxLayout()
        
        self.UI["display"]["btngrp"] = QButtonGroup(self.panel)
        self.UI["direction"]["btngrp"] = QButtonGroup(self.panel)
        
        self.panelListHeading = QHBoxLayout()
        self.panelListHeadingLabel = QLabel("List", self.panel)
        self.panelListHeadingLine = QLabel("", self.panel)
        self.panelListHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.panelDirectionLayout = QVBoxLayout()
        self.panelDirectionLabel = QLabel("Direction", self.panel)
        self.UI["direction"]["btnHorizontal"] = QRadioButton("Horizontal", self.panel)
        self.UI["direction"]["btnVertical"  ] = QRadioButton("Vertical", self.panel)
        self.UI["direction"]["btnAuto"      ] = QRadioButton("Auto", self.panel)
        self.UI["direction"]["btnAuto"      ].setToolTip("The list will be arranged on its longest side.")
        
        self.panelDisplayAndDirectionLayout = QHBoxLayout()
        self.panelDisplayLayout = QVBoxLayout()
        self.panelDisplayLabel = QLabel("Display", self.panel)
        self.UI["display"]["btnThumbnails"] = QRadioButton("Thumbnails", self.panel)
        self.UI["display"]["btnThumbnails"].setObjectName("thumbnails")
        self.UI["display"]["btnText"      ] = QRadioButton("Text", self.panel)
        self.UI["display"]["btnText"      ].setObjectName("text")
        
        self.dockerDisplayToggleButton = QToolButton()
        self.dockerDisplayToggleButton.setCheckable(True)
        self.dockerDisplayToggleButton.setIcon(Application.icon('folder-pictures'))
        self.dockerDisplayToggleButton.setChecked(self.readSetting("display") == "thumbnails")
        self.dockerDisplayToggleButton.clicked.connect(self.changedDisplay)
        
        self.panelGridLayout = QHBoxLayout()
        self.UI["grid"]["btn"] = QCheckBox("Grid", self.panel)
        self.UI["grid"]["btn"].setChecked(self.readSetting("grid") == "true")
        self.UI["grid"]["btn"].stateChanged.connect(self.changedGrid)
        self.UI["grid"]["btn"].setToolTip(
                "Lay thumbnails out in a grid if possible.\n\n" +
                "Thumbnail display scale must be 0.5 or less.\n" +
                "When the list is vertical, items are arranged left-to-right, row-by-row.\n" +
                "When the list is horizontal, items are arranged top-to-bottom, column-by-column."
        )
        
        setting = self.readSetting("gridMode")
        self.UI["gridMode"]["btn"] = QComboBox()
        self.UI["gridMode"]["btn"].addItems(self.SD["gridMode"]["strings"])
        self.UI["gridMode"]["btn"].setCurrentText(convertSettingValueToString("gridMode", setting))
        for i in range(len(self.SD["gridMode"]["tooltips"])):
            self.UI["gridMode"]["btn"].setItemData(i, self.SD["gridMode"]["tooltips"][i], Qt.ToolTipRole)
        self.UI["gridMode"]["btn"].activated.connect(self.changedGridMode)
        
        self.panelThumbnailsLabel = QLabel("Thumbnails", self.panel)
        
        setting = self.readSetting("thumbUseProjectionMethod")
        self.UI["thumbUseProjectionMethod"]["btn"] = QCheckBox("Use projection method", self.panel)
        self.setUiValuesForThumbUseProjectionMethod(setting)
        self.UI["thumbUseProjectionMethod"]["btn"].stateChanged.connect(self.changedThumbnailUseProjectionMethod)
        self.UI["thumbUseProjectionMethod"]["btn"].setToolTip(
                "If enabled, ODD will generate thumbnails with the projection method.\n" +
                "If disabled, ODD will use the thumbnail method.\n" +
                "Projection should be faster. If there are no issues, leave this enabled."
        )
        
        setting = self.readSetting("thumbAspectLimit")
        self.panelThumbnailsAspectLimitLayout = QHBoxLayout()
        self.panelThumbnailsAspectLimitLabel = QLabel("Aspect limit", self.panel)
        self.UI["thumbAspectLimit"]["value" ] = QLabel("1:{:1.3g}".format(float(setting)), self.panel)
        self.UI["thumbAspectLimit"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["thumbAspectLimit"]["slider"].setRange(0, 200)
        self.UI["thumbAspectLimit"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["thumbAspectLimit"]["slider"].setTickInterval(1)
        self.UI["thumbAspectLimit"]["slider"].setValue(int(math.log10(float(setting))*200.0))
        self.UI["thumbAspectLimit"]["slider"].setToolTip(
                "The maximum deviation a document size can be from square before its thumbnail is shrunk.\n\n" +
                "For example, 1:1 forces all thumbnails to be square, 1:2 allows thumbnails to be up to twice as long as their width.\n" +
                "Higher values give better representation of wide/tall documents, at the cost of ease of list navigation."
        )
        
        setting = self.readSetting("thumbDisplayScale")
        self.panelThumbnailsDisplayScaleLayout = QHBoxLayout()
        self.panelThumbnailsDisplayScaleLabel = QLabel("Display scale", self.panel)
        self.UI["thumbDisplayScale"]["value" ] = QLabel(setting, self.panel)
        self.UI["thumbDisplayScale"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["thumbDisplayScale"]["slider"].setRange(0, 95)
        self.UI["thumbDisplayScale"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["thumbDisplayScale"]["slider"].setTickInterval(1)
        self.UI["thumbDisplayScale"]["slider"].setPageStep(5)
        self.UI["thumbDisplayScale"]["slider"].setValue(round((float(setting)-0.05)*100.0))
        
        self.dockerThumbnailsDisplayScaleSlider = QSlider(Qt.Horizontal)
        self.dockerThumbnailsDisplayScaleSlider.setRange(       self.UI["thumbDisplayScale"]["slider"].minimum(),
                                                                self.UI["thumbDisplayScale"]["slider"].maximum())
        self.dockerThumbnailsDisplayScaleSlider.setTickPosition(self.UI["thumbDisplayScale"]["slider"].tickPosition())
        self.dockerThumbnailsDisplayScaleSlider.setTickInterval(self.UI["thumbDisplayScale"]["slider"].tickInterval())
        self.dockerThumbnailsDisplayScaleSlider.setPageStep(    self.UI["thumbDisplayScale"]["slider"].pageStep())
        self.dockerThumbnailsDisplayScaleSlider.setValue(       self.UI["thumbDisplayScale"]["slider"].value())
        
        setting = self.readSetting("thumbRenderScale")
        self.panelThumbnailsRenderScaleLayout = QHBoxLayout()
        self.panelThumbnailsRenderScaleLabel = QLabel("Render scale", self.panel)
        self.UI["thumbRenderScale"]["value" ] = QLabel(setting, self.panel)
        self.UI["thumbRenderScale"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["thumbRenderScale"]["slider"].setRange(0, len(self.SD["thumbRenderScale"]["values"])-1)
        self.UI["thumbRenderScale"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["thumbRenderScale"]["slider"].setTickInterval(1)
        self.UI["thumbRenderScale"]["slider"].setValue(
                convertSettingStringToValue("thumbRenderScale", setting)
        )
        self.UI["thumbRenderScale"]["slider"].setToolTip(
                "Thumbnails in the list can be generated at a reduced size then scaled up.\n" +
                "This can improve performance when using the thumbnail method."
        )
        
        setting = self.readSetting("thumbFadeAmount")
        self.panelThumbnailsFadeAmountLayout = QHBoxLayout()
        self.panelThumbnailsFadeAmountLabel = QLabel("Fade amount", self.panel)
        self.UI["thumbFadeAmount"]["value" ] = QLabel(setting, self.panel)
        self.UI["thumbFadeAmount"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["thumbFadeAmount"]["slider"].setRange(0, 100)
        self.UI["thumbFadeAmount"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["thumbFadeAmount"]["slider"].setTickInterval(1)
        self.UI["thumbFadeAmount"]["slider"].setValue(round(float(setting)*100))
        
        self.panelThumbnailsFadeAmountControlsLayout = QHBoxLayout()
        self.UI["thumbFadeUnfade"]["btn"] = QCheckBox(self.panel)
        self.UI["thumbFadeUnfade"]["btn"].setChecked(self.readSetting("thumbFadeUnfade") == "true")
        self.UI["thumbFadeUnfade"]["btn"].stateChanged.connect(self.changedThumbFadeUnfade)
        self.UI["thumbFadeUnfade"]["btn"].setToolTip("Un-fade on mouse hover.")
        
        setting = self.readSetting("thumbShowModified")
        self.panelThumbnailsShowModifiedLayout = QHBoxLayout()
        self.panelThumbnailsShowModifiedLabel = QLabel("Modified indicator", self.panel)
        self.UI["thumbShowModified"]["btn"] = QComboBox(self.panel)
        self.UI["thumbShowModified"]["btn"].addItems(self.SD["thumbShowModified"]["strings"])
        self.setUiValuesForThumbShowModified(setting)
        self.UI["thumbShowModified"]["btn"].setToolTip(
                "An icon to show on modified document thumbnails.\n" +
                "A preview will be shown as you highlight options (if there are visible thumbnails)."
        )
        self.previewThumbnailsShowModified = ""
        
        self.UI["refreshOnSave"]["btn"] = QCheckBox("Refresh on save", self.panel)
        self.UI["refreshOnSave"]["btn"].setChecked(self.readSetting("refreshOnSave") == "true")
        self.UI["refreshOnSave"]["btn"].stateChanged.connect(self.changedRefreshOnSave)
        self.UI["refreshOnSave"]["btn"].setToolTip("When you save an image, refresh its thumbnail automatically.")
        
        self.UI["refreshPeriodically"]["btn"] = QCheckBox("Refresh periodically (experimental)", self.panel)
        self.UI["refreshPeriodically"]["btn"].setChecked(self.readSetting("refreshPeriodically") == "true")
        self.UI["refreshPeriodically"]["btn"].stateChanged.connect(self.changedRefreshPeriodically)
        self.UI["refreshPeriodically"]["btn"].setToolTip(
                "Automatically refresh the thumbnail for the active image if a change is detected.\n\n" + 
                "Checks for changes to the image so-many times each second.\n" +
                "Then tries to refresh the thumbnail every so-many seconds.\n" +
                "May not catch quick changes if they happen between checks.\n" +
                "Aggressive settings may degrade performance."
        )
        
        self.dockerRefreshPeriodicallyToggleButton = QToolButton()
        self.dockerRefreshPeriodicallyToggleButton.setCheckable(True)
        self.dockerRefreshPeriodicallyToggleButton.setIcon(Application.icon('animation_play'))
        self.dockerRefreshPeriodicallyToggleButton.setChecked(self.UI["refreshPeriodically"]["btn"].isChecked())
        self.dockerRefreshPeriodicallyToggleButton.clicked.connect(self.changedRefreshPeriodically)
        
        setting = self.readSetting("refreshPeriodicallyChecks")
        self.panelThumbnailsRefreshPeriodicallyChecksLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyChecksLabel = QLabel("Checks", self.panel)
        self.UI["refreshPeriodicallyChecks"]["value"]  = QLabel(self.decoratedSettingText("refreshPeriodicallyChecks", setting), self.panel)
        self.UI["refreshPeriodicallyChecks"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["refreshPeriodicallyChecks"]["slider"].setRange(0, len(self.SD["refreshPeriodicallyChecks"]["values"])-1)
        self.UI["refreshPeriodicallyChecks"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["refreshPeriodicallyChecks"]["slider"].setTickInterval(1)
        self.UI["refreshPeriodicallyChecks"]["slider"].setValue(
                convertSettingStringToValue("refreshPeriodicallyChecks", setting)
        )
        self.UI["refreshPeriodicallyChecks"]["slider"].setToolTip("Number of times each second the image is checked for activity.")
        
        setting = self.readSetting("refreshPeriodicallyDelay")
        settingValue = convertSettingStringToValue("refreshPeriodicallyDelay", setting)
        settingString = convertSettingValueToString("refreshPeriodicallyDelay", settingValue)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout = QHBoxLayout()
        self.panelThumbnailsRefreshPeriodicallyDelayLabel = QLabel("Delay by", self.panel)
        self.UI["refreshPeriodicallyDelay"]["value" ] = QLabel(settingString, self.panel)
        self.UI["refreshPeriodicallyDelay"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["refreshPeriodicallyDelay"]["slider"].setRange(0, len(self.SD["refreshPeriodicallyDelay"]["values"])-1)
        self.UI["refreshPeriodicallyDelay"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["refreshPeriodicallyDelay"]["slider"].setTickInterval(1)
        self.UI["refreshPeriodicallyDelay"]["slider"].setValue(settingValue)
        self.UI["refreshPeriodicallyDelay"]["slider"].setToolTip("How long after the last detected change to refresh the thumbnail.")
        
        self.panelTooltipsHeading = QHBoxLayout()
        self.UI["tooltipShow"]["btn"] = QCheckBox("Tooltips", self.panel)
        self.UI["tooltipShow"]["btn"].setChecked(self.readSetting("tooltipShow") == "true")
        self.UI["tooltipShow"]["btn"].stateChanged.connect(self.changedTooltipShow)
        self.panelTooltipsHeadingLine = QLabel("", self.panel)
        self.panelTooltipsHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        setting = self.readSetting("tooltipThumbLimit")
        self.panelTooltipThumbnailLimitLayout = QHBoxLayout()
        self.panelTooltipThumbnailLimitLabel = QLabel("Limit", self.panel)
        self.UI["tooltipThumbLimit"]["value" ] = QLabel(self.decoratedSettingText("tooltipThumbLimit", setting), self.panel)
        self.UI["tooltipThumbLimit"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["tooltipThumbLimit"]["slider"].setRange(0, len(self.SD["tooltipThumbLimit"]["values"])-1)
        self.UI["tooltipThumbLimit"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["tooltipThumbLimit"]["slider"].setTickInterval(1)
        self.setUiValuesForTooltipThumbLimit(setting)
        self.UI["tooltipThumbLimit"]["slider"].setToolTip(
                "Thumbnails in tooltips will be generated for images up to the chosen size."
        )
        
        setting = self.readSetting("tooltipThumbSize")
        self.panelTooltipThumbnailSizeLayout = QHBoxLayout()
        self.panelTooltipThumbnailSizeLabel = QLabel("Size", self.panel)
        self.UI["tooltipThumbSize"]["value" ] = QLabel(self.decoratedSettingText("tooltipThumbSize", setting), self.panel)
        self.UI["tooltipThumbSize"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["tooltipThumbSize"]["slider"].setRange(0, len(self.SD["tooltipThumbSize"]["values"])-1)
        self.UI["tooltipThumbSize"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["tooltipThumbSize"]["slider"].setTickInterval(1)
        self.setUiValuesForTooltipThumbSize(setting)
        
        self.panelMiscHeading = QHBoxLayout()
        self.panelMiscHeadingLabel = QLabel("Miscellaneous", self.panel)
        self.panelMiscHeadingLine = QLabel("", self.panel)
        self.panelMiscHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.UI["showCommonControlsInDocker"]["btn"] = QCheckBox("Show commonly used settings in the docker", self.panel)
        self.UI["showCommonControlsInDocker"]["btn"].setChecked(self.readSetting("showCommonControlsInDocker") == "true")
        self.UI["showCommonControlsInDocker"]["btn"].stateChanged.connect(self.changedShowCommonControlsInDocker)
        self.UI["showCommonControlsInDocker"]["btn"].setToolTip(
                "Make some of the most-used of these settings adjustable in the docker itself.\n\n" +
                "Included are a slider for the list thumbnail display scale,\n" +
                "and toggle buttons for changing display mode and enabling periodic thumbnail refresh."
        )
        
        self.UI["dockerAlignButtonsToSettingsPanel"]["btn"] = QCheckBox("Move docker buttons to align with settings panel", self.panel)
        self.UI["dockerAlignButtonsToSettingsPanel"]["btn"].setChecked(self.readSetting("dockerAlignButtonsToSettingsPanel") == "true")
        self.UI["dockerAlignButtonsToSettingsPanel"]["btn"].stateChanged.connect(self.changedDockerAlignButtonsToSettingsPanel)
        self.UI["dockerAlignButtonsToSettingsPanel"]["btn"].setToolTip(
                "Allow the docker buttons to move around the docker so that the settings button will be close to the settings panel.\n\n" +
                "This panel will try to appear in a place that obscures the docker list as little as possible.\n" +
                "This means it may appear on the other side of the docker, far from the default position of the settings button.\n" +
                "This setting allows the docker buttons to move to the side of the docker where the settings button will be closest.\n" +
                "The refresh and settings buttons may also switch position."
        )
        
        self.panelThumbCacheLabel = QLabel("Thumbnail Cache", self.panel)
        
        setting = self.readSetting("excessThumbCacheLimit")
        self.panelExcessThumbCacheLimitLayout = QHBoxLayout()
        self.panelExcessThumbCacheLimitLabel = QLabel("Unused limit", self.panel)
        self.UI["excessThumbCacheLimit"]["value" ] = QLabel(setting + "mb", self.panel)
        self.UI["excessThumbCacheLimit"]["slider"] = QSlider(Qt.Horizontal, self.panel)
        self.UI["excessThumbCacheLimit"]["slider"].setRange(0, 1024)
        self.UI["excessThumbCacheLimit"]["slider"].setTickPosition(QSlider.NoTicks)
        self.UI["excessThumbCacheLimit"]["slider"].setTickInterval(1)
        self.setUiValuesForExcessThumbCacheLimit(setting)
        self.UI["excessThumbCacheLimit"]["slider"].setToolTip(
                "Limit the amount of memory allowed to keep unused but potentially reusable thumbnails in cache.\n\n" +
                "Unused thumbnails remain in memory so they can be reused. This is faster than generating new ones.\n" +
                "For example, caching the tooltip thumbnail reduces lag when hovering the mouse over the list.\n" +
                "When the size of these unused thumbnails exceeds this limit, the least recently used ones will be discarded."
        )
        
        settingDisplay = self.readSetting("display")
        self.UI["display"]["btngrp"       ].addButton(self.UI["display"]["btnThumbnails"])
        self.UI["display"]["btngrp"       ].addButton(self.UI["display"]["btnText"      ])
        self.setUiValuesForDisplay(settingDisplay)
        self.UI["display"]["btnThumbnails"].clicked.connect(self.setDisplayToThumbnails)
        self.UI["display"]["btnText"      ].clicked.connect(self.setDisplayToText)
        settingDirection = self.readSetting("direction")
        self.UI["direction"]["btngrp"       ].addButton(self.UI["direction"]["btnHorizontal"])
        self.UI["direction"]["btngrp"       ].addButton(self.UI["direction"]["btnVertical"  ])
        self.UI["direction"]["btngrp"       ].addButton(self.UI["direction"]["btnAuto"      ])
        self.setUiValuesForDirection(settingDirection)
        self.UI["direction"]["btnHorizontal"].clicked.connect(self.setDirectionToHorizontal)
        self.UI["direction"]["btnVertical"  ].clicked.connect(self.setDirectionToVertical)
        self.UI["direction"]["btnAuto"      ].clicked.connect(self.setDirectionToAuto)
        
        sliderLayoutStretchAmount = (4, 4, 10)
        
        self.panelListHeading.addWidget(self.panelListHeadingLabel)
        self.panelListHeading.addWidget(self.panelListHeadingLine)
        self.panelListHeading.setStretch(0, 1)
        self.panelListHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelListHeading)
        self.panelDirectionLayout.addWidget(self.panelDirectionLabel)
        self.panelDirectionLayout.addWidget(self.UI["direction"]["btnHorizontal"])
        self.panelDirectionLayout.addWidget(self.UI["direction"]["btnVertical"])
        self.panelDirectionLayout.addWidget(self.UI["direction"]["btnAuto"])
        self.panelDisplayAndDirectionLayout.addLayout(self.panelDirectionLayout)
        self.panelDisplayLayout.addWidget(self.panelDisplayLabel)
        self.panelDisplayLayout.addWidget(self.UI["display"]["btnThumbnails"])
        self.panelDisplayLayout.addWidget(self.UI["display"]["btnText"])
        self.panelGridLayout.addWidget(self.UI["grid"]["btn"])
        self.panelGridLayout.addWidget(self.UI["gridMode"]["btn"])
        self.panelDisplayLayout.addLayout(self.panelGridLayout)
        self.panelDisplayAndDirectionLayout.addLayout(self.panelDisplayLayout)
        self.panelLayout.addLayout(self.panelDisplayAndDirectionLayout)
        self.panelLayout.addWidget(self.panelThumbnailsLabel)
        self.panelLayout.addWidget(self.UI["thumbUseProjectionMethod"]["btn"])
        self.panelThumbnailsAspectLimitLayout.addWidget(self.panelThumbnailsAspectLimitLabel)
        self.panelThumbnailsAspectLimitLayout.addWidget(self.UI["thumbAspectLimit"]["value"])
        self.panelThumbnailsAspectLimitLayout.addWidget(self.UI["thumbAspectLimit"]["slider"])
        self.panelThumbnailsAspectLimitLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelThumbnailsAspectLimitLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelThumbnailsAspectLimitLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelThumbnailsAspectLimitLayout)
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.panelThumbnailsDisplayScaleLabel)
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.UI["thumbDisplayScale"]["value"])
        self.panelThumbnailsDisplayScaleLayout.addWidget(self.UI["thumbDisplayScale"]["slider"])
        self.panelThumbnailsDisplayScaleLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelThumbnailsDisplayScaleLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelThumbnailsDisplayScaleLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelThumbnailsDisplayScaleLayout)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.panelThumbnailsRenderScaleLabel)
        self.panelThumbnailsRenderScaleLayout.addWidget(self.UI["thumbRenderScale"]["value"])
        self.panelThumbnailsRenderScaleLayout.addWidget(self.UI["thumbRenderScale"]["slider"])
        self.panelThumbnailsRenderScaleLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelThumbnailsRenderScaleLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelThumbnailsRenderScaleLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelThumbnailsRenderScaleLayout)
        self.panelThumbnailsFadeAmountLayout.addWidget(self.panelThumbnailsFadeAmountLabel)
        self.panelThumbnailsFadeAmountLayout.addWidget(self.UI["thumbFadeAmount"]["value"])
        self.panelThumbnailsFadeAmountControlsLayout.addWidget(self.UI["thumbFadeAmount"]["slider"])
        self.panelThumbnailsFadeAmountControlsLayout.addWidget(self.UI["thumbFadeUnfade"]["btn"])
        self.panelThumbnailsFadeAmountControlsLayout.setStretch(0, 19)
        self.panelThumbnailsFadeAmountControlsLayout.setStretch(1, 1)
        self.panelThumbnailsFadeAmountLayout.addLayout(self.panelThumbnailsFadeAmountControlsLayout)
        self.panelThumbnailsFadeAmountLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelThumbnailsFadeAmountLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelThumbnailsFadeAmountLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelThumbnailsFadeAmountLayout)
        self.panelThumbnailsShowModifiedLayout.addWidget(self.panelThumbnailsShowModifiedLabel)
        self.panelThumbnailsShowModifiedLayout.addWidget(self.UI["thumbShowModified"]["btn"])
        self.panelThumbnailsShowModifiedLayout.setStretch(0, 4)
        self.panelThumbnailsShowModifiedLayout.setStretch(1, 5)
        self.panelLayout.addLayout(self.panelThumbnailsShowModifiedLayout)
        self.panelLayout.addWidget(self.UI["refreshOnSave"]["btn"])
        self.panelLayout.addWidget(self.UI["refreshPeriodically"]["btn"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyChecksLabel)
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.UI["refreshPeriodicallyChecks"]["value"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.addWidget(self.UI["refreshPeriodicallyChecks"]["slider"])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelThumbnailsRefreshPeriodicallyChecksLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelThumbnailsRefreshPeriodicallyChecksLayout)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.panelThumbnailsRefreshPeriodicallyDelayLabel)
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.UI["refreshPeriodicallyDelay"]["value"])
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.addWidget(self.UI["refreshPeriodicallyDelay"]["slider"])
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelThumbnailsRefreshPeriodicallyDelayLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelThumbnailsRefreshPeriodicallyDelayLayout)
        self.panelTooltipsHeading.addWidget(self.UI["tooltipShow"]["btn"])
        self.panelTooltipsHeading.addWidget(self.panelTooltipsHeadingLine)
        self.panelTooltipsHeading.setStretch(0, 1)
        self.panelTooltipsHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelTooltipsHeading)
        self.panelTooltipThumbnailLimitLayout.addWidget(self.panelTooltipThumbnailLimitLabel)
        self.panelTooltipThumbnailLimitLayout.addWidget(self.UI["tooltipThumbLimit"]["value"])
        self.panelTooltipThumbnailLimitLayout.addWidget(self.UI["tooltipThumbLimit"]["slider"])
        self.panelTooltipThumbnailLimitLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelTooltipThumbnailLimitLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelTooltipThumbnailLimitLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelTooltipThumbnailLimitLayout)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.panelTooltipThumbnailSizeLabel)
        self.panelTooltipThumbnailSizeLayout.addWidget(self.UI["tooltipThumbSize"]["value"])
        self.panelTooltipThumbnailSizeLayout.addWidget(self.UI["tooltipThumbSize"]["slider"])
        self.panelTooltipThumbnailSizeLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelTooltipThumbnailSizeLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelTooltipThumbnailSizeLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelTooltipThumbnailSizeLayout)
        self.panelMiscHeading.addWidget(self.panelMiscHeadingLabel)
        self.panelMiscHeading.addWidget(self.panelMiscHeadingLine)
        self.panelMiscHeading.setStretch(0, 1)
        self.panelMiscHeading.setStretch(1, 99)
        self.panelLayout.addLayout(self.panelMiscHeading)
        self.panelLayout.addWidget(self.UI["showCommonControlsInDocker"]["btn"])
        self.panelLayout.addWidget(self.UI["dockerAlignButtonsToSettingsPanel"]["btn"])
        self.panelLayout.addWidget(self.panelThumbCacheLabel)
        self.panelExcessThumbCacheLimitLayout.addWidget(self.panelExcessThumbCacheLimitLabel)
        self.panelExcessThumbCacheLimitLayout.addWidget(self.UI["excessThumbCacheLimit"]["value"])
        self.panelExcessThumbCacheLimitLayout.addWidget(self.UI["excessThumbCacheLimit"]["slider"])
        self.panelExcessThumbCacheLimitLayout.setStretch(0, sliderLayoutStretchAmount[0])
        self.panelExcessThumbCacheLimitLayout.setStretch(1, sliderLayoutStretchAmount[1])
        self.panelExcessThumbCacheLimitLayout.setStretch(2, sliderLayoutStretchAmount[2])
        self.panelLayout.addLayout(self.panelExcessThumbCacheLimitLayout)
        self.panel.setLayout(self.panelLayout)
        self.panel.setMinimumWidth(432)#384)
        
        self.oddDocker.layout.insertWidget(1, self.dockerThumbnailsDisplayScaleSlider)
        self.dockerCommonControlsLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.dockerCommonControlsLayout.setSpacing(0)
        self.dockerCommonControlsLayout.addWidget(self.dockerDisplayToggleButton)
        self.dockerCommonControlsLayout.addWidget(self.dockerRefreshPeriodicallyToggleButton)
        self.oddDocker.buttonLayout.insertLayout(1, self.dockerCommonControlsLayout)
        
        self.UI["thumbAspectLimit"         ]["slider"].valueChanged.connect(self.changedThumbAspectLimitSlider)
        self.UI["thumbDisplayScale"        ]["slider"].valueChanged.connect(self.changedThumbDisplayScaleSlider)
        self.UI["thumbRenderScale"         ]["slider"].valueChanged.connect(self.changedThumbRenderScaleSlider)
        self.UI["thumbFadeAmount"          ]["slider"].valueChanged.connect(self.changedThumbFadeAmountSlider)
        self.UI["thumbShowModified"        ]["btn"   ].activated.connect(self.changedThumbShowModified)
        self.UI["thumbShowModified"        ]["btn"   ].highlighted.connect(self.highlightedThumbShowModified)
        self.UI["thumbShowModified"        ]["btn"   ].installEventFilter(self)
        self.UI["tooltipThumbLimit"        ]["slider"].valueChanged.connect(self.changedTooltipThumbLimitSlider)
        self.UI["tooltipThumbSize"         ]["slider"].valueChanged.connect(self.changedTooltipThumbSizeSlider)
        self.UI["refreshPeriodicallyChecks"]["slider"].valueChanged.connect(self.changedRefreshPeriodicallyChecksSlider)
        self.UI["refreshPeriodicallyDelay" ]["slider"].valueChanged.connect(self.changedRefreshPeriodicallyDelaySlider)
        self.UI["excessThumbCacheLimit"    ]["slider"].valueChanged.connect(self.changedExcessThumbCacheLimitSlider)
        
        self.dockerThumbnailsDisplayScaleSlider.valueChanged.connect(self.changedThumbDisplayScaleSlider)
        
        for setting in self.SD:
            self.updateControlsEnabledState(setting)
    
    def eventFilter(self, obj, event):
        if event.type() in [QEvent.FocusIn, QEvent.Hide]:
            self.unhighlightedThumbShowModified()
        return False
    
    def clickedViewButton(self):
        self.panel.move(self.panelPosition)
        self.panel.show()
    
    def updatePanelPosition(self):
        if not hasattr(self, "panel"):
            return
        
        direction = self._updatePanelPosition()
        if self.readSetting("dockerAlignButtonsToSettingsPanel") == "false":
            direction = 0
        #print("updatePanelPosition: direction =", direction)
        if self.oddDocker.list.flow() == QListView.TopToBottom:
            self.oddDocker.layout.setDirection(QBoxLayout.TopToBottom if not direction == 1 else QBoxLayout.BottomToTop)
            self.oddDocker.buttonLayout.setDirection(QBoxLayout.LeftToRight if not direction == 3 else QBoxLayout.RightToLeft)
        else:
            self.oddDocker.layout.setDirection(QBoxLayout.LeftToRight if not direction == 3 else QBoxLayout.RightToLeft)
            self.oddDocker.buttonLayout.setDirection(QBoxLayout.TopToBottom if not direction == 1 else QBoxLayout.BottomToTop)
    
    def _updatePanelPosition(self):
        baseGeo = QRect(self.oddDocker.mapToGlobal(self.oddDocker.baseWidget.frameGeometry().topLeft()), self.oddDocker.baseWidget.frameGeometry().size())
        baseTopLeft = baseGeo.topLeft()
        baseTopRight = baseGeo.topRight() + QPoint(1,0)
        baseBottomRight = baseGeo.bottomRight() + QPoint(1,1)
        
        listTopLeft = self.oddDocker.mapToGlobal(self.oddDocker.list.frameGeometry().topLeft())
        listRect = QRect(listTopLeft, self.oddDocker.list.size())
        
        screen = self.odd.getScreen(self.oddDocker).availableGeometry()
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
    
    @classmethod
    def debugDump(cls):
        print(" - ODDSettings - ")
        for setting in cls.SD.items():
            first = True
            for attr in setting[1].items():
                print("{:<36}{:<10}{}".format(setting[0] if first else "", attr[0], attr[1] if not attr[0]=="tooltips" else "<snip>"))
                first = False
        for setting in cls.globalSettings.items():
            print("{:<36}{}".format(setting[0], setting[1]))
    
    def roundToNSigFigures(v, n):
        """
        (tested with zero and positive integers only)
        """
        x = 10 ** (math.floor(math.log10(v)) - (n+1))
        return v if v == 0 else int(round(v/x) * x)
    
    def millisecondsToString(msec):
        """
        convert time in milliseconds to a more readable string.
        in   0   | 50   | 1000 | 30001     | 60000 | 90000   | 90500
        out  0ms | 50ms | 1sec | 30.001sec | 1min  | 1min30s | 1min30.5s
        """
        hasMins = hasSecs = hasMsec = False
        mins = secs = 0
        if msec >= 60000:
            mins  = msec // 60000
            msec -= mins *  60000
            hasMins = True
        if msec >= 1000:
            secs  = msec // 1000
            msec -= secs *  1000
            hasSecs = True
        if msec > 0 or not (hasMins or hasSecs):
            hasMsec = True
        if hasMins and hasMsec and not hasSecs:
            hasSecs = True
        padSecs = 2 if (hasMins) else 0
        padMsec = 3 if (hasMins or hasSecs) else 0
        
        if hasSecs or hasMins:
            return "{}{}{}{}{}".format(
                    str(mins) if hasMins else "",
                    "min"     if hasMins else "",
                    ("{:0>"+str(padSecs)+"}").format(str(secs)) \
                              if hasSecs else "",
                    (".{:0>"+str(padMsec)+"}").format(str(msec)).rstrip("0") \
                              if hasMsec else "",
                    "sec"     if hasSecs and not hasMins else "s" if hasSecs and hasMins else ""
            )
        else:
            return str(msec) + "ms"
    
    @classmethod
    def repairConfig(cls):
        cases = {
                "refreshPeriodicallyChecks":'/sec',
                "refreshPeriodicallyDelay": ('sec', 'min'),
                "tooltipThumbLimit":        ('≤', 'px²'),
                "tooltipThumbSize":         'px',
        }
        for c in cases.items():
            s = Application.readSetting("OpenDocumentsDocker", c[0], "")
            if s == "":
                continue
            if type(c[1]) is str and not c[1] in s:
                continue
            if type(c[1]) is tuple and not any(x in s for x in c[1]):
                continue
            Application.writeSetting("OpenDocumentsDocker", c[0], str(cls.SD[c[0]]["default"]))

# initial setup
ODDSettings.repairConfig()
ODDSettings.cacheSettingsDataDependencies()
ODDSettings.setupGlobalSettings()
