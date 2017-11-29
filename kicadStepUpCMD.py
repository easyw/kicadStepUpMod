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
import FreeCAD, FreeCADGui, Part, os, sys
import imp, os, sys, tempfile
import FreeCAD, FreeCADGui, Draft, DraftGeomUtils, OpenSCAD2Dgeom
from PySide import QtGui
import ksu_locator
# from kicadStepUptools import onLoadBoard, onLoadFootprint
import math


precision = 0.1 # precision in spline or bezier conversion

reload_Gui=False#True

def reload_lib(lib):
    if (sys.version_info > (3, 0)):
        import importlib
        importlib.reload(lib)
    else:
        reload (lib)

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
        reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
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
            reload_lib( kicadStepUptools )
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.routineCollisions()

FreeCADGui.addCommand('ksuToolsCollisions',ksuToolsCollisions())
##

class ksuTools3D2D:
    "ksu tools 3D to 2D object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , '3Dto2D.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu 3D to 2D" ,
                     'ToolTip' : "3D object to 2D projection"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        FreeCAD.Console.PrintMessage('projecting the selected object to a 2D shape in the document\n')
        faces = []
        objs = []
        if FreeCAD.ActiveDocument is not None:
            vec = FreeCADGui.ActiveDocument.ActiveView.getViewDirection().negative()
            sel = FreeCADGui.Selection.getSelectionEx()
            if FreeCADGui.Selection.getSelectionEx():
                for s in sel:
                    objs.append(s.Object)
                    for e in s.SubElementNames:
                        if "Face" in e:
                            faces.append(int(e[4:])-1)
                #print(objs,faces)
                ##if len(objs) == 1:
                ##    if faces:
                ##        Draft.makeShape2DView(objs[0],vec,facenumbers=faces)
                ##        #return
                for o in objs:
                    Draft.makeShape2DView(o,vec)
            else:
                reply = QtGui.QMessageBox.information(None,"Warning", "select something\nto project it to a 2D shape in the document")
                FreeCAD.Console.PrintError('select something\nto project it to a 2D shape in the document\n')
        else:
            reply = QtGui.QMessageBox.information(None,"Warning", "select something\nto project it to a 2D shape in the document")
            FreeCAD.Console.PrintError('select something\nto project it to a 2D shape in the document\n')
#

FreeCADGui.addCommand('ksuTools3D2D',ksuTools3D2D())

