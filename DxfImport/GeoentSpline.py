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

import Core.Globals as g

from DxfImport.SplineConvert import Spline2Arcs
from Core.Point import Point
from DxfImport.Classes import PointsClass, ContourClass

import logging
logger = logging.getLogger("DxfImport.GeoentSpline")

class GeoentSpline:
    def __init__(self, Nr=0, caller=None):
        self.Typ = 'Spline'
        self.Nr = Nr

        #Initialisieren der Werte
        #Initialise the values
        self.Layer_Nr = 0
        self.Spline_flag = []
        self.degree = 1
        self.Knots = []
        self.Weights = []
        self.CPoints = []
        self.geo = []
        self.length = 0.0

        #Lesen der Geometrie
        #Read the geometry
        self.Read(caller)

        #Zuweisen der Toleranz f�rs Fitting
        #Assign the fitting tolerance
        tol = g.config.fitting_tolerance
        check = g.config.vars.Import_Parameters['spline_check']

        #Umwandeln zu einem ArcSpline
        #Convert to a ArcSpline
        Spline2ArcsClass = Spline2Arcs(degree=self.degree, Knots=self.Knots, \
                                Weights=self.Weights, CPoints=self.CPoints, tol=tol, check=check)


        self.geo = Spline2ArcsClass.Curve

        for geo in self.geo:
            self.length += geo.length

    def __str__(self):
        # how to print the object
        s = ('\nTyp: Spline') + \
           ('\nNr: %i' % self.Nr) + \
           ('\nLayer Nr: %i' % self.Layer_Nr) + \
           ('\nSpline flag: %i' % self.Spline_flag) + \
           ('\ndegree: %i' % self.degree) + \
           ('\nlength: %0.3f' % self.length) + \
           ('\nGeo elements: %i' % len(self.geo)) + \
           ('\nKnots: %s' % self.Knots) + \
           ('\nWeights: %s' % self.Weights) + \
           ('\nCPoints: ')

        for Point in self.CPoints:
            s = s + "\n" + str(Point)
        s += ('\ngeo: ')

        return s

    def reverse(self):
        """
        reverse()
        """
        self.geo.reverse()
        for geo in self.geo:
            geo.reverse()

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol, warning):
        """
        App_Cont_or_Calc_IntPts()
        """
        #Hinzuf�gen falls es keine geschlossener Spline ist
        #Add if it is not a closed spline
        if self.CPoints[0].within_tol(self.CPoints[-1], tol):
            self.analyse_and_opt()
            cont.append(ContourClass(len(cont), 1, [[i, 0]], self.length))
        else:
            points.append(PointsClass(point_nr=len(points), geo_nr=i, \
                                      Layer_Nr=self.Layer_Nr, \
                                      be=self.geo[0].Ps, \
                                      en=self.geo[-1].Pe, \
                                      be_cp=[], en_cp=[]))
        return warning

    def analyse_and_opt(self):
        """
        analyse_and_opt()
        """
        summe = 0

        #Richtung in welcher der Anfang liegen soll (unten links)
        #Direction of the top (lower left) ???
        Popt = Point(x= -1e3, y= -1e6)

        #Calculation of the alignment after Gaussian-Elling
        #Positive value means CW, negative value indicates CCW
        #closed polygon
        for Line in self.geo:
            summe += (Line.Ps.x * Line.Pe.y - Line.Pe.x * Line.Ps.y) / 2

        if summe > 0.0:
            self.reverse()

        #Find the smallest starting point from bottom left X (Must be new loop!)
        #logger.debug(self.geo)

        min_distance = self.geo[0].Ps.distance(Popt)
        min_geo_nr = 0
        for geo_nr in range(1, len(self.geo)):
            if (self.geo[geo_nr].Ps.distance(Popt) < min_distance):
                min_distance = self.geo[geo_nr].Ps.distance(Popt)
                min_geo_nr = geo_nr

        #Order contour so the new starting point is at the beginning
        self.geo = self.geo[min_geo_nr:len(self.geo)] + self.geo[0:min_geo_nr]

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

        #Spline Flap zuweisen
        #Assign Spline Flap
        s = lp.index_code(70, s + 1)
        self.Spline_flag = int(lp.line_pair[s].value)

        #Spline Ordnung zuweisen
        #Spline order to assign
        s = lp.index_code(71, s + 1)
        self.degree = int(lp.line_pair[s].value)

        #Number of CPts
        st = lp.index_code(73, s + 1)
        nCPts = int(lp.line_pair[s].value)

        s = st
        #Read the node (knot)
        while 1:
            #Node (knot) value
            sk = lp.index_code(40, s + 1, e)
            if sk == None:
                break
            self.Knots.append(float(lp.line_pair[sk].value))
            s = sk

        #Read the weights
        s = st
        while 1:
            #Node (knot) weights
            sg = lp.index_code(41, s + 1, e)
            if sg == None:
                break
            self.Weights.append(float(lp.line_pair[sg].value))
            s = sg

        #Read the control points
        s = st
        while 1:
            #X value
            s = lp.index_code(10, s + 1, e)
            #Wenn kein neuer Punkt mehr gefunden wurde abbrechen ...
            #Cancel if no new item was detected
            if s == None:
                break
            x = float(lp.line_pair[s].value)

            #Y value
            s = lp.index_code(20, s + 1, e)
            y = float(lp.line_pair[s].value)

            self.CPoints.append(Point(x, y))

        if len(self.Weights) == 0:
            for nr in range(len(self.CPoints)):
                self.Weights.append(1)


        caller.start = e
#        print nCPts
#        print len(self.Knots)
#        print len(self.Weights)
#        print len(self.CPoints)
#        print self


    def get_start_end_points(self, direction=0):
        """
        get_start_end_points()
        """
        if not(direction):
            punkt, angle = self.geo[0].get_start_end_points(direction)
        elif direction:
            punkt, angle = self.geo[-1].get_start_end_points(direction)

        return punkt, angle
