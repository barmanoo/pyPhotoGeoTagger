# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pyPhotoGeoTagger.ui'
#
# Created: Thu Feb 26 00:11:42 2015
#      by: pyside-uic 0.2.13 running on PySide 1.1.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(775, 601)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtGui.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.listWidget = QtGui.QListWidget(self.splitter)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget.setObjectName("listWidget")
        self.webView = QtWebKit.QWebView(self.splitter)
        self.webView.setUrl(QtCore.QUrl("about:blank"))
        self.webView.setObjectName("webView")
        self.horizontalLayout.addWidget(self.splitter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 775, 19))
        self.menubar.setObjectName("menubar")
        self.menuPhoto_geotag = QtGui.QMenu(self.menubar)
        self.menuPhoto_geotag.setObjectName("menuPhoto_geotag")
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionSave_positions_to_photo = QtGui.QAction(MainWindow)
        self.actionSave_positions_to_photo.setObjectName("actionSave_positions_to_photo")
        self.actionLoad_photo_from_directory = QtGui.QAction(MainWindow)
        self.actionLoad_photo_from_directory.setObjectName("actionLoad_photo_from_directory")
        self.actionAbout = QtGui.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.menuPhoto_geotag.addAction(self.actionLoad_photo_from_directory)
        self.menuPhoto_geotag.addAction(self.actionSave_positions_to_photo)
        self.menuPhoto_geotag.addAction(self.actionQuit)
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuPhoto_geotag.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.menuPhoto_geotag.setTitle(QtGui.QApplication.translate("MainWindow", "Photo", None, QtGui.QApplication.UnicodeUTF8))
        self.menuHelp.setTitle(QtGui.QApplication.translate("MainWindow", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave_positions_to_photo.setText(QtGui.QApplication.translate("MainWindow", "Save positions to photo", None, QtGui.QApplication.UnicodeUTF8))
        self.actionLoad_photo_from_directory.setText(QtGui.QApplication.translate("MainWindow", "Load photo from directory", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAbout.setText(QtGui.QApplication.translate("MainWindow", "About...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("MainWindow", "Quit", None, QtGui.QApplication.UnicodeUTF8))

from PySide import QtWebKit
