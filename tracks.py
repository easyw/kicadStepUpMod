#!/usr/bin/python
# -*- coding: utf-8 -*-
#****************************************************************************

import kicad_parser
#import kicad_parser; import importlib; importlib.reload(kicad_parser)
import time
import PySide
from PySide import QtGui, QtCore
import sys,os
import FreeCAD, FreeCADGui
global start_time, last_pcb_path, min_drill_size

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

from kicadStepUptools import removesubtree, cfg_read_all
from kicadStepUptools import KicadPCB, make_unicode, make_string
#filename="C:/Cad/Progetti_K/ksu-test/pic_smart_switch.kicad_pcb"
#filename="C:/Cad/Progetti_K/eth-32gpio/eth-32gpio.kicad_pcb"
def addtracks():
    global start_time, last_pcb_path, min_drill_size
    global use_LinkGroups, use_AppPart
    import sys
    
    # cfg_read_all() it doesn't work through different files
    # print (min_drill_size)
    
    Filter=""
    pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
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
        mypcb = KicadPCB.load(filename)
        pcbThickness = float(mypcb.general.thickness)
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
        import kicad_parser; reload_lib(kicad_parser)
        pcb = kicad_parser.KicadFcad(filename)
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
        pcb.makeCopper(holes=True, minSize=minSizeDrill)
        doc=FreeCAD.ActiveDocument
        docG=FreeCADGui.ActiveDocument
        deltaz = 0.01 #10 micron
        composed = doc.ActiveObject
        s = composed.Shape
        doc.addObject('Part::Feature','topTracks').Shape=composed.Shape
        topTracks = doc.ActiveObject
        #print (doc.ActiveObject.Label)
        #print (topTracks.Label)
        docG.ActiveObject.ShapeColor   = docG.getObject(composed.Name).ShapeColor
        docG.ActiveObject.LineColor    = docG.getObject(composed.Name).LineColor
        docG.ActiveObject.PointColor   = docG.getObject(composed.Name).PointColor
        docG.ActiveObject.DiffuseColor = docG.getObject(composed.Name).DiffuseColor
        #doc.recompute()
        #doc.addObject('Part::Feature',"topTraks").Shape=s
        topTracks.Label="topTracks"
        topTracks.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,deltaz),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
        #if hasattr(doc.Pcb, 'Shape'):
        if len (doc.getObjectsByLabel('Pcb')) >0:
            topTracks.Placement = doc.getObjectsByLabel('Pcb')[0].Placement
            topTracks.Placement.Base.z+=deltaz
            if len (doc.getObjectsByLabel('Board_Geoms')) > 0:
                if use_AppPart and not use_LinkGroups:
                    doc.getObject('Board_Geoms').addObject(topTracks)
                elif use_LinkGroups:
                    doc.getObject('Board_Geoms').ViewObject.dropObject(topTracks,None,'',[])
        #topTracks.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0.05),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
        ##docG.getObject(topTracks.Name).Transparency=40
        if 0:
            docG.getObject(topTracks.Name).ShapeColor = (0.78,0.46,0.20)
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(doc.getObject(composed.Name))
        #stop
        removesubtree(FreeCADGui.Selection.getSelection())
        say_time()
        #except Exception as e:
        #    exc_type, exc_obj, exc_tb = sys.exc_info()
        #    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #    FreeCAD.Console.PrintError('error class: '+str(exc_type)+'\nfile name: '+str(fname)+'\nerror @line: '+str(exc_tb.tb_lineno)+'\nerror value: '+str(e.args[0])+'\n')
        
        #try:    #doing bot tracks layer
        #pcb.setLayer(LvlBotName)
        pcb.setLayer(Bot_lvl)
        pcb.makeCopper(holes=True, minSize=minSizeDrill)
        composed = doc.ActiveObject
        s = composed.Shape
        doc.addObject('Part::Feature','botTracks').Shape=composed.Shape
        botTracks = doc.ActiveObject
        #print (doc.ActiveObject.Label)
        #print (topTracks.Label)
        docG.ActiveObject.ShapeColor   = docG.getObject(composed.Name).ShapeColor
        docG.ActiveObject.LineColor    = docG.getObject(composed.Name).LineColor
        docG.ActiveObject.PointColor   = docG.getObject(composed.Name).PointColor
        docG.ActiveObject.DiffuseColor = docG.getObject(composed.Name).DiffuseColor
        #doc.recompute()
        #doc.addObject('Part::Feature',"topTraks").Shape=s
        botTracks.Label="botTracks"
        botTracks.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,-1.6-deltaz),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))            
        #if hasattr(doc.Pcb, 'Shape'):
        ##docG.getObject(botTracks.Name).Transparency=40
        if 0:
            docG.getObject(botTracks.Name).ShapeColor = (0.78,0.46,0.20)
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(doc.getObject(composed.Name))
        
        removesubtree(FreeCADGui.Selection.getSelection())
        #if hasattr(doc.Pcb, 'Shape'):
        if len (doc.getObjectsByLabel('Pcb')) > 0:
            botTracks.Placement = doc.getObjectsByLabel('Pcb')[0].Placement
            #botTracks.Placement = doc.Pcb.Placement
            botTracks.Placement.Base.z-=pcbThickness+deltaz
            if len (doc.getObjectsByLabel('Board_Geoms')) > 0:
                if use_AppPart and not use_LinkGroups:
                    doc.getObject('Board_Geoms').addObject(botTracks)
                elif use_LinkGroups:
                    doc.getObject('Board_Geoms').ViewObject.dropObject(botTracks,None,'',[])
        #botTracks = FreeCAD.ActiveDocument.ActiveObject
        #botTracks.Label="botTracks"
        #botTracks.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,-1.6),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))    
        #docG.ActiveObject.Transparency=40
        #except Exception as e:
        #    exc_type, exc_obj, exc_tb = sys.exc_info()
        #    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #    FreeCAD.Console.PrintError('error class: '+str(exc_type)+'\nfile name: '+str(fname)+'\nerror @line: '+str(exc_tb.tb_lineno)+'\nerror value: '+str(e.args[0])+'\n')
        say_time()
        
        FreeCADGui.SendMsgToActiveView("ViewFit")
        docG.activeView().viewAxonometric()
