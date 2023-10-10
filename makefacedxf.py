# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Cad\Progetti_K\3D-FreeCad-tools\explode.ui'
#
# Created: Fri Sep 21 14:09:48 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

import FreeCAD, FreeCADGui, os, Part
import PySide
from PySide import QtGui, QtCore
QtWidgets = QtGui
from sys import platform as _platform
import sys,os
import time
global copper_diffuse, silks_diffuse, silks_version, use_dxf_internal
use_dxf_internal = True

global use_AppPart, use_Links, use_LinkGroups
use_AppPart=False # False
use_Links=False

global FC_export_min_version
FC_export_min_version="11670"  #11670 latest JM
silks_version = '1.3'

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

def crc_gen_d(data):
    import binascii
    import re
    
    #data=u'Würfel'
    content=re.sub(r'[^\x00-\x7F]+','_', data)
    #make_unicode(hex(binascii.crc_hqx(content.encode('utf-8'), 0x0000))[2:])
    #hex(binascii.crc_hqx(content.encode('utf-8'), 0x0000))[2:].encode('utf-8')
    #print(data +u'_'+ hex(binascii.crc_hqx(content.encode('utf-8'), 0x0000))[2:])
    return u'_'+ make_unicode_d(hex(binascii.crc_hqx(content.encode('utf-8'), 0x0000))[2:])
##

def make_unicode_d(input):
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

def find_pcb_name():
    #searching for a pcb 
    pcb_name = ''
    for o in FreeCAD.ActiveDocument.Objects:
        if 'Pcb' in o.Label:
            pcb_name=o.Name
            break
    return pcb_name

def say(msg):
    FreeCAD.Console.PrintMessage(msg)
    FreeCAD.Console.PrintMessage('\n')

metal_copper="""material DEF MET-COPPER Material {
        ambientIntensity 0.022727
        diffuseColor 0.7038 0.27048 0.0828
        specularColor 0.780612 0.37 0.000000
        emissiveColor 0.000000 0.000000 0.000000
        shininess 0.2
        transparency 0.0
        }"""    

copper_diffuse = (0.7038, 0.27048, 0.0828)
silks_diffuse = (0.98,0.92,0.84)

# Name      Ambient                             Diffuse                             Specular                            Shininess
# brass     0.329412    0.223529    0.027451    0.780392    0.568627    0.113725    0.992157    0.941176    0.807843    0.21794872
brass_diffuse = (0.780392,0.568627,0.113725)

def simple_cpy (obj,lbl):
    copy = FreeCAD.ActiveDocument.addObject('Part::Feature',obj.Name)
    copy.Label = lbl
    copy.Shape = obj.Shape
    copy.ViewObject.ShapeColor   = obj.ViewObject.ShapeColor
    copy.ViewObject.LineColor    = obj.ViewObject.LineColor
    copy.ViewObject.PointColor   = obj.ViewObject.PointColor
    copy.ViewObject.DiffuseColor = obj.ViewObject.DiffuseColor
    return copy


if not use_dxf_internal:
    import importDXF
else:
    from dxf_parser import _importDXF
from kicadStepUptools import make_unicode, make_string

