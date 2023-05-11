#!/usr/bin/python
# -*- coding: utf-8 -*-
#****************************************************************************

global fps_version
fps_version = '1.0.8'

dvp=False #True
if dvp:
    import fps; import importlib; importlib.reload(fps)

#import kicad_parser; import importlib; importlib.reload(kicad_parser)
import time
import PySide
from PySide import QtGui, QtCore
import sys,os
import FreeCAD, FreeCADGui
import Draft, Part

#import fcad_pcb
#from fcad_pcb import kicad

import fcad_parser
import kicad_parser
from kicad_parser import KicadPCB, make_fp_poly

import math
from math import radians

consolePrint = FreeCAD.Console.PrintMessage
consolePrint('fp loader v'+fps_version+'\n')

global start_time, last_pcb_path, min_drill_size, deltaz
#pcbThickness=1.6
deltaz = 0.01 #10 micron

def getFCversion():

    FC_majorV=int(float(FreeCAD.Version()[0]))
    FC_minorV=int(float(FreeCAD.Version()[1]))
    try:
        FC_git_Nbr=int (float(FreeCAD.Version()[2].strip(" (Git)").split(' ')[0])) #+int(FreeCAD.Version()[2].strip(" (Git)").split(' ')[1])
    except:
        FC_git_Nbr=0
    return FC_majorV,FC_minorV,FC_git_Nbr

FC_majorV,FC_minorV,FC_git_Nbr=getFCversion()
FreeCAD.Console.PrintWarning('FC Version '+str(FC_majorV)+str(FC_minorV)+"-"+str(FC_git_Nbr)+'\n')    

current_milli_time = lambda: int(round(time.time() * 1000))

def say_time():
    end_milli_time = current_milli_time()
    running_time=(end_milli_time-start_time)/1000
    msg="running time: "+str(running_time)+"sec"
    print(msg)
###
py2=False
try:  ## maui py3
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring
    py2=True

def reload_lib(lib):
    if (sys.version_info > (3, 0)):
        import importlib
        importlib.reload(lib)
    else:
        reload (lib)

def recompute_active_object():
    try:
        FreeCAD.ActiveDocument.ActiveObject.recompute(True)
    except:
        FreeCAD.ActiveDocument.ActiveObject.recompute()
##    

def crc_gen_t(data):
    import binascii
    import re
    
    #data=u'Würfel'
    content=re.sub(r'[^\x00-\x7F]+','_', data)
    #make_unicode(hex(binascii.crc_hqx(content.encode('utf-8'), 0x0000))[2:])
    #hex(binascii.crc_hqx(content.encode('utf-8'), 0x0000))[2:].encode('utf-8')
    #print(data +u'_'+ hex(binascii.crc_hqx(content.encode('utf-8'), 0x0000))[2:])
    return u'_'+ make_unicode_t(hex(binascii.crc_hqx(content.encode('utf-8'), 0x0000))[2:])
##

def make_unicode_t(input):
    if (sys.version_info > (3, 0)):  #py3
        if isinstance(input, str):
            return input
        else:
            input =  input.decode('utf-8')
            return input
    else: #py2
        if type(input) != unicode:
            input =  input.decode('utf-8')
            return input
        else:
            return input

def mkColor(*color):
    if len(color)==1:
        if isinstance(color[0],basestring):
            if color[0].startswith('#'):
                #color = color[0].replace('#','0x')
                #color = int(color,0)
                #print (color)
                #r = float((color>>24)&0xFF)
                #g = float((color>>16)&0xFF)
                #b = float((color>>8)&0xFF)
                color = color[0] #[1:]
                #print(color[1:3])
                r = int((color[1:3]), 16) #/255
                g = int((color[3:5]), 16) #/255
                b = int((color[5:7]), 16) #/255
                #print(r,g,b);stop
                #print(r,g,b)
                #stop
            else:
                color = int(color[0],0)
                r = float((color>>24)&0xFF)
                g = float((color>>16)&0xFF)
                b = float((color>>8)&0xFF)
        else:
            color = color[0]
            r = float((color>>24)&0xFF)
            g = float((color>>16)&0xFF)
            b = float((color>>8)&0xFF)
    else:
        r,g,b = color
    return (r/255.0,g/255.0,b/255.0)
