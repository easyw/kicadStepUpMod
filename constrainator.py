#!/usr/bin/python
# -*- coding: utf-8 -*-
#****************************************************************************

## todo :
# ok  1) add a dialog to set tolerance and constraint type
# ok 2) remove only coincident and hor-vert pre-existent constraints
# ok 3) add constraints only if not already present a coincident constraint for that point
# ok 4) Line, Arcs, Bsplines, ArcOfEllipse are parsed
# 5) remove coindident bsplines (approx)

import FreeCAD, Part, Sketcher
from FreeCAD import Base
from math import sqrt

__ksuConstrainator_version__='1.2.2'

def sk_distance(p0, p1):
    return sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)
#

def sanitizeSkBsp(s_name, dist_tolerance):
    # s_name = 'Sketch001'
    s=FreeCAD.ActiveDocument.getObject(s_name)
    FreeCAD.Console.PrintWarning('check to sanitize\n')
    if 'Sketcher' in s.TypeId:
        FreeCAD.ActiveDocument.openTransaction('Sanitizing')
        idx_to_del = []
        geo_to_del = []
        inverted=False
        # check for duplicates in splines
        # NB!!! Knots are not reliable here to check!!!
        if 1: #len (s.Geometry) > 2: #cleaning algo approx valid for more than 2 splines
            for i,g in enumerate (s.Geometry):
                if 'BSplineCurve object' in str(g):
                    j=i+1
                    for bg in s.Geometry[(i + 1):]:
                        if 'BSplineCurve object' in str(bg):
                            if j not in idx_to_del:
                                if (len(g.getPoles()) == len(bg.getPoles())):
                                    #print('equal pole nbrs')
                                    eqp = True
                                    if sk_distance(g.StartPoint,bg.StartPoint) > dist_tolerance:
                                        if sk_distance(g.StartPoint,bg.EndPoint) > dist_tolerance:
                                            eqp = False
                                    if sk_distance(g.EndPoint,bg.EndPoint) > dist_tolerance:
                                        if sk_distance(g.EndPoint,bg.StartPoint) > dist_tolerance:
                                            eqp = False        
                                    if (eqp):
                                        if sk_distance(g.StartPoint,bg.StartPoint) > dist_tolerance:
                                            inverted=True
                                        else:
                                            inverted=False
                                        print ('identical splines, inverted=',inverted )
                                        #print(g.getPoles())
                                        #print(bg.getPoles())
                                        if j not in idx_to_del:
                                            print ('len ',len(bg.getPoles()))
                                            if inverted == False:
                                                for k,kn in enumerate (bg.getPoles()):
                                                    #a = float(kn); b = float(g.KnotSequence[k])
                                                    #print(k)
                                                    a = kn; b = g.getPole(k+1)
                                                    #print(kn,g.getPole(k+1))
                                                    #print('dif ',(float(kn)-float(g.KnotSequence[k])))
                                                    #print('abs ',abs(float(kn)-float(g.KnotSequence[k])))
                                                    #print(a,b)
                                                    #print(a[0],a[1],a[2])
                                                    #print(b[0],b[1],b[2])
                                                    #print('dif ',abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
                                                    #print('abs ',abs(a-b))
                                                    #if abs(float(kn)-float(g.KnotSequence[k])) > dist_tolerance:
                                                    if abs(a[0]-b[0]) > dist_tolerance or abs(a[1]-b[1]) > dist_tolerance or abs(a[2]-b[2]) > dist_tolerance:
                                                        print('node NOT coincident')
                                                        #print(a,b)
                                                        eqp=False
                                                        break # break the for loop
                                                    #print('next--')
                                            else:
                                                l = len(bg.getPoles())
                                                for k,kn in enumerate (bg.getPoles()):
                                                    #a = float(kn); b = float(g.KnotSequence[k])
                                                    #print(k)
                                                    a = kn; b = g.getPole(l-k)
                                                    #print(kn,g.getPole(l-k))
                                                    #print('dif ',(float(kn)-float(g.KnotSequence[k])))
                                                    #print('abs ',abs(float(kn)-float(g.KnotSequence[k])))
                                                    #print(a,b)
                                                    #print(a[0],a[1],a[2])
                                                    #print(b[0],b[1],b[2])
                                                    #print('dif ',abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))
                                                    #print('abs ',abs(a-b))
                                                    #if abs(float(kn)-float(g.KnotSequence[k])) > dist_tolerance:
                                                    if abs(a[0]-b[0]) > dist_tolerance or abs(a[1]-b[1]) > dist_tolerance or abs(a[2]-b[2]) > dist_tolerance:
                                                        print('node NOT coincident')
                                                        #print(a,b)
                                                        eqp=False
                                                        break # break the for loop
                                                    #print('next--')
                                            if (eqp):
                                                idx_to_del.append(j)
                        j+=1
        j=0
        #print(idx_to_del)
        if len(idx_to_del) >0:
            FreeCAD.Console.PrintMessage(u'sanitizing '+s.Label)
            FreeCAD.Console.PrintMessage('\n')
            idx_to_del.sort() 
            #print(idx_to_del)
            idx_to_del.reverse() 
            #print(idx_to_del)
            #stop
            for i, e in enumerate(idx_to_del):
                #print('to delete ',s.Geometry[(e)],e)
                print('deleting identical geo')
                #print(s.Geometry)
                s.delGeometry(e)
                #print(s.Geometry)
        FreeCAD.ActiveDocument.commitTransaction()
        return s.Geometry
    else:
        return None
##
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
    """ adding coincident points constraints """
    
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
            Part.ArcOfEllipse: [0,1,2,3], # 
            Part.Ellipse: [0,1], #
            Part.ArcOfHyperbola: [0,1,2], #
            Part.ArcOfParabola: [0,1,2], #
            Part.Point: [0], #
        }
    else:
        g_geom_points = {
            Base.Vector: [1],
            Part.Line: [1, 2],  # first point, last point
            Part.Circle: [0, 3],  # curve, center
            Part.ArcOfCircle: [1, 2, 3],  # first point, last point, center
            Part.BSplineCurve: [0,1,2,3], # for poles
            Part.ArcOfEllipse: [0,1,2,3], #
            Part.Point: [0], #
        }
    points=[]
    geoms=[]
    #print len((s.Geometry))
    #stop
    for geom_index in range(len((s.Geometry))):
        if hasattr(s,'GeometryFacadeList'):
            # Gm = s.GeometryFacadeList.Geometry
            Gc = s.GeometryFacadeList
        else:
            # Gm = s.Geometry
            Gc = s.Geometry
        #if not(s.Geometry[geom_index].Construction):
        if not(Gc[geom_index].Construction):
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
            elif 'ArcOfEllipse' in type(s.Geometry[geom_index]).__name__\
              or 'ArcOfHyperbola' in type(s.Geometry[geom_index]).__name__\
              or 'ArcOfParabola' in type(s.Geometry[geom_index]).__name__:
                point1 = s.getPoint(geom_index, point_indexes[1])
                point2 = s.getPoint(geom_index, point_indexes[2])
                tp = 'Arc'
                geoms.append([point1[0],point1[1],point2[0],point2[1],tp])
            elif 'Ellipse' in type(s.Geometry[geom_index]).__name__:
                pass
            elif 'Point' in type(s.Geometry[geom_index]).__name__:
                pass
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
