# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThreePoint
                                 A QGIS plugin
 Determine the orientation of geological surfaces using three point vector method
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-12-30
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Ewelina Brach
        email                : ewebrach@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import *
import math
from qgis.core import *
from PyQt5.QtWidgets import QMessageBox, QAction,QFileDialog

from qgis.utils import plugins

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .three_point_dialog import ThreePointDialog
import os.path
from PyQt5.QtCore import QVariant
import pandas as pd
import  processing
from qgis.core import QgsPalLayerSettings


class ThreePoint:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ThreePoint_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&ThreePoint')
        self.dlg=None

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ThreePoint', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/three_point/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'ThreePoint'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&ThreePoint'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_input_file(self):
        filename, _filter = QFileDialog.getOpenFileName(
            self.dlg, "Select input file ","", '*.shp'
        )
        self.dlg.comboBox.addItem(filename)
        index = self.dlg.comboBox.findText(filename)
        self.dlg.comboBox.setCurrentIndex(index)


    def select_inputDEM(self):
        filename, _filter = QFileDialog.getOpenFileName(
            self.dlg, "Select input DEM ","", '*.tif'
        )
        self.dlg.comboBox_2.addItem(filename)
        index = self.dlg.comboBox_2.findText(filename)
        self.dlg.comboBox_2.setCurrentIndex(index)


    def select_output_file(self):
        filename, _filter = QFileDialog.getSaveFileName(
        self.dlg, "Select output file ", "", '*.shp'
        )
        
        self.dlg.lineEdit_2.setText(filename)


    def run(self):
        isrunning=plugins["three_point"]
        if (isrunning.dlg):
            if isrunning.dlg.isVisible():
                return
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = ThreePointDialog()
            self.dlg.pushButton.clicked.connect(self.select_input_file)
            self.dlg.pushButton_2.clicked.connect(self.select_output_file)
            self.dlg.pushButton_3.clicked.connect(self.select_inputDEM)
            self.dlg.pushButton_4.clicked.connect(self.on_pushOK)
            self.dlg.pushButton_5.clicked.connect(self.on_pushCancel)
        
        #clear the dialog
        self.clear_dlg()

        #add layers to the comboBox
        layers_shp = ['<Select an input layer>'] 
        layers_raster = ['<Select a raster layer>']
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.type() != QgsMapLayer.RasterLayer:
                layers_shp.append(layer.name())

            else: layers_raster.append(layer.name())


        self.dlg.comboBox.addItems(layers_shp)
        self.dlg.comboBox_2.addItems(layers_raster)

        # show the dialog
        self.dlg.show()

    def clear_dlg(self):
        self.dlg.comboBox.clear()
        self.dlg.lineEdit_2.clear()
        self.dlg.comboBox_2.clear()
    

    def on_pushCancel(self):
        self.clear_dlg()
        self.dlg.close()


    def set_path(self,path):
        if not QgsProject.instance().mapLayersByName(path):
            layer = path
        else:
            raster_layer = QgsProject.instance().mapLayersByName(path)[0]
            layer = raster_layer.source()
        return layer


    def get_dir(self,name, path=None):
                if not path:
                    path = os.path.dirname(os.path.realpath(__file__))
                return os.path.join(path, name)
    
      
    def on_pushOK(self):
        
        path_input = self.set_path(self.dlg.comboBox.currentText())
        path_raster = self.set_path(self.dlg.comboBox_2.currentText())
        
            
        if os.path.exists(path_input) == False:
            QMessageBox.warning(self.dlg, "Warning", "Select an Input File")
        elif os.path.exists(path_raster) == False:
            QMessageBox.warning(self.dlg, "Warning", "Select an Input DEM")
        elif not self.dlg.lineEdit_2.text():
            QMessageBox.warning(self.dlg, "Warning", "Select a location for Output File")
        elif os.path.exists(self.dlg.lineEdit_2.text()) == True:
            QMessageBox.warning(self.dlg, "Warning","File already exists, please change the name")
                
        else:

            #set Z value from raster
            params1 = {'INPUT': path_input,
                    'RASTER': path_raster,
                    'BAND': 1,
                    'SCALE':1.0,
                    'OUTPUT': 'TEMPORARY_OUTPUT'}


            temp = processing.run("native:setzfromraster", params1)
            temp = temp['OUTPUT']

            #export geometry to attribute table
            params2 = {'INPUT': temp,
                    'CALC_METHOD': 1,
                    'OUTPUT': self.dlg.lineEdit_2.text()}

        
            processing.run("qgis:exportaddgeometrycolumns", params2)

            
            path = os.path.basename(self.dlg.lineEdit_2.text())
            layer = QgsVectorLayer(self.dlg.lineEdit_2.text(), path.strip(".shp"))
            tab_values = ["Id","FID","U1","-U2","U3","eastingFlo","northingFl","strikeFloa","dipFloat","strike","dipDir","dip","easting","northing","elevation"]
            tab_name = {}
            
            #adding new columns
            layer_provider = layer.dataProvider()
            for i in range(1,len(tab_values)):
                if i == 1 or i == 9 or i==10 or i == 11:
                    
                    layer_provider.addAttributes([QgsField(tab_values[i], QVariant.Int)])
                else:
                    layer_provider.addAttributes([QgsField(tab_values[i], QVariant.Double)])
                    
            layer.updateFields()


            for i in range(len(tab_values)):
                tab_name.update({tab_values[i]:layer.fields().indexFromName(tab_values[i])})
               
           
            nrows = 0
            tabU1 = []
            tabU2 = []
            tabU3 = []
            tabEst = []
            tabNor = []
            tabEle = []
            attrE = []
            attrN = []
            attrS = []
            attrD = []
            fid = []

            features = layer.getFeatures()
            for f in features:
                nrows = nrows + 1

            fields = [field.name() for field in layer.fields()]
            tab_attr = []
            features = layer.getFeatures()
            for feature in features:
                tab_attr += [feature.attributes()]
            attr = pd.DataFrame(tab_attr, columns=fields)

            features = layer.getFeatures()
            layer_provider = layer.dataProvider()


            for i in range(0, nrows, 3):
                a = attr[i :i+1]
                b = attr[i+1:i + 2]
                c = attr[i + 2:i + 3]

                U1i = (float(a['ycoord']) - float(b['ycoord'])) * ((float(c['zcoord'] - float(b['zcoord'])))) - ((float(c['ycoord'] - float(b['ycoord'])))) * (float(a['zcoord'] - float(b['zcoord'])))
                U2j = -(float((a['xcoord']) - float(b['xcoord'])) * (float(c['zcoord']) - float(b['zcoord'])) - (float(c['xcoord']) - float(b['xcoord'])) * (float(a['zcoord']) - float(b['zcoord'])))
                U3k = (float(a['xcoord']) - float(b['xcoord'])) * (float(c['ycoord']) - float(b['ycoord'])) - (float(c['xcoord']) - float(b['xcoord'])) * (float(a['ycoord']) - float(b['ycoord']))
                easting = (float(a['xcoord']) + float(b['xcoord']) + float(c['xcoord'])) / 3
                northing = (float(a['ycoord']) + float(b['ycoord']) + float(c['ycoord'])) / 3
                elevation = (float(a['zcoord']) + float(b['zcoord']) + float(c['zcoord'])) / 3
                for k in range(0,3):
                    tabU1.append(U1i)
                    tabU2.append(U2j)
                    tabU3.append(U3k)
                    tabEst.append(easting)
                    tabNor.append(northing)
                    tabEle.append(elevation)


            
            j = 0
            layer.startEditing()
            for f in features:
                for i in range(0,3):
                    fid.append(j)
                id = f.id()
                
                #adding values to features
                attr_id = {tab_name["Id"]: id}
                attr_fid = {tab_name["FID"]: fid[j]}
                attr_value1 = {tab_name["U1"]:tabU1[j]}
                attr_value2 = {tab_name["-U2"]:tabU2[j]}
                attr_value3 = {tab_name["U3"]:tabU3[j]}
                attr_easting = {tab_name["easting"]:tabEst[j]}
                attr_northing = {tab_name["northing"]:tabNor[j]}
                attr_elevation = {tab_name["elevation"]:tabEle[j]}

                layer_provider.changeAttributeValues({id:attr_id})
                layer_provider.changeAttributeValues({id:attr_fid})
                layer_provider.changeAttributeValues({id:attr_value1})
                layer_provider.changeAttributeValues({id:attr_value2})
                layer_provider.changeAttributeValues({id:attr_value3})
                layer_provider.changeAttributeValues({id:attr_easting})
                layer_provider.changeAttributeValues({id:attr_northing})
                layer_provider.changeAttributeValues({id:attr_elevation})

                if tabU3[j] < 0:
                    attr_eastingFloat = {tab_name["eastingFlo"]:tabU2[j]}
                    attr_northingFloat = {tab_name["northingFl"]:-tabU1[j]}

                else:
                    attr_eastingFloat = {tab_name["eastingFlo"]:-tabU2[j]}
                    attr_northingFloat = {tab_name["northingFl"]:tabU1[j]}

                attrE.append(attr_eastingFloat[tab_name["eastingFlo"]])
                layer_provider.changeAttributeValues({id:attr_eastingFloat})

                attrN.append(attr_northingFloat[tab_name["northingFl"]])
                layer_provider.changeAttributeValues({id:attr_northingFloat})

                if attrE[j] >= 0:
                    attr_strikeFloat = {tab_name["strikeFloa"]: math.degrees(math.acos(attrN[j] / pow(((attrE[j] * attrE[j]) + (attrN[j] * attrN[j])), 0.5)))}

                else:
                    attr_strikeFloat = {tab_name["strikeFloa"]: math.degrees(2 * math.pi - math.acos(attrN[j] / pow(((attrE[j] * attrE[j]) + (attrN[j] * attrN[j])), 0.5)))}

                attrS.append(attr_strikeFloat[tab_name["strikeFloa"]])
                layer_provider.changeAttributeValues({id:attr_strikeFloat})

                attr_dipFloat = {tab_name["dipFloat"]: math.degrees(math.asin(pow((tabU1[j] * tabU1[j] + tabU2[j] * tabU2[j]), 0.5) / pow((tabU1[j] * tabU1[j] + tabU2[j] * tabU2[j] + tabU3[j] * tabU3[j]), 0.5)))}

                attrD.append(attr_dipFloat[tab_name["dipFloat"]])
                layer_provider.changeAttributeValues({id:attr_dipFloat})

                attr_strikeInt = {tab_name["strike"]: int(round(attrS[j]))}
                layer_provider.changeAttributeValues({id:attr_strikeInt})

                attr_dipDir = {tab_name["dipDir"]: attrS[j] + 90}
                layer_provider.changeAttributeValues({id:attr_dipDir})

                attr_dipInt = {tab_name["dip"]: int(round(attrD[j]))}
                layer_provider.changeAttributeValues({id:attr_dipInt})

                j = j + 1
            
            layer.commitChanges()

            #set a projection from raster layer to centroid layer
            crs_raster_layer = QgsRasterLayer(path_raster).crs().authid()
            
            layer2 = processing.run("qgis:createpointslayerfromtable",
                                        {'INPUT':self.dlg.lineEdit_2.text(),
                                            'XFIELD':'easting',
                                            'YFIELD':'northing',
                                            'TARGET_CRS':QgsCoordinateReferenceSystem(crs_raster_layer),
                                            'OUTPUT': 'TEMPORARY_OUTPUT'})
            layer2 = layer2['OUTPUT']
            layer2.setName('Layer with centroid')
        
            
            centroid_layer_data = layer2.dataProvider()
            for i in range(5,15):
                centroid_layer_data.deleteAttributes([5])
            layer2.updateFields()

            for i in range (15,18):
                layer_provider.deleteAttributes([15])
            layer.updateFields()


            QgsProject.instance().addMapLayer(layer)
            QgsProject.instance().addMapLayer(layer2)

     
            #adding a svg symbol of dip direction to output layer
            symbol = QgsMarkerSymbol()
            svgSymbol = {}
            svgSymbol['name'] = self.get_dir('symbol.svg')
            svgSymbol['size'] = '7'

            layer_symbol = QgsSvgMarkerSymbolLayer.create(svgSymbol)
            symbol.changeSymbolLayer(0, layer_symbol)
            symbol.setDataDefinedAngle(QgsProperty().fromField("dipDir"))
            layer.setRenderer(QgsSingleSymbolRenderer(symbol))

            layer_settings = QgsPalLayerSettings()
            text = QgsTextFormat()
            text.setFont(QFont("Tahoma"))
            text.setSize(7)
            layer_settings.setFormat(text)
            layer_settings.fieldName = "dip"
            layer_settings.placement = QgsPalLayerSettings.OverPoint
           
            layer_settings.xOffset = -2
            layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
            layer.setLabelsEnabled(True)
            layer.setLabeling(layer_settings)
            layer.triggerRepaint()
            
            #clear and close the dialog
            self.clear_dlg()
            self.dlg.close()