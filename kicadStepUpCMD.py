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

import FreeCAD, FreeCADGui, Part
from FreeCAD import Base
import os, sys, tempfile, re
import Draft, DraftGeomUtils  #, OpenSCAD2Dgeom
import PySide
from PySide import QtGui, QtCore
from PySide.QtCore import QT_TRANSLATE_NOOP
QtWidgets = QtGui

from pivy import coin
from threading import Timer

import ksu_locator
# from kicadStepUptools import onLoadBoard, onLoadFootprint
import math
from math import sqrt

import constrainator
from constrainator import add_constraints, sanitizeSkBsp

ksuCMD_version__='2.4.1'


precision = 0.1 # precision in spline or bezier conversion
q_deflection = 0.02 # quasi deflection parameter for discretization

hide_compound = True

reload_Gui=False#True

a3 = False
try:
    from freecad.asm3 import assembly as asm
    FreeCAD.Console.PrintWarning('A3 available\n')
    a3 = True
except:
    # FreeCAD.Console.PrintWarning('A3 not available\n')
    a3 = False

try:
    from PathScripts.PathUtils import horizontalEdgeLoop
    from PathScripts.PathUtils import horizontalFaceLoop
    from PathScripts.PathUtils import loopdetect
    import PathCommands
except:
    FreeCAD.Console.PrintError('Path WB not found\n')

def reload_lib(lib):
    if (sys.version_info > (3, 0)):
        import importlib
        importlib.reload(lib)
    else:
        reload (lib)

use_outerwire = False #False #True
remove_shapes = True #False #True 
hide_objects = True #False # True
use_draft = True #False  # True use Draft.makesketch
attach_sketch = False #True
create_plane = False# True #False

conv_started = False

global max_geo_admitted
max_geo_admitted = 1500 # after this number, no recompute is applied

from sys import platform as _platform

pt_lnx=False
# window GUI dimensions parameters
if _platform == "linux" or _platform == "linux2":
   # linux
   pt_lnx=True
   sizeXmin=172;sizeYmin=34+34
   sizeX=172;sizeY=516 #536
   sizeXright=172;sizeYright=536 #556
else:
    sizeXmin=172;sizeYmin=34
    sizeX=172;sizeY=482#502
    sizeXright=172;sizeYright=502#522
if _platform == "darwin":
    pt_osx=True

def P_Line(prm1,prm2):
    if hasattr(Part,"LineSegment"):
        return Part.LineSegment(prm1, prm2)
    else:
        return Part.Line(prm1, prm2)

def fuse_objs(GuiObjSel):
    objList= []
    for s in GuiObjSel:
        objList.append(s.Object)
    FreeCAD.ActiveDocument.addObject("Part::MultiFuse","MultiFuse")
    MultiFuseName = FreeCAD.ActiveDocument.ActiveObject.Name
    FreeCAD.ActiveDocument.getObject(MultiFuseName).Shapes = objList
    # [App.activeDocument().Part__Feature002,App.activeDocument().Part__Feature003,App.activeDocument().Part__Feature004,App.activeDocument().Part__Feature005,App.activeDocument().Part__Feature006,App.activeDocument().Part__Feature007,App.activeDocument().Part__Feature008,App.activeDocument().Part__Feature009,App.activeDocument().Part__Feature010,App.activeDocument().Part__Feature011,]
    FreeCAD.ActiveDocument.recompute()
    return MultiFuseName
#

def rmvsubtree(objs):
    def addsubobjs(obj,toremoveset):
        toremove.add(obj)
        if hasattr(obj,'OutList'):
            for subobj in obj.OutList:
                addsubobjs(subobj,toremoveset)
    import FreeCAD
    toremove=set()
    for obj in objs:
        addsubobjs(obj,toremove)
    checkinlistcomplete =False
    while not checkinlistcomplete:
        for obj in toremove:
            if (obj not in objs) and (frozenset(obj.InList) - toremove):
                toremove.remove(obj)
                break
        else:
            checkinlistcomplete = True
    for obj in toremove:
        try:
            obj.Document.removeObject(obj.Name)
        except:
            pass
###
def info_msg(msg):
        QtGui.QApplication.restoreOverrideCursor()
        # msg="""Select <b>a Compound</b> or <br><b>a Part Design group</b><br>or <b>more than one Part</b> object !<br>"""
        spc="""<font color='white'>*******************************************************************************</font><br>
        """
        msg1="Info ..."
        QtGui.QApplication.restoreOverrideCursor()
        #RotateXYZGuiClass().setGeometry(25, 250, 500, 500)
        diag = QtGui.QMessageBox(QtGui.QMessageBox.Icon.Information,
                                msg1,
                                msg)
        diag.setWindowModality(QtCore.Qt.ApplicationModal)
        diag.exec_()
##

ksuWBpath = os.path.dirname(ksu_locator.__file__)
#sys.path.append(ksuWB + '/Gui')
ksuWB_icons_path =  os.path.join( ksuWBpath, 'Resources', 'icons')

#__dir__ = os.path.dirname(__file__)
#iconPath = os.path.join( __dir__, 'Resources', 'icons' )

def getTopLevel (obj):
    lvl=10000
    top=None
    if hasattr(obj,'InListRecursive'):
        for ap in obj.InListRecursive:
            if hasattr(ap,'Placement'):
                if len(ap.InListRecursive) < lvl:
                    top = ap
                    lvl = len(ap.InListRecursive)
            #else:
            #    sayerr(obj.Label)
        #top = obj
    return top
##
def getSortedList (obj):
    lvl=10000
    completed=0
    listUs=obj.InListRecursive
    #sayerr('unsorted')
    #for p in listUs:
    #    print p.Label
    listUsName=[]
    for o in obj.InListRecursive:
        listUsName.append(o.Name)
    listS=[]
    i=0
    #for i, ap in enumerate(listUs):
    #    top=ap
    #    if len(ap.InListRecursive) < lvl:
    #        lvl = len(ap.InListRecursive)
    #    for ap2 in listUs[(i + 1):]:
    #        if len(ap2.InListRecursive) < lvl:
    #            top = ap2
    #            lvl = len(ap2.InListRecursive)
    #    listS.append(top)
    #sayw(listUsName)
    i=0
    while len (listUsName) > 0:
        for apName in listUsName:
            #apName=listUsName[i]
            ap=FreeCAD.ActiveDocument.getObject(apName)
            if len(ap.InListRecursive) < lvl:
                lvl = len(ap.InListRecursive)
                top = ap
                topName = ap.Name
        listS.append(top)
        #print topName
        idx=listUsName.index(topName)
        #sayw(idx)
        listUsName.pop(idx)
        lvl=10000
        #sayerr(listUsName)

    return listS
##
def getNormalPlacementHierarchy (sel0):
    """get normal at face and placement relative to hierarchy
       of first selection object/face
       return normal, placement, topObj, bbox center absolute"""

    import Draft
    from FreeCAD import Base
    use_hierarchy = True
    
    Obj=sel0.Object
    subObj=sel0.SubObjects[0]
    edge_op=0

    top_level_obj = getTopLevel(Obj)
    if top_level_obj is not None: #hierarchy object
        # say('Hierarchy obj')
        pad=0
        open_circle=False
        if 'Face' in str(subObj):
            # say('Hierarchy obj Face')
            pad=0 #face
        elif 'Edge' in str(subObj):
            wire = Part.Wire(subObj)
            if subObj.isClosed():
                subObj = Part.Face(wire)
            else:
                # sayerr(str(subObj.Curve))
                if 'Circle' in str(subObj.Curve):
                    # sayerr('Circle radius '+str(subObj.Curve.Radius))
                    #f1=subObj.Shape.Faces[0]

                    wf = Part.Face(Part.Wire(subObj))
                    Part.show(wf)
                    wf_name=FreeCAD.ActiveDocument.ActiveObject.Name

                    dirz=wf.normalAt(0,0)
                    # ccircle = Part.makeCircle(r, Base.Vector(cnt), Base.Vector(dirz))
                    # > Circle (Radius : 10, Position : (10, 0, 0), Direction : (1, 0, 0))
                    ccircle = Part.makeCircle(subObj.Curve.Radius, Base.Vector(subObj.Curve.Center), Base.Vector(dirz))
                    #ccircle_face = Part.Face(ccircle)
                    #Part.show(ccircle_face)
                    #ccircle_face_name=FreeCAD.ActiveDocument.ActiveObject.Name
                    #FreeCAD.ActiveDocument.getObject(ccircle_face_name).Label='ccircle_face'
                    Part.show(ccircle)
                    ccircle_name=FreeCAD.ActiveDocument.ActiveObject.Name
                    FreeCAD.ActiveDocument.getObject(ccircle_name).Label='ccircle'
                    f2=Part.Face(Part.Wire((FreeCAD.ActiveDocument.getObject(ccircle_name).Shape.Edges[0])))
                    Part.show(f2)
                    f2_name=FreeCAD.ActiveDocument.ActiveObject.Name
                    FreeCAD.ActiveDocument.removeObject(ccircle_name)
                    FreeCAD.ActiveDocument.removeObject(wf_name)
                    # ccircle.Curve
                    # > Circle (Radius : 10, Position : (10, 0, 0), Direction : (1, 0, 0))
                    bbxCenter = subObj.Curve.Center

                    norm = f2.normalAt(0,0)
                    subObj = f2
                    FreeCAD.ActiveDocument.removeObject(f2_name)
                    #PC1=Draft.makePoint(subObj.Curve.Center)
                    #w.close
                    open_circle=True
                else:
                    subObj = wire
                #subObj = wire
                edge_op=1
            pad=1 #edge
        if use_hierarchy:
            nwshp = subObj.copy()
            pOriginal=subObj.Placement
            if 'Datum' not in str(Obj.Name):
                p0 =  FreeCAD.Placement (FreeCAD.Vector(0,0,0), FreeCAD.Rotation(0,0,0), FreeCAD.Vector(0,0,0))
                nwshp.Placement=p0
            r=[]
            t=nwshp.copy()
            #resetting Placement
            for i in t.childShapes():
                c=i.copy()
                c.Placement=t.Placement.multiply(c.Placement)
                r.append((i,c))
            acpy=t.replaceShape(r)
            acpy.Placement=FreeCAD.Placement()
            if hasattr(Obj,'InListRecursive'):
                lrl=len(Obj.InListRecursive)
                # for o_ in Obj.InListRecursive:
                #     say(o_.Name)
                if len(Obj.InList):
                    top_level_obj = getTopLevel(Obj)
                    #sayerr(top_level_obj[j].Label)
                    listSorted=getSortedList (Obj)
                    #for p in listSorted:
                    #    print p.Name
                    #print listSorted, ' Sorted; Top ', top_level_obj[j]
                    #stop
                    for i in range (0,lrl):
                        if hasattr(listSorted[i],'Placement'):
                            #if 'Plane' not in ob.InListRecursive[i].TypeId:
                            if listSorted[i].hasExtension("App::GeoFeatureGroupExtension"):
                                acpy.Placement=acpy.Placement.multiply(listSorted[i].Placement)
            # say(acpy.Placement)
            #acpy.Placement=acpy.Placement.multiply(pOriginal)
            #acpy.Placement=acpy.Placement.multiply(pOriginal)
            if pad == 0: #note making wire from edge already resets the original placement
                acpy.Placement=acpy.Placement.multiply(pOriginal)
            nwshp.Placement = acpy.Placement
            if open_circle==True:
                nwnorm = nwshp.normalAt(0,0)
            elif edge_op==1:
                nwnorm = (nwshp.Vertex2.Point - nwshp.Vertex1.Point).normalize()
            else:
                nwnorm = nwshp.normalAt(0,0)
            bbxCenter = nwshp.BoundBox.Center
        else:
            nwshp = subObj.copy()
            if open_circle==True:
                nwnorm = nwshp.normalAt(0,0)
            elif edge_op==1:
                nwnorm = (subObj.Vertex2.Point - subObj.Vertex1.Point).normalize()
            else:
                nwnorm = nwshp.normalAt(0,0)
            bbxCenter = nwshp.BoundBox.Center

        return nwnorm, nwshp.Placement, top_level_obj, bbxCenter

    elif 'Face' in str(subObj) or 'Edge' in str(subObj): # not in hierarchy
        # say('Part obj')
        pad=0 #face
        open_circle=False
        if 'Edge' in str(subObj):
            wire = Part.Wire(subObj)
            if subObj.isClosed():
                subObj = Part.Face(wire)
                norm = subObj.normalAt(0,0)
                bbxCenter = subObj.BoundBox.Center
            else:
                # sayerr(str(subObj.Curve))
                if 'Circle' in str(subObj.Curve):
                    # sayerr('Circle radius '+str(subObj.Curve.Radius))
                    #f1=subObj.Shape.Faces[0]

                    wf = Part.Face(Part.Wire(subObj))
                    Part.show(wf)
                    wf_name=FreeCAD.ActiveDocument.ActiveObject.Name

                    dirz=wf.normalAt(0,0)
                    # ccircle = Part.makeCircle(r, Base.Vector(cnt), Base.Vector(dirz))
                    # > Circle (Radius : 10, Position : (10, 0, 0), Direction : (1, 0, 0))
                    ccircle = Part.makeCircle(subObj.Curve.Radius, Base.Vector(subObj.Curve.Center), Base.Vector(dirz))
                    #ccircle_face = Part.Face(ccircle)
                    #Part.show(ccircle_face)
                    #ccircle_face_name=FreeCAD.ActiveDocument.ActiveObject.Name
                    #FreeCAD.ActiveDocument.getObject(ccircle_face_name).Label='ccircle_face'
                    Part.show(ccircle)
                    ccircle_name=FreeCAD.ActiveDocument.ActiveObject.Name
                    FreeCAD.ActiveDocument.getObject(ccircle_name).Label='ccircle'
                    f2=Part.Face(Part.Wire((FreeCAD.ActiveDocument.getObject(ccircle_name).Shape.Edges[0])))
                    Part.show(f2)
                    f2_name=FreeCAD.ActiveDocument.ActiveObject.Name
                    FreeCAD.ActiveDocument.removeObject(ccircle_name)
                    FreeCAD.ActiveDocument.removeObject(wf_name)
                    # ccircle.Curve
                    # > Circle (Radius : 10, Position : (10, 0, 0), Direction : (1, 0, 0))
                    bbxCenter = subObj.Curve.Center

                    norm = f2.normalAt(0,0)
                    #subObj = f2
                    FreeCAD.ActiveDocument.removeObject(f2_name)
                    #PC1=Draft.makePoint(subObj.Curve.Center)
                    #w.close
                else:
                    norm = (subObj.Vertex2.Point - subObj.Vertex1.Point).normalize()
                    bbxCenter = subObj.BoundBox.Center
            pad=1 #edge
        else:
            norm = subObj.normalAt(0,0)
            bbxCenter = subObj.BoundBox.Center
        top_level_obj=None
        #sayerr(str(norm)+str(Obj.Placement)+str(bbxCenter)+str(top_level_obj))

        return norm, Obj.Placement, top_level_obj, bbxCenter

##


def ksu_edges2sketch():
    global conv_started, max_geo_admitted
    
    cp_edges = [];cp_edges_names = []
    cp_edges_shapes = []; cp_edges_obj = []
    cp_obj = []; cp_obj_name = []
    cp_points = []; cp_faces = []
    wires = []
    doc=FreeCAD.ActiveDocument
    docG = FreeCADGui.ActiveDocument
    en = None
    selEx=FreeCADGui.Selection.getSelectionEx()
    import Draft
    if len (selEx) > 0:
        for selEdge in selEx:
            if not (conv_started):
                doc.openTransaction('e2sk')
                conv_started = True
            for i,e in enumerate(selEdge.SubObjects):
                if 'Edge' in selEdge.SubElementNames[i]:
                    cp_edges.append(e)
                    #cp_edges_shapes.append(e.toShape())
                    Part.show(Part.Wire(e))
                    cp = doc.ActiveObject
                    cp_edges_obj.append(cp)
                    #print(cp)
                    cp_edges_names.append(selEdge.ObjectName+'.'+selEdge.SubElementNames[i])
                    cp_obj.append(selEdge.Object)
                    cp_edges_shapes.append(selEdge.Object.Shape)
                    cp_obj_name.append(selEdge.ObjectName)
                    if create_plane:
                        for v in cp.Shape.Vertexes[:3]: #selEdge.Object.Shape.Vertexes[:3]:
                            if v.Point not in cp_points:
                                cp_points.append(v.Point)
                            if len (cp_points) > 2:
                                    break
                    #FreeCAD.Console.PrintMessage(selEdge.ObjectName);FreeCAD.Console.PrintMessage('\n')
                    FreeCAD.Console.PrintMessage(selEdge.ObjectName+'.'+selEdge.SubElementNames[i])
                    FreeCAD.Console.PrintMessage('\n')
                    if hide_objects:
                        docG.getObject(selEdge.ObjectName).Visibility = False
                    #FreeCAD.Console.PrintMessage(e);FreeCAD.Console.PrintMessage('\n')
                    #cp_e = Part.show(Part.Wire(e))
                    wire = Part.Wire(e)
                    #cp_edges_shapes.append(wire.toShape())
                    wires.append (wire)
                elif 'Face'  in selEdge.SubElementNames[i]:
                    #o.Shape.Faces
                    cp_faces.append(e)
                    if use_outerwire:
                        ow=e.OuterWire
                        wires.append (ow)
                        #es = ow.Edges
                        for _e in ow.Edges:
                            cp_edges.append(_e)
                        Part.show(ow)
                        cp = doc.ActiveObject
                        cp_edges_obj.append(cp)
                        if create_plane:
                            for v in cp.Vertexes[:3]: #selEdge.Object.Shape.Vertexes[:3]:
                                print('point')
                                if v.Point not in cp_points:
                                    cp_points.append(v.Point)
                                if len (cp_points) > 2:
                                    break
                    else:    
                        ws=e.Wires
                        wires.append (ws)
                        #es=e.Edges
                        if create_plane:
                            for v in e.Vertexes[:3]: #selEdge.Object.Shape.Vertexes[:3]:
                                print(v.Point)
                                if len (cp_points) > 2:
                                    break
                                if v.Point not in cp_points:
                                    cp_points.append(v.Point)
                        for w in ws:
                            for _e in w.Edges:
                                cp_edges.append(_e)
                            Part.show(w)
                            cp = doc.ActiveObject
                            cp_edges_obj.append(cp)
                    if hide_objects:
                        docG.getObject(selEdge.ObjectName).Visibility = False
                    #for ed in es:
                    #    Part.show(ed)
                elif 'Vertex'  in selEdge.SubElementNames[i]:
                    #print(selEdge.SubElementNames[i])
                    #print(selEdge.Object.Shape.Volume)
                    if selEdge.Object.Shape.Volume == 0:
                        print('outline selected')
                        #for _e in selEdge.Object.Shape.Edges:
                        #    Part.show(_e.Curve.toShape())
                        #    cp_edges.append(_e)
                        #    cp_edges_shapes.append(e.toShape())
                        #    Part.show(Part.Wire(_e))
                        #    cp = doc.ActiveObject
                        #    cp_edges_obj.append(cp)
                        cp_edges_obj.append(selEdge.Object.Shape.copy())
                        if hide_objects:
                            docG.getObject(selEdge.ObjectName).Visibility = False
                    
        if len (cp_edges_obj) >0: # (wires) >0:
            if not (use_draft):
                FreeCAD.activeDocument().addObject('Sketcher::SketchObject','Sketch')
                #FreeCAD.activeDocument().Sketch.MapMode = "ObjectXY"
                #doc.recompute()
                sketch = doc.ActiveObject
                sketch.Label = "Sketch_converted"
            if len (cp_edges_obj) > 1:
                doc.addObject("Part::MultiFuse","union")
                union = doc.ActiveObject
                doc.union.Shapes = cp_edges_obj #cp_obj # [doc.Shape005,doc.Shape006]
                if len (cp_edges_obj) < max_geo_admitted:
                    doc.recompute()
            else:
                union = cp_edges_obj[0]
            #sketch.MapMode = "ObjectXZ"
            #sketch.Support = [(doc.Cut,'Face2')]
            #sketch.MapMode = 'FlatFace'
            # doc.recompute()
            #Draft.makeSketch([wire],addTo=sketch)
            # points = 
            #print(cp_points)
            triple = []
            if len (cp_points) > 2:
                for p in cp_points:
                    if p not in triple:
                        triple.append(p)
                face= Part.Face(Part.makePolygon([p for p in triple], True))
            else:
                for _e in cp_edges:
                    if _e.isClosed():
                        face = Part.Face(Part.Wire(_e))
            #print (triple)
            #plane = Part.Plane(*[p for p in triple])
            #print([p for p in triple])
            if create_plane:
                doc.addObject('Part::Feature','Face').Shape=face
                newface = doc.ActiveObject
            #[App.ActiveDocument.union.Shape.Vertex2.Point, App.ActiveDocument.union.Shape.Vertex5.Point, App.ActiveDocument.union.Shape.Vertex1.Point, ], True))
            #print(plane)
            ## _makeSketch(plane,wires,addTo=sketch)
            #Draft.makeSketch(wires,addTo=sketch)
            _objs_ = []
            obj_tobd = []
            use_workaround_1 = False
            use_workaround_2 = False
            active_view = FreeCADGui.ActiveDocument.activeView()
            rotation_view = active_view.getCameraOrientation()
            top_rotation = FreeCAD.Rotation(0.0,0.0,0.0,1.0)
            if rotation_view != top_rotation and len(union.Shape.Edges) < max_geo_admitted:
                use_workaround_1 = True
                use_workaround_2 = True
            if use_workaround_1:
                FreeCAD.Console.PrintWarning('workaround to avoid issues in Draft.makeSketch from Bottom\n')
                _objs_ = Draft.downgrade(FreeCAD.ActiveDocument.getObject('union'), delete=False)
                FreeCAD.ActiveDocument.recompute()
                _objs_ = []
                obj_tobd.append(FreeCADGui.Selection.getSelection())
                _objs_ = Draft.upgrade(FreeCADGui.Selection.getSelection(), delete=True)
                _objs_ = []
                FreeCAD.ActiveDocument.recompute()
                obj_tobd.append(FreeCADGui.Selection.getSelection())
                _objs_ = Draft.downgrade(FreeCADGui.Selection.getSelection(), delete=True)
                # print(_objs_)
                # FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.ActiveObject)
                sel_objs = FreeCADGui.Selection.getSelection()
                FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.ActiveObject)
                # print(len(sel_objs))
                # for o in sel_objs:
                #     print (o.Label)
                #FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.getObject('union'))
                # FreeCADGui.runCommand('ksuTools2D2Sketch',0)
            if use_draft:
                #Draft.makeSketch(union,addTo=sketch)
                if use_workaround_1:
                    #FreeCADGui.runCommand('ksuTools2D2Sketch',0)
                    Draft.makeSketch(FreeCADGui.Selection.getSelection(),autoconstraints=True) #,addTo=sketch)
                else:
                    Draft.makeSketch(union,autoconstraints=True) #,addTo=sketch)
                sketch = doc.ActiveObject
                p = sketch.Placement
                # print(p)
                # print(p.Rotation.Axis)
                if use_workaround_2 and p.Rotation.Axis.z != 1:
                    FreeCAD.Console.PrintWarning('workaround on Axis to avoid issues in Draft.makeSketch\n')
                    p.Rotation.Axis.x = 0
                    p.Rotation.Axis.y = 0
                    p.Rotation.Axis.z = 1
                    p.Base.x = 0
                    p.Base.y = 0
                    p.Base.z = 1
                    # print(p)
                sketch.Label = "Sketch_converted"
            else:
                for _e in union.Shape.Edges:
                    if isinstance(_e.Curve,Part.Line) or isinstance(_e.Curve,Part.LineSegment):
                        sketch.addGeometry(P_Line(Base.Vector(_e.firstVertex().Point), Base.Vector(_e.lastVertex().Point)))
                    #sketch.addGeometry(_e.Curve)
            sk = doc.ActiveObject
            if attach_sketch:
                sketch.Support = [newface, 'Face1']
                sketch.MapMode = 'FlatFace'
            #sk.Placement = union.Placement
            if remove_shapes:
                rmvsubtree([union])
                if use_workaround_1:
                    for o in obj_tobd:
                        #print(o)
                        for s in o:
                            try:
                                FreeCAD.ActiveDocument.removeObject(s.Name)
                            except:
                                pass
                    for o in sel_objs:
                        FreeCAD.ActiveDocument.removeObject(o.Name)
                if create_plane:
                    rmvsubtree([newface])
            sketch.MapMode = 'Deactivated'
            # for e in cp_edges:
            #     sketch.addGeometry(e.Curve, False)
            #     print ('e added')
            for i in range(0, len(sketch.Geometry)):
                try: 
                    g = str(sketch.Geometry[i])
                    if 'BSpline' in g or 'Ellipse' in g:
                        sketch.exposeInternalGeometry(i)
                except:
                    #print 'error'
                    pass
            docG.getObject(sketch.Name).LineColor = (1.00,1.00,1.00)
            docG.getObject(sketch.Name).PointColor = (1.00,1.00,1.00)
            #print(docG.getObject(sketch.Name).PointColor)
            lg = len(sketch.Geometry)
            if lg == 0:
                doc.removeObject(sketch.Name)
                docG.getObject(selEdge.ObjectName).Visibility = True
                QtGui.QApplication.restoreOverrideCursor()
                reply = QtGui.QMessageBox.information(None,"info", "All Shapes must be co-planar")
                doc.abortTransaction()
            else:
                for s in FreeCADGui.Selection.getSelection():
                    FreeCADGui.Selection.removeSelection(s)
                FreeCADGui.Selection.addSelection(sketch)
                doc.commitTransaction()
            conv_started = False
            if lg < max_geo_admitted:
                doc.recompute()
        else:
            print('Select coplanar edge(s) or Face(s) or a single Vertex \nof a coplanar outline to get a corresponding Sketch\n')
    # for ob in FreeCAD.ActiveDocument.Objects:
    #     FreeCADGui.Selection.removeSelection(ob)
