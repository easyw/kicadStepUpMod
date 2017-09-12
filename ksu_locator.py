# -*- coding: utf-8 -*-
#****************************************************************************
#*                                                                          *
#*  Kicad STEPUP (TM) (3D kicad board and models to STEP) for FreeCAD       *
#*  3D exporter for FreeCAD                                                 *
#*  Kicad STEPUP TOOLS (TM) (3D kicad board and models to STEP) for FreeCAD *
#*  Copyright (c) 2015                                                      *
#*  Maurice easyw@katamail.com                                              *
#*                                                                          *
#*  Kicad STEPUP (TM) is a TradeMark and cannot be freely useable           *
#*                                                                          *


import os, sys

def module_path():
    #return os.path.dirname(unicode(__file__, encoding))
    return os.path.dirname(__file__)
 
def abs_module_path():
    #return os.path.dirname(unicode(__file__, encoding))
    #return os.path.dirname(__file__)
    return os.path.realpath(__file__)
