#!/usr/bin/env python3

"""
PhotoGeoTagger allows to add a geographic position to picture (geotag).
The geographic position is saved in the EXIF metadata of the picture.


apt install libexiv2-dev exiv2
apt-get install libboost-all-dev
pip3 install py3exiv2
"""

import sys
import os
import glob
import fractions
import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.Qt import *

try:
    import pyexiv2
except:
    print("pyexiv2 is not installed. See http://python3-exiv2.readthedocs.io/en/latest/developers.html#getting-the-code")
    sys.exit(1)

__version__ = 0.4
__version_date__ = "2017-03-14"


defaultServer= "tile.osm.org"
#defaultServer =  'tile.opencyclemap.org/cycle'

THUMBNAIL_SIZE = 128

defaultLat = 45.03
defaultLon = 7.66
defaultZoom = 12
GPS = "Exif.GPSInfo.GPS"

HTML = """
<html>
<head><style>#map { position:absolute; left:0; top:0; bottom:0; width:100%%; }</style></head>
<body>
<script src="http://cdn.leafletjs.com/leaflet-0.7.3/leaflet.js"></script>
<link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.7.3/leaflet.css" />
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>    
new QWebChannel(qt.webChannelTransport, function (channel) { window.bridge = channel.objects.bridge;});
</script>

<div id="map"></div>

<script>
var map = L.map('map').setView([%(defaultLat)f, %(defaultLon)f], %(defaultZoom)f);

L.tileLayer('http://{s}.%(defaultServer)s/{z}/{x}/{y}.png', { attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);

//map.on('moveend', function(e) {update.out( map.getZoom() ) })

map.on('click', function(e) { window.bridge.print(e.latlng.lat + "|" + e.latlng.lng)})
map.on('moveend', function(e) {window.bridge.get_zoom(map.getZoom())})

</script>
</body>
</html>
""" % globals()


class Fraction(fractions.Fraction):
    def __new__(cls, value, ignore=None):
        return fractions.Fraction.from_float(value).limit_denominator(99999)

def decimal_to_dms(decimal):
    """
    Convert decimal degrees into degrees, minutes, seconds.
    """
    remainder, degrees = math.modf(abs(decimal))
    remainder, minutes = math.modf(remainder * 60)
    return [Fraction(n) for n in (degrees, minutes, remainder * 60)]

def decCoordinate(ref, coord):
    """
    Convert degree, minutes coordinates to decimal coordinates
    """
    deg, min, sec = coord.split(" ")
    coordDec = eval(deg) + eval(min)/60 + eval(sec)/3600
    if ref in ["S", "W"]:
        coordDec =- coordDec
    return coordDec


def MessageDialog(title, text, buttons):
    """
    show message dialog and return text of clicked button
    """
    response = ""
    message = QMessageBox()
    message.setWindowTitle(title)
    message.setText(text)
    message.setIcon(QMessageBox.Question)
    for button in buttons:
        message.addButton(button, QMessageBox.YesRole)

    message.exec_()
    return message.clickedButton().text()

class WebPage(QWebEnginePage):
    
    def __init__(self, parent=None):
        super(WebPage, self).__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, msg, linenumber, source_id):
        try:
            print('%s:%s: %s' % (source_id, linenumber, msg))
        except OSError:
            pass

    @pyqtSlot(int)
    def get_zoom(self, z):
        """
        update zoom value from leaflet value
        """

        print("zoom", z)
        self.parent.zoom = z
        self.parent.statusbar.showMessage("Zoom: {}".format(z), 0)


    @pyqtSlot(str)
    def print(self, text):
        print('From JS:', text)
        
        click_lat, click_long = [float(x) for x in text.split('|')]
        print(click_lat, click_long)

        
        self.parent.statusbar.showMessage('Position %.6f, %.6f  ' % (click_lat, click_long ), 0)


        '''
        if self.parent.listWidget.selectedItems():
            self.parent.removeAllMarkers()
        '''

        for item in self.parent.listWidget.selectedItems():

            flagChanged = False

            if self.parent.gps_dict[ item.text() ]['gps'] == (0.0, 0.0, 0.0):
                flagChanged = True

                b = QBrush()
                b.setColor(QColor(0,0,0))
                item.setForeground( b)

            else:

                if MessageDialog("photoGeoTagger", "Replace current position?", ['Yes', 'No']) == 'Yes':
                    flagChanged = True

            if flagChanged:

                    self.parent.gps_dict[ item.text()]['gps'] = ( click_lat, click_long,  0.0)

                    id = item.text().replace("-", "")
                    s = "m%(id)s = new L.Marker([%(lat)f, %(lon)f], {draggable:true});map.addLayer(m%(id)s);m%(id)s.bindPopup('%(id)s').openPopup();" % {'lat':click_lat, 'lon':click_long, 'id': id}

                    #self.parent.frame.evaluateJavaScript(s )
                    self.parent.browser.page().runJavaScript(s)
                    self.parent.memMarker.append(id)

                    self.parent.get_map(click_lat, click_long, self.parent.zoom)

                    self.parent.statusbar.showMessage("Set picture position %.6f, %.6f  " % (click_lat, click_long ), 0)

                    self.parent.changed.append( item.text() )