##
class Ui_Offset_value(object):
    def setupUi(self, Offset_value):
        Offset_value.setObjectName("Offset_value")
        Offset_value.resize(292, 177)
        Offset_value.setWindowTitle(translate("ksu","Offset value"))
        Offset_value.setToolTip("")
        self.buttonBoxLayer = QtWidgets.QDialogButtonBox(Offset_value)
        self.buttonBoxLayer.setGeometry(QtCore.QRect(10, 130, 271, 32))
        self.buttonBoxLayer.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBoxLayer.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBoxLayer.setObjectName("buttonBoxLayer")
        self.gridLayoutWidget = QtWidgets.QWidget(Offset_value)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 10, 271, 101))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.offset_label = QtWidgets.QLabel(self.gridLayoutWidget)
        self.offset_label.setMinimumSize(QtCore.QSize(0, 0))
        self.offset_label.setToolTip("")
        self.offset_label.setText(translate("ksu","Offset [+/- mm]:"))
        self.offset_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.offset_label.setObjectName("offset_label")
        self.gridLayout.addWidget(self.offset_label, 0, 0, 1, 1)
        self.lineEdit_offset = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_offset.setToolTip(translate("ksu","Offset value [+/- mm]"))
        self.lineEdit_offset.setText("0.16")
        self.lineEdit_offset.setObjectName("lineEdit_offset")
        self.gridLayout.addWidget(self.lineEdit_offset, 0, 1, 1, 1)
        self.checkBox = QtWidgets.QCheckBox(self.gridLayoutWidget)
        self.checkBox.setToolTip(translate("ksu","Arc or Intersection Offset method"))
        self.checkBox.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.checkBox.setText(translate("ksu","Arc"))
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 2, 0, 1, 1)
        
        self.offset_label_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.offset_label_2.setMinimumSize(QtCore.QSize(0, 0))
        self.offset_label_2.setToolTip("")
        self.offset_label_2.setText(translate("ksu","Offset Y [mm]:"))
        self.offset_label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.offset_label_2.setObjectName("offset_label_2")
        self.gridLayout.addWidget(self.offset_label_2, 1, 0, 1, 1)
        self.lineEdit_offset_2 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_offset_2.setToolTip(translate("ksu","Offset Y value [+/- mm]"))
        self.lineEdit_offset_2.setText("5.0")
        self.lineEdit_offset_2.setObjectName("lineEdit_offset_2")
        self.gridLayout.addWidget(self.lineEdit_offset_2, 1, 1, 1, 1)

        self.retranslateUi(Offset_value)
        self.buttonBoxLayer.accepted.connect(Offset_value.accept)
        self.buttonBoxLayer.rejected.connect(Offset_value.reject)
        QtCore.QMetaObject.connectSlotsByName(Offset_value)

    def retranslateUi(self, Offset_value):
        pass

##
#
# class SMExtrudeCommandClass():
#   """Extrude face"""
# 
#   def GetResources(self):
#     return {'Pixmap'  : os.path.join( iconPath , 'SMExtrude.svg') , # the name of a svg file available in the resources
#             'MenuText': "Extend Face" ,
#             'ToolTip' : "Extend a face along normal"}
class Ui_CDialog(object):
    def setupUi(self, CDialog):
        CDialog.setObjectName("CDialog")
        CDialog.resize(317, 302)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Sketcher_LockAll.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        CDialog.setWindowIcon(icon)
        CDialog.setToolTip("")
        CDialog.setStatusTip("")
        CDialog.setWhatsThis("")
        self.buttonBox = QtGui.QDialogButtonBox(CDialog)
        self.buttonBox.setGeometry(QtCore.QRect(8, 255, 207, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.Label_howto = QtGui.QLabel(CDialog)
        self.Label_howto.setGeometry(QtCore.QRect(20, 5, 265, 61))
        self.Label_howto.setToolTip(translate("ksu","Select a Sketch and Parameters\n"
"to constraint the sketch\n"
"NB the Sketch will be modified!"))
        self.Label_howto.setStatusTip("")
        self.Label_howto.setWhatsThis("")
        self.Label_howto.setText(translate("ksu","<b>Select a Sketch and Parameters to<br>constrain the sketch.<br>NB the Sketch will be modified!</b>"))
        self.Label_howto.setObjectName("Label_howto")
        self.Constraints = QtGui.QGroupBox(CDialog)
        self.Constraints.setGeometry(QtCore.QRect(10, 70, 145, 166))
        self.Constraints.setToolTip("")
        self.Constraints.setStatusTip("")
        self.Constraints.setWhatsThis("")
        self.Constraints.setTitle(translate("ksu","Constraints"))
        self.Constraints.setObjectName("Constraints")
        self.verticalLayoutWidget = QtGui.QWidget(self.Constraints)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(12, 20, 125, 137))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.all_constraints = QtGui.QRadioButton(self.verticalLayoutWidget)
        self.all_constraints.setMinimumSize(QtCore.QSize(92, 64))
        self.all_constraints.setToolTip(translate("ksu","Lock Coincident, Horizontal\n"
"and Vertical"))
        self.all_constraints.setText("")
        self.all_constraints.setIcon(icon)
        self.all_constraints.setIconSize(QtCore.QSize(48, 48))
        self.all_constraints.setChecked(True)
        self.all_constraints.setObjectName("all_constraints")
        self.verticalLayout.addWidget(self.all_constraints)
        self.coincident = QtGui.QRadioButton(self.verticalLayoutWidget)
        self.coincident.setMinimumSize(QtCore.QSize(92, 64))
        self.coincident.setToolTip(translate("ksu","Lock Coincident"))
        self.coincident.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("Sketcher_LockCoincident.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.coincident.setIcon(icon1)
        self.coincident.setIconSize(QtCore.QSize(48, 48))
        self.coincident.setChecked(False)
        self.coincident.setObjectName("coincident")
        self.verticalLayout.addWidget(self.coincident)
        self.Tolerance = QtGui.QGroupBox(CDialog)
        self.Tolerance.setGeometry(QtCore.QRect(166, 70, 141, 91))
        self.Tolerance.setToolTip("")
        self.Tolerance.setStatusTip("")
        self.Tolerance.setWhatsThis("")
        self.Tolerance.setTitle(translate("ksu","Tolerance"))
        self.Tolerance.setObjectName("Tolerance")
        self.verticalLayoutWidget_2 = QtGui.QWidget(self.Tolerance)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(8, 20, 125, 57))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtGui.QLabel(self.verticalLayoutWidget_2)
        self.label.setToolTip("mm")
        self.label.setStatusTip("")
        self.label.setWhatsThis("")
        self.label.setText(translate("ksu","tolerance in mm"))
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.tolerance = QtGui.QLineEdit(self.verticalLayoutWidget_2)
        self.tolerance.setMinimumSize(QtCore.QSize(64, 22))
        self.tolerance.setMaximumSize(QtCore.QSize(64, 22))
        self.tolerance.setToolTip(translate("ksu","Tolerance on Constraints"))
        self.tolerance.setStatusTip("")
        self.tolerance.setWhatsThis("")
        self.tolerance.setInputMethodHints(QtCore.Qt.ImhPreferNumbers)
        self.tolerance.setInputMask("")
        self.tolerance.setText("0.1")
        self.tolerance.setPlaceholderText("")
        self.tolerance.setObjectName("tolerance")
        self.verticalLayout_2.addWidget(self.tolerance)
        self.rmvXGeo = QtGui.QCheckBox(CDialog)
        self.rmvXGeo.setGeometry(QtCore.QRect(170, 180, 141, 20))
        self.rmvXGeo.setToolTip(translate("ksu","remove duplicated geometries"))
        self.rmvXGeo.setStatusTip("")
        self.rmvXGeo.setText("rmv xtr geo")
        self.rmvXGeo.setObjectName("rmvXGeo")

        #self.retranslateUi(CDialog)
        ###  --------------------------------------------------------
        #self.checkBox.setText("rmv xtr geo")
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), CDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), CDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CDialog)
        
        
        myiconsize=48
        icon = QtGui.QIcon()
        myicon=os.path.join( ksuWB_icons_path , 'Sketcher_LockCoincident.svg')
        icon.addPixmap(QtGui.QPixmap(myicon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.coincident.setIcon(icon)
        self.coincident.setIconSize(QtCore.QSize(myiconsize, myiconsize))
        self.coincident.setChecked(True)
        icon1 = QtGui.QIcon()
        myicon=os.path.join( ksuWB_icons_path , 'Sketcher_LockAll.svg')
        icon1.addPixmap(QtGui.QPixmap(myicon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.all_constraints.setIcon(icon1)
        self.all_constraints.setIconSize(QtCore.QSize(myiconsize, myiconsize))
        icond = QtGui.QIcon()
        myicon=os.path.join( ksuWB_icons_path , 'Sketcher_LockAll.svg')
        icond.addPixmap(QtGui.QPixmap(myicon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        CDialog.setWindowIcon(icon)
    

        # remove question mark from the title bar
        CDialog.setWindowFlags(CDialog.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        #self.Label_howto.setText("<b>Select a Sketch and Parameters<br>to constraint the sketch<br>NB the Sketch will be modified!</b>")

    def return_strings(self):
    #   Return list of values. It need map with str (self.lineedit.text() will return QString)
        return map(str, [self.tolerance.text(), self.all_constraints.isChecked(), self.rmvXGeo.isChecked()])
        
    # @staticmethod
    # def get_data(parent=None):
    #     #dialog = Ui_CDialog()
    #     dialog = Ui_CDialog(parent)
    #     #dialog = QtGui.QDialog()
    #     dialog.exec_()
    #     return dialog.return_strings()
        
################ ------------------- end CD-ui #############################

class ksuTools:
    "ksu tools object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'kicad-StepUp-icon.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuTools","ksu Tools") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuTools","Activate the main\nkicad StepUp Tools Dialog")}
 
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
        kicadStepUptools.KSUWidget.activateWindow()
        kicadStepUptools.KSUWidget.show()
        kicadStepUptools.KSUWidget.raise_()
        FreeCAD.Console.PrintWarning( 'active :)\n' )
        #import kicadStepUptools
 
FreeCADGui.addCommand('ksuTools',ksuTools())
##

class ksuToolsContour2Poly:
    "ksu tools Shapes Selection to PolyLine Sketch"
    
    def GetResources(self):
        mybtn_tooltip = QT_TRANSLATE_NOOP("ksuToolsContour2Poly","ksu tools \'RF PolyLined Sketch\'\nSelection\'s Shapes to PolyLine Sketch")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_CreatePolyline-RF.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def __init__(self):
        self.obj = None
        self.sub = []
        self.active = False

    def IsActive(self):
        if bool(FreeCADGui.Selection.getSelection()) is False:
            return False
        return True
        
    def Activated(self):
        #import segments2poly
        #import wires2poly
        import Draft
        doc=FreeCAD.ActiveDocument
        docG = FreeCADGui.ActiveDocument
        selEx=FreeCADGui.Selection.getSelectionEx()
        dwglines =[]
        dqd = 0.01 #discretize(QuasiDeflection=d) => gives a list of points with a maximum deflection 'd' to the edge (faster)
        class XYline:
            def __init__(self, xs, ys, xe, ye):
                self.start = [xs, ys]
                self.end   = [xe, ye]
        if len (selEx) > 0:
            doc.openTransaction('e2skd')
            if len(selEx)>1:
                mFuseNm = fuse_objs(selEx)
                FuseWires = FreeCAD.ActiveDocument.getObject(mFuseNm).Shape.Wires
                Vol = FreeCAD.ActiveDocument.getObject(mFuseNm).Shape.Volume
            else:
                FuseWires = FreeCAD.ActiveDocument.getObject(selEx[0].Object.Name).Shape.Wires
                Vol = FreeCAD.ActiveDocument.getObject(selEx[0].Object.Name).Shape.Volume
                mFuseNm = selEx[0].Object.Name
            if Vol == 0:
                EdgesContour = []
                idx2rmv = []
                for w in FuseWires:
                    for ew in w.Edges:
                        if 'Line object' in str(ew.Curve):
                            foundE = False
                            for i,e in enumerate (EdgesContour):
                                if (e.Vertexes[0].Point == ew.Vertexes[0].Point) and (e.Vertexes[1].Point == ew.Vertexes[1].Point):
                                #if (_Equal(e.start[0], ew.end[0]) and _Equal(e.start[1], ew.end[1])):
                                    foundE = True
                                    idx2rmv.append(i)
                                    #print('found edge',i)
                                #elif (_Equal(e.start[1], ew.end[0]) and _Equal(e.start[0], ew.end[1])):
                                elif (e.Vertexes[1].Point == ew.Vertexes[0].Point) and (e.Vertexes[0].Point == ew.Vertexes[1].Point):
                                    foundE = True
                                    idx2rmv.append(i)
                                    #print('found edge',i)
                            if foundE == False:
                                EdgesContour.append(ew)
                        else:
                            EdgesContour.append (ew)
                #print(len(EdgesContour))
                #print(idx2rmv,len(idx2rmv))
                EdgesContourCleaned = []
                for j,e in enumerate (EdgesContour):
                    if j not in idx2rmv:
                        EdgesContourCleaned.append (e)
                sk = Draft.makeSketch(EdgesContourCleaned, autoconstraints=True)
                sk.Label = 'Pads_Poly'
                if len(selEx)>1:
                    FreeCAD.ActiveDocument.removeObject(mFuseNm)
            else:
                FreeCAD.ActiveDocument.addObject('Part::Refine','Refined').Source=FreeCAD.ActiveDocument.getObject(mFuseNm)
                RefName = FreeCAD.ActiveDocument.ActiveObject.Name
                FreeCAD.ActiveDocument.recompute()
                sv0 = Draft.makeShape2DView(FreeCAD.ActiveDocument.getObject(RefName), FreeCAD.Vector(-0.0, -0.0, 1.0))
                FreeCAD.ActiveDocument.recompute()
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name,sv0.Name)
                sk = Draft.makeSketch(FreeCADGui.Selection.getSelection(), autoconstraints=True)
                sk.Label = 'Pads_Poly'
                if 1:
                    ### Begin command Std_Delete
                    FreeCAD.ActiveDocument.removeObject(RefName)
                    FreeCAD.ActiveDocument.removeObject(sv0.Name)
                    #FreeCAD.ActiveDocument.recompute()
                if len(selEx)>1:
                    FreeCAD.ActiveDocument.removeObject(mFuseNm)
            FreeCAD.ActiveDocument.recompute()
            #creating an edge ordered sketch
            sv0 = Draft.makeShape2DView(FreeCAD.ActiveDocument.getObject(sk.Name), FreeCAD.Vector(-0.0, -0.0, 1.0))
            FreeCAD.ActiveDocument.recompute()
            FreeCAD.ActiveDocument.removeObject(sk.Name)
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name,sv0.Name)
            sk = Draft.makeSketch(FreeCADGui.Selection.getSelection(), autoconstraints=True)
            FreeCADGui.ActiveDocument.getObject(sk.Name).LineColor = (1.000,1.000,1.000)
            FreeCADGui.ActiveDocument.getObject(sk.Name).PointColor = (1.000,1.000,1.000)
            FreeCAD.ActiveDocument.removeObject(sv0.Name)
            sk.Label = 'Pads_Poly'
            FreeCAD.ActiveDocument.recompute()
            
            
        doc.commitTransaction()
        msg=translate("ksu","""PolyLine Contour generated<br><br>""")
        msg+=translate("ksu","<b>For PolyLine Pads, please add \'circles\' inside each closed polyline</b><br>")
        info_msg(msg)
        #stop
        #FreeCAD.ActiveDocument.recompute()
#
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('ksuToolsContour2Poly',ksuToolsContour2Poly())
##
class ksuToolsMoveSketch:
    "ksu tools MoveSketch"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_Move.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsMoveSketch","Move Sketch") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsMoveSketch","ksu Move 2D Sketch")}
 
    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 0:
            return False
        else:
            return True

    def Activated(self):
        # do something here...
        sel=FreeCADGui.Selection.getSelection()
        if len (sel) == 1:
            doc = FreeCAD.ActiveDocument
            if 'Sketcher' in sel[0].TypeId:
                s = doc.getObject(sel[0].Name)
                offsetDlg = QtGui.QDialog()
                ui = Ui_Offset_value()
                ui.setupUi(offsetDlg)
                ui.offset_label.setText(translate("ksu","Select a Sketch and Parameters to<br>move the sketch.<br>Offset X:"))
                ui.lineEdit_offset.setText("10.0")
                ui.offset_label_2.setText("Offset Y [mm]:")
                ui.lineEdit_offset_2.setToolTip("Offset Y value [+/- mm]")
                ui.lineEdit_offset_2.setText("0.0")
                ui.checkBox.setText("reset Placement")
                ui.checkBox.setVisible(True)
                ui.checkBox.setChecked(False)
                ui.checkBox.setToolTip("reset Placement of Sketch,\nmoving the internal geometry\nignoring offset imput fields")
                reply=offsetDlg.exec_()
                skip=False
                if reply==1: # ok
                    if ui.checkBox.isChecked():
                        if s.Placement.Rotation == FreeCAD.Rotation(0.0,0.0,0.0,1.0):
                            offsetX=s.Placement.Base.x
                            offsetY=s.Placement.Base.y
                        else:
                            #print(s.Placement.Rotation)
                            print('available only on Angle (0,0,0)')
                            msg="""available only on Angle (0,0,0)"""
                            QtGui.QApplication.restoreOverrideCursor()
                            QtGui.QMessageBox.information(None,"Info ...",msg)
                            skip=True
                    else:
                        offsetX=float(ui.lineEdit_offset.text().replace(',','.'))
                        offsetY=float(ui.lineEdit_offset_2.text().replace(',','.'))
                    if not skip:
                        doc.openTransaction('moveSk')
                        n = doc.getObject(s.Name).GeometryCount
                        mv = []
                        for j in range (n):
                            mv.append(j)
                        doc.getObject(s.Name).addMove(mv, FreeCAD.Vector(offsetX, offsetY, 0))
                        if ui.checkBox.isChecked():
                            s.Placement.Base.x=0
                            s.Placement.Base.y=0
                        doc.recompute([s])
                        doc.commitTransaction()
                else:
                    print('Cancel')
            else:
                print('select a Sketch')
            #doc.recompute(None,True,True)
            #doc.abortTransaction()

FreeCADGui.addCommand('ksuToolsMoveSketch',ksuToolsMoveSketch())    
##
class ksuToolsOffset2D:
    "ksu tools Offset2D"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Offset2D.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsOffset2D","Offset 2D") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsOffset2D","ksu Offset 2D object")}
 
    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 0:
            return False
        else:
            return True

    def Activated(self):
        # do something here...
        sel=FreeCADGui.Selection.getSelection()
        if len (sel) == 1:
            doc = FreeCAD.ActiveDocument
            offsetDlg = QtGui.QDialog()
            ui = Ui_Offset_value()
            ui.setupUi(offsetDlg)
            ui.lineEdit_offset.setText("-1.0")
            ui.offset_label_2.setVisible(False)
            ui.lineEdit_offset_2.setVisible(False)
            reply=offsetDlg.exec_()
            if reply==1: # ok
                offset=float(ui.lineEdit_offset.text().replace(',','.'))
                if ui.checkBox.isChecked():
                    offset_method = 'Arc'
                else:
                    offset_method = 'Intersection'
                doc.openTransaction('off2D')
                f = doc.addObject("Part::Offset2D", "Offset2D")
                f.Source = sel[0] #some object
                f.Value = offset
                f.Join=offset_method
                doc.ActiveObject.ViewObject.LineColor = (0.00,0.0,1.0)
                doc.ActiveObject.ViewObject.PointColor = (0.00,0.0,1.0)
                sel[0].ViewObject.Visibility = False
                doc.commitTransaction()
                doc.recompute([f])
            else:
                print('Cancel')
            #doc.recompute(None,True,True)
            #doc.abortTransaction()

