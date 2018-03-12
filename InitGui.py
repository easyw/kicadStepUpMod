# -*- coding: utf-8 -*-
#****************************************************************************
#*                                                                          *
#*  Kicad STEPUP (TM) (3D kicad board and models to STEP) for FreeCAD       *
#*  3D exporter for FreeCAD                                                 *
#*  Kicad STEPUP TOOLS (TM) (3D kicad board and models to STEP) for FreeCAD *
#*  Copyright (c) 2015                                                      *
#*  Maurice easyw@katamail.com                                              *
#*                                                                          *
#*  Kicad STEPUP (TM) is a TradeMark and cannot be freely useable           *
#*                                                                          *

import FreeCAD, FreeCADGui, Part, os, sys
import urllib2, re
from urllib2 import Request, urlopen, URLError, HTTPError

import ksu_locator
from kicadStepUpCMD import *

ksuWBpath = os.path.dirname(ksu_locator.__file__)
#sys.path.append(ksuWB + '/Gui')
ksuWB_icons_path =  os.path.join( ksuWBpath, 'Resources', 'icons')

global main_ksu_Icon, wb_activated
main_ksu_Icon = os.path.join( ksuWB_icons_path , 'kicad-StepUp-tools-WB.svg')
wb_activated=False

ksu_wb_version='v 7.5.1'
global myurl
myurl='https://github.com/easyw/kicadStepUpMod'
global mycommits
mycommits=57 #v7.5.1


#try:
#    from FreeCADGui import Workbench
#except ImportError as e:
#    FreeCAD.Console.PrintWarning("error")


class ksuWB ( Workbench ):
    global main_ksu_Icon, ksu_wb_version, myurl, mycommits, wb_activated
    
    "kicad StepUp WB object"
    Icon = main_ksu_Icon
    #Icon = ":Resources/icons/kicad-StepUp-tools-WB.svg"
    MenuText = "kicad StepUp WB"
    ToolTip = "kicad StepUp workbench"
 
    def GetClassName(self):
        return "Gui::PythonWorkbench"
    
    def Initialize(self):
        import kicadStepUpCMD
        submenu = ['demo.kicad_pcb','d-pak.kicad_mod', 'demo-sketch.FCStd', 'demo.step',\
                   'footprint-template.FCStd', 'footprint-Edge-template.FCStd', 'footprint-template-roundrect-polylines.FCStd',\
                   'footprint-RF-antenna.FCStd', 'footprint-RF-antenna-w-solder-Mask.FCStd', 'RF-antenna-dxf.dxf', \
                   'kicadStepUp-cheat-sheet.pdf', 'kicad-3D-to-MCAD.pdf' ]
        dirs = self.ListDemos()

        #self.appendToolbar("ksu Tools", ["ksuTools"])
        self.appendToolbar("ksu Tools", ["ksuTools","ksuToolsOpenBoard","ksuToolsLoadFootprint",\
                           "ksuToolsExportModel","ksuToolsPushPCB","ksuToolsCollisions", \
                           "ksuToolsImport3DStep","ksuToolsExport3DStep","ksuToolsMakeUnion",\
                           "ksuToolsMakeCompound", "ksuToolsSimpleCopy", "ksuToolsDeepCopy", "ksuToolsCheckSolid", "ksuTools3D2D", "ksuTools2D2Sketch", "ksuTools2DtoFace",\
                           "ksuToolsFootprintGen"])
        
        #self.appendMenu("ksu Tools", ["ksuTools","ksuToolsEdit"])
        self.appendMenu("ksu Tools", ["ksuTools"])
        self.appendMenu(["ksu Tools", "Demo"], submenu)
        
        Log ("Loading ksuModule... done\n")
 
    def Activated(self):
                # do something here if needed...
        Msg ("ksuWB.Activated("+ksu_wb_version+")\n")
        from PySide import QtGui
        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
        if pg.IsEmpty():
            pg.SetBool("checkUpdates",1)
            upd=True
        else:
            upd=pg.GetBool("checkUpdates")
        def check_updates(url, commit_nbr):
            global wb_activated
            import urllib2, re
            from urllib2 import Request, urlopen, URLError, HTTPError
            wb_activated=True
            req = Request(url)
            
            try:
                response = urlopen(req)
            except HTTPError as e:
                FreeCAD.Console.PrintWarning('The server couldn\'t fulfill the request.')
                FreeCAD.Console.PrintWarning('Error code: ' + str(e.code)+'\n')
            except URLError as e:
                FreeCAD.Console.PrintWarning('We failed to reach a server.\n')
                FreeCAD.Console.PrintWarning('Reason: '+ str(e.reason)+'\n')
            else:
                # everything is fine
                the_page = response.read()
                # print the_page
                str2='<li class=\"commits\">'
                pos=the_page.find(str2)
                str_commits=(the_page[pos:pos+600])
                # print str_commits
                pos=str_commits.find('<span class=\"num text-emphasized\">')
                commits=(str_commits[pos:pos+200])
                commits=commits.replace('<span class=\"num text-emphasized\">','')
                #commits=commits.strip(" ")
                #exp = re.compile("\s-[^\S\r\n]")
                #print exp
                #nbr_commits=''
                my_commits=re.sub('[\s+]', '', commits)
                pos=my_commits.find('</span>')
                #print my_commits
                nbr_commits=my_commits[:pos]
                nbr_commits=nbr_commits.replace(',','')
                nbr_commits=nbr_commits.replace('.','')
                
                FreeCAD.Console.PrintMessage(url+'-> commits:'+str(nbr_commits)+'\n')
                if commit_nbr < int(nbr_commits):
                    FreeCAD.Console.PrintError('PLEASE UPDATE "kicadStepUpMod" WB!!!\n')
                    msg="""
                    <font color=red>PLEASE UPDATE "kicadStepUpMod" WB!!!</font>
                    <br>through \"Tools\" \"Addon manager\" Menu
                    <br><a href=\""""+myurl+"""\">kicad StepUp WB</a>
                    <br>
                    <br>set \'checkUpdates\' to \'False\' to avoid this checking
                    <br>in \"Tools\", \"Edit Parameters\",<br>\"Preferences\"->\"Mod\"->\"kicadStepUp\"
                    """
                    QtGui.qApp.restoreOverrideCursor()
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                else:
                    FreeCAD.Console.PrintMessage('the WB is Up to Date\n')
                #<li class="commits">
        ##
        if not wb_activated and upd:
            check_updates(myurl, mycommits)
 
    def Deactivated(self):
                # do something here if needed...
        Msg ("ksuWB.Deactivated()\n")
    @staticmethod
    def ListDemos():
        import os
        import ksu_locator

        dirs = []
        # List all of the example files in an order that makes sense
        module_base_path = ksu_locator.module_path()
        demo_dir_path = os.path.join(module_base_path, 'demo')
        dirs = os.listdir(demo_dir_path)
        dirs.sort()

        return dirs
    ##

###

dirs = ksuWB.ListDemos()
#print dirs
#FreeCADGui.addCommand('ksuWBOpenDemo', ksuOpenDemo())
#dirs = ksuWB.ListDemos()
for curFile in dirs:
    FreeCADGui.addCommand(curFile, ksuExcDemo(curFile))

FreeCADGui.addWorkbench(ksuWB)


#check_updates(myurl, mycommits)