def makeFaceDXF():
    global copper_diffuse, silks_diffuse, use_dxf_internal
    global use_LinkGroups, use_AppPart, silks_version
    import _DXF_Import
    from dxf_parser import _importDXF
    
    FreeCAD.Console.PrintMessage('SilkS version: '+silks_version+'\n')

    doc=FreeCAD.ActiveDocument
    if doc is None:
        FreeCAD.newDocument()
        doc=FreeCAD.ActiveDocument
    docG=FreeCADGui.ActiveDocument
    Filter=""
    last_pcb_path=""
    pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
    last_pcb_path = pg.GetString("last_pcb_path")
    prefs_ = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
    #print('native_dlg',prefs_.GetBool('native_dlg'))
    if not(prefs_.GetBool('not_native_dlg')):
        fn, Filter = PySide.QtGui.QFileDialog.getOpenFileNames(None, "Open File...",
                make_unicode(last_pcb_path), "*.dxf")
    else:
        fn, Filter = PySide.QtGui.QFileDialog.getOpenFileNames(None, "Open File...",
                make_unicode(last_pcb_path), "*.dxf",options=QtWidgets.QFileDialog.DontUseNativeDialog)
    for fname in fn:
        path, name = os.path.split(fname)
        filename=os.path.splitext(name)[0]
        say("filename = "+str(filename))
        #importDXF.open(os.path.join(dirname,filename))
        if len(fname) > 0:
            #importDXF.open(fname)
            last_pcb_path=os.path.dirname(fname)
            ftname_sfx=crc_gen_d(make_unicode_d(filename))

            pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
            pg.SetString("last_pcb_path", make_string(last_pcb_path)) # py3 .decode("utf-8")
            pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
            pcb_color_pos = pg.GetInt('pcb_color')
            #print(pcb_color_pos)
            if pcb_color_pos == 9:
                silks_diffuse = (0.18,0.18,0.18)  #slick black
            else:
                silks_diffuse = (0.98,0.92,0.84) # #antique white  # white (0.906,0.906,0.910)           
            doc=FreeCAD.ActiveDocument
            objects = []
            say("loading... ")
            t = time.time()
            if doc is not None:
                for o in doc.Objects:
                    objects.append(o.Name)
                if not use_dxf_internal:
                    importDXF.insert(fname, doc.Name)
                else:
                    say("Legacy internal DXF importer 1")
                    _importDXF.insert(fname, doc.Name, forcePrefs=True)
                    # _DXF_Import.insert(fname, doc.Name)
                    
            else:
                if not use_dxf_internal:
                    importDXF.open(fname)
                else:
                    say("Legacy internal DXF importer 2")
                    _importDXF.open(fname,forcePrefs=True)
                    # _DXF_Import.open(fname)
            imp_objects = []
            if doc is not None:
                for o in doc.Objects:
                    if o.Name not in str(objects):
                        imp_objects.append(o)
            FreeCADGui.SendMsgToActiveView("ViewFit")
            timeP = time.time() - t
            say("loading time = "+str(timeP) + "s")
            #print(imp_objects)

            if use_dxf_internal: # not(checkDXFsettings(True)):
                try:
                    say("standard DXF importer [using OSCD2Dg_edgestofaces]")
                    edges=sum((obj.Shape.Edges for obj in \
                    imp_objects if hasattr(obj,'Shape')),[])
                    #for edge in edges:
                    #    print "geomType ",DraftGeomUtils.geomType(edge)
                    import kicadStepUptools
                    if 0: #reload_Gui:
                        reload_lib( kicadStepUptools )
                    face = kicadStepUptools.OSCD2Dg_edgestofaces(edges,3 , kicadStepUptools.edge_tolerance)
                    ##face = OpenSCAD2Dgeom.edgestofaces(edges)
                    #face = OpenSCAD2DgeomMau.edgestofaces(edges)
                    if 0:
                        face.check() # reports errors
                        face.fix(0,0,0)
                    if 0:
                        faceobj = FreeCAD.ActiveDocument.addObject('Part::Feature',"Face")
                        faceobj.Label = "Face"
                        faceobj.Shape = face
                    # for obj in doc.Objects: # FreeCADGui.Selection.getSelection():
                    #     FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                    FreeCAD.ActiveDocument.recompute()
                    f = face
                    pass
                except Part.OCCError: # Exception: #
                    # FreeCAD.Console.PrintError('Error in source %s (%s)' % (faceobj.Name,faceobj.Label)+"\n")
                    FreeCAD.Console.PrintError('Error in source %s (%s)' % (face.Name,face.Label)+"\n")

            #stop

            if 0: #(checkDXFsettings(True)):  # DXF Legacy importer
                say("Legacy DXF importer [using part.makeFace]")
                edges=[]
                sorted_edges=[]
                w=[]
                
                for o in imp_objects: #doc.Objects:
                    #if o.Name not in str(objects):
                        if hasattr(o,'Shape'):
                            w1 = Part.Wire(Part.__sortEdges__(o.Shape.Edges))
                            w.append(w1)
                #print (w)
                f=Part.makeFace(w,'Part::FaceMakerBullseye')
            for o in imp_objects: #doc.Objects:
                # if o.Name not in str(objects):
                    doc.removeObject(o.Name)
            if 'Silk' in filename:
                layerName = 'Silks'
            else:
                layerName = 'Tracks'
            if 'F.Silk' in filename or 'F_Silk' in filename:
                layerName = 'top'+layerName
            elif 'B.Silk' in filename or 'B_Silk' in filename:
                layerName = 'bot'+layerName
            elif 'F.' in filename or 'F_' in filename:
                layerName = 'top'+layerName
            elif 'B.' in filename or 'B_' in filename:
                layerName = 'bot'+layerName

            doc.addObject('Part::Feature',layerName+ftname_sfx).Shape=f # +'tmp').Shape=f
            newShape=doc.ActiveObject
            # doc.recompute(None,True,True)
            botOffset = 1.6
            if 'Silk' in layerName:
                docG.getObject(newShape.Name).ShapeColor = silks_diffuse
            else:
                docG.getObject(newShape.Name).ShapeColor = brass_diffuse #copper_diffuse  #(0.78,0.56,0.11)
            pcb_name = find_pcb_name()
            # new_obj = simple_cpy(newShape,layerName+ftname_sfx)
            # doc.removeObject(newShape.Name)
            # newShape = new_obj
            if len (doc.getObjectsByLabel(pcb_name)) > 0:
                ### shifting placement to be removed if dxf is exported with drill place file origin
                newShape.Placement = doc.getObjectsByLabel(pcb_name)[0].Placement
                #botTracks.Placement = doc.Pcb.Placement
                board_geom_name='Board_Geoms'+pcb_name[pcb_name.rfind('_'):]
                if len (doc.getObjectsByLabel(board_geom_name)) > 0:
                    if use_AppPart and not use_LinkGroups:
                        doc.getObject(board_geom_name).addObject(newShape)
                    elif use_LinkGroups:
                        doc.getObject(board_geom_name).ViewObject.dropObject(newShape,None,'',[])
                if hasattr(doc.getObjectsByLabel(pcb_name)[0], 'Shape'):
                    botOffset = doc.getObjectsByLabel(pcb_name)[0].Shape.BoundBox.ZLength
                else:
                    botOffset = doc.getObjectsByLabel(pcb_name)[0].OutList[1].Shape.BoundBox.ZLength
            #elif 'bot' in layerName:
            #    newShape.Placement.Base.z-=1.6
            if 'top' in layerName:
                newShape.Placement.Base.z+=0.07
            if 'bot' in layerName:
                newShape.Placement.Base.z-=botOffset+0.07
            timeD = time.time() - t - timeP
            say("displaying time = "+str(timeD) + "s")
    FreeCADGui.SendMsgToActiveView("ViewFit")
    # doc.recompute(None,True,True)
    #docG.activeView().viewAxonometric()
    docG.activeView().viewTop()
