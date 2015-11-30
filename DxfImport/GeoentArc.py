# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
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

from math import  sin, cos, radians, pi


from Core.Point import Point
from DxfImport.Classes import PointsClass
from Core.ArcGeo import  ArcGeo

import logging
logger = logging.getLogger("DXFImport.GeoentArc")


class GeoentArc():
    def __init__(self, Nr=0, caller=None):
        self.Typ = 'Arc'
        self.Nr = Nr
        self.Layer_Nr = 0
        self.length = 0
        self.geo = []

        #Lesen der Geometrie
        #Read the geometry
        self.Read(caller)

    def __str__(self):
        # how to print the object
        return("\nTyp: Arc ") + \
              ("\nNr: %i" % self.Nr) + \
              ("\nLayer Nr:%i" % self.Layer_Nr) + \
              str(self.geo[-1])

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol, warning):
        """
        App_Cont_or_Calc_IntPts()
        """
        if abs(self.length) > tol:
            points.append(PointsClass(point_nr=len(points),
                          geo_nr=i,
                          Layer_Nr=self.Layer_Nr,
                          be=self.geo[-1].Ps,
                          en=self.geo[-1].Pe,
                          be_cp=[], en_cp=[]))
        else:
            warning = 1
        return warning

    def Read(self, caller):
        """
        Read()
        """
        #Assign short name
        lp = caller.line_pairs
        e = lp.index_code(0, caller.start + 1)

        #Assign layer
        s = lp.index_code(8, caller.start + 1)
        self.Layer_Nr = caller.Get_Layer_Nr(lp.line_pair[s].value)

        #X Value
        s = lp.index_code(10, s + 1)
        x0 = float(lp.line_pair[s].value)

        #Y Value
        s = lp.index_code(20, s + 1)
        y0 = float(lp.line_pair[s].value)
        O = Point(x0, y0)

        #Radius
        s = lp.index_code(40, s + 1)
        r = float(lp.line_pair[s].value)

        #Start angle
        s = lp.index_code(50, s + 1)
        s_ang = radians(float(lp.line_pair[s].value))

        #End angle
        s = lp.index_code(51, s + 1)
        e_ang = radians(float(lp.line_pair[s].value))

        #Searching for an extrusion direction
        s_nxt_xt = lp.index_code(230, s + 1, e)
        #If there is a extrusion direction given flip around x-Axis
        if s_nxt_xt != None:
            extrusion_dir = float(lp.line_pair[s_nxt_xt].value)
            logger.debug(('Found extrusion direction: %s')
                                 % extrusion_dir)
            if extrusion_dir == -1:
                x0 = -x0
                s_ang = s_ang + pi
                e_ang = e_ang + pi

        #Calculate the start and end points of the arcs
        Ps = Point(x=cos(s_ang) * r, y=sin(s_ang) * r) + O
        Pe = Point(x=cos(e_ang) * r, y=sin(e_ang) * r) + O

        #Anh�ngen der ArcGeo Klasse f�r die Geometrie
        #Annexes to ArcGeo class for geometry
        self.geo.append(ArcGeo(Ps=Ps, Pe=Pe, O=O, r=r,
                                s_ang=s_ang, e_ang=e_ang, direction=1))

        #L�nge entspricht der L�nge des Kreises
        #Length is the length (circumference?) of the circle
        self.length = self.geo[-1].length

#        logger.debug(self.geo[-1])

        #Neuen Startwerd f�r die n�chste Geometrie zur�ckgeben
        #New starting value for the next geometry
        caller.start = s

    def get_start_end_points(self, direction):
        """
        get_start_end_points()
        """
        punkt, angle = self.geo[-1].get_start_end_points(direction)
        return punkt, angle


