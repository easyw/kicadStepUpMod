# -*- coding: utf-8 -*-
#****************************************************************************
#*                                                                          *
#*  Kicad STEPUP (TM) (3D kicad board and models to STEP) for FreeCAD       *
#*  3D exporter for FreeCAD                                                 *
#*  Kicad STEPUP TOOLS (TM) (3D kicad board and models to STEP) for FreeCAD *
#*  Copyright (c) 2015                                                      *
#*  Maurice easyw@katamail.com                                              *
#*                                                                          *
#*  Kicad STEPUP (TM) is a TradeMark and cannot be freely usable            *
#*                                                                          *

ksu_wb_version='v 11.03.2'
global myurlKWB, ksuWBpath
myurlKWB='https://github.com/easyw/kicadStepUpMod'
global mycommitsKWB
mycommitsKWB=672 #  v11.02.7 NB all the commits must have commit message ending with _cmtnum=nnn
# cmtnum=672'
global verKSU
verKSU="12.3.1"

import FreeCAD, FreeCADGui, Part, os, sys
import re, time

if (sys.version_info > (3, 0)):  #py3
    import urllib
    from urllib import request, error #URLError, HTTPError
else:  #py2
    import urllib2
    from urllib2 import Request, urlopen, URLError, HTTPError

import ksu_locator
from kicadStepUpCMD import *


ksuWBpath = os.path.dirname(ksu_locator.__file__)
#sys.path.append(ksuWB + '/Gui')
ksuWB_icons_path =  os.path.join( ksuWBpath, 'Resources', 'icons')
ksuWB_ui_path = os.path.join( ksuWBpath, 'Resources','ui' )
ksuWB_trans_path = os.path.join( ksuWBpath, 'translations')

FreeCADGui.addLanguagePath(ksuWB_trans_path)
FreeCADGui.updateLocale()

global main_ksu_Icon
main_ksu_Icon = os.path.join( ksuWB_icons_path , 'kicad-StepUp-tools-WB.svg')

from PySide import QtGui

import hlp
header_txt="""<font color=GoldenRod><b>kicad StepUp version """+verKSU+"""</font></b><br>"""
help_t = header_txt+hlp.help_txt

#try:
#    from FreeCADGui import Workbench
#except ImportError as e:
#    FreeCAD.Console.PrintWarning("error")
# class CalendarPage:
#     def __init__(self):
#         from PySide import QtGui
#         self.form = QtGui.QCalendarWidget()
#         self.form.setWindowTitle("Calendar")
#     def saveSettings(self):
#         print ("saveSettings")
#     def loadSettings(self):
#         print ("loadSettings")

