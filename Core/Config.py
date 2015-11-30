# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2009-2015
#    Christian Kohlöffel
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
import os
import pprint
import logging


from Core.configobj import ConfigObj, flatten_errors
from Core.validate import Validator
import Core.constants as c
import Core.Globals as g
from d2gexceptions import *


logger = logging.getLogger("Core.Config")

CONFIG_VERSION = "9.5"
"""
version tag - increment this each time you edit CONFIG_SPEC

compared to version number in config file so
old versions are recognized and skipped"
"""

CONFIG_SPEC = str('''
#  Section and variable names must be valid Python identifiers
#      do not use whitespace in names

# do not edit the following section name:
    [Version]
    # do not edit the following value:
    config_version = string(default = "''' +
    str(CONFIG_VERSION) + '")\n' +
    '''
    [Paths]
    # by default look for DXF files in
    import_dir = string(default = "D:/Eclipse_Workspace/DXF2GCODE/trunk/dxf")

    # export generated gcode by default to
    output_dir = string(default = "D:")

    [Filters]
    pstoedit_cmd = string(default = "C:\Program Files (x86)\pstoedit\pstoedit.exe")
    pstoedit_opt = list(default = list('-f', 'dxf', '-mm', '-dt'))

    [Axis_letters]
    ax1_letter = string(default = "X")
    ax2_letter = string(default = "Y")
    ax3_letter = string(default = "Z")

    [Plane_Coordinates]
    axis1_start_end = float(default = 0)
    axis2_start_end = float(default = 0)

    [Depth_Coordinates]
    axis3_retract = float(default = 15.0)
    axis3_safe_margin = float(default = 3.0)
    axis3_start_mill_depth = float(default = 0.0)
    axis3_slice_depth = float(default = -1.5)
    axis3_mill_depth = float(default = -3.0)

    [Feed_Rates]
    f_g1_plane = float(default = 400)
    f_g1_depth = float(default = 150)

    [General]
    write_to_stdout = boolean(default = False)
    show_disabled_paths = boolean(default = True)
    live_update_export_route = boolean(default = False)
    default_SplitEdges = boolean(default = False)
    default_AutomaticCutterCompensation = boolean(default = False)
    machine_type = option('milling', 'drag_knife', 'lathe', default = 'milling')
    tool_units = option('mm', 'in', default = 'mm')

    [Drag_Knife_Options]
    # dragAngle: if larger than this angle (in degrees), tool retracts to dragDepth
    # the dragDepth is given by axis3_slice_depth
    dragAngle = float(default = 20)

    [Route_Optimisation]
    default_TSP = boolean(default = False)

    # Path optimizer behaviour:
    #  CONSTRAIN_ORDER_ONLY: fixed Shapes and optimized Shapes can be mixed. Only order of fixed shapes is kept
    #  CONSTRAIN_PLACE_AFTER: optimized Shapes are always placed after any fixed Shape
    TSP_shape_order = option('CONSTRAIN_ORDER_ONLY', 'CONSTRAIN_PLACE_AFTER', default = 'CONSTRAIN_ORDER_ONLY')
    mutation_rate = float(default = 0.95)
    max_population = integer(default = 20)
    max_iterations = integer(default = 300)
    begin_art = option('ordered', 'random', 'heuristic', default = 'heuristic')

    [Import_Parameters]
    point_tolerance = float(default = 0.001)
    spline_check = integer(default = 3)
    fitting_tolerance = float(default = 0.001)

    [Layer_Options]
    id_float_separator = string(default = ":")

    # mill options
    mill_depth_identifiers = list(default = list('MillDepth', 'Md', 'TiefeGesamt', 'Tg'))
    slice_depth_identifiers = list(default = list('SliceDepth', 'Sd', 'TiefeZustellung', 'Tz'))
    start_mill_depth_identifiers = list(default = list('StartMillDepth', 'SMd', 'StartTiefe', 'St'))
    retract_identifiers = list(default = list('RetractHeight', 'Rh', 'Freifahrthoehe', 'FFh'))
    safe_margin_identifiers = list(default = list('SafeMargin', 'Sm', 'Sicherheitshoehe', 'Sh'))
    f_g1_plane_identifiers = list(default = list('FeedXY', 'Fxy', 'VorschubXY', 'Vxy', 'F'))
    f_g1_depth_identifiers = list(default = list('FeedZ', 'Fz', 'VorschubZ', 'Vz'))

    # tool options
    tool_nr_identifiers = list(default = list('ToolNr', 'Tn', 'T', 'WerkzeugNummer', 'Wn'))
    tool_diameter_identifiers = list(default = list('ToolDiameter', 'Td', 'WerkzeugDurchmesser', 'Wd'))
    spindle_speed_identifiers = list(default = list('SpindleSpeed', 'Drehzahl', 'RPM', 'UPM', 'S'))
    start_radius_identifiers = list(default = list('StartRadius', 'Sr'))

    [Tool_Parameters]
    [[1]]
    diameter = float(default = 2.0)
    speed = float(default = 6000)
    start_radius = float(default = 0.2)

    [[2]]
    diameter = float(default = 2.0)
    speed = float(default = 6000.0)
    start_radius = float(default = 1.0)

    [[10]]
    diameter = float(default = 10.0)
    speed = float(default = 6000.0)
    start_radius = float(default = 2.0)

    [[__many__]]
    diameter = float(default = 3.0)
    speed = float(default = 6000)
    start_radius = float(default = 3.0)

    [Custom_Actions]
    [[custom_gcode]]
    gcode = string(default = '"""(change subsection name and insert your custom GCode here. Use triple quote to place the code on several lines)"""')

    [[__many__]]
    gcode = string(default = "(change subsection name and insert your custom GCode here. Use triple quote to place the code on several lines)")

    [Logging]
    # Logging to textfile is enabled automatically for now
    logfile = string(default = "logfile.txt")

    # log levels are one in increasing importance:
    #      DEBUG INFO WARNING  ERROR CRITICAL
    # log events with importance >= loglevel are logged to the
    # corresponding output

    # this really goes to stderr
    console_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'CRITICAL')

    file_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'DEBUG')

    # logging level for the message window
    window_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'INFO')

''').splitlines()
""" format, type and default value specification of the global config file"""


