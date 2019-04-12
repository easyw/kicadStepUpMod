#!/usr/bin/python
# -*- coding: utf-8 -*-
#****************************************************************************

## todo :
# 1) add a dialog to set tolerance and constraint type
# 2) remove only coincident and hor-vert pre-existent constraints
# 3) add constraints only if not already present a coincident consstraint for that point
# 4) ATM only Line and Arcs are parsed

import FreeCAD, Part, Sketcher
from FreeCAD import Base
from math import sqrt

__ksuConstrainator_version__='1.1.5'

def sk_distance(p0, p1):
    return sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)
#
def sanitizeSk(s_name, edg_tol):
    ''' simplifying & sanitizing sketches '''
    #global edge_tolerance
    
    s=FreeCAD.ActiveDocument.getObject(s_name)
    FreeCAD.Console.PrintWarning('check to sanitize\n')
    if 'Sketcher' in s.TypeId:
        idx_to_del=[]
        for i,g in enumerate (s.Geometry):
            #print(g,i)
            if 'Line' in str(g):
                #print(g.length())
                if g.length() <= edg_tol:
                    FreeCAD.Console.PrintMessage(str(g)+' '+str(i)+' too short\n')
                    idx_to_del.append(i)
            elif 'Circle' in str(g):
                if g.Radius <= edg_tol:
                    FreeCAD.Console.PrintMessage(str(g)+' '+str(i)+' too short\n')
                    idx_to_del.append(i)
        j=0
        if len(idx_to_del) >0:
            FreeCAD.Console.PrintMessage(u'sanitizing '+s.Label)
            FreeCAD.Console.PrintMessage('\n')
        for i in idx_to_del:
            s.delGeometry(i-j)
            j+=1
