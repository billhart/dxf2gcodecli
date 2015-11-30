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

#from Canvas import Oval, Arc, Line
from math import sin, cos, pi, ceil
from Core.LineGeo import LineGeo
from Core.ArcGeo import ArcGeo
from Core.Point import Point

class BiarcClass:
    """
    BiarcClass Class for the generation of Biarc Section. It is used for the
    Ellipse fitting and the Nurbs conversion to Line and Arc segments.
    """
    def __init__(self, Ps=Point(), tan_a=0.0,
                  Pb=Point, tan_b=0.0, min_r=1e-6):
        """
        Std. method to initialise the class.
        @param Ps: Start Point for the Biarc
        @param tan_a: Tangent of the Start Point
        @param Pb: End Point of the Biarc
        @param tan_b: Tangent of the End Point
        @param min_r: The minimum radius of a arc section.
        """
        min_len = 1e-12       #Min Abstand f�r doppelten Punkt / Minimum clearance for double point
        min_alpha = 1e-4      #Winkel ab welchem Gerade angenommen wird inr rad / Angle for which it is assumed straight inr rad
        max_r = 5e3           #Max Radius ab welchem Gerade angenommen wird (5m) / Max radius is assumed from which line (5m)
        min_r = min_r         #Min Radius ab welchem nichts gemacht wird / Min radius beyond which nothing is done

        self.Ps = Ps
        self.tan_a = tan_a
        self.Pb = Pb
        self.tan_b = tan_b
        self.l = 0.0
        self.shape = None
        self.geos = []
        self.k = 0.0

        #Errechnen der Winkel, L�nge und Shape
        #Calculate the angle, length and shape
        norm_angle, self.l = self.calc_normal(self.Ps, self.Pb)

        alpha, beta, self.teta, self.shape = self.calc_diff_angles(norm_angle, \
                                                              self.tan_a, \
                                                              self.tan_b, \
                                                              min_alpha)

        if(self.l < min_len):
            self.shape = "Zero"

        elif(self.shape == "LineGeo"):
            #Erstellen der Geometrie
            #Create the geometry
            self.shape = "LineGeo"
            self.geos.append(LineGeo(self.Ps, self.Pb))
        else:
            #Berechnen der Radien, Mittelpunkte, Zwichenpunkt
            #Calculate the radii, midpoints Zwichenpunkt
            r1, r2 = self.calc_r1_r2(self.l, alpha, beta, self.teta)

            if (abs(r1) > max_r)or(abs(r2) > max_r):
                #Erstellen der Geometrie
                #Create the geometry
                self.shape = "LineGeo"
                self.geos.append(LineGeo(self.Ps, self.Pb))
                return

            elif (abs(r1) < min_r)or(abs(r2) < min_r):
                self.shape = "Zero"
                return

            O1, O2, k = self.calc_O1_O2_k(r1, r2, self.tan_a, self.teta)

            #Berechnen der Start und End- Angles f�r das drucken
            #Calculate the start and end angles for the print
            s_ang1, e_ang1 = self.calc_s_e_ang(self.Ps, O1, k)
            s_ang2, e_ang2 = self.calc_s_e_ang(k, O2, self.Pb)

            #Berechnen der Richtung und der Extend
            #Calculate the direction and extent
            dir_ang1 = (tan_a - s_ang1) % (-2 * pi)
            dir_ang1 -= ceil(dir_ang1 / (pi)) * (2 * pi)

            dir_ang2 = (tan_b - e_ang2) % (-2 * pi)
            dir_ang2 -= ceil(dir_ang2 / (pi)) * (2 * pi)


            #Erstellen der Geometrien
            #Create the geometries
            self.geos.append(ArcGeo(Ps=self.Ps, Pe=k, O=O1, r=r1, \
                                    s_ang=s_ang1, e_ang=e_ang1, direction=dir_ang1))
            self.geos.append(ArcGeo(Ps=k, Pe=self.Pb, O=O2, r=r2, \
                                    s_ang=s_ang2, e_ang=e_ang2, direction=dir_ang2))

    def calc_O1_O2_k(self, r1, r2, tan_a, teta):
        """
        calc_O1_O2_k()
        """
        #print("r1: %0.3f, r2: %0.3f, tan_a: %0.3f, teta: %0.3f" %(r1,r2,tan_a,teta))
        #print("N1: x: %0.3f, y: %0.3f" %(-sin(tan_a), cos(tan_a)))
        #print("V: x: %0.3f, y: %0.3f" %(-sin(teta+tan_a),cos(teta+tan_a)))

        O1 = Point(x=self.Ps.x - r1 * sin(tan_a), \
                      y=self.Ps.y + r1 * cos(tan_a))
        k = Point(x=self.Ps.x + r1 * (-sin(tan_a) + sin(teta + tan_a)), \
                     y=self.Ps.y + r1 * (cos(tan_a) - cos(tan_a + teta)))
        O2 = Point(x=k.x + r2 * (-sin(teta + tan_a)), \
                      y=k.y + r2 * (cos(teta + tan_a)))
        return O1, O2, k

    def calc_normal(self, Ps, Pb):
        """
        calc_normal()
        """
        norm_angle = Ps.norm_angle(Pb)
        l = Ps.distance(Pb)
        return norm_angle, l

    def calc_diff_angles(self, norm_angle, tan_a, tan_b, min_alpha):
        """
        calc_diff_angles()
        """
        #print("Norm angle: %0.3f, tan_a: %0.3f, tan_b %0.3f" %(norm_angle,tan_a,tan_b))
        alpha = (norm_angle - tan_a)
        beta = (tan_b - norm_angle)
        alpha, beta = self.limit_angles(alpha, beta)

        if alpha * beta > 0.0:
            shape = "C-shaped"
            teta = alpha
        elif abs(alpha - beta) < min_alpha:
            shape = "LineGeo"
            teta = alpha
        else:
            shape = "S-shaped"
            teta = (3 * alpha - beta) / 2

        return alpha, beta, teta, shape

    def limit_angles(self, alpha, beta):
        """
        limit_angles()
        """
        #print("limit_angles: alpha: %s, beta: %s" %(alpha,beta))
        if (alpha < -pi):
            alpha += 2 * pi
        if (alpha > pi):
            alpha -= 2 * pi
        if (beta < -pi):
            beta += 2 * pi
        if (beta > pi):
            beta -= 2 * pi
        while (alpha - beta) > pi:
            alpha = alpha - 2 * pi
        while (alpha - beta) < -pi:
            alpha = alpha + 2 * pi
        #print("   -->>       alpha: %s, beta: %s" %(alpha,beta))
        return alpha, beta

    def calc_r1_r2(self, l, alpha, beta, teta):
        """
        calc_r1_r2()
        """
        #print("alpha: %s, beta: %s, teta: %s" %(alpha,beta,teta))
        r1 = (l / (2 * sin((alpha + beta) / 2)) *
              sin((beta - alpha + teta) / 2) / sin(teta / 2))
        r2 = (l / (2 * sin((alpha + beta) / 2)) *
              sin((2 * alpha - teta) / 2) / sin((alpha + beta - teta) / 2))
        return r1, r2

    def calc_s_e_ang(self, P1, O, P2):
        """
        calc_s_e_ang()
        """
        s_ang = O.norm_angle(P1)
        e_ang = O.norm_angle(P2)
        return s_ang, e_ang

    def get_biarc_fitting_error(self, Pt):
        """
        get_biarc_fitting_error()
        """
        #Query in which segment of the circle the point is:
        w1 = self.geos[0].O.norm_angle(Pt)
        if (w1 >= min([self.geos[0].s_ang, self.geos[0].e_ang]))and\
           (w1 <= max([self.geos[0].s_ang, self.geos[0].e_ang])):
            diff = abs(self.geos[0].O.distance(Pt) - abs(self.geos[0].r))  # swapped 1 for 0
        else:
            diff = abs(self.geos[1].O.distance(Pt) - abs(self.geos[1].r))  # swapped 0 for 1
        # diff1 = abs(self.geos[0].O.distance(Pt) - abs(self.geos[0].r))
        # diff2 = abs(self.geos[1].O.distance(Pt) - abs(self.geos[1].r))
        # if diff != min(diff1,diff2):
        #     print "different ",diff,diff1,diff2
        return abs(diff)

    def __str__(self):
        s = ("\nBiarc Shape: %s" % (self.shape)) + \
           ("\nPs : %s; Tangent: %0.3f" % (self.Ps, self.tan_a)) + \
           ("\nPb : %s; Tangent: %0.3f" % (self.Pb, self.tan_b)) + \
           ("\nteta: %0.3f, l: %0.3f" % (self.teta, self.l))
        for geo in self.geos:
            s += str(geo)
        return s
