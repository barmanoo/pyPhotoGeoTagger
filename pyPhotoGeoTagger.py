#!/usr/bin/env python
'''

pyPhotoGeoTagger
Copyright 2014 Olivier Friard

usage:
left button: save coordinates (latitude, longitude) of clicked pixel in selected picture

based on Leaflet (http://leafletjs.com/)
require pyexiv2:
aptitude install python2.7-pyexiv2

This file is part of pyPhotoGeoTagger.


  pyPhotoGeoTagger is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 3 of the License, or
  any later version.
  
  pyPhotoGeoTagger is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with this program; if not see <http://www.gnu.org/licenses/>.



'''

from __future__ import division, print_function

__version__ = 0.1
__version_date__ = '2014-12-18'

defaultServer= 'tile.osm.org'
#defaultServer =  'tile.opencyclemap.org/cycle'

defaultLat = 45.03
defaultLon = 7.66
defaultZoom = 12


HTML = """
<html>
<head><style>#map { position:absolute; left:0; top:0; bottom:0; width:100%%; }</style></head>
<body>
<script src="http://cdn.leafletjs.com/leaflet-0.7.3/leaflet.js"></script>
<link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.7.3/leaflet.css" />

<div id="map"></div>

<script>
var map = L.map('map').setView([%(defaultLat)f, %(defaultLon)f], %(defaultZoom)f);

L.tileLayer('http://{s}.%(defaultServer)s/{z}/{x}/{y}.png', { attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);

map.on('click', function(e) {clickedPos.out(e.latlng.lat + "|" + e.latlng.lng)})
map.on('moveend', function(e) {update.out( map.getZoom() ) })

</script>
</body>
</html>
""" % globals()

GPS = 'Exif.GPSInfo.GPS'

import PySide
from PySide.QtCore import *
from PySide import QtCore
from PySide.QtGui import *
import glob
import os
import sys
import math
import fractions

try:
    import pyexiv2
except:
    print( 'pyexiv2 is not installed. See http://tilloy.net/dev/pyexiv2/')
    sys.exit(1)
    

from pyPhotoGeoTagger_ui import Ui_MainWindow

RED = QColor(255,0,0)


class Fraction(fractions.Fraction):
    def __new__(cls, value, ignore=None):
        return fractions.Fraction.from_float(value).limit_denominator(99999)

def decimal_to_dms(decimal):
    '''
    Convert decimal degrees into degrees, minutes, seconds.
    '''
    remainder, degrees = math.modf(abs(decimal))
    remainder, minutes = math.modf(remainder * 60)
    return [Fraction(n) for n in (degrees, minutes, remainder * 60)]


def decCoordinate(ref, coord):
    '''
    Convert degree, minutes coordinates to decimal coordinates
    '''
    deg, min, sec = coord.split(' ')
   
    coordDec = eval(deg) + eval(min)/60 + eval(sec)/3600

    if ref in ['S','W']:
        coordDec =- coordDec

    return coordDec


def MessageDialog(title, text, buttons):
    '''
    show message dialog and return text of clicked button
    '''
    response = ''
    message = QMessageBox()
    message.setWindowTitle(title)
    message.setText(text)
    message.setIcon(QMessageBox.Question)
    for button in buttons:
        message.addButton(button, QMessageBox.YesRole)

    message.exec_()
    return message.clickedButton().text()

class Update(QObject):
    def __init__(self, parent=None):
        super(Update, self).__init__(parent)
        self.parent = parent

    @QtCore.Slot(str)


    def out(self, message):
        '''
        update zoom value from leaflet value
        '''

        self.parent.zoom = int(message)
        self.parent.statusbar.showMessage('Zoom: %s ' % (message ), 0)
    

class ClickedPos(QObject):
    def __init__(self, parent=None):
        super(ClickedPos, self).__init__(parent)
        self.parent = parent


    @QtCore.Slot(str)
    def out(self, message):
        '''
        obtain clicked position from leaflet
        '''
        
        click_lat, click_long = [float(x) for x in message.split('|')]
        self.parent.statusbar.showMessage('Position %.6f, %.6f  ' % (click_lat, click_long ), 0)
        

        if self.parent.listWidget.selectedItems():
            self.parent.removeAllMarkers()

        for item in self.parent.listWidget.selectedItems():
            
            flagChanged = False

            if self.parent.gps_dict[ item.text() ]['gps'] == (0.0, 0.0, 0.0):
                flagChanged = True

                b = QBrush()
                b.setColor(QColor(0,0,0))
                item.setForeground( b)

            else:

                if MessageDialog('photoGeoTagger', 'Replace current position?', ['Yes', 'No']) == 'Yes':
                    flagChanged = True

            if flagChanged:

                    self.parent.gps_dict[ item.text()]['gps'] = ( click_lat, click_long,  0.0)

                    id = item.text().replace('-','')
                    s = "m%(id)s = new L.Marker([%(lat)f, %(lon)f], {draggable:true});map.addLayer(m%(id)s);m%(id)s.bindPopup('%(id)s').openPopup();" % {'lat':click_lat, 'lon':click_long, 'id': id}
    
                    self.parent.frame.evaluateJavaScript(s )
                    self.parent.memMarker.append( id )

                    self.parent.get_map(click_lat, click_long, self.parent.zoom)

                    self.parent.statusbar.showMessage('Set picture position %.6f, %.6f  ' % (click_lat, click_long ), 0)
                    
                    self.parent.changed.append( item.text() )