class MySignal(QObject):
    sig = pyqtSignal(str)
    coord = pyqtSignal(dict)
    thumbnail = pyqtSignal(QImage, str)


class MyLongThread(QThread):
    def __init__(self, parent = None):
            QThread.__init__(self, parent)
            self.picturesPath = ""
            self.signal = MySignal()

    def run(self):

        path = self.picturesPath

        if os.path.isdir(path):
            imgList = sorted(glob.glob(path + "/*.jpg") + glob.glob(path + "/*.JPG"))

        if os.path.isfile(path):
            imgList = [path]

        self.changed =  []

        for pic in sorted(imgList):
            print('processing {}'.format(pic))

            label = os.path.basename(pic).replace('.jpg','').replace('.JPG','')

            # read GPS exif tag
            metadata = pyexiv2.ImageMetadata(pic)
            metadata.read()
            latRaw, lonRaw = 0, 0
            try:
                latRaw = metadata['Exif.GPSInfo.GPSLatitude'].raw_value
                latRef = metadata['Exif.GPSInfo.GPSLatitudeRef'].raw_value
                lonRaw = metadata['Exif.GPSInfo.GPSLongitude'].raw_value
                lonRef = metadata['Exif.GPSInfo.GPSLongitudeRef'].raw_value
            except KeyError:
                pass

            if latRaw and lonRaw:
                #self.gps_dict[ label ] = {'gps': (decCoordinate(latRef, latRaw), decCoordinate(lonRef, lonRaw), 0.0),  'filename': pic}
                self.signal.coord.emit({'gps': (decCoordinate(latRef, latRaw), decCoordinate(lonRef, lonRaw), 0.0),  'filename': pic})
            else:
                #self.gps_dict[ label ] = {'gps': (0, 0, 0), 'filename': pic}
                self.signal.coord.emit({'gps': (0, 0, 0), 'filename': pic})

            i = QImage(pic).scaledToWidth(THUMBNAIL_SIZE)
            self.signal.thumbnail.emit(i, label)


            # filename in red for pictures with no location
            '''
            if self.gps_dict[ label]['gps'] == (0, 0, 0):
                b = QBrush()
                b.setColor(QColor(255,0,0))
                configButton.setForeground( b)
            '''


        '''
        if len(imgList) == 1:
            print 'set current item',self.listWidget.item(0)
            self.listWidget.setCurrentItem(self.listWidget.item(0))
        '''

        '''self.signal.sig.emit('OK')'''



