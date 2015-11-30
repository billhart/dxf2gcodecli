# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2012-2015
#    Xavier Izard
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


logger = logging.getLogger("Core.CustomGCodeClass")


class CustomGCodeClass():
    """
    This class contains a "custom gcode" object. Custom GCode objects are part
    of a layer (LayerContent.py) and are used to insert custom GCode into the
    generated file.
    Custom GCodes are defined in the config file

    @purpose: store user defined GCode
    """
    def __init__(self, name, nr, gcode=None, parent=None):
        """
        Standard method to initialize the class
        @param name: the name of the GCode, as defined in the config file
        @param gcode: the user defined gcode
        @param parent: The parent layer Class of the shape
        """
        self.type = "CustomGCode"
        self.name = name
        self.nr = nr
        self.gcode = gcode
        self.LayerContent = parent
        self.disabled = False
        self.send_to_TSP = False #Never optimize path for CustomGCode

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nCustomGCode" +\
               "\nname:  %s" % self.name +\
               "\nnr:    %i" % self.nr +\
               "\ngcode: %s" % self.gcode



    def setDisable(self, flag=False):
        """
        Function to modify the disable property
        @param flag: The flag to enable or disable Selection
        """
        self.disabled = flag

    def isDisabled(self):
        """
        Returns the state of self.disabled
        """
        return self.disabled

    def Write_GCode(self, parent=None, PostPro=None):
        """
        This method returns the string to be exported for this custom gcode, including
        @param LayerContent: This parameter includes the parent LayerContent
        @param PostPro: this is the Postprocessor class including the methods to export
        """
        return self.gcode
