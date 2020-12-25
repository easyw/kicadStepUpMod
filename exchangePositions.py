# -*- coding: utf-8 -*-
#

## https://www.freecadweb.org/wiki/Placement
# App.ActiveDocument.Cylinder.Placement=App.Placement(App.Vector(0,0,0), App.Rotation(10,20,30), App.Vector(0,0,0)) 
# App.Rotation(10,20,30) = Euler Angle 
## https://forum.freecadweb.org/viewtopic.php?t=11799

__version_exchPos__ = "1.2.1"


import FreeCAD, FreeCADGui,sys, os 
from FreeCAD import Base
import Part

import PySide 
from PySide import QtGui, QtCore
#from PySide.QtGui import QTreeWidgetItemIterator
import ksu_locator

from os.path import expanduser
import difflib, re, time, datetime

FreeCAD.Console.PrintWarning('MCAD export/check version ='+ str(__version_exchPos__)+'\n')

generateSketch = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui").GetBool('generate_sketch')


generate_sketch=True

def PLine(prm1,prm2):
    if hasattr(Part,"LineSegment"):
        return Part.LineSegment(prm1, prm2)
    else:
        return Part.Line(prm1, prm2)

def get_Selected ():
    InListRec=[]
    InListRecSelEx=FreeCADGui.Selection.getSelectionEx('',False)[0]
    InListRecSubEN=InListRecSelEx.SubElementNames
    print (InListRecSubEN)
    if len (InListRecSubEN) >=1:
        InListRec.append(InListRecSelEx.Object.Name)
        InListRec.extend(InListRecSubEN[0].split('.'))
        print (InListRec)
        if len(InListRec)>1:
            ro = InListRec.pop()
        for oName in InListRec:
            print ('hierarchy \"'+FreeCAD.ActiveDocument.getObject(oName).Label+'\"')
        #print (InListRec[:-1])
        print (InListRec)
    print ('top Level Obj \"'+InListRecSelEx.Object.Label+'\"')
    if len(InListRec) > 0:
        print ('Selected  Obj \"'+FreeCAD.ActiveDocument.getObject(InListRec[-1]).Label+'\"')
    else:
        print ('Selected  Obj \"'+InListRecSelEx.Object.Label+'\"')
    print (InListRec)
    #print (len(InListRecSubEN));print (len(InListRec))

def get_sorted_list (obj):
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
    #print(listUsName)
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
def gui_addSelection(obj):
    if hasattr(obj,'InListExRecursive'): #asm3 A3 present
        #ol=obj.InListRecursive
        ol = get_sorted_list (obj)
        #print (ol)
        #print (len(ol))
        #to_add=ol[len(ol)-1].Name+','
        to_add=''
        #for i in range(len(ol),1,-1):
        for i in range(1, len(ol)):
            #to_add += ol[i-2].Name+'.'
            to_add += ol[i].Name+'.'
        to_add += obj.Name+'.'
        #to_add +=','
        #print (to_add);
        #print (str(ol[len(ol)-1].Name+','+to_add+','))
        #FreeCADGui.Selection.addSelection(ol[len(ol)-1],to_add,)
        #FreeCADGui.Selection.addSelection(obj)
        #get_Selected()
        #print (str(ol[0].Name+','+to_add+','))
        FreeCADGui.Selection.addSelection(ol[0],to_add,)
    else:
        FreeCADGui.Selection.addSelection(obj)
    #stop
##

def decimals(f,n):
    v = str(round(f,n))
    if '.' in v:
        if (len(v[v.find('.'):]) > n+1):
            v = v[:len(v)-1]
    return float(v)

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

def trunc (f,n):
    s=str(f)
    l=len(s)
    dp=(s.find('.'))
    if dp+n+1 < l:
        s=s[:dp+n+1]
    return s
    
