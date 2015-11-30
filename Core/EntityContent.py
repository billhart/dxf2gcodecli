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

from __future__ import absolute_import
import logging

from Core.Point import Point


logger = logging.getLogger("Core.EntityContent")


class EntityContentClass(object):

    def __init__(self, Nr=None, Name='', parent=None,
                children=[], p0=Point(), pb=Point(),
                sca=[1, 1, 1], rot=0.0):

        self.type = "Entity"
        self.Nr = Nr
        self.Name = Name
        self.children = children
        self.p0 = p0
        self.pb = pb
        self.sca = sca
        self.rot = rot
        self.parent = parent

    def __cmp__(self, other):
        return cmp(self.EntNr, other.EntNr)

    def __str__(self):
        return "\nEntity" +\
               "\nNr:       %i" % self.Nr +\
               "\nName:     %s" % self.Name +\
               "\np0:       %s" % self.p0 +\
               "\npb:       %s" % self.pb +\
               "\nsca:      %s" % self.sca +\
               "\nrot:      %s" % self.rot +\
               "\nchildren: %s" % self.children


    def addchild(self, child):
        """
        Add the contour of the Entities
        """
        self.children.append(child)

