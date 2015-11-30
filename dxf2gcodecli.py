#!/usr/bin/python
# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2010-2015
#    Christian Kohlöffel
#    Jean-Paul Schouwstra
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################


import os
import sys

from math import degrees, radians

import logging
logger = logging.getLogger()
from Core.Logger import LoggerClass

from copy import copy, deepcopy

import subprocess
import tempfile

import argparse


from Core.Config import MyConfig
from Core.Point import Point
from Core.LayerContent import LayerContentClass
from Core.EntityContent import EntityContentClass
import Core.Globals as g
import Core.constants as c
from Core.Shape import ShapeClass

from PostPro.PostProcessor import MyPostProcessor
from PostPro.Breaks import Breaks

from DxfImport.Import import ReadDXF


from PostPro.TspOptimisation import TSPoptimize

sys.setrecursionlimit(2500)

# Get folder of the main instance and write into globals
g.folder = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
if os.path.islink(sys.argv[0]):
    g.folder = os.path.dirname(os.readlink(sys.argv[0]))

# Create a class for our main window
class Main():
    """Main Class"""

    def __init__(self):
        """
        Initialization of the Main window. This is directly called after the
        Logger has been initialized. The Function loads the GUI, creates the
        used Classes and connects the actions to the GUI.
        """

        self.MyPostProcessor = MyPostProcessor()
        self.shapes = []
        self.LayerContents = []
        self.EntitiesRoot = []
        self.filename = ""


    def optimize_TSP(self):
        """
        Method is called to optimize the order of the shapes. This is performed
        by solving the TSP Problem.
        """

        logger.debug(('Optimize order of enabled shapes per layer'))

        #Get the export order from the QTreeView
        logger.debug(('Updating order according to TreeView'))

        for LayerContent in self.LayerContents:

            #Initial values for the Lists to export.
            self.shapes_to_write = []
            self.shapes_fixed_order = []
            shapes_st_en_points = []

            #Check all shapes of Layer which shall be exported and create List
            #for it.
            logger.debug(("Nr. of Shapes %s; Nr. of Shapes in Route %s")
                                 % (len(LayerContent.shapes),
                                 len(LayerContent.exp_order)))
            logger.debug(("Export Order for start: %s") % LayerContent.exp_order)

            for shape in self.shapes:
                self.shapes_to_write.append(shape.nr)
                shapes_st_en_points.append(shape.get_st_en_points())

            #Perform Export only if the Number of shapes to export is bigger than 0
            if len(self.shapes_to_write)>0:
                        #Errechnen der Iterationen
                        #Calculate the iterations
                iter_ = min(g.config.vars.Route_Optimisation['max_iterations'],
                         len(self.shapes_to_write)*50)

                #Adding the Start and End Points to the List.
                x_st = g.config.vars.Plane_Coordinates['axis1_start_end']
                y_st = g.config.vars.Plane_Coordinates['axis2_start_end']
                start = Point(x = x_st, y = y_st)
                ende = Point(x = x_st, y = y_st)
                shapes_st_en_points.append([start, ende])

                TSPs = []
                TSPs.append(TSPoptimize(st_end_points = shapes_st_en_points))
                logger.info(("TSP start values initialised for Layer %s")
                                    % LayerContent.LayerName)
                logger.debug(("Shapes to write: %s")
                                     % self.shapes_to_write)
                logger.debug(("Fixed order: %s")
                                     % self.shapes_fixed_order)

                for it_nr in range(iter_):
                    #Only show each 50th step.
                    if (it_nr % 50) == 0:
                        TSPs[-1].calc_next_iteration()
                        new_exp_order = []
                        for nr in TSPs[-1].opt_route[1:len(TSPs[-1].opt_route)]:
                            new_exp_order.append(nr)

                logger.debug(("TSP done with result: %s") % TSPs[-1])

                LayerContent.exp_order = new_exp_order

                logger.debug(("New Export Order after TSP: %s")
                                     % new_exp_order)
            else:
                LayerContent.exp_order = []





    def exportShapes(self, status=False, saveas=None):
        """
        This function is called by the menu "Export/Export Shapes". It may open
        a Save Dialog if used without LinuxCNC integration. Otherwise it's
        possible to select multiple postprocessor files, which are located
        in the folder.
        """

        logger.debug(('Export the enabled shapes'))

        #Get the export order from the QTreeView

        logger.debug(("Sorted layers:"))
        for i, layer in enumerate(self.LayerContents):
            logger.debug("LayerContents[%i] = %s" % (i, layer))

        if not(g.config.vars.General['write_to_stdout']):

            #Get the name of the File to export
            if saveas == None:
                self.save_filename = str(filename[0].toUtf8()).decode("utf-8")
            else:
                filename = [None, None]
                self.save_filename = saveas

            (beg, ende) = os.path.split(self.save_filename)
            (fileBaseName, fileExtension) = os.path.splitext(ende)

            pp_file_nr = 0
            for i in range(len(self.MyPostProcessor.output_format)):
                name = "%s " % (self.MyPostProcessor.output_text[i])
                format_ = "(*%s)" % (self.MyPostProcessor.output_format[i])
                MyFormats = name + format_
                if filename[1] == MyFormats:
                    pp_file_nr = i
            if fileExtension != self.MyPostProcessor.output_format[pp_file_nr]:
                self.save_filename = self.save_filename + self.MyPostProcessor.output_format[pp_file_nr]

            self.MyPostProcessor.getPostProVars(pp_file_nr)
        else:
            self.save_filename = None
            self.MyPostProcessor.getPostProVars(0)

        """
        Export will be performed according to LayerContents and their order
        is given in this variable too.
        """

        self.MyPostProcessor.exportShapes(self.load_filename,
                                          self.save_filename,
                                          self.LayerContents)

        if g.config.vars.General['write_to_stdout']:
            self.close()




    def loadFile(self, filename):
        """
        Loads the file given by filename.  Also calls the command to
        make the plot.
        @param filename: String containing filename which should be loaded
        """

        self.load_filename = filename
        (name, ext) = os.path.splitext(filename)

        if (ext.lower() == ".ps") or (ext.lower() == ".pdf"):
            logger.info(("Sending Postscript/PDF to pstoedit"))

            #Create temporary file which will be read by the program
            filename = os.path.join(tempfile.gettempdir(), 'dxf2gcode_temp.dxf')

            pstoedit_cmd = g.config.vars.Filters['pstoedit_cmd'] #"C:\Program Files (x86)\pstoedit\pstoedit.exe"
            pstoedit_opt = g.config.vars.Filters['pstoedit_opt'] #['-f','dxf','-mm']
            ps_filename = os.path.normcase(self.load_filename)
            cmd = [(('%s') % pstoedit_cmd)] + pstoedit_opt + [(('%s') % ps_filename), (('%s') % filename)]
            logger.debug(cmd)
            retcode = subprocess.call(cmd)

        #self.textbox.text.delete(7.0, END)
        logger.info(('Loading file: %s') % filename)
        #logger.info("<a href=file:%s>%s</a>" % (filename, filename))

        values = ReadDXF(filename)

        #Output the information in the text window
        logger.info(('Loaded layers: %s') % len(values.layers))
        logger.info(('Loaded blocks: %s') % len(values.blocks.Entities))
        for i in range(len(values.blocks.Entities)):
            layers = values.blocks.Entities[i].get_used_layers()
            logger.info(('Block %i includes %i Geometries, reduced to %i Contours, used layers: %s')\
                                     % (i, len(values.blocks.Entities[i].geo), len(values.blocks.Entities[i].cont), layers))
        layers = values.entities.get_used_layers()
        insert_nr = values.entities.get_insert_nr()
        logger.info(('Loaded %i Entities geometries, reduced to %i Contours, used layers: %s, Number of inserts: %i') \
                                 % (len(values.entities.geo), len(values.entities.cont), layers, insert_nr))


        self.makeShapesAndPlot(values)



    def makeShapesAndPlot(self, values):
        """
        Plots all data stored in the values parameter to the Canvas
        @param values: Includes all values loaded from the dxf file
        """

        #Generate the Shapes
        self.makeShapes(values,
                        p0 = Point(x = self.cont_dx, y = self.cont_dy),
                        pb = Point(x = 0.0, y = 0.0),
                        sca = [self.cont_scale, self.cont_scale, self.cont_scale],
                        rot = self.rotate)


        # Break insertion
 #       Breaks(self.LayerContents).process()




    def makeShapes(self, values, p0, pb, sca, rot):
        """
        Instance is called by the Main Window after the defined file is loaded.
        It generates all ploting functionality. The parameters are generally
        used to scale or offset the base geometry (by Menu in GUI).

        @param values: The loaded dxf values from the dxf_import.py file
        @param p0: The Starting Point to plot (Default x=0 and y=0)
        @param bp: The Base Point to insert the geometry and base for rotation
        (Default is also x=0 and y=0)
        @param sca: The scale of the basis function (default =1)
        @param rot: The rotation of the geometries around base (default =0)
        """
        self.values = values

        #Put back the contours
        del(self.shapes[:])
        del(self.LayerContents[:])
        del(self.EntitiesRoot)
        self.EntitiesRoot = EntityContentClass(Nr = 0, Name = 'Entities',
                                                parent = None, children = [],
                                                p0 = p0, pb = pb,
                                                sca = sca, rot = rot)

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        #Start with () means to assign the entities -1 = Default ???
        self.makeEntitiesShapes(parent = self.EntitiesRoot)
        self.LayerContents.sort()

    def makeEntitiesShapes(self, parent = None, ent_nr = -1, layerNr=-1):
        """
        Instance is called prior to plotting the shapes. It creates
        all shape classes which are later plotted into the graphics.

        @param parent: The parent of a shape is always an Entities. It may be root
        or, if it is a Block, this is the Block.
        @param ent_nr: The values given in self.values are sorted so
        that 0 is the Root Entities and 1 is beginning with the first block.
        This value gives the index of self.values to be used.
        """

        if parent.Name == "Entities":
            entities = self.values.entities
        else:
            ent_nr = self.values.Get_Block_Nr(parent.Name)
            entities = self.values.blocks.Entities[ent_nr]

        #Zuweisen der Geometrien in die Variable geos & Konturen in cont
        #Assigning the geometries in the variables geos & contours in cont
        ent_geos = entities.geo

        #Loop for the number of contours
        for cont in entities.cont:
            #Abfrage falls es sich bei der Kontur um ein Insert eines Blocks handelt
            #Query if it is in the contour of an insert of a block
            if ent_geos[cont.order[0][0]].Typ == "Insert":
                ent_geo = ent_geos[cont.order[0][0]]

                #Zuweisen des Basispunkts f�r den Block
                #Assign the base point for the block
                new_ent_nr = self.values.Get_Block_Nr(ent_geo.BlockName)
                new_entities = self.values.blocks.Entities[new_ent_nr]
                pb = new_entities.basep

                #Skalierung usw. des Blocks zuweisen
                #Scaling, etc. assign the block
                p0 = ent_geos[cont.order[0][0]].Point
                sca = ent_geos[cont.order[0][0]].Scale
                rot = ent_geos[cont.order[0][0]].rot


                #Erstellen des neuen Entitie Contents f�r das Insert
                #Creating the new Entitie Contents for the insert
                NewEntitieContent = EntityContentClass(Nr = 0,
                                        Name = ent_geo.BlockName,
                                        parent = parent, children = [],
                                        p0 = p0,
                                        pb = pb,
                                        sca = sca,
                                        rot = rot)

                parent.addchild(NewEntitieContent)

                self.makeEntitiesShapes(parent = NewEntitieContent,
                                        ent_nr = ent_nr,
                                        layerNr = ent_geo.Layer_Nr)

            else:
                self.shapes.append(ShapeClass(len(self.shapes),
                                              cont.closed,
                                              40,
                                              0.0,
                                              parent,
                                              []))

                #Loop for the number of geometries
                for ent_geo_nr in range(len(cont.order)):
                    ent_geo = ent_geos[cont.order[ent_geo_nr][0]]
                    if cont.order[ent_geo_nr][1]:
                        ent_geo.geo.reverse()
                        for geo in ent_geo.geo:
                            geo = copy(geo)
                            geo.reverse()
                            self.appendshapes(geo)
                        ent_geo.geo.reverse()
                    else:
                        for geo in ent_geo.geo:
                            self.appendshapes(copy(geo))

                #All shapes have to be CW direction.
                self.shapes[-1].AnalyseAndOptimize()
                self.shapes[-1].FindNearestStPoint()

                self.addtoLayerContents(self.shapes[-1], layerNr if layerNr != -1 else ent_geo.Layer_Nr)
                parent.addchild(self.shapes[-1])

    def appendshapes(self, geo):
        """
        Documentation required
        """
        self.shapes[-1].geos.append(geo)

        if g.config.machine_type == 'drag_knife' and geo.type == 'HoleGeo':
            self.shapes[-1].disabled = True
            self.shapes[-1].allowedToChange = False

    def addtoLayerContents(self, shape, lay_nr):
        """
        Instance is called while the shapes are created. This gives the
        structure which shape is laying on which layer. It also writes into the
        shape the reference to the LayerContent Class.

        @param shape: The shape to be appended of the shape
        @param lay_nr: The Nr. of the layer
        """

        #Check if the layer already exists and add shape if it is.
        for LayCon in self.LayerContents:
            if LayCon.LayerNr == lay_nr:
                LayCon.shapes.append(shape)
                return

        #If the Layer does not exist create a new one.
        LayerName = self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr, LayerName, [shape]))



    def closeEvent(self, e):
        logger.debug(("exiting"))
        self.writeSettings()
        e.accept()


