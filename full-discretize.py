 #!/usr/bin/python
# -*- coding: utf-8 -*-
#****************************************************************************

import FreeCAD, FreeCADGui
import sys,os
import Draft
import PySide
from PySide import QtGui, QtCore

q_deflection = 0.005 #0.02 ##0.005
tol = 0.01
constr = 'coincident' #'all'

sel = FreeCADGui.Selection.getSelection()
if len(sel) != 1:
    reply = QtGui.QMessageBox.information(None,"Warning", "select one single object to be discretized")
    FreeCAD.Console.PrintError('select one single object to be discretized\n')
else:
    FreeCAD.ActiveDocument.openTransaction("Discretizing") #open a transaction for undo management
    shapes = []
    for selobj in sel:
        for e in selobj.Shape.Edges:
            shapes.append(Part.makePolygon(e.discretize(QuasiDeflection=q_deflection)))
    Draft.makeSketch(shapes)
    sk_d = FreeCAD.ActiveDocument.ActiveObject
    if sk_d is not None:
        FreeCADGui.ActiveDocument.getObject(sk_d.Name).LineColor = (1.00,1.00,1.00)
        FreeCADGui.ActiveDocument.getObject(sk_d.Name).PointColor = (1.00,1.00,1.00)
        max_geo_admitted = 1500 # after this number, no recompute is applied
        if len (sk_d.Geometry) < max_geo_admitted:
            FreeCAD.ActiveDocument.recompute()
    import constrainator
    constrainator.add_constraints(sk_d.Name, tol, constr)
    skt = FreeCAD.ActiveDocument.getObject(sk_d.Name)
    if hasattr(skt, 'OpenVertices'):
        openVtxs = skt.OpenVertices
        if len(openVtxs) >0:
            FreeCAD.Console.PrintError("Open Vertexes found.\n")
            FreeCAD.Console.PrintWarning(str(openVtxs)+'\n')
            msg = """Open Vertexes found.<br>"""+str(openVtxs)
            reply = QtGui.QMessageBox.information(None,"info", msg)
    FreeCADGui.ActiveDocument.getObject(sel[0].Name).Visibility=False
    shp = skt.Shape
    ofs=[0.0,0.0]
    edge_width = 0.1 
    edges = shp.Edges
    segments_nbr=len(edges)
    fillzone = """  (zone (net 0) (net_name "") (layer B.Cu) (tstamp 0) (hatch edge 0.508)"""+os.linesep
    fillzone+="""    (connect_pads (clearance 0.508))"""+os.linesep
    fillzone+="""    (min_thickness 0.254)"""+os.linesep
    fillzone+="""    (fill yes (arc_segments 32) (thermal_gap 0.508) (thermal_bridge_width 0.508))"""+os.linesep
    fillzone+="""    (polygon"""+os.linesep
    i=1
    pts = "      (pts "+os.linesep
    for e in edges:
        if 'Line' not in e.Curve.TypeId:
            stop
        e0x = e.Vertexes[0].Point.x
        e0y = e.Vertexes[0].Point.y
        e1x = e.Vertexes[1].Point.x
        e1y = e.Vertexes[1].Point.y
        #print(e0x,e0y)
        #print(e1x,e1y)
        #k_edg = "  (gr_line (start {0:.3f} {1:.3f}) (end {2:.3f} {3:.3f}) (angle 0) (layer {5}) (width {4}))"\
        #                .format(x1+ofs[0], y1+ofs[1], x2+ofs[0], y2+ofs[1], edge_width, layer)
        if i < segments_nbr:
            pts=pts+"         (xy {0:.3f} {1:.3f}) (xy {2:.3f} {3:.3f})".format(e0x+ofs[0], -e0y+ofs[1], e1x+ofs[0], -e1y+ofs[1])+os.linesep
        else:
            pts=pts+"         (xy {0:.3f} {1:.3f})".format(e0x+ofs[0], -e0y+ofs[1])+os.linesep+"      )"+os.linesep
        
        #if i < segments_nbr:
        #    pts=pts+"         (xy "+str(e0x)+" "+str(-1*e0y)+") (xy "+str(e1x)+" "+str(-1*e1y)+")"+os.linesep
        #else:
        #    pts=pts+"         (xy "+str(e0x)+" "+str(-1*e0y)+")"+os.linesep+"      )"+os.linesep
        i=i+1
    fillzone += pts
    fillzone+="    )"+os.linesep+"  )"+os.linesep #+")"+os.linesep
    print(fillzone)
    FreeCAD.ActiveDocument.commitTransaction()
    with open("/home/mau/Downloads/out.txt", "wb") as f:
        f.write(fillzone.encode('utf-8'))

