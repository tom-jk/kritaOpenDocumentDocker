#
#  SPDX-License-Identifier: GPL-3.0-or-later
#

import krita
from .odddocker import ODDDocker, ODDExtension


Application.addDockWidgetFactory(
    krita.DockWidgetFactory("openDocumentsDocker",
                            krita.DockWidgetFactoryBase.DockLeft,
                            ODDDocker))