FreeCADGui.addCommand('ksuToolsOffset2D',ksuToolsOffset2D())    
##
class ksuToolsExtrude:
    "ksu tools Extrude Selection"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsExtrude","ksu tools \'Extrude\'\nExtrude selection")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Part_Extrude.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def __init__(self):
        self.obj = None
        self.sub = []
        self.active = False

    def IsActive(self):
        if bool(FreeCADGui.Selection.getSelection()) is False:
            return False
        return True
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()[0]
        FreeCADGui.runCommand('Part_Extrude',0)

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('ksuToolsExtrude',ksuToolsExtrude())
##

class ksuToolsSkValidate:
    "ksu tools Sketcher Validate Selection"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsSkValidate","ksu tools \'Sketcher Validate\'\nValidate selected Sketch")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_Validate.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def __init__(self):
        self.obj = None
        self.sub = []
        self.active = False

    def IsActive(self):
        if bool(FreeCADGui.Selection.getSelection()) is False:
            return False
        return True
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()[0]
        FreeCADGui.runCommand('Sketcher_ValidateSketch',0)

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('ksuToolsSkValidate',ksuToolsSkValidate())
##

class ksuToolsOpenBoard:
    "ksu tools Open Board object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importBoard.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsOpenBoard","Load Board") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsOpenBoard","ksu Load KiCad PCB Board and Parts")}
 
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
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsLoadFootprint","Load FootPrint") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsLoadFootprint","ksu Load KiCad PCB FootPrint")}
 
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
        if 1: #reload_Gui:
            reload_lib( kicadStepUptools )
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.KSUWidget.activateWindow()
        kicadStepUptools.KSUWidget.show()
        kicadStepUptools.KSUWidget.raise_()
        kicadStepUptools.onLoadFootprint()

FreeCADGui.addCommand('ksuToolsLoadFootprint',ksuToolsLoadFootprint())
##

class ksuToolsExportModel:
    "ksu tools Export Model to KiCad object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'export3DModel.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsExportModel","Export 3D Model") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsExportModel","ksu Export 3D Model to KiCad")}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        # import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        #if reload_Gui:
        #    reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
      ##evaluate to read cfg and get materials value???
      ##or made something as in load board
        #ini_content=kicadStepUptools.cfg_read_all()
        if FreeCAD.ActiveDocument.FileName == "":
            msg="""please <b>save</b> your job file before exporting."""
            QtGui.QApplication.restoreOverrideCursor()
            QtGui.QMessageBox.information(None,"Info ...",msg)
            FreeCADGui.SendMsgToActiveView("Save")
        
        from kicadStepUptools import routineScaleVRML
        if reload_Gui:
            reload_lib( kicadStepUptools )
        routineScaleVRML()
        ## kicadStepUptools.routineScaleVRML()
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
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsImport3DStep","Import 3D Step") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsImport3DStep","ksu Import 3D Step Model")}
 
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
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsExport3DStep","Export 3D to Step") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsExport3DStep","ksu Export selected objects to Step Model")}
 
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
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsMakeUnion","Make Union") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsMakeUnion","ksu Make a Union of selected objects")}
 
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
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsMakeCompound","Make Compound") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsMakeCompound","ksu Make a Compound of selected objects")}
 
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
    "ksu tools Push Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_Rectangle.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsPushPCB","Push Sketch to PCB") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsPushPCB","ksu Push Sketch to PCB Edge")}
 
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
        sel = FreeCADGui.Selection.getSelection()
        if len (sel) ==1:
            if 'Sketcher' in sel[0].TypeId:
                #FreeCADGui.ActiveDocument.ActiveView.setCameraOrientation(sel[0].Placement.Rotation)
                #FreeCAD.ActiveDocument.recompute(None,True,True)
                FreeCAD.ActiveDocument.openTransaction('pushpcb')
                from pivy import coin
                print('getting camera view')
                pcam = FreeCADGui.ActiveDocument.ActiveView.getCamera()
                # 
                sketch = sel[0]
                rot = sketch.getGlobalPlacement().Rotation
                cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
                cam.orientation.setValue(coin.SbVec3f(rot.Axis.x, rot.Axis.y, rot.Axis.z), rot.Angle)
                FreeCADGui.ActiveDocument.ActiveView.fitAll()
                print('evaluate to recompute')
                ## s = sel[0].Shape
                ## sk = Draft.make_sketch(s.Edges, autoconstraints=True)
                kicadStepUptools.sanitizeSketch(sketch.Name)
                FreeCAD.ActiveDocument.recompute()
                sk = Draft.make_sketch(sketch, autoconstraints=True)
                sk_obj = FreeCAD.ActiveDocument.ActiveObject
                FreeCAD.ActiveDocument.recompute()
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(sk_obj)
                FreeCADGui.ActiveDocument.ActiveView.viewTop()
                sel[0].ViewObject.Visibility = False
                FreeCADGui.ActiveDocument.ActiveView.fitAll()
                # print('evaluate to recompute')
                # FreeCAD.ActiveDocument.recompute()
                # print(sel[0].Label)
                
                # tol = 0.0001
                # constr = 'coincident'
                # add_constraints(sk_obj.Name, tol, constr)
                # FreeCAD.ActiveDocument.recompute(None,True,True)
                FreeCAD.ActiveDocument.recompute() #we must recompute first
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(sk_obj)
                kicadStepUptools.PushPCB()
                FreeCAD.ActiveDocument.removeObject(sk_obj.Name)
                print('restoring cam view')
                FreeCADGui.ActiveDocument.ActiveView.setCamera(pcam)
                print('restoring sk visibility')
                sel[0].ViewObject.Visibility = True
                # FreeCADGui.ActiveDocument.ActiveView.setCamera(pcam)
                FreeCAD.ActiveDocument.commitTransaction()
                FreeCADGui.runCommand('Std_Undo',0)
            else:
                msg="""select one Sketch to be pushed to kicad board!"""
                FreeCAD.Console.PrintError(msg)
                FreeCAD.Console.PrintWarning('\n')
                kicadStepUptools.say_warning(msg)
        else:
            msg="""select one Sketch to be pushed to kicad board!"""
            FreeCAD.Console.PrintError(msg)
            FreeCAD.Console.PrintWarning('\n')
            kicadStepUptools.say_warning(msg)
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools


FreeCADGui.addCommand('ksuToolsPushPCB',ksuToolsPushPCB())
##
class ksuToolsPullPCB:
    "ksu tools Pull Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_Pull.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsPullPCB","Pull Sketch from PCB") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsPullPCB","ksu Pull Sketch from PCB Edge")}
 
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
        kicadStepUptools.PullPCB()
        #FreeCAD.ActiveDocument.commitTransaction()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools


FreeCADGui.addCommand('ksuToolsPullPCB',ksuToolsPullPCB())
##

class ksuToolsPushMoved:
    "ksu tools Push 3D moved model"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'PushMoved.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsPushMoved","Push 3D moved model(s) to PCB") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsPushMoved","ksu Push 3D moved model(s) to PCB")}
 
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
        kicadStepUptools.PushMoved()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools

FreeCADGui.addCommand('ksuToolsPushMoved',ksuToolsPushMoved())
##
class ksuToolsPullMoved:
    "ksu tools Pull 3D model placement from PCB"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'PullMoved.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsPullMoved","Pull 3D model(s) placement from PCB") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsPullMoved","ksu Pull 3D model(s) placement from PCB")}
 
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
        kicadStepUptools.PullMoved()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()

        #onPushPCB()
        #import kicadStepUptools

FreeCADGui.addCommand('ksuToolsPullMoved',ksuToolsPullMoved())
##
class ksuAsm2Part:
    "ksu tools Push/Pull 3D moved model"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Assembly_To_Part.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuAsm2Part","Convert an Assembly (A3) to Part hierarchy") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuAsm2Part","ksu Convert an Assembly (A3) to Part hierarchy")}
 
    def IsActive(self):
        import FreeCADGui
        #if a3:
        if 'LinkView' in dir(FreeCADGui): #pre a3 Link3 merge
            return True
        else:
            return False
 
    def Activated(self):
        # do something here...
        # import kicadStepUptools
        # if reload_Gui:
        #     reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        #kicadStepUptools.Asm2Part()
        #Asm2Part()
        import FreeCAD, FreeCADGui, Part
        def Asm2Part(parentObj=None,doc=None,subname=''):
            if doc is None:
                # 'doc' allows you to copy object into another document.
                # If not give, then use the current document.
                doc = FreeCAD.ActiveDocument
            if not parentObj:
                # If no object is given, then obtain selection from all opened document
                parentObj = []
                for sel in FreeCADGui.Selection.getSelectionEx('*'):
                    parentObj.append(sel.Object)
                if not parentObj:
                    return
            if isinstance(parentObj,(tuple,list)):
                if len(parentObj) == 1:
                    copy = Asm2Part(parentObj[0],doc)
                else:
                    part = doc.addObject('App::Part','Part')
                    for o in parentObj:
                        copy = Asm2Part(o,doc)
                        if copy:
                            part.addObject(copy)
                    copy = part
                if copy:
                    FreeCADGui.SendMsgToActiveView("ViewFit")
                    copy.recompute(True)
                return copy
        
            obj,matrix = parentObj.getSubObject(subname,1,FreeCAD.Matrix(),not subname)
            if not obj:
                return
            # getSubObjects() is the API for getting child of a group. It returns a list
            # of subnames, and the subname inside may contain more than one levels of
            # hierarchy. Assembly uses this API to skip hierarchy to PartGroup.
            subs = obj.getSubObjects()
            if not subs:
                # Non group object will return empty subs
                shape = Part.getShape(obj,transform=False)
                if shape.isNull():
                    return
                shape.transformShape(matrix,False,True)
                copy = doc.addObject('Part::Feature',obj.Name)
                copy.Label = obj.Label
                copy.Shape = shape
                if hasattr (copy.ViewObject,"mapShapeColors"):  # available on asm3 branch
                    copy.ViewObject.mapShapeColors(obj.Document)
                return copy
        
            part = doc.addObject('App::Part',obj.Name)
            part.Label = obj.Label
            part.Placement = FreeCAD.Placement(matrix)
            for sub in subs:
                sobj,parent,childName,_ = obj.resolve(sub)
                if not sobj:
                    continue
                copy = Asm2Part(obj,doc,sub)
                if not copy:
                    continue
                vis = parent.isElementVisible(childName)
                if vis < 0:
                    copy.Visibility = sobj.Visibility
                else:
                    copy.Visibility = vis>0
                part.addObject(copy)
            return part
        CopyOnNewDoc=True
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 1:
            if 'App::LinkGroup' in sel[0].Object.TypeId:
                if CopyOnNewDoc:
                    doc_base=FreeCAD.ActiveDocument
                    doc1 = FreeCAD.newDocument(doc_base.Name)
                    doc1_Name = FreeCAD.ActiveDocument.Name
                    FreeCAD.setActiveDocument(doc_base.Name)
                    #sel = FreeCADGui.Selection.getSelectionEx()
                    parentObj=[]
                    parentObj.append(sel[0].Object)
                    Asm2Part(parentObj,doc1)
                    FreeCAD.setActiveDocument(doc1_Name)
                else:
                    Asm2Part()
                if FreeCAD.ActiveDocument is not None:
                    FreeCADGui.SendMsgToActiveView("ViewFit")
            else:
                FreeCAD.Console.PrintWarning("select one Assembly to convert it to Part hierarchy")
                FreeCAD.Console.PrintWarning('\n')
                msg="""<b>select one Assembly to convert it to Part hierarchy</b>"""
                msg1="Warning ..."
                QtGui.QApplication.restoreOverrideCursor()
                #RotateXYZGuiClass().setGeometry(25, 250, 500, 500)
                diag = QtGui.QMessageBox(QtGui.QMessageBox.Icon.Warning,
                                        msg1,
                                        msg)
                diag.setWindowModality(QtCore.Qt.ApplicationModal)
                diag.exec_()
        else:
            FreeCAD.Console.PrintWarning("select one Assembly to convert it to Part hierarchy")
            FreeCAD.Console.PrintWarning('\n')
            msg="""<b>select one Assembly to convert it to Part hierarchy</b>"""
            msg1="Warning ..."
            QtGui.QApplication.restoreOverrideCursor()
            #RotateXYZGuiClass().setGeometry(25, 250, 500, 500)
            diag = QtGui.QMessageBox(QtGui.QMessageBox.Icon.Warning,
                                    msg1,
                                    msg)
            diag.setWindowModality(QtCore.Qt.ApplicationModal)
            diag.exec_()

FreeCADGui.addCommand('ksuAsm2Part',ksuAsm2Part())

##
class ksuToolsSync3DModels:
    "ksu tools Push/Pull 3D moved model"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sync3Dmodels.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsSync3DModels","Sync 3D model(s) Ref & TimeStamps with PCB") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsSync3DModels","ksu Sync 3D model(s) Ref & TimeStamps\nof the Selected 3D model with kicad PCB")}
 
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
        kicadStepUptools.Sync3DModel()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools

FreeCADGui.addCommand('ksuToolsSync3DModels',ksuToolsSync3DModels())
##
##
class ksuToolsGeneratePositions:
    "ksu tools Generate 3D models Positions"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'File_Positions.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsGeneratePositions","tools Generate 3D models Positions") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsGeneratePositions","ksu Generate 3D models Positions\nData for Active Document\n[MCAD Synchronize]")}
 
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        #import kicadStepUptools
        #if reload_Gui:
        #    reload_lib( kicadStepUptools )
        import exchangePositions;reload_lib(exchangePositions)
        exchangePositions.expPos()
        

FreeCADGui.addCommand('ksuToolsGeneratePositions',ksuToolsGeneratePositions())
##
class ksuToolsComparePositions:
    "ksu tools Compare 3D models Positions"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Compare_Positions.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsComparePositions","tools Compare 3D models Positions") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsComparePositions","ksu Compare 3D models Positions\nData with the Active Document\n[MCAD Synchronize]")}
 
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import exchangePositions;reload_lib(exchangePositions)
        exchangePositions.cmpPos()
        

FreeCADGui.addCommand('ksuToolsComparePositions',ksuToolsComparePositions())
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
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsCollisions","Check Collisions") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsCollisions","ksu Check Collisions and Interferences")}
 
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
        FreeCAD.ActiveDocument.openTransaction('collisions')
        kicadStepUptools.routineCollisions()
        FreeCAD.ActiveDocument.commitTransaction()

FreeCADGui.addCommand('ksuToolsCollisions',ksuToolsCollisions())
##

class ksuTools3D2D:
    "ksu tools 3D to 2D object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , '3Dto2D.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuTools3D2D","3D to 2D") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuTools3D2D","ksu 3D object to 2D projection")}
 
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
                new_sks = []
                for o in objs:
                    Draft.makeShape2DView(o,vec)
                    new_sks.append(FreeCAD.ActiveDocument.ActiveObject)
                FreeCAD.ActiveDocument.recompute()
                for s in new_sks:
                    FreeCADGui.ActiveDocument.getObject(s.Name).LineColor = (1.00,1.00,1.00)
                    FreeCADGui.ActiveDocument.getObject(s.Name).PointColor = (1.00,1.00,1.00)
            else:
                reply = QtGui.QMessageBox.information(None,"Warning", "select something\nto project it to a 2D shape in the document")
                FreeCAD.Console.PrintError('select something\nto project it to a 2D shape in the document\n')
        else:
            reply = QtGui.QMessageBox.information(None,"Warning", "select something\nto project it to a 2D shape in the document")
            FreeCAD.Console.PrintError('select something\nto project it to a 2D shape in the document\n')
#

FreeCADGui.addCommand('ksuTools3D2D',ksuTools3D2D())
##
class ksuToolsTurnTable:
    "ksu tools TurnTable"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'texture_turntable.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsTurnTable","TurnTable") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsTurnTable","ksu TurnTable")}
 
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
 
    def Activated(self):
        # do something here...
        # https://forum.freecadweb.org/viewtopic.php?f=3&t=28795
        
        ## references
        # My 2 favorite docs about coin are :
        # http://www-evasion.imag.fr/~Francois.Fa ... index.html
        # https://grey.colorado.edu/coin3d/annotated.html
        
        imgfilename = os.path.join( ksuWB_icons_path , '../textures/infinite_reflection_blur.png')
        paramGet = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View")
        #old_AutoRotation = paramGet.GetBool("UseAutoRotation")
        #print(old_AutoRotation);print(paramGet.GetBool("UseAutoRotation"))
        paramGet.SetBool("UseAutoRotation",1)
        sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
        tex = sg.getByName("myTexture")
        tc = sg.getByName("myTextCoord")
        if tex: # remove existing
            sg.removeChild(tex)
        else: # or insert a new one
            tex =  coin.SoTexture2()
            tex.setName("myTexture")
            #jpgfilename = QtGui.QFileDialog.getOpenFileName(QtGui.qApp.activeWindow(),'Open image file','*.jpg')
            #tex.filename = str(jpgfilename[0])
            #print(str(jpgfilename[0]))
            tex.filename = str(imgfilename)
            #print (str(imgfilename))
            sg.insertChild(tex,1)
            FreeCADGui.ActiveDocument.ActiveView.startAnimating(0,1,0,0.2)
        if tc:
            sg.removeChild(tc)
            FreeCADGui.ActiveDocument.ActiveView.stopAnimating()
            # uar = 0 if (old_AutoRotation) else 1
            #if (old_AutoRotation):
            #    uar = 1 
            #else:
            #    uar = 0
            #paramGet.SetBool("UseAutoRotation",uar)
            #print(old_AutoRotation);print (uar);print(paramGet.GetBool("UseAutoRotation"))
        else:
            tc = coin.SoTextureCoordinateEnvironment()
            tc.setName("myTextCoord")
            sg.insertChild(tc,2)
        

