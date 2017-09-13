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

import FreeCAD,FreeCADGui
import FreeCAD, FreeCADGui, Part, os
import imp, os, sys, tempfile
import FreeCAD, FreeCADGui
from PySide import QtGui
import ksu_locator
# from kicadStepUptools import onLoadBoard, onLoadFootprint

reload_Gui=False#True

ksuWBpath = os.path.dirname(ksu_locator.__file__)
#sys.path.append(ksuWB + '/Gui')
ksuWB_icons_path =  os.path.join( ksuWBpath, 'Resources', 'icons')

#__dir__ = os.path.dirname(__file__)
#iconPath = os.path.join( __dir__, 'Resources', 'icons' )


# class SMExtrudeCommandClass():
#   """Extrude face"""
# 
#   def GetResources(self):
#     return {'Pixmap'  : os.path.join( iconPath , 'SMExtrude.svg') , # the name of a svg file available in the resources
#             'MenuText': "Extend Face" ,
#             'ToolTip' : "Extend a face along normal"}

class ksuTools:
    "ksu tools object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'kicad-StepUp-icon.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Tools" ,
                     'ToolTip' : "kicad StepUp Tools"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        import os, sys
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        reload( kicadStepUptools )
        FreeCAD.Console.PrintWarning( 'active :)\n' )
        #import kicadStepUptools
 
FreeCADGui.addCommand('ksuTools',ksuTools())
##

class ksuToolsOpenBoard:
    "ksu tools Open Board object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importBoard.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Load Board" ,
                     'ToolTip' : "Load KiCad PCB Board and Parts"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.onLoadBoard()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
    
        #onPushPCB()
        #import kicadStepUptools


FreeCADGui.addCommand('ksuToolsOpenBoard',ksuToolsOpenBoard())
##

class ksuToolsLoadFootprint:
    "ksu tools Load Footprint object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importFP.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Load FootPrint" ,
                     'ToolTip' : "Load KiCad PCB FootPrint"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.onLoadFootprint()

FreeCADGui.addCommand('ksuToolsLoadFootprint',ksuToolsLoadFootprint())
##

class ksuToolsExportModel:
    "ksu tools Export Model to KiCad object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'export3DModel.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Export 3D Model" ,
                     'ToolTip' : "Export 3D Model to KiCad"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
      ##evaluate to read cfg and get materials value???
      ##or made something as in load board
        #ini_content=kicadStepUptools.cfg_read_all()
        kicadStepUptools.routineScaleVRML()
        #kicadStepUptools.Ui_DockWidget.onCfg()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools

FreeCADGui.addCommand('ksuToolsExportModel',ksuToolsExportModel())
##

class ksuToolsImport3DStep:
    "ksu tools Import 3D Step object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'add_block_y.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Import 3D Step" ,
                     'ToolTip' : "Import 3D Step Model"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.Import3DModelF()

FreeCADGui.addCommand('ksuToolsImport3DStep',ksuToolsImport3DStep())
##

class ksuToolsExport3DStep:
    "ksu tools Export 3D to Step object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'export3DStep.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Export 3D to Step" ,
                     'ToolTip' : "Export selected objects to Step Model"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.Export3DStepF()

FreeCADGui.addCommand('ksuToolsExport3DStep',ksuToolsExport3DStep())
##

class ksuToolsMakeUnion:
    "ksu tools Make a Union object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'fusion.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Make Union" ,
                     'ToolTip' : "Make a Union of selected objects"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.group_part_union()

FreeCADGui.addCommand('ksuToolsMakeUnion',ksuToolsMakeUnion())
##

class ksuToolsMakeCompound:
    "ksu tools Make a Union object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'compound.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Make Compound" ,
                     'ToolTip' : "Make a Compound of selected objects"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.group_part()

FreeCADGui.addCommand('ksuToolsMakeCompound',ksuToolsMakeCompound())
##

class ksuToolsPushPCB:
    "ksu tools Push/Pull Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_Rectangle.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Push/Pull Sketch to PCB" ,
                     'ToolTip' : "Push/Pull Sketch to/from PCB Edge"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.PushPullPCB()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools


FreeCADGui.addCommand('ksuToolsPushPCB',ksuToolsPushPCB())
##

# class ksuToolsEdit:
#     "ksu tools Editor object"
#  
#     def GetResources(self):
#         return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'edit.svg') , # the name of a svg file available in the resources
#                      'MenuText': "ksu Edit parameters" ,
#                      'ToolTip' : "ksu View Config Parameters"}
#  
#     def IsActive(self):
#         return True
#  
#     def Activated(self):
#         # do something here...
#         import kicadStepUptools
#         #if not kicadStepUptools.checkInstance():
#         #    reload( kicadStepUptools )
#         if reload_Gui:
#             reload( kicadStepUptools )
#         FreeCAD.Console.PrintWarning( 'active :)\n' )
#         kicadStepUptools.view_cfg()
# 
# FreeCADGui.addCommand('ksuToolsEdit',ksuToolsEdit())
##

