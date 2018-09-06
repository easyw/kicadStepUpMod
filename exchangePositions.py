# -*- coding: utf-8 -*-
#

## https://www.freecadweb.org/wiki/Placement
# App.ActiveDocument.Cylinder.Placement=App.Placement(App.Vector(0,0,0), App.Rotation(10,20,30), App.Vector(0,0,0)) 
# App.Rotation(10,20,30) = Euler Angle 
## https://forum.freecadweb.org/viewtopic.php?t=11799


import FreeCAD, FreeCADGui,sys, os 
import PySide 
from PySide import QtGui
#from PySide.QtGui import QTreeWidgetItemIterator

from os.path import expanduser
import difflib, re, time, datetime

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
  
def expPos(doc=None):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    rmvSuffix(doc)
    full_content=[]
    positions_content=[]
    sketch_content=[]
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
        if hasattr(o, 'Shape') or o.TypeId == 'App::Link':
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
                sketch_content.append(line+'\n')
                print('Sketch geometry -------------------')
                if hasattr(o,'Geometry'):
                    for e in o.Geometry:
                        line=str(e)
                        sketch_content.append(line+'\n')
                        print (e) 
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
def cmpPos(doc=None):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    rmvSuffix(doc)
    full_content=[]
    positions_content=[]
    sketch_content=[]
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
        if hasattr(o, 'Shape') or o.TypeId == 'App::Link':
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
            sketch_content.append(line+'\n')
            #print('Sketch geometry -------------------')
            if hasattr(o,'Geometry'):
                for e in o.Geometry:
                    line=str(e)
                    sketch_content.append(line+'\n')
                    #print (e) 
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
            elif line.startswith("+"):
                if not line.startswith("+++") and not line.startswith("+title") \
                        and not line.startswith("+FileN") and not line.startswith("+date "):
                    #print(i,'\t\t'+line)
                    #print('Ln '+str(i)+(8-(len(str(i))))*' '),(line),
                    diff_content.append('Ln '+str(i)+(8-len(str(i)))*' '+line)
                    diff_list.append(line[1:])
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
        #print(''.join(diff_content)); stop
        if nObj > 0:
            print(''.join(diff_content))
            for o in diff_objs:
                FreeCAD.Console.PrintWarning(o.Label+'\n')
            FreeCAD.Console.PrintError('N.'+str(nObj)+' Object(s) with changed placement \'Selected\'\n')
        elif len(diff_content) > 3:
            FreeCAD.Console.PrintError('\'Pcb Sketch\' modified!\n')
            #for d in (diff_content):
            #    print (d)
            print(''.join(diff_content))
            if len(pcbN)>0:
                FreeCADGui.ActiveDocument.getObject(pcbN).Transparency = old_pcb_tval
        else:
            FreeCAD.Console.PrintWarning('no changes\n')
            if len(pcbN)>0:
                FreeCADGui.ActiveDocument.getObject(pcbN).Transparency = old_pcb_tval
## https://stackoverflow.com/questions/3605680/creating-a-simple-xml-file-using-python



