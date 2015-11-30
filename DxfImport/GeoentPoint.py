# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2014-2014
#    Robert Lichtenberger
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



from Core.HoleGeo import  HoleGeo
from Core.LineGeo import  LineGeo
from Core.Point import Point
from DxfImport.Classes import ContourClass

import logging
logger = logging.getLogger("DXFImport.GeoentPoint")

class GeoentPoint:
    def __init__(self, Nr=0, caller=None):
        self.Typ = 'Point'
        self.Nr = Nr
        self.Layer_Nr = 0
        self.geo = []
        self.length = 0;

        #Lesen der Geometrie
        #Read the geometry
        self.Read(caller)

    def __str__(self):
        # how to print the object
        return("\nTyp: Point") + \
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
        cont.append(ContourClass(len(cont), 0, [[i, 0]], 0))
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

        Ps = Point(x0, y0)

        self.geo.append(HoleGeo(Ps))
        #self.geo.append(LineGeo(Ps=Point(0,0), Pe=P))

        #Neuen Startwert für die nächste Geometrie zurückgeben
        #New starting value for the next geometry
        caller.start = s

