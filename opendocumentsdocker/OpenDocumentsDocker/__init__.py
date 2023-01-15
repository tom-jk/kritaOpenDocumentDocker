#
#  SPDX-License-Identifier: GPL-3.0-or-later
#

import krita
from .opendocumentsdocker import OpenDocumentsDocker


Application.addDockWidgetFactory(
    krita.DockWidgetFactory("openDocumentsDocker",
                            krita.DockWidgetFactoryBase.DockLeft,
                            OpenDocumentsDocker))