#####
class ksuTools2D2Sketch:
    "ksu tools 2D to Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , '2DtoSketch.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu 2D to Sketch" ,
                     'ToolTip' : "2D object (or DXF) to Sketch"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            try:
                edges=sum((obj.Shape.Edges for obj in \
                FreeCADGui.Selection.getSelection() if hasattr(obj,'Shape')),[])
                #for edge in edges:
                #    print "geomType ",DraftGeomUtils.geomType(edge)
                ##face = OpenSCAD2Dgeom.edgestofaces(edges)
                import kicadStepUptools
                if reload_Gui:
                    reload_lib( kicadStepUptools )
                face = kicadStepUptools.OSCD2Dg_edgestofaces(edges,3 , kicadStepUptools.edge_tolerance)
                #face = OpenSCAD2DgeomMau.edgestofaces(edges)
                face.check() # reports errors
                face.fix(0,0,0)
                faceobj = FreeCAD.ActiveDocument.addObject('Part::Feature',"Face")
                faceobj.Label = "Face"
                faceobj.Shape = face
                for obj in FreeCADGui.Selection.getSelection():
                    FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                FreeCAD.ActiveDocument.recompute()
                FC_majorV=int(FreeCAD.Version()[0])
                FC_minorV=int(FreeCAD.Version()[1])
                wires,_faces = Draft.downgrade(faceobj,delete=True)
                if FC_majorV==0 and FC_minorV<=16:
                    try:
                        sketch = Draft.makeSketch(wires[0:1])
                        sketch.Label = "Sketch_converted"
                        for wire in wires[1:]:
                            Draft.makeSketch([wire],addTo=sketch)
                        sname=FreeCAD.ActiveDocument.ActiveObject.Name
                    except:
                        sname=FreeCAD.ActiveDocument.ActiveObject.Name
                        FreeCAD.ActiveDocument.removeObject(sname)
                        reply = QtGui.QMessageBox.information(None,"Error", "BSplines not supported in FC0.16\nUse FC0.17")
                    #sname=FreeCAD.ActiveDocument.ActiveObject.Name
                    for wire in wires:
                        FreeCAD.ActiveDocument.removeObject(wire.Name)
                #FreeCAD.Console.PrintWarning("\nConverting Bezier curves to Arcs\n")                                
                #wires,_faces = Draft.downgrade(faceobj,delete=True)
                else:
                    newShapeList = []
                    newShapes = []
                    found_BCurve=False
                    newBSlEdges = []
                    #stop
                    for wire in wires:
                        for e in wire.Shape.Edges:
                            if DraftGeomUtils.geomType(e) == "BSplineCurve":
                                #print 'found BSpline'
                                found_BCurve=True
                                newBSlEdges.append(e)
                            elif DraftGeomUtils.geomType(e) == "BezierCurve":
                                #print 'found BezierCurve'
                                found_BCurve=True
                                edges = []
                                newspline = e.Curve.toBSpline()
                                arcs = newspline.toBiArcs(precision)
                                for i in arcs:
                                    edges.append(Part.Edge(i))
                                w = Part.Wire([Part.Edge(i) for i in edges])
                                Part.show(w)
                                w_name=FreeCAD.ActiveDocument.ActiveObject.Name
                                newShapeList.append(w_name)
                                wn=FreeCAD.ActiveDocument.getObject(w_name)
                                newShapes.append(wn)
                            else:
                                #print 'found STD Geom'
                                w = Part.Wire(e)
                                Part.show(w)
                                newShapes.append(w)
                                w_name = FreeCAD.ActiveDocument.ActiveObject.Name
                                newShapeList.append(w_name)
                                
                    #stop
                    #print newShapes
                    if len(newShapes)>0:  #at least a STD geometry exists
                        sketch = Draft.makeSketch(newShapes[0])
                        FreeCAD.ActiveDocument.ActiveObject.Label="Sketch_conv"
                        sname=FreeCAD.ActiveDocument.ActiveObject.Name
                
                        if len(newShapes)>1:  #at least a STD geometry exists
                            for w in newShapes[1:]:
                                Draft.makeSketch([w],addTo=sketch)
                            FreeCAD.ActiveDocument.recompute()
                        for e in newBSlEdges:
                            # sk = FreeCAD.ActiveDocument.addObject('Sketcher::SketchObject','Sketch_bsp')
                            # sk.addGeometry(e.Curve, False)
                            sketch.addGeometry(e.Curve, False)
                            # Sketcher magic fonction :
                        for i in range(0, len(sketch.Geometry)):
                            try: 
                                if 'BSpline' in str(sketch.Geometry[i]):
                                    sketch.exposeInternalGeometry(i)
                            except:
                                #print 'error'
                                pass
                        FreeCAD.ActiveDocument.recompute()
                        FreeCAD.ActiveDocument.getObject(sname).Label="Sketch_converted"
                        #Draft.makeSketch([w])    
                    else:
                        if len (newBSlEdges)>0:
                            sketch = FreeCAD.activeDocument().addObject('Sketcher::SketchObject','Sketch_conv')
                            sname = sketch.Name
                            FreeCAD.ActiveDocument.getObject(sname).Label="Sketch_converted"
                            for e in newBSlEdges:
                                # sk = FreeCAD.ActiveDocument.addObject('Sketcher::SketchObject','Sketch_bsp')
                                # sk.addGeometry(e.Curve, False)
                                sketch.addGeometry(e.Curve, False)
                                # Sketcher magic fonction :
                                for i in range(0, len(sketch.Geometry)):
                                    try: 
                                        if 'BSpline' in str(sketch.Geometry[i]):
                                            sketch.exposeInternalGeometry(i)
                                    except:
                                        #print 'error'
                                        pass
                                FreeCAD.ActiveDocument.recompute()                        
                    for wire in wires:
                        FreeCAD.ActiveDocument.removeObject(wire.Name)
                    for wnm in newShapeList:
                        FreeCAD.ActiveDocument.removeObject(wnm)
                    FreeCAD.ActiveDocument.recompute()
            except Part.OCCError: # Exception: #
                FreeCAD.Console.PrintError('Error in source %s (%s)' % (faceobj.Name,faceobj.Label)+"\n")
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select elements to be converted to Sketch")
            FreeCAD.Console.PrintWarning("Select elements to be converted to Sketch\n")             
        
        pass
#
FreeCADGui.addCommand('ksuTools2D2Sketch',ksuTools2D2Sketch())

#####
class ksuTools2DtoFace:
    "ksu tools 2D to Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , '2DtoFace.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu 2D to Face" ,
                     'ToolTip' : "2D object (or DXF) to Surface for extruding"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            try:
                edges=sum((obj.Shape.Edges for obj in \
                FreeCADGui.Selection.getSelection() if hasattr(obj,'Shape')),[])
                #for edge in edges:
                #    print "geomType ",DraftGeomUtils.geomType(edge)
                import kicadStepUptools
                if reload_Gui:
                    reload_lib( kicadStepUptools )
                face = kicadStepUptools.OSCD2Dg_edgestofaces(edges,3 , kicadStepUptools.edge_tolerance)
                ##face = OpenSCAD2Dgeom.edgestofaces(edges)
                #face = OpenSCAD2DgeomMau.edgestofaces(edges)
                face.check() # reports errors
                face.fix(0,0,0)
                faceobj = FreeCAD.ActiveDocument.addObject('Part::Feature',"Face")
                faceobj.Label = "Face"
                faceobj.Shape = face
                for obj in FreeCADGui.Selection.getSelection():
                    FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                FreeCAD.ActiveDocument.recompute()
                pass
            except Part.OCCError: # Exception: #
                FreeCAD.Console.PrintError('Error in source %s (%s)' % (faceobj.Name,faceobj.Label)+"\n")
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select elements to be converted to Face")
            FreeCAD.Console.PrintWarning("Select elements to be converted to Face\n")             

FreeCADGui.addCommand('ksuTools2DtoFace',ksuTools2DtoFace())

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
                reload_lib( kicadStepUptools )
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