class MySignal(QObject):
        sig = Signal(str)
        coord = Signal(dict)
        thumbnail = Signal(QImage,str)

class MyLongThread(QThread):
    def __init__(self, parent = None):
            QThread.__init__(self, parent)
            self.picturesPath = ''
            self.signal = MySignal()

    def run(self):

        path = self.picturesPath

        if os.path.isdir(path):
            imgList = sorted(glob.glob(path + '/*.jpg') + glob.glob(path + '/*.JPG'))

        if os.path.isfile(path):
            imgList = [ path ]

        self.changed =  []

        for pic in sorted(imgList):
            print('processing %s' % pic)

            label = os.path.basename(pic).replace('.jpg','').replace('.JPG','')

            i = QImage(pic).scaledToWidth(128)
            self.signal.thumbnail.emit( i, label)

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


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle('pyPhotoGeoTagger')

        self.changed = []

        self.listWidget.setViewMode(QListView.IconMode)
        self.listWidget.setIconSize(QSize(128, 128))
        self.listWidget.setMovement(QListView.Static)
        self.listWidget.setMaximumWidth(256)
        self.listWidget.setSpacing(12)

        self.listWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.actionCopyPosition = QAction("Copy position", self.listWidget)
        self.actionPastePosition = QAction("Paste position", self.listWidget)
        self.listWidget.addAction(self.actionCopyPosition)
        self.listWidget.addAction(self.actionPastePosition)
        self.connect(self.actionCopyPosition, SIGNAL("triggered()"), self.copyPosition)
        self.connect(self.actionPastePosition, SIGNAL("triggered()"), self.pastePosition)

        self.listWidget.itemSelectionChanged.connect(self.itemSelectionChanged)

        # menu
        self.actionSave_positions_to_photo.activated.connect(self.save_positions)
        self.actionLoad_photo_from_directory.activated.connect(self.load_directory_activated)
        self.actionQuit.activated.connect(self.close)

        self.actionAbout.triggered.connect(self.actionAbout_activated)

        self.gps_dict = {}

        self.frame = self.webView.page().mainFrame()
        clickedPos = ClickedPos(self)
        update = Update(self)
        self.webView.setHtml(HTML)
        self.frame.addToJavaScriptWindowObject('clickedPos', clickedPos)
        self.frame.addToJavaScriptWindowObject('update', update)


        self.longthread = MyLongThread()
        self.longthread.finished.connect(self.terminated)
        self.longthread.signal.coord.connect(self.addCoord)
        self.longthread.signal.thumbnail.connect(self.addThumbnail)


        self.lat = defaultLat
        self.long = defaultLon
        self.zoom = defaultZoom
        self.memPosition = (0,0,0)

        # list of markers on leaflet
        self.memMarker = []

    def terminated(self):
        '''
        longthread terminated
        '''
        self.statusbar.showMessage('Directory loaded' )


    def addCoord(self, coord):
        '''
        add coordinates to dictionary
        '''

        label = os.path.basename(coord['filename']).replace('.jpg','').replace('.JPG','')
        self.gps_dict[ label ] = coord

    def addThumbnail(self, image, label):
        '''
        add thumbnail to listview
        '''
        configButton = QListWidgetItem(self.listWidget)
        configButton.setIcon(QIcon(QPixmap(image)))
    
        configButton.setText(label)
    
        configButton.setTextAlignment(Qt.AlignHCenter)
        configButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)


    def copyPosition(self):

        if len(self.listWidget.selectedItems()) == 1:

            self.memPosition = self.gps_dict[ self.listWidget.selectedItems()[0].text() ]['gps']
            if self.memPosition != (0,0,0):
                self.statusbar.showMessage('Copied position '+str(self.memPosition)  , 5000)
            else:
                self.statusbar.showMessage('Photo do not contain position' , 5000)



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

            self.frame.evaluateJavaScript(s )
            self.memMarker.append( id )

            self.get_map(self.memPosition[0], self.memPosition[1], self.parent.zoom)

            self.statusbar.showMessage('Set photo position %.6f, %.6f  ' % (self.memPosition[0], self.memPosition[1] ), 0)


            b = QBrush()
            b.setColor(QColor(0,0,0))
            item.setForeground( b)



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


    def load_directory_activated(self):

        if self.changed:
            response = MessageDialog('pyPhotoGeoTagger', 'Save positions to photos?', ['Yes', 'No', 'Cancel'])

            if response == 'Yes':
                self.save_positions()

            if response == 'Cancel':
                return

        flags = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Open Directory", os.getcwd(), flags)

        '''
        if directory:
            self.load_directory(directory)
        '''

        self.longthread.picturesPath = directory
        self.longthread.start()



    def load_directory(self, path):
        '''
        load thumbnails of images from directory in listview widget
        '''
        
        if os.path.isdir(path):
            imgList = sorted(glob.glob(path + '/*.jpg') + glob.glob(path + '/*.JPG'))

        if os.path.isfile(path):
            imgList = [ path ]

        self.listWidget.clear()
        self.changed =  []

        for pic in sorted(imgList):
            print('processing %s' % pic)
            configButton = QListWidgetItem(self.listWidget)
            configButton.setIcon(QIcon(QPixmap(pic).scaledToWidth(128)))

            label = os.path.basename(pic).replace('.jpg','').replace('.JPG','')
            configButton.setText(label)

            configButton.setTextAlignment(Qt.AlignHCenter)
            configButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

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
                self.gps_dict[ label ] = {'gps': (decCoordinate(latRef, latRaw), decCoordinate(lonRef, lonRaw), 0.0),  'filename': pic}
            else:
                self.gps_dict[ label ] = {'gps': (0, 0, 0), 'filename': pic}

            # filename in red for pictures with no location
            if self.gps_dict[ label]['gps'] == (0, 0, 0):
                b = QBrush()
                b.setColor(RED)
                configButton.setForeground( b)

        if len(imgList) == 1:
            self.listWidget.setCurrentItem(self.listWidget.item(0))


    def save_positions(self):
        '''
        save modified position to photo
        '''
        if self.changed:
            for pic in self.changed:
                metadata = pyexiv2.ImageMetadata(self.gps_dict[ pic ]['filename'])
                metadata.read()

                metadata[GPS + 'Latitude']     = decimal_to_dms(self.gps_dict[ pic ]['gps'][0])
                metadata[GPS + 'LatitudeRef']  = 'N' if self.gps_dict[ pic ]['gps'][0] >= 0 else 'S'
                metadata[GPS + 'Longitude']    = decimal_to_dms(self.gps_dict[ pic ]['gps'][1])
                metadata[GPS + 'LongitudeRef'] = 'E' if self.gps_dict[ pic ]['gps'][1] >= 0 else 'W'
                metadata.write()

            self.statusbar.showMessage('Picture positions saved', 5000)
            self.changed = []


    def removeAllMarkers(self):
        '''
        remove all markers from leaflet
        '''
        for m in self.memMarker:
            self.frame.evaluateJavaScript("map.removeLayer(m%s);" % m )
            
        self.memMarker = []
        

    def itemSelectionChanged(self):

        self.removeAllMarkers()

        for item in self.listWidget.selectedItems():
            pictLat, pictLon = self.gps_dict[ item.text() ]['gps'][0:2]
            id = item.text().replace('-','')
            s = "m%(id)s = new L.Marker([%(lat)f, %(lon)f], {draggable:true});map.addLayer(m%(id)s);m%(id)s.bindPopup('%(id)s').openPopup();" % {'lat':pictLat, 'lon':pictLon, 'id': id}

            self.frame.evaluateJavaScript(s )
            self.memMarker.append( id )
            self.get_map(pictLat, pictLon, self.zoom)


    def get_map(self, lat, lon, zoom):
        '''
        set leaflet with parameters latitude, longitude and zoom
        '''
        if lat or lon:
            self.frame.evaluateJavaScript("map.setView([%f, %f], %d);" % (lat, lon, zoom))


    def actionAbout_activated(self):
        '''
        about window
        '''
        import platform

        QMessageBox.about(self, "About pyPhotoGeoTagger",
        """<b>%s</b><br>
        v. %s - %s<br>
        Copyright &copy; 2014 Olivier Friard<br>
        <br>
        https://github.com/olivierfriard/pyphotogeotagger<br>
        <br>
        Python %s - Qt %s - PySide %s on %s""" % \
        ('pyPhotoGeoTagger', __version__, __version_date__, platform.python_version(), PySide.QtCore.__version__, PySide.__version__, platform.system()))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    mainWindow = MainWindow()
    if len(sys.argv) > 1:
        mainWindow.load_directory( os.path.abspath( sys.argv[1]) )
    
    mainWindow.show()
    mainWindow.resize(800, 500)
    sys.exit(app.exec_())
