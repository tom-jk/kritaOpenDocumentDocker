# SPDX-License-Identifier: GPL-3.0-or-later

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QScreen
from PyQt5.QtWidgets import QWidget, QBoxLayout, QLabel, QCheckBox, QRadioButton, QButtonGroup, QSlider, QFrame, QToolButton, QStackedLayout, QTabBar
from krita import *
import math
from ast import literal_eval

import logging
logger = logging.getLogger("odd")


def convertSettingStringToValue(settingName, string):
    setting = ODDSettings.SD[settingName]
    strings = setting["strings"]
    if type(strings) == list and not ODDSettings.settingFlag(settingName, "onlyStringifyForDisplay"):
        if string in strings:
            return strings.index(string)
        else:
            return strings.index(setting["default"])
    else:
        numString = ''.join(i for i in string if i.isdigit() or i in '-./\\')
        value = literal_eval(numString)
        values = setting["values"]
        if value in values:
            return values.index(value)
        else:
            numString = ''.join(i for i in setting["default"] if i.isdigit() or i in '-./\\')
            default = literal_eval(numString)
            return values.index(default)

def convertSettingValueToString(settingName, value):
    """
    takes the raw value of a setting and returns a string representation
    which can be written to config on disk, or decorated and displayed.
    """
    setting = ODDSettings.SD[settingName]
    if not "strings" in setting:
        return str(value)
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
        if "values" in setting:
            # value is index into values list.
            return strings(setting["values"][value])

def mapValue(fromMin, fromMax, toMin, toMax, value):
    fromRange = fromMax - fromMin
    normValue = 1.0 / fromRange * (value - fromMin)
    toRange = toMax - toMin
    return toMin + toRange * normValue

def lerpi(a,b,t):
    return round(a+(b-a)*t)