##
def checkDXFsettings(leg=None):
    
    pgD = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft")
    dxfLI = pgD.GetBool("dxfUseLegacyImporter")
    dxfJG = pgD.GetBool("joingeometry")
    dxfCP = pgD.GetBool("dxfCreatePart")
    checkResult = True
    #FreeCAD.Console.PrintMessage (dxfLI);FreeCAD.Console.PrintMessage (dxfJG); FreeCAD.Console.PrintMessage (dxfCP)
    if not dxfLI: 
        FreeCAD.Console.PrintError('DXF Legacy Importer NOT selected A\n')
        # checkResult = False #enabling new DXFImporter also
    if dxfLI and (leg == True): # not dxfLI: enabling new DXFImporter also
        FreeCAD.Console.PrintMessage('DXF Legacy Importer selected\n')
        # checkResult = False
        return True
    if not(dxfLI) and (leg == True): # not dxfLI: enabling new DXFImporter also
        FreeCAD.Console.PrintMessage('DXF Legacy Importer NOT selected B\n')
        # checkResult = False
        return True
    if not dxfJG:
        FreeCAD.Console.PrintError('DXF Join Geometries NOT selected\n')
        checkResult = False
    if not dxfCP:
        FreeCAD.Console.PrintError('DXF Create Simple Part Shapes NOT selected\n')
        checkResult = False
    return checkResult
    
#makeFaceDXF()
