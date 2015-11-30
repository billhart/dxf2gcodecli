# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2014-2015
#    Robert Lichtenberger
#    Wojciech Nycz
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

from Core.LineGeo import LineGeo


logger = logging.getLogger("Core.BreakGeo")


class BreakGeo(LineGeo):
    """
    BreakGeo interrupts another geometry item by changing the Z-Position.
    """
    def __init__(self, Ps, Pe, height, xyfeed, zfeed):
        LineGeo.__init__(self, Ps, Pe)

        self.type = "BreakGeo"
        self.height = height
        self.xyfeed = xyfeed
        self.zfeed = zfeed

    def __deepcopy__(self, memo):
        return BreakGeo(copy.deepcopy(self.Ps, memo),
                        copy.deepcopy(self.Pe, memo),
                        copy.deepcopy(self.height, memo),
                        copy.deepcopy(self.xyfeed, memo),
                        copy.deepcopy(self.zfeed, memo))

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nBreakGeo" +\
               "\nPs:     %s" % self.Ps +\
               "\nPe:     %s" % self.Pe +\
               "\nheight: %0.5f" % self.height



    def Write_GCode(self, parent=None, PostPro=None):
        """
        Writes the GCODE for a Break.
        @param parent: This is the parent LayerContentClass
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to file.
        """
        oldZ = PostPro.ze
        oldFeed = PostPro.feed
        if self.height <= oldZ:
            return (
                LineGeo.Write_GCode(self, parent, PostPro)
            )
        else:
            return (
                PostPro.chg_feed_rate(self.zfeed) +
                PostPro.lin_pol_z(self.height) +
                PostPro.chg_feed_rate(self.xyfeed) +
                LineGeo.Write_GCode(self, parent, PostPro) +
                PostPro.chg_feed_rate(self.zfeed) +
                PostPro.lin_pol_z(oldZ) +
                PostPro.chg_feed_rate(oldFeed)
            )
