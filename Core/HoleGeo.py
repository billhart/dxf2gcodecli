# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2014-2015
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

from __future__ import absolute_import
import logging
import copy


logger = logging.getLogger("Core.HoleGeo")


class HoleGeo():
    """
    HoleGeo represents drilling holes.
    """
    def __init__(self, Ps):
        """
        Standard Method to initialise the HoleGeo
        """

        self.type = "HoleGeo"
        self.Ps = Ps

    def __deepcopy__(self, memo):
        return HoleGeo(copy.deepcopy(self.Ps, memo))

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nHoleGeo at (%s) " % self.Ps


    def reverse(self):
        """
        Reverses the direction.
        """
        pass

    def make_abs_geo(self, parent=None):
        """
        Generates the absolute geometry based on itself and the parent.
        @param parent: The parent of the geometry (EntityContentClass)
        @return: A new HoleGeoClass will be returned.
        """
        Ps = self.Ps.rot_sca_abs(parent=parent)

        return HoleGeo(Ps)

    def get_start_end_points(self, direction, parent=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle
        """
        return self.Ps.rot_sca_abs(parent=parent), 0

    def add2path(self, papath=None, parent=None, layerContent=None):
        """
        Plots the geometry of self into defined path for hit testing.
        @param papath: The hitpath to add the geometrie
        @param parent: The parent of the shape
        testing.
        """
        abs_geo = self.make_abs_geo(parent)
        radius = 2
        if layerContent is not None:
            radius = layerContent.getToolRadius()
        papath.addRoundedRect(abs_geo.Ps.x - radius, -abs_geo.Ps.y - radius, 2*radius, 2*radius, radius, radius)

    def Write_GCode(self, parent=None, PostPro=None):
        """
        Writes the GCODE for a Hole.
        @param parent: This is the parent LayerContentClass
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        return PostPro.make_print_str("(Drilled hole)%nl")
