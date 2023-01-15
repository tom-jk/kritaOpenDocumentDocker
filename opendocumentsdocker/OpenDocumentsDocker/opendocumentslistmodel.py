# SPDX-License-Identifier: CC0-1.0

from PyQt5.QtCore import QAbstractListModel, Qt, QSize, QModelIndex
from PyQt5.QtGui import QImage
import krita
import zipfile
from pathlib import Path


class OpenDocumentsListModel(QAbstractListModel):

    def __init__(self, devicePixelRatioF, parent=None):
        super(OpenDocumentsListModel, self).__init__(parent)

        self.rootItem = ('Path',)
        self.kritaInstance = krita.Krita.instance()
        self.openDocuments = []
        self.devicePixelRatioF = devicePixelRatioF

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() >= len(self.openDocuments):
            return None

        if role == Qt.DecorationRole:
            return self.openDocuments[index.row()]
        else:
            return None
    
    def flags(self, index):
        #print("flags")
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
    
    def supportedDragActions(self):
        #print("supportedDragActions")
        return Qt.MoveAction
    
    def supportedDropActions(self):
        #print("supportedDropActions")
        return Qt.MoveAction
    
    def rowCount(self, parent=QModelIndex()):
        #print("rowCount = ", len(self.openDocuments))
        return len(self.openDocuments)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem[section]

        return None

    def loadOpenDocuments(self, width):
        print("loading!")
        self.openDocuments = []
        openDocumentsList = self.kritaInstance.documents()

        for i in range(len(openDocumentsList)):
            print(openDocumentsList[i].fileName() if (openDocumentsList[i].fileName()) else "[Not Saved]")
        
        for doc in openDocumentsList:
            path = doc.fileName()
            thumbnail = None
            if False: #path:
                extension = Path(path).suffix
                page = None
                if extension == '.kra':
                    page = zipfile.ZipFile(path, "r")
                    thumbnail = QImage.fromData(page.read("mergedimage.png"))
                    if thumbnail.isNull():
                        thumbnail = QImage.fromData(page.read("preview.png"))
                else:
                    thumbnail = QImage(path)
                
                if thumbnail.isNull():
                    continue
            else:
                thumbnail = doc.thumbnail(width, width)
                print("thumbnail = ", thumbnail)
                
                if thumbnail.isNull():
                    continue
                
            #thumbSize = QSize(200*self.devicePixelRatioF, 150*self.devicePixelRatioF)
            thumbSize = QSize(width*self.devicePixelRatioF, width*0.75*self.devicePixelRatioF)
            if thumbnail.width() <= thumbSize.width() or thumbnail.height() <= thumbSize.height():
            	thumbnail = thumbnail.scaled(thumbSize, Qt.KeepAspectRatio, Qt.FastTransformation)
            else:
            	thumbnail = thumbnail.scaled(thumbSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumbnail.setDevicePixelRatio(self.devicePixelRatioF)
            self.openDocuments.append(thumbnail)
        self.modelReset.emit()