def roundMatrix(mtx):
    mtxR = [] #mtx
    for i, v in enumerate (mtx.A):
        n_dec = 4
        rv = str(round(v,n_dec))
        l=len(rv)
        if '.' in rv:
            if (len(rv[rv.find('.'):]) > n_dec):
                #print (rv);print (rv.find('.'))
                rv = rv[:l-1]
                #print (rv)
        rv = rv.replace('-0.0','0.0')
        #rv = truncate(v, 3)
        #rv = trunc(v,3)
        mtxR.append(float(rv))
        #mtxR.append(rv)
        #mtxR.append((str(rv).replace('-0.0','0.0')))
    return mtxR
###
def roundEdge(edg):    
    if 'Line' in str(edg):
        #print (str(edg))
        ps = edg.StartPoint; psx=round(ps.x,3);psy=round(ps.y,3);psz=round(ps.z,3)
        pe = edg.EndPoint; pex=round(pe.x,3);pey=round(pe.y,3);pez=round(pe.z,3)
        return PLine(Base.Vector(psx,psy,psz), Base.Vector(pex,pey,pez))
    elif 'ArcOfCircle' in str(edg):
        #print (str(edg))
        #v=FreeCAD.Vector
        c=edg.Center;cx=round(c[0],3);cy=round(c[1],3);cz=round(c[0],3);
        r=round(edg.Radius,3);axis=edg.Axis
        sa=round(edg.FirstParameter,4);ea=round(edg.LastParameter,4)
        return Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(cx,cy,cz),axis,r),sa,ea)        
    elif 'Circle' in str(edg):
        #print (str(edg))
        c=edg.Center;cx=round(c[0],3);cy=round(c[1],3);cz=round(c[0],3);
        r=round(edg.Radius,3);axis=edg.Axis
        return Part.Circle(FreeCAD.Vector(cx,cy,cz),axis,r)
##
def roundVal(v,n_dec=None):
    #round to n_dec after '.'
    if n_dec is None:
        n_dec = 3
    v=float(v)
    rv = str(round(v,n_dec+1))
    l=len(rv)
    if '.' in rv:
        if (len(rv[rv.find('.'):]) > n_dec+1):
            #print (rv);print (rv.find('.'))
            rv = rv[:l-1]
            #print (rv)
    rv = rv.replace('-0.0','0.0')
    #rv = truncate(v, 3)
    #rv = trunc(v,3)
    return(float(rv))
###
def rmvSuffix(doc=None):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    for ob in doc.Objects:
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
                    o.Label = re.sub('.stp', '', o.Label, flags=re.IGNORECASE)
                    o.Label = re.sub('.step', '', o.Label, flags=re.IGNORECASE)
                    #print (o.Label)
                if o.TypeId == 'App::Part' or o.TypeId == 'App::LinkGroup':
                    o.Label = re.sub('_stp', '', o.Label, flags=re.IGNORECASE)
                    o.Label = re.sub('_step', '', o.Label, flags=re.IGNORECASE)
                    o.Label = re.sub('.stp', '', o.Label, flags=re.IGNORECASE)
                    o.Label = re.sub('.step', '', o.Label, flags=re.IGNORECASE)                              
            for o in o_list:
                if (o.TypeId == 'App::Link'):
                    o.Label = o.LinkedObject.Label
    FreeCAD.Console.PrintWarning('removed Suffix \'.stp\', \'.step\' \n')
##
  
