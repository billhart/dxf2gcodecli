# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2014
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



from Core.Point import Point
from DxfImport.Classes import PointsClass
from Core.LineGeo import  LineGeo

import logging
logger = logging.getLogger("DXFImport.GeoentLine")

class GeoentLine:
    def __init__(self, Nr=0, caller=None):
        self.Typ = 'Line'
        self.Nr = Nr
        self.Layer_Nr = 0
        self.geo = []
        self.length = 0

        #Lesen der Geometrie
        #Read the geometry
        self.Read(caller)

    def __str__(self):
        # how to print the object
        return("\nTyp: Line") + \
              ("\nNr: %i" % self.Nr) + \
              ("\nLayer Nr: %i" % self.Layer_Nr) + \
              str(self.geo[-1])


    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("ReadDXF",
                                                    string_to_translate,
                                                    None,
                                                    QtGui.QApplication.UnicodeUTF8))


    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol, warning):
        """
        App_Cont_or_Calc_IntPts()
        """
        if abs(self.length) > tol:
            points.append(PointsClass(point_nr=len(points), geo_nr=i,
                                      Layer_Nr=self.Layer_Nr,
                                      be=self.geo[-1].Ps,
                                      en=self.geo[-1].Pe, be_cp=[], en_cp=[]))
        else:
#            showwarning("Short Arc Elemente", ("Length of Line geometry too short!"\
#                                               "\nLength must be greater than tolerance."\
#                                               "\nSkipping Line Geometry"))
            warning = 1
        return warning

    def Read(self, caller):
        """
        This function does read the geometry.
        @param caller: The instance which is calling the function
        """
        #Assign short name
        lp = caller.line_pairs
        e = lp.index_code(0, caller.start + 1)

        #Assign layer
        s = lp.index_code(8, caller.start + 1)
        self.Layer_Nr = caller.Get_Layer_Nr(lp.line_pair[s].value)

        #X Value
        sl = lp.index_code(10, s + 1)
        x0 = float(lp.line_pair[sl].value)

        #Y Value
        s = lp.index_code(20, sl + 1)
        y0 = float(lp.line_pair[s].value)

        #X Value 2
        s = lp.index_code(11, sl + 1)
        x1 = float(lp.line_pair[s].value)

        #Y Value 2
        s = lp.index_code(21, s + 1)
        y1 = float(lp.line_pair[s].value)

        #Searching for an extrusion direction
        s_nxt_xt = lp.index_code(230, s + 1, e)
        #If there is a extrusion direction given flip around x-Axis
        if s_nxt_xt != None:
            extrusion_dir = float(lp.line_pair[s_nxt_xt].value)
            logger.debug(self.tr('Found extrusion direction: %s') %extrusion_dir)
            if extrusion_dir == -1:
                x0 = -x0
                x1 = -x1

        Ps = Point(x0, y0)
        Pe = Point(x1, y1)

        #Anhängen der LineGeo Klasse für die Geometrie
        #Annexes to LineGeo class for geometry ???
        self.geo.append(LineGeo(Ps=Ps, Pe=Pe))

        #Länge entspricht der Länge des Kreises
        #Length corresponding to the length (circumference?) of the circle
        self.length = self.geo[-1].length

        #Neuen Startwert für die nächste Geometrie zurückgeben
        #New starting value for the next geometry
        caller.start = s

    def get_start_end_points(self, direction):
        """
        get_start_end_points()
        """
        punkt, angle = self.geo[-1].get_start_end_points(direction)
        return punkt, angle


