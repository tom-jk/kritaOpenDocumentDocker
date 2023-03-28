#
#  SPDX-License-Identifier: GPL-3.0-or-later
#

import krita
from .odd import ODD
from .odddocker import ODDDocker


Application.addExtension(ODD(Application))

Application.addDockWidgetFactory(
    krita.DockWidgetFactory("openDocumentsDocker",
                            krita.DockWidgetFactoryBase.DockLeft,
                            ODDDocker))