# https://stackoverflow.com/a/35833467
import re
def formatFloatStandardToDecimal(f):
    s = str(f)
    m = re.fullmatch(r'(-?)(\d)(?:\.(\d+))?e([+-]\d+)', s)
    if not m:
        return s
    sign, intpart, fractpart, exponent = m.groups('')
    exponent = int(exponent) + 1
    digits = intpart + fractpart
    if exponent < 0:
        return sign + '0.' + '0'*(-exponent) + digits
    exponent -= len(digits)
    return sign + digits + '0'*exponent + '.0'

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
                    "default":"masonry",
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
                    "depends": {
                            "dependsOn":["display"],
                            "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "flags"  :["perInstance"],
            },
            "refreshPeriodically": {
                    "label"  :"Refresh periodically",
                    "default":"false",
                    "depends": {
                            "dependsOn":["display"],
                            "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "initial":lambda self: self.setUiValuesForCheckboxSetting("refreshPeriodically"),
            },
            "refreshPeriodicallyChecks": {
                    "label"  :"Checks",
                    "default":"15",
                    "strings":["1","2","3","4","5","6","8","10","12","15","20","25","30","36","40","45","50"],
                    "suffix" :"/sec",
                    "values" :[1000, 500, 333, 250, 200, 167, 125, 100, 83, 67, 50, 40, 33, 28, 25, 22, 20],
                    "depends": {
                            "dependsOn":["refreshPeriodically"],
                            "evaluator": lambda self: self.settingValue("refreshPeriodically"),
                    },
                    "initial":lambda self: self.setUiValuesForSliderSetting("refreshPeriodicallyChecks"),
            },
            "refreshPeriodicallyDelay": {
                    "label"  :"Delay by",
                    "default":2000,
                    "strings":lambda msec: ODDSettings.formatMillisecondsToString(msec),
                    "values" :[250, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 15000, 20000, 30000, 45000, 60000, 120000],
                    "depends": {
                            "dependsOn":["refreshPeriodically"],
                            "evaluator": lambda self: self.settingValue("refreshPeriodically"),
                    },
                    "initial":lambda self: self.setUiValuesForSliderSetting("refreshPeriodicallyDelay"),
                    "flags"  :["onlyStringifyForDisplay"],
            },
            "thumbAspectLimit": {
                    "label"  :"Aspect limit",
                    "default":"10",
                    "min": 1.0,
                    "max": 10.0,
                    "pow":10,
                    "depends": {
                        "dependsOn":["display", "grid", "gridMode"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails" and \
                                                 not (self.settingValue("grid") and self.settingValue("gridMode") != "masonry"),
                    },
                    "flags"  :["perInstance"],
            },
            "thumbDisplayScale": {
                    "label"  :"Display scale",
                    "default":"1.00",
                    "format" :"{:4.2f}",
                    "min":0.05,
                    "max":1.00,
                    "depends": {
                        "dependsOn":["display", "grid"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails" and not self.settingValue("grid"),
                    },
                    "flags"  :["perInstance", "writeAsUndecoratedLabel"],
            },
            "thumbDisplayScaleGrid": {
                    "label"  :"Display across",
                    "default":"2",
                    "strings":[str(i) for i in range(16, 0, -1)],
                    "values":[1/i for i in range(16, 0, -1)],
                    "depends": {
                        "dependsOn":["display", "grid"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails" and self.settingValue("grid"),
                    },
                    "flags"  :["perInstance", "writeAsUndecoratedLabel"],
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
                    "format" :"{:4.2f}",
                    "min":0.00,
                    "max":1.00,
                    "depends": {
                        "dependsOn":["display"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "flags"  :["perInstance", "writeAsUndecoratedLabel"],
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
                    "default":"corner",
                    "strings":["Don't show", "Corner", "Square", "Circle", "Asterisk", "Big Corner", "Big Square", "Big Circle", "Big Asterisk"],
                    "values" :["none", "corner", "square", "circle", "asterisk", "cornerBig", "squareBig", "circleBig", "asteriskBig"],
                    "depends": {
                        "dependsOn":["display"],
                        "evaluator":lambda self: self.settingValue("display", True) == "thumbnails",
                    },
                    "initial":lambda self: self.setUiValuesForThumbShowModified(self.readSetting("thumbShowModified")),
            },
            "tooltipShow": {
                    "label"  :"Show tooltips",
                    "default":"true",
                    "flags"  :["perInstance"],
            },
            "tooltipSizeMode": {
                    "default":"large",
                    "depends": {
                            "dependsOn":["tooltipShow"],
                            "evaluator": lambda self: self.settingValue("tooltipShow"),
                    },
                    "initial":lambda self: self.setUiValuesForTooltipSizeMode(self.readSetting("tooltipSizeMode")),
            },
            "tooltipThumbLimit": {
                    "label"  :"Limit",
                    "default":"8192",
                    "strings":["never","128","256","512","1024","2048","4096","8192","16384","always"],
                    "prefix" :"≤",
                    "suffix" :"px²",
                    "noDeco" :("never", "always"),
                    "values" :[0, 128*128, 256*256, 512*512, 1024*1024, 2048*2048, 4096*4096, 8192*8192, 16384*16384, float("inf")],
                    "depends": {
                            "dependsOn":["tooltipShow"],
                            "evaluator": lambda self: self.settingValue("tooltipShow"),
                    },
                    "initial":lambda self: self.setUiValuesForSliderSetting("tooltipThumbLimit"),
            },
            "tooltipThumbSize": {
                    "label"  :"Size",
                    "default":"128",
                    "strings":["24", "32", "64", "96", "128", "160", "192", "256", "384", "512"],
                    "suffix" :"px",
                    "values" :[24, 32, 64, 96, 128, 160, 192, 256, 384, 512],
                    "depends": {
                            "dependsOn":["tooltipShow", "tooltipThumbLimit"],
                            "evaluator": lambda self: self.settingValue("tooltipShow") and self.settingValue("tooltipThumbLimit") != 0,
                    },
                    "initial":lambda self: self.setUiValuesForSliderSetting("tooltipThumbSize"),
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
                    "initial":lambda self: self.setUiValuesForCheckboxSetting("thumbUseProjectionMethod"),
            },
            "progressiveThumbs": {
                    "label"  :"Enable progressive thumbnail generation",
                    "default":"true",
                    "depends": {
                            "dependsOn":["thumbUseProjectionMethod"],
                            "evaluator": lambda self: self.settingValue("thumbUseProjectionMethod"),
                    },
                    "initial":lambda self: self.setUiValuesForCheckboxSetting("progressiveThumbs"),
            },
            "progressiveThumbsWidth": {
                    "label"  :"Block width",
                    "default":"1024",
                    "strings":lambda v: str(v),
                    "suffix" :"px",
                    "values" :[64, 96, 128, 160, 192, 256, 384, 512, 640, 768, 1024, 1280, 1536, 1792, 2048, 2560, 3072, 3584, 4096, 5120, 6144, 7168, 8192],
                    "depends": {
                            "dependsOn":["thumbUseProjectionMethod", "progressiveThumbs"],
                            "evaluator": lambda self: self.settingValue("thumbUseProjectionMethod") and self.settingValue("progressiveThumbs"),
                    },
                    "initial":lambda self: self.setUiValuesForSliderSetting("progressiveThumbsWidth"),
            },
            "progressiveThumbsHeight": {
                    "label"  :"Block height",
                    "default":"1024",
                    "strings":lambda v: str(v),
                    "suffix" :"px",
                    "values" :[64, 96, 128, 160, 192, 256, 384, 512, 640, 768, 1024, 1280, 1536, 1792, 2048, 2560, 3072, 3584, 4096, 5120, 6144, 7168, 8192],
                    "depends": {
                            "dependsOn":["thumbUseProjectionMethod", "progressiveThumbs"],
                            "evaluator": lambda self: self.settingValue("thumbUseProjectionMethod") and self.settingValue("progressiveThumbs"),
                    },
                    "initial":lambda self: self.setUiValuesForSliderSetting("progressiveThumbsHeight"),
            },
            "progressiveThumbsSpeed": {
                    "label"  :"Speed",
                    "default":17,
                    "strings":["10","12","15","20","25","30","36","45","60","65","80","100","120"],
                    "suffix" :" blocks/sec",
                    "values" :[100, 83, 67, 50, 40, 33, 28, 22, 17, 15, 12, 10, 8],
                    "depends": {
                            "dependsOn":["thumbUseProjectionMethod", "progressiveThumbs"],
                            "evaluator": lambda self: self.settingValue("thumbUseProjectionMethod") and self.settingValue("progressiveThumbs"),
                    },
                    "initial":lambda self: self.setUiValuesForSliderSetting("progressiveThumbsSpeed"),
                    "flags"  :["onlyStringifyForDisplay"],
            },
            "excessThumbCacheLimit": {
                    "label"  :"Unused limit",
                    "default":"16384",
                    "strings":lambda kb: ODDSettings.formatBytesToString(kb*1024),
                    "values":[0] + [lerpi(2**(i//2), 2**(i//2+1), 0.5*(i%2)) for i in range(0, 45)][16:45],
                    "initial":lambda self: self.setUiValuesForSliderSetting("excessThumbCacheLimit"),
                    "flags"  :["onlyStringifyForDisplay"]
            },
    }
    
    def __init__(self, odd, oddDocker):
        super(ODDSettings, self).__init__()
        logger.debug("ODDSettings: init")
        #logger.debug(self.SD)
        self.odd = odd
        self.oddDocker = oddDocker
        self.panelSize = QSize()
        self.panelPosition = QPoint()
        
        ODDSettings.instances.append(self)
        logger.debug("instances:")
        for i in ODDSettings.instances:
            logger.debug(i)
        
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
                "thumbDisplayScaleGrid":            {"value":None, "slider":None},
                "thumbRenderScale":                 {"value":None, "slider":None},
                "thumbFadeAmount":                  {"value":None, "slider":None},
                "thumbFadeUnfade":                  {"btn":None},
                "thumbShowModified":                {"btn":None},
                "tooltipShow":                      {"btn":None},
                "tooltipSizeMode":                  {"btngrp":None, "btnSmall":None, "btnNormal":None, "btnLarge":None},
                "tooltipThumbLimit":                {"value":None, "slider":None},
                "tooltipThumbSize":                 {"value":None, "slider":None},
                "showCommonControlsInDocker":       {"btn":None},
                "dockerAlignButtonsToSettingsPanel":{"btn":None},
                "thumbUseProjectionMethod":         {"btn":None},
                "progressiveThumbs":                {"btn":None},
                "progressiveThumbsWidth":           {"value":None, "slider":None},
                "progressiveThumbsHeight":          {"value":None, "slider":None},
                "progressiveThumbsSpeed":           {"value":None, "slider":None},
                "excessThumbCacheLimit":            {"value":None, "slider":None},
        }
    
    @classmethod
    def cacheSettingsDataDependencies(cls):
        for setting in cls.SD.items():
            sName = setting[0]
            sData = setting[1]
            #logger.debug("%s %s", sName, sData)
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
                        #logger.debug("%s depends on %s", sName, i)
        #logger.debug(cls.SD)
    
    @classmethod
    def setupGlobalSettings(cls):
        cls.globalSettings = {}
        for setting in cls.SD:
            cls.globalSettings[setting] = cls.readSettingFromConfig(setting)
            #logger.debug("setting %s = %s", setting, cls.globalSettings[setting])
    
    def setupInstanceSettings(self):
        fromWindow = Application.activeWindow()
        logger.debug("setupInstanceSettings: fromWindow: %s (%s)", fromWindow, fromWindow.qwindow().objectName() if fromWindow else "")
        fromDocker = self.odd.findDockerWithWindow(fromWindow) if fromWindow else None
        settingsSource = fromDocker.vs.settings if fromDocker else self.globalSettings
        self.settings = {}
        for setting in self.SD:
            if self.settingFlag(setting, "perInstance"):
                self.settings[setting] = settingsSource[setting]
                #logger.debug("setting %s overriden in instance.", setting)
    
    @classmethod
    def settingFlag(cls, setting, flag):
        return flag in cls.SD[setting]["flags"] if "flags" in cls.SD[setting] else False
    
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
            logger.debug("writeSetting for local setting %s with value %s", setting, value)
            self.settings[setting] = value
            
        else:
            cls = type(self)
            logger.debug("writeSetting for global setting %s with value %s", setting, value)
            if not cls.isUpdatingControlsInInstances:
                cls.globalSettings[setting] = value
                #logger.debug("... done, start updating control in other dockers.")
                if not "initial" in cls.SD[setting]:
                    logger.warning("warning: setting %s does not have an 'initial' item.", setting)
                    return
                cls.isUpdatingControlsInInstances = True
                for inst in cls.instances:
                    if inst != self:
                        #logger.debug("updating controls for %s in other docker settings %s", setting, inst)
                        cls.SD[setting]["initial"](inst)
                cls.isUpdatingControlsInInstances = False
            #else:
                #logger.debug("... stop, we're just being updated by another docker.")
        
        if not setting in self.configFlushBuffer:
            self.configFlushBuffer.append(setting)
        self.startConfigFlushDelayTimer()
        self.updateControlsEnabledState(setting)
    
    def startConfigFlushDelayTimer(self):
        delay = self.configFlushDelay
        delay.start()
    
    def flushSettingsToConfig(self):
        logger.debug("flush")
        for i in self.configFlushBuffer:
            self.writeSettingToConfig(i, self.readSetting(i))
        self.configFlushBuffer.clear()
    
    def writeSettingToConfig(self, setting, value):
        logger.info("write %s = %s", setting, value)
        if not setting in self.SD:
            return
        Application.writeSetting("OpenDocumentsDocker", setting, str(value))
    
    def updateControlsEnabledState(self, setting):
        if "depends" in self.SD[setting] and "dependedOnBy" in self.SD[setting]["depends"]:
            for i in self.SD[setting]["depends"]["dependedOnBy"]:
                enable = self.SD[i]["depends"]["evaluator"](self)
                if "btngrp" in self.UI[i]:
                    for btn in self.UI[i]["btngrp"].buttons():
                        btn.setEnabled(enable)
                elif "btn" in self.UI[i]:
                    self.UI[i]["btn"].setEnabled(enable)
                    if i == "refreshPeriodically":
                        self.dockerRefreshPeriodicallyToggleButton.setEnabled(enable)
                elif "slider" in self.UI[i]:
                    self.UI[i]["slider"].setEnabled(enable)
                    if i == "thumbDisplayScale":
                        self.dockerThumbsDisplayScaleSlider.setEnabled(enable)
                    elif i == "thumbDisplayScaleGrid":
                        self.dockerThumbsDisplayScaleGridSlider.setEnabled(enable)
    
    def settingValue(self, setting, asName=False):
        ui = self.UI[setting]
        sd = self.SD[setting]
        if "slider" in ui:
            if "values" in sd:
                return sd["values"][ui["slider"].value()]
            elif "max" in sd:
                v = mapValue(ui["slider"].minimum(), ui["slider"].maximum(), sd["min"], sd["max"], ui["slider"].value())
                if "pow" in sd:
                    v = pow(setting["pow"], v) # TODO: currently unused.
                return v
        elif "btngrp" in ui:
            btn = ui["btngrp"].checkedButton()
            return btn.objectName() if asName else btn
        elif "btn" in ui:
            if "values" in sd:
                return sd["values"][ui["btn"].currentIndex()]
            else:
                return ui["btn"].isChecked()
        return None
    
    @classmethod
    def globalSettingValue(cls, setting, asName=False):
        # get from first available docker, global settings should be same in all anyway.
        return cls.instances[0].settingValue(setting, asName)
    
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
        self.UI["display"]["btnThumbnails" if checked else "btnText"].click()
    
    def setDisplayToThumbnails(self):
        self._setDisplay("thumbnails", True)
    
    def setDisplayToText(self):
        self._setDisplay("text", False)
    
    def _setDisplay(self, setTo, toggleState):
        self.writeSetting("display", setTo)
        self.oddDocker.setDockerDirection(self.readSetting("direction"))
        self.oddDocker.refreshOpenDocuments()
        self.oddDocker.updateScrollBarPolicy()
        
        self.dockerDisplayToggleButton.setChecked(toggleState)
    
    def setUiValuesForDirection(self, setting):
        self.UI["direction"]["btnHorizontal"].setChecked(setting=="horizontal")
        self.UI["direction"]["btnVertical"  ].setChecked(setting=="vertical")
        self.UI["direction"]["btnAuto"      ].setChecked(setting=="auto")
    
    def setDirectionTo(self, direction):
        self.writeSetting("direction", direction)
        self.oddDocker.setDockerDirection(direction)
    
    def updateListThumbnails(self):
        if self.readSetting("display") != "thumbnails":
            return
        self.oddDocker.list.invalidateItemRectsCache()
        self.oddDocker.list.updateGeometries()
        self.oddDocker.list.viewport().update()
        self.startRefreshAllDelayTimer()
    
    def changedGridMode(self, index):
        setting = self.settingValue("gridMode")
        logger.debug("changedGridMode to %s", setting)
        self.writeSetting("gridMode", setting)
        self.updateListThumbnails()
    
    def changedThumbAspectLimitSlider(self, value):
        setting = "{:1.6g}".format(pow(10, value/200.0))
        self.UI["thumbAspectLimit"]["value"].setText("1:{:1.3g}".format(float(setting)))
        self.writeSetting("thumbAspectLimit", setting)
        logger.debug("changedThumbAspectLimitSlider: value, setting: %s %s", value, setting)
        #logger.debug("find original value: %s -> %s -> %s", value/200.0, setting, "{:1.3g}".format(math.log10(float(setting))))
        
        self.updateListThumbnails()
    
    def changedThumbDisplayScaleSlider(self, value):
        self.UI["thumbDisplayScale"]["slider"].setValue(value)
        
    def postchangeThumbDisplayScaleSlider(self):
        self.updateListThumbnails()
        self.dockerThumbsDisplayScaleSlider.setValue(self.UI["thumbDisplayScale"]["slider"].value())
    
    def changedThumbDisplayScaleGridSlider(self, value):
        self.UI["thumbDisplayScaleGrid"]["slider"].setValue(value)
        
    def postchangeThumbDisplayScaleGridSlider(self):
        self.updateListThumbnails()
        self.dockerThumbsDisplayScaleGridSlider.setValue(self.UI["thumbDisplayScaleGrid"]["slider"].value())
    
    def changedThumbRenderScaleSlider(self, value):
        setting = convertSettingValueToString("thumbRenderScale", value)
        self.UI["thumbRenderScale"]["value"].setText(setting)
        self.writeSetting("thumbRenderScale", setting)
        
        self.startRefreshAllDelayTimer()
    
    def setUiValuesForThumbShowModified(self, setting):
        self.UI["thumbShowModified"]["btn"].setCurrentText(convertSettingValueToString("thumbShowModified", setting))

    def changedThumbShowModified(self, index):
        setting = self.settingValue("thumbShowModified")
        logger.debug("changedThumbShowModified to %s", setting)
        self.writeSetting("thumbShowModified", setting)
        self.oddDocker.list.viewport().update()
    
    def highlightedThumbShowModified(self, index):
        setting = self.SD["thumbShowModified"]["values"][index]
        self.previewThumbsShowModified = setting
        self.oddDocker.list.viewport().update()
    
    def unhighlightedThumbShowModified(self):
        self.previewThumbsShowModified = ""
        self.oddDocker.list.viewport().update()
    
    def setUiValuesForTooltipSizeMode(self, setting):
        self.UI["tooltipSizeMode"]["btnSmall" ].setChecked(setting=="small")
        self.UI["tooltipSizeMode"]["btnNormal"].setChecked(setting=="normal")
        self.UI["tooltipSizeMode"]["btnLarge" ].setChecked(setting=="large")
        
    def setTooltipSizeModeTo(self, sizeMode):
        self.writeSetting("tooltipSizeMode", sizeMode)
    
    def setUiValuesForCheckboxSetting(self, setting):
        self.UI[setting]["btn"].setChecked(self.readSetting(setting) == "true")
    
    def setUiValuesForSliderSetting(self, setting):
        self.UI[setting]["slider"].setValue(
            convertSettingStringToValue(setting, self.readSetting(setting))
        )
    
    def changedRefreshPeriodically(self, state):
        self.UI["refreshPeriodically"]["btn"].setChecked(state==1)
        
    def postchangeRefreshPeriodically(self):
        state = self.readSetting("refreshPeriodically") == "true"
        if state:
            ODDImageChangeDetector.removeStopper(ODDImageChangeDetector.StopReasonUser)
        else:
            ODDImageChangeDetector.addStopper(ODDImageChangeDetector.StopReasonUser)
        
        self.dockerRefreshPeriodicallyToggleButton.setChecked(state)
    
    def postchangeGrid(self):
        setting = self.readSetting("grid")
        self.panelThumbsDisplayScaleStack.setCurrentIndex(1 if setting == "true" else 0)
        self.dockerThumbsDisplayScaleStack.setCurrentIndex(1 if setting == "true" else 0)
        self.updateListThumbnails()
    
    def postchangeShowCommonControlsInDocker(self):
        state = self.readSetting("showCommonControlsInDocker") == "true"
        self.dockerThumbsDisplayScaleSlider.setVisible(state)
        self.dockerThumbsDisplayScaleGridSlider.setVisible(state)
        self.dockerDisplayToggleButton.setVisible(state)
        self.dockerRefreshPeriodicallyToggleButton.setVisible(state)
        self.oddDocker.buttonWidget.layout().update()
    
    def startRefreshAllDelayTimer(self):
        delay = self.oddDocker.refreshAllDelay
        delay.start()
    
    def postchangeRefreshPeriodicallyChecksSlider(self):
        ODDImageChangeDetector.checkTimer.setInterval(self.settingValue("refreshPeriodicallyChecks"))
    
    def postchangeRefreshPeriodicallyDelaySlider(self):
        ODDImageChangeDetector.refreshDelay = self.settingValue("refreshPeriodicallyDelay")
    
    def changedSettingCheckBox(self, setting, state=None, postCallable=None):
        if not state:
            state = self.UI[setting]["btn"].isChecked()
        #logger.debug("changedSettingCheckBox: %s %s %s %s", setting, state, self.sender(), postCallable)
        writeValue = str(state==2).lower()
        self.writeSetting(setting, writeValue)
        
        if postCallable is not None:
            postCallable()
    
    def sliderValueText(self, setting, value):
        if "strings" in self.SD[setting]:
            if type(self.SD[setting]["strings"]) is list:
                return convertSettingValueToString(setting, value)
            else:
                return self.SD[setting]["strings"](self.settingValue(setting))
        else:
            formatString = self.SD[setting]["format"] if "format" in self.SD[setting] else "{}"
            return formatString.format(self.settingValue(setting))
    
    def changedSettingSlider(self, setting, value, valueText=None, postCallable=None):
        #logger.debug("changedSettingSlider: %s %s %s %s %s", setting, value, valueText, self.sender(), postCallable)
        
        valueText = valueText or self.sliderValueText(setting, value)
        self.UI[setting]["value"].setText(self.decoratedSettingText(setting, valueText))
        
        if self.settingFlag(setting, "writeAsUndecoratedLabel"):
            writeValue = valueText
        else:
            writeValue = str(self.settingValue(setting)) if self.settingFlag(setting, "onlyStringifyForDisplay") else convertSettingValueToString(setting, value)
        self.writeSetting(setting, writeValue)
        
        if postCallable is not None:
            postCallable()
    
    def createPanelCheckBoxControlsForSetting(self, setting, labelText=None, state=None, stateChanged=None, tooltipText="", icon=None):
        if icon:
            self.UI[setting]["btn"] = QPushButton(self.panel)
            self.UI[setting]["btn"].setIcon(icon)
            self.UI[setting]["btn"].setCheckable(True)
        else:
            self.UI[setting]["btn"] = QCheckBox(labelText if labelText != None else (self.SD[setting]["label"] if "label" in self.SD[setting] else ""), self.panel)
        if state == None:
            if "initial" in self.SD[setting]:
                self.SD[setting]["initial"](self)
            else:
                self.UI[setting]["btn"].setChecked(self.readSetting(setting) == "true")
        else:
            self.UI[setting]["btn"].setChecked(state)
        if icon:
            self.UI[setting]["btn"].clicked.connect(stateChanged)
        else:
            self.UI[setting]["btn"].stateChanged.connect(stateChanged)
        self.UI[setting]["btn"].setToolTip(tooltipText)
    
    def createPanelSliderControlsForSetting(self, setting, valueText=None, valRange=None, labelText=None, value=None, tooltipText=""):
        #logger.debug("cPSCFS: {} vt:{} vr:{} lt:{}, v:{}".format(setting, valueText, valRange, labelText, value))
        layout = QHBoxLayout()
        label = QLabel(labelText if labelText != None else (self.SD[setting]["label"] if "label" in self.SD[setting] else ""), self.panel)
        control = QSlider(Qt.Horizontal, self.panel)
        if valRange == None:
            control.setRange(0, len(self.SD[setting]["values"])-1)
        else:
            control.setRange(valRange[0], valRange[1])
        rangeDiff = control.maximum() - control.minimum()
        control.setPageStep(max(1, round(rangeDiff/50)))
        control.setTickPosition(QSlider.NoTicks)
        control.setTickInterval(1)
        control.setToolTip(tooltipText)
        self.UI[setting]["slider"] = control
        if value == None:
            self.SD[setting]["initial"](self)
            value = self.UI[setting]["slider"].value()
        else:
            control.setValue(value)
        valueText = valueText or self.sliderValueText(setting, value)
        self.UI[setting]["value"] = QLabel(self.decoratedSettingText(setting, valueText), self.panel)
        return (layout, label)
    
    def createPanel(self):
        app = Application
        
        self.panel = QFrame(self.oddDocker, Qt.Popup)
        self.panel.setFrameShape(QFrame.StyledPanel)
        self.panelOuterLayout = QVBoxLayout()
        self.panelLayout = QStackedLayout()
        
        self.subpanelListLayout = QVBoxLayout()
        
        self.UI["display"]["btngrp"] = QButtonGroup(self.panel)
        self.UI["direction"]["btngrp"] = QButtonGroup(self.panel)
        
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
        
        self.dockerDisplayToggleButton = QPushButton()
        self.dockerDisplayToggleButton.setCheckable(True)
        self.dockerDisplayToggleButton.setIcon(Application.icon('folder-pictures'))
        self.dockerDisplayToggleButton.setChecked(self.readSetting("display") == "thumbnails")
        self.dockerDisplayToggleButton.clicked.connect(self.changedDisplay)
        
        self.panelGridLayout = QHBoxLayout()
        self.createPanelCheckBoxControlsForSetting(
                setting = "grid",
                stateChanged = lambda state: self.changedSettingCheckBox("grid", state, postCallable=self.postchangeGrid),
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
        
        self.panelThumbsDisplayScaleStack = QStackedLayout()
        self.dockerThumbsDisplayScaleStack = QStackedLayout()
        
        setting = self.readSetting("thumbDisplayScale")
        self.panelThumbsDisplayScaleLayout, self.panelThumbsDisplayScaleLabel = self.createPanelSliderControlsForSetting(
                setting     = "thumbDisplayScale",
                valRange    = (0, 95),
                value       = round((float(setting)-0.05)*100.0)
        )
        self.panelThumbsDisplayScaleLayout.setContentsMargins(0,0,0,0)
        self.panelThumbsDisplayScaleWidget = QWidget(self.panel)
        self.panelThumbsDisplayScaleWidget.setLayout(self.panelThumbsDisplayScaleLayout)
        self.panelThumbsDisplayScaleStack.addWidget(self.panelThumbsDisplayScaleWidget)
        
        self.dockerThumbsDisplayScaleSlider = QSlider(Qt.Horizontal)
        self.dockerThumbsDisplayScaleSlider.setRange(       self.UI["thumbDisplayScale"]["slider"].minimum(),
                                                            self.UI["thumbDisplayScale"]["slider"].maximum())
        self.dockerThumbsDisplayScaleSlider.setTickPosition(self.UI["thumbDisplayScale"]["slider"].tickPosition())
        self.dockerThumbsDisplayScaleSlider.setTickInterval(self.UI["thumbDisplayScale"]["slider"].tickInterval())
        self.dockerThumbsDisplayScaleSlider.setPageStep(    self.UI["thumbDisplayScale"]["slider"].pageStep())
        self.dockerThumbsDisplayScaleSlider.setValue(       self.UI["thumbDisplayScale"]["slider"].value())
        self.dockerThumbsDisplayScaleLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.dockerThumbsDisplayScaleLayout.setContentsMargins(0,0,0,0)
        self.dockerThumbsDisplayScaleWidget = QWidget(self.panel)
        self.dockerThumbsDisplayScaleWidget.setLayout(self.dockerThumbsDisplayScaleLayout)
        self.dockerThumbsDisplayScaleStack.addWidget(self.dockerThumbsDisplayScaleWidget)
        
        setting = self.readSetting("thumbDisplayScaleGrid")
        self.panelThumbsDisplayScaleGridLayout, self.panelThumbsDisplayScaleGridLabel = self.createPanelSliderControlsForSetting(
                setting     = "thumbDisplayScaleGrid",
                value       = convertSettingStringToValue("thumbDisplayScaleGrid", setting)
        )
        self.panelThumbsDisplayScaleGridLayout.setContentsMargins(0,0,0,0)
        self.panelThumbsDisplayScaleGridWidget = QWidget(self.panel)
        self.panelThumbsDisplayScaleGridWidget.setLayout(self.panelThumbsDisplayScaleGridLayout)
        self.panelThumbsDisplayScaleStack.addWidget(self.panelThumbsDisplayScaleGridWidget)
        
        self.dockerThumbsDisplayScaleGridSlider = QSlider(Qt.Horizontal)
        self.dockerThumbsDisplayScaleGridSlider.setRange(       self.UI["thumbDisplayScaleGrid"]["slider"].minimum(),
                                                                self.UI["thumbDisplayScaleGrid"]["slider"].maximum())
        self.dockerThumbsDisplayScaleGridSlider.setTickPosition(self.UI["thumbDisplayScaleGrid"]["slider"].tickPosition())
        self.dockerThumbsDisplayScaleGridSlider.setTickInterval(self.UI["thumbDisplayScaleGrid"]["slider"].tickInterval())
        self.dockerThumbsDisplayScaleGridSlider.setPageStep(    self.UI["thumbDisplayScaleGrid"]["slider"].pageStep())
        self.dockerThumbsDisplayScaleGridSlider.setValue(       self.UI["thumbDisplayScaleGrid"]["slider"].value())
        self.dockerThumbsDisplayScaleGridLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.dockerThumbsDisplayScaleGridLayout.setContentsMargins(0,0,0,0)
        self.dockerThumbsDisplayScaleGridWidget = QWidget(self.panel)
        self.dockerThumbsDisplayScaleGridWidget.setLayout(self.dockerThumbsDisplayScaleGridLayout)
        self.dockerThumbsDisplayScaleStack.addWidget(self.dockerThumbsDisplayScaleGridWidget)
        
        self.panelThumbsDisplayScaleStack.setCurrentIndex( 1 if self.readSetting("grid") == "true" else 0)
        self.dockerThumbsDisplayScaleStack.setCurrentIndex(1 if self.readSetting("grid") == "true" else 0)
        
        setting = self.readSetting("thumbRenderScale")
        self.panelThumbsRenderScaleLayout, self.panelThumbsRenderScaleLabel = self.createPanelSliderControlsForSetting(
                setting     = "thumbRenderScale",
                value       = convertSettingStringToValue("thumbRenderScale", setting),
                tooltipText = 
                        "Thumbnails in the list can be generated at a reduced size then scaled up.\n" +
                        "This can improve performance when using the thumbnail method."
        )
        
        setting = self.readSetting("thumbFadeAmount")
        self.panelThumbsFadeAmountLayout, self.panelThumbsFadeAmountLabel = self.createPanelSliderControlsForSetting(
                setting      = "thumbFadeAmount",
                valRange     = (0, 100),
                value        = round(float(setting)*100)
        )
        
        self.panelThumbsFadeAmountControlsLayout = QHBoxLayout()
        self.createPanelCheckBoxControlsForSetting(
                setting      = "thumbFadeUnfade",
                stateChanged = lambda : self.changedSettingCheckBox("thumbFadeUnfade"),
                tooltipText  = "Un-fade on mouse hover.",
                icon         = Application.icon('onionOn')
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
                stateChanged = lambda state: self.changedSettingCheckBox("refreshOnSave", state),
                tooltipText  = "When you save an image, refresh its thumbnail automatically."
        )
        
        self.createPanelCheckBoxControlsForSetting(
                setting      = "refreshPeriodically",
                stateChanged = lambda state: self.changedSettingCheckBox("refreshPeriodically", state, postCallable=self.postchangeRefreshPeriodically),
                tooltipText  = 
                        "Automatically refresh the thumbnail for the active image if a change is detected.\n\n" + 
                        "Checks for changes to the image so-many times each second.\n" +
                        "Then tries to refresh the thumbnail every so-many seconds.\n" +
                        "May not catch quick changes if they happen between checks.\n" +
                        "Aggressive settings may degrade performance."
        )
        
        self.dockerRefreshPeriodicallyToggleButton = QPushButton()
        self.dockerRefreshPeriodicallyToggleButton.setCheckable(True)
        self.dockerRefreshPeriodicallyToggleButton.setIcon(Application.icon('animation_play'))
        self.dockerRefreshPeriodicallyToggleButton.setChecked(self.UI["refreshPeriodically"]["btn"].isChecked())
        self.dockerRefreshPeriodicallyToggleButton.clicked.connect(self.changedRefreshPeriodically)
        
        setting = self.readSetting("refreshPeriodicallyChecks")
        self.panelThumbsRefreshPeriodicallyChecksLayout, self.panelThumbsRefreshPeriodicallyChecksLabel = self.createPanelSliderControlsForSetting(
                setting     = "refreshPeriodicallyChecks",
                value       = convertSettingStringToValue("refreshPeriodicallyChecks", setting),
                tooltipText = "Number of times each second the image is checked for activity."
        )
        
        setting = self.readSetting("refreshPeriodicallyDelay")
        settingValue = convertSettingStringToValue("refreshPeriodicallyDelay", setting)
        self.panelThumbsRefreshPeriodicallyDelayLayout, self.panelThumbsRefreshPeriodicallyDelayLabel = self.createPanelSliderControlsForSetting(
                setting     = "refreshPeriodicallyDelay",
                value       = convertSettingStringToValue("refreshPeriodicallyDelay", setting),
                tooltipText = "How long after the last detected change to refresh the thumbnail."
        )
        
        self.subpanelTooltipsLayout = QVBoxLayout()
        
        self.createPanelCheckBoxControlsForSetting(
                setting      = "tooltipShow",
                stateChanged = lambda state: self.changedSettingCheckBox("tooltipShow", state),
        )
        
        self.UI["tooltipSizeMode"]["btngrp"   ] = QButtonGroup(self.panel)
        
        self.panelTooltipSizeLayout = QHBoxLayout()
        self.panelTooltipSizeLabel = QLabel("Size mode", self.panel)
        self.panelTooltipSizeSubLayout = QHBoxLayout()
        self.UI["tooltipSizeMode"]["btnSmall" ] = QRadioButton("Small", self.panel)
        self.UI["tooltipSizeMode"]["btnSmall" ].setObjectName("small")
        self.UI["tooltipSizeMode"]["btnNormal"] = QRadioButton("Normal", self.panel)
        self.UI["tooltipSizeMode"]["btnNormal"].setObjectName("normal")
        self.UI["tooltipSizeMode"]["btnLarge" ] = QRadioButton("Large", self.panel)
        self.UI["tooltipSizeMode"]["btnLarge" ].setObjectName("large")
        self.panelTooltipSizeSubLayout.addWidget(self.UI["tooltipSizeMode"]["btnSmall" ])
        self.panelTooltipSizeSubLayout.addWidget(self.UI["tooltipSizeMode"]["btnNormal"])
        self.panelTooltipSizeSubLayout.addWidget(self.UI["tooltipSizeMode"]["btnLarge" ])
        
        self.panelTooltipThumbLabel = QLabel("Thumbnail", self.panel)
        
        self.panelTooltipThumbLimitLayout, self.panelTooltipThumbLimitLabel = self.createPanelSliderControlsForSetting(
                setting     = "tooltipThumbLimit",
                tooltipText = "Thumbnails in tooltips will be generated for images up to the chosen size."
        )
        
        self.panelTooltipThumbSizeLayout, self.panelTooltipThumbSizeLabel = self.createPanelSliderControlsForSetting(
                setting     = "tooltipThumbSize",
        )
        
        self.subpanelMiscLayout = QVBoxLayout()
        
        self.createPanelCheckBoxControlsForSetting(
                setting      = "showCommonControlsInDocker",
                stateChanged = lambda state: self.changedSettingCheckBox("showCommonControlsInDocker", state, postCallable=self.postchangeShowCommonControlsInDocker),
                tooltipText  =
                        "Make some of the most-used of these settings adjustable in the docker itself.\n\n" +
                        "Included are a slider for the list thumbnail display scale,\n" +
                        "and toggle buttons for changing display mode and enabling periodic thumbnail refresh."
        )
        
        self.createPanelCheckBoxControlsForSetting(
                setting      = "dockerAlignButtonsToSettingsPanel",
                stateChanged = lambda state: self.changedSettingCheckBox("dockerAlignButtonsToSettingsPanel", state, postCallable=self.updatePanelPosition),
                tooltipText  =
                        "Allow the docker buttons to move around the docker so that the settings button will be close to the settings panel.\n\n" +
                        "This panel will try to appear in a place that obscures the docker list as little as possible.\n" +
                        "This means it may appear on the other side of the docker, far from the default position of the settings button.\n" +
                        "This setting allows the docker buttons to move to the side of the docker where the settings button will be closest.\n" +
                        "The refresh and settings buttons may also switch position."
        )
        
        self.panelMiscThumbsLabel = QLabel("Thumbnails", self.panel)
        
        self.createPanelCheckBoxControlsForSetting(
                setting = "thumbUseProjectionMethod",
                stateChanged = lambda state: self.changedSettingCheckBox("thumbUseProjectionMethod", state, postCallable=self.startRefreshAllDelayTimer),
                tooltipText = 
                        "If enabled, ODD will generate thumbnails with the projection method.\n" +
                        "If disabled, ODD will use the thumbnail method.\n" +
                        "Projection should be faster. If there are no issues, leave this enabled."
        )
        
        self.createPanelCheckBoxControlsForSetting(
                setting = "progressiveThumbs",
                stateChanged = lambda state: self.changedSettingCheckBox("progressiveThumbs", state),
                tooltipText = 
                        "If enabled, construct thumbnails in increments over a short time.\n" +
                        "If disabled, always generate whole thumbnails immediately.\n\n" +
                        "Generating thumbnails for large documents can take a while, and krita will pause during this time.\n" +
                        "If this frequently happens when you try to paint, it can become an annoyance.\n\n" +
                        "Progressive thumbnail generation takes a small piece of the document (a 'block') at a time to fill\n" +
                        "in the thumbnail bit-by-bit. It will take longer for a complete thumbnail to be ready to be displayed,\n" +
                        "but you should experience no interruptions while painting. ODD will also discard an in-progress\n" +
                        "thumbnail and start over if the image changes in the meantime (provided periodic refresh is enabled)."
        )
        
        self.panelProgressiveThumbsWidthLayout, self.panelProgressiveThumbsWidthLabel = self.createPanelSliderControlsForSetting(
                setting     = "progressiveThumbsWidth",
                tooltipText =
                        "The width of the document subregions ('blocks') used to construct its thumbnail.\n\n" +
                        "You should make the blocks as large as possible, but not so large as to cause a noticeable delay.\n" +
                        "It's recommended to adjust the block size while testing on a large square document. You should only have to do this once.\n" +
                        "Note that ODD will automatically adjust the block size for comparatively narrow documents."
        )
        
        self.panelProgressiveThumbsHeightLayout, self.panelProgressiveThumbsHeightLabel = self.createPanelSliderControlsForSetting(
                setting     = "progressiveThumbsHeight",
                tooltipText =
                        "The height of the document subregions ('blocks') used to construct its thumbnail.\n\n" +
                        "You should make the blocks as large as possible, but not so large as to cause a noticeable delay.\n" +
                        "It's recommended to adjust the block size while testing on a large square document. You should only have to do this once.\n" +
                        "Note that ODD will automatically adjust the block size for comparatively narrow documents."
        )
        
        self.panelProgressiveThumbsSpeedLayout, self.panelProgressiveThumbsSpeedLabel = self.createPanelSliderControlsForSetting(
                setting     = "progressiveThumbsSpeed",
                tooltipText =
                        "How frequently to get new blocks for thumbnail.\n\n" +
                        "This setting is an approximate upper limit; the actual speed will be affected by the block size.\n" +
                        "It's recommended to choose larger block sizes and moderate frequencies; there is a small overhead cost\n" +
                        "for each block processed, so using many tiny blocks means your computer will do more work in total."
        )
        
        self.panelThumbCacheLabel = QLabel("Thumbnail cache", self.panel)
        
        self.panelExcessThumbCacheLimitLayout, self.panelExcessThumbCacheLimitLabel = self.createPanelSliderControlsForSetting(
                setting     = "excessThumbCacheLimit",
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
        self.UI["direction"]["btnHorizontal"].clicked.connect(lambda : self.setDirectionTo("horizontal"))
        self.UI["direction"]["btnVertical"  ].clicked.connect(lambda : self.setDirectionTo("vertical"))
        self.UI["direction"]["btnAuto"      ].clicked.connect(lambda : self.setDirectionTo("auto"))
        
        self.UI["tooltipSizeMode"]["btngrp"   ].addButton(self.UI["tooltipSizeMode"]["btnSmall"])
        self.UI["tooltipSizeMode"]["btngrp"   ].addButton(self.UI["tooltipSizeMode"]["btnNormal"])
        self.UI["tooltipSizeMode"]["btngrp"   ].addButton(self.UI["tooltipSizeMode"]["btnLarge"])
        self.setUiValuesForTooltipSizeMode(self.readSetting("tooltipSizeMode"))
        self.UI["tooltipSizeMode"]["btnSmall" ].clicked.connect(lambda : self.setTooltipSizeModeTo("small"))
        self.UI["tooltipSizeMode"]["btnNormal"].clicked.connect(lambda : self.setTooltipSizeModeTo("normal"))
        self.UI["tooltipSizeMode"]["btnLarge" ].clicked.connect(lambda : self.setTooltipSizeModeTo("large"))
        
        def addSliderSettingToPanel(settingLayout, nameLabel, setting, extraLayout=None, extraSetting=None, **kwargs):
            nonlocal currentTargetLayout
            targetLayout = kwargs["targetLayout"] if "targetLayout" in kwargs else currentTargetLayout
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
            if targetLayout:
                targetLayout.addLayout(settingLayout)
        
        currentTargetLayout = self.subpanelListLayout
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
        self.subpanelListLayout.addLayout(self.panelDisplayAndDirectionLayout)
        self.subpanelListLayout.addWidget(self.panelThumbsLabel)
        addSliderSettingToPanel(self.panelThumbsAspectLimitLayout, self.panelThumbsAspectLimitLabel, "thumbAspectLimit")
        addSliderSettingToPanel(self.panelThumbsDisplayScaleLayout, self.panelThumbsDisplayScaleLabel, "thumbDisplayScale", targetLayout=None)
        addSliderSettingToPanel(self.panelThumbsDisplayScaleGridLayout, self.panelThumbsDisplayScaleGridLabel, "thumbDisplayScaleGrid", targetLayout=None)
        self.subpanelListLayout.addLayout(self.panelThumbsDisplayScaleStack)
        addSliderSettingToPanel(self.panelThumbsRenderScaleLayout, self.panelThumbsRenderScaleLabel, "thumbRenderScale")
        addSliderSettingToPanel(
                self.panelThumbsFadeAmountLayout, self.panelThumbsFadeAmountLabel, "thumbFadeAmount",
                self.panelThumbsFadeAmountControlsLayout, "thumbFadeUnfade"
        )
        self.panelThumbsShowModifiedLayout.addWidget(self.panelThumbsShowModifiedLabel)
        self.panelThumbsShowModifiedLayout.addWidget(self.UI["thumbShowModified"]["btn"])
        self.panelThumbsShowModifiedLayout.setStretch(0, 4)
        self.panelThumbsShowModifiedLayout.setStretch(1, 5)
        self.subpanelListLayout.addLayout(self.panelThumbsShowModifiedLayout)
        self.subpanelListLayout.addWidget(self.UI["refreshOnSave"]["btn"])
        self.subpanelListLayout.addWidget(self.UI["refreshPeriodically"]["btn"])
        addSliderSettingToPanel(self.panelThumbsRefreshPeriodicallyChecksLayout, self.panelThumbsRefreshPeriodicallyChecksLabel, "refreshPeriodicallyChecks")
        addSliderSettingToPanel(self.panelThumbsRefreshPeriodicallyDelayLayout, self.panelThumbsRefreshPeriodicallyDelayLabel, "refreshPeriodicallyDelay")
        
        currentTargetLayout = self.subpanelTooltipsLayout
        self.subpanelTooltipsLayout.addWidget(self.UI["tooltipShow"]["btn"])
        
        self.panelTooltipSizeLayout.addWidget(self.panelTooltipSizeLabel)
        self.panelTooltipSizeLayout.addLayout(self.panelTooltipSizeSubLayout)
        self.panelTooltipSizeLayout.setStretch(0, 4)
        self.panelTooltipSizeLayout.setStretch(1, 5)
        self.subpanelTooltipsLayout.addLayout(self.panelTooltipSizeLayout)
        self.subpanelTooltipsLayout.addWidget(self.panelTooltipThumbLabel)
        
        addSliderSettingToPanel(self.panelTooltipThumbLimitLayout, self.panelTooltipThumbLimitLabel, "tooltipThumbLimit")
        addSliderSettingToPanel(self.panelTooltipThumbSizeLayout, self.panelTooltipThumbSizeLabel, "tooltipThumbSize")
        
        currentTargetLayout = self.subpanelMiscLayout
        self.subpanelMiscLayout.addWidget(self.UI["showCommonControlsInDocker"]["btn"])
        self.subpanelMiscLayout.addWidget(self.UI["dockerAlignButtonsToSettingsPanel"]["btn"])
        self.subpanelMiscLayout.addWidget(self.panelMiscThumbsLabel)
        self.subpanelMiscLayout.addWidget(self.UI["thumbUseProjectionMethod"]["btn"])
        self.subpanelMiscLayout.addWidget(self.UI["progressiveThumbs"]["btn"])
        addSliderSettingToPanel(self.panelProgressiveThumbsWidthLayout, self.panelProgressiveThumbsWidthLabel, "progressiveThumbsWidth")
        addSliderSettingToPanel(self.panelProgressiveThumbsHeightLayout, self.panelProgressiveThumbsHeightLabel, "progressiveThumbsHeight")
        addSliderSettingToPanel(self.panelProgressiveThumbsSpeedLayout, self.panelProgressiveThumbsSpeedLabel, "progressiveThumbsSpeed")
        self.subpanelMiscLayout.addWidget(self.panelThumbCacheLabel)
        addSliderSettingToPanel(self.panelExcessThumbCacheLimitLayout, self.panelExcessThumbCacheLimitLabel, "excessThumbCacheLimit")
        
        self.panelLayout.addWidget(QWidget(self.panel))
        self.subpanelListLayout.setAlignment(Qt.AlignTop)
        self.panelLayout.widget(0).setLayout(self.subpanelListLayout)
        self.panelLayout.addWidget(QWidget(self.panel))
        self.subpanelTooltipsLayout.setAlignment(Qt.AlignTop)
        self.panelLayout.widget(1).setLayout(self.subpanelTooltipsLayout)
        self.panelLayout.addWidget(QWidget(self.panel))
        self.subpanelMiscLayout.setAlignment(Qt.AlignTop)
        self.panelLayout.widget(2).setLayout(self.subpanelMiscLayout)
        self.panelOuterLayout.addLayout(self.panelLayout)
        
        tb = QTabBar(self.panel)
        b1 = tb.addTab("List")
        b2 = tb.addTab("Tooltips")
        b3 = tb.addTab("Miscellaneous")
        self.subpanelSelectorLayout = QHBoxLayout()
        self.subpanelSelectorLayout.addWidget(tb)
        tb.currentChanged.connect(lambda index: self.panelLayout.setCurrentIndex(index))
        self.panelOuterLayout.insertLayout(0, self.subpanelSelectorLayout)
        
        self.panel.setLayout(self.panelOuterLayout)
        self.panel.setMinimumWidth(452)
        
        self.dockerThumbsDisplayScaleLayout.addWidget(self.dockerThumbsDisplayScaleSlider)
        self.dockerThumbsDisplayScaleGridLayout.addWidget(self.dockerThumbsDisplayScaleGridSlider)
        
        self.oddDocker.layout.insertLayout(1, self.dockerThumbsDisplayScaleStack)
        self.oddDocker.layout.setStretch(1, 0)
        self.oddDocker.buttonLayout.insertWidget(0, self.dockerDisplayToggleButton)
        self.oddDocker.buttonLayout.insertWidget(1, self.dockerRefreshPeriodicallyToggleButton)
        
        self.UI["thumbAspectLimit"         ]["slider"].valueChanged.connect(self.changedThumbAspectLimitSlider)
        self.UI["thumbDisplayScale"        ]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("thumbDisplayScale", value, postCallable=self.postchangeThumbDisplayScaleSlider)
        )
        self.UI["thumbDisplayScaleGrid"    ]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("thumbDisplayScaleGrid", value, postCallable=self.postchangeThumbDisplayScaleGridSlider)
        )
        self.UI["thumbRenderScale"         ]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("thumbRenderScale", value, postCallable=self.startRefreshAllDelayTimer)
        )
        self.UI["thumbFadeAmount"          ]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("thumbFadeAmount", value, postCallable=self.oddDocker.list.viewport().update)
        )
        self.UI["thumbShowModified"        ]["btn"   ].activated.connect(self.changedThumbShowModified)
        self.UI["thumbShowModified"        ]["btn"   ].highlighted.connect(self.highlightedThumbShowModified)
        self.UI["thumbShowModified"        ]["btn"   ].installEventFilter(self)
        self.UI["tooltipThumbLimit"        ]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("tooltipThumbLimit", value)
        )
        self.UI["tooltipThumbSize"         ]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("tooltipThumbSize", value)
        )
        self.UI["refreshPeriodicallyChecks"]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("refreshPeriodicallyChecks", value, postCallable=self.postchangeRefreshPeriodicallyChecksSlider)
        )
        self.UI["refreshPeriodicallyDelay" ]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("refreshPeriodicallyDelay", value, postCallable=self.postchangeRefreshPeriodicallyDelaySlider)
        )
        self.UI["progressiveThumbsWidth"]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("progressiveThumbsWidth", value, postCallable=None)
        )
        self.UI["progressiveThumbsHeight"]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("progressiveThumbsHeight", value, postCallable=None)
        )
        self.UI["progressiveThumbsSpeed"]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("progressiveThumbsSpeed", value, postCallable=None)
        )
        self.UI["excessThumbCacheLimit"    ]["slider"].valueChanged.connect(
                lambda value: self.changedSettingSlider("excessThumbCacheLimit", value, postCallable=self.odd.evictExcessUnusedCache)
        )
        
        self.dockerThumbsDisplayScaleSlider.valueChanged.connect(self.changedThumbDisplayScaleSlider)
        self.dockerThumbsDisplayScaleGridSlider.valueChanged.connect(self.changedThumbDisplayScaleGridSlider)
        self.postchangeShowCommonControlsInDocker()
        
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
        logger.info(" - ODDSettings - ")
        for setting in cls.SD.items():
            first = True
            for attr in setting[1].items():
                logger.info("{:<36}{:<10}{}".format(setting[0] if first else "", attr[0], attr[1] if not attr[0]=="tooltips" else "<snip>"))
                first = False
        for setting in cls.globalSettings.items():
            logger.info("{:<36}{}".format(setting[0], setting[1]))
    
    def roundToNSigFigures(v, n):
        """(tested with zero and positive integers only)"""
        x = 10 ** (math.floor(math.log10(v)) - (n+1))
        return v if v == 0 else int(round(v/x) * x)
    
    def formatMillisecondsToString(msec):
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
    
    def formatBytesToString(By):
        """
        convert size in bytes to a more readable string.
        in   0      | 512       | 1024  | 1025     | 524288  | 1048575     | 1048576  | 1073741824  | 1073741825
        out  0 bytes| 512 bytes | 1 kb  | 1.001 kb | 512 kb  | 1023.999 kb | 1 mb     | 1 gb        | 1.000000001 gb
        """
        if type(By) is float:
            By  = round(By)
            
        bytesPerGb = 1073741824
        if By >= bytesPerGb:
            Gb  = By // bytesPerGb
            By -= Gb *  bytesPerGb
            if By > 0:
                return "{}.{} gb".format(Gb, formatFloatStandardToDecimal(By/bytesPerGb)[2:12].rstrip("0"))
            else:
                return "{} gb".format(Gb)
        bytesPerMb = 1048576
        if By >= bytesPerMb:
            Mb  = By // bytesPerMb
            By -= Mb *  bytesPerMb
            if By > 0:
                return "{}.{} mb".format(Mb, formatFloatStandardToDecimal(By/bytesPerMb)[2:8].rstrip("0"))
            else:
                return "{} mb".format(Mb)
        bytesPerKb = 1024
        if By >= bytesPerKb:
            Kb  = By // bytesPerKb
            By -= Kb *  bytesPerKb
            if By > 0:
                return "{}.{} kb".format(Kb, formatFloatStandardToDecimal(By/bytesPerKb)[2:6].rstrip("0"))
            else:
                return "{} kb".format(Kb)
        return "{} bytes".format(By)
    
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

from .oddimagechangedetector import ODDImageChangeDetector
