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
                    "label"  :"Grid",
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
                    "label"  :"Refresh on save",
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "refreshPeriodically": {
                    "label"  :"Refresh periodically (experimental)",
                    "default":"false",
                    "flags"  :["perInstance"],
            },
            "refreshPeriodicallyChecks": {
                    "label"  :"Checks",
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
                    "label"  :"Delay by",
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
                    "label"  :"Aspect limit",
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
                    "label"  :"Display scale",
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
                    "label"  :"Render scale",
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
                    "label"  :"Fade amount",
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
                    "label"  :"Modified indicator",
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
                    "label"  :"Tooltips",
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "tooltipThumbLimit": {
                    "label"  :"Limit",
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
                    "label"  :"Size",
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
                    "label"  :"Show commonly used settings in the docker",
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "dockerAlignButtonsToSettingsPanel": {
                    "label"  :"Move docker buttons to align with settings panel",
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "thumbUseProjectionMethod": {
                    "label"  :"Use projection method",
                    "default":"true",
                    "initial":lambda self: self.setUiValuesForThumbUseProjectionMethod(self.readSetting("thumbUseProjectionMethod")),
            },
            "excessThumbCacheLimit": {
                    "label"  :"Unused limit",
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
                "direction":                        {"btngrp":None, "btnHorizontal":None, "btnVertical":None, "btnAuto":None},
                "display":                          {"btngrp":None, "btnThumbnails":None, "btnText":None},
                "grid":                             {"btn":None},
                "gridMode":                         {"btn":None},
                "refreshOnSave":                    {"btn":None},
                "refreshPeriodically":              {"btn":None},
                "refreshPeriodicallyChecks":        {"value":None, "slider":None},
                "refreshPeriodicallyDelay":         {"value":None, "slider":None},
                "thumbAspectLimit":                 {"value":None, "slider":None},
                "thumbDisplayScale":                {"value":None, "slider":None},
                "thumbRenderScale":                 {"value":None, "slider":None},
                "thumbFadeAmount":                  {"value":None, "slider":None},
                "thumbFadeUnfade":                  {"btn":None},
                "thumbShowModified":                {"btn":None},
                "tooltipShow":                      {"btn":None},
                "tooltipThumbLimit":                {"value":None, "slider":None},
                "tooltipThumbSize":                 {"value":None, "slider":None},
                "showCommonControlsInDocker":       {"btn":None},
                "dockerAlignButtonsToSettingsPanel":{"btn":None},
                "thumbUseProjectionMethod":         {"btn":None},
                "excessThumbCacheLimit":            {"value":None, "slider":None},
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
        if self.sender() == self.dockerThumbsDisplayScaleSlider:
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
        
        self.dockerThumbsDisplayScaleSlider.setValue(value)
    
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
        self.previewThumbsShowModified = setting
        self.oddDocker.list.viewport().update()
    
    def unhighlightedThumbShowModified(self):
        self.previewThumbsShowModified = ""
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
            self.dockerThumbsDisplayScaleSlider.show()
            self.dockerDisplayToggleButton.show()
            self.dockerRefreshPeriodicallyToggleButton.show()
        else:
            self.dockerThumbsDisplayScaleSlider.hide()
            self.dockerDisplayToggleButton.hide()
            self.dockerRefreshPeriodicallyToggleButton.hide()
    
    def changedDockerAlignButtonsToSettingsPanel(self, state):
        setting = str(state==2).lower()
        print("changedDockerAlignButtonsToSettingsPanel to", setting)
        self.writeSetting("dockerAlignButtonsToSettingsPanel", setting)
        
        self.updatePanelPosition()
    
    def setUiValuesForThumbUseProjectionMethod(self, setting):
        self.UI["thumbUseProjectionMethod"]["btn"].setChecked(setting == "true")
    
    def changedThumbUseProjectionMethod(self, state):
        setting = str(state==2).lower()
        print("changedThumbUseProjectionMethod to", setting)
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
    
    def createPanelCheckBoxControlsForSetting(self, setting, labelText=None, state=None, stateChanged=None, tooltipText=""):
        self.UI[setting]["btn"] = QCheckBox(labelText if labelText != None else (self.SD[setting]["label"] if "label" in self.SD[setting] else ""), self.panel)
        if state == None:
            if "initial" in self.SD[setting]:
                self.SD[setting]["initial"](self)
            else:
                self.UI[setting]["btn"].setChecked(self.readSetting(setting) == "true")
        else:
            self.UI[setting]["btn"].setChecked(state)
        self.UI[setting]["btn"].stateChanged.connect(stateChanged)
        self.UI[setting]["btn"].setToolTip(tooltipText)
    
    def createPanelSliderControlsForSetting(self, setting, valueText, valRange=None, labelText=None, value=None, tooltipText=""):
        layout = QHBoxLayout()
        label = QLabel(labelText if labelText != None else (self.SD[setting]["label"] if "label" in self.SD[setting] else ""), self.panel)
        self.UI[setting]["value"] = QLabel(valueText, self.panel)
        control = QSlider(Qt.Horizontal, self.panel)
        if valRange == None:
            control.setRange(0, len(self.SD[setting]["values"])-1)
        else:
            control.setRange(valRange[0], valRange[1])
        control.setTickPosition(QSlider.NoTicks)
        control.setTickInterval(1)
        control.setToolTip(tooltipText)
        self.UI[setting]["slider"] = control
        if value == None:
            self.SD[setting]["initial"](self)
        else:
            control.setValue(value)
        return (layout, label)
    
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
        self.createPanelCheckBoxControlsForSetting(
                setting = "grid",
                stateChanged = self.changedGrid,
                tooltipText = 
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
        
        self.panelThumbsLabel = QLabel("Thumbnails", self.panel)
        
        self.createPanelCheckBoxControlsForSetting(
                setting = "thumbUseProjectionMethod",
                stateChanged = self.changedThumbUseProjectionMethod,
                tooltipText = 
                        "If enabled, ODD will generate thumbnails with the projection method.\n" +
                        "If disabled, ODD will use the thumbnail method.\n" +
                        "Projection should be faster. If there are no issues, leave this enabled."
        )
        
        setting = self.readSetting("thumbAspectLimit")
        self.panelThumbsAspectLimitLayout, self.panelThumbsAspectLimitLabel = self.createPanelSliderControlsForSetting(
                setting     = "thumbAspectLimit",
                valueText   = "1:{:1.3g}".format(float(setting)),
                valRange    = (0, 200),
                value       = int(math.log10(float(setting))*200.0),
                tooltipText = 
                        "The maximum deviation a document size can be from square before its thumbnail is shrunk.\n\n" +
                        "For example, 1:1 forces all thumbnails to be square, 1:2 allows thumbnails to be up to twice as long as their width.\n" +
                        "Higher values give better representation of wide/tall documents, at the cost of ease of list navigation."
        )
        
        setting = self.readSetting("thumbDisplayScale")
        self.panelThumbsDisplayScaleLayout, self.panelThumbsDisplayScaleLabel = self.createPanelSliderControlsForSetting(
                setting     = "thumbDisplayScale",
                valueText   = setting,
                valRange    = (0, 95),
                value       = round((float(setting)-0.05)*100.0)
        )
        
        self.dockerThumbsDisplayScaleSlider = QSlider(Qt.Horizontal)
        self.dockerThumbsDisplayScaleSlider.setRange(       self.UI["thumbDisplayScale"]["slider"].minimum(),
                                                            self.UI["thumbDisplayScale"]["slider"].maximum())
        self.dockerThumbsDisplayScaleSlider.setTickPosition(self.UI["thumbDisplayScale"]["slider"].tickPosition())
        self.dockerThumbsDisplayScaleSlider.setTickInterval(self.UI["thumbDisplayScale"]["slider"].tickInterval())
        self.dockerThumbsDisplayScaleSlider.setPageStep(    self.UI["thumbDisplayScale"]["slider"].pageStep())
        self.dockerThumbsDisplayScaleSlider.setValue(       self.UI["thumbDisplayScale"]["slider"].value())
        
        setting = self.readSetting("thumbRenderScale")
        self.panelThumbsRenderScaleLayout, self.panelThumbsRenderScaleLabel = self.createPanelSliderControlsForSetting(
                setting     = "thumbRenderScale",
                valueText   = setting,
                value       = convertSettingStringToValue("thumbRenderScale", setting),
                tooltipText = 
                        "Thumbnails in the list can be generated at a reduced size then scaled up.\n" +
                        "This can improve performance when using the thumbnail method."
        )
        
        setting = self.readSetting("thumbFadeAmount")
        self.panelThumbsFadeAmountLayout, self.panelThumbsFadeAmountLabel = self.createPanelSliderControlsForSetting(
                setting      = "thumbFadeAmount",
                valueText    = setting,
                valRange     = (0, 100),
                value        = round(float(setting)*100)
        )
        
        self.panelThumbsFadeAmountControlsLayout = QHBoxLayout()
        self.createPanelCheckBoxControlsForSetting(
                setting      = "thumbFadeUnfade",
                stateChanged = self.changedThumbFadeUnfade,
                tooltipText  = "Un-fade on mouse hover."
        )
        
        setting = self.readSetting("thumbShowModified")
        self.panelThumbsShowModifiedLayout = QHBoxLayout()
        self.panelThumbsShowModifiedLabel = QLabel(self.SD["thumbShowModified"]["label"], self.panel)
        self.UI["thumbShowModified"]["btn"] = QComboBox(self.panel)
        self.UI["thumbShowModified"]["btn"].addItems(self.SD["thumbShowModified"]["strings"])
        self.setUiValuesForThumbShowModified(setting)
        self.UI["thumbShowModified"]["btn"].setToolTip(
                "An icon to show on modified document thumbnails.\n" +
                "A preview will be shown as you highlight options (if there are visible thumbnails)."
        )
        self.previewThumbsShowModified = ""
        
        self.createPanelCheckBoxControlsForSetting(
                setting      = "refreshOnSave",
                stateChanged = self.changedRefreshOnSave,
                tooltipText  = "When you save an image, refresh its thumbnail automatically."
        )
        
        self.createPanelCheckBoxControlsForSetting(
                setting      = "refreshPeriodically",
                stateChanged = self.changedRefreshPeriodically,
                tooltipText  = 
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
        self.panelThumbsRefreshPeriodicallyChecksLayout, self.panelThumbsRefreshPeriodicallyChecksLabel = self.createPanelSliderControlsForSetting(
                setting     = "refreshPeriodicallyChecks",
                valueText   = self.decoratedSettingText("refreshPeriodicallyChecks", setting),
                value       = convertSettingStringToValue("refreshPeriodicallyChecks", setting),
                tooltipText = "Number of times each second the image is checked for activity."
        )
        
        setting = self.readSetting("refreshPeriodicallyDelay")
        settingValue = convertSettingStringToValue("refreshPeriodicallyDelay", setting)
        settingString = convertSettingValueToString("refreshPeriodicallyDelay", settingValue)
        self.panelThumbsRefreshPeriodicallyDelayLayout, self.panelThumbsRefreshPeriodicallyDelayLabel = self.createPanelSliderControlsForSetting(
                setting     = "refreshPeriodicallyDelay",
                valueText   = settingString,
                value       = settingValue,
                tooltipText = "How long after the last detected change to refresh the thumbnail."
        )
        
        self.panelTooltipsHeading = QHBoxLayout()
        self.createPanelCheckBoxControlsForSetting(
                setting      = "tooltipShow",
                stateChanged = self.changedTooltipShow,
        )
        self.panelTooltipsHeadingLine = QLabel("", self.panel)
        self.panelTooltipsHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        setting = self.readSetting("tooltipThumbLimit")
        self.panelTooltipThumbLimitLayout, self.panelTooltipThumbLimitLabel = self.createPanelSliderControlsForSetting(
                setting     = "tooltipThumbLimit",
                valueText   = self.decoratedSettingText("tooltipThumbLimit", setting),
                tooltipText = "Thumbnails in tooltips will be generated for images up to the chosen size."
        )
        
        setting = self.readSetting("tooltipThumbSize")
        self.panelTooltipThumbSizeLayout, self.panelTooltipThumbSizeLabel = self.createPanelSliderControlsForSetting(
                setting     = "tooltipThumbSize",
                valueText   = self.decoratedSettingText("tooltipThumbSize", setting),
        )
        
        self.panelMiscHeading = QHBoxLayout()
        self.panelMiscHeadingLabel = QLabel("Miscellaneous", self.panel)
        self.panelMiscHeadingLine = QLabel("", self.panel)
        self.panelMiscHeadingLine.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        
        self.createPanelCheckBoxControlsForSetting(
                setting      = "showCommonControlsInDocker",
                stateChanged = self.changedShowCommonControlsInDocker,
                tooltipText  =
                        "Make some of the most-used of these settings adjustable in the docker itself.\n\n" +
                        "Included are a slider for the list thumbnail display scale,\n" +
                        "and toggle buttons for changing display mode and enabling periodic thumbnail refresh."
        )
        
        self.createPanelCheckBoxControlsForSetting(
                setting      = "dockerAlignButtonsToSettingsPanel",
                stateChanged = self.changedDockerAlignButtonsToSettingsPanel,
                tooltipText  =
                        "Allow the docker buttons to move around the docker so that the settings button will be close to the settings panel.\n\n" +
                        "This panel will try to appear in a place that obscures the docker list as little as possible.\n" +
                        "This means it may appear on the other side of the docker, far from the default position of the settings button.\n" +
                        "This setting allows the docker buttons to move to the side of the docker where the settings button will be closest.\n" +
                        "The refresh and settings buttons may also switch position."
        )
        
        self.panelThumbCacheLabel = QLabel("Thumbnail Cache", self.panel)
        
        setting = self.readSetting("excessThumbCacheLimit")
        self.panelExcessThumbCacheLimitLayout, self.panelExcessThumbCacheLimitLabel = self.createPanelSliderControlsForSetting(
                setting     = "excessThumbCacheLimit",
                # ~ nameText    = "Unused limit",
                valueText   = setting + "mb",
                valRange    = (0, 1024),
                tooltipText = 
                        "Limit the amount of memory allowed to keep unused but potentially reusable thumbnails in cache.\n\n" +
                        "Unused thumbnails remain in memory so they can be reused. This is faster than generating new ones.\n" +
                        "For example, caching the tooltip thumbnail reduces lag when hovering the mouse over the list.\n" +
                        "When the size of these unused thumbnails exceeds this limit, the least recently used ones will be discarded."
        )
        
        self.UI["display"  ]["btngrp"       ].addButton(self.UI["display"  ]["btnThumbnails"])
        self.UI["display"  ]["btngrp"       ].addButton(self.UI["display"  ]["btnText"      ])
        self.setUiValuesForDisplay(self.readSetting("display"))
        self.UI["display"  ]["btnThumbnails"].clicked.connect(self.setDisplayToThumbnails)
        self.UI["display"  ]["btnText"      ].clicked.connect(self.setDisplayToText)
        self.UI["direction"]["btngrp"       ].addButton(self.UI["direction"]["btnHorizontal"])
        self.UI["direction"]["btngrp"       ].addButton(self.UI["direction"]["btnVertical"  ])
        self.UI["direction"]["btngrp"       ].addButton(self.UI["direction"]["btnAuto"      ])
        self.setUiValuesForDirection(self.readSetting("direction"))
        self.UI["direction"]["btnHorizontal"].clicked.connect(self.setDirectionToHorizontal)
        self.UI["direction"]["btnVertical"  ].clicked.connect(self.setDirectionToVertical)
        self.UI["direction"]["btnAuto"      ].clicked.connect(self.setDirectionToAuto)
                
        def addHeadingToPanel(layout, label, line):
            layout.addWidget(label)
            layout.addWidget(line)
            layout.setStretch(0, 1)
            layout.setStretch(1, 99)
            self.panelLayout.addLayout(layout)
        
        def addSliderSettingToPanel(settingLayout, nameLabel, setting, extraLayout=None, extraSetting=None):
            settingLayout.addWidget(nameLabel)
            settingLayout.addWidget(self.UI[setting]["value"])
            if extraLayout == None:
                settingLayout.addWidget(self.UI[setting]["slider"])
            else:
                extraLayout.addWidget(self.UI[setting]["slider"])
                extraLayout.addWidget(self.UI[extraSetting]["btn"])
                extraLayout.setStretch(0, 19)
                extraLayout.setStretch(1, 1)
                settingLayout.addLayout(extraLayout)
            for i in range(0, 3):
                settingLayout.setStretch(i, (4,4,10)[i])
            self.panelLayout.addLayout(settingLayout)
        
        addHeadingToPanel(self.panelListHeading, self.panelListHeadingLabel, self.panelListHeadingLine)
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
        self.panelLayout.addWidget(self.panelThumbsLabel)
        self.panelLayout.addWidget(self.UI["thumbUseProjectionMethod"]["btn"])
        addSliderSettingToPanel(self.panelThumbsAspectLimitLayout, self.panelThumbsAspectLimitLabel, "thumbAspectLimit")
        addSliderSettingToPanel(self.panelThumbsDisplayScaleLayout, self.panelThumbsDisplayScaleLabel, "thumbDisplayScale")
        addSliderSettingToPanel(self.panelThumbsRenderScaleLayout, self.panelThumbsRenderScaleLabel, "thumbRenderScale")
        addSliderSettingToPanel(
                self.panelThumbsFadeAmountLayout, self.panelThumbsFadeAmountLabel, "thumbFadeAmount",
                self.panelThumbsFadeAmountControlsLayout, "thumbFadeUnfade"
        )
        self.panelThumbsShowModifiedLayout.addWidget(self.panelThumbsShowModifiedLabel)
        self.panelThumbsShowModifiedLayout.addWidget(self.UI["thumbShowModified"]["btn"])
        self.panelThumbsShowModifiedLayout.setStretch(0, 4)
        self.panelThumbsShowModifiedLayout.setStretch(1, 5)
        self.panelLayout.addLayout(self.panelThumbsShowModifiedLayout)
        self.panelLayout.addWidget(self.UI["refreshOnSave"]["btn"])
        self.panelLayout.addWidget(self.UI["refreshPeriodically"]["btn"])
        addSliderSettingToPanel(self.panelThumbsRefreshPeriodicallyChecksLayout, self.panelThumbsRefreshPeriodicallyChecksLabel, "refreshPeriodicallyChecks")
        addSliderSettingToPanel(self.panelThumbsRefreshPeriodicallyDelayLayout, self.panelThumbsRefreshPeriodicallyDelayLabel, "refreshPeriodicallyDelay")
        addHeadingToPanel(self.panelTooltipsHeading, self.UI["tooltipShow"]["btn"], self.panelTooltipsHeadingLine)
        addSliderSettingToPanel(self.panelTooltipThumbLimitLayout, self.panelTooltipThumbLimitLabel, "tooltipThumbLimit")
        addSliderSettingToPanel(self.panelTooltipThumbSizeLayout, self.panelTooltipThumbSizeLabel, "tooltipThumbSize")
        addHeadingToPanel(self.panelMiscHeading, self.panelMiscHeadingLabel, self.panelMiscHeadingLine)
        self.panelLayout.addWidget(self.UI["showCommonControlsInDocker"]["btn"])
        self.panelLayout.addWidget(self.UI["dockerAlignButtonsToSettingsPanel"]["btn"])
        self.panelLayout.addWidget(self.panelThumbCacheLabel)
        addSliderSettingToPanel(self.panelExcessThumbCacheLimitLayout, self.panelExcessThumbCacheLimitLabel, "excessThumbCacheLimit")
        self.panel.setLayout(self.panelLayout)
        self.panel.setMinimumWidth(432)
        
        self.oddDocker.layout.insertWidget(1, self.dockerThumbsDisplayScaleSlider)
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
        
        self.dockerThumbsDisplayScaleSlider.valueChanged.connect(self.changedThumbDisplayScaleSlider)
        
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