FreeCADGui.addCommand('ksuToolsTurnTable',ksuToolsTurnTable())
##

class ksuToolsConstrainator:
    "ksu tools Constraint Sketch"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_LockAll.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsTurnTable","Constrain a Sketch") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsTurnTable","ksu Fix & auto Constrain a Sketch")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        sel = FreeCADGui.Selection.getSelection()
        if len(sel)==1:    
            if sel[0].TypeId == 'Sketcher::SketchObject' and len(sel)==1:
                CDialog = QtGui.QDialog()
                ui = Ui_CDialog()
                ui.setupUi(CDialog)
                CDialog.setWindowTitle("Sketch Constrainator")
                reply=CDialog.exec_()
                if reply==1:
                    FreeCAD.ActiveDocument.openTransaction('Constrainator')
                    dialog_values = (ui.return_strings()) # window is value from edit field
                    #print (dialog_values)
                    for i,dv in enumerate (dialog_values): #py3 compatibility
                        if i == 0:
                            tol = float(dv)
                            if tol <= 0:
                                tol = 0.01
                        if i == 1:
                            if 'True' in dv:
                                constr = 'all'
                            else:
                                constr = 'coincident'
                        if i ==2:
                            if 'True' in dv:
                                rmvXG = True
                            else:
                                rmvXG = False
                    if rmvXG:
                        sanitizeSkBsp(sel[0].Name, tol)
                    add_constraints(sel[0].Name, tol, constr)
                    skt = FreeCAD.ActiveDocument.getObject(sel[0].Name)
                    if hasattr(skt, 'OpenVertices'):
                        openVtxs = skt.OpenVertices
                        add_points = True
                        if len(openVtxs) >0:
                            FreeCAD.Console.PrintError("Open Vertexes found.\n")
                            FreeCAD.Console.PrintWarning(str(openVtxs)+'\n')
                            msg = """Open Vertexes found.<br>"""+str(openVtxs)
                            reply = QtGui.QMessageBox.information(None,"info", msg)
                        if add_points:
                            for v in openVtxs:
                                FreeCAD.ActiveDocument.addObject('PartDesign::Point','DatumPoint')
                                dp = FreeCAD.ActiveDocument.ActiveObject
                                dp.Placement = FreeCAD.Placement (FreeCAD.Vector(v[0],v[1],0), FreeCAD.Rotation(0,0,0), FreeCAD.Vector(0,0,0))
                                dp.Label = 'OpenVertexPointer'
                    FreeCAD.ActiveDocument.commitTransaction()
            else:
                reply = QtGui.QMessageBox.information(None,"Warning", "select a Sketch to be Fix & Constrained")
                FreeCAD.Console.PrintError('select a Sketch to be Fix & Constrained\n')
        else:
            reply = QtGui.QMessageBox.information(None,"Warning", "select ONE Sketch to be Fix & Constrained")
            FreeCAD.Console.PrintError('select ONE Sketch to be Fix & Constrained\n')
    

FreeCADGui.addCommand('ksuToolsConstrainator',ksuToolsConstrainator())
##
class ksuToolsDiscretize:
    "ksu tools Discretize"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Discretize.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsDiscretize","Discretize") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsDiscretize","ksu Discretize a shape/outline to a Sketch")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) != 1:
            reply = QtGui.QMessageBox.information(None,"Warning", "select one single object to be discretized")
            FreeCAD.Console.PrintError('select one single object to be discretized\n')
        else:
            shapes = []
            for selobj in sel:
                for e in selobj.Shape.Edges:
                    # if not hasattr(e.Curve,'Radius'):
                    if not e.Closed:  # Arc and not Circle
                        shapes.append(Part.makePolygon(e.discretize(QuasiDeflection=q_deflection)))
                    elif e.Curve.TypeId == 'Part::GeomEllipse':
                        shapes.append(Part.makePolygon(e.discretize(QuasiDeflection=q_deflection)))
                    else:
                        shapes.append(Part.Wire(e))
                    #sd=e.copy().discretize(QuasiDeflection=dqd)    
            Draft.makeSketch(shapes)
            sk_d = FreeCAD.ActiveDocument.ActiveObject
            if sk_d is not None:
                FreeCADGui.ActiveDocument.getObject(sk_d.Name).LineColor = (1.00,1.00,1.00)
                FreeCADGui.ActiveDocument.getObject(sk_d.Name).PointColor = (1.00,1.00,1.00)
                max_geo_admitted = 1500 # after this number, no recompute is applied
                if len (sk_d.Geometry) < max_geo_admitted:
                    FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand('ksuToolsDiscretize',ksuToolsDiscretize())
##
##
class ksuToolsEdges2Sketch:
    "ksu tools edge to sketch"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Edges2Sketch.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsEdges2Sketch","Edges to Sketch") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsEdges2Sketch","ksu Select coplanar edge(s) or Face(s) or \na single Vertex of a coplanar outline \nto get a corresponding Sketch")}
 
    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 0:
            return False
        else:
            return True
 
    def Activated(self):
        # do something here...
        ksu_edges2sketch()
        
FreeCADGui.addCommand('ksuToolsEdges2Sketch',ksuToolsEdges2Sketch())
##

class ksuToolsResetPartPlacement:
    "ksu tools Reset PartPlacement"
    #####################################
    # Copyright (c) openBrain 2019
    # Licensed under LGPL v2
    #
    # This macro will reset position of all part containers to document origin while keeping the absolute object positions
    # __Web__ = 'https://www.freecadweb.org/wiki/Macro_PlacementAbsolufy'
    # Version history :
    # *0.1 : alpha release, almost no test performed
    # *0.2 : some typo improvement + commenting for official PR
    #
    #####################################
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'resetPartPlacement.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsResetPartPlacement","Reset Part Placement") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsResetPartPlacement","ksu Reset Placement for all Part containers in selection")}
    def getLinkGlobalPlacement(self,ob):
        # print(ob.Name,'Link object')
        # FreeCAD.Console.PrintMessage(ob.Parents)
        # FreeCAD.Console.PrintWarning(ob.Parents[0][0].Name+' '+ob.Parents[0][1])
        # FreeCAD.Console.PrintWarning(Part.getShape(ob.Parents[0][0],ob.Parents[0][1]).Placement)
        # return ob.Label
        return Part.getShape(ob.Parents[0][0],ob.Parents[0][1]).Placement
    #
    def Activated(self):        
        doc = FreeCAD.ActiveDocument
        found_kSU_PCB = False
        if doc is None:
            FreeCAD.Console.Print("No Active Document found")
            return
        else:
            currState = {} #initialize a dictionary to store current object placements
            sel = FreeCADGui.Selection.getSelection()
            if sel[0].Placement != FreeCAD.Placement(FreeCAD.Vector(0,0,0),FreeCAD.Rotation(0,0,0)):
                doc.openTransaction("Absolufy-kSU") #open a transaction for undo management
                if sel[0].TypeId == 'App::Part':
                    # https://forum.freecad.org/viewtopic.php?p=461588#p461588
                    # print('before',sel[0].Placement)
                    center = sel[0].Shape.BoundBox.Center
                    # using a temporary shape for moving placement
                    point = FreeCAD.ActiveDocument.addObject("Part::Vertex", "refPoint")
                    point.Placement = sel[0].Placement
                    point.Placement.move(-center)
                    # cent_Placement=sel[0].Placement
                    # cent_Placement.move(-center)
                    # print('after',sel[0].Placement)
                    for obj in sel[0].OutList: ## App.ActiveDocument.Objects: #going through active document objects
                        if obj.TypeId == 'App::Part' and ('Board_Geoms_' in obj.Label or 'Step_Models_' in obj.Label or 'Step_Virtual_Models_' in obj.Label):
                            # print (obj.Label)
                            comp_plc = obj.Placement.multiply(point.Placement) #.inverse()) #sel[0].Placement.inverse()
                            ## comp_plc = obj.Placement.multiply(cent_Placement) #.inverse()) #sel[0].Placement.inverse()
                            # comp_plc = obj.Placement.multiply(sel[0].Placement) #.inverse()) #sel[0].Placement.inverse()
                            obj.Placement=comp_plc
                            #sel[0].Placement.move(center)
                            obj.Placement.move(center)
                            found_kSU_PCB = True
                    if found_kSU_PCB:
                        print('applyied reset Part Placement on kSU pcb sub Parts')
                        sel[0].Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0),FreeCAD.Rotation(0,0,0)) #reset its placement to global document origin
                    FreeCAD.ActiveDocument.removeObject(point.Name)
                if not found_kSU_PCB:
                    for obj in sel: ## App.ActiveDocument.Objects: #going through active document objects
                        if "Placement" in obj.PropertiesList and obj.TypeId != 'Sketcher::SketchObject' \
                        and 'body object' not in str(obj.InList): #if object has a Placement property
                            #FreeCAD.Console.PrintWarning(obj.TypeId)
                            if hasattr(obj,'getGlobalPlacement'):
                                currState[obj] = obj.getGlobalPlacement() #store the object pointer with its global placement
                            #elif obj.TypeId == 'App::Link':
                            #    obj.getLinkGlobalPlacement()
                        for o in obj.OutListRecursive:
                            if "Placement" in o.PropertiesList and o.TypeId != 'Sketcher::SketchObject' \
                            and 'body object' not in str(o.InList): #if object has a Placement property
                                #FreeCAD.Console.PrintWarning(o.TypeId)
                                if hasattr(o,'getGlobalPlacement'):
                                    currState[o] = o.getGlobalPlacement() #store the object pointer with its global placement
                                elif o.TypeId == 'App::Link':
                                    plc = Part.getShape(o.Parents[0][0],o.Parents[0][1]).Placement #getLinkGlobalPlacement(o)
                                    # print(o.Label+' App::Link')
                                    # print(plc)
                                    #pp.inverse().multiply(plp)
                                    if len(o.OutList) == 1:
                                        if 'Part object' in str(o.OutList[0]): #Link Part container
                                            #print(o.Parents[0][0].Label+' Part-base calc plac',o.Parents[0][0].Placement)
                                            # print(o.OutList[0].Label+' Part-base calc plac',o.OutList[0].Placement)
                                            # print(o.Label+' Part-App::Link plac',o.Placement)
                                            #comp_plc = o.Placement.multiply(o.Parents[0][0].Placement.inverse()) # plc.inverse().multiply(o.Placement) #o.Parents[0][0].Placement.inverse().multiply(o.Placement)
                                            comp_plc = o.Placement.multiply(o.OutList[0].Placement.inverse())
                                            # print(o.Label+' Part-App::Link calc plac',comp_plc)
                                            currState[o] = comp_plc
                                        else:
                                            currState[o] = plc
                    # FreeCAD.ActiveDocument.openTransaction("Absolufy") #open a transaction for undo management
                    for obj, plac in currState.items(): #going through all moveable objects
                        if obj.isDerivedFrom("App::Part"): #if object is a part container
                            obj.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0),FreeCAD.Rotation(0,0,0)) #reset its placement to global document origin
                        # or obj.isDerivedFrom("App::Link")
                        #elif len(obj.OutList) == 1:
                        #    if 'Part object' in str(obj.OutList[0]): #Link Part container
                        #        print(obj.Label+' Part-App::Link new plac',plac)
                        #        obj.Placement = plac
                        #        # obj.Placement = mainP_origP.inverse().multiply(plac)
                        #    else: #for all other objects Link obj
                        #        obj.Placement = plac
                        elif obj.TypeId[:5] == "App::" and obj.TypeId != 'App::Link': #if object is another App type (typically an origin axis or plane)
                            None #do nothing
                        else: #for all other objects Link obj
                            obj.Placement = plac
                        #  elif not(obj.isDerivedFrom("App::Link")):
                        #      obj.Placement = plac
                        #  else:
                        #      obj.Placement = sel[0].Placement.multiply(plac) #replace them at their global (absolute) placement
                            # if hasattr(obj, 'LinkedObject'):
                            #     print(obj.LinkedObject)
                            #     if 'Part::PartFeature' not in str(obj.LinkedObject):
                            #     # if obj.LinkedObject == 'Part::PartFeature':
                            #         print(obj.LinkedObject,'here')
                            #         obj.Placement = plac #replace them at their global (absolute) placement
                            #     else:
                            #         None
                    print('applyied reset Part Placement base')
                doc.commitTransaction() #commit transaction
                doc.recompute()
            else:
                FreeCAD.Console.PrintMessage("Placement already Zero\n")
        return

    def IsActive(self):
        import FreeCAD, FreeCADGui, Part
        doc = FreeCAD.activeDocument()
        if doc is None:
            return False
        else:
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) >1 or len(sel)==0:
                return False
            elif len(sel)==1:
                if hasattr(sel[0], 'TypeId'):
                    if (sel[0].TypeId) != 'App::Part':
                        return False
        return True
FreeCADGui.addCommand('ksuToolsResetPartPlacement',ksuToolsResetPartPlacement())
##

class ksuToolsResetPlacement:
    "ksu tools Reset Placement"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'resetPlacement.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsResetPlacement","Reset Placement") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsResetPlacement","ksu Reset Placement for a Shape")}
 
    def IsActive(self):
        doc = FreeCAD.activeDocument()
        if doc is None: return False
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) >1 or len(sel)==0:
            return False
        elif sel[0].TypeId == 'App::Part':
            return False
        return True
 
    def Activated(self):
        # do something here...
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) != 1:
            reply = QtGui.QMessageBox.information(None,"Warning", "select one single object to Reset its Placement")
            FreeCAD.Console.PrintError('select one single object to Reset its Placement\n')
        else:
            if sel[0].Placement != FreeCAD.Placement(FreeCAD.Vector(0,0,0),FreeCAD.Rotation(0,0,0)):
                FreeCAD.ActiveDocument.openTransaction("Absolufy") #open a transaction for undo management
                import kicadStepUptools
                FreeCAD.ActiveDocument.openTransaction('rst')
                kicadStepUptools.routineResetPlacement(keepWB=True)
                FreeCAD.ActiveDocument.commitTransaction()
            else:
                FreeCAD.Console.PrintMessage("Placement already Zero\n")
FreeCADGui.addCommand('ksuToolsResetPlacement',ksuToolsResetPlacement())
##

#####
class ksuTools2D2Sketch:
    "ksu tools 2D to Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , '2DtoSketch.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuTools2D2Sketch","2D to Sketch") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuTools2D2Sketch","ksu 2D object (or DXF) to Sketch")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            max_geo_admitted = 1500 # after this number, no recompute is applied
            try:
                edges=sum((obj.Shape.Edges for obj in \
                FreeCADGui.Selection.getSelection() if hasattr(obj,'Shape')),[])
                #for edge in edges:
                #    print "geomType ",DraftGeomUtils.geomType(edge)
                ##face = OpenSCAD2Dgeom.edgestofaces(edges)
                import kicadStepUptools
                if reload_Gui:
                    reload_lib( kicadStepUptools )
                #face = OpenSCAD2DgeomMau.edgestofaces(edges)
                FC_majorV=int(float(FreeCAD.Version()[0]))
                FC_minorV=int(float(FreeCAD.Version()[1]))
                using_draft_makeSketch=True
                faceobj=None
                if not using_draft_makeSketch or (FC_majorV==0 and FC_minorV<=16):
                    try:
                        faceobj=None
                        face = kicadStepUptools.OSCD2Dg_edgestofaces(edges,3 , kicadStepUptools.edge_tolerance)
                        face.check() # reports errors
                        face.fix(0,0,0)
                        faceobj = FreeCAD.ActiveDocument.addObject('Part::Feature',"Face")
                        faceobj.Label = "Face"
                        faceobj.Shape = face
                        for obj in FreeCADGui.Selection.getSelection():
                            FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                        FreeCAD.ActiveDocument.recompute()
                        wires,_faces = Draft.downgrade(faceobj,delete=True)
                    except:
                        import Draft
                        if faceobj is not None:
                            FreeCAD.ActiveDocument.removeObject(faceobj.Name)
                        sk = None
                        sk = Draft.makeSketch(FreeCADGui.Selection.getSelection(),autoconstraints=True)
                        if sk is None:
                            reply = QtGui.QMessageBox.information(None,"Warning", "Select edge elements to be converted to Sketch\nBSplines and Bezier curves are not supported by this tool")
                            FreeCAD.Console.PrintWarning("Select edge elements to be converted to Sketch\nBSplines and Bezier curves are not supported by this tool\n")
                            stop
                        sk.Label = "Sketch_converted"
                        sname=FreeCAD.ActiveDocument.ActiveObject.Name
                        using_draft_makeSketch=True
                        for obj in FreeCADGui.Selection.getSelection():
                            FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                    
                    if FC_majorV==0 and FC_minorV>=16:
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
                ##elif using_draft_makeSketch == False:
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
                            # Sketcher magic function :
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
                    elif FC_majorV==0 and FC_minorV>=16:
                        if len (newBSlEdges)>0:
                            sketch = FreeCAD.activeDocument().addObject('Sketcher::SketchObject','Sketch_conv')
                            sname = sketch.Name
                            FreeCAD.ActiveDocument.getObject(sname).Label="Sketch_converted"
                            for e in newBSlEdges:
                                # sk = FreeCAD.ActiveDocument.addObject('Sketcher::SketchObject','Sketch_bsp')
                                # sk.addGeometry(e.Curve, False)
                                sketch.addGeometry(e.Curve, False)
                                # Sketcher magic function :
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
                else:
                    import Draft
                    if faceobj is not None:
                        FreeCAD.ActiveDocument.removeObject(faceobj.Name)
                    sk = None
                    sk = Draft.makeSketch(FreeCADGui.Selection.getSelection(),autoconstraints=True)
                    if sk is None:
                        reply = QtGui.QMessageBox.information(None,"Warning", "Select edge elements to be converted to Sketch")
                        FreeCAD.Console.PrintWarning("Select edge elements to be converted to Sketch\n")
                        stop
                    sk.Label = "Sketch_converted"
                    sname=FreeCAD.ActiveDocument.ActiveObject.Name
                    FreeCAD.ActiveDocument.ActiveObject.ViewObject.LineColor = (1.00,1.00,1.00)
                    FreeCAD.ActiveDocument.ActiveObject.ViewObject.PointColor = (1.00,1.00,1.00)
                    for i,g in enumerate (sk.Geometry):
                        if 'BSplineCurve object' in str(g):
                            sk.exposeInternalGeometry(i)
                    using_draft_makeSketch=True
                    for obj in FreeCADGui.Selection.getSelection():
                        FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                    if len (sk.Geometry) < max_geo_admitted:
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
                     'MenuText': QT_TRANSLATE_NOOP("ksuTools2DtoFace","2D to Face") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuTools2DtoFace","ksu 2D object (or DXF) to Surface for extruding")}
 
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

class ksuToolsSimplifySketck:
    "ksu tools Simplify Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'SimplifySketch.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsSimplifySketck","Simplify Sketch") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsSimplifySketck","ksu Simplifying Sketch to Arcs and Lines")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if len(FreeCADGui.Selection.getSelection()):
            import kicadStepUptools
            if reload_Gui:
                reload_lib( kicadStepUptools )
            FreeCAD.Gui.activeDocument().activeView().viewTop()
            kicadStepUptools.simplify_sketch()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select ONE Sketch to be Simplified")
            FreeCAD.Console.PrintWarning("Select ONE Sketch to be Simplified\n")             

FreeCADGui.addCommand('ksuToolsSimplifySketck',ksuToolsSimplifySketck())
#####

class ksuToolsBsplineNormalize:
    "ksu tools Normalize Bspline for KiCAD format"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_BSplineNormalize.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsBsplineNormalize","Geo to Bspline") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsBsplineNormalize","ksu Convert Geometry to Bspline for KiCAD format")}
 
    def IsActive(self):
        return True
        #return False
 
    def Activated(self):
        # do something here...
        if len(FreeCADGui.Selection.getSelection()):
            import kicadStepUptools
            if reload_Gui:
                reload_lib( kicadStepUptools )
            kicadStepUptools.normalize_bsplines()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select ONE Sketch to be Normalized")
            FreeCAD.Console.PrintWarning("Select ONE Sketch to be Normalized\n")             

FreeCADGui.addCommand('ksuToolsBsplineNormalize',ksuToolsBsplineNormalize())

#####
class ksuToolsFootprintGen:
    "ksu tools Footprint generator object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'exportFootprint.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsFootprintGen","Footprint generator") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsFootprintGen","ksu Footprint editor and exporter")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            #for edge in edges:
            #    print "geomType ",DraftGeomUtils.geomType(edge)
            import kicadStepUptools
            if reload_Gui:
                reload_lib( kicadStepUptools )
            kicadStepUptools.PushFootprint()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select Group or Sketch/Text elements to be converted to KiCad Footprint")
            FreeCAD.Console.PrintWarning("Select Group or Sketch/Text elements to be converted to KiCad Footprint\n")             

FreeCADGui.addCommand('ksuToolsFootprintGen',ksuToolsFootprintGen())