##
#colors = {
#           'board':makeColor("0x3A6629"),
#           'pad':{0:makeColor(219,188,126)},
#           'zone':{0:makeColor(200,117,51)},
#           'track':{0:makeColor(200,117,51)},
#           'copper':{0:makeColor(200,117,51)},
#        }

def extrude_holes (holes,w):

    FreeCAD.ActiveDocument.addObject("Part::Extrusion","Extrude_drills")
    extrude_d_name=FreeCAD.ActiveDocument.ActiveObject.Name
    FreeCAD.ActiveDocument.getObject(extrude_d_name).Base = FreeCAD.ActiveDocument.getObject(holes.Name)
    FreeCAD.ActiveDocument.getObject(extrude_d_name).Dir = (0,0,w)
    FreeCAD.ActiveDocument.getObject(extrude_d_name).Solid = (True)
    FreeCAD.ActiveDocument.getObject(extrude_d_name).TaperAngle = (0)
    FreeCAD.ActiveDocument.getObject(extrude_d_name).Symmetric = True
    FreeCADGui.ActiveDocument.getObject(holes.Name).Visibility = False
    FreeCAD.ActiveDocument.getObject(extrude_d_name).Label = 'solid_drills'
    extrude_drill_name=FreeCAD.ActiveDocument.ActiveObject.Name
    recompute_active_object()
    FreeCADGui.ActiveDocument.getObject(holes.Name).Visibility = False
#

def cut_fuzzy(base,tool,ftol):

    Part.show(base.Shape.cut(tool.Shape, ftol))
    
#