def expPos(doc=None):  ## export positions
    if doc is None:
        doc = FreeCAD.ActiveDocument
    # rmvSuffix(doc)
    full_content=[]
    positions_content=[]
    sketch_content=[];sketch_content_header=[]
    #if doc is not None:
    if len(doc.FileName) == 0:
        docFn = 'File Not Saved'
    else:
        docFn = doc.FileName
    line='title: '+doc.Name
    full_content.append(line+'\n')
    line = 'FileN: '+docFn
    full_content.append(line+'\n')
    print(line)
    line='date :'+str(datetime.datetime.now())
    full_content.append(line+'\n')
    print(line)
    line='3D models Placement ---------------'
    full_content.append(line+'\n')
    print(line)
    for o in doc.Objects:
        # print(o.Name,o.Label,o.TypeId)
        if (hasattr(o, 'Shape') or o.TypeId == 'App::Link') and (hasattr(o, 'Placement')) and (o.TypeId != 'App::Line') and (o.TypeId != 'App::Plane'):
            if 'Sketch' not in o.Label and 'Pcb' not in o.Label:
                #print(o.Placement.Rotation.Q[3])
                # oPlacement = 'Placement [Pos=('+"{0:.2f}".format(o.Placement.Base.x,3)+','+"{0:.2f}".format(o.Placement.Base.y)+','+"{0:.2f}".format(o.Placement.Base.z)+\
                # '), Yaw-Pitch-Roll=('+"{0:.2f}".format(o.Placement.Rotation.toEuler()[0]*qsign)+','+"{0:.2f}".format(o.Placement.Rotation.toEuler()[1])+\
                # ','+"{0:.2f}".format(o.Placement.Rotation.toEuler()[2])+')]'
                #oPlacement=oPlacement.replace('-0.00','0.00')
                if 0:
                    oPl=str(o.Placement)
                    Pos=oPl[oPl.find('(')+1:oPl.find(')')].split(',')
                    PosN=[]
                    for p in Pos:
                        p=float(p);PosN.append(p)    
                    Ypr=oPl[oPl.rfind('(')+1:oPl.rfind(')')].split(',')
                    YprN=[]
                    for a in Ypr:
                        a=float(a);YprN.append(a)
                    oPlacement = 'Placement [Pos=('+"{0:.2f}".format(PosN[0])+','+"{0:.2f}".format(PosN[1])+','+"{0:.2f}".format(PosN[2])+','+\
                        '), Yaw-Pitch-Roll=('+"{:.2f}".format(YprN[0])+','+"{:.2f}".format(YprN[1])+','+"{:.2f}".format(YprN[2])+')]'
                    line=o.Label[:o.Label.find('_')]+','+oPlacement
                    positions_content.append(line+'\n')
                    line=o.Label[:o.Label.find('_')]+','+str(o.Placement)+' Q '+str(o.Placement.Rotation.Q)
                    positions_content.append(line+'\n')
                    # https://forum.freecadweb.org/viewtopic.php?f=8&t=25737&start=10
                # line=o.Label[:o.Label.find('_')]+','+ str(o.Placement.toMatrix())
                # positions_content.append(line+'\n')
                # print (line)
                rMtx=roundMatrix(o.Placement.toMatrix())
                line=o.Label[:o.Label.find('_')]+', P.Mtx('+ str(rMtx)+')'
                positions_content.append(line+'\n')
                print (line)
            if o.Label == 'PCB_Sketch':
                line='Sketch geometry -------------------'
                sketch_content_header.append(line+'\n')
                print('Sketch geometry -------------------')
                if hasattr(o,'Geometry'):
                    if hasattr(o,'GeometryFacadeList'):
                        Gm = o.GeometryFacadeList
                        for e in Gm:
                            if not e.Construction:
                                line=str(roundEdge(e.Geometry))
                                sketch_content.append(line+'\n')
                                #print (e) 
                    else:
                        for e in o.Geometry:
                            if not e.Construction:
                                line=str(roundEdge(e))
                                sketch_content.append(line+'\n')
                                #print (e) 
                sketch_content.sort()
                sketch_content[:0] = sketch_content_header
                line='-----------------------------------'
                sketch_content.append(line+'\n')
                print(line)
            if o.Label == 'Pcb':
                line='Pcb Volume -------------------'
                sketch_content.append(line+'\n')
                print(line)
                vol = o.Shape.Volume
                vol = decimals(vol,3)
                line = 'Pcb Volume = ' + str(vol)
                sketch_content.append(line+'\n')
                print (line) 
                line='-----------------------------------'
                sketch_content.append(line+'\n')
                print(line)
    positions_content.sort()
    full_content.extend(positions_content)
    full_content.extend(sketch_content)
    line='END of List -----------------------'
    full_content.append(line+'\n')
    print(line)
    testing=False
    pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
    if not pg.IsEmpty():
        lastPath = pg.GetString('lastPath') 
    if len(lastPath)==0:
        home = expanduser("~")
        pg.SetString('lastPath', home) 
    else:
        home = lastPath
    if not testing:
        Filter=""
        name, Filter = PySide.QtGui.QFileDialog.getSaveFileName(None, "Write 3D models & footprint positions to a Report file ...",
            home, "*.rpt")
        #path, fname = os.path.split(name)
        #fname=os.path.splitext(fname)[0]
        #fpth = os.path.dirname(os.path.abspath(__file__))
        if name:
            lastPath = os.path.dirname(os.path.abspath(name))
            pg.SetString('lastPath', lastPath)
    else:
        if os.path.isdir("d:/Temp/"):
            name='d:/Temp/ex2.rpt'
        elif os.path.isdir("c:/Temp/"):
            name='c:/Temp/ex2.rpt'                        
    #say(name)
    if name:
        #if os.path.exists(name):
        f = open(name, "w")
        f.write(''.join(full_content))
        f.close

