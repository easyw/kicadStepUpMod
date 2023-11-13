#!/usr/bin/python
# -*- coding: utf-8 -*-
#****************************************************************************

global tracks_version
tracks_version = '2.6.5'

import kicad_parser
#import kicad_parser; import importlib; importlib.reload(kicad_parser)
import time
import PySide
from PySide import QtGui, QtCore
QtWidgets = QtGui
import sys,os
import FreeCAD, FreeCADGui
import Draft, Part
global start_time, last_pcb_path, min_drill_size
global FC_export_min_version
FC_export_min_version="11670"  #11670 latest JM

# from kicadStepUptools import PLine
from kicad_parser import makeVect, make_gr_rect, make_gr_poly, makeThickLine
from fcad_parser import unquote #maui

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
    # print (pcbsk.Name)
    #shp = pcbsk.Shape.copy()
    # shp_nw = pcbsk.copy()
    #Part.show(shp)
    doc = FreeCAD.ActiveDocument
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(doc.Name,pcbsk.Name)
    FreeCADGui.runCommand('Std_Copy',0)
    FreeCADGui.runCommand('Std_Paste',0)
    shp_nw=FreeCAD.ActiveDocument.ActiveObject
    extrude.Base = shp_nw #pcbsk
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
    try:
        extrude.adjustRelativeLinks(FreeCAD.ActiveDocument.getObject('Board_Geoms'+tname_sfx))
        FreeCAD.ActiveDocument.getObject('Board_Geoms'+tname_sfx).addObject(extrude)
    except:
        FreeCAD.Console.PrintWarning('error on moving Board Geoms inside Part container\n')
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
        FreeCAD.ActiveDocument.removeObject(shp_nw.Name)
    else:
        doc = FreeCAD.ActiveDocument
        #temp_tobedeleted.append([doc.getObject(Common_Top.Name),doc.getObject(tracks.Name),doc.getObject(extrude.Name)])
        temp_tobedeleted.append(doc.getObject(Common_Top.Name))
        temp_tobedeleted.append(doc.getObject(tracks.Name))
        temp_tobedeleted.append(doc.getObject(extrude.Name))
        temp_tobedeleted.append(doc.getObject(shp_nw.Name))
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
    import kicad_parser
    FreeCAD.Console.PrintMessage('kicad_parser_version '+kicad_parser.__kicad_parser_version__+'\n') # maui 

    # cfg_read_all() it doesn't work through different files
    # print (min_drill_size)
    
    FreeCAD.Console.PrintMessage('tracks version: '+tracks_version+'\n')
    Filter=""
    pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
    if fname is None:
        last_pcb_path = pg.GetString("last_pcb_path")
        if len (last_pcb_path) == 0:
                last_pcb_path = ""
        prefs_ = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
        #print('native_dlg',prefs_.GetBool('native_dlg'))
        if not(prefs_.GetBool('not_native_dlg')):
            fname, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open File...",
                make_unicode(last_pcb_path), "*.kicad_pcb")
        else:
            fname, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open File...",
                make_unicode(last_pcb_path), "*.kicad_pcb",options=QtWidgets.QFileDialog.DontUseNativeDialog)
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
        #pcb_color_values = [light_green,green,blue,red,purple,darkgreen,darkblue,lightblue,yellow,black,white]
        assign_col=['#41c382','#5d917a','#2474cf','#ff4000','#9a1a85','#3c7f5d','#426091','#005fff','#fff956','#4d4d4d','#f0f0f0']
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
        pcb_sk = None
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
        #pcb = kicad_parser.KicadFcad(filename,via_skip_hole=False,via_bound=0)
        pcb = kicad_parser.KicadFcad(filename,merge_pads=False)  # creating multiple shape, one each pad item
        # pcb = kicad_parser.KicadFcad(filename,merge_pads=True)
        #kicad.KicadFcad(filename,via_skip_hole=False,via_bound=1)
        ## pcb = kicad_parser.KicadFcad(filename, arc_fit_accuracy=1e-4) #to increase accuracy 
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
        #pcb.makePads(shape_type='face',thickness=0.05,holes=True,fit_arcs=True) #,prefix='')
        pcb.makePads(shape_type='face',thickness=0.05,holes=True,fit_arcs=True) #,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                pads=FreeCAD.ActiveDocument.ActiveObject
                pads.Placement.Base.z = pads.Placement.Base.z + 2*deltaz
                new_obj = simple_cpy(pads,'topPads'+ftname_sfx)
                say_time()
                # removesubtree([pads])
                pads.ViewObject.Visibility = False
                add_toberemoved.append([pads])
                topPads = new_obj
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        # pcb.makeTracks(shape_type='face',fit_arcs=True,thickness=0.05,holes=True) #,prefix='')
        # pcb.makeTracks(shape_type='face',fit_arcs=True,thickness=0.05,holes=True) #,prefix='')
        pcb.makeTracks(shape_type='face',fit_arcs=True,thickness=0.05,holes=False) # holes=True) #,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                tracks_=FreeCAD.ActiveDocument.ActiveObject
                objsNum = len(FreeCAD.ActiveDocument.Objects)
                #print(objsNum,len(FreeCAD.ActiveDocument.Objects))
                holes=pcb.makeHoles(oval=True)
                #print(objsNum,len(FreeCAD.ActiveDocument.Objects))
                if (objsNum) < len(FreeCAD.ActiveDocument.Objects):
                    drl = Draft.makeShape2DView(holes, FreeCAD.Vector(0.0, 0.0, 1.0))
                    recompute_active_object()
                    holesSk = Draft.makeSketch(FreeCAD.ActiveDocument.ActiveObject, autoconstraints=True)
                    recompute_active_object()
                    extrude_holes(holesSk,pcbThickness*3)
                    holes_ = FreeCAD.ActiveDocument.ActiveObject
                    cut_fuzzy(tracks_,holes_,0.00006) #6e-5 fuzzy tolerance
                    holes.ViewObject.Visibility = False
                    holes_.ViewObject.Visibility = False
                    holesSk.ViewObject.Visibility = False
                    drl.ViewObject.Visibility = False
                    add_toberemoved.append([holes,holes_,holesSk,drl])
                say_time()
                tracks=FreeCAD.ActiveDocument.ActiveObject
                tracks.Placement.Base.z+=deltaz
                tracks.ViewObject.ShapeColor=mkColor(trk_col)
                new_obj = simple_cpy(tracks,'topTracks'+ftname_sfx)
                say_time()
                # removesubtree([tracks])
                tracks.ViewObject.Visibility = False
                tracks_.ViewObject.Visibility = False
                add_toberemoved.append([tracks,tracks_])
                topTracks = new_obj
                #stop
        
        if 0:
            ply_area=[]
            for lp in mypcb.gr_poly: #pcb area polylines    
                if 'F.Cu' not in lp.layer:
                    continue
                # print(lp, lp.fill)
                if lp.fill != 'solid':
                    continue
                # print('solid')
                ply_lines = []
                edges=[]
                ind = 0
                l = len(lp.pts.xy)
                # print(l)
                for p in lp.pts.xy:
                    if ind == 0:
                        # line1=Part.Edge(PLine(FreeCAD.Base.Vector(lp.pts.xy[l-1][0],-lp.pts.xy[l-1][1],0), FreeCAD.Base.Vector(lp.pts.xy[0][0],-lp.pts.xy[0][1],0)))
                        # edges.append(line1);
                        line2=Part.Edge(PLine(FreeCAD.Base.Vector(lp.pts.xy[l-1][0],-lp.pts.xy[l-1][1],0), FreeCAD.Base.Vector(lp.pts.xy[0][0],-lp.pts.xy[0][1],0)))
                        ply_lines.append(line2)
                    else:
                        # line1=Part.Edge(PLine(FreeCAD.Base.Vector(lp.pts.xy[ind-1][0],-lp.pts.xy[ind-1][1],0), FreeCAD.Base.Vector(lp.pts.xy[ind][0],-lp.pts.xy[ind][1],0)))
                        # edges.append(line1);
                        line2=Part.Edge(PLine(FreeCAD.Base.Vector(lp.pts.xy[ind-1][0],-lp.pts.xy[ind-1][1],0), FreeCAD.Base.Vector(lp.pts.xy[ind][0],-lp.pts.xy[ind][1],0)))
                        ply_lines.append(line2)
                    ind+=1
                
                if len(ply_lines)>0:
                    #w=Part.Wire(edges)
                    #Part.show(Part.Wire(edges))
                    wl=Part.Wire(ply_lines)
                    # Part.show(Part.Wire(ply_lines))
                    # fc=Part.makeFace(w,'Part::FaceMakerSimple')
                    fc=Part.makeFace(wl,'Part::FaceMakerSimple')
                    ply_area.append(fc)
                
            if len(ply_area) > 0:
                Part.show(Part.makeCompound(ply_area))

        ws=[]
        wst=[]
        for j,pl in enumerate(mypcb.gr_poly): #pcb area polylines          
            if unquote(pl.layer) == 'F.Cu':
                pln=Part.Wire(make_gr_poly(pl))
                if pl.fill == 'solid':
                    ws.append((pln))
                if hasattr(pl,'stroke'):
                    width = pl.stroke.width
                else:
                    width = pl.width
                for e in pln.Edges:
                    #aco=_wire(e,self.layer)
                    wst.append(makeThickLine(makeVect([e.Vertexes[0].X,-e.Vertexes[0].Y]),makeVect([e.Vertexes[1].X,-e.Vertexes[1].Y]),width/2.0))
                # cp = Part.makeCompound(wst+ws)
                # fc=Part.makeFace(cp,'Part::FaceMakerSimple')
                # Part.show(fc)
        #if len (ws)>0:
        #    fc=Part.makeFace(ws,'Part::FaceMakerSimple')
        #    Part.show(fc)
        if len (wst)>0 or len(ws)>0:
            if 0:
                f=Part.makeFace(wst[0],'Part::FaceMakerSimple')
                f1=Part.makeFace(wst[1],'Part::FaceMakerSimple')
                f2=f.fuse(f1)
                Part.show(f2)
                Part.show(f)
                Part.show(f1)
                for w in wst[1:]:
                    f.fuse(Part.makeFace(w,'Part::FaceMakerSimple'))
                Part.show(f)
            fc=Part.makeFace(Part.makeCompound(wst+ws),'Part::FaceMakerSimple')
            Part.show(fc)
        print('TBD: gr_rect,gr_poly use stroke width (w makethickline)')
        #stop
        gr_rects=[]
        for r in mypcb.gr_rect: #pcb area from rect
            if 'F.Cu' not in r.layer:
                continue
            if r.fill != 'solid':
                continue
            # rct = Part.show(make_gr_rect(r))
            if 0:
                l1=Part.Edge(PLine(FreeCAD.Base.Vector(r.start[0],-r.start[1],0), FreeCAD.Base.Vector(r.end[0],-r.start[1],0)))
                l2=Part.Edge(PLine(FreeCAD.Base.Vector(r.end[0],-r.start[1],0), FreeCAD.Base.Vector(r.end[0],-r.end[1],0)))
                l3=Part.Edge(PLine(FreeCAD.Base.Vector(r.end[0],-r.end[1],0), FreeCAD.Base.Vector(r.start[0],-r.end[1],0)))
                l4=Part.Edge(PLine(FreeCAD.Base.Vector(r.start[0],-r.end[1],0), FreeCAD.Base.Vector(r.start[0],-r.start[1],0)))
                w=Part.Wire([l1,l2,l3,l4])
                #Part.show(w)
                fc=Part.makeFace(w,'Part::FaceMakerSimple')
                #Part.show(fc)
                gr_rects.append(fc)
            fc = Part.makeFace(make_gr_rect(r),'Part::FaceMakerSimple')
            gr_rects.append(fc)

        if len(gr_rects) > 0:
            Part.show(Part.makeCompound(gr_rects))
        
        gr_circles=[]
        for c in mypcb.gr_circle: #pcb area from circles
            if 'F.Cu' not in c.layer:
                continue
            if c.fill != 'solid':
                continue        
            width = c.stroke.width
            center = makeVect(c.center)
            end = makeVect(c.end)
            r = center.distanceToPoint(end)
            c = FreeCAD.Base.Vector(0,0,0)
            d = FreeCAD.Base.Vector(0,0,1)
            cr1=(Part.makeFace(Part.makeCircle(r+width*0.5, center),'Part::FaceMakerSimple'))
            gr_circles.append(cr1)
        if len(gr_circles) > 0:
            Part.show(Part.makeCompound(gr_circles))
            
        print('TBD: gr_rect,gr_poly use stroke width (w makethickline), FC build date') 
        #stop
        
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        #pcb.makeZones(shape_type='face',thickness=0.05, fit_arcs=True,holes=True) #,prefix='')
        prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
        skip_import_zones = prefs.GetBool('skip_import_zones')
        if skip_import_zones != True:
            pcb.makeZones(shape_type='face',thickness=0.05, fit_arcs=True,holes=True) #,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                say_time()
                zones=FreeCAD.ActiveDocument.ActiveObject
                zones.Placement.Base.z+=deltaz
                new_obj = simple_cpy(zones,'topZones'+ftname_sfx)
                say_time()
                # removesubtree([zones])
                zones.ViewObject.Visibility = False
                add_toberemoved.append([zones])
                topZones = new_obj
            if len (FreeCAD.ActiveDocument.getObjectsByLabel('Pcb'+ftname_sfx)) >0:
                #PCB_Sketch_5737
                # pcb_sk = FreeCAD.ActiveDocument.getObject('PCB_Sketch'+ftname_sfx)
                pcb_ = FreeCAD.ActiveDocument.getObject('Pcb'+ftname_sfx)
                area_max=0
                f_max=''
                for f in pcb_.Shape.Faces:
                    # print (f.Area)
                    if f.Area > area_max:
                        area_max=f.Area
                        f_max=f
                        #print (area_max)
                    #print('area_max=',area_max)
                ### check if BBOx pcb > BBOx tracks
                # Part.show(f_max.OuterWire)
                #Part.show(Part.makeFace(f_max.OuterWire,'Part::FaceMakerSimple').extrude(FreeCAD.Vector(0.0, 0.0, -pcbThickness)))
                if 0: #max lenth esternal perimeter 
                    l_max=0
                    w_max=''
                    for w in f_max.Wires:
                        if w.Length > l_max:
                            l_max=w.Length
                            w_max=w
                    pcb_sk = Draft.makeSketch(w_max,autoconstraints=True)
                FC_majorV,FC_minorV,FC_git_Nbr=getFCversion()
                if FC_majorV>=0 and FC_minorV>=21:
                    pcb_sk = Draft.makeSketch(f_max,autoconstraints=True)
                    #pcb_sk.autoRemoveRedundants(True)
                    #pcb_sk.solve()
                    FreeCAD.ActiveDocument.recompute()   
                    if len (pcb_sk.RedundantConstraints)>0:
                        print('fixing over constrained sketch')
                        new_constrains=[]
                        list1 = pcb_sk.Constraints 
                        index_list=pcb_sk.RedundantConstraints
                        for i in range(len(index_list)):
                            index_list[i] -= 1
                        index_set = set(index_list) # optional but faster    
                        new_constrains=[x for i, x in enumerate(list1) if i not in index_set]
                        pcb_sk.Constraints=new_constrains
                        FreeCAD.ActiveDocument.recompute()
                    # pcb_sk = Draft.makeSketch(f_max.OuterWire,autoconstraints=True)  # esternal perimeter 
                else:
                    pcb_sk = Draft.makeSketch(f_max,autoconstraints=False)
                    FreeCAD.ActiveDocument.recompute()
                
                add_toberemoved.append([pcb_sk])
                
                #stop
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
                        print('TBD pcb sketch open due to edgecuts in fp')
                        # Part.show(App.ActiveDocument.Cut.Shape.Faces[64].OuterWire)
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
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(topPads,topPads,'',[])
                        if topTracks is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(topTracks,topTracks,'',[])
                        if topZones is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(topZones,topZones,'',[])
        #try:    #doing bot tracks layer
        #pcb.setLayer(LvlBotName)
        #stop
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
        #pcb.makePads(shape_type='face',thickness=0.05,holes=True,fit_arcs=True,prefix='')
        pcb.makePads(shape_type='face',thickness=0.05,holes=True,fit_arcs=True) #,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                doc=FreeCAD.ActiveDocument
                padsB=FreeCAD.ActiveDocument.ActiveObject
                padsB.Placement.Base.z = padsB.Placement.Base.z - (pcbThickness + 2*deltaz)
                new_obj = simple_cpy(padsB,'botPads'+ftname_sfx)
                say_time()
                # removesubtree([pads])
                padsB.ViewObject.Visibility = False
                add_toberemoved.append([padsB])
                botPads = new_obj
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        # pcb.makeTracks(shape_type='face',fit_arcs=True,thickness=0.05,holes=True,prefix='')
        pcb.makeTracks(shape_type='face',fit_arcs=True,thickness=0.05,holes=False) # holes=True) #,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                tracksB_=FreeCAD.ActiveDocument.ActiveObject
                objsNum = len(FreeCAD.ActiveDocument.Objects)
                holesB=pcb.makeHoles(oval=True)
                if (objsNum) < len(FreeCAD.ActiveDocument.Objects):
                    drlB = Draft.makeShape2DView(holesB, FreeCAD.Vector(0.0, 0.0, 1.0))
                    recompute_active_object()
                    holesSkB = Draft.makeSketch(FreeCAD.ActiveDocument.ActiveObject, autoconstraints=True)
                    recompute_active_object()
                    extrude_holes(holesSkB,pcbThickness*3)
                    holesB_ = FreeCAD.ActiveDocument.ActiveObject
                    cut_fuzzy(tracksB_,holesB_,0.00006) #6e-5 fuzzy tolerance
                    holesB.ViewObject.Visibility = False
                    holesB_.ViewObject.Visibility = False
                    holesSkB.ViewObject.Visibility = False
                    drlB.ViewObject.Visibility = False
                    add_toberemoved.append([holesB,holesB_,holesSkB,drlB])
                say_time()
                tracksB=FreeCAD.ActiveDocument.ActiveObject
                tracksB.Placement.Base.z-=(pcbThickness + deltaz)
                tracksB.ViewObject.ShapeColor=mkColor(trk_col)
                new_obj = simple_cpy(tracksB,'botTracks'+ftname_sfx)
                say_time()
                # removesubtree([tracks])
                tracksB.ViewObject.Visibility = False
                tracksB_.ViewObject.Visibility = False
                add_toberemoved.append([tracksB,tracksB_])
                botTracks = new_obj
                #stop
        if FreeCAD.ActiveDocument is not None:
            objsNum = len(FreeCAD.ActiveDocument.Objects)
        #pcb.makeZones(shape_type='face',thickness=0.05, fit_arcs=True,holes=True) # ,prefix='')
        if skip_import_zones != True:
            pcb.makeZones(shape_type='face',thickness=0.05, fit_arcs=True,holes=True) # ,prefix='')
        if FreeCAD.ActiveDocument is not None:
            if objsNum < len(FreeCAD.ActiveDocument.Objects):
                say_time()
                zonesB=FreeCAD.ActiveDocument.ActiveObject
                zonesB.Placement.Base.z = zonesB.Placement.Base.z - (pcbThickness + deltaz)
                new_obj = simple_cpy(zonesB,'botZones'+ftname_sfx)
                say_time()
                # removesubtree([zones])
                zonesB.ViewObject.Visibility = False
                add_toberemoved.append([zonesB])
                botZones = new_obj
            if len (FreeCAD.ActiveDocument.getObjectsByLabel('Pcb'+ftname_sfx)) >0:
                #PCB_Sketch_5737
                # pcb_sk = FreeCAD.ActiveDocument.getObject('PCB_Sketch'+ftname_sfx)
                if pcb_sk is None:
                    pcb_ = FreeCAD.ActiveDocument.getObject('Pcb'+ftname_sfx)
                    area_max=0
                    f_max=''
                    for f in pcb_.Shape.Faces:
                        # print (f.Area)
                        if f.Area > area_max:
                            area_max=f.Area
                            f_max=f
                            # print (area_max)
                        # print('area_max=',area_max)
                    ### check if BBOx pcb > BBOx tracks
                    # Part.show(f_max.OuterWire)
                    #Part.show(Part.makeFace(f_max.OuterWire,'Part::FaceMakerSimple').extrude(FreeCAD.Vector(0.0, 0.0, -pcbThickness)))
                    # pcb_sk = Draft.makeSketch(f_max.OuterWire,autoconstraints=True) # external perimeter
                    pcb_sk = Draft.makeSketch(f_max,autoconstraints=True)
                    #pcb_sk = Draft.makeSketch(f_max,autoconstraints=False)
                    FreeCAD.ActiveDocument.recompute()   
                    if len (pcb_sk.RedundantConstraints)>0:
                        #stop
                        new_constrains=[]
                        list1 = pcb_sk.Constraints 
                        index_list=pcb_sk.RedundantConstraints
                        for i in range(len(index_list)):
                            index_list[i] -= 1
                        index_set = set(index_list) # optional but faster    
                        new_constrains=[x for i, x in enumerate(list1) if i not in index_set]
                        pcb_sk.Constraints=new_constrains
                        FreeCAD.ActiveDocument.recompute()
                    add_toberemoved.append([pcb_sk])
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
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(botPads,botPads,'',[])
                        if botTracks is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(botTracks,botTracks,'',[])
                        if botZones is not None:
                            FreeCAD.ActiveDocument.getObject('Board_Geoms'+ftname_sfx).ViewObject.dropObject(botZones,botZones,'',[])
        if skip_import_zones == True:
            FreeCAD.Console.PrintWarning('import Zone(s) skipped'+'\n')
        say_time()
        
        if FreeCAD.ActiveDocument is not None:
            FreeCADGui.SendMsgToActiveView("ViewFit")
            # FreeCADGui.ActiveDocument.activeView().viewAxonometric()
            return add_toberemoved
###