class MainWindow(QMainWindow):
    

    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.changed = []

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        self.actionLoad_photo_from_directory = QAction("Load photos from directory", self)
        self.actionLoad_photo_from_directory.setObjectName("actionLoad_photo_from_directory")

        self.actionSave_positions_to_photo = QAction("Save positions to photos", self)
        self.actionSave_positions_to_photo.setObjectName("actionSave_positions_to_photo")


        self.actionClear = QAction("Clear", self)
        self.actionClear.setObjectName("actionClear")

        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        fileMenu.addAction(self.actionLoad_photo_from_directory)
        fileMenu.addAction(self.actionSave_positions_to_photo)
        fileMenu.addAction(self.actionClear)
        fileMenu.addAction(exitAction)
        
        menuHelp = menubar.addMenu('&Help')

        self.actionAbout = QAction("About", self)
        self.actionAbout.setObjectName("actionAbout")
        menuHelp.addAction(self.actionAbout)

        '''self.menubar.addAction(self.menuPhoto_geotag.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        '''

        self.actionSave_positions_to_photo.triggered.connect(self.save_positions)
        self.actionLoad_photo_from_directory.triggered.connect(self.load_directory_activated)
        self.actionClear.triggered.connect(self.clear)

        self.actionAbout.triggered.connect(self.actionAbout_activated)

        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage('ciao', 0)

        self.longthread = MyLongThread()
        self.longthread.finished.connect(self.terminated)
        self.longthread.signal.coord.connect(self.addCoord)
        self.longthread.signal.thumbnail.connect(self.addThumbnail)
        
        self.gps_dict = {}
        self.lat = defaultLat
        self.long = defaultLon
        self.zoom = defaultZoom
        self.memPosition = (0, 0, 0)
        
        self.memMarker = []

        _widget = QWidget()

        self.vbox = QVBoxLayout()
        self.hbox = QHBoxLayout()

        self.splitter = QSplitter(_widget)
        self.splitter.setOrientation(Qt.Horizontal)

        self.listWidget = QListWidget(self.splitter)
        self.listWidget.width()
        self.listWidget.setViewMode(QListView.IconMode)
        self.listWidget.setIconSize(QSize(128, 128))
        self.listWidget.setMovement(QListView.Static)
        self.listWidget.setMaximumWidth(256)
        self.listWidget.setSpacing(12)
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        self.listWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.actionCopyPosition = QAction("Copy position", self.listWidget)
        self.actionPastePosition = QAction("Paste position", self.listWidget)
        self.listWidget.addAction(self.actionCopyPosition)
        self.listWidget.addAction(self.actionPastePosition)
        self.actionCopyPosition.triggered.connect(self.copyPosition)
        self.actionPastePosition.triggered.connect(self.pastePosition)

        self.listWidget.itemSelectionChanged.connect(self.itemSelectionChanged)
        
        
        self.hbox.addWidget(self.listWidget)

        self.browser = QWebEngineView(self.splitter)
        self.p = WebPage(self)
        self.browser.setPage(self.p)
        c = QWebChannel(self)
        c.registerObject('bridge', self.p)
        self.p.setWebChannel(c)
        self.browser.setHtml(HTML)

        
        self.hbox.addWidget(self.browser)
        self.hbox.addWidget(self.splitter)
        self.vbox.addLayout(self.hbox)
        _widget.setLayout(self.vbox)

        self.setCentralWidget(_widget)


    def terminated(self):
        """
        longthread terminated
        """
        self.listWidget.setMinimumWidth(self.listWidget.sizeHintForColumn(0))
        self.statusbar.showMessage("Photos loaded from directory")


    def addCoord(self, coord):
        """
        add coordinates to dictionary
        """

        label = os.path.basename(coord['filename']).replace('.jpg','').replace('.JPG','')
        self.gps_dict[label] = coord

    def addThumbnail(self, image, label):
        """
        add thumbnail to listview
        """
        configButton = QListWidgetItem(self.listWidget)
        configButton.setIcon(QIcon(QPixmap(image)))

        print(label)
        if label in self.gps_dict:
            print( self.gps_dict[label] )

        if label in self.gps_dict and self.gps_dict[label]['gps'] == (0, 0, 0):
            b = QBrush()
            b.setColor(QColor(255,0,0))
            configButton.setForeground( b)

        configButton.setText(label)

        configButton.setTextAlignment(Qt.AlignHCenter)
        configButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def copyPosition(self):

        if len(self.listWidget.selectedItems()) == 1:

            self.memPosition = self.gps_dict[ self.listWidget.selectedItems()[0].text() ]['gps']
            if self.memPosition != (0,0,0):
                self.statusbar.showMessage('Copied position ' + str(self.memPosition)  , 5000)
            else:
                self.statusbar.showMessage('Photo do not contain position', 5000)


    def pastePosition(self):

        if self.memPosition == (0,0,0):
            self.statusbar.showMessage('No position in clipboard' , 5000)
            return

        if self.listWidget.selectedItems():
            self.removeAllMarkers()

        for item in self.listWidget.selectedItems():
            self.gps_dict[ item.text() ]['gps'] = self.memPosition
            self.changed.append( item.text())

            id = item.text().replace('-','')
            s = "m%(id)s = new L.Marker([%(lat)f, %(lon)f], {draggable:true});map.addLayer(m%(id)s);m%(id)s.bindPopup('%(id)s').openPopup();" % {'lat':self.memPosition[0], 'lon':self.memPosition[1], 'id': id}

            #self.frame.evaluateJavaScript(s )

            self.browser.page().runJavaScript(s)
            self.memMarker.append( id )

            self.get_map(self.memPosition[0], self.memPosition[1], self.zoom)

            self.statusbar.showMessage("Set photo position %.6f, %.6f  " % (self.memPosition[0], self.memPosition[1] ), 0)

            b = QBrush()
            b.setColor(QColor(0,0,0))
            item.setForeground( b)


    def actionAbout_activated(self):
        '''
        about window
        '''
        import platform

        QMessageBox.about(self, "About PhotoGeoTagger",
        """<b>{programName}</b><br>
        v. {version} - {versionDate}<br>
        <br>
        Copyright 2014-2017 Olivier Friard<br>
        <br>
        https://github.com/barmanoo/pyPhotoGeoTagger<br>
        <br>
        Python {pythonVersion} - Qt {qtVersion} - PyQt v. {pyqtVersion}""".format( 
        programName="pyPhotoGeoTagger", version=__version__, versionDate=__version_date__,
         pythonVersion=platform.python_version(),
          qtVersion=QT_VERSION_STR, pyqtVersion=PYQT_VERSION_STR )
          )



    def save_positions(self):
        """
        save modified position to photo
        """
        if self.changed:
            for pic in self.changed:
                metadata = pyexiv2.ImageMetadata(self.gps_dict[ pic ]['filename'])
                metadata.read()

                metadata[GPS + 'Latitude']     = decimal_to_dms(self.gps_dict[ pic ]['gps'][0])
                metadata[GPS + 'LatitudeRef']  = 'N' if self.gps_dict[ pic ]['gps'][0] >= 0 else 'S'
                metadata[GPS + 'Longitude']    = decimal_to_dms(self.gps_dict[ pic ]['gps'][1])
                metadata[GPS + 'LongitudeRef'] = 'E' if self.gps_dict[ pic ]['gps'][1] >= 0 else 'W'
                metadata.write()

            self.statusbar.showMessage('Positions saved in photos', 5000)
            self.changed = []

    def removeAllMarkers(self):
        '''
        remove all markers from leaflet
        '''
        for m in self.memMarker:
            self.browser.page().runJavaScript("map.removeLayer({});".format(m))

        self.memMarker = []

    def itemSelectionChanged(self):

        '''self.removeAllMarkers()'''

        for item in self.listWidget.selectedItems():
            pictLat, pictLon = self.gps_dict[ item.text()]["gps"][0:2]
            if pictLat or pictLon:
                id = item.text().replace("-", "")
                s = "m%(id)s = new L.Marker([%(lat)f, %(lon)f], {draggable:true});map.addLayer(m%(id)s);m%(id)s.bindPopup('%(id)s').openPopup();" % {'lat':pictLat, 'lon':pictLon, 'id': id}

                #self.frame.evaluateJavaScript(s)
                self.browser.page().runJavaScript(s)
                self.memMarker.append(id)
                self.get_map(pictLat, pictLon, self.zoom)

    def get_map(self, lat, lon, zoom):
        """
        set leaflet with parameters latitude, longitude and zoom
        """
        if lat or lon:
            #self.frame.evaluateJavaScript("map.setView([%f, %f], %d);" % (lat, lon, zoom))
            self.browser.page().runJavaScript("map.setView([%f, %f], %d);" % (lat, lon, zoom))



    def load_directory_activated(self):

        if self.changed:
            response = MessageDialog("PhotoGeoTagger", "Save positions to photos?", ["Yes", "No", "Cancel"])

            if response == "Yes":
                self.save_positions()

            if response == "Cancel":
                return

        directory = QFileDialog.getExistingDirectory(self, "Open Directory", os.getcwd(), QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly)

        self.longthread.picturesPath = directory
        self.longthread.start()

    def closeEvent(self, event):
        '''
        check if pictures position are saved and close program
        '''

        if self.changed:
            response = MessageDialog('pyPhotoGeoTagger', 'Save positions to photos?', ['Yes', 'No', 'Cancel'])

            if response == 'Yes':
                self.save_positions()

            if response == 'Cancel':
                event.ignore()


    def clear(self):
        """
        clear list view
        """
        self.gps_dict = {}
        self.listWidget.clear()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    if len(sys.argv) > 1:
        if os.path.isdir(os.path.abspath(sys.argv[1])) or os.path.isfile(os.path.abspath(sys.argv[1])):
            longthread = MyLongThread()
            longthread.finished.connect(win.terminated)
            longthread.signal.coord.connect(win.addCoord)
            longthread.signal.thumbnail.connect(win.addThumbnail)
            longthread.picturesPath = os.path.abspath(sys.argv[1])
            longthread.start()

    win.show()
    app.exec_()


if __name__ == '__main__':
    sys.exit(main())