def cut_out_tracks (pcbsk,tracks,tname_sfx):
    
    # import tracks; import importlib;importlib.reload(tracks)
    import random
    temp_tobedeleted = []
    removing_temp_objs = False
    Extrude_Name = 'Extrude' + str(random.randrange(1,100))
    FreeCAD.ActiveDocument.addObject('Part::Extrusion', Extrude_Name)
    extrude = FreeCAD.ActiveDocument.ActiveObject
    #f = FreeCAD.ActiveDocument.getObject('Extrude')
    print (pcbsk.Name)
    extrude.Base = pcbsk
    extrude.DirMode = "Custom"
    extrude.Dir = (0.000, 0.000, 1.000)
    extrude.DirLink = None
    extrude.LengthFwd = 5.0
    extrude.LengthRev = 0.0
    extrude.Solid = True
    extrude.Reversed = False
    extrude.Symmetric = True
    extrude.TaperAngle = 0.000000000000000
    extrude.TaperAngleRev = 0.000000000000000
    extrude.ViewObject.ShapeColor=getattr(pcbsk.getLinkedObject(True).ViewObject,'ShapeColor',extrude.ViewObject.ShapeColor)
    extrude.ViewObject.LineColor=getattr(pcbsk.getLinkedObject(True).ViewObject,'LineColor',extrude.ViewObject.LineColor)
    extrude.ViewObject.PointColor=getattr(pcbsk.getLinkedObject(True).ViewObject,'PointColor',extrude.ViewObject.PointColor)
    pcbsk.Visibility = False
    FreeCAD.ActiveDocument.recompute()
    Common_Top_Name = "Common_Top"+ str(random.randrange(1,100))
    FreeCAD.ActiveDocument.addObject("Part::MultiCommon",Common_Top_Name)
    Common_Top = FreeCAD.ActiveDocument.ActiveObject
    Common_Top.Shapes = [tracks,extrude,]
    FreeCADGui.ActiveDocument.getObject(tracks.Name).Visibility=False
    FreeCADGui.ActiveDocument.getObject(extrude.Name).Visibility=False
    FreeCAD.ActiveDocument.recompute()
    
    # placing inside the container
    if len (FreeCAD.ActiveDocument.getObjectsByLabel('Board_Geoms'+tname_sfx)) > 0:
        # extrude.adjustRelativeLinks(FreeCAD.ActiveDocument.getObject('Board_Geoms'+tname_sfx))
        FreeCAD.ActiveDocument.getObject('Board_Geoms'+tname_sfx).addObject(extrude)
    # simple copy
    FreeCAD.ActiveDocument.addObject('Part::Feature',tracks.Label+'_').Shape=FreeCAD.ActiveDocument.getObject(Common_Top.Name).Shape
    tracks_ct = FreeCAD.ActiveDocument.ActiveObject
    tracks_ctV = FreeCADGui.ActiveDocument.ActiveObject
    new_label=tracks.Label +'_cut'
    FreeCADGui.ActiveDocument.ActiveObject.ShapeColor=FreeCADGui.ActiveDocument.getObject(Common_Top.Name).ShapeColor
    FreeCADGui.ActiveDocument.ActiveObject.ShapeColor=FreeCADGui.ActiveDocument.getObject(Common_Top.Name).ShapeColor
    FreeCADGui.ActiveDocument.ActiveObject.LineColor=FreeCADGui.ActiveDocument.getObject(Common_Top.Name).LineColor
    FreeCADGui.ActiveDocument.ActiveObject.PointColor=FreeCADGui.ActiveDocument.getObject(Common_Top.Name).PointColor
    FreeCADGui.ActiveDocument.ActiveObject.DiffuseColor=FreeCADGui.ActiveDocument.getObject(Common_Top.Name).DiffuseColor
    FreeCADGui.ActiveDocument.ActiveObject.Transparency=FreeCADGui.ActiveDocument.getObject(Common_Top.Name).Transparency
    FreeCAD.ActiveDocument.ActiveObject.Label=new_label
    tracks_ct_Name = FreeCAD.ActiveDocument.ActiveObject.Name
    if removing_temp_objs:
        FreeCAD.ActiveDocument.removeObject(Common_Top.Name)
        FreeCAD.ActiveDocument.removeObject(tracks.Name)
        FreeCAD.ActiveDocument.removeObject(extrude.Name)
    else:
        doc = FreeCAD.ActiveDocument
        #temp_tobedeleted.append([doc.getObject(Common_Top.Name),doc.getObject(tracks.Name),doc.getObject(extrude.Name)])
        temp_tobedeleted.append(doc.getObject(Common_Top.Name))
        temp_tobedeleted.append(doc.getObject(tracks.Name))
        temp_tobedeleted.append(doc.getObject(extrude.Name))
    FreeCAD.ActiveDocument.getObject(tracks_ct_Name).Label = new_label
    FreeCAD.ActiveDocument.recompute()
    
    return tracks_ct_Name, temp_tobedeleted
##
def simple_cpy (obj,lbl):
    copy = FreeCAD.ActiveDocument.addObject('Part::Feature',obj.Name)
    copy.Label = lbl
    copy.Shape = obj.Shape
    copy.ViewObject.ShapeColor   = obj.ViewObject.ShapeColor
    copy.ViewObject.LineColor    = obj.ViewObject.LineColor
    copy.ViewObject.PointColor   = obj.ViewObject.PointColor
    copy.ViewObject.DiffuseColor = obj.ViewObject.DiffuseColor
    return copy
#
#def rmv_obj(o):
#    FreeCADGui.Selection.clearSelection()
#    FreeCADGui.Selection.addSelection(doc.getObject(pads.Name))
#    removesubtree(FreeCADGui.Selection.getSelection())
#

from kicadStepUptools import removesubtree, cfg_read_all
from kicadStepUptools import make_unicode, make_string
import fcad_parser
from fcad_parser import KicadPCB,SexpList

start_f="""(kicad_pcb (version 20211014) (generator pcbnew)

  (general
    (thickness 1.6)
  )

  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
    (50 "User.1" user)
    (51 "User.2" user)
    (52 "User.3" user)
    (53 "User.4" user)
    (54 "User.5" user)
    (55 "User.6" user)
    (56 "User.7" user)
    (57 "User.8" user)
    (58 "User.9" user)
  )

"""
end_f="""
)"""

