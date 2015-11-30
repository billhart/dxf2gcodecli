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

from Core.Point import Point
from DxfImport.Classes import PointsClass, ContourClass
from Core.ArcGeo import ArcGeo
from Core.LineGeo import LineGeo


class GeoentLwPolyline:
    def __init__(self, Nr=0, caller=None):
        self.Typ = 'LWPolyline'
        self.Nr = Nr
        self.Layer_Nr = 0
        self.length = 0
        self.geo = []

        #Lesen der Geometrie
        #Read the geometry
        self.Read(caller)

    def __str__(self):
        # how to print the object
        string = ("\nTyp: LWPolyline") + \
               ("\nNr: %i" % self.Nr) + \
               ("\nLayer Nr: %i" % self.Layer_Nr) + \
               ("\nNr. of geos: %i" % len(self.geo)) + \
               ("\nlength: %0.3f" % self.length)

        return string

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
        if abs(self.length) < tol:
            pass

        #Add if it is not a closed polyline
        elif  self.geo[0].Ps.within_tol(self.geo[-1].Pe, tol):
            self.analyse_and_opt()
            cont.append(ContourClass(len(cont), 1, [[i, 0]], self.length))
        else:
            points.append(PointsClass(point_nr=len(points), geo_nr=i, \
                                      Layer_Nr=self.Layer_Nr, \
                                      be=self.geo[0].Ps,
                                      en=self.geo[-1].Pe, be_cp=[], en_cp=[]))
        return warning

    def analyse_and_opt(self):
        """
        analyse_and_opt()
        """
        summe = 0

        #Richtung in welcher der Anfang liegen soll (unten links)
        #Direction of the top (lower left) ????
        Popt = Point(x= -1e3, y= -1e6)

        #Calculation of the alignment after Gaussian-Elling
        #Positive value means CW, negative value indicates CCW
        #closed polygon
        for Line in self.geo:
            summe += (Line.Ps.x * Line.Pe.y - Line.Pe.x * Line.Ps.y) / 2

        if summe > 0.0:
            self.reverse()

        #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
        #Find the smallest starting point from bottom left X (Must be new loop!)
        min_distance = self.geo[0].Ps.distance(Popt)
        min_geo_nr = 0
        for geo_nr in range(1, len(self.geo)):
            if (self.geo[geo_nr].Ps.distance(Popt) < min_distance):
                min_distance = self.geo[geo_nr].Ps.distance(Popt)
                min_geo_nr = geo_nr

        #Kontur so anordnen das neuer Startpunkt am Anfang liegt
        #Order Contour so new starting point is at the beginning
        self.geo = self.geo[min_geo_nr:len(self.geo)] + self.geo[0:min_geo_nr]


    def Read(self, caller):
        """
        Read()
        """
        Old_Point = Point(0, 0)

        #Assign short name
        lp = caller.line_pairs
        e = lp.index_code(0, caller.start + 1)

        #Assign layer
        s = lp.index_code(8, caller.start + 1)
        self.Layer_Nr = caller.Get_Layer_Nr(lp.line_pair[s].value)

        #Ps=None for the first point
        Ps = None

        #Number of vertices
        s = lp.index_code(90, s + 1, e)
        NoOfVert = int(lp.line_pair[s].value)

        #Polyline flag (bit-coded); default is 0; 1 = Closed; 128 = Plinegen
        s = lp.index_code(70, s + 1, e)
        LWPLClosed = int(lp.line_pair[s].value)
        #print LWPLClosed

        s = lp.index_code(10, s + 1, e)
        while 1:
            #X Value
            if s == None:
                break
            x = float(lp.line_pair[s].value)

            #Y Value
            s = lp.index_code(20, s + 1, e)
            y = float(lp.line_pair[s].value)
            Pe = Point(x=x, y=y)

            #Bulge
            bulge = 0

            s_nxt_x = lp.index_code(10, s + 1, e)
            e_nxt_b = s_nxt_x

            #Wenn am Ende dann Suche bis zum Ende
            #If in the end the search until the end ???
            if e_nxt_b == None:
                e_nxt_b = e

            s_bulge = lp.index_code(42, s + 1, e_nxt_b)

            #print('stemp: %s, e: %s, next 10: %s' %(s_temp,e,lp.index_code(10,s+1,e)))
            if s_bulge != None:
                bulge = float(lp.line_pair[s_bulge].value)
                s_nxt_x = s_nxt_x

            #Take the next X value as the starting value
            s = s_nxt_x

            #Assign the geometries for the Polyline
            if not(type(Ps) == type(None)):
                if next_bulge == 0:
                    self.geo.append(LineGeo(Ps=Ps, Pe=Pe))
                else:
                    #self.geo.append(LineGeo(Ps=Ps,Pe=Pe))
                    #print bulge
                    self.geo.append(self.bulge2arc(Ps, Pe, next_bulge))

                #L�nge drauf rechnen wenns eine Geometrie ist
                #Wenns Ldnge count on it is a geometry ???
                self.length += self.geo[-1].length

            #The bulge is always given for the next point
            next_bulge = bulge
            Ps = Pe


        if (LWPLClosed == 1)or(LWPLClosed == 129):
            #print("sollten �bereinstimmen: %s, %s" %(Ps,Pe))
            if next_bulge:
                self.geo.append(self.bulge2arc(Ps, self.geo[0].Ps, next_bulge))
            else:
                self.geo.append(LineGeo(Ps=Ps, Pe=self.geo[0].Ps))

            self.length += self.geo[-1].length

        #New starting value for the next geometry
        caller.start = e

    def get_start_end_points(self, direction=0):
        if not(direction):
            punkt, angle = self.geo[0].get_start_end_points(direction)
        elif direction:
            punkt, angle = self.geo[-1].get_start_end_points(direction)
        return punkt, angle

    def bulge2arc(self, Ps, Pe, bulge):
        """
        bulge2arc()
        """
        c = (1 / bulge - bulge) / 2

        #Calculate the centre point (Micke's formula!)
        O = Point(x=(Ps.x + Pe.x - (Pe.y - Ps.y) * c) / 2, \
                  y=(Ps.y + Pe.y + (Pe.x - Ps.x) * c) / 2)

        #Radius = Distance between the centre and Ps
        r = O.distance(Ps)

        #Check if they are equal (fits ...)
        #r=O.distance(Pe)

        #Unterscheidung f�r den �ffnungswinkel.
        #Distinction for the opening angle. ???
        if bulge > 0:
            return ArcGeo(Ps=Ps, Pe=Pe, O=O, r=r)
        else:
            arc = ArcGeo(Ps=Pe, Pe=Ps, O=O, r=r)
            arc.reverse()
            return arc