#####

class ksuToolsStepImportModeSTD:
    "ksu tools full STEP Import Mode"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'ImportModeSTD.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsStepImportModeSTD","disable Full STEP Import Mode") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsStepImportModeSTD","ksu tools disable Full STEP Import Mode")}
 
    def IsActive(self):
        paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
        if not ReadShapeCompoundMode_status:
            return True
        else:
            return False

    def Activated(self):
        # do something here...
        ##ReadShapeCompoundMode
        paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
        #sayerr("checking ReadShapeCompoundMode")
        FreeCAD.Console.PrintWarning("ReadShapeCompoundMode status "+str(ReadShapeCompoundMode_status)+'\n')
        #if ReadShapeCompoundMode_status:
        #    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        #    paramGetVS.SetBool("ReadShapeCompoundMode",False)
        #    FreeCAD.Console.PrintWarning("disabling ReadShapeCompoundMode"+'\n')
        if not ReadShapeCompoundMode_status:
            paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
            paramGetVS.SetBool("ReadShapeCompoundMode",True)
            FreeCAD.Console.PrintError("enabling ReadShapeCompoundMode -> Simplified Mode"+'\n')

FreeCADGui.addCommand('ksuToolsStepImportModeSTD',ksuToolsStepImportModeSTD())
####

class ksuToolsStepImportModeComp:
    "ksu tools disable Simplified STEP Import Mode"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'ImportModeSimplified.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsStepImportModeComp","disable Simplified STEP Import Mode") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsStepImportModeComp","ksu tools disable Simplified STEP Import Mode")}
 
    def IsActive(self):
        paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
        if ReadShapeCompoundMode_status:
            return True
        else:
            return False

    def Activated(self):
        # do something here...
        ##ReadShapeCompoundMode
        paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
        #sayerr("checking ReadShapeCompoundMode")
        FreeCAD.Console.PrintWarning("ReadShapeCompoundMode status "+str(ReadShapeCompoundMode_status)+'\n')
        if ReadShapeCompoundMode_status:
            paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
            paramGetVS.SetBool("ReadShapeCompoundMode",False)
            FreeCAD.Console.PrintWarning("disabling ReadShapeCompoundMode"+'\n')
        #if not ReadShapeCompoundMode_status:
        #    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        #    paramGetVS.SetBool("ReadShapeCompoundMode",True)
        #    FreeCAD.Console.PrintError("enabling ReadShapeCompoundMode -> Simplified Mode"+'\n')

FreeCADGui.addCommand('ksuToolsStepImportModeComp',ksuToolsStepImportModeComp())

####
class ksuToolsCopyPlacement:
    "ksu tools Copy Placement"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Placement_Copy.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsCopyPlacement","Copy Placement 1st to 2nd") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsCopyPlacement","ksu tools Copy Placement 1st to 2nd")}
 
    def IsActive(self):
        return True

    def Activated(self):
        # do something here...
        def copy_placement(sel):
            if hasattr(sel[0],'Placement'):
                main_p=sel[0].Placement
            else:
                FreeCAD.Console.PrintWarning("select TWO objects to copy \'1st placement\' to \'2nd placement\'\n")
                return
            for o in sel:
                if hasattr(o,'Placement'):
                    o.Placement=main_p
        
        doc = FreeCADGui.ActiveDocument
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("Select at least two objects!\n")
            FreeCAD.Console.PrintMessage("all selected objects will receive first object placement\n")
        elif len(sel)<2:
            FreeCAD.Console.PrintWarning("Select at least two objects!\n")
            FreeCAD.Console.PrintMessage("all selected objects will receive first object placement\n")
        else:
            doc = FreeCAD.ActiveDocument
            doc.openTransaction("cpyPlacement")
            copy_placement(FreeCADGui.Selection.getSelection())
            doc.commitTransaction()
            FreeCAD.Console.PrintMessage("Placement copied\n")

FreeCADGui.addCommand('ksuToolsCopyPlacement',ksuToolsCopyPlacement())

####
class ksuToolsColoredClone:
    "ksu tools colored Clone object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'CloneYlw.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsColoredClone","Colored Clone") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsColoredClone","Colored Clone object")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            def mk_str(input):
                if (sys.version_info > (3, 0)):  #py3
                    if isinstance(input, str):
                        return input
                    else:
                        input =  input.encode('utf-8')
                        return input
                else:  #py2
                    if type(input) == unicode:
                        input =  input.encode('utf-8')
                        return input
                    else:
                        return input
            if len(sel) != 1:
                    msg="Select one object with Shape to be colored Cloned!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else: #sel[0].TypeId != 'PartDesign::Body'):
            
                obj_tocopy=sel[0]
                cp_label=mk_str(obj_tocopy.Label)+u'_cl'
                
                if hasattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name), "Shape"):
                    import Draft
                    newObj = Draft.make_clone(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name))
                    FreeCAD.ActiveDocument.recompute()
                    newObj.Label=cp_label
                    if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'ShapeColor'):# and ('Origin' not in FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).TypeId):
                        # if 'LinkView' in dir(FreeCADGui):
                        #     FreeCAD.ActiveDocument.ActiveObject.ViewObject.ShapeColor=getattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getLinkedObject(True).ViewObject,'ShapeColor',FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).ViewObject.ShapeColor)
                        #     FreeCAD.ActiveDocument.ActiveObject.ViewObject.LineColor=getattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getLinkedObject(True).ViewObject,'LineColor',FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).ViewObject.LineColor)
                        #else:
                        FreeCADGui.ActiveDocument.ActiveObject.ShapeColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).ShapeColor
                        if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'LineColor'):
                            FreeCADGui.ActiveDocument.ActiveObject.LineColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).LineColor
                            FreeCADGui.ActiveDocument.ActiveObject.PointColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).PointColor
                        if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'DiffuseColor'):
                            FreeCADGui.ActiveDocument.ActiveObject.DiffuseColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).DiffuseColor
                        if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'Transparency'):
                            FreeCADGui.ActiveDocument.ActiveObject.Transparency=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).Transparency
                    else:
                        FreeCAD.Console.PrintWarning('missing copy of color attributes')
                FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).Visibility = False
                    #FreeCAD.ActiveDocument.recompute()
                #else:
                #    FreeCAD.Console.PrintWarning("Select object with a \"Shape\" to be copied!\n")             
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one object with Shape to be cloned!")
            FreeCAD.Console.PrintWarning("Select one object with Shape to be cloned!\n")             

FreeCADGui.addCommand('ksuToolsColoredClone',ksuToolsColoredClone())

####
class ksuToolsColoredBinder:
    "ksu tools colored Binder object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'SubShapeBinderYlw.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsColoredBinder","Colored Binder") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsColoredBinder","Colored Binder object")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            def mk_str(input):
                if (sys.version_info > (3, 0)):  #py3
                    if isinstance(input, str):
                        return input
                    else:
                        input =  input.encode('utf-8')
                        return input
                else:  #py2
                    if type(input) == unicode:
                        input =  input.encode('utf-8')
                        return input
                    else:
                        return input
            if len(sel) != 1:
                    msg="Select one object with Shape to generate a colored Binder!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else: #sel[0].TypeId != 'PartDesign::Body'):
            
                obj_tocopy=sel[0]
                cp_label=mk_str(obj_tocopy.Label)+u'_bnd'
                
                if hasattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name), "Shape"):
                    import PartDesignGui
                    FreeCADGui.runCommand('PartDesign_SubShapeBinder')
                    # newObj = FreeCAD.ActiveDocument.addObject('PartDesign::SubShapeBinder',obj_tocopy.Name)
                    # newObj.Support = [obj_tocopy]
                    newObj = FreeCAD.ActiveDocument.ActiveObject
                    FreeCADGui.ActiveDocument.getObject(newObj.Name).DrawStyle = u"Dashed"
                    FreeCADGui.ActiveDocument.getObject(newObj.Name).DisplayMode = u"Wireframe"
                    FreeCAD.ActiveDocument.recompute()
                    newObj.Label=cp_label
                    if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'ShapeColor'):# and ('Origin' not in FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).TypeId):
                        # if 'LinkView' in dir(FreeCADGui):
                        #     FreeCAD.ActiveDocument.ActiveObject.ViewObject.ShapeColor=getattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getLinkedObject(True).ViewObject,'ShapeColor',FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).ViewObject.ShapeColor)
                        #     FreeCAD.ActiveDocument.ActiveObject.ViewObject.LineColor=getattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getLinkedObject(True).ViewObject,'LineColor',FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).ViewObject.LineColor)
                        #else:
                        FreeCADGui.ActiveDocument.ActiveObject.ShapeColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).ShapeColor
                        if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'LineColor'):
                            FreeCADGui.ActiveDocument.ActiveObject.LineColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).LineColor
                            FreeCADGui.ActiveDocument.ActiveObject.PointColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).PointColor
                        if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'DiffuseColor'):
                            FreeCADGui.ActiveDocument.ActiveObject.DiffuseColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).DiffuseColor
                        if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'Transparency'):
                            FreeCADGui.ActiveDocument.ActiveObject.Transparency=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).Transparency
                        else:
                            FreeCADGui.ActiveDocument.ActiveObject.Transparency=60
                    else:
                        FreeCAD.Console.PrintWarning('missing copy of color attributes')
                    #if hasattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name), "getGlobalPlacement"):
                    #    newObj.Placement = FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getGlobalPlacement()
                FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).Visibility = False
                    #FreeCAD.ActiveDocument.recompute()
                #else:
                #    FreeCAD.Console.PrintWarning("Select object with a \"Shape\" to be copied!\n")             
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one object with Shape to generate a colored Binder!")
            FreeCAD.Console.PrintWarning("Select one object with Shape to generate a colored Binder!\n")             

FreeCADGui.addCommand('ksuToolsColoredBinder',ksuToolsColoredBinder())

####
####
class ksuToolsReLinkBinder:
    "ksu tools Relink Binder object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'SubShapeBinderRelink.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsReLinkBinder","Relink Binder") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsReLinkBinder","Relink Binder object Select Binder and an Object to be linked")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            def mk_str(input):
                if (sys.version_info > (3, 0)):  #py3
                    if isinstance(input, str):
                        return input
                    else:
                        input =  input.encode('utf-8')
                        return input
                else:  #py2
                    if type(input) == unicode:
                        input =  input.encode('utf-8')
                        return input
                    else:
                        return input
            if len(sel) != 2:
                    msg="Select the Binder and one object with Shape to ReLink the Binder!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else: #sel[0].TypeId != 'PartDesign::Body'):
                selEx = FreeCADGui.Selection.getSelectionEx("", 0)
                binder=selEx[0]
                obj2link = selEx[1]
                #FreeCAD.Console.PrintMessage(obj2link.Object.Name+'.'+obj2link.SubElementNames[0]+'\n')
                if binder.Object.TypeId == 'PartDesign::SubShapeBinder' and hasattr(sel[1], "Shape"):
                # [(<Part object>, ('Part.Part001.Cylinder.',))]
                    #FreeCAD.Console.PrintMessage('here'+obj2link.Object.Name+'.'+obj2link.SubElementNames[0]+'\n')
                    binder.Object.BindMode = u"Synchronized"
                    binder.Object.Support = [(obj2link.Object,(obj2link.SubElementNames[0],))]
                    binder.Object.recompute(True)
                else:
                    msg="Select the Binder and one object with Shape to ReLink the Binder!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select the Binder and one object with Shape to ReLink the Binder!")
            FreeCAD.Console.PrintWarning("Select the Binder and one object with Shape to ReLink the Binder!\n")             

FreeCADGui.addCommand('ksuToolsReLinkBinder',ksuToolsReLinkBinder())

####
class ksuToolsUnion:
    "ksu tools Make Union objects"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Part-Fuse.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsUnion","Fuse objects") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsUnion","Make Union (Fuse) objects")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            def mk_str(input):
                if (sys.version_info > (3, 0)):  #py3
                    if isinstance(input, str):
                        return input
                    else:
                        input =  input.encode('utf-8')
                        return input
                else:  #py2
                    if type(input) == unicode:
                        input =  input.encode('utf-8')
                        return input
                    else:
                        return input
            ##
            if len(sel)<=1:
                    msg="Select at least two objects with Shape to be copied!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else: #sel[0].TypeId != 'PartDesign::Body'):
                FreeCAD.activeDocument().addObject("Part::MultiFuse","Fusion")
                Fusion = FreeCAD.activeDocument().ActiveObject
                Fusion.Shapes = sel
                FreeCAD.ActiveDocument.recompute()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select at least two objects with Shape to be copied!")
            FreeCAD.Console.PrintWarning("Select at least two objects with Shape to be copied!\n")             

FreeCADGui.addCommand('ksuToolsUnion',ksuToolsUnion())

####
class ksuToolsSimpleCopy:
    "ksu tools Simple Copy object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'simple_copy.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsSimpleCopy","Simple Copy") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsSimpleCopy","ksu Simple Copy object")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            def mk_str(input):
                if (sys.version_info > (3, 0)):  #py3
                    if isinstance(input, str):
                        return input
                    else:
                        input =  input.encode('utf-8')
                        return input
                else:  #py2
                    if type(input) == unicode:
                        input =  input.encode('utf-8')
                        return input
                    else:
                        return input
            ##
            if len(sel)<1:
                    msg="Select at least one object with Shape to be copied!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else: #sel[0].TypeId != 'PartDesign::Body'):
                for obj_tocopy in sel:
                #obj_tocopy=sel[0]
                    cp_label=mk_str(obj_tocopy.Label)+u'_sc'
                    if hasattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name), "Shape"):
                        FreeCAD.ActiveDocument.addObject('Part::Feature',cp_label).Shape=FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).Shape
                        newObj = FreeCAD.ActiveDocument.ActiveObject
                        newObjV = FreeCADGui.ActiveDocument.ActiveObject
                        newObj.Label=cp_label
                        #FreeCAD.Console.PrintMessage(obj_tocopy.Label);FreeCAD.Console.PrintMessage('\n')
                        #FreeCAD.Console.PrintMessage(obj_tocopy.TypeId)
                        #FreeCAD.Console.PrintMessage(obj_tocopy.OutList)
                        #FreeCAD.Console.PrintMessage(obj_tocopy.TypeId);FreeCAD.Console.PrintMessage('\n')
                        if obj_tocopy.TypeId == 'App::Part':
                            for subobj in obj_tocopy.OutList:
                                #FreeCAD.Console.PrintMessage(subobj.Label);FreeCAD.Console.PrintMessage('\n')
                                if hasattr(FreeCADGui.ActiveDocument.getObject(subobj.Name),'ShapeColor'):# and ('Origin' not in FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).TypeId):
                                    # if 'LinkView' in dir(FreeCADGui):
                                    #     FreeCAD.ActiveDocument.ActiveObject.ViewObject.ShapeColor=getattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getLinkedObject(True).ViewObject,'ShapeColor',FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).ViewObject.ShapeColor)
                                    #     FreeCAD.ActiveDocument.ActiveObject.ViewObject.LineColor=getattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getLinkedObject(True).ViewObject,'LineColor',FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).ViewObject.LineColor)
                                    #else:
                                    newObjV.ShapeColor=FreeCADGui.ActiveDocument.getObject(subobj.Name).ShapeColor
                                    #FreeCAD.Console.PrintMessage(subobj.Label);FreeCAD.Console.PrintMessage(' ShapeColor ' +str(FreeCADGui.ActiveDocument.getObject(subobj.Name).ShapeColor)+ '\n')
                                    if hasattr(FreeCADGui.ActiveDocument.getObject(subobj.Name),'LineColor'):
                                        #FreeCAD.Console.PrintMessage(subobj.Label);FreeCAD.Console.PrintMessage(' LineColor ' +str(FreeCADGui.ActiveDocument.getObject(subobj.Name).LineColor)+ '\n')
                                        newObjV.LineColor=FreeCADGui.ActiveDocument.getObject(subobj.Name).LineColor
                                        newObjV.PointColor=FreeCADGui.ActiveDocument.getObject(subobj.Name).PointColor
                                    if hasattr(FreeCADGui.ActiveDocument.getObject(subobj.Name),'DiffuseColor'):
                                        #FreeCAD.Console.PrintMessage(subobj.Label);FreeCAD.Console.PrintMessage(' DiffuseColor ' +str(FreeCADGui.ActiveDocument.getObject(subobj.Name).DiffuseColor)+ '\n')
                                        newObjV.DiffuseColor=FreeCADGui.ActiveDocument.getObject(subobj.Name).DiffuseColor
                                    if hasattr(FreeCADGui.ActiveDocument.getObject(subobj.Name),'Transparency'):
                                        #FreeCAD.Console.PrintMessage(subobj.Label);FreeCAD.Console.PrintMessage(' Transparency ' +str(FreeCADGui.ActiveDocument.getObject(subobj.Name).Transparency)+ '\n')
                                        newObjV.Transparency=FreeCADGui.ActiveDocument.getObject(subobj.Name).Transparency
                        elif hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'ShapeColor'):# and ('Origin' not in FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).TypeId):
                            # if 'LinkView' in dir(FreeCADGui):
                            #     FreeCAD.ActiveDocument.ActiveObject.ViewObject.ShapeColor=getattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getLinkedObject(True).ViewObject,'ShapeColor',FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).ViewObject.ShapeColor)
                            #     FreeCAD.ActiveDocument.ActiveObject.ViewObject.LineColor=getattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).getLinkedObject(True).ViewObject,'LineColor',FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).ViewObject.LineColor)
                            #else:
                            FreeCADGui.ActiveDocument.ActiveObject.ShapeColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).ShapeColor
                            if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'LineColor'):
                                FreeCADGui.ActiveDocument.ActiveObject.LineColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).LineColor
                                FreeCADGui.ActiveDocument.ActiveObject.PointColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).PointColor
                            if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'DiffuseColor'):
                                FreeCADGui.ActiveDocument.ActiveObject.DiffuseColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).DiffuseColor
                            if hasattr(FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name),'Transparency'):
                                FreeCADGui.ActiveDocument.ActiveObject.Transparency=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).Transparency
                        else:
                            FreeCAD.Console.PrintWarning('missing copy of color attributes')
                        FreeCAD.ActiveDocument.recompute()
                    #else:
                    #    FreeCAD.Console.PrintWarning("Select object with a \"Shape\" to be copied!\n")             
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select at least one object with Shape to be copied!")
            FreeCAD.Console.PrintWarning("Select at least one object with Shape to be copied!\n")             

FreeCADGui.addCommand('ksuToolsSimpleCopy',ksuToolsSimpleCopy())

#####
class ksuToolsDeepCopy:
    "ksu tools PartDN Copy object"

    __Name__ = 'Deep Copy'
    __Help__ = 'Select a part and launch'
    __Author__ = 'galou_breizh'

###
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'deep_copy.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsDeepCopy","PartDN Copy") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsDeepCopy","ksu PartDN Copy object\nwith relative placement\n[flattened model]")}
 
    def IsActive(self):
        if int(float(FreeCAD.Version()[0]))==0 and int(float(FreeCAD.Version()[1]))<=16: #active only for FC>0.16
            return False
        else:
            return True
 
    def Activated(self):
        # do something here...

        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()        
            if len(sel)!=1 and (sel[0].TypeId == 'App::Part' or sel[0].TypeId == 'PartDesign::Body'):
                msg="Select ONE Part Design Next object\nor one or more objects to be copied!\n"
                reply = QtGui.QMessageBox.information(None,"Warning", msg)
                FreeCAD.Console.PrintWarning(msg)             
            else:
                doc = FreeCAD.activeDocument()
                if sel[0].TypeId != 'App::Part' and sel[0].TypeId != 'PartDesign::Body':
                    for o in sel:
                        if o.TypeId != 'App::Part' and o.TypeId != 'PartDesign::Body':
                            copy_subobject(doc,o,'copy')
                else:
                    deep_copy(doc,'flat','copy')
                    FreeCADGui.ActiveDocument.getObject(sel[0].Name).Visibility=False
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select ONE Part Design Next object\nor one or more objects to be copied!")
            FreeCAD.Console.PrintWarning("Select ONE Part Design Next object\nor one or more objects to be copied!\n")             
        
FreeCADGui.addCommand('ksuToolsDeepCopy',ksuToolsDeepCopy())
#####
def mk_str_u(input):
    if (sys.version_info > (3, 0)):  #py3
        if isinstance(input, str):
            return input
        else:
            input =  input.encode('utf-8')
            return input
    else:  #py2
        if type(input) == unicode:
            input =  input.encode('utf-8')
            return input
        else:
            return input
###
make_compound = False

# import FreeCAD as app,FreeCADGui as gui

# from FreeCAD import app
# from FreeCAD import gui


def deep_copy(doc,compound='flat',suffix='(copy)'):
    #FreeCAD.Console.PrintMessage(compound)
    for sel_object in FreeCADGui.Selection.getSelectionEx():
        pName=deep_copy_part(doc, sel_object.Object, compound,suffix)
    return pName

