#-*- coding: utf-8 -*-
#****************************************************************************
#*                                                                          *
#*  Kicad STEPUP (TM) (3D kicad board and models to STEP) for FreeCAD       *
#*  3D exporter for FreeCAD                                                 *
#*  Kicad STEPUP TOOLS (TM) (3D kicad board and models to STEP) for FreeCAD *
#*  Copyright (c) 2015                                                      *
#*  Maurice easyw@katamail.com                                              *
#*                                                                          *
#*  Kicad STEPUP (TM) is a TradeMark and cannot be freely usable            *
#*                                                                          *

# two options for IDF added by Milos Koutny (12-Feb-2010)
#FreeCAD.addImportType("Kicad pcb board/mod File Type (*.kicad_pcb *.emn *.kicad_mod)","kicadStepUptools") 
# ___ver___ = "6.0.4.5"
## idf import dropped

#FreeCAD.addImportType("Kicad pcb board/mod File Type (*.kicad_pcb *.kicad_mod)","kicadStepUptools") 
FreeCAD.addImportType("Kicad pcb board File Type (*.kicad_pcb)","kicadStepUptools") 
FreeCAD.addImportType("Kicad pcb mod File Type (*.kicad_mod)","kicadStepUptools") 

FreeCAD.addImportType("zip of STEP/FCStd File Type (*.zip)","ZipStepImport")

# using faithful old legacy dxf v1.4.0
# FreeCAD.addImportType("DXF Legacy Type (*.dxf)","_DXF_Import")

import FreeCAD

#FreeCAD.addImportType("IDF emp File Type (*.emp)","Import_Emp") 