#filename="C:/Cad/Progetti_K/ksu-test/pic_smart_switch.kicad_pcb"
#filename="C:/Cad/Progetti_K/eth-32gpio/eth-32gpio.kicad_pcb"
def addfootprint(fname = None):
    global start_time, last_pcb_path, min_drill_size
    global tracks_version
    global start_f, end_f, deltaz
    import sys
    import kicad_parser
    FreeCAD.Console.PrintMessage('kicad_parser_version '+kicad_parser.__kicad_parser_version__+'\n') # maui 

    # cfg_read_all() it doesn't work through different files
    # print (min_drill_size)
    
    FreeCAD.Console.PrintMessage('footprints version: '+fps_version+'\n')
    Filter=""
    pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
    if fname is None:
        last_pcb_path = pg.GetString("last_pcb_path")
        if len (last_pcb_path) == 0:
                last_pcb_path = ""
        fname, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open File...",
                make_unicode(last_pcb_path), "*.kicad_mod")
        path, name = os.path.split(fname)
    #filename=os.path.splitext(name)[0]
    filename = fname
    #importDXF.open(os.path.join(dirname,filename))
    if len(fname) > 0:
        start_time=current_milli_time()
        last_pcb_path=os.path.dirname(fname)
        path, ftname = os.path.split(fname)
        ftname=os.path.splitext(ftname)[0]
        ftname_sfx=crc_gen_t(make_unicode_t(ftname))
        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
        pg.SetString("last_pcb_path", make_string(last_pcb_path)) # py3 .decode("utf-8")
        prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
        pcb_color_pos = prefs.GetInt('pcb_color')
        #pcb_color_values = [light_green,blue,red,purple,darkgreen,darkblue,lightblue,yellow,black,white]
        assign_col=['#41c382','#2474cf','#ff4000','#9a1a85','#3c7f5d','#426091','#005fff','#fff956','#4d4d4d','#f0f0f0']
        #print(pcb_color_pos)
        pcb_transparency = 80
        pcb_col = (assign_col[pcb_color_pos])
        if pcb_color_pos == 9:
            slk_col = '#2d2d2d'
        else:
            slk_col = '#f8f8f0'
        pads_color = (0.81,0.71,0.23) #(0.85,0.53,0.10)
        pads_transparency = 60
        nettie_color = (1.0,0.33,0.0)
        nettie_transparency = 50
        tbassembled=[]
        # import kicad_parser 
        # pcb = kicad_parser.KicadFcad(filename)
        del_file = False
        
        consolePrint(filename+'\n')
        fn=os.path.splitext(os.path.basename(filename))[0]
        
        if filename.endswith('kicad_mod'):
            with open(filename , 'r') as f:
                lines = f.readlines() # readlines creates a list of the lines
            #lines = start_f+lines+end_f
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False,suffix='.kicad_pcb')
            with tmp as f:
            #with open(tmp.name, 'w') as f:
                for l in start_f:
                    f.write(l.encode(encoding='UTF-8'))
                for l in lines:
                    f.write(l.encode(encoding='UTF-8'))
                for l in end_f:
                    f.write(l.encode(encoding='UTF-8'))
            filename = tmp.name
            del_file = True
            #print(filename)
        
        _pcb = KicadPCB.load(filename)
        pcb = kicad_parser.KicadFcad(filename,via_skip_hole=False,via_bound=0)
        if del_file:
            os.remove(filename)
            consolePrint('file removed\n')
        doc=FreeCAD.ActiveDocument
        if doc is None:
            doc=FreeCAD.newDocument()
            doc.Label = fn
            ini_objs=doc.Objects
        doc.openTransaction('addFp')

        pcbThickness = float(_pcb.general.thickness)
        fp_name = fn
        ar=0
        for i,m in enumerate(_pcb.module):
            if hasattr(m, 'model'):
                try:
                    ar=m.model[0].rotate.xyz[2]
                except:
                    pass
            # print(m.fp_text[1][0],m.fp_text[1][1])
            if hasattr(m, 'fp_text'):
                for t in m.fp_text:
                    #print(t[0],' ',t[1])
                    if t[0] == 'value':
                        fp_name = t[1]
            if hasattr(m, 'zone'):
                # print(m.zone)
                zones=[]
                #print(m.zone, len(m.zone))
                #print(SexpList(m.zone))
                #zl=SexpList(m.zone)
                #z0=zl[0]
                #Part.show(make_fp_poly(z0.polygon))
                ## print(zl.layer)
                #zl = m.zone
                #z0=zl[0]
                #print(z0.polygon)
                #Part.show(make_fp_poly(z0.polygon))
                #zl=SexpList(m.zone)
                #print(zl)
                # print(m.zone)
                #if hasattr(m.zone, 'polygon'):
                for z in (m.zone):
                    # print(z) #,SexpList(z))
                    # print(z.layer)
                    # print(z.keepout)
                    # print(z.polygon.pts)
                    if hasattr(z,'keepout'):
                        pg=make_fp_poly(z.polygon)
                        zones.append(pg)
                if len(zones) > 0:
                    consolePrint('making keepout zones\n')
                    Part.show(Part.makeCompound(zones))
                    zn = doc.ActiveObject
                    zn.Label = 'keepout-Zones'
                    zn.ViewObject.DrawStyle = u"Dashed"
                    zn.ViewObject.LineColor = (255,0,127)
                    import Draft
                    if ar!=0:
                        zn.Placement.Rotation.Angle = radians(ar)
                    zone_keepout = Draft.makeSketch(zn,autoconstraints=True)
                    zone_keepout.Label = 'keepout-Zones_'
                    zone_keepout.ViewObject.DrawStyle = u"Dashed"
                    zone_keepout.ViewObject.LineColor = (255,0,127)
                    doc.removeObject(zn.Name)
                    tbassembled.append(zone_keepout)
                #stop
        #from kicad_parser import KicadFcad
        #from kicad_parser import makePads
        # import kicad_pads_parser
        # for m in _pcb.module:
        #     for p in m.pad:
        #         print (p)
        #         # kicad_pads_parser.makePads(p,shape_type='solid',thickness=0.01,holes=True,fit_arcs=True)
        #         # KicadFcad.makePads(shape_type='solid',thickness=0.01,holes=True,fit_arcs=True)
        
        #print(ar)
        # pcb = kicad.KicadFcad(filename,via_skip_hole=False,via_bound=0)
        
        consolePrint('making holes\n')
        Holes_Compound = None
        holesT=pcb.makeHoles(shape_type='solid',oval=True)
        if hasattr (holesT,'Name'):
            holesT.ViewObject.Transparency = 70
            holesT.Placement.Base.z-=pcbThickness-deltaz
            hole_ws = holesT.OutList[0].OutList[0].Shape
            wires=hole_ws.Wires
            anr=[]
            tbd=[]
            i=0
            for w in wires:
                Part.show(w)
                ia = doc.ActiveObject
                doc.addObject("Part::Offset2D","Offset2D")
                o2d=doc.ActiveObject
                o2d.Source = ia #doc.getObject(ia.Name)
                o2d.Value = 0.01
                doc.recompute()
                tbd.append(o2d)
                dw=[o2d.Shape.Wires,ia.Shape.Wires]
                # s = Part.makeCompound([o2d.Shape,ia.Shape]).extrude(FreeCAD.Vector(0.0, 0.0, -pcbThickness))
                s = Part.makeCompound([o2d.Shape,ia.Shape])
                Part.show(s)
                s = doc.ActiveObject
                doc.addObject('Part::Extrusion', 'drl_ann')
                extrude = doc.ActiveObject
                #f = FreeCAD.ActiveDocument.getObject('Extrude')
                extrude.Base = s
                extrude.DirMode = "Custom"
                extrude.Dir = (0.000, 0.000, 1.000)
                extrude.DirLink = None
                extrude.LengthFwd = pcbThickness
                extrude.LengthRev = 0.0
                extrude.Solid = True
                extrude.Reversed = True
                extrude.Symmetric = False
                doc.recompute()
                tbd.append(extrude)
                doc.addObject('Part::Feature','anr_').Shape=extrude.Shape
                nanr=doc.ActiveObject
                nanr.Label='drill_'+'{0:0{1}}'.format(i, 3)
                anr.append(nanr)
            for o in tbd:
                removesubtree([o])
            doc.addObject("Part::Compound","annulars")
            Holes_Compound=doc.ActiveObject
            Holes_Compound.Links = anr
            Holes_Compound.ViewObject.Transparency=70
            doc.recompute()
            Holes_Compound.ViewObject.ShapeColor = (0.33,1.00,0.00)
            Holes_Compound.Label='TH-Drills'
            # tbassembled.append(Holes_Compound)
            holesT.ViewObject.Visibility = False
            #stop

        #stop

        consolePrint('making Top Pads\n')
        pcb.setLayer(0) #'F.Cu')
        topP=pcb.makePads(shape_type='wire',thickness=deltaz,holes=False,fit_arcs=True)  #solid',thickness=deltaz,holes=True,fit_arcs=True)
        topPf=None
        topPe=None
        #print(topP.Label)
        # print(FreeCAD.ActiveDocument.ActiveObject.Label)
        if hasattr(topP, 'OutList'):
            topPWs = topP.OutList[0]
            s_p = None
            for w in topPWs.Shape.Wires:
                #Part.show(w)
                # Part.show(Part.Face(w))
                s = Part.Face(w)
                if s_p is not None:
                    s = s.fuse(s_p)
                s_p=s
            #Part.show(s.extrude(FreeCAD.Vector(0.0, 0.0, deltaz)))
            Part.show(s)
            topPf = doc.ActiveObject
            topPf.Label = 'topPadFace'
            removesubtree([topP])
            s = topPf.Shape
            if hasattr (holesT,'Name'): # cutting holes
                s = s.cut(holesT.Shape)
                #Part.show(s)
            Part.show(s.extrude(FreeCAD.Vector(0.0, 0.0, deltaz)))
            topPe = doc.ActiveObject
            removesubtree([topPf])
            if hasattr (topPe,'Name'):
                topPe.Label = 'topPads'
                #btmP.ViewObject.Transparency = 50
                topPe.Placement.Base.z-=deltaz
                topPe.ViewObject.Transparency=pads_transparency
                topPe.ViewObject.ShapeColor = pads_color
                if ar!=0:
                    topPe.Placement.Rotation.Angle = radians(ar)
                if topPe.Shape.Area != 0:
                    tbassembled.append(topPe)
                else:
                    removesubtree([topPe])
            #stop
        
        
        #stop
        consolePrint('making Bot Pads\n')
        pcb.setLayer(31) #'B.Cu')
        btmP=pcb.makePads(shape_type='wire',thickness=0.01,holes=False,fit_arcs=True)
        btmPf = None
        btmPe=None
        if hasattr(btmP, 'OutList'):
            btmPWs = btmP.OutList[0]
            s_p = None
            for w in btmPWs.Shape.Wires:
                #Part.show(w)
                #Part.show(Part.Face(w))
                s = Part.Face(w)
                if s_p is not None:
                    s = s.fuse(s_p)
                s_p=s
            #Part.show(s.extrude(FreeCAD.Vector(0.0, 0.0, -deltaz)))
            Part.show(s)
            btmPf = doc.ActiveObject
            s = btmPf.Shape
            if hasattr (holesT,'Name'): # cutting holes
                s = s.cut(holesT.Shape)
                #Part.show(s)
            Part.show(s.extrude(FreeCAD.Vector(0.0, 0.0, deltaz)))
            btmPe = doc.ActiveObject
            if hasattr (btmPe,'Name'):
                btmPe.Label = 'btmPads'    
                removesubtree([btmP])
                removesubtree([btmPf])
                # tbassembled.append(btmPe)
                #stop
                #btmP.ViewObject.Transparency = 50
                btmPe.Placement.Base.z-=pcbThickness # -deltaz
                btmPe.ViewObject.Transparency=pads_transparency
                btmPe.ViewObject.ShapeColor = pads_color
                if ar!=0:
                    btmPe.Placement.Rotation.Angle = radians(ar)
            if btmPe.Shape.Area != 0:
                tbassembled.append(btmPe)
            else:
                removesubtree([btmPe])
        doc.Tip = doc.addObject('App::DocumentObjectGroup','Group')
        fp_group=doc.ActiveObject
        fp_group.Label = fp_name+'-fp'
        
        for o in tbassembled:
            # doc.getObject(o.Name).adjustRelativeLinks(doc.getObject(fp_group.Name))
            doc.getObject(fp_group.Name).addObject(doc.getObject(o.Name))
        #stop
        
        consolePrint('making Top Net Ties\n')
        #net ties
        pcb.setLayer(0) #'F.Cu')
        ntt=pcb.makeNetTies(shape_type='wire',thickness=0.01,fit_arcs=True)
        if hasattr (ntt,'Name'):
            s_p = None
            for w in ntt.Shape.Wires:
                s = Part.Face(w)
                if s_p is not None:
                    s = s.fuse(s_p)
                s_p=s
            Part.show(s)
            nttF = doc.ActiveObject
            removesubtree([ntt])
            s = nttF.Shape
            if hasattr (holesT,'Name'): # cutting holes
                s = s.cut(holesT.Shape)
                #Part.show(s)
            nttE = Part.show(s.extrude(FreeCAD.Vector(0.0, 0.0, deltaz)))
            removesubtree([nttF])
            nttE.Label = 'topNetTie'
            nttE.ViewObject.Transparency = nettie_transparency
            nttE.ViewObject.ShapeColor = nettie_color
            # nttE.Placement.Base.z+=deltaz
            # doc.getObject(nttE.Name).adjustRelativeLinks(doc.getObject(fp_group.Name))
            doc.getObject(fp_group.Name).addObject(nttE)

        consolePrint('making Bot Net Ties\n')
        pcb.setLayer(31) #'B.Cu')
        ntb=pcb.makeNetTies(shape_type='wire',thickness=0.01,fit_arcs=True)
        if hasattr (ntb,'Name'):
            s_p = None
            for w in ntb.Shape.Wires:
                s = Part.Face(w)
                if s_p is not None:
                    s = s.fuse(s_p)
                s_p=s
            Part.show(s)
            ntbF = doc.ActiveObject
            removesubtree([ntb])
            s = ntbF.Shape
            if hasattr (holesT,'Name'): # cutting holes
                s = s.cut(holesT.Shape)
                #Part.show(s)
            ntbE = Part.show(s.extrude(FreeCAD.Vector(0.0, 0.0, +deltaz)))
            removesubtree([ntbF])
            ntbE.Label = 'btmNetTie'
            ntbE.ViewObject.Transparency = nettie_transparency
            ntbE.ViewObject.ShapeColor = nettie_color
            ntbE.Placement.Base.z-=(pcbThickness+deltaz)
            # doc.getObject(ntbE.Name).adjustRelativeLinks(doc.getObject(fp_group.Name))
            doc.getObject(fp_group.Name).addObject(ntbE)

        if Holes_Compound is not None:
            # Holes_Compound.adjustRelativeLinks(doc.getObject(fp_group.Name))
            doc.getObject(fp_group.Name).addObject(Holes_Compound)
        
        
        consolePrint('making Drawings sketches\n')
        tbds=[];tbp=[];tltbp=[]
        # top layers
        pcb.setLayer(37) #'F.Silks')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        #print(doc, tbd, tbd[0].OutList[0].Name, tbd[0].Name)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        pcb.setLayer(47) #'F.CrtYd')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        pcb.setLayer(49) #'F.Fab')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        pcb.setLayer(44) #'Edge.Cuts')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        pcb.setLayer(45) #'Margins')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        pcb.setLayer(33) #'F.Adhes')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))

        # User layers
        pcb.setLayer(40) #'Dwgs.User')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        # User layers
        pcb.setLayer(41) #'Cmts.User')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        for l in tbds:
            for o in l:
                doc.removeObject(o.OutList[0].Name)
                doc.removeObject(o.Name)
        for t in tbp:
            sk=t[0]
            tl=t[1]
            if hasattr (sk,'Name'):
                sk.Placement.Base.z+=deltaz
                if ar!=0:
                    sk.Placement.Rotation.Angle = radians(ar)
                # sk.adjustRelativeLinks(doc.getObject(fp_group.Name))
                doc.getObject(fp_group.Name).addObject(sk)
            if hasattr (tl,'Name'):
                tl.Placement.Base.z+=deltaz
                if ar!=0:
                    tl.Placement.Rotation.Angle = radians(ar)
                # tl.adjustRelativeLinks(doc.getObject(fp_group.Name))
                doc.getObject(fp_group.Name).addObject(tl)
        
        tbds=[];tbp=[]
        # btm layers
        pcb.setLayer(36) #'B.Silks')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        pcb.setLayer(46) #'B.CrtYd')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))
        
        pcb.setLayer(48) #'B.Fab')
        sk,tls,tbd=pcb.makeSketches(fit_arcs=True)
        tbds.append(tbd)
        tbp.append((sk,tls))

        for l in tbds:
            for o in l:
                doc.removeObject(o.OutList[0].Name)
                doc.removeObject(o.Name)
        for t in tbp:
            sk=t[0]
            tl=t[1]
            if hasattr (sk,'Name'):
                sk.Placement.Base.z-=pcbThickness-deltaz
                if ar!=0:
                    sk.Placement.Rotation.Angle = radians(ar)
                # sk.adjustRelativeLinks(doc.getObject(fp_group.Name))
                doc.getObject(fp_group.Name).addObject(sk)
            if hasattr (tl,'Name'):
                tl.Placement.Base.z-=pcbThickness-deltaz
                if ar!=0:
                    tl.Placement.Rotation.Angle = radians(ar)
                # tl.adjustRelativeLinks(doc.getObject(fp_group.Name))
                doc.getObject(fp_group.Name).addObject(tl)

        if fp_group is not None:
            doc.addObject("Part::Compound","TCompound")
            TComp = doc.ActiveObject
            TComp.Links = fp_group.OutList
            doc.recompute()
            bbComp = TComp.Shape.BoundBox
            removesubtree([TComp])
            delta = 0.5
            centerX = bbComp.Center.x
            centerY = bbComp.Center.y
            pcb_XL = bbComp.XLength*(1+delta)
            pcb_YL = bbComp.YLength*(1+delta)
            pcb_ZL = pcbThickness-2*deltaz
            pcb=FreeCAD.ActiveDocument.addObject('Part::Feature','PCB')
            for o in fp_group.OutList:
                o.ViewObject.Visibility = True
            try:
                if hasattr (holesT,'Name'):
                    pcb.Shape=Part.makeBox(pcb_XL, pcb_YL, pcb_ZL, FreeCAD.Vector(centerX-pcb_XL/2,centerY-pcb_YL/2,-(pcb_ZL+deltaz)), FreeCAD.Vector(0,0,1)).cut(holesT.Shape)
                    removesubtree([holesT])
                else:
                    pcb.Shape=Part.makeBox(pcb_XL, pcb_YL, pcb_ZL, FreeCAD.Vector(centerX-pcb_XL/2,centerY-pcb_YL/2,-(pcb_ZL+deltaz)), FreeCAD.Vector(0,0,1))
                pcb.ViewObject.Transparency = pcb_transparency
                pcb.ViewObject.ShapeColor = mkColor(pcb_col)
                # pcb.adjustRelativeLinks(doc.getObject(fp_group.Name))
                doc.getObject(fp_group.Name).addObject(pcb)
                doc.recompute()
            except:
                doc.removeObject(pcb.Name)
                consolePrint('no shapes generated\n')
        doc.commitTransaction()
        
        if FreeCAD.ActiveDocument is not None:
            FreeCADGui.SendMsgToActiveView("ViewFit")
            #FreeCADGui.ActiveDocument.activeView().viewAxonometric()

###