if __name__ == "__main__":
    """
    The main function which is executed after program start.
    """
    Log=LoggerClass(logger)
    #Get local language and install if available.

    g.config = MyConfig()

    Log.set_console_handler_loglevel()
    Log.add_file_logger()

    window = Main()
    g.window = window


    parser = argparse.ArgumentParser()
    parser.add_argument("filename",nargs="?")

#    parser.add_argument("-f", "--file", dest = "filename",
#                      help = "read data from FILENAME")
    parser.add_argument("-e", "--export", dest = "export_filename",
                      help = "export data to FILENAME")
    parser.add_argument("-q", "--quiet", action = "store_true",
                      dest = "quiet", help = "no GUI")

#    parser.add_option("-v", "--verbose",
#                      action = "store_true", dest = "verbose")
    options = parser.parse_args()

    #(options, args) = parser.parse_args()
    logger.debug("Started with following options \n%s" % (parser))


    if not(options.filename is None):
        window.filename = options.filename.decode("cp1252")
        #Initialize the scale, rotate and move coordinates
        window.cont_scale = 1.0
        window.cont_dx = 0.0
        window.cont_dy = 0.0
        window.rotate = 0.0

        window.loadFile(window.filename)

    if not(options.export_filename is None):
        window.optimize_TSP()
        window.exportShapes(None, options.export_filename)