def deep_copy_part(doc, part, compound='flat',suffix='(copy)'):
    if part.TypeId != 'App::Part' and part.TypeId != 'PartDesign::Body':
        # Part is not a part, return.
        return
    
    #FreeCAD.Console.PrintWarning(compound)
    make_compound=compound
    copied_subobjects = []
    copied_subobjects_Names = []
    #print (get_all_subobjects(part))
    for o in get_all_subobjects(part):
        if o.Name not in copied_subobjects_Names:
            if FreeCADGui.ActiveDocument.getObject(o.Name).Visibility:
                vis=True
                for Container in o.InListRecursive:
                    if not (FreeCADGui.ActiveDocument.getObject(Container.Name).Visibility):
                        vis=False
                if vis:
                    copied_subobjects_Names.append(o.Name)
                    copied_subobjects += copy_subobject(doc, o,suffix)
                    copied_subobjects_Names.append(o.Name)
    if doc.ActiveObject is not None:
        pName = doc.ActiveObject.Name
    else:
        pName= 'None'
    
    if make_compound=='compound':
        compound = doc.addObject('Part::Compound', mk_str_u(part.Label)+suffix)
        compound.Links = copied_subobjects
        pName = doc.ActiveObject.Name
    elif make_compound=='part':
        doc.addObject('App::Part',mk_str_u(part.Label)+'_')
        #FreeCAD.Console.PrintMessage(doc.ActiveObject.Label)
        actobj=doc.ActiveObject
        for uplvlobj in actobj.InListRecursive:
            if uplvlobj.TypeId=='App::Part':
                pName=uplvlobj.Name
        #pName=doc.ActiveObject.Name
        for obj in copied_subobjects:
            #doc.getObject(pName).addObject(doc.getObject(obj.Name))
            #FreeCAD.Console.PrintMessage(doc.getObject(pName))
            #FreeCAD.Console.PrintMessage(doc.getObject(obj.Name))
            doc.getObject(pName).addObject(doc.getObject(obj.Name))
        #FreeCAD.Console.PrintMessage(doc.ActiveObject.Label)
    doc.recompute()
    return pName

def get_all_subobjects(o):
    """Recursively get all subobjects
    
    Subobjects of objects having a Shape attribute are not included otherwise each
    single feature of the object would be copied. The result is that bodies,
    compounds, and the result of boolean operations will be converted into a
    simple copy of their shape.
    """
    # Depth-first search algorithm.
    discovered = []
    # We do not need an extra copy for stack because OutList is already a copy.
    stack = o.OutList
    while stack:
        v = stack.pop(0)
        if v not in discovered:
            discovered.append(v)
            if not hasattr(v, 'Shape'):
                stack += v.OutList
    return discovered


    
def get_all_subobjects_old(o):
    """Recursively get all subobjects
    
    Subobjects of objects having a Shape attribute are not included otherwise each
    single feature of the object would be copied. The result is that bodies,
    compounds, and the result of boolean operations will be converted into a
    simple copy of their shape.
    """
    if hasattr(o, 'Shape'):
        return []
    # With the assumption that the attribute InList is ordered, only add the
    # subobject if o is the direct parent, i.e. the first in InList.
    l = [so for so in o.OutList if so.InList and so.InList[0] is o]
    for subobject in l:
        l += get_all_subobjects(subobject)
    return l


def copy_subobject(doc, o,suffix='(copy)'):
    copied_object = []
    if not hasattr(o, 'Shape') or o.TypeId == 'Sketcher::SketchObject' or o.Shape.isNull():
        return copied_object
    vo_o = o.ViewObject
    try:
        copy = doc.addObject('Part::Feature', o.Name + '_Shape')
        copy.Shape = o.Shape
        #copy.Label = 'Copy of ' + o.Label
        if suffix=='_':
            copy.Label = mk_str_u(o.Label)+suffix
        else:
            copy.Label = mk_str_u(o.Label)+'.'+suffix
        #copy.Placement = get_recursive_inverse_placement(o).inverse()
        copy.Placement = o.getGlobalPlacement()

        vo_copy = copy.ViewObject
        vo_copy.ShapeColor = vo_o.ShapeColor
        vo_copy.LineColor = vo_o.LineColor
        vo_copy.PointColor = vo_o.PointColor
        vo_copy.DiffuseColor = vo_o.DiffuseColor
        vo_copy.Transparency = vo_o.Transparency
    except AttributeError:
        pass
    else:
        copied_object = [copy]
    return copied_object

def get_recursive_inverse_placement(o):
    # We browse the parent in reverse order so we have to multiply the inverse
    # placements and return the inverse placement.
    # Note that we cannot rely on o.InListRecursive because the order there is
    # not reliable.
    # TODO: see if this cannot be replaced with o.getGlobalPlacement().
    p = o.Placement.inverse()
    parent = o.getParentGeoFeatureGroup()
    if parent:
        p = p.multiply(get_recursive_inverse_placement(parent))
    return p
##
def toggle_highlight_subtree(objs):
    def addsubobjs(obj,totoggleset):
        totoggle.add(obj)
        for subobj in obj.OutList:
            addsubobjs(subobj,totoggleset)

    import FreeCAD
    totoggle=set()
    for obj in objs:
        addsubobjs(obj,totoggle)
    checkinlistcomplete =False
    while not checkinlistcomplete:
        for obj in totoggle:
            if (obj not in objs):
                if (frozenset(obj.InList) - totoggle):
                    if hasattr (set, 'totoggle'):
                        totoggle.toggle(obj)
                        break
        else:
            checkinlistcomplete = True
    obj_tree=objs[1:len(objs)]
    for obj in totoggle:
        if 'Compound' not in FreeCADGui.ActiveDocument.getObject(obj.Name).TypeId: # and 'App::Part' not in Gui.ActiveDocument.getObject(obj.Name).TypeId:
            if 'Part' in obj.TypeId or 'App::Link' in obj.TypeId:
                if obj not in obj_tree:
                    FreeCADGui.Selection.addSelection(obj)
                else:
                    FreeCADGui.Selection.removeSelection(obj)
        else:
            if hide_compound==True:
                FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False

#####
def toggle_visibility_subtree(objs):
    def addsubobjs(obj,totoggleset):
        totoggle.add(obj)
        for subobj in obj.OutList:
            addsubobjs(subobj,totoggleset)

    import FreeCAD
    totoggle=set()
    for obj in objs:
        addsubobjs(obj,totoggle)
    checkinlistcomplete =False
    while not checkinlistcomplete:
        for obj in totoggle:
            if (obj not in objs) and (frozenset(obj.InList) - totoggle):
                totoggle.toggle(obj)
                break
        else:
            checkinlistcomplete = True
    for obj in totoggle:
        if 'Compound' not in FreeCADGui.ActiveDocument.getObject(obj.Name).TypeId:
            if 'Part' in obj.TypeId or 'Sketch' in obj.TypeId:
            #if 'Part::Feature' in obj.TypeId or 'App::Part' in obj.TypeId:
                #if obj.Visibility==True:
                if FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility==True:
                    #obj.Document.getObject(obj.Name).Visibility=False
                    FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                else:
                    FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=True
        else:
            if hide_compound==True:
                FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False

#####
class ksuToolsRemoveFromTree:
    "ksu tools Remove from Tree"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'TreeItemOutMinus.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsRemoveFromTree","Remove from Tree") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsRemoveFromTree","ksu Remove Object(s) from Container Tree\nkeeping Placement\nFirst Selection is the Container")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            doc=FreeCAD.ActiveDocument
            #if "App::Part" in doc.getObject(sel[0].Name).TypeId or "App::LinkGroup" in doc.getObject(sel[0].Name).TypeId:
            if "App::Part" in sel[0].TypeId or "App::LinkGroup" in sel[0].TypeId:
                doc.openTransaction('rmvTree')
                base=doc.getObject(sel[0].Name)
                for o in sel:
                    if o.Name != sel[0].Name:
                        #o_glob_plac = o.getGlobalPlacement()
                        if hasattr(base, "OutList"):
                            if o in base.OutList:
                                if "App::Part" in o.TypeId:
                                    base.removeObject(o)
                                elif "App::LinkGroup" in o.TypeId:
                                    base.ViewObject.dragObject(o)
                            else:
                                for item in base.OutListRecursive:
                                    if hasattr(item, "OutList"):
                                        if o in item.OutList:
                                            if "App::Part" in item.TypeId:
                                                item.removeObject(o)
                                            elif "App::LinkGroup" in item.TypeId:
                                                #print(item.Label,o.Label)
                                                item.ViewObject.dragObject(o)
                                            o.Placement = item.Placement.multiply(o.Placement)
                        #o.Placement = o_glob_plac
                        o.Placement = base.Placement.multiply(o.Placement)
                        for item in base.InListRecursive:
                            #fcc_prn(item.Label)
                            if item.TypeId == 'App::Part' or item.TypeId == 'PartDesign::Body' or item.TypeId == 'App::LinkGroup':
                                if "App::Part" in item.TypeId:
                                    #doc.getObject(item.Name).addObject(doc.getObject(o.Name))
                                    item.addObject(o)
                                elif "App::LinkGroup" in item.TypeId:
                                    #doc.getObject(item.Name).ViewObject.dropObject(doc.getObject(o.Name))
                                    item.ViewObject.dropObject(o)
                doc.commitTransaction()
            else:
                #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
                reply = QtGui.QMessageBox.information(None,"Warning", "Select one Container and some object(s) to be Removed from the Tree.")
                FreeCAD.Console.PrintWarning("Select one Container and some object(s) to be Removed from the Tree.\n")
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one Container and some object(s) to be Removed from the Tree.")
            FreeCAD.Console.PrintWarning("Select one Container and some object(s) to be Removed from the Tree.\n")
                
FreeCADGui.addCommand('ksuToolsRemoveFromTree',ksuToolsRemoveFromTree())

#####
class ksuToolsAddToTree:
    "ksu tools Add to Tree"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'TreeItemInPlus.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsAddToTree","Add to Tree") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsAddToTree","ksu Add Object(s) to Container Tree\nkeeping Placement\nFirst Selection is the Container")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            doc=FreeCAD.ActiveDocument
            #if "App::Part" in doc.getObject(sel[0].Name).TypeId:
            if "App::Part" in sel[0].TypeId or "App::LinkGroup" in sel[0].TypeId:
                doc.openTransaction('addTree')
                base=doc.getObject(sel[0].Name)
                for o in sel:
                    if o.Name != sel[0].Name:
                        if hasattr(base, "OutList"):
                            for item in base.InListRecursive:
                                if item.TypeId == 'App::Part' or item.TypeId == 'PartDesign::Body' or "App::LinkGroup" in item.TypeId:
                                    o.Placement = item.Placement.inverse().multiply(o.Placement)
                                    #s=o.Shape.copy()
                                    #Part.show(s)
                        o.Placement = base.Placement.inverse().multiply(o.Placement)
                        #s1=o.Shape.copy()
                        #Part.show(s1)
                        if "App::Part" in sel[0].TypeId:
                            sel[0].addObject(o)
                            #doc.getObject(sel[0].Name).addObject(doc.getObject(o.Name))
                        elif "App::LinkGroup" in sel[0].TypeId:
                            sel[0].ViewObject.dropObject(o)
                doc.commitTransaction()
            else:
                #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
                reply = QtGui.QMessageBox.information(None,"Warning", "Select one Container and some object(s) to be Added to the Tree.")
                FreeCAD.Console.PrintWarning("Select one Container and some object(s) to be Added to the Tree.\n")
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one Container and some object(s) to be Added to the Tree.")
            FreeCAD.Console.PrintWarning("Select one Container and some object(s) to be Added to the Tree.\n")
        
FreeCADGui.addCommand('ksuToolsAddToTree',ksuToolsAddToTree())

#####
def toggle_transparency_subtree(objs):
    def addsubobjs(obj,totoggleset):
        totoggle.add(obj)
        for subobj in obj.OutList:
            addsubobjs(subobj,totoggleset)

    import FreeCAD
    doc=FreeCADGui.ActiveDocument
    totoggle=set()
    for obj in objs:
        addsubobjs(obj,totoggle)
    checkinlistcomplete =False
    while not checkinlistcomplete:
        for obj in totoggle:
            if (obj not in objs) and (frozenset(obj.InList) - totoggle):
                try:
                    totoggle.toggle(obj)
                    break
                except:
                    FreeCAD.Console.PrintWarning('totoggle not allowed\n')
        else:
            checkinlistcomplete = True
    for obj in totoggle:
        #FreeCAD.Console.PrintMessage(obj.Label)
        #if 'App::Part' not in obj.TypeId and 'Part::Feature' in obj.TypeId:
        if 'App::Part' not in obj.TypeId and 'Part' in obj.TypeId:
            #if obj.Visibility==True:
            #FreeCAD.Console.PrintMessage(obj.Label)
            if doc.getObject(obj.Name).Transparency == 0:
                #obj.Document.getObject(obj.Name).Visibility=False
                doc.getObject(obj.Name).Transparency = 70
            else:
                doc.getObject(obj.Name).Transparency = 0
##
class ksuToolsTransparencyToggle:
    "ksu tools Transparency Toggle"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'transparency_toggle.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsTransparencyToggle","Transparency Toggle") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsTransparencyToggle","ksu Selection Transparency Toggle")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            doc=FreeCADGui.ActiveDocument
            for obj in sel:
                if "App::Part" not in obj.TypeId and "App::LinkGroup" not in obj.TypeId:
                    if hasattr(doc.getObject(obj.Name), 'Transparency'):
                        if doc.getObject(obj.Name).Transparency == 0:
                            doc.getObject(obj.Name).Transparency = 70
                        else:
                            doc.getObject(obj.Name).Transparency = 0
                else:
                    toggle_transparency_subtree(FreeCADGui.Selection.getSelection())
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one or more object(s) to change its transparency!")
            FreeCAD.Console.PrintWarning("Select one or more object(s) to change its transparency!\n")             

FreeCADGui.addCommand('ksuToolsTransparencyToggle',ksuToolsTransparencyToggle())

#####

##
class ksuToolsHighlightToggle:
    "ksu tools Highlight Toggle"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'select_toggle.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsHighlightToggle","Highlight Toggle") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsHighlightToggle","ksu Selection Highlight Toggle")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            #if 'LinkView' not in dir(FreeCADGui): #pre a3 Link3 merge
            toggle_highlight_subtree(FreeCADGui.Selection.getSelection())
        #if FreeCADGui.Selection.getSelection():
        #    sel=FreeCADGui.Selection.getSelection()
        #    doc=FreeCADGui.ActiveDocument
        #    FreeCADGui.runCommand('Std_ToggleVisibility',0)
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one or more object(s) to be highlighted!")
            FreeCAD.Console.PrintWarning("Select one or more object(s) to be highlighted!\n")             

FreeCADGui.addCommand('ksuToolsHighlightToggle',ksuToolsHighlightToggle())

#####
class ksuToolsVisibilityToggle:
    "ksu tools Visibility Toggle"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'visibility_toggle.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsVisibilityToggle","Visibility Toggle") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsVisibilityToggle","ksu Selection Visibility Toggle")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            #toggle_visibility_subtree(FreeCADGui.Selection.getSelection())
            FreeCADGui.runCommand('Std_ToggleVisibility',0)
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one or more object(s) to toggle visibility!")
            FreeCAD.Console.PrintWarning("Select one or more object(s) to toggle visibility!\n")             

FreeCADGui.addCommand('ksuToolsVisibilityToggle',ksuToolsVisibilityToggle())

#####
class ksuToolsCheckSolid:
    "ksu tools Check Solid property"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'ShapeInfo_check.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsCheckSolid","Check Solid property") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsCheckSolid","ksu Check Solid property\nToggle suffix")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            def mk_str(input):
                if (sys.version_info > (3, 0)):  #py3
                    if isinstance(input, str):
                        return input
                    else:
                        input =  input.encode('utf-8')
                        return input
                else:  #py2
                    if type(input) == unicode:
                        input =  input.encode('utf-8')
                        return input
                    else:
                        return input
            def i_say(msg):
                FreeCAD.Console.PrintMessage(msg)
                FreeCAD.Console.PrintMessage('\n')
            
            def i_sayw(msg):
                FreeCAD.Console.PrintWarning(msg)
                FreeCAD.Console.PrintWarning('\n')
                
            def i_sayerr(msg):
                FreeCAD.Console.PrintError(msg)
                FreeCAD.Console.PrintWarning('\n')
            ##
            if len(sel)<1:
                    msg="Select one or more object(s) to be checked!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else:
                non_solids=''
                solids=''
                for o in sel:
                    if hasattr(o,"Shape"):
                        if '.[compsolid]' in o.Label or '.[solid]' in o.Label or '.[shell]' in o.Label\
                                 or '.[compound]' in o.Label or '.[face]' in o.Label:
                            o.Label=mk_str(o.Label).replace('.[solid]','').replace('.[shell]','').replace('.[compsolid]','').replace('.[compound]','').replace('.[face]','')
                        else:
                            if len(o.Shape.Solids)>0:
                                i_say(mk_str(o.Label)+' Solid object(s) NBR : '+str(len(o.Shape.Solids)))
                                solids+=mk_str(o.Label)+'<br>'
                                if '.[solid]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[solid]'
                            else:
                                i_sayerr(mk_str(o.Label)+' object is a NON Solid')
                                non_solids+=mk_str(o.Label)+'<br>'
                            if len(o.Shape.Shells)>0:
                                i_say(mk_str(o.Label)+' Shell object(s) NBR : '+str(len(o.Shape.Shells)))
                                if '.[shell]' not in o.Label and '.[solid]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[shell]'
                            if len(o.Shape.Compounds)>0:
                                i_say(mk_str(o.Label)+' Compound object(s) NBR : '+str(len(o.Shape.Compounds)))
                                if '.[compound]' not in o.Label and '.[solid]' not in o.Label and '.[shell]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[compound]'
                            if len(o.Shape.CompSolids)>0:
                                i_say(mk_str(o.Label)+' CompSolids object(s) NBR : '+str(len(o.Shape.CompSolids)))
                                if '.[compsolid]' not in o.Label and '.[solid]' not in o.Label and '.[shell]' not in o.Label\
                                    and '.[compound]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[compsolid]'
                            if len(o.Shape.Faces)>0:
                                i_say(mk_str(o.Label)+' Faces object(s) NBR : '+str(len(o.Shape.Faces)))
                                if '.[compsolid]' not in o.Label and '.[solid]' not in o.Label and '.[shell]' not in o.Label\
                                    and '.[compound]' not in o.Label and '.[face]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[face]'
                    else:
                        FreeCAD.Console.PrintWarning("Select object with a \"Shape\" to be checked!\n")
                # if len (non_solids)>0:
                #     reply = QtGui.QMessageBox.information(None,"Warning", 'List of <b>NON Solid</b> object(s):<br>'+non_solids)
                # if len (solids)>0:
                #     reply = QtGui.QMessageBox.information(None,"Info", 'List of <b>Solid</b> object(s):<br>'+solids)
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one or more object(s) to be checked!")
            FreeCAD.Console.PrintWarning("Select one or more object(s) to be checked!\n")             

FreeCADGui.addCommand('ksuToolsCheckSolid',ksuToolsCheckSolid())

#####
def toggleAlly(tree, item, collapse):
    if collapse == False:
        tree.expandItem(item)
    elif collapse == True:  
        tree.collapseItem(item)
    for i in range(item.childCount()):
        print(item.child(i).text(0))
        if 'Origin' not in item.child(i).text(0):
            toggleAlly(tree, item.child(i), collapse)
##


class ksuToolsToggleTreeView:
    "ksu tools Toggle Tree View"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'expand_all.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksuToolsToggleTreeView","Expand/Collapse Tree View") ,
                     'ToolTip' : QT_TRANSLATE_NOOP("ksuToolsToggleTreeView","ksu tools Expand/Collapse Tree View")}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            ##
            sel=FreeCADGui.Selection.getSelection()
            ##
            if len(sel)!=1:
                    msg="Select one expandable tree object to be expanded/compressed!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else:
                import expTree;reload_lib(expTree)
                expTree.toggle_Tree()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one expandable tree object to be expanded/compressed!")
            FreeCAD.Console.PrintWarning("Select one expandable tree object to be expanded/compressed!\n")             

FreeCADGui.addCommand('ksuToolsToggleTreeView',ksuToolsToggleTreeView())

#####
class ksuToolsAligner:
    "ksu tools Aligner"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsAligner","Manipulator tools \'Aligner\'")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Align.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            import Aligner;reload_lib(Aligner)

FreeCADGui.addCommand('ksuToolsAligner',ksuToolsAligner())

#####
class ksuToolsMover:
    "ksu tools Mover"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsMover","Manipulator tools \'Mover\'")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Mover.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            import Mover;reload_lib(Mover)

FreeCADGui.addCommand('ksuToolsMover',ksuToolsMover())
#####
class ksuToolsCaliper:
    "ksu tools Caliper"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsCaliper","Manipulator tools \'Caliper\'")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Caliper.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            import Caliper;reload_lib(Caliper)

