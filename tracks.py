#!/usr/bin/python
# -*- coding: utf-8 -*-
#****************************************************************************

global tracks_version
tracks_version = '2.4.6'

import kicad_parser
#import kicad_parser; import importlib; importlib.reload(kicad_parser)
import time
import PySide
from PySide import QtGui, QtCore
import sys,os
import FreeCAD, FreeCADGui
global start_time, last_pcb_path, min_drill_size
global FC_export_min_version
FC_export_min_version="11670"  #11670 latest JM


global use_AppPart, use_Links, use_LinkGroups
use_AppPart=False # False
use_Links=False

use_LinkGroups = False
if 'LinkView' in dir(FreeCADGui):
    prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
    if prefs.GetBool('asm3_linkGroups'):
        use_LinkGroups = True
        use_Links=True #False
        #print('using \'LinkGroups\' and \'Links\'')
    elif prefs.GetBool('asm3_links'):
        use_Links=True #False
        #print('using \'Part\' container and \'Links\'')
    else:
        use_LinkGroups = False
        #print('using \'Part\' container')
else:
    use_LinkGroups = False
    #print('using \'Part\' container')
#
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
if FC_majorV == 0 and FC_minorV == 17:
    if FC_git_Nbr >= int(FC_export_min_version):
        use_AppPart=True
#if FreeCAD.Version()[2] == 'Unknown':  #workaround for local building
#    use_AppPart=True
if FC_majorV > 0:
    use_AppPart=True
if FC_majorV == 0 and FC_minorV > 17:
    #if FC_git_Nbr >= int(FC_export_min_version):
    use_AppPart=True

current_milli_time = lambda: int(round(time.time() * 1000))

def say_time():
    end_milli_time = current_milli_time()
    running_time=(end_milli_time-start_time)/1000
    msg="running time: "+str(running_time)+"sec"
    print(msg)
###
#try:  #maui
#  basestring
#except NameError:
#  basestring = str
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
        extrude.adjustRelativeLinks(FreeCAD.ActiveDocument.getObject('Board_Geoms'+tname_sfx))
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

