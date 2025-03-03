import Draft
import numpy as np
import FreeCAD, FreeCADGui, Part

def sel2edges():

    tol = 0.000000001
    delete=False
    mk_sketch=True
    
    rh_edges=[]
    rh_edges_names=[]
    rh_obj_name=[]
    rh_obj=[]
    eobj_list=[]
    selEx=FreeCADGui.Selection.getSelectionEx()
    doc=FreeCAD.ActiveDocument
    if len (selEx) > 0:
        doc.openTransaction('ed2sk')
        for selEdge in selEx:
            for i,e in enumerate(selEdge.SubObjects):
                rh_edges.append(e)
                rh_edges_names.append(selEdge.ObjectName+'.'+selEdge.SubElementNames[i])
                rh_obj.append(selEdge.Object)
                rh_obj_name.append(selEdge.ObjectName)
                Part.show(e)
                eobj=doc.ActiveObject
                eobj_list.append(eobj)
        doc.recompute()
        for e in rh_edges_names:
            print(e)
        doc.addObject("Part::Compound","Compound")
        cmp=doc.ActiveObject
        cmp.Links = eobj_list
        doc.recompute()
        
        active_view = FreeCADGui.ActiveDocument.activeView()
        rotation_view = active_view.getCameraOrientation()
        view_direction = active_view.getViewDirection()
        
        def placement_tol(vect1,vect2,tol):
            ''' 1 if tolerance of placement is low '''
            r=abs(np.subtract(vect1, vect2))
            if np.sum(r > tol):
                return 0
            else:
                return 1
    
        if placement_tol(FreeCADGui.ActiveDocument.activeView().getViewDirection(),FreeCAD.Vector(1.0, 0.0, 0.0),tol):
            print('left')
            # sv = Draft.makeShape2DView(cmp, FreeCAD.Vector(-1.0, 0.0, 0.0))
            sv = Draft.make_shape2dview(cmp, FreeCAD.Vector(-1.0, -0.0, -0.0))
            doc.recompute()
            cmp.ViewObject.Visibility=False
            sv.Placement=FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0)).multiply(sv.Placement)
            doc.recompute()
            sv.Placement=FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,0,1),180), FreeCAD.Vector(0,0,0)).multiply(sv.Placement)       
        elif placement_tol(FreeCADGui.ActiveDocument.activeView().getViewDirection(), FreeCAD.Vector(-1.0, 0.0, 0.0),tol):
            print('right')
            sv = Draft.make_shape2dview(cmp, FreeCAD.Vector(1.0, 0.0, 0.0))
            cmp.ViewObject.Visibility=False
            doc.recompute()
            sv.Placement=FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),-90), FreeCAD.Vector(0,0,0)).multiply(sv.Placement)
            doc.recompute()
            sv.Placement=FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,0,1),180), FreeCAD.Vector(0,0,0)).multiply(sv.Placement)        
        elif placement_tol(FreeCADGui.ActiveDocument.activeView().getViewDirection(), FreeCAD.Vector(0.0, 0.0, -1.0),tol):
            print('top')
            sv = Draft.make_shape2dview(cmp, FreeCAD.Vector(0.0, 0.0, 1.0))
            cmp.ViewObject.Visibility=False
            doc.recompute()
        elif placement_tol(FreeCADGui.ActiveDocument.activeView().getViewDirection(), FreeCAD.Vector(0.0, 0.0, 1.0),tol):
            print('bottom')
            sv = Draft.make_shape2dview(cmp, FreeCAD.Vector(-0.0, -0.0, -1.0))
            cmp.ViewObject.Visibility=False
            doc.recompute()
            sv.Placement=FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),180), FreeCAD.Vector(0,0,0)).multiply(sv.Placement)
        else:
            FreeCAD.Console.PrintWarning('This tool works only on front, rear, top, bot, left, right views')
            mk_sketch=False
        doc.recompute()
        if mk_sketch:
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(doc.Name,sv.Name)
            sk = Draft.makeSketch(sv, autoconstraints=False, delete=False) #, radiusPrecision=0)
            sv.ViewObject.Visibility=False
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(doc.Name,sk.Name)
        if delete:
            doc.removeObject(cmp.Name)
            for o in eobj_list:
                doc.removeObject(o.Name)
        doc.recompute()
        doc.commitTransaction()
# end