FreeCADGui.addCommand('ksuToolsCaliper',ksuToolsCaliper())
#####
class ksuToolsLoopSelection:
    "ksu tools Loop Selection"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsLoopSelection","ksu tools \'LoopSelection\'\nLoop selection on a xy outline")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Path-SelectLoop.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def __init__(self):
        self.obj = None
        self.sub = []
        self.active = False

    def IsActive(self):
        if bool(FreeCADGui.Selection.getSelection()) is False:
            return False
        return True
        
    def Activated(self):
        try:
            sel = FreeCADGui.Selection.getSelectionEx()[0]
            PathCommands._CommandSelectLoop.Activated(sel)
        except:
            print('Path WB not working')
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('ksuToolsLoopSelection',ksuToolsLoopSelection())
##


#####
class ksuToolsMergeSketches:
    "ksu tools Merge Sketches"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsMergeSketches","Merge Sketches")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_MergeSketch.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if FreeCADGui.Selection.getSelection():
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        FreeCADGui.runCommand('Sketcher_MergeSketches')
        for s in FreeCADGui.Selection.getSelection():
            FreeCADGui.ActiveDocument.getObject(s.Name).Visibility=False
        
FreeCADGui.addCommand('ksuToolsMergeSketches',ksuToolsMergeSketches())
###
class ksuToolsEditPrefs:
    "ksu tools Edit Preferences"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsEditPrefs","Edit Preferences")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Preferences-Edit.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        #import kicadStepUptools
        # import hlp
        # reload_lib(hlp)
        FreeCADGui.runCommand("Std_DlgPreferences")
        
FreeCADGui.addCommand('ksuToolsEditPrefs',ksuToolsEditPrefs())

#####
###
class ksuOpDXF:
    "ksu tools open Legacy DXF"
    
    def GetResources(self):
        mybtn_tooltip ="open Legacy DXF"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'openDXF.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip+' v1.4.0'}
 
    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        #import kicadStepUptools
        # import hlp
        # reload_lib(hlp)
        #FreeCADGui.runCommand("Std_DlgPreferences") 
        
        import _DXF_Import
        import os
        from kicadStepUptools import make_unicode, make_string
        # _DXF_Import.open('D:/Temp/t4k3-DWG.DXF')
        prefs_ = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
        last_pcb_path = prefs_.GetString("last_pcb_path")
        if not(prefs_.GetBool('not_native_dlg')):
            name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open a DXF file...",
                last_pcb_path, filter="*.dxf *.DXF")
        else:
            name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open a DXF file...",
                last_pcb_path, filter="*.dxf *.DXF",options=QtWidgets.QFileDialog.DontUseNativeDialog)
        # fname, fnamefilter = QtGui.QFileDialog.getOpenFileName(parent=FreeCADGui.getMainWindow(), caption='Read a DXF file', filter='*.dxf *.DXF')
        if name:
            last_pcb_path=os.path.dirname(name)
            prefs_.SetString("last_pcb_path", make_string(last_pcb_path))
            _DXF_Import.read(name)
            FreeCADGui.SendMsgToActiveView("ViewFit")
        
FreeCADGui.addCommand('ksuOpDXF',ksuOpDXF())

###
class ksuOpEzDXF:
    "ksu tools open ezDXF"
    
    def GetResources(self):
        mybtn_tooltip ="open ezDXF"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'openEzDXF.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip }
 
    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        #import kicadStepUptools
        # import hlp
        # reload_lib(hlp)
        #FreeCADGui.runCommand("Std_DlgPreferences") 
        from ezDXF_import import open_ezdxf
        try:
            import ezdxf
            import os
            from kicadStepUptools import make_unicode, make_string
            # _DXF_Import.open('D:/Temp/t4k3-DWG.DXF')
            prefs_ = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
            last_pcb_path = prefs_.GetString("last_pcb_path")
            if not(prefs_.GetBool('not_native_dlg')):
                name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open a DXF file (w ezDXF lib)...",
                    last_pcb_path, filter="*.dxf *.DXF")
            else:
                name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open a DXF file (w ezDXF lib)...",
                    last_pcb_path, filter="*.dxf *.DXF",options=QtWidgets.QFileDialog.DontUseNativeDialog)
            # fname, fnamefilter = QtGui.QFileDialog.getOpenFileName(parent=FreeCADGui.getMainWindow(), caption='Read a DXF file', filter='*.dxf *.DXF')
            if name:
                last_pcb_path=os.path.dirname(name)
                prefs_.SetString("last_pcb_path", make_string(last_pcb_path))
                open_ezdxf(name,True,True)
                FreeCADGui.SendMsgToActiveView("ViewFit")
        except:
            FreeCAD.Console.PrintError("ezDXF missing; use: \'pip install ezdxf python lib\'\n")
        
FreeCADGui.addCommand('ksuOpEzDXF',ksuOpEzDXF())
###
class ksuImpDXF:
    "ksu tools import Legacy DXF"
    
    def GetResources(self):
        mybtn_tooltip ="import Legacy DXF"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importDXF.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip+' v1.4.0'}
 
    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        #import kicadStepUptools
        # import hlp
        # reload_lib(hlp)
        #FreeCADGui.runCommand("Std_DlgPreferences") 
        
        import _DXF_Import
        from dxf_parser import _importDXF
        import os
        from kicadStepUptools import make_unicode, make_string
        prefs_ = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
        last_pcb_path = prefs_.GetString("last_pcb_path")
        if not(prefs_.GetBool('not_native_dlg')):
            name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Import a DXF file...",
                last_pcb_path, filter="*.dxf *.DXF")
        else:
            name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Import a DXF file...",
                last_pcb_path, filter="*.dxf *.DXF",options=QtWidgets.QFileDialog.DontUseNativeDialog)
        # fname, fnamefilter = QtGui.QFileDialog.getOpenFileName(parent=FreeCADGui.getMainWindow(), caption='Read a DXF file', filter='*.dxf *.DXF')
        if name:
            if FreeCAD.ActiveDocument is not None:
                _importDXF.insert(name,FreeCAD.ActiveDocument.Name)
            else:
                _DXF_Import.read(name)
            last_pcb_path=os.path.dirname(name)
            prefs_.SetString("last_pcb_path", make_string(last_pcb_path))
            FreeCADGui.SendMsgToActiveView("ViewFit")
        
FreeCADGui.addCommand('ksuImpDXF',ksuImpDXF())
###
if 0:
    class ksuExpDXF:
        "ksu tools export Legacy DXF"
        
        def GetResources(self):
            mybtn_tooltip ="export Legacy DXF"
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'exportDXF.svg') , # the name of a svg file available in the resources
                        'MenuText': mybtn_tooltip ,
                        'ToolTip' : mybtn_tooltip}
    
        def IsActive(self):
            return True
            #else:
            #    self.setToolTip("Grayed Tooltip!")
            #    print(self.ObjectName)
            #    grayed_tooltip="Grayed Tooltip!"
            #    mybtn_tooltip=grayed_tooltip
    
        def Activated(self):
            # do something here...
            #import kicadStepUptools
            # import hlp
            # reload_lib(hlp)
            FreeCADGui.runCommand("Std_DlgPreferences")
            
    FreeCADGui.addCommand('ksuExpDXF',ksuExpDXF())
#####
class ksuRemoveTimeStamp:
    "ksu  Remove TimeStamp"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuRemoveTimeStamp","Remove TimeStamp from Labels")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'remove_TimeStamp.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        doc = FreeCAD.ActiveDocument
        if doc is not None:
            if FreeCADGui.Selection.getSelection():
                sel=FreeCADGui.Selection.getSelection()
                if len(sel)==1:        
                    return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # removing TimeStamp ...
        doc = FreeCAD.ActiveDocument
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            if len(sel)!=1:
                msg="Select one tree object to remove its Label TimeStamps!\n"
                reply = QtGui.QMessageBox.information(None,"Warning", msg)
                FreeCAD.Console.PrintWarning(msg)             
            else:
                #msgBox = QtGui.QMessageBox()
                #msgBox.setText("This will remove ALL TimeStamps from selection objects.\nIt cannot be ondone.")
                #msgBox.setInformativeText("Do you want to continue?")
                #msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                #msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
                ret = QtGui.QMessageBox.warning(None, ("Warning"),
                               ("This will remove ALL TimeStamps from selection objects.\nDo you want to continue?"),
                               QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                               QtGui.QMessageBox.Cancel)
                #ret = msgBox.exec_()
                if ret == QtGui.QMessageBox.Ok:
                    for ob in sel:
                    #for o in doc.Objects:
                        #print (ob.Name,ob.Label,ob.TypeId)    
                        if ob.TypeId == 'App::Part' or ob.TypeId == 'App::LinkGroup':
                            o_list = ob.OutListRecursive
                            for o in o_list:
                                #print (o.Label)
                                if (hasattr(o, 'Shape')) \
                                        and ('Axis' not in o.Label and 'Plane' not in o.Label and 'Sketch' not in o.Label):
                                    if o.Label.rfind('_') < o.Label.rfind('['):
                                        ts = o.Label[o.Label.rfind('_')+1:o.Label.rfind('[')]
                                        #print (len(ts))
                                        if len(ts) == 8:
                                            o.Label=o.Label[:o.Label.rfind('_')]+o.Label[o.Label.rfind('['):]
                                    else:
                                        ts = o.Label[o.Label.rfind('_')+1:]
                                        #print (len(ts))
                                        if len(ts) == 8:
                                            o.Label=o.Label[:o.Label.rfind('_')]
                                    #print (o.Label)
                            for o in o_list:
                                #if ('App::Link' in o.TypeId):
                                if (o.TypeId == 'App::Link'):
                                    o.Label = o.LinkedObject.Label
                    FreeCAD.Console.PrintWarning('removed Time Stamps\n')
                elif ret == QtGui.QMessageBox.Cancel:
                    FreeCAD.Console.PrintMessage('Operation Aborted\n')                
        else:
            msg="Select one tree object to remove its Label TimeStamps!\n"
            reply = QtGui.QMessageBox.information(None,"Warning", msg)
            FreeCAD.Console.PrintWarning(msg)             

FreeCADGui.addCommand('ksuRemoveTimeStamp',ksuRemoveTimeStamp())
###
class ksuRemoveSuffix:
    "ksu  Remove Suffix"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuRemoveSuffix","Remove \'custom\' Suffix from Labels")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'RemoveSuffix.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        doc = FreeCAD.ActiveDocument
        if doc is not None:
            if FreeCADGui.Selection.getSelection():
                sel=FreeCADGui.Selection.getSelection()
                if len(sel)==1:        
                    return True

    def Activated(self):
        # removing TimeStamp ...
        doc = FreeCAD.ActiveDocument
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            if len(sel)!=1:
                msg="Select one tree object to remove its Label Suffix!\n"
                reply = QtGui.QMessageBox.information(None,"Warning", msg)
                FreeCAD.Console.PrintWarning(msg)             
            else:
                import exchangePositions;reload_lib(exchangePositions)
                #msgBox = QtGui.QMessageBox()
                #msgBox.setText("This will remove ALL TimeStamps from selection objects.\nIt cannot be ondone.")
                #msgBox.setInformativeText("Do you want to continue?")
                #msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                #msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
                #ret = QtGui.QMessageBox.warning(None, ("Warning"),
                # message box
                rdlg = exchangePositions.RemoveSuffixDlg()
                #msg_box = QtGui.QMessageBox()
                #msg_box.setWindowTitle("Warning")
                #msg_box.setText("This will remove ALL Suffix \'.stp\', \'.step\' from selection objects.\nDo you want to continue?")
                ##layout = msg_box.layout()
                #msg_box.txtInp = QtGui.QLineEdit()
                ##layout.addWidget(msg_box.txtInp)
                #gl = QtGui.QVBoxLayout()
                #gl.addWidget(msg_box.txtInp)
                #msg_box.setLayout(gl) 
                #msg_box.setInformativeText('Informative text.')
                #msg_box.setDetailedText("Detailed text.")
                ##msg_box.DetailedText.setTextInteractionFlags (QtCore.Qt.TextEditorInteraction)  #(QtCore.Qt.NoTextInteraction) # (QtCore.Qt.TextSelectableByMouse)
                #msg_box.setIcon(QtGui.QMessageBox.Critical)
                #msg_box.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                #msg_box.setDefaultButton(QtGui.QMessageBox.Cancel)
                #
                #ret = msg_box.exec_()
                
                ret = rdlg.exec_()
                
                # ret = QtGui.QMessageBox.warning(None, ("Warning"),
                #                ("This will remove ALL Suffix \'.stp\', \'.step\' from selection objects.\nDo you want to continue?"),
                #                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                #                QtGui.QMessageBox.Cancel)
                #ret = msgBox.exec_()
                # print(ret)
                # print (rdlg.le.text())
                filtering=rdlg.le.text()
                if ret: # == QtGui.QMessageBox.Ok:
                    for ob in sel:
                    #for o in doc.Objects:
                        #print (ob.Name,ob.Label,ob.TypeId)    
                        if ob.TypeId == 'App::Part' or ob.TypeId == 'App::LinkGroup':
                            #suffix1 = '.stp';suffix2 = '.step';suffix3 = '_stp';suffix2 = '_step'
                            #if ob.Label.lower().endswith(suffix1) or ob.Label.lower().endswith(suffix2)\
                            #   or ob.Label.lower().endswith(suffix1) or ob.Label.lower().endswith(suffix2):
                            o_list = ob.OutListRecursive
                            for o in o_list:
                                #print (o.Label)
                                if (hasattr(o, 'Shape')) \
                                        and ('Axis' not in o.Label and 'Plane' not in o.Label and 'Sketch' not in o.Label):
                                    #suffix1 = '.stp';suffix2 = '.step'
                                    #if o.Label.lower().endswith(suffix1) or o.Label.lower().endswith(suffix2):
                                    #o.Label = re.sub(rdlg.le.text()+'$', '', o.Label, flags=re.IGNORECASE)
                                    #print(o.Label[:o.Label.rfind (filtering)])
                                    if o.Label.rfind (filtering) != -1:
                                        o.Label = o.Label[:o.Label.rfind (filtering)]
                                    #o.Label = re.sub('.stp', '', o.Label, flags=re.IGNORECASE)
                                    #o.Label = re.sub('.step', '', o.Label, flags=re.IGNORECASE)
                                    #print (o.Label)
                                if o.TypeId == 'App::Part' or o.TypeId == 'App::LinkGroup':
                                    #o.Label = re.sub(rdlg.le.text()+'$', '', o.Label, flags=re.IGNORECASE)
                                    fixfiltering = filtering.replace('.','_')
                                    #print (fixfiltering)
                                    #print(o.Label[:o.Label.rfind (fixfiltering)])
                                    if o.Label.rfind (fixfiltering) != -1:
                                        o.Label = o.Label[:o.Label.rfind (fixfiltering)]
                                    #o.Label = re.sub('_stp', '', o.Label, flags=re.IGNORECASE)
                                    #o.Label = re.sub('_step', '', o.Label, flags=re.IGNORECASE)
                                    #o.Label = re.sub('.stp', '', o.Label, flags=re.IGNORECASE)
                                    #o.Label = re.sub('.step', '', o.Label, flags=re.IGNORECASE)                              
                            for o in o_list:
                                if (o.TypeId == 'App::Link'):
                                    o.Label = o.LinkedObject.Label
                    FreeCAD.Console.PrintWarning('removed Suffix \''+filtering+'\' \n')
                elif ret == 0: #== QtGui.QMessageBox.Cancel:
                    msg='Operation Aborted\n'
                    FreeCAD.Console.PrintMessage(msg)
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)                    
        else:
            msg="Select one tree object to remove its Label Suffix!\n"
            reply = QtGui.QMessageBox.information(None,"Warning", msg)
            FreeCAD.Console.PrintWarning(msg)             

FreeCADGui.addCommand('ksuRemoveSuffix',ksuRemoveSuffix())

#####
class ksuToolsExplode:
    "ksu tools Explode"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsExplode","ksu Tools PCB Explode\nSelect the top container of a kicad PCB to exlode it")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Explode_Pcb.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
 
    def Activated(self):
        # do something here...
        import explode
        explode.runExplodeGui()
        #import explode;reload_lib(explode)

FreeCADGui.addCommand('ksuToolsExplode',ksuToolsExplode())
#####
class ksuToolsDefeaturingTools:
    "ksu tools DefeaturingTools"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsDefeaturingTools","Defeaturing Tools from Defeaturing WorkBench")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'DefeaturingTools.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if 'Defeaturing' in combined_path:
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        combined_path = '\t'.join(sys.path)
        if 'Defeaturing' in combined_path:
            import DefeaturingTools;reload_lib(DefeaturingTools)

FreeCADGui.addCommand('ksuToolsDefeaturingTools',ksuToolsDefeaturingTools())
#####
class ksuToolsRemoveSubTree:
    "ksu tools Remove Sub Tree"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsRemoveSubTree","Remove Sub Tree")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'RemoveSubtree.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        FreeCAD.ActiveDocument.openTransaction('rmvSubTree')
        import kicadStepUptools
        kicadStepUptools.removesubtree(FreeCADGui.Selection.getSelection())
        FreeCAD.ActiveDocument.commitTransaction()
        
FreeCADGui.addCommand('ksuToolsRemoveSubTree',ksuToolsRemoveSubTree())
####
class ksuToolsAddTracks:
    "ksu tools Add Tracks"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsAddTracks","ksu tools Add Tracks\nNB: it could be a very intensive loading!")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'tracks.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 


    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        import tracks
        from kicadStepUptools import removesubtree
        from kicadStepUptools import ZoomFitThread
        from PySide import QtGui, QtCore
        if FreeCAD.ActiveDocument is not None:
            doc = FreeCAD.ActiveDocument
        else:
            doc = FreeCAD.newDocument()
        #doc.commitTransaction()
        #doc.UndoMode = 1
        doc.openTransaction('add_tracks_kicad')
        add_toberemoved = tracks.addtracks()
        # print(add_toberemoved)
        doc.commitTransaction()
        doc.recompute()
        def removing_objs():
            ''' removing objects after delay ''' 
            from kicadStepUptools import removesubtree
            doc.openTransaction('rmv_tracks_kicad')
            for tbr in add_toberemoved:
                removesubtree(tbr)
            doc.commitTransaction()
            # doc.undo()
            # doc.undo()
        # adding a timer to allow double transactions during the python code
        QtCore.QTimer.singleShot(0.2,removing_objs)
        if (not pt_lnx): # and (not pt_osx): issue on AppImages hanging on loading 
            FreeCADGui.SendMsgToActiveView("ViewFit")
        else:
            zf= Timer (0.25,ZoomFitThread)
            zf.start()        

    ##

FreeCADGui.addCommand('ksuToolsAddTracks',ksuToolsAddTracks())
#####
class ksuToolsAddSilks:
    "ksu tools Add Silks"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("ksuToolsAddSilks","ksu tools Add Silks from kicad exported DXF\nNB: it could be a very intensive loading!")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Silks.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        import makefacedxf
        if FreeCAD.ActiveDocument is not None:
            doc = FreeCAD.ActiveDocument
        else:
            doc = FreeCAD.newDocument()
        if 1: # using internal dxf old legacy library loader makefacedxf.checkDXFsettings():
            doc.openTransaction('add_silks')
            makefacedxf.makeFaceDXF()
            doc.commitTransaction()
        else:
            msg = """<b>DXF import setting NOT as required.</b><br>Please check to have selected:<br>
            - DXF Legacy Importer<br>
            - DXF Join Geometries<br>
            - DXF Create Simple Part Shapes<br>
            in DXF Preferences Import options"""
            reply = QtGui.QMessageBox.information(None,"Warning", msg)

FreeCADGui.addCommand('ksuToolsAddSilks',ksuToolsAddSilks())
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
        elif 'dxf' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , '2D-frame.svg') ,
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
        FC_majorV=int(float(FreeCAD.Version()[0]))
        FC_minorV=int(float(FreeCAD.Version()[1]))

        if ext.lower()==".pdf":
            import subprocess, sys
            if sys.platform == "linux" or sys.platform == "linux2":
                if 'LD_LIBRARY_PATH' in os.environ: # workaround for AppImage
                    my_env = os.environ
                    ldlp = os.environ['LD_LIBRARY_PATH']
                    del my_env['LD_LIBRARY_PATH']
                    #print("xdg-open", fnameDemo)
                    subprocess.Popen(["xdg-open", fnameDemo], env=my_env)
                else:
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
            if 'footprint' not in fnameDemo:
                FreeCADGui.activeDocument().activeView().viewAxonometric()
        elif ext.lower()==".step":
            if FC_majorV==0 and FC_minorV <17:
                fnameDemo=fnameDemo.rstrip(ext)+'-fc16'+ ext
                FreeCAD.Console.PrintWarning('opening ' + fnameDemo + "\r\n")
            import ImportGui
            ImportGui.open(fnameDemo)
            FreeCADGui.activeDocument().activeView().viewAxonometric()
            FreeCADGui.SendMsgToActiveView("ViewFit")
        elif ext.lower()==".dxf":
            #import ImportGui
            import importDXF
            importDXF.open(fnameDemo)
            #ImportGui.open(fnameDemo)
            #FreeCADGui.activeDocument().activeView().viewAxonometric()
            FreeCADGui.SendMsgToActiveView("ViewFit")
        #if ext==".pdf":
        #    subprocess.Popen([file],shell=True)
        
        #import ImportGui
        #ImportGui.open(os.path.join(exs_dir_path, self.exFile))
        #ImportCQ.open(os.path.join(exs_dir_path, self.exFile))

