# SPDX-License-Identifier: CC0-1.0

from PyQt5.QtCore import Qt, QPoint, QItemSelection, QByteArray, QBuffer, QRect, QTimer
from PyQt5.QtGui import QCursor, QRegion, QColor, QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QPushButton, QToolTip, QMenu, QAbstractItemView, QListWidget, QListWidgetItem, QLabel
import krita
from . import opendocumentslistmodel
from pathlib import Path


class OpenDocumentsDocker(krita.DockWidget):
    
    # https://krita-artists.org/t/scripting-open-an-existing-file/32124/4
    def find_and_activate_view(self, doc):
        app = Krita.instance()
        for win in app.windows():
            for view in win.views():
                if view.document() == doc:
                    win.activate()
                    win.showView(view)
                    view.setVisible()
                    return

    #def activated(self, index):
    def clicked(self, index):
        print("activated!")
        print("index: col ", index.column(), ", row ", index.row(), ", data ", index.data())
        print(self.listModel.openDocuments[index.row()])
        ki = Krita.instance()
        self.find_and_activate_view(ki.documents()[index.row()])
        #ki.setActiveDocument(ki.documents()[index.row()])
    
    def entered(self, index):
        print("entered!")
        print("index: col ", index.column(), ", row ", index.row(), ", data ", index.data())
        print(self.listModel.openDocuments[index.row()])
        ki = Krita.instance()
        ttPos = self.mapToGlobal(self.listView.frameGeometry().topRight()) + self.listView.visualRect(index).topLeft()
        doc = ki.documents()[index.row()]
        fPath = doc.fileName()
        fName = Path(fPath).name
        tModi = " *" * doc.modified()
        tHead = ""
        ttText = ""
        
        ttText += "<table border='0' style='margin:16px; padding:16px'><tr>"
        
        # From answer to "Use a picture or image in a QToolTip": https://stackoverflow.com/a/34300771
        img = doc.thumbnail(128, 128)
        data = QByteArray()
        buffer = QBuffer(data)
        img.save(buffer, "PNG", 100)
        imgHtml = "<img src='data:image/png;base64, " + str(data.toBase64()).split("'")[1] + "'>"
        
        if fName:
            tHead = fName + tModi
        else:
            tHead = "[not saved]" + tModi
        
        ttText += "<td><table border='1'><tr><td>" + imgHtml + "</td></tr></table></td>"
        ttText += "<td style='padding-left: 8px'><h2 style='margin-bottom:0px'>" + tHead + "</h2>"
        ttText += "<p style='white-space:pre; margin-top:0px'><small>" + fPath + "</small></p>"
        ttText += "<p style='margin-top:0px'><small>" + str(doc.width()) + " x " + str(doc.height()) + "</small></p>"
        ttText += "</td>"
        ttText += "</tr></table>"
        
        #ttBounds = QRect(self.mapToGlobal(self.listView.frameGeometry().topLeft()), self.listView.size())
        print("ttBounds: ", QRect(QPoint(0,0), self.listView.size()))
        #QToolTip.showText(ttPos, ttText, self.listView, QRect(QPoint(0,0), self.listView.size()))
        
        #lb = QLabel(self)
        self.listToolTip.setWindowFlags(Qt.ToolTip)
        self.listToolTip.setText(ttText)
        self.listToolTip.move(ttPos)
        self.listToolTip.show()
        #QTimer.singleShot(500, lb.hide)
    
    def __init__(self):
        print("hello, I inited")
        super(OpenDocumentsDocker, self).__init__()
        
        self.baseWidget = QWidget()
        self.layout = QVBoxLayout()
        self.listView = QListWidget()
        self.listToolTip = QLabel()
        self.loadButton = QPushButton(i18n("Refresh"))
        self.listModel = opendocumentslistmodel.OpenDocumentsListModel(self.devicePixelRatioF())

        #self.listView.setModel(self.listModel)
        self.listView.setFlow(QListView.TopToBottom)
        self.listView.setMovement(QListView.Free)
        #self.listView.setToolTip("hi, I'm the tooltip.")
        #self.listView.activated.connect(self.activated)
        self.listView.clicked.connect(self.clicked)
        self.listView.setMouseTracking(True)
        self.listView.entered.connect(self.entered)
        self.listView.viewportEntered.connect(self.viewportEntered)
        if False:
            self.listView.setAcceptDrops(True)
            self.listView.setDragEnabled(True)
            self.listView.setDropIndicatorShown(True)
            print("qaiv.im: ", QAbstractItemView.InternalMove)
            self.listView.setDragDropMode(QAbstractItemView.InternalMove)
            self.listView.setDefaultDropAction(Qt.MoveAction)
            self.listView.setDragDropOverwriteMode(False)
        else:
            self.listView.setAcceptDrops(False)
            self.listView.setDragEnabled(False)

        self.layout.addWidget(self.listView)
        self.layout.addWidget(self.loadButton)

        self.baseWidget.setLayout(self.layout)
        self.baseWidget.setMinimumWidth(56)
        self.setWidget(self.baseWidget)

        self.loadButton.clicked.connect(self.refreshOpenDocuments)
        self.setWindowTitle(i18n("Open Documents Docker"))
        
        appNotifier = Krita.instance().notifier()
        appNotifier.setActive(True)
        #appNotifier.viewCreated.connect(self.refreshOpenDocuments)
        #appNotifier.viewClosed.connect(self.refreshOpenDocuments)
        appNotifier.imageCreated.connect(self.refreshOpenDocuments)
        appNotifier.imageClosed.connect(self.refreshOpenDocuments)

    def canvasChanged(self, canvas):
        pass
    
    def leaveEvent(self, event):
        print("leave event!")
        # empty string does not hide tooltip immediately for some reason,
        # but tooltip will respond immediately to non-empty string, so
        # make a small tooltip somewhere out of the way to make the
        # tooltip "disappear".
        #QToolTip.showText(QPoint(0,300), " ", self.listView, QRect(0,0,0,0))

        # using a label instead (looks like what layer docker does too).
        self.listToolTip.hide()
    
    def viewportEntered(self):
        print("viewport entered!")
        self.listToolTip.hide()
    
    def contextMenuEvent(self, event):
        print("ctx menu event - ", str(event))
        ki = Krita.instance()
        index = self.listView.selectedIndexes()[0]
        doc = ki.documents()[index.row()]
        print("selected: ", index, " - ", doc.fileName())
        self.find_and_activate_view(ki.documents()[index.row()])
        #ki.setActiveDocument(doc)
        menu = QMenu(self)
        menu.addAction(ki.action('file_save'))
        menu.addAction(ki.action('file_save_as'))
        menu.addAction(ki.action('file_export_file'))
        menu.addAction(ki.action('create_copy'))
        menu.addAction(ki.action('file_documentinfo'))
        menu.addAction(ki.action('file_close'))
        menu.exec(event.globalPos())
    
