# -*- coding: utf-8 -*-
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
import FreeCAD, sys, os, re
    
def reload_lib(lib):
    if (sys.version_info > (3, 0)):
        import importlib
        importlib.reload(lib)
    else:
        reload (lib)


def update_ksuGui():
    vrml_materials = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui").GetBool('vrml_materials')
    mode_virtual = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui").GetBool('mode_virtual')
    exp_step = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui").GetBool('exp_step')
    #print('\'vrml_materials\' assigned to: ', vrml_materials)
            
    import kicadStepUptools
    reload_lib( kicadStepUptools )
    if not vrml_materials:
        kicadStepUptools.KSUWidget.ui.cb_materials.setChecked(False)  # Check by default True or False
    else:
        kicadStepUptools.KSUWidget.ui.cb_materials.setChecked(True)  # Check by default True or False    
    if not mode_virtual:
        kicadStepUptools.KSUWidget.ui.cb_virtual.setChecked(False)  # Check by default True or False
    else:
        kicadStepUptools.KSUWidget.ui.cb_virtual.setChecked(True)  # Check by default True or False
    if not exp_step:
        kicadStepUptools.KSUWidget.ui.cb_expStep.setChecked(False)  # Check by default True or False
    else:
        kicadStepUptools.KSUWidget.ui.cb_expStep.setChecked(True)  # Check by default True or False