class ksuToolsCollisions:
    "ksu tools Check Collisions object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'collisions.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Check Collisions" ,
                     'ToolTip' : "Check Collisions and Interferences"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload( kicadStepUptools )
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.routineCollisions()

FreeCADGui.addCommand('ksuToolsCollisions',ksuToolsCollisions())
##

#####
class ksuExcDemo:
    exFile = None

    def __init__(self, exFile):
        self.exFile = str(exFile)
        self.ext    = self.exFile[self.exFile.rfind('.'):].lower()
        #print self.ext
    
    # 'hierarchy_nav.svg' for Demo
    #'Pixmap'  : os.path.join( ksuWB_icons_path , 'hierarchy_nav.svg') ,

    def GetResources(self):
        if 'pdf' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'datasheet.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}
        elif 'kicad_pcb' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importPCB.svg'), #'importBoard.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}
        elif 'kicad_mod' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importFP.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}
        elif 'fcstd' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Freecad.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}        
        elif 'step' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importStep.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}                    
        else:
            return {'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}

    def Activated(self):
        FreeCAD.Console.PrintWarning('opening ' + self.exFile + "\r\n")
        import os, sys
        # So we can open the "Open File" dialog
        mw = FreeCADGui.getMainWindow()

        # Start off defaulting to the Examples directory
        ksu_base_path = ksu_locator.module_path()
        exs_dir_path = os.path.join(ksu_base_path, 'demo')
        abs_ksu_path = ksu_locator.abs_module_path()
        # Append this script's directory to sys.path
        sys.path.append(os.path.dirname(exs_dir_path))

        # We've created a library that FreeCAD can use as well to open CQ files
        fnameDemo=(os.path.join(exs_dir_path, self.exFile))
        demo_model='dpak-to252.step'
        stepfname=(os.path.join(exs_dir_path, 'shapes',demo_model))
        ext = os.path.splitext(os.path.basename(fnameDemo))[1]
        nme = os.path.splitext(os.path.basename(fnameDemo))[0]
        FC_majorV=int(FreeCAD.Version()[0])
        FC_minorV=int(FreeCAD.Version()[1])

        if ext.lower()==".pdf":
            import subprocess, sys
            if sys.platform == "linux" or sys.platform == "linux2":
                # linux
                subprocess.call(["xdg-open", fnameDemo])
            if sys.platform == "darwin":
                # osx
                cmd_open = 'open '+fnameDemo
                os.system(cmd_open) #win, osx
            else:
                # win
                subprocess.Popen([fnameDemo],shell=True)
        elif ext.lower()==".kicad_pcb" or ext.lower()==".kicad_mod":
            #FreeCAD.Console.PrintMessage(abs_ksu_path + "\r\n")
            #FreeCAD.Console.PrintMessage(stepfname + "\r\n")
            #FreeCAD.Console.PrintMessage(exs_dir_path + "\r\n")
            import kicadStepUptools
            #    reload( kicadStepUptools )
            if reload_Gui:
                reload( kicadStepUptools )
            from kicadStepUptools import open, create_axis #onLoadBoard, onLoadFootprint
            if ext.lower()==".kicad_mod":
                dname= (demo_model).split('.')[0].replace('-','_')
                doc = FreeCAD.newDocument(dname)
                dname=doc.Name
                #print dname
                FreeCAD.setActiveDocument(dname)
                FreeCAD.ActiveDocument=FreeCAD.getDocument(dname)
                FreeCADGui.ActiveDocument=FreeCADGui.getDocument(dname)
                #doc=FreeCAD.newDocument((demo_model).split('.')[0].replace('-','_'))
                #FreeCAD.setActiveDocument(doc)
                import ImportGui
                ImportGui.insert(stepfname,doc.Name)
                FreeCADGui.activeDocument().activeView().viewAxonometric()
                open (fnameDemo)
                if FreeCAD.ActiveDocument.getObject("axis") is None:
                    create_axis()
            else:
                open (fnameDemo)
            #docL=FreeCAD.ActiveDocument.Label
        elif ext.lower()==".fcstd":
            if FC_majorV==0 and FC_minorV <17:
                fnameDemo=fnameDemo.rstrip(ext)+'-fc16'+ ext
                FreeCAD.Console.PrintWarning('opening ' + fnameDemo + "\r\n")
            FreeCAD.open(fnameDemo)
            FreeCADGui.activeDocument().activeView().viewAxonometric()
        elif ext.lower()==".step":
            if FC_majorV==0 and FC_minorV <17:
                fnameDemo=fnameDemo.rstrip(ext)+'-fc16'+ ext
                FreeCAD.Console.PrintWarning('opening ' + fnameDemo + "\r\n")
            import ImportGui
            ImportGui.open(fnameDemo)
            FreeCADGui.activeDocument().activeView().viewAxonometric()
            FreeCADGui.SendMsgToActiveView("ViewFit")
        #if ext==".pdf":
        #    subprocess.Popen([file],shell=True)
        
        #import ImportGui
        #ImportGui.open(os.path.join(exs_dir_path, self.exFile))
        #ImportCQ.open(os.path.join(exs_dir_path, self.exFile))

##
