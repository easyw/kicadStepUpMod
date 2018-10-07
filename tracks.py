import kicad
#import kicad; import importlib; importlib.reload(kicad)
import time
import PySide
from PySide import QtGui, QtCore
import sys,os
import FreeCAD, FreeCADGui
global start_time, last_pcb_path

current_milli_time = lambda: int(round(time.time() * 1000))
def say_time():
    end_milli_time = current_milli_time()
    running_time=(end_milli_time-start_time)/1000
    msg="running time: "+str(running_time)+"sec"
    print(msg)
###

from kicadStepUptools import removesubtree, cfg_read_all
from kicadStepUptools import KicadPCB
#filename="C:/Cad/Progetti_K/ksu-test/pic_smart_switch.kicad_pcb"
#filename="C:/Cad/Progetti_K/eth-32gpio/eth-32gpio.kicad_pcb"
def addtracks():
    global start_time, last_pcb_path
    #cfg_read_all()
    Filter=""
    if 'last_pcb_path' in globals():
        print (last_pcb_path)
        if len (last_pcb_path) == 0:
            last_pcb_path = ""
    else:
        last_pcb_path = ""
    print(last_pcb_path)
    fname, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open File...",
                last_pcb_path, "*.kicad_pcb")
    path, name = os.path.split(fname)
    #filename=os.path.splitext(name)[0]
    filename = fname
    #importDXF.open(os.path.join(dirname,filename))
    if len(fname) > 0:
        start_time=current_milli_time()
        
        mypcb = KicadPCB.load(filename)
        pcbThickness = float(mypcb.general.thickness)
        #print (mypcb.general.thickness)
        print(mypcb.layers)
        
        #if version>=4:
        Top_lvl=0;Bot_lvl=31
        #for lynbr in mypcb.layers: #getting layers name
        #    if float(lynbr) == Top_lvl:
        #        LvlTopName=(mypcb.layers['{0}'.format(str(lynbr))][0])
        #    if float(lynbr) == Bot_lvl:
        #        LvlBotName=(mypcb.layers['{0}'.format(str(lynbr))][0])
        #print(LvlTopName,'  ',LvlBotName)
        pcb = kicad.KicadFcad(filename)
        #pcb.setLayer(LvlTopName)
        pcb.setLayer(Top_lvl)
        pcb.makeCopper(holes=True)
        
        doc=FreeCAD.ActiveDocument
        docG=FreeCADGui.ActiveDocument
        deltaz=0.01 #10 micron
        composed = doc.ActiveObject
        s = composed.Shape
        doc.addObject('Part::Feature',"topTraks").Shape=s
        topTracks = doc.ActiveObject
        topTracks.Label="topTracks"
        topTracks.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,deltaz),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
        #if hasattr(doc.Pcb, 'Shape'):
        if len (doc.getObjectsByLabel('Pcb')) >0:
            topTracks.Placement = doc.getObjectsByLabel('Pcb')[0].Placement
            topTracks.Placement.Base.z+=deltaz
            if len (doc.getObjectsByLabel('Board_Geoms')) > 0:
                doc.getObject('Board_Geoms').addObject(topTracks)
        
        #topTracks.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0.05),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
        docG.getObject(topTracks.Name).Transparency=40
        docG.getObject(topTracks.Name).ShapeColor = (0.78,0.46,0.20)
        FreeCADGui.Selection.addSelection(doc.getObject(composed.Name))
        removesubtree(FreeCADGui.Selection.getSelection())
        say_time()
        
        #pcb.setLayer(LvlBotName)
        pcb.setLayer(Bot_lvl)
        pcb.makeCopper(holes=True)
        
        composed = doc.ActiveObject
        s = composed.Shape
        doc.addObject('Part::Feature',"botTraks").Shape=s
        botTracks = doc.ActiveObject
        botTracks.Label="botTracks"
        botTracks.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,-1.6-deltaz),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))    
        docG.getObject(botTracks.Name).Transparency=40
        docG.getObject(botTracks.Name).ShapeColor = (0.78,0.46,0.20)
        FreeCADGui.Selection.addSelection(doc.getObject(composed.Name))
        removesubtree(FreeCADGui.Selection.getSelection())
        
        #if hasattr(doc.Pcb, 'Shape'):
        if len (doc.getObjectsByLabel('Pcb')) > 0:
            botTracks.Placement = doc.getObjectsByLabel('Pcb')[0].Placement
            #botTracks.Placement = doc.Pcb.Placement
            botTracks.Placement.Base.z-=pcbThickness+deltaz
            if len (doc.getObjectsByLabel('Board_Geoms')) > 0:
                doc.getObject('Board_Geoms').addObject(botTracks)
        #botTracks = FreeCAD.ActiveDocument.ActiveObject
        #botTracks.Label="botTracks"
        #botTracks.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,-1.6),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))    
        #docG.ActiveObject.Transparency=40
        say_time()
        
        FreeCADGui.SendMsgToActiveView("ViewFit")
        docG.activeView().viewAxonometric()