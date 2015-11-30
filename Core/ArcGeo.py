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
from math import sqrt, sin, cos, degrees, pi, floor, ceil
import logging
import copy

from Core.Point import Point
import Core.Globals as g


logger = logging.getLogger("Core.ArcGeo")


class ArcGeo():
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """
    def __init__(self, Ps=None, Pe=None, O=None, r=1,
                 s_ang=None, e_ang=None, direction=1, drag=False):
        """
        Standard Method to initialize the ArcGeo. Not all of the parameters are
        required to fully define a arc. e.g. Ps and Pe may be given or s_ang and
        e_ang
        @param Ps: The Start Point of the arc
        @param Pe: the End Point of the arc
        @param O: The center of the arc
        @param r: The radius of the arc
        @param s_ang: The Start Angle of the arc
        @param e_ang: the End Angle of the arc
        @param direction: The arc direction where 1 is in positive direction
        """
        self.type = "ArcGeo"
        self.Ps = Ps
        self.Pe = Pe
        self.O = O
        self.r = abs(r)
        self.s_ang = s_ang
        self.e_ang = e_ang
        self.drag = drag

        # Get the Circle center point with known Start and End Points
        if self.O is None:

            if self.Ps is not None and\
               self.Pe is not None and\
               direction is not None:

                arc = self.Pe.norm_angle(self.Ps) - pi / 2
                m = self.Pe.distance(self.Ps) / 2

                logger.debug('lo: %s; m: %s' % (self.r, m))

                if abs(self.r - m) < g.config.fitting_tolerance:
                    lo = 0.0
                else:
                    lo = sqrt(pow(self.r, 2) - pow(m, 2))

                d = -1 if direction < 0 else 1

                self.O = self.Ps + (self.Pe - self.Ps) / 2
                self.O.y += lo * sin(arc) * d
                self.O.x += lo * cos(arc) * d

            # Falls nicht übergeben Mittelpunkt ausrechnen
            # Compute centre...
            elif self.s_ang is not None and self.e_ang is not None:
                self.O.x = self.Ps.x - self.r * cos(self.s_ang)
                self.O.y = self.Ps.y - self.r * sin(self.s_ang)
            else:
                logger.error(("Missing value for Arc Geometry"))

        # Falls nicht übergeben dann Anfangs- und Endwinkel ausrechen
        # Calculate start and end angles
        if self.s_ang is None:
            self.s_ang = self.O.norm_angle(Ps)
        if self.e_ang is None:
            self.e_ang = self.O.norm_angle(Pe)

        self.ext = self.dif_ang(self.Ps, self.Pe, direction)

        self.length = self.r * abs(self.ext)

    def __deepcopy__(self, memo):
        return ArcGeo(copy.deepcopy(self.Ps, memo),
                      copy.deepcopy(self.Pe, memo),
                      copy.deepcopy(self.O, memo),
                      copy.deepcopy(self.r, memo),
                      copy.deepcopy(self.s_ang, memo),
                      copy.deepcopy(self.e_ang, memo),
                      copy.deepcopy(self.ext, memo))

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nArcGeo" +\
               "\nPs:  %s; s_ang: %0.5f" % (self.Ps, self.s_ang) +\
               "\nPe:  %s; e_ang: %0.5f" % (self.Pe, self.e_ang) +\
               "\nO:   %s; r: %0.3f" % (self.O, self.r) +\
               "\next: %0.5f; length: %0.5f" % (self.ext, self.length)

    def toShortString(self):
        """
        Method to print only start and end point of the arc
        @return: A string
        """
        return ("(%f, %f) -> (%f, %f)" % (self.Ps.x, self.Ps.y, self.Pe.x, self.Pe.y));


    def dif_ang(self, Ps, Pe, direction):
        """
        Calculated the angle between Pe and Ps with respect to the origin
        @param Ps: the start Point of the arc
        @param Pe: the end Point of the arc
        @param direction: the direction of the arc
        @return: Returns the angle between -2* pi and 2 *pi for the arc,
        0 excluded - we got a complete circle
        """
        dif_ang = (self.O.norm_angle(Pe) - self.O.norm_angle(Ps)) % (-2 * pi)

        if direction > 0:
            dif_ang += 2 * pi
        elif dif_ang == 0:
            dif_ang = -2 * pi

        return dif_ang

    def reverse(self):
        """
        Reverses the direction of the arc (switch direction).
        """
        self.Ps, self.Pe = self.Pe, self.Ps
        self.s_ang, self.e_ang = self.e_ang, self.s_ang
        self.ext = -self.ext

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself self and the parent.
        @param parent: The parent of the geometry (EntityContentClass)
        @return: A new ArcGeoClass will be returned.
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)
        O = self.O.rot_sca_abs(parent=parent)
        r = self.scaled_r(self.r, parent)

        direction = 1 if self.ext > 0.0 else -1

        if parent is not None and parent.sca[0] * parent.sca[1] < 0.0:
            direction *= -1

        return ArcGeo(Ps=Ps, Pe=Pe, O=O, r=r, direction=direction)

    def scaled_r(self, r, parent):
        """
        Scales the radius based on the scale given in its parents. This is done
        recursively.
        @param r: The radius which shall be scaled
        @param parent: The parent Entity (Instance: EntityContentClass)
        @return: The scaled radius
        """
        # Rekursive Schleife falls mehrfach verschachtelt.
        # Recursive loop if nested.
        if parent is not None:
            r *= parent.sca[0]
            r = self.scaled_r(r, parent.parent)

        return r

    def get_start_end_points(self, direction, parent=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle Returns the hdl or hdls of the plotted objects.
        """
        abs_geo = self.make_abs_geo(parent)

        if not direction:
            punkt = abs_geo.Ps
            angle = abs_geo.s_ang + pi/2 * abs_geo.ext / abs(abs_geo.ext)
        else:
            punkt = abs_geo.Pe
            angle = abs_geo.e_ang - pi/2 * abs_geo.ext / abs(abs_geo.ext)

        return punkt, angle

    def add2path(self, papath=None, parent=None, layerContent=None):
        """
        Plots the geometry of self into defined path for hit testing. Refer
        to http://stackoverflow.com/questions/11734618/check-if-point-exists-in-qpainterpath
        for description
        @param papath: The hitpath to add the geometrie
        @param parent: The parent of the shape
        """
        abs_geo = self.make_abs_geo(parent)

        segments = int(abs(degrees(abs_geo.ext) // 3) + 1)

        for i in range(segments + 1):

            ang = abs_geo.s_ang + i * abs_geo.ext / segments
            p_cur = Point(abs_geo.O.x + cos(ang) * abs(abs_geo.r),
                          abs_geo.O.y + sin(ang) * abs(abs_geo.r))

            if i >= 1:
                papath.lineTo(p_cur.x, -p_cur.y)

    def Write_GCode(self, parent=None, PostPro=None):
        """
        Writes the GCODE for an Arc.
        @param parent: This is the parent LayerContentClass
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        abs_geo = self.make_abs_geo(parent)

        Ps, s_ang = abs_geo.get_start_end_points(0)
        Pe, e_ang = abs_geo.get_start_end_points(1)

        O = abs_geo.O
        r = abs_geo.r
        IJ = O - Ps

        # If the radius of the element is bigger than the max, radius export the element as an line.
        if r > PostPro.vars.General["max_arc_radius"]:
            string = PostPro.lin_pol_xy(Ps, Pe)
        else:
            if self.ext > 0:
                string = PostPro.lin_pol_arc("ccw", Ps, Pe, s_ang, e_ang, r, O, IJ)
            elif self.ext < 0 and PostPro.vars.General["export_ccw_arcs_only"]:
                string = PostPro.lin_pol_arc("ccw", Pe, Ps, e_ang, s_ang, r, O, O - Pe)
            else:
                string = PostPro.lin_pol_arc("cw", Ps, Pe, s_ang, e_ang, r, O, IJ)

        return string