##
def cmpPos(doc=None):  ## compare exported positions with the selected doc
    if doc is None:
        doc = FreeCAD.ActiveDocument
    # rmvSuffix(doc)
    full_content=[]
    positions_content=[]
    sketch_content=[];sketch_content_header=[]
    #if doc is not None:
    if len(doc.FileName) == 0:
        docFn = 'File Not Saved'
    else:
        docFn = doc.FileName
    line='title: '+doc.Name
    full_content.append(line+'\n')
    line = 'FileN: '+docFn
    full_content.append(line+'\n')
    #print(line)
    line='date :'+str(datetime.datetime.now())
    full_content.append(line+'\n')
    #print(line)
    line='3D models Placement ---------------'
    full_content.append(line+'\n')
    #print(line)
    for o in doc.Objects:
        # print(o.Name,o.Label,o.TypeId)
        if (hasattr(o, 'Shape') or o.TypeId == 'App::Link') and (hasattr(o, 'Placement')) and (o.TypeId != 'App::Line') and (o.TypeId != 'App::Plane'):
            if 'Sketch' not in o.Label and 'Pcb' not in o.Label:
                #oPlacement = 'Placement [Pos=('+"{0:.3f}".format(o.Placement.Base.x)+','+"{0:.3f}".format(o.Placement.Base.y)+','+"{0:.3f}".format(o.Placement.Base.z)+\
                #'), Yaw-Pitch-Roll=('+"{0:.3f}".format(o.Placement.Rotation.toEuler()[0])+','+"{0:.3f}".format(o.Placement.Rotation.toEuler()[1])+','+"{0:.3f}".format(o.Placement.Rotation.toEuler()[2])+')]'
                #oPlacement = 'Placement [Pos=('+"{0:.2f}".format(o.Placement.Base.x)+','+"{0:.2f}".format(o.Placement.Base.y)+','+"{0:.2f}".format(o.Placement.Base.z)+\
                #'), Yaw-Pitch-Roll=('+"{0:.2f}".format(o.Placement.Rotation.toEuler()[0])+','+"{0:.2f}".format(o.Placement.Rotation.toEuler()[1])+','+"{0:.2f}".format(o.Placement.Rotation.toEuler()[2])+')]'
                #oPlacement=oPlacement.replace('-0.00','0.00')
                #line=o.Label[:o.Label.find('_')]+','+oPlacement
                # line=o.Label[:o.Label.find('_')]+','+ str(o.Placement.toMatrix())
                # positions_content.append(line+'\n')
                # print (line)
                rMtx=roundMatrix(o.Placement.toMatrix())
                line=o.Label[:o.Label.find('_')]+', P.Mtx('+ str(rMtx)+')'
                positions_content.append(line+'\n')
                #print (line)    
        if o.Label == 'PCB_Sketch':
            line='Sketch geometry -------------------'
            sketch_content_header.append(line+'\n')
            #print('Sketch geometry -------------------')
            if hasattr(o,'Geometry'):
                if hasattr(o,'Geometry'):
                    if hasattr(o,'GeometryFacadeList'):
                        Gm = o.GeometryFacadeList
                        for e in Gm:
                            if not e.Construction:
                                line=str(roundEdge(e.Geometry))
                                sketch_content.append(line+'\n')
                                #print (e) 
                    else:
                        Gm = o.Geometry
                        for e in Gm:
                            if not e.Construction:
                                line=str(roundEdge(e))
                                sketch_content.append(line+'\n')
                                #print (e) 
            sketch_content.sort()
            sketch_content[:0] = sketch_content_header
            #sketch_content_header.extend(sketch_content)
            #sketch_content=[]
            #sketch_content=sketch_content_header
            line='-----------------------------------'
            sketch_content.append(line+'\n')
            #print(line)
        if o.Label == 'Pcb':
            line='Pcb Volume -------------------'
            sketch_content.append(line+'\n')
            #print(line)
            vol = o.Shape.Volume
            vol = decimals(vol,3)
            line = 'Pcb Volume = ' + str(vol)
            sketch_content.append(line+'\n')
            #print (line) 
            line='-----------------------------------'
            sketch_content.append(line+'\n')
            #print(line)
    positions_content.sort()
    full_content.extend(positions_content)
    full_content.extend(sketch_content)
    line='END of List -----------------------'
    full_content.append(line+'\n')
    #print(line)
    testing=False
    pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
    if not pg.IsEmpty():
        lastPath = pg.GetString('lastPath') 
    if len(lastPath)==0:
        home = expanduser("~")
        pg.SetString('lastPath', home) 
    else:
        home = lastPath
    #home = expanduser("~")
    #home = r'C:\Cad\Progetti_K\board-revision\SolidWorks-2018-09-03_fede'
    if not testing:
        Filter=""
        name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open 3D models & footprint positions Report file\nto compare positions with the Active Document...",
            home, "*.rpt")
        #path, fname = os.path.split(name)
        #fname=os.path.splitext(fname)[0]
        #fpth = os.path.dirname(os.path.abspath(__file__))
        if name:
            lastPath = os.path.dirname(os.path.abspath(name))
            pg.SetString('lastPath', lastPath)
    else:
        if os.path.isdir("d:/Temp/"):
            name='d:/Temp/ex2.rpt'
        elif os.path.isdir("c:/Temp/"):
            name='c:/Temp/ex2.rpt'                        
    #say(name)
    if os.path.exists(name):
        with open(name) as a:
            a_content = a.readlines()
        b_content = full_content
        #print (a_content);print ('-----------b_c----------');print (b_content);stop
        diff = difflib.unified_diff(a_content,b_content)
        diff_content=[]
        diff_list=[]
        sk_add=[]
        sk_sub=[]
        header="***** Unified diff ************"
        diff_content.append(header+os.linesep)
        #print(header)
        header1="Line no"+5*' '+'previous'+5*' '+'updated'
        #print("Line no"+'\t'+'file1'+'\t'+'file2')
        #print(header1)
        diff_content.append(header1+os.linesep)
        for i,line in enumerate(diff):
            if line.startswith("-"):
                if not line.startswith("---") and not line.startswith("-title") \
                        and not line.startswith("-FileN") and not line.startswith("-date "):
                    #print(i,'\t\t'+line)
                    #print('Ln '+str(i)+(8-(len(str(i))))*' '),(line),
                    diff_content.append('Ln '+str(i)+(8-len(str(i)))*' '+line)
                    if line.startswith('-<Line'):
                        points=line.replace('-<Line segment (','').replace(') >','')
                        p1 = points[:points.find(')')].split(',')
                        p2 = points[points.rfind('(')+1:-1].split(',')
                        sk_sub.append(PLine(Base.Vector(round(float(p1[0]),3),round(float(p1[1]),3),round(float(p1[2]),3)), Base.Vector(float(p2[0]),float(p2[1]),float(p2[2]))))
                    elif line.startswith('-ArcOfCircle'):
                        data=line.replace('-ArcOfCircle (Radius : ','').replace('))\n','')
                        data=data.split(':')
                        radius = data[0].split(',')[0]
                        pos = data[1][data[1].find('(')+1:data[1].find(')')].split(',')
                        dir = data[2][data[2].find('(')+1:data[2].rfind(')')].split(',')
                        par = data[3][data[3].find('(')+1:].split(',')
                        #print (radius,pos,dir,par);stop
                        sk_sub.append(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(round(float(pos[0]),3),round(float(pos[1]),3),round(float(pos[2]),3)),FreeCAD.Vector(float(dir[0]),float(dir[1]),float(dir[2])),round(float(radius),3)),round(float(par[0]),5),round(float(par[1]),5)))
                    elif line.startswith('-Circle'):
                        data=line.replace('-Circle (Radius : ','').replace('))\n','')
                        data=data.split(':')
                        radius = data[0].split(',')[0]
                        pos = data[1][data[1].find('(')+1:data[1].find(')')].split(',')
                        dir = data[2][data[2].find('(')+1:].split(',')
                        print (radius,pos,dir)
                        sk_sub.append(Part.Circle(FreeCAD.Vector(round(float(pos[0]),3),round(float(pos[1]),3),round(float(pos[2]),3)),FreeCAD.Vector(float(dir[0]),float(dir[1]),float(dir[2])),round(float(radius),3)))
            elif line.startswith("+"):
                if not line.startswith("+++") and not line.startswith("+title") \
                        and not line.startswith("+FileN") and not line.startswith("+date "):
                    #print(i,'\t\t'+line)
                    #print('Ln '+str(i)+(8-(len(str(i))))*' '),(line),
                    diff_content.append('Ln '+str(i)+(8-len(str(i)))*' '+line)
                    diff_list.append(line[1:])
                    if line.startswith('+<Line'):
                        points=line.replace('+<Line segment (','').replace(') >','')
                        p1 = points[:points.find(')')].split(',')
                        p2 = points[points.rfind('(')+1:-1].split(',')
                        sk_add.append(PLine(Base.Vector(float(p1[0]),float(p1[1]),float(p1[2])), Base.Vector(float(p2[0]),float(p2[1]),float(p2[2]))))
                    #    sk_add.append(line.replace('+<Line segment ','').replace(' >',''))
                    elif line.startswith('+ArcOfCircle'):
                        data=line.replace('+ArcOfCircle (Radius : ','').replace('))\n','')
                        data=data.split(':')
                        radius = data[0].split(',')[0]
                        pos = data[1][data[1].find('(')+1:data[1].find(')')].split(',')
                        dir = data[2][data[2].find('(')+1:data[2].rfind(')')].split(',')
                        par = data[3][data[3].find('(')+1:].split(',')
                        #print (radius,pos,dir,par);stop
                        sk_add.append(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(float(pos[0]),float(pos[1]),float(pos[2])),FreeCAD.Vector(float(dir[0]),float(dir[1]),float(dir[2])),float(radius)),float(par[0]),float(par[1])))
                    elif line.startswith('+Circle'):
                        data=line.replace('+Circle (Radius : ','').replace('))\n','')
                        data=data.split(':')
                        radius = data[0].split(',')[0]
                        pos = data[1][data[1].find('(')+1:data[1].find(')')].split(',')
                        dir = data[2][data[2].find('(')+1:].split(',')
                        print (radius,pos,dir)
                        sk_add.append(Part.Circle(FreeCAD.Vector(float(pos[0]),float(pos[1]),float(pos[2])),FreeCAD.Vector(float(dir[0]),float(dir[1]),float(dir[2])),float(radius)))
        #for d in (diff_content):
        #    print (d)
        #for d in (diff_list):
        #    print(d)
        #diff_content = a_content + b_content
        try:
            f = open(home+"\list_diff.lst", "w")
            f.write(''.join(diff_content))
            f.close
        except:
            FreeCAD.Console.PrintError('Error in write permission for \'list_diff.lst\' report file.\n')
        FreeCADGui.Selection.clearSelection()
        nObj=0;old_pcb_tval=100;pcbN=''
        diff_objs=[]
        generate_sketch=False
        for o in doc.Objects:
            if hasattr(o, 'Shape') or o.TypeId == 'App::Link':
                if 'Sketch' not in o.Label and 'Pcb' not in o.Label:
                    for changed in diff_list:
                        if not changed[0].startswith('date'):
                            ref = changed.split(',')[0]
                            if o.Label.startswith(ref+'_'):
                                #FreeCADGui.Selection.addSelection(o)
                                gui_addSelection(o)
                                diff_objs.append(o)
                                #FreeCAD.Console.PrintWarning(o.Label+'\n') #;print('selected')
                                nObj+=1
                if 'Sketch' not in o.Label and 'Pcb' in o.Label:
                    old_pcb_tval = FreeCADGui.ActiveDocument.getObject(o.Name).Transparency
                    FreeCADGui.ActiveDocument.getObject(o.Name).Transparency = 70
                    pcbN=o.Name
                if 'PCB_Sketch' in o.Label and 'Sketch' in o.TypeId:
                    generate_sketch=True
        #print(''.join(diff_content)); stop
        if nObj > 0:
            dc = ''.join(diff_content)
            print(dc)
            for o in diff_objs:
                FreeCAD.Console.PrintWarning(o.Label+'\n')
            FreeCAD.Console.PrintError('N.'+str(nObj)+' Object(s) with changed placement \'Selected\'\n')
            #print ('Circle' in diff_content)
            if dc.find('Circle')!=-1 or dc.find('Line segment')!=-1: # or dc.find('ArcOfCircle')!=-1:
                FreeCAD.Console.PrintError('*** \'Pcb Sketch\' modified! ***\n')
        elif len(diff_content) > 3:
            FreeCAD.Console.PrintError('\'Pcb Sketch\' modified!\n')
            #for d in (diff_content):
            #    print (d)
            #print(''.join(diff_content))
            if len(pcbN)>0:
                FreeCADGui.ActiveDocument.getObject(pcbN).Transparency = old_pcb_tval
        else:
            FreeCAD.Console.PrintWarning('no changes\n')
            if len(pcbN)>0:
                FreeCADGui.ActiveDocument.getObject(pcbN).Transparency = old_pcb_tval
        generateSketch = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui").GetBool('generate_sketch')
        if generate_sketch and generateSketch:
            if len(sk_add)>0:
                #print(sk_add)
                if FreeCAD.activeDocument().getObject("Sketch_Addition") is not None:
                    FreeCAD.activeDocument().removeObject("Sketch_Addition")
                Sketch_Addition = FreeCAD.activeDocument().addObject('Sketcher::SketchObject','Sketch_Addition')
                FreeCADGui.activeDocument().getObject("Sketch_Addition").LineColor = (0.000,0.000,1.000)
                FreeCADGui.activeDocument().getObject("Sketch_Addition").PointColor = (0.000,0.000,1.000)
                Sketch_Addition.Geometry = sk_add
            if len(sk_sub)>0:
                #print(sk_sub)
                if FreeCAD.activeDocument().getObject("Sketch_Subtraction") is not None:
                    FreeCAD.activeDocument().removeObject("Sketch_Subtraction")
                Sketch_Subtraction = FreeCAD.activeDocument().addObject('Sketcher::SketchObject','Sketch_Subtraction')
                FreeCADGui.activeDocument().getObject("Sketch_Subtraction").LineColor = (0.667,0.000,0.498)
                FreeCADGui.activeDocument().getObject("Sketch_Subtraction").PointColor = (0.667,0.000,0.498)
                Sketch_Subtraction.Geometry = sk_sub
            if len(sk_add)>0 or len(sk_sub)>0:
                FreeCAD.ActiveDocument.recompute()