class MyConfig():
    """
    This class hosts all functions related to the Config File.
    """
    def __init__(self):
        """
        initialize the varspace of an existing plugin instance
        init_varspace() is a superclass method of plugin
        """

        self.folder = os.path.join(g.folder, c.DEFAULT_CONFIG_DIR)
        self.filename = os.path.join(self.folder, 'config' + c.CONFIG_EXTENSION)

        self.default_config = False # whether a new name was generated
        self.var_dict = dict()
        self.spec = ConfigObj(CONFIG_SPEC, interpolation=False, list_values=False, _inspec=True)

        # try:

        self.load_config()
        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.vars = DictDotLookup(self.var_dict)

        self.machine_type = self.vars.General['machine_type']
        self.fitting_tolerance = self.vars.Import_Parameters['fitting_tolerance']
        self.point_tolerance = self.vars.Import_Parameters['point_tolerance']

        self.metric = 1  # true unit is determined while importing
        self.tool_units_metric = 0 if self.vars.General['tool_units'] == 'in' else 1

        # except Exception, msg:
        #     logger.warning(("Config loading failed: %s") % msg)
        #     return False


    def make_settings_folder(self):
        """Create settings folder if necessary"""
        try:
            os.mkdir(self.folder)
        except OSError:
            pass

    def load_config(self):
        """Load Config File"""
        if os.path.isfile(self.filename):
            try:
                # file exists, read & validate it
                self.var_dict = ConfigObj(self.filename, configspec=CONFIG_SPEC)
                _vdt = Validator()
                result = self.var_dict.validate(_vdt, preserve_errors=True)
                validate_errors = flatten_errors(self.var_dict, result)

                if validate_errors:
                    logger.error(("errors reading %s:") % self.filename)

                for entry in validate_errors:
                    section_list, key, error = entry
                    if key is not None:
                        section_list.append(key)
                    else:
                        section_list.append('[missing section]')
                    section_string = ', '.join(section_list)
                    if not error:
                        error = ('Missing value or section.')
                    logger.error( section_string + ' = ' + error)

                if validate_errors:
                    raise BadConfigFileError("syntax errors in config file")

                # check config file version against internal version
                if CONFIG_VERSION:
                    fileversion = self.var_dict['Version']['config_version']  # this could raise KeyError

                    if fileversion != CONFIG_VERSION:
                        raise VersionMismatchError(fileversion, CONFIG_VERSION)

            except VersionMismatchError, values:
                raise VersionMismatchError(fileversion, CONFIG_VERSION)

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
                    logger.debug(("created default varspace '%s'") % self.filename)
            else:
                self.default_config = False
                # logger.debug(self.dir())
                # logger.debug(("created default varspace '%s'") %(self.filename))
                # logger.debug(("read existing varspace '%s'") %(self.filename))
        else:
            self.create_default_config()
            self.default_config = True
            logger.debug(("created default varspace '%s'") % (self.filename))

        self.var_dict.main.interpolation = False  # avoid ConfigObj getting too clever

    def create_default_config(self):
        # check for existing setting folder or create one
        self.make_settings_folder()

        # derive config file with defaults from spec
        self.var_dict = ConfigObj(configspec=CONFIG_SPEC)
        _vdt = Validator()
        self.var_dict.validate(_vdt, copy=True)
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def _save_varspace(self):
        """Saves Variables space"""
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def print_vars(self):
        """Prints Variables"""
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

    def __setitem__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value

    def __iter__(self):
        return iter(self.__dict__.keys())

    def __repr__(self):
        return pprint.pformat(self.__dict__)

# if __name__ == '__main__':
#     cfg_data = eval("""{
#         'foo' : {
#             'bar' : {
#                 'tdata' : (
#                     {'baz' : 1 },
#                     {'baz' : 2 },
#                     {'baz' : 3 },
#                 ),
#             },
#         },
#         'quux' : False,
#     }""")
#
#     cfg = DictDotLookup(cfg_data)
#
#     # iterate
#     for k, v in cfg.__iter__(): #foo.bar.iteritems():
#         print k, " = ", v
#
#     print "cfg=", cfg
#
#     #   Standard nested dictionary lookup.
#     print 'normal lookup :', cfg['foo']['bar']['tdata'][0]['baz']
#
#     #   Dot-style nested lookup.
#     print 'dot lookup    :', cfg.foo.bar.tdata[0].baz
#
#     print "qux=", cfg.quux
#     cfg.quux = '123'
#     print "qux=", cfg.quux
#
#     del cfg.foo.bar
#     cfg.foo.bar = 4711
#     print 'dot lookup    :', cfg.foo.bar #.tdata[0].baz