#filename="C:/Cad/Progetti_K/ksu-test/pic_smart_switch.kicad_pcb"
#filename="C:/Cad/Progetti_K/eth-32gpio/eth-32gpio.kicad_pcb"
def addtracks(fname = None):
    global start_time, last_pcb_path, min_drill_size
    global use_LinkGroups, use_AppPart, tracks_version
    import sys
    
    # cfg_read_all() it doesn't work through different files
    # print (min_drill_size)
    
    FreeCAD.Console.PrintMessage('tracks version: '+tracks_version+'\n')
    Filter=""
    pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
    if fname is None:
        last_pcb_path = pg.GetString("last_pcb_path")
        if len (last_pcb_path) == 0:
                last_pcb_path = ""
        fname, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open File...",
                make_unicode(last_pcb_path), "*.kicad_pcb")
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
        trk_col = (assign_col[pcb_color_pos])
        if pcb_color_pos == 9:
            slk_col = '#2d2d2d'
        else:
            slk_col = '#f8f8f0'
        # mypcb = KicadPCB.load(filename)
        # pcbThickness = float(mypcb.general.thickness)
        #print (mypcb.general.thickness)
        #print(mypcb.layers)
        
        #if version>=4:
        Top_lvl=0;Bot_lvl=31
        #for lynbr in mypcb.layers: #getting layers name
        #    if float(lynbr) == Top_lvl:
        #        LvlTopName=(mypcb.layers['{0}'.format(str(lynbr))][0])
        #    if float(lynbr) == Bot_lvl:
        #        LvlBotName=(mypcb.layers['{0}'.format(str(lynbr))][0])
        #print(LvlTopName,'  ',LvlBotName)
        import kicad_parser 
        # reload_lib(kicad_parser)
        pcb = kicad_parser.KicadFcad(filename)
        # pcbThickness = pcb.board_thickness ## this doesn't always give the full board thickness
        # print(pcbThickness,'pcbThickness')
        
        mypcb = KicadPCB.load(filename)
        pcbThickness = float(mypcb.general.thickness)
        # print(pcbThickness,'mypcb.pcbThickness')
        #pcbThickness = float(pcb.general.thickness)
        #pcb.setLayer(LvlTopName)
        minSizeDrill = 0.0  #0.8
        #print(pcb.colors)
        # https://www.seeedstudio.com/blog/2017/07/23/why-are-printed-circuit-boards-are-usually-green-in-colour/
        # <span style="color: #105e7d;">deep-sea blue</span></strong>, <strong><span style="color: #ff2f00;">Ferrari red</span></strong>, <strong><span style="color: #ffcc00;">sunshine yellow</span></strong>, <strong>slick black</strong>, <span style="color: #999999;"><strong>pure white</strong></span> and of course <strong><span style="color: #339966;">good</span></strong> <strong><span style="color: #339966;">ol’ green</span>
        # (r/255.0,g/255.0,b/255.0)
        pcb_col = pcb.colors
        #zone_col = pcb_col['zone'][0]
        #track_col = pcb_col['track'][0]
        pcb_col['track'][0] = mkColor(trk_col)
        pcb_col['zone'][0] = mkColor(trk_col)
        # print(pcb_col['track'][0])
        # print(pcb_col['pad'][0])
        # print(pcb_col)
        #pcb_col['track'][0] = mkColor('#147b9d')
        #pcb_col['zone'][0] = mkColor('#147b9d')
        #pcb.colors = {
        #   'board':mkColor("0x3A6629"),
        #   'pad':{0:mkColor(219,188,126)},
        #   'zone':{0:mkColor('#147b9d')},
        #   'track':{0:mkColor(26,157,204)},
        #   'copper':{0:mkColor(200,117,51)},
        #}
        #pcb.colors={'board':(1.,1.,1.),'pad':{0:(219/255,188/255,126/255)},'zone':{0:(0.,1.,0.)},'track':{0:(0.,1.,1.)},'copper':{0:(0.,1.,1.)},}  
        pcb.setLayer(Top_lvl)
        #try:   #doing top tracks layer
        ## pcb.makeCopper(holes=True, minSize=minSizeDrill)
        # pcb.make(copper_thickness=0.035, board_thickness=pcbThickness, combo=False, fuseCoppers=True ) 
        # pcb.makeCopper(holes=True,fuse=False)
        # say_time()
        # stop
        topPads = None
        topTracks = None
        topZones = None
        deltaz = 0.01 #10 micron
        add_toberemoved = []
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        else:
            objsNum = 0
        pcb.makePads(shape_type='face',thickness=0.05,holes=True,fit_arcs=True) #,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                pads=FreeCAD.ActiveDocument.ActiveObject
                pads.Placement.Base.z = pads.Placement.Base.z + 2*deltaz
                new_obj = simple_cpy(pads,'topPads'+ftname_sfx)
                say_time()
                # removesubtree([pads])
                add_toberemoved.append([pads])
                topPads = new_obj
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        pcb.makeTracks(shape_type='face',fit_arcs=True,thickness=0.05,holes=True) #,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                say_time()
                tracks=FreeCAD.ActiveDocument.ActiveObject
                tracks.Placement.Base.z+=deltaz
                new_obj = simple_cpy(tracks,'topTracks'+ftname_sfx)
                say_time()
                # removesubtree([tracks])
                add_toberemoved.append([tracks])
                topTracks = new_obj
                #stop
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        pcb.makeZones(shape_type='face',thickness=0.05, fit_arcs=True,holes=True) #,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                say_time()
                zones=FreeCAD.ActiveDocument.ActiveObject
                zones.Placement.Base.z+=deltaz
                new_obj = simple_cpy(zones,'topZones'+ftname_sfx)
                say_time()
                # removesubtree([zones])
                add_toberemoved.append([zones])
                topZones = new_obj
            if len (FreeCAD.ActiveDocument.getObjectsByLabel('Pcb'+ftname_sfx)) >0:
                #PCB_Sketch_5737
                pcb_sk = FreeCAD.ActiveDocument.getObject('PCB_Sketch'+ftname_sfx)
                ### check if BBOx pcb > BBOx tracks
                if topPads is not None:
                    topPads.Placement = FreeCAD.ActiveDocument.getObject('Pcb'+ftname_sfx).Placement
                    #if (topPads.Shape.BoundBox.XLength > pcb_sk.Shape.BoundBox.XLength) or \
                    #        (topPads.Shape.BoundBox.YLength > pcb_sk.Shape.BoundBox.YLength):
                    if (topPads.Shape.BoundBox.XMax > pcb_sk.Shape.BoundBox.XMax) or \
                            (topPads.Shape.BoundBox.XMin < pcb_sk.Shape.BoundBox.XMin) or \
                            (topPads.Shape.BoundBox.YMax > pcb_sk.Shape.BoundBox.YMax) or \
                            (topPads.Shape.BoundBox.YMin < pcb_sk.Shape.BoundBox.YMin):
                        topPads_cut_Name, temp_tobedeleted = cut_out_tracks(pcb_sk,topPads,ftname_sfx)
                        topPads = FreeCAD.ActiveDocument.getObject(topPads_cut_Name)
                        add_toberemoved.append(temp_tobedeleted)
                    topPads.Placement.Base.z+=2*deltaz
                if topTracks is not None:
                    topTracks.Placement = FreeCAD.ActiveDocument.getObject('Pcb'+ftname_sfx).Placement
                    topTracks.Placement.Base.z+=deltaz
                if topZones is not None:
                    topZones.Placement = FreeCAD.ActiveDocument.getObject('Pcb'+ftname_sfx).Placement
                    topZones.Placement.Base.z+=deltaz
                if len (FreeCAD.ActiveDocument.getObjectsByLabel('Board_Geoms'+ftname_sfx)) > 0:
                    if use_AppPart and not use_LinkGroups:
                        if topPads is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).addObject(topPads)
                        if topTracks is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).addObject(topTracks)
                        if topZones is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).addObject(topZones)
                    elif use_LinkGroups:
                        if topPads is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(topPads,None,'',[])
                        if topTracks is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(topTracks,None,'',[])
                        if topZones is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(topZones,None,'',[])
        #try:    #doing bot tracks layer
        #pcb.setLayer(LvlBotName)
        pcb.setLayer(Bot_lvl)
        # pcb.makeCopper(holes=True, minSize=minSizeDrill)
        #pcb.makeCopper(holes=True)
        botPads = None
        botTracks = None
        botZones = None
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        else:
            objsNum = 0
        pcb.makePads(shape_type='face',thickness=0.05,holes=True,fit_arcs=True,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                doc=FreeCAD.ActiveDocument
                pads=FreeCAD.ActiveDocument.ActiveObject
                pads.Placement.Base.z = pads.Placement.Base.z - (pcbThickness + 2*deltaz)
                new_obj = simple_cpy(pads,'botPads'+ftname_sfx)
                say_time()
                # removesubtree([pads])
                add_toberemoved.append([pads])
                botPads = new_obj
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        pcb.makeTracks(shape_type='face',fit_arcs=True,thickness=0.05,holes=True,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                say_time()
                tracks=FreeCAD.ActiveDocument.ActiveObject
                tracks.Placement.Base.z = tracks.Placement.Base.z - (pcbThickness + deltaz)
                new_obj = simple_cpy(tracks,'botTracks'+ftname_sfx)
                say_time()
                # removesubtree([tracks])
                add_toberemoved.append([tracks])
                botTracks = new_obj
                #stop
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        pcb.makeZones(shape_type='face',thickness=0.05, fit_arcs=True,holes=True) # ,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                say_time()
                zones=FreeCAD.ActiveDocument.ActiveObject
                zones.Placement.Base.z = zones.Placement.Base.z - (pcbThickness + deltaz)
                new_obj = simple_cpy(zones,'botZones'+ftname_sfx)
                say_time()
                # removesubtree([zones])
                add_toberemoved.append([zones])
                botZones = new_obj
            if len (FreeCAD.ActiveDocument.getObjectsByLabel('Pcb'+ftname_sfx)) >0:
                #PCB_Sketch_5737
                pcb_sk = FreeCAD.ActiveDocument.getObject('PCB_Sketch'+ftname_sfx)
                ### check if BBOx pcb > BBOx tracks
                if botPads is not None:
                    botPads.Placement = FreeCAD.ActiveDocument.getObject('Pcb'+ftname_sfx).Placement
                    #if (botPads.Shape.BoundBox.XLength > pcb_sk.Shape.BoundBox.XLength) or \
                    #        (botPads.Shape.BoundBox.YLength > pcb_sk.Shape.BoundBox.YLength):
                    if (botPads.Shape.BoundBox.XMax > pcb_sk.Shape.BoundBox.XMax) or \
                            (botPads.Shape.BoundBox.XMin < pcb_sk.Shape.BoundBox.XMin) or \
                            (botPads.Shape.BoundBox.YMax > pcb_sk.Shape.BoundBox.YMax) or \
                            (botPads.Shape.BoundBox.YMin < pcb_sk.Shape.BoundBox.YMin):
                        botPads_cut_Name, temp_tobedeleted = cut_out_tracks(pcb_sk,botPads,ftname_sfx)
                        botPads = FreeCAD.ActiveDocument.getObject(botPads_cut_Name)
                        add_toberemoved.append(temp_tobedeleted)
                    botPads.Placement.Base.z-=pcbThickness+2*deltaz
                if botTracks is not None:
                    botTracks.Placement = FreeCAD.ActiveDocument.getObject('Pcb'+ftname_sfx).Placement
                    botTracks.Placement.Base.z-=pcbThickness+deltaz
                if botZones is not None:
                    botZones.Placement = FreeCAD.ActiveDocument.getObject('Pcb'+ftname_sfx).Placement
                    botZones.Placement.Base.z-=pcbThickness+deltaz
                if len (FreeCAD.ActiveDocument.getObjectsByLabel('Board_Geoms'+ftname_sfx)) > 0:
                    if use_AppPart and not use_LinkGroups:
                        if botPads is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).addObject(botPads)
                        if botTracks is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).addObject(botTracks)
                        if botZones is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).addObject(botZones)
                    elif use_LinkGroups:
                        if botPads is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(botPads,None,'',[])
                        if botTracks is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(botTracks,None,'',[])
                        if botZones is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(botZones,None,'',[])
        say_time()
        
        if FreeCAD.ActiveDocument is not None:
            FreeCADGui.SendMsgToActiveView("ViewFit")
            FreeCADGui.ActiveDocument.activeView().viewAxonometric()
            return add_toberemoved
###