#    def quickCopyMergedAction(self):
#        ki = Krita.instance()
#        ki.action('select_all').trigger()
#        ki.action('copy_merged').trigger()
#        ki.action('edit_undo').trigger()
#        ki.action('edit_undo').trigger()
#
#    def createActions(self, window):
#        action = window.createAction("quickCopyMergedAction", "Quick Copy Merged")
#        action.triggered.connect(self.quickCopyMergedAction)
    
    def dropEvent(self, event):
        print("dropEvent: ", event)
    
    def refreshOpenDocuments(self):
        print("width: ")
        print(self.listView.width())
        kludgePixels=10
        self.listModel.loadOpenDocuments(self.baseWidget.width()-kludgePixels)
        self.listView.clear()
        for i in self.listModel.openDocuments:
            #QListWidgetItem(QIcon(i), self.listView)
            item = QListWidgetItem("", self.listView)
            item.setData(Qt.DecorationRole, QPixmap.fromImage(i))


##BBD's Krita Script Starter Feb 2018
#from krita import DockWidget, DockWidgetFactory, DockWidgetFactoryBase

#DOCKER_NAME = 'OpenDocumentsDocker'
#DOCKER_ID = 'pykrita_opendocumentsdocker'
#
#
#class Opendocumentsdocker(DockWidget):
#
#    def __init__(self):
#        super().__init__()
#        self.setWindowTitle(DOCKER_NAME)
#
#    def canvasChanged(self, canvas):
#        pass
#
#
#instance = Krita.instance()
#dock_widget_factory = DockWidgetFactory(DOCKER_ID,
#                                        DockWidgetFactoryBase.DockRight,
#                                        Opendocumentsdocker)
#
#instance.addDockWidgetFactory(dock_widget_factory)