class kSU_MainPrefPage:

    def selectDirectory(self):
        from PySide import QtGui, QtCore
        selected_directory = QtGui.QFileDialog.getExistingDirectory()
        # Use the selected directory...
        print ('selected_directory:', selected_directory)

    def __init__(self, parent=None):
        from PySide import QtGui, QtCore
        import os, hlp, sys
        # os.environ["QT_ENABLE_HIGHDPI_SCALING"]   = "1"
        # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        # os.environ["QT_SCALE_FACTOR"]             = "1"
        global ksuWBpath
        def reload_lib(lib):
            if (sys.version_info > (3, 0)):
                import importlib
                importlib.reload(lib)
            else:
                reload (lib)

        print ("Created kSU Auxiliary Pref page")

        # https://stackoverflow.com/questions/71852282/qt-designer-not-playing-nicely-with-windows-display-scaling
        # https://stackoverflow.com/questions/20464814/changing-dpi-scaling-size-of-display-make-qt-applications-font-size-get-rendere

        #help_t = hlp.help_txt
        #reload_lib(hlp)
        header_txt="""<font color=GoldenRod><b>kicad StepUp version """+verKSU+"""</font></b><br>"""
        help_t = header_txt+hlp.help_txt
        self.form = QtGui.QWidget()
        #self.form.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

        # mw1 = FreeCADGui.getMainWindow()
        # print ('physical DPI',mw1.screen().physicalDotsPerInch())
        # print ('logical  DPI',mw1.screen().logicalDotsPerInch())

        print ('physical aux page',self.form.physicalDpiX())
        print ('logical  aux page',self.form.logicalDpiX())
        scaling = self.form.logicalDpiX() / self.form.physicalDpiX() # /96.0  # self is of QWidget
        print ('scaling aux page',scaling)
        # print(self.form.screen.devicePixelRatio())
        self.form.setWindowTitle("kSU 'Help Tips'")
        self.form.mainLayout = QtGui.QGridLayout(self.form)
        self.form.mainLayout.setObjectName("mainLayout")
        self.form.groupBox = QtGui.QGroupBox("KSU Help Tips", self.form)
        self.form.groupBoxLayout = QtGui.QVBoxLayout(self.form.groupBox)
        self.form.groupBoxLayout.setObjectName("groupBoxLayout")
        self.form.textEdit = QtGui.QTextBrowser(self.form.groupBox)
        self.form.textEdit.setOpenExternalLinks(True)
        self.form.textEdit.setObjectName("textEdit")
        self.form.textEdit.setText(help_t)
        self.form.groupBoxLayout.addWidget(self.form.textEdit)
        self.form.mainLayout.addWidget(self.form.groupBox, 0, 0, 1, 1)
        # Button UI
        add_button=False
        if add_button:
            self.form.btn = QtGui.QPushButton('Create Folder', self.form.verticalLayoutWidget)
            self.form.btn.setToolTip('This creates the folders.')
            self.form.btn.resize(self.form.btn.sizeHint())
            self.form.btn.move(5, 60)
            self.form.btn.clicked.connect(self.selectDirectory)
            self.form.verticalLayout.addWidget(self.form.btn)

    def saveSettings(self):
        print ("saveSettings Helper")
        import SaveSettings
        SaveSettings.update_ksuGui()

    def loadSettings(self):
        print ("loadSettings Helper")
        prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui").GetString('prefix3d_1')+'/'
        print('KISYS3DMOD assigned to: ', prefs)
        prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
        #if prefs.GetContents() is not None:
        #    for p in prefs.GetContents():
        #        print (p)
        print(FreeCAD.getUserAppDataDir())

