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
from DxfImport.Classes import ContourClass
from math import degrees, radians

class GeoentInsert:
    def __init__(self, Nr=0, caller=None):
        self.Typ = 'Insert'
        self.Nr = Nr

        #Initialisieren der Werte
        #Initialise the values
        self.Layer_Nr = 0
        self.BlockName = ''
        self.Point = []
        self.Scale = [1, 1, 1]
        self.rot = 0.0
        self.length = 0.0

        #Lesen der Geometrie
        #Red the geometry
        self.Read(caller)   

        
    def __str__(self):
        # how to print the object
        return '\nTyp:          Insert' + \
                '\nNr:          %i' % self.Nr + \
                '\nLayer Nr:    %i' % self.Layer_Nr + \
                '\nBlockName:   %s' % self.BlockName + \
                '\nPoint:       %s' % self.Point + \
                '\nrot:         %0.2f' % degrees(self.rot) + \
                '\nScale:       %s' % self.Scale 

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

        #Block Name        
        ind = lp.index_code(2, caller.start + 1, e)
        #print lp.line_pair[ind].value ########################################
        self.BlockName = lp.line_pair[ind].value
        
        #Assign layer
        s = lp.index_code(8, caller.start + 1, e)
        self.Layer_Nr = caller.Get_Layer_Nr(lp.line_pair[s].value)
        
        #X Value
        s = lp.index_code(10, s + 1, e)
        x0 = float(lp.line_pair[s].value)
        
        #Y Value
        s = lp.index_code(20, s + 1, e)
        y0 = float(lp.line_pair[s].value)
        self.Point = Point(x0, y0)
        
        #XScale
        s_temp = lp.index_code(41, s + 1, e)
        if s_temp != None:
            self.Scale[0] = float(lp.line_pair[s_temp].value)
        
        #YScale
        s_temp = lp.index_code(42, s + 1, e)
        if s_temp != None:
            self.Scale[1] = float(lp.line_pair[s_temp].value)
        
        #ZScale
        s_temp = lp.index_code(43, s + 1, e)
        if s_temp != None:
            self.Scale[2] = float(lp.line_pair[s_temp].value)
        
        #Rotation
        s_temp = lp.index_code(50, s + 1, e)
        if s_temp != None:
            self.rot = radians(float(lp.line_pair[s_temp].value))
        
        #New starting value for the next geometry
        caller.start = e      