## https://stackoverflow.com/questions/3605680/creating-a-simple-xml-file-using-python


    
class RemoveSuffixDlg(QtGui.QDialog):
    
    def __init__(self, parent= None):
        super(RemoveSuffixDlg, self).__init__(parent, QtCore.Qt.WindowStaysOnTopHint)    
        #QtGui.QMainWindow.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)
        #icon = style.standardIcon(
        #    QtGui.QStyle.SP_MessageBoxCritical, None, widget)
        #self.setWindowIcon(self.style().standardIcon(QtGui.QStyle.SP_MessageBoxCritical))
        #self.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MessageBoxCritical))
        #self.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        #QtGui.QIcon(QtGui.QMessageBox.Critical))
        #icon = QtGui.QIcon()
        #icon.addPixmap(QtGui.QPixmap("icons/157-stats-bars.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #Widget.setWindowIcon(icon)
        ksuWBpath = os.path.dirname(ksu_locator.__file__)
        ksuWB_icons_path =  os.path.join( ksuWBpath, 'Resources', 'icons')
        
        self.pix =  QtGui.QLabel()
        self.pix.setText('')
        self.pix.setText('')
        self.pix.setPixmap(QtGui.QPixmap(ksuWB_icons_path+'/warning.svg'))
        self.pix.setObjectName("pix")
        self.txt =  QtGui.QLabel()
        self.txt.setText("This will remove ALL Suffix from selection objects.  \nDo you want to continue?")
        
        self.txt2 =  QtGui.QLabel()
        self.txt2.setText("\'suffix\'")
        self.le = QtGui.QLineEdit()
        self.le.setObjectName("suffix_filter")
        self.le.setText(".step")
        self.le.setToolTip("change the text to be\nstripped out from the end of Labels")
    
        #self.pb = QtGui.QPushButton()
        #self.pb.setObjectName("OK")
        #self.pb.setText("OK") 
        #
        #self.pbC = QtGui.QPushButton()
        #self.pbC.setObjectName("Cancel")
        #self.pbC.setText("Cancel") 
    
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
            
        layout2 = QtGui.QHBoxLayout()
        layout2.addWidget(self.pix)
        layout2.addWidget(self.txt)
        
        layout3 = QtGui.QHBoxLayout()
        #layout3.addWidget(self.pb)
        #layout3.addWidget(self.pbC)
        
        
        layout = QtGui.QVBoxLayout()
        layout.addLayout(layout2)
        layout.addWidget(self.txt2)
        layout.addWidget(self.le)
        layout.addLayout(layout3)
        layout.addWidget(self.buttonBox)
        
        #layout.addWidget(self.pb)
        #layout.addWidget(self.pbC)
    
        self.setWindowTitle("Warning ...")
        #self.setWindowIcon(self.style().standardIcon(QtGui.QStyle.SP_MessageBoxCritical))
        
        self.setLayout(layout)
        #self.setLayout(layout)
        #self.connect(self.pb, QtCore.SIGNAL("clicked()"),self.OK_click)
        #self.connect(self.pbC, QtCore.SIGNAL("clicked()"),self.Cancel_click)
        
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).clicked.connect(self.OK_click)
        self.buttonBox.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.Cancel_click)
        
    
    def OK_click(self):
        # shost is a QString object
        filtered = self.le.text()
        #print (self.le.text())
        #return (QtGui.QMessageBox.Ok)
        #self.close()*
        self.accept()
        
    def Cancel_click(self):
        # shost is a QString object
        #filtered = '.stp'
        self.le.setText('')
        # print (filtered)
        #return (QtGui.QMessageBox.Cancel)
        #self.close()*
        self.close()

