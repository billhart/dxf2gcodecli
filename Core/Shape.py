# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
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

from __future__ import absolute_import
from math import cos, sin, degrees, pi
import logging


import Core.Globals as g
from Core.Point import Point


logger = logging.getLogger("Core.Shape")


class ShapeClass():
    """
    The Shape Class includes all plotting, GUI functionality and export functions
    related to the Shapes.
    """
    def __init__(self, nr='None', closed=0,
                 cut_cor=40, length=0.0,
                 parent=None,
                 geos=[],
                 axis3_start_mill_depth=None, axis3_mill_depth=None,
                 axis3_slice_depth=None, f_g1_plane=None, f_g1_depth=None):
        """
        Standard method to initialize the class
        @param nr: The number of the shape. Starting from 0 for the first one
        @param closed: Gives information about the shape, when it is closed this
        value becomes 1
        @param cut_cor: Gives the selected Curring Correction of the shape
        (40=None, 41=Left, 42= Right)
        @param length: The total length of the shape including all geometries
        @param parent: The parent EntityContentClass of the shape
        @param geos: The list with all geometries included in the shape
        @param axis3_mill_depth: Optional parameter for the export of the shape.
        If this parameter is None the mill_depth of the parent layer will be used.
        """


        self.disabled = False
        self.allowedToChange = True
        self.send_to_TSP = g.config.vars.Route_Optimisation['default_TSP']
        self.type = "Shape"
        self.nr = nr
        self.closed = closed
        self.cut_cor = cut_cor
        self.length = length
        self.parent = parent
        self.stmove = []
        self.LayerContent = None
        self.geos = geos
        self.axis3_mill_depth = axis3_mill_depth
        self.axis3_start_mill_depth = axis3_start_mill_depth
        self.axis3_slice_depth = axis3_slice_depth
        self.f_g1_plane = f_g1_plane
        self.f_g1_depth = f_g1_depth
        self.selectionChangedCallback = None
        self.enableDisableCallback = None


    def contains_point(self, point):
        """
        Method to determine the minimal distance from the point to the shape
        @param point: a QPointF
        @return: minimal distance
        """
        min_distance = float(0x7fffffff)
        ref_point = Point(point.x(), point.y())
        t = 0.0
        while t < 1.0:
            per_point = self.path.pointAtPercent(t)
            spline_point = Point(per_point.x(), per_point.y())
            distance = ref_point.distance(spline_point)
            if distance < min_distance:
                min_distance = distance
            t += 0.01
        return min_distance

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\ntype:        %s" % self.type +\
               "\nnr:          %i" % self.nr +\
               "\nclosed:      %i" % self.closed +\
               "\ncut_cor:     %s" % self.cut_cor +\
               "\nlen(geos):   %i" % len(self.geos) +\
               "\ngeos:        %s" % self.geos +\
               "\nsend_to_TSP: %i" % self.send_to_TSP

 


    def boundingRect(self):
        """
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """
        return self.path.boundingRect()





    def setSelected(self, flag=True, blockSignals=False):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        self.starrow.setSelected(flag)
        self.enarrow.setSelected(flag)
        self.stmove.setSelected(flag)

        super(ShapeClass, self).setSelected(flag)

        if self.selectionChangedCallback and not blockSignals:
            self.selectionChangedCallback(self, flag)



    def isDisabled(self):
        """
        Returns the state of self.Disabled
        """
        return self.disabled

    def setToolPathOptimized(self, flag=False):
        """
        @param flag: The flag to enable or disable tool path optimisation for this shape
        """
        self.send_to_TSP = flag

    def isToolPathOptimized(self):
        """
        Returns the state of self.send_to_TSP
        """
        return self.send_to_TSP

    def AnalyseAndOptimize(self):
        """
        This method is called after the shape has been generated before it gets
        plotted to change all shape direction to a CW shape.
        """
        logger.debug(("Analysing the shape for CW direction Nr: %s") % self.nr)
        # Optimization for closed shapes
        if self.closed:
            # Start value for the first sum
            start = self.geos[0].get_start_end_points(0)[0]
            summe = 0.0
            for geo in self.geos:
                if geo.type == 'LineGeo':
                    ende = geo.get_start_end_points(1)[0]
                    summe += (start.x + ende.x) * (ende.y - start.y) / 2
                    start = ende
                elif geo.type == 'ArcGeo':
                    segments = int(abs(degrees(geo.ext)) // 90 + 1)
                    for i in range(segments):
                        ang = geo.s_ang + (i + 1) * geo.ext / segments
                        ende = Point(geo.O.x + cos(ang) * geo.r,
                                     geo.O.y + sin(ang) * geo.r)
                        summe += (start.x + ende.x) * (ende.y - start.y) / 2
                        start = ende

            if summe > 0.0:
                self.reverse()
                logger.debug(("Had to reverse the shape to be cw"))

    def FindNearestStPoint(self, StPoint=Point()):
        """
        Find Nearest Point to given StartPoint. This is used to change the
        start of closed contours
        @param StPoint: This is the point for which the nearest point shall
        be searched.
        """
        if self.closed:
            logger.debug(("Clicked Point: %s") % StPoint)
            start = self.geos[0].get_start_end_points(0, self.parent)[0]
            min_distance = start.distance(StPoint)

            logger.debug(("Old Start Point: %s") % start)

            min_geo_nr = 0
            for geo_nr in range(1, len(self.geos)):
                start = self.geos[geo_nr].get_start_end_points(0, self.parent)[0]

                if start.distance(StPoint) < min_distance:
                    min_distance = start.distance(StPoint)
                    min_geo_nr = geo_nr

            # Overwrite the geometries in changed order.
            self.geos = self.geos[min_geo_nr:] + self.geos[:min_geo_nr]

            start = self.geos[0].get_start_end_points(0, self.parent)[0]
            logger.debug(("New Start Point: %s") % start)

    def reverse(self):
        """
        Reverses the direction of the whole shape (switch direction).
        """
        self.geos.reverse()
        for geo in self.geos:
            geo.reverse()




    def get_st_en_points(self, dir=None):
        """
        Returns the start/end Point and its direction
        @param dir: direction - 0 to return start Point or 1 to return end Point
        @return: a list of Point and angle
        """
        start, start_ang = self.geos[0].get_start_end_points(0, self.parent)

        # max_slice = self.LayerContent.axis3_slice_depth if self.axis3_slice_depth is None else self.axis3_slice_depth
        # workpiece_top_Z = self.LayerContent.axis3_start_mill_depth if self.axis3_start_mill_depth is None else self.axis3_start_mill_depth
        # depth = self.LayerContent.axis3_mill_depth if self.axis3_mill_depth is None else self.axis3_mill_depth
        # max_slice = max(max_slice, depth - workpiece_top_Z)
        # if (workpiece_top_Z - depth)//max_slice % 2 == 0:
        #     end, end_ang = start, start_ang
        # else:
        end, end_ang = self.geos[-1].get_start_end_points(1, self.parent)

        if dir is None:
            return start, end
        elif dir == 0:
            return start, start_ang
        elif dir == 1:
            return end, end_ang

    def make_papath(self):
        """
        To be called if a Shape shall be printed to the canvas
        """
        start, start_ang = self.get_st_en_points()

        logger.debug(("Adding shape to Scene Nr: %i") % self.nr)

        for geo in self.geos:
            geo.add2path(papath=self.path, parent=self.parent, layerContent=self.LayerContent)





    def Write_GCode(self, LayerContent=None, PostPro=None):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape.
        @param LayerContent: This parameter includes the parent LayerContent
        which includes tool and additional cutting parameters.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """


        # initialisation of the string
        exstr = ""

        # Create the Start_moves once again if something was changed.
        #self.stmove.make_start_moves()


        # Move the tool to the start.
        start, start_ang = self.get_st_en_points(0)
        exstr += PostPro.rap_pos_xy(start)
        #exstr += self.stmove.geos[0].Write_GCode(parent=self.parent, PostPro=PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_pre_shape_cut()

        # Write the geometries for the first cut
        for geo in self.geos:
            exstr += geo.Write_GCode(self.parent, PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr


