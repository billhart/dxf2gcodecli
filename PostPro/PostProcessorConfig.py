# -*- coding: utf-8 -*-

############################################################################
#   
#   Copyright (C) 2008-2014
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

import os

from Core.configobj import ConfigObj, flatten_errors
from Core.validate import Validator

#from dotdictlookup import DictDotLookup
import time

import Core.constants as c
import Core.Globals as g
from d2gexceptions import *


import logging
logger = logging.getLogger("PostPro.PostProcessorConfig") 

POSTPRO_VERSION = "4"
"""
version tag - increment this each time you edit CONFIG_SPEC

compared to version number in config file so
old versions are recognized and skipped
"""
    
POSTPRO_SPEC = str('''
#  Section and variable names must be valid Python identifiers
#      do not use whitespace in names 

# do not edit the following section name:
    [Version]

    # do not edit the following value:
    config_version = string(default="'''  + \
    str(POSTPRO_VERSION) + '")\n' + \
'''
    [General]
    output_format = string(default=".ngc")
    output_text = string(default="G-CODE for LinuxCNC")
    output_type = string(default="g-code")
    
    abs_export = boolean(default=True)
    cancel_cc_for_depth = boolean(default=False)
    cc_outside_the_piece = boolean(default=True)
    export_ccw_arcs_only = boolean(default=False)
    max_arc_radius = float(default=10000)
    
    code_begin_units_mm = string(default="G21 (Units in millimeters)")
    code_begin_units_in = string(default="G20 (Units in inches)")
    code_begin = string(default="G90 (Absolute programming) G64 (Default cutting) G17 (XY plane) G40 (Cancel radius comp.) G49 (Cancel length comp.)")
    code_end = string(default="M2 (Program end)")
    
    [Number_Format]
    pre_decimals = integer(default=4)
    post_decimals = integer(default=3)
    decimal_seperator = string(default=".")
    pre_decimal_zero_padding = boolean(default=False)
    post_decimal_zero_padding = boolean(default=True)
    signed_values = boolean(default=False)
    
    [Line_Numbers]
    use_line_nrs = boolean(default=False)
    line_nrs_begin = integer(default=10)
    line_nrs_step = integer(default=10)
    
    [Program]
    tool_change = string(default=T%tool_nr M6%nlS%speed%nl)
    feed_change = string(default=F%feed%nl)
    rap_pos_plane = string(default=G0 X%XE Y%YE%nl)
    rap_pos_depth = string(default=G0 Z%ZE %nl)
    lin_mov_plane = string(default= G1 X%XE Y%YE%nl)
    lin_mov_depth = string(default= G1 Z%ZE%nl)
    arc_int_cw = string(default=G2 X%XE Y%YE I%I J%J%nl)
    arc_int_ccw = string(default=G3 X%XE Y%YE I%I J%J%nl)
    cutter_comp_off = string(default=G40%nl) ''' + \
# FIXME: adding G40 before each G41/G42 invokation is a dirty fix for open shapes when using tool compensation. we need to turn it off before turning it on in the opposite direction so the linuxCNC axis does not complain. Needs more elegant way to do that in the code.
'''
    cutter_comp_left = string(default=G40%nlG41%nl)
    cutter_comp_right = string(default=G40%nlG42%nl)
    pre_shape_cut = string(default=M3 M8%nl)
    post_shape_cut = string(default=M9 M5%nl)
    comment = string(default=%nl(%comment)%nl)              

''').splitlines()  
""" format, type and default value specification of the global config file"""


class MyPostProConfig():
    """
    This class hosts all functions related to the PostProConfig File.
    """
    def __init__(self, filename = 'postpro_config' + c.CONFIG_EXTENSION):
        """
        initialize the varspace of an existing plugin instance
        init_varspace() is a superclass method of plugin
        @param filename: The filename for the creation of a new config
        file and the filename of the file to read config from.
        """
        
        
        self.folder = os.path.join(g.folder, c.DEFAULT_POSTPRO_DIR)
        self.filename = os.path.join(self.folder, filename)
        
        self.default_config = False # whether a new name was generated
        self.var_dict = dict()
        self.spec = ConfigObj(POSTPRO_SPEC, interpolation=False, list_values=False, _inspec=True)


    def load_config(self):
        """
        This method tries to load the defined postprocessor file given in 
        self.filename. If this fails it will create a new one 
        """

        try:
            # file exists, read & validate it
            self.var_dict = ConfigObj(self.filename, configspec=POSTPRO_SPEC)
            _vdt = Validator()
            result = self.var_dict.validate(_vdt, preserve_errors=True)
            validate_errors = flatten_errors(self.var_dict, result)

            if validate_errors:
                g.logger.logger.error(("errors reading %s:") % (self.filename))
            for entry in validate_errors:
                section_list, key, error = entry
                if key is not None:
                    section_list.append(key)
                else:
                    section_list.append('[missing section]')
                section_string = ', '.join(section_list)
                if error == False:
                    error = ('Missing value or section.')
                g.logger.logger.error( section_string + ' = ' + error)       

            if validate_errors:
                raise BadConfigFileError, ("syntax errors in postpro_config file")
                
            # check config file version against internal version

            if POSTPRO_VERSION:
                fileversion = self.var_dict['Version']['config_version'] # this could raise KeyError

                if fileversion != POSTPRO_VERSION:
                    raise VersionMismatchError, (fileversion, POSTPRO_VERSION)
          
        except VersionMismatchError, values:
            raise VersionMismatchError, (fileversion, POSTPRO_VERSION)
                   
        except Exception, inst:
            logger.error(inst)               
            (base, ext) = os.path.splitext(self.filename)
            badfilename = base + c.BAD_CONFIG_EXTENSION
            logger.debug(("trying to rename bad cfg %s to %s") % (self.filename, badfilename))
            try:
                os.rename(self.filename, badfilename)
            except OSError, e:
                logger.error(("rename(%s,%s) failed: %s") % (self.filename, badfilename, e.strerror))
                raise
            else:
                logger.debug(("renamed bad varspace %s to '%s'") % (self.filename, badfilename))
                self.create_default_config()
                self.default_config = True
                logger.debug(("created default varspace '%s'") % (self.filename))
        else:
            self.default_config = False
            logger.debug(("read existing varspace '%s'") % (self.filename))

        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.var_dict.main.interpolation = False # avoid ConfigObj getting too clever
        self.vars = DictDotLookup(self.var_dict) 

    def make_settings_folder(self): 
        """
        This method creates the postprocessor settings folder if necessary
        """ 
        try: 
            os.mkdir(self.folder) 
        except OSError: 
            pass        

    def create_default_config(self):
        """
        If no postprocessor config file exists this function is called 
        to generate the config file based on its specification.
        """
        #check for existing setting folder or create one
        self.make_settings_folder()
        
        # derive config file with defaults from spec
        logger.debug(POSTPRO_SPEC)
        
        self.var_dict = ConfigObj(configspec=POSTPRO_SPEC)
        _vdt = Validator()
        self.var_dict.validate(_vdt, copy=True)
        self.var_dict.filename = self.filename
        self.var_dict.write()
        
        
#    def _save_varspace(self):
#        self.var_dict.filename = self.filename
#        self.var_dict.write()   
#    
    def print_vars(self):
        """
        Print all the variables with their values
        """
        print "Variables:"
        for k, v in self.var_dict['Variables'].items():
            print k, " = ", v
            

class DictDotLookup(object):
    """
    Creates objects that behave much like a dictionaries, but allow nested
    key access using object '.' (dot) lookups.
    """
    def __init__(self, d):
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]

    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def __iter__(self):
        return iter(self.__dict__.keys())

#    def __repr__(self):
#        return pprint.pformat(self.__dict__)
