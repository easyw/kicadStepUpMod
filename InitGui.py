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

import FreeCAD, FreeCADGui, Part, os, sys
import ksu_locator
from kicadStepUpCMD import *

ksuWBpath = os.path.dirname(ksu_locator.__file__)
#sys.path.append(ksuWB + '/Gui')
ksuWB_icons_path =  os.path.join( ksuWBpath, 'Resources', 'icons')

global main_ksu_Icon
main_ksu_Icon = os.path.join( ksuWB_icons_path , 'kicad-StepUp-tools-WB.svg')

ksu_wb_version='v 7.4.1'
#try:
#    from FreeCADGui import Workbench
#except ImportError as e:
#    FreeCAD.Console.PrintWarning("error")
    
class ksuWB ( Workbench ):
    global main_ksu_Icon, ksu_wb_version
    
    "kicad StepUp WB object"
    Icon = main_ksu_Icon
    #Icon = ":Resources/icons/kicad-StepUp-tools-WB.svg"
    MenuText = "kicad StepUp WB"
    ToolTip = "kicad StepUp workbench"
 
    def GetClassName(self):
        return "Gui::PythonWorkbench"
    
    def Initialize(self):
        import kicadStepUpCMD
        submenu = ['demo.kicad_pcb','d-pak.kicad_mod', 'demo-sketch.FCStd', 'demo.step', 'kicadStepUp-cheat-sheet.pdf', 'kicad-3D-to-MCAD.pdf' ]
        dirs = self.ListDemos()

        #self.appendToolbar("ksu Tools", ["ksuTools"])
        self.appendToolbar("ksu Tools", ["ksuTools","ksuToolsOpenBoard","ksuToolsLoadFootprint",\
                           "ksuToolsExportModel","ksuToolsPushPCB","ksuToolsCollisions", \
                           "ksuToolsImport3DStep","ksuToolsExport3DStep","ksuToolsMakeUnion",\
                           "ksuToolsMakeCompound", "ksuTools3D2D", "ksuTools2D2Sketch", "ksuTools2DtoFace"])
        
        #self.appendMenu("ksu Tools", ["ksuTools","ksuToolsEdit"])
        self.appendMenu("ksu Tools", ["ksuTools"])
        self.appendMenu(["ksu Tools", "Demo"], submenu)
        
        Log ("Loading ksuModule... done\n")
 
    def Activated(self):
                # do something here if needed...
        Msg ("ksuWB.Activated("+ksu_wb_version+")\n")
 
    def Deactivated(self):
                # do something here if needed...
        Msg ("ksuWB.Deactivated()\n")
    @staticmethod
    def ListDemos():
        import os
        import ksu_locator

        dirs = []
        # List all of the example files in an order that makes sense
        module_base_path = ksu_locator.module_path()
        demo_dir_path = os.path.join(module_base_path, 'demo')
        dirs = os.listdir(demo_dir_path)
        dirs.sort()

        return dirs

###

dirs = ksuWB.ListDemos()
#FreeCADGui.addCommand('ksuWBOpenDemo', ksuOpenDemo())
#dirs = ksuWB.ListDemos()
for curFile in dirs:
    FreeCADGui.addCommand(curFile, ksuExcDemo(curFile))

FreeCADGui.addWorkbench(ksuWB)