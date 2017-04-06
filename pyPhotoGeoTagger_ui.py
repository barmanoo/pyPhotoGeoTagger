# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pyPhotoGeoTagger.ui'
#
# Created: Sun Mar 20 15:35:43 2016
#      by: PyQt4 UI code generator 4.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(775, 601)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.splitter = QtGui.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.listWidget = QtGui.QListWidget(self.splitter)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.webView = QtWebKit.QWebView(self.splitter)
        self.webView.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.webView.setObjectName(_fromUtf8("webView"))
        self.horizontalLayout.addWidget(self.splitter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 775, 19))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuPhoto_geotag = QtGui.QMenu(self.menubar)
        self.menuPhoto_geotag.setObjectName(_fromUtf8("menuPhoto_geotag"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionSave_positions_to_photo = QtGui.QAction(MainWindow)
        self.actionSave_positions_to_photo.setObjectName(_fromUtf8("actionSave_positions_to_photo"))
        self.actionLoad_photo_from_directory = QtGui.QAction(MainWindow)
        self.actionLoad_photo_from_directory.setObjectName(_fromUtf8("actionLoad_photo_from_directory"))
        self.actionAbout = QtGui.QAction(MainWindow)
        self.actionAbout.setObjectName(_fromUtf8("actionAbout"))
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionClear = QtGui.QAction(MainWindow)
        self.actionClear.setObjectName(_fromUtf8("actionClear"))
        self.menuPhoto_geotag.addAction(self.actionLoad_photo_from_directory)
        self.menuPhoto_geotag.addAction(self.actionSave_positions_to_photo)
        self.menuPhoto_geotag.addAction(self.actionClear)
        self.menuPhoto_geotag.addAction(self.actionQuit)
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuPhoto_geotag.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.menuPhoto_geotag.setTitle(_translate("MainWindow", "Photo", None))
        self.menuHelp.setTitle(_translate("MainWindow", "Help", None))
        self.actionSave_positions_to_photo.setText(_translate("MainWindow", "Save positions to photo", None))
        self.actionLoad_photo_from_directory.setText(_translate("MainWindow", "Load photo from directory", None))
        self.actionAbout.setText(_translate("MainWindow", "About...", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))
        self.actionClear.setText(_translate("MainWindow", "Clear", None))

from PyQt4 import QtWebKit
