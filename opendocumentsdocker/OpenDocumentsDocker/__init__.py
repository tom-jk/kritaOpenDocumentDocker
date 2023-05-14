# SPDX-License-Identifier: GPL-3.0-or-later

import tempfile
import logging
import logging.handlers

class CustomFormatter(logging.Formatter):
    def format(self, record):
        try:
            record.levelname = ["DBG ","INFO","WARN","ERR ","CRIT"][["DEBUG","INFO","WARNING","ERROR","CRITICAL"].index(record.levelname)]
        except ValueError:
            record.levelname = record.levelname[0:4].ljust(4, " ")
        result = super().format(record)
        return result

oddLogger = logging.getLogger("odd")
oddLogger.setLevel(logging.DEBUG)
oddHandlerS = logging.StreamHandler()
oddHandlerS.setFormatter(CustomFormatter('ODD %(levelname)s %(message)s'))
oddHandlerS.setLevel(logging.INFO)
oddHandlerF = logging.handlers.RotatingFileHandler(tempfile.gettempdir() + '/kritaodd.log', 'w', 1024*128, 2)
oddHandlerF.setFormatter(CustomFormatter('%(asctime)s,%(msecs)04d %(levelname)s %(message)s', datefmt='%H:%M:%S'))
oddHandlerF.setLevel(logging.DEBUG)
oddLogger.addHandler(oddHandlerS)
oddLogger.addHandler(oddHandlerF)
oddLogger.addFilter(lambda record: not (str(record.msg) if type(record.msg is not str) else record.msg).startswith('Unimportant'))

oddLogger.info("Begin.")

import krita
from .odd import ODD
from .odddocker import ODDDocker


Application.addExtension(ODD(Application))

if ODD.instance:
    Application.addDockWidgetFactory(
        krita.DockWidgetFactory("openDocumentsDocker",
                                krita.DockWidgetFactoryBase.DockLeft,
                                ODDDocker))