##
def add_constraints(s_name, edge_tolerance, add_Constraints):
    """ adding coincident points constaints """
    
    s=FreeCAD.ActiveDocument.getObject(s_name)
    
    FreeCAD.Console.PrintMessage('Constrainator version '+__ksuConstrainator_version__+'\n')
    FreeCAD.Console.PrintMessage('adding '+add_Constraints+' constraints with '+str(edge_tolerance)+'mm tolerance\n' )
    if hasattr(Part,"LineSegment"):
        g_geom_points = {
            Base.Vector: [1],
            Part.LineSegment: [1, 2],  # first point, last point
            Part.Circle: [0, 3],  # curve, center
            Part.ArcOfCircle: [1, 2, 3],  # first point, last point, center
            Part.BSplineCurve: [0,1,2,3], # for poles
        }
    else:
        g_geom_points = {
            Base.Vector: [1],
            Part.Line: [1, 2],  # first point, last point
            Part.Circle: [0, 3],  # curve, center
            Part.ArcOfCircle: [1, 2, 3],  # first point, last point, center
            Part.BSplineCurve: [0,1,2,3], # for poles
        }
    points=[]
    geoms=[]
    #print len((s.Geometry))
    #stop
    for geom_index in range(len((s.Geometry))):
        point_indexes = g_geom_points[type(s.Geometry[geom_index])]
        #sayerr(point_indexes), say (geom_index)
        #if 'Line' in type(PCB_Sketch.Geometry[geom_index]).__name__:
        
        if 'ArcOfCircle' in type(s.Geometry[geom_index]).__name__\
         or 'Line' in type(s.Geometry[geom_index]).__name__:
            point1 = s.getPoint(geom_index, point_indexes[0])
            #sayerr(str(point1[0])+';'+str(point1[1]))
            point2 = s.getPoint(geom_index, point_indexes[1])
            #sayw(str(point2[0])+';'+str(point1[1]))
            #points.append([[point1[0],point1[1]],[geom_index],[1]])
            #points.append([[point2[0],point2[1]],[geom_index],[2]])
            #points.append([[point1[0],point1[1]],[geom_index]]) #,[1]])
            #points.append([[point2[0],point2[1]],[geom_index]]) #,[2]])
            if 'Line' in type(s.Geometry[geom_index]).__name__:
                tp = 'Line'
            else:
                tp = 'Arc'
            geoms.append([point1[0],point1[1],point2[0],point2[1],tp])

    #
    #print geom
    sk_constraints = []
    cnt=1
    # print addConstraints, ' constraints'
    # stop
    if add_Constraints=='all':
        if hasattr (FreeCAD.ActiveDocument.getObject(s_name), "autoconstraint"):
            FreeCAD.Console.PrintWarning('using constrainator -> coincident\n')
            sanitizeSk(s_name, edge_tolerance)
            sk1=FreeCAD.ActiveDocument.getObject(s_name)
            sk1.detectMissingPointOnPointConstraints(edge_tolerance)
            sk1.makeMissingPointOnPointCoincident()
            FreeCAD.activeDocument().recompute()
            sk1.autoRemoveRedundants(True)
            sk1.solve()
            FreeCAD.activeDocument().recompute()
            FreeCAD.Console.PrintWarning('using constrainator -> H&V\n')
            for i, geo in enumerate(geoms):
            #for i in range(len(geom)):
                p_g0_0=[geo[0],geo[1]]
                p_g0_1=[geo[2],geo[3]]
                #print p_g0_0,pg_g0_1
                #sayw(abs(p_g0_0[0]-p_g0_1[0]))
                if abs(p_g0_0[0]-p_g0_1[0])< edge_tolerance and geo[4] == 'Line':
                    #s.addConstraint(Sketcher.Constraint('Vertical',i))
                    sk_constraints.append(Sketcher.Constraint('Vertical',i))
                elif abs(p_g0_0[1]-p_g0_1[1])< edge_tolerance and geo[4] == 'Line':
                    #s.addConstraint(Sketcher.Constraint('Horizontal',i))
                    sk_constraints.append(Sketcher.Constraint('Horizontal',i))
                j=i+1
        else:
            for i, geo in enumerate(geoms):
            #for i in range(len(geom)):
                p_g0_0=[geo[0],geo[1]]
                p_g0_1=[geo[2],geo[3]]
                #print p_g0_0,pg_g0_1
                #sayw(abs(p_g0_0[0]-p_g0_1[0]))
                if abs(p_g0_0[0]-p_g0_1[0])< edge_tolerance and geo[4] == 'Line':
                    #s.addConstraint(Sketcher.Constraint('Vertical',i))
                    sk_constraints.append(Sketcher.Constraint('Vertical',i))
                elif abs(p_g0_0[1]-p_g0_1[1])< edge_tolerance and geo[4] == 'Line':
                    #s.addConstraint(Sketcher.Constraint('Horizontal',i))
                    sk_constraints.append(Sketcher.Constraint('Horizontal',i))
                j=i+1
                FreeCAD.Console.PrintWarning('using old constrainator\n')
                for geo2 in geoms[(i + 1):]:
                    p_g1_0=[geo2[0],geo2[1]]
                    p_g1_1=[geo2[2],geo2[3]]
                    #rint p_g0_0, p_g0_1
                    #rint p_g1_0, p_g1_1
                    if sk_distance(p_g0_0,p_g1_0)< edge_tolerance:
                    ##App.ActiveDocument.PCB_Sketch.addConstraint(Sketcher.Constraint('Coincident',0,2,3,1)) 
                        #s.addConstraint(Sketcher.Constraint('Coincident',i,1,j,1))
                        sk_constraints.append(Sketcher.Constraint('Coincident',i,1,j,1))
                        #print i,1,i+1,1
                    elif sk_distance(p_g0_0,p_g1_1)< edge_tolerance:
                        #s.addConstraint(Sketcher.Constraint('Coincident',i,1,j,2))
                        sk_constraints.append(Sketcher.Constraint('Coincident',i,1,j,2))
                        #print i,1,i+1,2
                    elif sk_distance(p_g0_1,p_g1_0)< edge_tolerance:
                        #s.addConstraint(Sketcher.Constraint('Coincident',i,2,j,1))
                        sk_constraints.append(Sketcher.Constraint('Coincident',i,2,j,1))
                        #print i,2,i+1,1
                    elif sk_distance(p_g0_1,p_g1_1)< edge_tolerance:
                        #s.addConstraint(Sketcher.Constraint('Coincident',i,2,j,2))
                        sk_constraints.append(Sketcher.Constraint('Coincident',i,2,j,2))                   
                        #print i,2,i+1,2
                    j=j+1
                    cnt=cnt+1
    elif add_Constraints=='coincident':
        if hasattr (FreeCAD.ActiveDocument.getObject(s_name), "autoconstraint"):
            FreeCAD.Console.PrintWarning('using constrainator\n')
            sanitizeSk(s_name, edge_tolerance)
            sk1=FreeCAD.ActiveDocument.getObject(s_name)
            sk1.detectMissingPointOnPointConstraints(edge_tolerance)
            sk1.makeMissingPointOnPointCoincident()
            FreeCAD.activeDocument().recompute()
            sk1.autoRemoveRedundants(True)
            sk1.solve()
            FreeCAD.activeDocument().recompute()
        else:
            FreeCAD.Console.PrintWarning('using old constrainator\n')
            for i, geo in enumerate(geoms):
            #for i in range(len(geom)):
                p_g0_0=[geo[0],geo[1]]
                p_g0_1=[geo[2],geo[3]]
                #print p_g0_0,pg_g0_1
                #if add_Constraints=='all':
                #    if abs(p_g0_0[0]-p_g0_1[0])< edge_tolerance:
                #        s.addConstraint(Sketcher.Constraint('Vertical',i))
                #    elif abs(p_g0_0[1]-p_g0_1[1])< edge_tolerance:
                #        s.addConstraint(Sketcher.Constraint('Horizontal',i))
                j=i+1
                for geo2 in geoms[(i + 1):]:
                    p_g1_0=[geo2[0],geo2[1]]
                    p_g1_1=[geo2[2],geo2[3]]
                    #rint p_g0_0, p_g0_1
                    #rint p_g1_0, p_g1_1
                    if sk_distance(p_g0_0,p_g1_0)< edge_tolerance:
                    ##App.ActiveDocument.PCB_Sketch.addConstraint(Sketcher.Constraint('Coincident',0,2,3,1)) 
                        #s.addConstraint(Sketcher.Constraint('Coincident',i,1,j,1))
                        sk_constraints.append(Sketcher.Constraint('Coincident',i,1,j,1))
                        #print i,1,i+1,1
                    elif sk_distance(p_g0_0,p_g1_1)< edge_tolerance:
                        #s.addConstraint(Sketcher.Constraint('Coincident',i,1,j,2))
                        sk_constraints.append(Sketcher.Constraint('Coincident',i,1,j,2))
                        #print i,1,i+1,2
                    elif sk_distance(p_g0_1,p_g1_0)< edge_tolerance:
                        #s.addConstraint(Sketcher.Constraint('Coincident',i,2,j,1))
                        sk_constraints.append(Sketcher.Constraint('Coincident',i,2,j,1))                    
                        #print i,2,i+1,1
                    elif sk_distance(p_g0_1,p_g1_1)< edge_tolerance:
                        #s.addConstraint(Sketcher.Constraint('Coincident',i,2,j,2))
                        sk_constraints.append(Sketcher.Constraint('Coincident',i,2,j,2))
                        #print i,2,i+1,2
                    j=j+1
                    cnt=cnt+1
    if len(sk_constraints) > 0:
        old_sk_constraints = []
        for c in s.Constraints:
            #sayw(c)
            #if add_Constraints=='coincident':
            #    say('c')
            if (add_Constraints == "coincident"):
                if ("Coincident" not in str(c)):
                    old_sk_constraints.append(c)
                    #say('appending '+str(c))
            elif (add_Constraints=='all'):
                if hasattr (FreeCAD.ActiveDocument.getObject(s_name), "autoconstraint"):
                    if ('Vertical' not in str(c)) and ('Horizontal' not in str(c)):
                        old_sk_constraints.append(c)
                elif ('Coincident' not in str(c)) and ('Vertical' not in str(c)) and ('Horizontal' not in str(c)):
                    old_sk_constraints.append(c)
                    #say('appending all '+str(c))

        s.Constraints = []
        #sayw(old_sk_constraints)
        for oc in old_sk_constraints:
            sk_constraints.append(oc)
        #say(sk_constraints)
        s.addConstraint(sk_constraints)
        FreeCAD.ActiveDocument.recompute()
        #print 'counter ',cnt
            #print geo2
            
###