class KiCadStepUpWB ( Workbench ):
    from TranslateUtils import translate
    global main_ksu_Icon, ksu_wb_version, myurlKWB, mycommitsKWB, verKSU
    global ksuWB_ui_path, kSU_MainPrefPage, ksuWB_icons_path
    
    "KiCadStepUp WB object"
    Icon = main_ksu_Icon
    #Icon = ":Resources/icons/kicad-StepUp-tools-WB.svg"
    MenuText = translate("KiCadStepUpWB", "KiCadStepUp")
    ToolTip = translate("KiCadStepUpWB", "KiCadStepUp workbench")
 
    def GetClassName(self):
        return "Gui::PythonWorkbench"
    
    def Initialize(self):
        import kicadStepUpCMD, sys
        global pref_page
        pref_page = True # False #True #
        import FreeCADGui
        from TranslateUtils import translate

        submenu = ['demo.kicad_pcb','d-pak.kicad_mod', 'demo-sketch.FCStd', 'demo.step',\
                   'footprint-template.FCStd', 'footprint-Edge-template.FCStd', 'footprint-template-roundrect-polylines.FCStd',\
                   'footprint-RF-antenna.FCStd', 'footprint-RF-antenna-w-solder-Mask.FCStd', 'RF-antenna-dxf.dxf', \
                   'complex-Polyline-footprint.FCStd', 'footprint-complex-arc-pads.FCStd', 'hollow-pad.FCStd', \
                   'footprint-SPU0410LR5H.FCStd','WaveguideAntenna-RF-fp.FCStd', 'Notch-RF-filter-wNT-fp.FCStd', \
                   'Microstrip-RF-filter-fp.FCStd', 'Splitter-RF-fp.FCStd', 'FH36W-11S-0.3SHW_1x11-FlatCable.FCStd', \
                   'kicadStepUp-cheat-sheet.pdf', 'kicad-3D-to-MCAD.pdf', 'Generating-a-KiCAD-footprint-and-Model-from-3D-Step-Data.pdf', \
                   'ECAD-MCAD-collaboration.pdf']
        dirs = self.ListDemos()

        #self.appendToolbar(translate("Toolbar", "ksu Tools"), ["ksuTools"])
        self.appendToolbar(translate("Toolbar", "ksu Tools"), ["ksuToolsEditPrefs","ksuTools","ksuToolsOpenBoard","ksuToolsImportFootprint",\
                           "ksuToolsExportModel","ksuToolsPushPCB","ksuToolsFootprintGen","Separator","ksuToolsAddTracks","ksuToolsAddSilks","Separator",\
                           "ksuToolsCollisions","ksuToolsImport3DStep","ksuToolsExport3DStep","ksuToolsMakeUnion",\
                           "ksuToolsMakeCompound", "ksuToolsUnion", "ksuToolsSimpleCopy", "ksuToolsDeepCopy", "ksuToolsColoredClone",\
                           "ksuToolsColoredBinder", "ksuToolsReLinkBinder", "ksuToolsCheckSolid"])
                           #, "ksuToolsPushMoved","ksuToolsSync3DModels"])
        self.appendToolbar(translate("Toolbar", "ksu Sketching"), ["ksuTools3D2D", "ksuTools2D2Sketch", "ksuTools2DtoFace",\
                           "ksuToolsLoopSelection","ksuToolsEdges2Sketch","ksuToolsMoveSketch","ksuToolsOffset2D","ksuToolsExtrude","Create_BoundBox","ksuToolsMergeSketches",\
                           "ksuToolsSimplifySketck", "ksuToolsBsplineNormalize", "ksuToolsConstrainator", "ksuToolsSkValidate", "ksuToolsDiscretize",\
                           "ksuToolsContour2Poly", "Arcs2Circles", "approximateCenter"])
                           #, "ksuToolsPushMoved","ksuToolsSync3DModels"])
        ksuTB = ["ksuToolsOpenBoard","ksuToolsPushPCB","ksuToolsPushMoved","ksuToolsSync3DModels","ksuToolsPullPCB","ksuToolsPullMoved","ksuAsm2Part",\
                 "Separator","ksuToolsGeneratePositions","ksuToolsComparePositions",\
                 "Separator","ksuToolsToggleTreeView","Separator","ksuRemoveTimeStamp","ksuRemoveSuffix","Separator","ksuToolsImportFootprint","ksuToolsFootprintGen"]
        #ksuTB.extend(["Separator","ksuToolsAligner","ksuToolsMover","ksuToolsCaliper"])
        self.appendToolbar(translate("Toolbar", "ksu PushPull"), ksuTB)
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            ksuDTB=["ksuToolsAligner","ksuToolsMover","ksuToolsCaliper", "ksuToolsAlignView","Separator","ksuToolsDefeaturingTools"]
            self.appendToolbar(translate("Toolbar", "ksu Design Tools"), ksuDTB)
        else:
            ksuDTB=["ksuToolsAlignView"]
            self.appendToolbar(translate("Toolbar", "ksu Design Tools"), ksuDTB)
        Hlp_TB = ["ksuToolsToggleTreeView", "Restore_Transparency", "ksuToolsTransparencyToggle", "ksuToolsHighlightToggle",\
                            "ksuToolsVisibilityToggle", "ksuToolsStepImportModeSTD", "ksuToolsStepImportModeComp",\
                            "ksuToolsCopyPlacement", "ksuToolsResetPlacement", "ksuToolsResetPartPlacement", "ksuToolsAddToTree",\
                            "ksuToolsRemoveFromTree", "ksuToolsRemoveSubTree", "checkSolidExpSTEP"]
        #if 'LinkView' in dir(FreeCADGui):
        #    Hlp_TB.remove("ksuToolsHighlightToggle")
        self.appendToolbar(translate("Toolbar", "ksu Show"), ["ksuToolsTurnTable", "ksuToolsExplode"])
        self.appendToolbar(translate("Toolbar", "ksu Helpers"), Hlp_TB)
        #self.appendMenu(translate("Menu", "ksu Tools"), ["ksuTools","ksuToolsEdit"])
        self.appendMenu(translate("Menu", "ksu Tools"), ["ksuTools","ksuToolsEditPrefs","ksuImpDXF","ksuOpDXF","ksuOpEzDXF"])
        self.appendMenu(translate("Menu", "ksu PushPull"), ["ksuToolsOpenBoard","ksuToolsPushPCB","ksuToolsPushMoved","ksuToolsSync3DModels","ksuToolsPullPCB","ksuToolsPullMoved",\
                        "Separator","ksuToolsGeneratePositions","ksuToolsComparePositions",\
                        "Separator","ksuRemoveTimeStamp","ksuRemoveSuffix",\
                        "Separator","ksuToolsImportFootprint","ksuToolsFootprintGen"])
        self.appendMenu([translate("Menu", "ksu Tools"), translate("Menu", "Demo")], submenu)
        
        #FreeCADGui.addPreferencePage( a2plib.pathOfModule() + '/GuiA2p/ui/a2p_prefs.ui','A2plus' )
        if pref_page:
            mw1 = FreeCADGui.getMainWindow()
            scaling = mw1.logicalDpiX() / mw1.physicalDpiX() # /96.0  # self is of QWidget
            print('main win physicalDpiX()',mw1.physicalDpiX())
            print('main win logicalDpiX()',mw1.logicalDpiX())
            if hasattr(mw1,"screen"):
                print('screen physicalDotsPerInch()',mw1.screen().physicalDotsPerInch())
                print('screen logicalDotsPerInch()' ,mw1.screen().logicalDotsPerInch())
            print('scaling main',scaling)
            # print ('physical DPI',mw1.screen().physicalDotsPerInch())
            # print ('logical  DPI',mw1.screen().logicalDotsPerInch())
            
            FreeCADGui.addPreferencePage(
                ksuWB_ui_path + '/ksu_prefs.ui',
                'kicadStepUpGui'
                )
            FreeCADGui.addPreferencePage(kSU_MainPrefPage,"kicadStepUpGui")

        FreeCADGui.addIconPath(ksuWB_icons_path)
        Log ("Loading ksuModule... done\n")
 
    def Activated(self):
                # do something here if needed...
        Msg ("KiCadStepUpWB.Activated("+ksu_wb_version+")\n")
        from PySide import QtGui
        import time, sys, os, re
        from os.path import expanduser
        import codecs #utf-8 config parser
        import FreeCAD, FreeCADGui
        import commits_num
        
        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
        tnow = int(time.time())
        oneday = 86400
        if pg.IsEmpty():
            pg.SetBool("checkUpdates",1)
            upd=True
            pg.SetInt("updateDaysInterval",1)
            pg.SetInt("lastCheck",tnow-2*oneday)
            pg.SetInt("dockingMode",0)
            interval=True
            FreeCAD.Console.PrintError('new \'check for updates\' feature added!!!\n')
            msg="""
            <font color=red>new \'check for updates\' feature added!!!</font>
            <br>
            <br>set \'checkUpdates\' to \'False\' to avoid this checking
            <br>in \"Tools\", \"Edit Parameters\",<br>\"Preferences\"->\"Mod\"->\"kicadStepUp\"
            """
            QtGui.QApplication.restoreOverrideCursor()
            reply = QtGui.QMessageBox.information(None,"Warning", msg)
        else:
            upd=pg.GetBool("checkUpdates")
        prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
        if prefs.IsEmpty():
        #if prefs.GetContents() is None:
            def mk_str(input):
                if (sys.version_info > (3, 0)):  #py3
                    if isinstance(input, str):
                        return input
                    else:
                        input =  input.encode('utf-8')
                        return input
                else:  #py2
                    if type(input) == unicode:
                        input =  input.encode('utf-8')
                        return input
                    else:
                        return input
            def mk_uni(input):
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
            ##
            FreeCAD.Console.PrintError('Creating first time ksu preferences\n')
            #prefs.SetString('prefix3d_1',make_string(default_prefix3d))
            prefs.SetInt('pcb_color',0)
            prefs.SetString('drill_size',u'0.0')
            prefs.SetBool('make_union',0)
            prefs.SetBool('exp_step',0)
            prefs.SetBool('turntable',0)
            prefs.SetBool('generate_sketch',1)
            prefs.SetBool('asm3_links',1)
            prefs.SetBool('vrml_materials',1)
            prefs.SetBool('mode_virtual',1)
            prefs.SetInt('pcb_placement',0)
            prefs.SetInt('step_exp_mode',0)
            prefs.SetInt('3D_loading_mode',0)
            prefs.SetInt('sketch_constraints',0)
            prefs.SetString('blacklist',u'')
            prefs.SetString('blacklist',u'')
            home = expanduser("~")
            fname_ksu=home+os.sep+'ksu-config.ini'
            ksu_config_fname=fname_ksu
            if os.path.isfile(ksu_config_fname): # and len (models3D_prefix) == 0:
                FreeCAD.Console.PrintMessage("ksu file \'ksu-config.ini\' exists; getting old config values\n")
                ini_vars=[]
                for i in range (0,20):
                    ini_vars.append('-')
                ini_content=[];cfg_content=[]
                #Kicad_Board_elaborated = open(filename, "r").read()[0:]
                #txtFile = __builtin__.open(ksu_config_fname,"r")
                #with io.open(ksu_config_fname,'r', encoding='utf-8') as cfg_file:
                with codecs.open(ksu_config_fname,'r', encoding='utf-8') as cfg_file:
                    cfg_content = cfg_file.readlines() #
                    #ini_content = cfg_content
                    cfg_file.close()
                for line in cfg_content:
                    if re.match(r'^\s*$', line): #empty lines
                        FreeCAD.Console.PrintMessage('line empty\n')
                    else:
                        #ini_content.append(make_unicode(line))
                        #print(line)
                        ini_content.append(line)
                def find_nm(n):
                    n=n.lower()
                    return {
                        'prefix3d_1'    : 1,
                        'prefix3d_2'    : 2,
                        'pcb_color'     : 3,
                        'bklist'        : 4,
                        'bbox'          : 5,
                        'placement'     : 6,
                        'virt'          : 7,
                        'exportfusing'  : 8,
                        'min_drill_size': 9,
                        'last_pcb_path' :10,
                        'last_fp_path'  :11,
                        'export_to_step':12,
                        'mat'           :13,
                        'spin'          :14,
                        'compound'      :15,
                        'dkmode'        :16,
                        'font_size'     :17,
                        'exporting_mode':18,
                        'importing_mode':19,
                    }.get(n, 0)    # 0 is default if x not found
                for line in ini_content:
                    line = line.strip() #removes all whitespace at the start and end, including spaces, tabs, newlines and carriage returns
                    if len(line)>0:
                        if line[0] != ';' and line[0] != '[':
                            if '=' in line:
                                data = line.split('=', 1)
                                #sayw(len(data))
                                if len(data) == 1:
                                    name = mk_uni(data[0].strip())
                                    key_value = u"" #None
                                else:
                                    name = mk_uni(data[0].strip())
                                    key_value = mk_uni(data[1].strip())
                                # sayerr(len(ini_vars))
                                # sayw(str(find_name(name))+' -> '+name+' -> '+key_value)
                                ini_vars[find_nm(name)]= key_value
                #print(ini_vars)
                models3D_prefix = ini_vars[1]
                models3D_prefix2=ini_vars[2]
                FreeCAD.Console.PrintMessage('3D models prefix='+mk_str(models3D_prefix)+'\n')
                FreeCAD.Console.PrintMessage('3D models prefix2='+mk_str(models3D_prefix2)+'\n')
                prefs.SetString('prefix3d_1',mk_str(models3D_prefix.replace('\\','/').rstrip('/')))
                prefs.SetString('prefix3d_2',mk_str(models3D_prefix2.replace('\\','/').rstrip('/')))
                #stop
            ##
            FreeCAD.Console.PrintError('new \'preferences Page\' added to configure StepUp!!!\n')
            msg="""
            <font color=red>new \'preference Page\' added to configure StepUp!!!</font>
            <br>
            <br>old method using <b>ksu-config.ini</b>
            <br><font color=red>has been DROPPED</font>.
            <br>Please have a look at the <b><a href='https://github.com/easyw/kicadStepUpMod/blob/master/demo/kicadStepUp-cheat-sheet.pdf' target='_blank'>\'KiCad StepUp tools cheat sheet\'</a></b> pdf
            """
            QtGui.QApplication.restoreOverrideCursor()
            reply = QtGui.QMessageBox.information(None,"Warning", msg)
            # FreeCADGui.showPreferences("kicadStepUpGui") it cannot launched here until InitGui has run!!!
        ##
        time_interval = pg.GetInt("updateDaysInterval")
        if time_interval <= 0:
            time_interval = 1
            pg.SetInt("updateDaysInterval",1)
        nowTimeCheck = int(time.time())
        lastTimeCheck = pg.GetInt("lastCheck")
        #print (nowTimeCheck - lastTimeCheck)/(oneday*time_interval)
        if time_interval <= 0 or ((nowTimeCheck - lastTimeCheck)/(oneday*time_interval) >= 1):
            interval = True
            pg.SetInt("lastCheck",tnow)
        else:
            interval = False
        ##
        if upd and interval:
            # check_updates(myurlMWB, mycommitsMWB)
            url=myurlKWB
            commit_nbr=mycommitsKWB
            nbr_commits=commits_num.commitCount('easyw','kicadStepUpMod')
            if int(nbr_commits) == 0:
                FreeCAD.Console.PrintWarning('We failed to get the commit numbers from github.\n')
            else:
                FreeCAD.Console.PrintMessage(url+'-> commits:'+str(nbr_commits)+'\n')
                delta = int(nbr_commits) - commit_nbr
                if delta > 0:
                    s = ""
                    if delta >1:
                        s="s"
                    FreeCAD.Console.PrintError('PLEASE UPDATE "kicadStepUp" WB.\n')
                    msg="""
                    <font color=red>PLEASE UPDATE "kicadStepUp" WB.</font>
                    <br>through \"Tools\" \"Addon manager\" Menu
                    <br><br><b>your release is """+str(delta)+""" commit"""+s+""" behind</b><br>
                    <br><a href=\""""+myurlKWB+"""\">kicadStepUp WB</a>
                    <br>
                    <br>set \'checkUpdates\' to \'False\' to avoid this checking
                    <br>in \"Tools\", \"Edit Parameters\",<br>\"Preferences\"->\"Mod\"->\"kicadStepUp\"
                    """
                    QtGui.QApplication.restoreOverrideCursor()
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                else:
                    FreeCAD.Console.PrintMessage('the WB is Up to Date\n')
                #<li class="commits">

 
    def Deactivated(self):
                # do something here if needed...
        Msg ("KiCadStepUpWB.Deactivated()\n")
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

dirs = KiCadStepUpWB.ListDemos()
#print dirs
#FreeCADGui.addCommand('ksuWBOpenDemo', ksuOpenDemo())
#dirs = KiCadStepUpWB.ListDemos()
for curFile in dirs:
    FreeCADGui.addCommand(curFile, ksuExcDemo(curFile))

#FreeCADGui.addPreferencePage(kSU_MainPrefPage,"kicadStepUpGui")
#FreeCADGui.addPreferencePage(CalendarPage, "kicadStepUpGui")
        
FreeCADGui.addWorkbench(KiCadStepUpWB)