##
class checkSolidExpSTEP():
    "ksu tools check Export Step"
    
    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("checkSolidExpSTEP","Check if the selected part would be\nexported to STEP as a single solid")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Import-Export-STEP.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        if len(FreeCADGui.Selection.getSelection()) == 1:
            return True
 
    def Activated(self):
        # do something here...
        from PySide import QtGui, QtCore
        import tempfile
    
        doc=FreeCAD.ActiveDocument
        docG = FreeCADGui.ActiveDocument
        if doc is not None:
            fname = doc.Label #doc.FileName
            if len(fname) == 0:
                fname='untitled'
            tmpdir = tempfile.gettempdir() # get the current temporary directory
            tempfilepath = os.path.join(tmpdir,fname + u'-exported.step')
            sel=FreeCADGui.Selection.getSelection()
            if len (sel) == 1:
                doc_obj_nbr = len(doc.Objects)
                __objs__=[]
                __objs__.append(sel[0])
                docG.getObject(sel[0].Name).Visibility = False
                FreeCADGui.Selection.clearSelection()
                ##ReadShapeCompoundMode
                paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
                ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
                #sayerr("checking ReadShapeCompoundMode")
                print("ReadShapeCompoundMode status "+str(ReadShapeCompoundMode_status))
                restore_settings = False
                if ReadShapeCompoundMode_status:
                    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
                    paramGetVS.SetBool("ReadShapeCompoundMode",False)
                    print("disabling ReadShapeCompoundMode")
                    restore_settings = True
                import ImportGui
                ImportGui.export(__objs__,tempfilepath)
                del __objs__
                ImportGui.insert(tempfilepath,doc.Name)
                if restore_settings:
                    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
                    paramGetVS.SetBool("ReadShapeCompoundMode",True)
                    print("re-enabling ReadShapeCompoundMode")
                doc_newobj_nbr = len(doc.Objects)
                if (doc_newobj_nbr-doc_obj_nbr) >1:
                    msg='Exporting to STEP would create a multi solids object!\n'
                    msg1="""Exporting to STEP would create a <b>multi solids object!<b>"""
                    reply = QtGui.QMessageBox.warning(None,"Warning", msg1)
                    FreeCAD.Console.PrintError(msg)
                else:
                    FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.ActiveObject)
                    ksuToolsCheckSolid.Activated(FreeCAD.ActiveDocument.ActiveObject)
                    if '.[solid]' not in FreeCAD.ActiveDocument.ActiveObject.Label:
                        msg='Exporting to STEP would create a single NON solids object!\n'
                        msg1="""Exporting to STEP would create a <b>single NON solids object!<b>"""
                        reply = QtGui.QMessageBox.warning(None,"Warning", msg1)
                        FreeCAD.Console.PrintError(msg)
                    else:
                        msg='Exporting to STEP would create a single solids object!\n'
                        reply = QtGui.QMessageBox.information(None,"Info", msg)
                        FreeCAD.Console.PrintMessage(msg)
                FreeCADGui.SendMsgToActiveView("ViewFit")
                FreeCAD.Console.PrintMessage(tempfilepath+u'\n')

FreeCADGui.addCommand('checkSolidExpSTEP',checkSolidExpSTEP())


class Restore_Transparency():
    "ksu tools Restore Transparency to Active Document Objects"

    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("Restore_Transparency","Restore Transparency to Active Document Objects")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Restore_Transparency.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}

    def Activated(self):        
        doc = FreeCAD.ActiveDocument
        if doc is None:
            FreeCAD.Console.Print("No Active Document found")
            return
        else:
            for obj in doc.Objects:
                if hasattr (obj, 'ViewObject'):
                    if hasattr (obj.ViewObject, 'Transparency'):
                        if obj.ViewObject.Transparency < 100:
                            transparency = obj.ViewObject.Transparency
                            obj.ViewObject.Transparency = transparency + 1
                            obj.ViewObject.Transparency = transparency
        return

    def IsActive(self):
        doc = FreeCAD.activeDocument()
        if doc is None: return False
        return True

FreeCADGui.addCommand('Restore_Transparency',Restore_Transparency())

class Arcs2Circles():
    "ksu tools Convert Arcs to Circles in Sketch"

    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("Arcs2Circles","Convert Arcs to Circles in Sketch")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'arc2circle.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}

    def Activated(self):        
        import kicadStepUptools
        reload_lib( kicadStepUptools )
        sel = FreeCADGui.Selection.getSelection()
        o = sel[0]
        centers=[];rads=[]
        for idx,g in enumerate(o.Geometry):
            if 'Circle' in str(g) and kicadStepUptools.isConstruction(g) == False:
                found=False
                for i,c in enumerate(centers):
                #if not (g.Center in centers and g.Radius in rads):
                    if c == g.Center:
                        if g.Radius == rads[i]:
                            found=True
                            continue
                if not found:
                    centers.append(g.Center);rads.append(g.Radius)
        #print(len(centers), centers)
        skLabel = o.Label+"_circles"
        FreeCAD.ActiveDocument.addObject('Sketcher::SketchObject', skLabel)
        skd_name=FreeCAD.ActiveDocument.ActiveObject.Name
        FreeCAD.ActiveDocument.ActiveObject.Label = skLabel #workaround to keep '=' in Label
        #print(centers)
        for i,c in enumerate(centers):
            FreeCAD.ActiveDocument.getObject(skd_name).addGeometry(Part.Circle(FreeCAD.Vector(c[0], c[1]), FreeCAD.Vector(0, 0, 1), rads[i]))
        FreeCADGui.ActiveDocument.getObject(o.Name).Visibility=False
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        if len (sel) == 1:
            if sel[0].TypeId == 'Sketcher::SketchObject':
                return True
            else:
                return False
        else:
            return False

FreeCADGui.addCommand('Arcs2Circles',Arcs2Circles())

class approximateCenter():
    "ksu tools Create Center of Circle through 3 Vertices"

    def GetResources(self):
        mybtn_tooltip =QT_TRANSLATE_NOOP("approximateCenter","Create Center of Circle through 3 Vertices or Select two vertices to create a mid point or Select a Shape to create a center point")
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Three-Points-Center.svg') , # the name of a svg file available in the resources
                     'MenuText': QT_TRANSLATE_NOOP("ksu","Create Center of Circle through 3 Vertices") ,
                     'ToolTip' : mybtn_tooltip}

    def Activated(self):        
        selt = FreeCADGui.Selection.getSelectionEx()
        import Draft
        import math
        def circle_center(A, B, C):
            '''Return the circumcenter of three 3D vertices'''
            a2 = (B - C).Length**2
            b2 = (C - A).Length**2
            c2 = (A - B).Length**2
            a  = (B - C).Length
            b  = (C - A).Length
            c  = (A - B).Length
            if a2 * b2 * c2 == 0.0:
                print('Three vertices must be distinct')
                return
            alpha = a2 * (b2 + c2 - a2)
            beta = b2 * (c2 + a2 - b2)
            gamma = c2 * (a2 + b2 - c2)
            s = (a + b + c) / 2
            radius = a*b*c / 4 / math.sqrt(s * (s - a) * (s - b) * (s - c))
            return (alpha*A + beta * B + gamma * C)/(alpha + beta + gamma) , radius
        
        if len(selt) != 1:
            #print('Len='+str(len(selt))+' Select three vertices to create a point in the center of approximate circle')
            print('Select three vertices to create a point in the center of approximate circle')
            print('Select two vertices to create a mid point')
            print('Select a Shape to create a center point')
        else:
            to_process = False
            to_process_center = False
            debug=False
            sel = selt[0]
            if sel.HasSubObjects:
                vv = sel.SubObjects
                if len(vv) ==3 and vv[0].ShapeType == 'Vertex' and   vv[1].ShapeType == 'Vertex' and vv[2].ShapeType == 'Vertex':
                    shift, rd = circle_center(vv[0].Point, vv[1].Point, vv[2].Point)
                    suffix = '_center'
                    to_process = True
                    to_process_center = True
                    print (rd)
                    #print(shift)
                elif len(vv) ==2 and vv[0].ShapeType == 'Vertex' and   vv[1].ShapeType == 'Vertex':
                    halfedge = (vv[0].Point.sub(vv[1].Point)).multiply(.5)
                    mid=FreeCAD.Vector.add(vv[1].Point,halfedge)
                    shift = mid
                    suffix = '_mid'
                    # print (shift)
                    to_process = True
            elif hasattr(sel.Object, 'Shape'):
                shape = sel.Object.Shape
                if shape.ShapeType == 'Solid' or shape.ShapeType == 'Shell':
                    shift = shape.CenterOfMass
                    suffix = '_com'
                    to_process = True
                elif shape.ShapeType == 'Compound' or shape.ShapeType == 'CompSolid':
                    print('Centering on Bounding Box of Compound '+sel.Object.Label)
                    bb = shape.BoundBox
                    shift = FreeCAD.Vector(bb.XLength/2+bb.XMin,bb.YLength/2+bb.YMin,bb.ZLength/2+bb.ZMin)
                    suffix = '_bbc'
                    to_process = True
            if to_process:
                FreeCAD.ActiveDocument.openTransaction('Undo Create Center')
                nPt=Draft.makePoint(shift)
                nPt.Label = sel.Object.Label+suffix
                npt_Pl = nPt.Placement
                FreeCADGui.ActiveDocument.getObject(nPt.Name).PointColor = (0.333,0.667,1.000) #(1.000,0.667,0.498)
                FreeCADGui.ActiveDocument.getObject(nPt.Name).PointSize = 10.000
                if to_process_center:
                    circle = Draft.makeCircle(radius=rd, placement=npt_Pl, face=False, support=None)
                    circle.Label = sel.Object.Label+'_circle'
                    FreeCADGui.ActiveDocument.getObject(circle.Name).LineColor = (0.333,0.667,1.000)
                if len(sel.Object.InList) == 0:
                    FreeCAD.ActiveDocument.addObject('App::Part',sel.Object.Label+'_Part')
                    nP = FreeCAD.ActiveDocument.ActiveObject.Parents[0][0]
                else:
                    nP = sel.Object.InList[0]
                if debug:
                    print(nP.Label);print(nP.Name);print(nPt.Label);print(nPt.Name)
                    if len (sel.Object.InList) >= 1:
                        print(sel.Object.InList[0].Label)
                #FreeCAD.ActiveDocument.getObject(nPt.Name).adjustRelativeLinks(FreeCAD.ActiveDocument.getObject(nP.Name))
                FreeCAD.ActiveDocument.getObject(nP.Name).addObject(FreeCAD.ActiveDocument.getObject(nPt.Name))
                if to_process_center:
                    FreeCAD.ActiveDocument.getObject(nP.Name).addObject(FreeCAD.ActiveDocument.getObject(circle.Name))
                FreeCAD.ActiveDocument.getObject(nP.Name).addObject(FreeCAD.ActiveDocument.getObject(sel.Object.Name))
                FreeCAD.ActiveDocument.recompute()
                npt_Pl = nPt.Placement
                if to_process_center:
                    circle.Placement = npt_Pl
                FreeCAD.ActiveDocument.commitTransaction()

    def IsActive(self):
        selt = FreeCADGui.Selection.getSelectionEx()
        if len(selt) < 1:
            return False
        else:
            return True

FreeCADGui.addCommand('approximateCenter',approximateCenter())

class Create_BoundBox():
    "Create BoundBox of the Selected Object"

    def GetResources(self):
        mybtn_tooltip ="Create BoundBox of the Selected Object"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'BoundBox.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}

    def IsActive(self):
        doc = FreeCAD.ActiveDocument
        if doc is not None:
            if FreeCADGui.Selection.getSelection():
                sel=FreeCADGui.Selection.getSelection()
                if len(sel)>=1:        
                    return True
        return

    def Activated(self):        
        def make_shape_from_mesh (d,m):
            d.addObject('Part::Feature', 'Shape-Mesh')
            sm = d.ActiveObject
            __shape__ = Part.Shape()
            __shape__.makeShapeFromMesh(m.Mesh.Topology, 0.100000, False)
            sm.Shape = __shape__
            sm.purgeTouched()
            del __shape__
            return sm

        import Part
        doc = FreeCAD.ActiveDocument
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
        if len(sel)==1:
            selObj = sel[0]
            bbLbl = selObj.Label+"-BBox"
            bb = None
            if hasattr(selObj, 'Shape'):
                combined_path = '\t'.join(sys.path)
                if 'Assembly4' in combined_path:
                    import showHideLcsCmd
                    showHideLcsCmd.showHide(0)
                    FreeCAD.Console.PrintMessage('hiding LCs\n')
                    #FreeCADGui.runCommand('Asm4_hideLcs',0)
                else:
                    for e in selObj.OutList:
                        if e.TypeId == 'PartDesign::CoordinateSystem':
                            FreeCAD.Console.PrintMessage('hiding LCs\n')
                            e.ViewObject.Visibility = False
                bb = selObj.Shape.BoundBox
            elif hasattr(selObj, 'Mesh'):
                bb = selObj.ViewObject.getBoundingBox()
            if bb is not None:
                if len(FreeCAD.ActiveDocument.getObjectsByLabel(bbLbl))==0:
                    FreeCAD.ActiveDocument.addObject("Part::Box","Box")
                    bbO = FreeCAD.ActiveDocument.ActiveObject
                else:
                    bbO = FreeCAD.ActiveDocument.getObjectsByLabel(bbLbl)[0]
                bbO.Label = bbLbl
                # selObj.Label+"-BB"
                bbO.ViewObject.Transparency=90
                bbO.ViewObject.Visibility=True
                # bbO.ViewObject.ShapeColor = (0.67,0.00,0.00) # (0.00,0.00,0.50)
                sel_Old = sel[0]
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(bbO)
                FreeCADGui.runCommand('Std_RandomColor')
                # FreeCADGui.Selection.clearSelection()
                # FreeCADGui.Selection.addSelection(selObj)
                
                bbO.Placement.Base.x = bb.XMin
                bbO.Placement.Base.y = bb.YMin
                bbO.Placement.Base.z = bb.ZMin
                if bb.XLength > 0:
                    bbO.Length=bb.XLength 
                else:
                    bbO.Length=0.01
                if bb.YLength > 0:
                    bbO.Width=bb.YLength
                else:
                    bbO.Width=0.01
                if bb.ZLength > 0:
                    bbO.Height=bb.ZLength
                else:
                    bbO.Height=0.01
                FreeCAD.Console.PrintMessage('BB data x:'+str(bb.XLength)+", y:"+str(bb.YLength)+", z:"+str(bb.ZLength)+'\n')
                FreeCAD.ActiveDocument.recompute()
                FreeCADGui.SendMsgToActiveView("ViewFit")
        else:
            doc.addObject("Part::Compound","BBox-Compound")
            BBCompound= doc.ActiveObject
            sel_Old = sel
            cmpd_objs = []
            toDel_objs = []
            for o in sel:
                if hasattr(o.ViewObject, 'Visibility'):
                    if o.ViewObject.Visibility==True:
                        if hasattr(o, 'Shape'):
                            combined_path = '\t'.join(sys.path)
                            if 'Assembly4' in combined_path:
                                import showHideLcsCmd
                                showHideLcsCmd.showHide(0)
                                FreeCAD.Console.PrintMessage('hiding LCs\n')
                                #FreeCADGui.runCommand('Asm4_hideLcs',0)
                            else:
                                for e in o.OutList:
                                    if e.TypeId == 'PartDesign::CoordinateSystem':
                                        FreeCAD.Console.PrintMessage('hiding LCs\n')
                                        e.ViewObject.Visibility = False
                            cmpd_objs.append(o)
                        elif hasattr(o, 'Mesh'):
                            sm = make_shape_from_mesh (doc,o)
                            cmpd_objs.append(sm)
                            toDel_objs.append(sm)
            BBCompound.Links = cmpd_objs # sel
            doc.recompute()
            bb = BBCompound.Shape.BoundBox
            doc.addObject("Part::Box","Box")
            bbO = doc.ActiveObject
            bbO.Label = "BBox-multiObjects"
            bbO.ViewObject.Transparency=90
            bbO.ViewObject.Visibility=True
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(bbO)
            FreeCADGui.runCommand('Std_RandomColor')
            bbO.ViewObject.LineColor = bbO.ViewObject.ShapeColor
            bbO.Placement.Base.x = bb.XMin
            bbO.Placement.Base.y = bb.YMin
            bbO.Placement.Base.z = bb.ZMin
            if bb.XLength > 0:
                bbO.Length=bb.XLength 
            else:
                bbO.Length=0.01
            if bb.YLength > 0:
                bbO.Width=bb.YLength
            else:
                bbO.Width=0.01
            if bb.ZLength > 0:
                bbO.Height=bb.ZLength
            else:
                bbO.Height=0.01
            FreeCAD.Console.PrintMessage('BB data x:'+str(bb.XLength)+", y:"+str(bb.YLength)+", z:"+str(bb.ZLength)+'\n')
            doc.recompute()
            for o in cmpd_objs:
                o.ViewObject.Visibility=True
            FreeCADGui.SendMsgToActiveView("ViewFit")
            doc.removeObject(BBCompound.Name)
            for o in toDel_objs:
                doc.removeObject(o.Name)
            doc.recompute()
                    
FreeCADGui.addCommand('Create_BoundBox',Create_BoundBox())

#####
class ksuToolsImportFootprint:
    "ksu tools Load Footprint object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importFPs.svg') , # the name of a svg file available in the resources
                     'MenuText': "Load FootPrint" ,
                     'ToolTip' : "ksu Load KiCad PCB FootPrint"}
 
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
        if 1: #reload_Gui:
            reload_lib( kicadStepUptools )
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        if 0:
            kicadStepUptools.KSUWidget.activateWindow()
            kicadStepUptools.KSUWidget.show()
            kicadStepUptools.KSUWidget.raise_()
            kicadStepUptools.onLoadFootprint()
        import fps
        reload_lib( fps )
        doc = FreeCAD.ActiveDocument
        fps.addfootprint()
        
FreeCADGui.addCommand('ksuToolsImportFootprint',ksuToolsImportFootprint())
##
class ksuToolsAlignView:
    "ksu tools AlignView to Face"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'AlignView2Face.svg') , # the name of a svg file available in the resources
                     'MenuText': "AlignView to Face" ,
                     'ToolTip' : "ksu AlignView to Face"}
 
    def IsActive(self):
        doc = FreeCAD.ActiveDocument
        if doc is not None:
            if FreeCADGui.Selection.getSelectionEx():
                sl=FreeCADGui.Selection.getSelectionEx()
                if len (sl[0].SubObjects)==1:
                    if 'Vertex' not in str(sl[0].SubObjects[0]) and 'Edge' not in str(sl[0].SubObjects[0]):
                        return True
        return
 
    def Activated(self):
        # do something here...
        AlignView2Face()
                
FreeCADGui.addCommand('ksuToolsAlignView',ksuToolsAlignView())
##
def AlignView2Face():
    """ macro Macro_Align_View_to_Face
        App:Part and Body compliant"""
    
    inv_view=False
    
    def pointAt(normal, up):
        z = normal
        y = up
        x = y.cross(z)
        y = z.cross(x)
        rot = FreeCAD.Matrix()
        rot.A11 = x.x
        rot.A21 = x.y
        rot.A31 = x.z
        rot.A12 = y.x
        rot.A22 = y.y
        rot.A32 = y.z
        rot.A13 = z.x
        rot.A23 = z.y
        rot.A33 = z.z
        return FreeCAD.Placement(rot).Rotation

    #try:
    sl=FreeCADGui.Selection.getSelectionEx()
    if len (sl)>0:
        if len (sl[0].SubObjects)>0:
            if 'Vertex' not in str(sl[0].SubObjects[0]) and 'Edge' not in str(sl[0].SubObjects[0]):
                # QtCore.QTimer.singleShot(doubleClickDly,onDoubleClick)
                ob=sl[0]
                #faceSel = ob.SubObjects[0]
                norm, plcm, top, bbC = getNormalPlacementHierarchy (sl[0])
                cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()

                if inv_view==True: #:
                    # sayerr('double click: inversion View')
                    #dirz = faceSel.normalAt(0,0)*-1
                    dirz = norm*-1
                else:
                    # sayw('single click: standard View')
                    #dirz = faceSel.normalAt(0,0)
                    dirz = norm
                if dirz.z == 1 :
                    rot = pointAt(dirz, FreeCAD.Vector(0.0,1.0,0.0))
                elif dirz.z == -1 :
                    rot = pointAt(dirz, FreeCAD.Vector(0.0,1.0,0.0))
                else :
                    rot = pointAt(dirz, FreeCAD.Vector(0.0,0.0,-1.0))

                cam.orientation.setValue(rot.Q)
                #FreeCADGui.SendMsgToActiveView("ViewSelection")
                FreeCADGui.SendMsgToActiveView("ViewFit")
                inv_view = True
                for s in FreeCADGui.Selection.getSelection():
                    FreeCADGui.Selection.removeSelection(s)
##


#####