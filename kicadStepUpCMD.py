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

import FreeCAD,FreeCADGui
import FreeCAD, FreeCADGui, Part
from FreeCAD import Base
import imp, os, sys, tempfile, re
import FreeCAD, FreeCADGui, Draft, DraftGeomUtils, OpenSCAD2Dgeom
from PySide import QtGui, QtCore
from pivy import coin

import ksu_locator
# from kicadStepUptools import onLoadBoard, onLoadFootprint
import math
from math import sqrt

import constrainator
from constrainator import add_constraints, sanitizeSkBsp

__ksuCMD_version__='1.6.2'

precision = 0.1 # precision in spline or bezier conversion
q_deflection = 0.02 # quasi deflection parameter for discretization

reload_Gui=False#True

a3 = False
try:
    from freecad.asm3 import assembly as asm
    FreeCAD.Console.PrintWarning('A3 available\n')
    a3 = True
except:
    # FreeCAD.Console.PrintWarning('A3 not available\n')
    a3 = False


def reload_lib(lib):
    if (sys.version_info > (3, 0)):
        import importlib
        importlib.reload(lib)
    else:
        reload (lib)

ksuWBpath = os.path.dirname(ksu_locator.__file__)
#sys.path.append(ksuWB + '/Gui')
ksuWB_icons_path =  os.path.join( ksuWBpath, 'Resources', 'icons')

#__dir__ = os.path.dirname(__file__)
#iconPath = os.path.join( __dir__, 'Resources', 'icons' )


# class SMExtrudeCommandClass():
#   """Extrude face"""
# 
#   def GetResources(self):
#     return {'Pixmap'  : os.path.join( iconPath , 'SMExtrude.svg') , # the name of a svg file available in the resources
#             'MenuText': "Extend Face" ,
#             'ToolTip' : "Extend a face along normal"}
class Ui_CDialog(object):
    def setupUi(self, CDialog):
        CDialog.setObjectName("CDialog")
        CDialog.resize(317, 302)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Sketcher_LockAll.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        CDialog.setWindowIcon(icon)
        CDialog.setToolTip("")
        CDialog.setStatusTip("")
        CDialog.setWhatsThis("")
        self.buttonBox = QtGui.QDialogButtonBox(CDialog)
        self.buttonBox.setGeometry(QtCore.QRect(8, 255, 207, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.Label_howto = QtGui.QLabel(CDialog)
        self.Label_howto.setGeometry(QtCore.QRect(20, 5, 265, 61))
        self.Label_howto.setToolTip("Select a Sketch and Parameters\n"
"to constraint the sketch\n"
"NB the Sketch will be modified!")
        self.Label_howto.setStatusTip("")
        self.Label_howto.setWhatsThis("")
        self.Label_howto.setText("<b>Select a Sketch and Parameters to<br>constrain the sketch.<br>NB the Sketch will be modified!</b>")
        self.Label_howto.setObjectName("Label_howto")
        self.Constraints = QtGui.QGroupBox(CDialog)
        self.Constraints.setGeometry(QtCore.QRect(10, 70, 145, 166))
        self.Constraints.setToolTip("")
        self.Constraints.setStatusTip("")
        self.Constraints.setWhatsThis("")
        self.Constraints.setTitle("Constraints")
        self.Constraints.setObjectName("Constraints")
        self.verticalLayoutWidget = QtGui.QWidget(self.Constraints)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(12, 20, 125, 137))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.all_constraints = QtGui.QRadioButton(self.verticalLayoutWidget)
        self.all_constraints.setMinimumSize(QtCore.QSize(92, 64))
        self.all_constraints.setToolTip("Lock Coincident, Horizontal\n"
"and Vertical")
        self.all_constraints.setText("")
        self.all_constraints.setIcon(icon)
        self.all_constraints.setIconSize(QtCore.QSize(48, 48))
        self.all_constraints.setChecked(True)
        self.all_constraints.setObjectName("all_constraints")
        self.verticalLayout.addWidget(self.all_constraints)
        self.coincident = QtGui.QRadioButton(self.verticalLayoutWidget)
        self.coincident.setMinimumSize(QtCore.QSize(92, 64))
        self.coincident.setToolTip("Lock Coincident")
        self.coincident.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("Sketcher_LockCoincident.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.coincident.setIcon(icon1)
        self.coincident.setIconSize(QtCore.QSize(48, 48))
        self.coincident.setChecked(False)
        self.coincident.setObjectName("coincident")
        self.verticalLayout.addWidget(self.coincident)
        self.Tolerance = QtGui.QGroupBox(CDialog)
        self.Tolerance.setGeometry(QtCore.QRect(166, 70, 141, 91))
        self.Tolerance.setToolTip("")
        self.Tolerance.setStatusTip("")
        self.Tolerance.setWhatsThis("")
        self.Tolerance.setTitle("Tolerance")
        self.Tolerance.setObjectName("Tolerance")
        self.verticalLayoutWidget_2 = QtGui.QWidget(self.Tolerance)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(8, 20, 125, 57))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtGui.QLabel(self.verticalLayoutWidget_2)
        self.label.setToolTip("mm")
        self.label.setStatusTip("")
        self.label.setWhatsThis("")
        self.label.setText("tolerance in mm")
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.tolerance = QtGui.QLineEdit(self.verticalLayoutWidget_2)
        self.tolerance.setMinimumSize(QtCore.QSize(64, 22))
        self.tolerance.setMaximumSize(QtCore.QSize(64, 22))
        self.tolerance.setToolTip("Tolerance on Constraints")
        self.tolerance.setStatusTip("")
        self.tolerance.setWhatsThis("")
        self.tolerance.setInputMethodHints(QtCore.Qt.ImhPreferNumbers)
        self.tolerance.setInputMask("")
        self.tolerance.setText("0.1")
        self.tolerance.setPlaceholderText("")
        self.tolerance.setObjectName("tolerance")
        self.verticalLayout_2.addWidget(self.tolerance)
        self.rmvXGeo = QtGui.QCheckBox(CDialog)
        self.rmvXGeo.setGeometry(QtCore.QRect(170, 180, 141, 20))
        self.rmvXGeo.setToolTip("remove duplicated geometries")
        self.rmvXGeo.setStatusTip("")
        self.rmvXGeo.setText("rmv xtr geo")
        self.rmvXGeo.setObjectName("rmvXGeo")

        #self.retranslateUi(CDialog)
        ###  --------------------------------------------------------
        #self.checkBox.setText("rmv xtr geo")
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), CDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), CDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CDialog)
        
        
        myiconsize=48
        icon = QtGui.QIcon()
        myicon=os.path.join( ksuWB_icons_path , 'Sketcher_LockCoincident.svg')
        icon.addPixmap(QtGui.QPixmap(myicon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.coincident.setIcon(icon)
        self.coincident.setIconSize(QtCore.QSize(myiconsize, myiconsize))
        self.coincident.setChecked(True)
        icon1 = QtGui.QIcon()
        myicon=os.path.join( ksuWB_icons_path , 'Sketcher_LockAll.svg')
        icon1.addPixmap(QtGui.QPixmap(myicon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.all_constraints.setIcon(icon1)
        self.all_constraints.setIconSize(QtCore.QSize(myiconsize, myiconsize))
        icond = QtGui.QIcon()
        myicon=os.path.join( ksuWB_icons_path , 'Sketcher_LockAll.svg')
        icond.addPixmap(QtGui.QPixmap(myicon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        CDialog.setWindowIcon(icon)
    

        # remove question mark from the title bar
        CDialog.setWindowFlags(CDialog.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        #self.Label_howto.setText("<b>Select a Sketch and Parameters<br>to constraint the sketch<br>NB the Sketch will be modified!</b>")

    def return_strings(self):
    #   Return list of values. It need map with str (self.lineedit.text() will return QString)
        return map(str, [self.tolerance.text(), self.all_constraints.isChecked(), self.rmvXGeo.isChecked()])
        
    # @staticmethod
    # def get_data(parent=None):
    #     #dialog = Ui_CDialog()
    #     dialog = Ui_CDialog(parent)
    #     #dialog = QtGui.QDialog()
    #     dialog.exec_()
    #     return dialog.return_strings()
        
################ ------------------- end CD-ui #############################

class ksuTools:
    "ksu tools object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'kicad-StepUp-icon.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Tools" ,
                     'ToolTip' : "kicad StepUp Tools"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        import os, sys
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        reload_lib( kicadStepUptools )
        FreeCAD.Console.PrintWarning( 'active :)\n' )
        #import kicadStepUptools
 
FreeCADGui.addCommand('ksuTools',ksuTools())
##

class ksuToolsOpenBoard:
    "ksu tools Open Board object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importBoard.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Load Board" ,
                     'ToolTip' : "Load KiCad PCB Board and Parts"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.onLoadBoard()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
    
        #onPushPCB()
        #import kicadStepUptools


FreeCADGui.addCommand('ksuToolsOpenBoard',ksuToolsOpenBoard())
##

class ksuToolsLoadFootprint:
    "ksu tools Load Footprint object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importFP.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Load FootPrint" ,
                     'ToolTip' : "Load KiCad PCB FootPrint"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.onLoadFootprint()

FreeCADGui.addCommand('ksuToolsLoadFootprint',ksuToolsLoadFootprint())
##

class ksuToolsExportModel:
    "ksu tools Export Model to KiCad object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'export3DModel.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Export 3D Model" ,
                     'ToolTip' : "Export 3D Model to KiCad"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
      ##evaluate to read cfg and get materials value???
      ##or made something as in load board
        #ini_content=kicadStepUptools.cfg_read_all()
        kicadStepUptools.routineScaleVRML()
        #kicadStepUptools.Ui_DockWidget.onCfg()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools

FreeCADGui.addCommand('ksuToolsExportModel',ksuToolsExportModel())
##

class ksuToolsImport3DStep:
    "ksu tools Import 3D Step object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'add_block_y.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Import 3D Step" ,
                     'ToolTip' : "Import 3D Step Model"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.Import3DModelF()

FreeCADGui.addCommand('ksuToolsImport3DStep',ksuToolsImport3DStep())
##

class ksuToolsExport3DStep:
    "ksu tools Export 3D to Step object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'export3DStep.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Export 3D to Step" ,
                     'ToolTip' : "Export selected objects to Step Model"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.Export3DStepF()

FreeCADGui.addCommand('ksuToolsExport3DStep',ksuToolsExport3DStep())
##

class ksuToolsMakeUnion:
    "ksu tools Make a Union object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'fusion.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Make Union" ,
                     'ToolTip' : "Make a Union of selected objects"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.group_part_union()

FreeCADGui.addCommand('ksuToolsMakeUnion',ksuToolsMakeUnion())
##

class ksuToolsMakeCompound:
    "ksu tools Make a Union object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'compound.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Make Compound" ,
                     'ToolTip' : "Make a Compound of selected objects"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.group_part()

FreeCADGui.addCommand('ksuToolsMakeCompound',ksuToolsMakeCompound())
##

class ksuToolsPushPCB:
    "ksu tools Push/Pull Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_Rectangle.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Push/Pull Sketch to PCB" ,
                     'ToolTip' : "Push/Pull Sketch to/from PCB Edge"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.PushPullPCB()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools


FreeCADGui.addCommand('ksuToolsPushPCB',ksuToolsPushPCB())
##

class ksuToolsPushMoved:
    "ksu tools Push/Pull 3D moved model"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'PushMoved.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Push/Pull 3D moved model(s) to PCB" ,
                     'ToolTip' : "Push/Pull 3D moved model(s) to PCB"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.PushMoved()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools

FreeCADGui.addCommand('ksuToolsPushMoved',ksuToolsPushMoved())
##
class ksuAsm2Part:
    "ksu tools Push/Pull 3D moved model"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Assembly_To_Part.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Convert an Assembly (A3) to Part hierarchy" ,
                     'ToolTip' : "Convert an Assembly (A3) to Part hierarchy"}
 
    def IsActive(self):
        if a3:
            return True
        else:
            return False
 
    def Activated(self):
        # do something here...
        # import kicadStepUptools
        # if reload_Gui:
        #     reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        #kicadStepUptools.Asm2Part()
        #Asm2Part()
        import FreeCAD, FreeCADGui, Part
        def Asm2Part(parentObj=None,doc=None,subname=''):
            if doc is None:
                # 'doc' allows you to copy object into another document.
                # If not give, then use the current document.
                doc = FreeCAD.ActiveDocument
            if not parentObj:
                # If no object is given, then obtain selection from all opened document
                parentObj = []
                for sel in FreeCADGui.Selection.getSelectionEx('*'):
                    parentObj.append(sel.Object)
                if not parentObj:
                    return
            if isinstance(parentObj,(tuple,list)):
                if len(parentObj) == 1:
                    copy = Asm2Part(parentObj[0],doc)
                else:
                    part = doc.addObject('App::Part','Part')
                    for o in parentObj:
                        copy = Asm2Part(o,doc)
                        if copy:
                            part.addObject(copy)
                    copy = part
                if copy:
                    FreeCADGui.SendMsgToActiveView("ViewFit")
                    copy.recompute(True)
                return copy
        
            obj,matrix = parentObj.getSubObject(subname,1,FreeCAD.Matrix(),not subname)
            if not obj:
                return
            # getSubObjects() is the API for getting child of a group. It returns a list
            # of subnames, and the subname inside may contain more than one levels of
            # hierarchy. Assembly uses this API to skip hierarchy to PartGroup.
            subs = obj.getSubObjects()
            if not subs:
                # Non group object will return empty subs
                shape = Part.getShape(obj,transform=False)
                if shape.isNull():
                    return
                shape.transformShape(matrix,False,True)
                copy = doc.addObject('Part::Feature',obj.Name)
                copy.Label = obj.Label
                copy.Shape = shape
                copy.ViewObject.mapShapeColors(obj.Document)
                return copy
        
            part = doc.addObject('App::Part',obj.Name)
            part.Label = obj.Label
            part.Placement = FreeCAD.Placement(matrix)
            for sub in subs:
                sobj,parent,childName,_ = obj.resolve(sub)
                if not sobj:
                    continue
                copy = Asm2Part(obj,doc,sub)
                if not copy:
                    continue
                vis = parent.isElementVisible(childName)
                if vis < 0:
                    copy.Visibility = sobj.Visibility
                else:
                    copy.Visibility = vis>0
                part.addObject(copy)
            return part
        CopyOnNewDoc=True
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 1:
            if 'App::LinkGroup' in sel[0].Object.TypeId:
                if CopyOnNewDoc:
                    doc_base=FreeCAD.ActiveDocument
                    doc1 = FreeCAD.newDocument(doc_base.Name)
                    doc1_Name = FreeCAD.ActiveDocument.Name
                    FreeCAD.setActiveDocument(doc_base.Name)
                    #sel = FreeCADGui.Selection.getSelectionEx()
                    parentObj=[]
                    parentObj.append(sel[0].Object)
                    Asm2Part(parentObj,doc1)
                    FreeCAD.setActiveDocument(doc1_Name)
                else:
                    Asm2Part()
            else:
                FreeCAD.Console.PrintWarning("select one Assembly to convert it to Part hierarchy")
                FreeCAD.Console.PrintWarning('\n')
                msg="""<b>select one Assembly to convert it to Part hierarchy</b>"""
                msg1="Warning ..."
                QtGui.QApplication.restoreOverrideCursor()
                #RotateXYZGuiClass().setGeometry(25, 250, 500, 500)
                diag = QtGui.QMessageBox(QtGui.QMessageBox.Icon.Warning,
                                        msg1,
                                        msg)
                diag.setWindowModality(QtCore.Qt.ApplicationModal)
                diag.exec_()
        else:
            FreeCAD.Console.PrintWarning("select one Assembly to convert it to Part hierarchy")
            FreeCAD.Console.PrintWarning('\n')
            msg="""<b>select one Assembly to convert it to Part hierarchy</b>"""
            msg1="Warning ..."
            QtGui.QApplication.restoreOverrideCursor()
            #RotateXYZGuiClass().setGeometry(25, 250, 500, 500)
            diag = QtGui.QMessageBox(QtGui.QMessageBox.Icon.Warning,
                                    msg1,
                                    msg)
            diag.setWindowModality(QtCore.Qt.ApplicationModal)
            diag.exec_()

FreeCADGui.addCommand('ksuAsm2Part',ksuAsm2Part())

##
class ksuToolsSync3DModels:
    "ksu tools Push/Pull 3D moved model"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sync3Dmodels.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Sync 3D model(s) Ref & TimeStamps with PCB" ,
                     'ToolTip' : "Sync 3D model(s) Ref & TimeStamps\nof the Selected 3D model with kicad PCB"}
 
    def IsActive(self):
        #if FreeCAD.ActiveDocument == None:
        #    return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #from kicadStepUptools import onPushPCB
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.Sync3DModel()
        # ppcb=kicadStepUptools.KSUWidget
        # ppcb.onPushPCB()
 
        #onPushPCB()
        #import kicadStepUptools

FreeCADGui.addCommand('ksuToolsSync3DModels',ksuToolsSync3DModels())
##
##
class ksuToolsGeneratePositions:
    "ksu tools Generate 3D models Positions"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'File_Positions.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu tools Generate 3D models Positions" ,
                     'ToolTip' : "Generate 3D models Positions\nData for Active Document\n[MCAD Syncronize]"}
 
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        #import kicadStepUptools
        #if reload_Gui:
        #    reload_lib( kicadStepUptools )
        import exchangePositions;reload_lib(exchangePositions)
        exchangePositions.expPos()
        

FreeCADGui.addCommand('ksuToolsGeneratePositions',ksuToolsGeneratePositions())
##
class ksuToolsComparePositions:
    "ksu tools Compare 3D models Positions"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Compare_Positions.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu tools Compare 3D models Positions" ,
                     'ToolTip' : "Compare 3D models Positions\nData with the Active Document\n[MCAD Syncronize]"}
 
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        #else:
        #    return True
        #import kicadStepUptools
        return True
 
    def Activated(self):
        # do something here...
        import exchangePositions;reload_lib(exchangePositions)
        exchangePositions.cmpPos()
        

FreeCADGui.addCommand('ksuToolsComparePositions',ksuToolsComparePositions())
##
# class ksuToolsEdit:
#     "ksu tools Editor object"
#  
#     def GetResources(self):
#         return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'edit.svg') , # the name of a svg file available in the resources
#                      'MenuText': "ksu Edit parameters" ,
#                      'ToolTip' : "ksu View Config Parameters"}
#  
#     def IsActive(self):
#         return True
#  
#     def Activated(self):
#         # do something here...
#         import kicadStepUptools
#         #if not kicadStepUptools.checkInstance():
#         #    reload( kicadStepUptools )
#         if reload_Gui:
#             reload( kicadStepUptools )
#         FreeCAD.Console.PrintWarning( 'active :)\n' )
#         kicadStepUptools.view_cfg()
# 
# FreeCADGui.addCommand('ksuToolsEdit',ksuToolsEdit())
##

class ksuToolsCollisions:
    "ksu tools Check Collisions object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'collisions.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Check Collisions" ,
                     'ToolTip' : "Check Collisions and Interferences"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        import kicadStepUptools
        #if not kicadStepUptools.checkInstance():
        #    reload( kicadStepUptools )
        if reload_Gui:
            reload_lib( kicadStepUptools )
        #FreeCAD.Console.PrintWarning( 'active :)\n' )
        kicadStepUptools.routineCollisions()

FreeCADGui.addCommand('ksuToolsCollisions',ksuToolsCollisions())
##

class ksuTools3D2D:
    "ksu tools 3D to 2D object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , '3Dto2D.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu 3D to 2D" ,
                     'ToolTip' : "3D object to 2D projection"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        FreeCAD.Console.PrintMessage('projecting the selected object to a 2D shape in the document\n')
        faces = []
        objs = []
        if FreeCAD.ActiveDocument is not None:
            vec = FreeCADGui.ActiveDocument.ActiveView.getViewDirection().negative()
            sel = FreeCADGui.Selection.getSelectionEx()
            if FreeCADGui.Selection.getSelectionEx():
                for s in sel:
                    objs.append(s.Object)
                    for e in s.SubElementNames:
                        if "Face" in e:
                            faces.append(int(e[4:])-1)
                #print(objs,faces)
                ##if len(objs) == 1:
                ##    if faces:
                ##        Draft.makeShape2DView(objs[0],vec,facenumbers=faces)
                ##        #return
                for o in objs:
                    Draft.makeShape2DView(o,vec)
            else:
                reply = QtGui.QMessageBox.information(None,"Warning", "select something\nto project it to a 2D shape in the document")
                FreeCAD.Console.PrintError('select something\nto project it to a 2D shape in the document\n')
        else:
            reply = QtGui.QMessageBox.information(None,"Warning", "select something\nto project it to a 2D shape in the document")
            FreeCAD.Console.PrintError('select something\nto project it to a 2D shape in the document\n')
#

FreeCADGui.addCommand('ksuTools3D2D',ksuTools3D2D())
##
class ksuToolsTurnTable:
    "ksu tools TurnTable"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'texture_turntable.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu TurnTable" ,
                     'ToolTip' : "TurnTable"}
 
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
 
    def Activated(self):
        # do something here...
        # https://forum.freecadweb.org/viewtopic.php?f=3&t=28795
        
        ## references
        # My 2 favorite docs about coin are :
        # http://www-evasion.imag.fr/~Francois.Fa ... index.html
        # https://grey.colorado.edu/coin3d/annotated.html
        
        imgfilename = os.path.join( ksuWB_icons_path , '../textures/infinite_reflection_blur.png')
        paramGet = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View")
        #old_AutoRotation = paramGet.GetBool("UseAutoRotation")
        #print(old_AutoRotation);print(paramGet.GetBool("UseAutoRotation"))
        paramGet.SetBool("UseAutoRotation",1)
        sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
        tex = sg.getByName("myTexture")
        tc = sg.getByName("myTextCoord")
        if tex: # remove existing
            sg.removeChild(tex)
        else: # or insert a new one
            tex =  coin.SoTexture2()
            tex.setName("myTexture")
            #jpgfilename = QtGui.QFileDialog.getOpenFileName(QtGui.qApp.activeWindow(),'Open image file','*.jpg')
            #tex.filename = str(jpgfilename[0])
            #print(str(jpgfilename[0]))
            tex.filename = str(imgfilename)
            #print (str(imgfilename))
            sg.insertChild(tex,1)
            FreeCADGui.ActiveDocument.ActiveView.startAnimating(0,1,0,0.2)
        if tc:
            sg.removeChild(tc)
            FreeCADGui.ActiveDocument.ActiveView.stopAnimating()
            # uar = 0 if (old_AutoRotation) else 1
            #if (old_AutoRotation):
            #    uar = 1 
            #else:
            #    uar = 0
            #paramGet.SetBool("UseAutoRotation",uar)
            #print(old_AutoRotation);print (uar);print(paramGet.GetBool("UseAutoRotation"))
        else:
            tc = coin.SoTextureCoordinateEnvironment()
            tc.setName("myTextCoord")
            sg.insertChild(tc,2)
        

FreeCADGui.addCommand('ksuToolsTurnTable',ksuToolsTurnTable())
##

class ksuToolsConstrainator:
    "ksu tools Constraint Sketch"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_LockAll.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Constrain a Sketch" ,
                     'ToolTip' : "Fix & auto Constrain a Sketch"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        sel = FreeCADGui.Selection.getSelection()
        if len(sel)==1:    
            if sel[0].TypeId == 'Sketcher::SketchObject' and len(sel)==1:
                CDialog = QtGui.QDialog()
                ui = Ui_CDialog()
                ui.setupUi(CDialog)
                CDialog.setWindowTitle("Sketch Constrainator")
                reply=CDialog.exec_()
                if reply==1:
                    FreeCAD.ActiveDocument.openTransaction('Constrainator')
                    dialog_values = (ui.return_strings()) # window is value from edit field
                    #print (dialog_values)
                    for i,dv in enumerate (dialog_values): #py3 compatibility
                        if i == 0:
                            tol = float(dv)
                            if tol <= 0:
                                tol = 0.01
                        if i == 1:
                            if 'True' in dv:
                                constr = 'all'
                            else:
                                constr = 'coincident'
                        if i ==2:
                            if 'True' in dv:
                                rmvXG = True
                            else:
                                rmvXG = False
                    if rmvXG:
                        sanitizeSkBsp(sel[0].Name, tol)
                    add_constraints(sel[0].Name, tol, constr)
                    FreeCAD.ActiveDocument.commitTransaction()
            else:
                reply = QtGui.QMessageBox.information(None,"Warning", "select a Sketch to be Fix & Constrained")
                FreeCAD.Console.PrintError('select a Sketch to be Fix & Constrained\n')
        else:
            reply = QtGui.QMessageBox.information(None,"Warning", "select ONE Sketch to be Fix & Constrained")
            FreeCAD.Console.PrintError('select ONE Sketch to be Fix & Constrained\n')
    

FreeCADGui.addCommand('ksuToolsConstrainator',ksuToolsConstrainator())
##
class ksuToolsDiscretize:
    "ksu tools Discretize"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Discretize.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Discretize" ,
                     'ToolTip' : "Discretize a shape/outline to a Sketch"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) != 1:
            reply = QtGui.QMessageBox.information(None,"Warning", "select one single object to be discretized")
            FreeCAD.Console.PrintError('select one single object to be discretized\n')
        else:
            shapes = []
            for selobj in sel:
                for e in selobj.Shape.Edges:
                    if not hasattr(e.Curve,'Radius'):
                    #if not e.Closed:  # Arc and not Circle
                        shapes.append(Part.makePolygon(e.discretize(QuasiDeflection=q_deflection)))
                    else:
                        shapes.append(Part.Wire(e))
                    #sd=e.copy().discretize(QuasiDeflection=dqd)    
            sk_d=Draft.makeSketch(shapes)
            max_geo_admitted = 1500 # after this number, no recompute is applied
            if len (sk_d.Geometry) < max_geo_admitted:
                FreeCAD.ActiveDocument.recompute()

FreeCADGui.addCommand('ksuToolsDiscretize',ksuToolsDiscretize())
##
##
class ksuToolsResetPlacement:
    "ksu tools Reset Placement"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'resetPlacement.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Reset Placement" ,
                     'ToolTip' : "Reset Placement for a Shape"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) != 1:
            reply = QtGui.QMessageBox.information(None,"Warning", "select one single object to Reset its Placement")
            FreeCAD.Console.PrintError('select one single object to Reset its Placement\n')
        else:
            import kicadStepUptools
            kicadStepUptools.routineResetPlacement(keepWB=True)

FreeCADGui.addCommand('ksuToolsResetPlacement',ksuToolsResetPlacement())
##

#####
class ksuTools2D2Sketch:
    "ksu tools 2D to Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , '2DtoSketch.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu 2D to Sketch" ,
                     'ToolTip' : "2D object (or DXF) to Sketch"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            max_geo_admitted = 1500 # after this number, no recompute is applied
            try:
                edges=sum((obj.Shape.Edges for obj in \
                FreeCADGui.Selection.getSelection() if hasattr(obj,'Shape')),[])
                #for edge in edges:
                #    print "geomType ",DraftGeomUtils.geomType(edge)
                ##face = OpenSCAD2Dgeom.edgestofaces(edges)
                import kicadStepUptools
                if reload_Gui:
                    reload_lib( kicadStepUptools )
                #face = OpenSCAD2DgeomMau.edgestofaces(edges)
                FC_majorV=int(float(FreeCAD.Version()[0]))
                FC_minorV=int(float(FreeCAD.Version()[1]))
                using_draft_makeSketch=True
                faceobj=None
                if not using_draft_makeSketch or (FC_majorV==0 and FC_minorV<=16):
                    try:
                        faceobj=None
                        face = kicadStepUptools.OSCD2Dg_edgestofaces(edges,3 , kicadStepUptools.edge_tolerance)
                        face.check() # reports errors
                        face.fix(0,0,0)
                        faceobj = FreeCAD.ActiveDocument.addObject('Part::Feature',"Face")
                        faceobj.Label = "Face"
                        faceobj.Shape = face
                        for obj in FreeCADGui.Selection.getSelection():
                            FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                        FreeCAD.ActiveDocument.recompute()
                        wires,_faces = Draft.downgrade(faceobj,delete=True)
                    except:
                        import Draft
                        if faceobj is not None:
                            FreeCAD.ActiveDocument.removeObject(faceobj.Name)
                        sk = None
                        sk = Draft.makeSketch(FreeCADGui.Selection.getSelection(),autoconstraints=True)
                        if sk is None:
                            reply = QtGui.QMessageBox.information(None,"Warning", "Select edge elements to be converted to Sketch\nBSplines and Bezier curves are not supported by this tool")
                            FreeCAD.Console.PrintWarning("Select edge elements to be converted to Sketch\nBSplines and Bezier curves are not supported by this tool\n")
                            stop
                        sk.Label = "Sketch_converted"
                        sname=FreeCAD.ActiveDocument.ActiveObject.Name
                        using_draft_makeSketch=True
                        for obj in FreeCADGui.Selection.getSelection():
                            FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                    
                    if FC_majorV==0 and FC_minorV>=16:
                        try:
                            sketch = Draft.makeSketch(wires[0:1])
                            sketch.Label = "Sketch_converted"
                            for wire in wires[1:]:
                                Draft.makeSketch([wire],addTo=sketch)
                            sname=FreeCAD.ActiveDocument.ActiveObject.Name
                        except:
                            sname=FreeCAD.ActiveDocument.ActiveObject.Name
                            FreeCAD.ActiveDocument.removeObject(sname)
                            reply = QtGui.QMessageBox.information(None,"Error", "BSplines not supported in FC0.16\nUse FC0.17")
                        #sname=FreeCAD.ActiveDocument.ActiveObject.Name
                        for wire in wires:
                            FreeCAD.ActiveDocument.removeObject(wire.Name)
                    #FreeCAD.Console.PrintWarning("\nConverting Bezier curves to Arcs\n")                                
                    #wires,_faces = Draft.downgrade(faceobj,delete=True)
                ##elif using_draft_makeSketch == False:
                    newShapeList = []
                    newShapes = []
                    found_BCurve=False
                    newBSlEdges = []
                    #stop
                    for wire in wires:
                        for e in wire.Shape.Edges:
                            if DraftGeomUtils.geomType(e) == "BSplineCurve":
                                #print 'found BSpline'
                                found_BCurve=True
                                newBSlEdges.append(e)
                            elif DraftGeomUtils.geomType(e) == "BezierCurve":
                                #print 'found BezierCurve'
                                found_BCurve=True
                                edges = []
                                newspline = e.Curve.toBSpline()
                                arcs = newspline.toBiArcs(precision)
                                for i in arcs:
                                    edges.append(Part.Edge(i))
                                w = Part.Wire([Part.Edge(i) for i in edges])
                                Part.show(w)
                                w_name=FreeCAD.ActiveDocument.ActiveObject.Name
                                newShapeList.append(w_name)
                                wn=FreeCAD.ActiveDocument.getObject(w_name)
                                newShapes.append(wn)
                            else:
                                #print 'found STD Geom'
                                w = Part.Wire(e)
                                Part.show(w)
                                newShapes.append(w)
                                w_name = FreeCAD.ActiveDocument.ActiveObject.Name
                                newShapeList.append(w_name)
                                
                    #stop
                    #print newShapes
                    if len(newShapes)>0:  #at least a STD geometry exists
                        sketch = Draft.makeSketch(newShapes[0])
                        FreeCAD.ActiveDocument.ActiveObject.Label="Sketch_conv"
                        sname=FreeCAD.ActiveDocument.ActiveObject.Name
                
                        if len(newShapes)>1:  #at least a STD geometry exists
                            for w in newShapes[1:]:
                                Draft.makeSketch([w],addTo=sketch)
                            FreeCAD.ActiveDocument.recompute()
                        for e in newBSlEdges:
                            # sk = FreeCAD.ActiveDocument.addObject('Sketcher::SketchObject','Sketch_bsp')
                            # sk.addGeometry(e.Curve, False)
                            sketch.addGeometry(e.Curve, False)
                            # Sketcher magic fonction :
                        for i in range(0, len(sketch.Geometry)):
                            try: 
                                if 'BSpline' in str(sketch.Geometry[i]):
                                    sketch.exposeInternalGeometry(i)
                            except:
                                #print 'error'
                                pass
                        FreeCAD.ActiveDocument.recompute()
                        FreeCAD.ActiveDocument.getObject(sname).Label="Sketch_converted"
                        #Draft.makeSketch([w])    
                    elif FC_majorV==0 and FC_minorV>=16:
                        if len (newBSlEdges)>0:
                            sketch = FreeCAD.activeDocument().addObject('Sketcher::SketchObject','Sketch_conv')
                            sname = sketch.Name
                            FreeCAD.ActiveDocument.getObject(sname).Label="Sketch_converted"
                            for e in newBSlEdges:
                                # sk = FreeCAD.ActiveDocument.addObject('Sketcher::SketchObject','Sketch_bsp')
                                # sk.addGeometry(e.Curve, False)
                                sketch.addGeometry(e.Curve, False)
                                # Sketcher magic fonction :
                                for i in range(0, len(sketch.Geometry)):
                                    try: 
                                        if 'BSpline' in str(sketch.Geometry[i]):
                                            sketch.exposeInternalGeometry(i)
                                    except:
                                        #print 'error'
                                        pass
                                FreeCAD.ActiveDocument.recompute()                        
                    for wire in wires:
                        FreeCAD.ActiveDocument.removeObject(wire.Name)
                    for wnm in newShapeList:
                        FreeCAD.ActiveDocument.removeObject(wnm)
                    FreeCAD.ActiveDocument.recompute()
                else:
                    import Draft
                    if faceobj is not None:
                        FreeCAD.ActiveDocument.removeObject(faceobj.Name)
                    sk = None
                    sk = Draft.makeSketch(FreeCADGui.Selection.getSelection(),autoconstraints=True)
                    if sk is None:
                        reply = QtGui.QMessageBox.information(None,"Warning", "Select edge elements to be converted to Sketch")
                        FreeCAD.Console.PrintWarning("Select edge elements to be converted to Sketch\n")
                        stop
                    sk.Label = "Sketch_converted"
                    sname=FreeCAD.ActiveDocument.ActiveObject.Name
                    for i,g in enumerate (sk.Geometry):
                        if 'BSplineCurve object' in str(g):
                            sk.exposeInternalGeometry(i)
                    using_draft_makeSketch=True
                    for obj in FreeCADGui.Selection.getSelection():
                        FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                    if len (sk.Geometry) < max_geo_admitted:
                        FreeCAD.ActiveDocument.recompute()
            except Part.OCCError: # Exception: #
                FreeCAD.Console.PrintError('Error in source %s (%s)' % (faceobj.Name,faceobj.Label)+"\n")
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select elements to be converted to Sketch")
            FreeCAD.Console.PrintWarning("Select elements to be converted to Sketch\n")             
        
        pass
#
FreeCADGui.addCommand('ksuTools2D2Sketch',ksuTools2D2Sketch())

#####
class ksuTools2DtoFace:
    "ksu tools 2D to Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , '2DtoFace.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu 2D to Face" ,
                     'ToolTip' : "2D object (or DXF) to Surface for extruding"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            try:
                edges=sum((obj.Shape.Edges for obj in \
                FreeCADGui.Selection.getSelection() if hasattr(obj,'Shape')),[])
                #for edge in edges:
                #    print "geomType ",DraftGeomUtils.geomType(edge)
                import kicadStepUptools
                if reload_Gui:
                    reload_lib( kicadStepUptools )
                face = kicadStepUptools.OSCD2Dg_edgestofaces(edges,3 , kicadStepUptools.edge_tolerance)
                ##face = OpenSCAD2Dgeom.edgestofaces(edges)
                #face = OpenSCAD2DgeomMau.edgestofaces(edges)
                face.check() # reports errors
                face.fix(0,0,0)
                faceobj = FreeCAD.ActiveDocument.addObject('Part::Feature',"Face")
                faceobj.Label = "Face"
                faceobj.Shape = face
                for obj in FreeCADGui.Selection.getSelection():
                    FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                FreeCAD.ActiveDocument.recompute()
                pass
            except Part.OCCError: # Exception: #
                FreeCAD.Console.PrintError('Error in source %s (%s)' % (faceobj.Name,faceobj.Label)+"\n")
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select elements to be converted to Face")
            FreeCAD.Console.PrintWarning("Select elements to be converted to Face\n")             

FreeCADGui.addCommand('ksuTools2DtoFace',ksuTools2DtoFace())

#####

class ksuToolsSimplifySketck:
    "ksu tools Simplify Sketch object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'SimplifySketch.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Simplify Sketch" ,
                     'ToolTip' : "Simplifying Sketch to Arcs and Lines"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if len(FreeCADGui.Selection.getSelection()):
            import kicadStepUptools
            if reload_Gui:
                reload_lib( kicadStepUptools )
            FreeCAD.Gui.activeDocument().activeView().viewTop()
            kicadStepUptools.simplify_sketch()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select ONE Sketch to be Simplified")
            FreeCAD.Console.PrintWarning("Select ONE Sketch to be Simplified\n")             

FreeCADGui.addCommand('ksuToolsSimplifySketck',ksuToolsSimplifySketck())
#####

class ksuToolsBsplineNormalize:
    "ksu tools Normalize Bspline for KiCAD format"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_BSplineNormalize.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Geo to Bspline" ,
                     'ToolTip' : "Convert Geometry to Bspline for KiCAD format"}
 
    def IsActive(self):
        return True
        #return False
 
    def Activated(self):
        # do something here...
        if len(FreeCADGui.Selection.getSelection()):
            import kicadStepUptools
            if reload_Gui:
                reload_lib( kicadStepUptools )
            kicadStepUptools.normalize_bsplines()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select ONE Sketch to be Normalized")
            FreeCAD.Console.PrintWarning("Select ONE Sketch to be Normalized\n")             

FreeCADGui.addCommand('ksuToolsBsplineNormalize',ksuToolsBsplineNormalize())

#####
class ksuToolsFootprintGen:
    "ksu tools Footprint generator object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'exportFootprint.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Footprint generator" ,
                     'ToolTip' : "Footprint editor and exporter"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            #for edge in edges:
            #    print "geomType ",DraftGeomUtils.geomType(edge)
            import kicadStepUptools
            if reload_Gui:
                reload_lib( kicadStepUptools )
            kicadStepUptools.PushFootprint()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select Group or Sketch/Text elements to be converted to KiCad Footprint")
            FreeCAD.Console.PrintWarning("Select Group or Sketch/Text elements to be converted to KiCad Footprint\n")             

FreeCADGui.addCommand('ksuToolsFootprintGen',ksuToolsFootprintGen())

#####

class ksuToolsStepImportModeSTD:
    "ksu tools full STEP Import Mode"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'ImportModeSTD.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu tools disable Full STEP Import Mode" ,
                     'ToolTip' : "ksu tools disable Full STEP Import Mode"}
 
    def IsActive(self):
        paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
        if not ReadShapeCompoundMode_status:
            return True
        else:
            return False

    def Activated(self):
        # do something here...
        ##ReadShapeCompoundMode
        paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
        #sayerr("checking ReadShapeCompoundMode")
        FreeCAD.Console.PrintWarning("ReadShapeCompoundMode status "+str(ReadShapeCompoundMode_status)+'\n')
        #if ReadShapeCompoundMode_status:
        #    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        #    paramGetVS.SetBool("ReadShapeCompoundMode",False)
        #    FreeCAD.Console.PrintWarning("disabling ReadShapeCompoundMode"+'\n')
        if not ReadShapeCompoundMode_status:
            paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
            paramGetVS.SetBool("ReadShapeCompoundMode",True)
            FreeCAD.Console.PrintError("enabling ReadShapeCompoundMode -> Simplified Mode"+'\n')

FreeCADGui.addCommand('ksuToolsStepImportModeSTD',ksuToolsStepImportModeSTD())
####

class ksuToolsStepImportModeComp:
    "ksu tools disable Simplified STEP Import Mode"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'ImportModeSimplified.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu tools disable Simplified STEP Import Mode" ,
                     'ToolTip' : "ksu tools disable Simplified STEP Import Mode"}
 
    def IsActive(self):
        paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
        if ReadShapeCompoundMode_status:
            return True
        else:
            return False

    def Activated(self):
        # do something here...
        ##ReadShapeCompoundMode
        paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
        #sayerr("checking ReadShapeCompoundMode")
        FreeCAD.Console.PrintWarning("ReadShapeCompoundMode status "+str(ReadShapeCompoundMode_status)+'\n')
        if ReadShapeCompoundMode_status:
            paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
            paramGetVS.SetBool("ReadShapeCompoundMode",False)
            FreeCAD.Console.PrintWarning("disabling ReadShapeCompoundMode"+'\n')
        #if not ReadShapeCompoundMode_status:
        #    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
        #    paramGetVS.SetBool("ReadShapeCompoundMode",True)
        #    FreeCAD.Console.PrintError("enabling ReadShapeCompoundMode -> Simplified Mode"+'\n')

FreeCADGui.addCommand('ksuToolsStepImportModeComp',ksuToolsStepImportModeComp())

####
class ksuToolsCopyPlacement:
    "ksu tools Copy Placement"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Placement_Copy.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu tools Copy Placement 1st to 2nd" ,
                     'ToolTip' : "ksu tools Copy Placement 1st to 2nd"}
 
    def IsActive(self):
        return True

    def Activated(self):
        # do something here...
        def copy_placement(sel):
            if hasattr(sel[0],'Placement'):
                main_p=sel[0].Placement
            else:
                FreeCAD.Console.PrintWarning("select TWO objects to copy \'1st placement\' to \'2nd placement\'\n")
                return
            for o in sel:
                if hasattr(o,'Placement'):
                    o.Placement=main_p
        
        doc = FreeCADGui.ActiveDocument
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("Select at least two objects!\n")
            FreeCAD.Console.PrintMessage("all selected objects will receive first object placement\n")
        elif len(sel)<2:
            FreeCAD.Console.PrintWarning("Select at least two objects!\n")
            FreeCAD.Console.PrintMessage("all selected objects will receive first object placement\n")
        else:
            doc = FreeCAD.ActiveDocument
            doc.openTransaction("cpyPlacement")
            copy_placement(FreeCADGui.Selection.getSelection())
            doc.commitTransaction()
            FreeCAD.Console.PrintMessage("Placement copied\n")

FreeCADGui.addCommand('ksuToolsCopyPlacement',ksuToolsCopyPlacement())

####
class ksuToolsSimpleCopy:
    "ksu tools Simple Copy object"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'simple_copy.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Simple Copy" ,
                     'ToolTip' : "Simple Copy object"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
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
            ##
            if len(sel)<1:
                    msg="Select at least one object with Shape to be copied!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            elif (sel[0].TypeId != 'PartDesign::Body'):
                for obj_tocopy in sel:
                #obj_tocopy=sel[0]
                    cp_label=mk_str(obj_tocopy.Label)+u'_sc'
                    if hasattr(FreeCAD.ActiveDocument.getObject(obj_tocopy.Name), "Shape"):
                        FreeCAD.ActiveDocument.addObject('Part::Feature',cp_label).Shape=FreeCAD.ActiveDocument.getObject(obj_tocopy.Name).Shape
                        FreeCAD.ActiveDocument.ActiveObject.Label=cp_label
                        FreeCADGui.ActiveDocument.ActiveObject.ShapeColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).ShapeColor
                        FreeCADGui.ActiveDocument.ActiveObject.LineColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).LineColor
                        FreeCADGui.ActiveDocument.ActiveObject.PointColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).PointColor
                        FreeCADGui.ActiveDocument.ActiveObject.DiffuseColor=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).DiffuseColor
                        FreeCADGui.ActiveDocument.ActiveObject.Transparency=FreeCADGui.ActiveDocument.getObject(obj_tocopy.Name).Transparency
                        FreeCAD.ActiveDocument.recompute()
                    #else:
                    #    FreeCAD.Console.PrintWarning("Select object with a \"Shape\" to be copied!\n")             
            else:
                #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
                reply = QtGui.QMessageBox.information(None,"Warning", "Select at least one object with Shape to be copied!\nBody PDN not allowed.")
                FreeCAD.Console.PrintWarning("Select at least one object with Shape to be copied!\nBody PDN not allowed.")             
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select at least one object with Shape to be copied!")
            FreeCAD.Console.PrintWarning("Select at least one object with Shape to be copied!\n")             

FreeCADGui.addCommand('ksuToolsSimpleCopy',ksuToolsSimpleCopy())

#####
class ksuToolsDeepCopy:
    "ksu tools PartDN Copy object"

    __Name__ = 'Deep Copy'
    __Help__ = 'Select a part and launch'
    __Author__ = 'galou_breizh'

###
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'deep_copy.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu PartDN Copy" ,
                     'ToolTip' : "PartDN Copy object\nwith relative placement\n[flattened model]"}
 
    def IsActive(self):
        if int(float(FreeCAD.Version()[0]))==0 and int(float(FreeCAD.Version()[1]))<=16: #active only for FC>0.16
            return False
        else:
            return True
 
    def Activated(self):
        # do something here...

        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()        
            if len(sel)!=1 and (sel[0].TypeId == 'App::Part' or sel[0].TypeId == 'PartDesign::Body'):
                msg="Select ONE Part Design Next object\nor one or more objects to be copied!\n"
                reply = QtGui.QMessageBox.information(None,"Warning", msg)
                FreeCAD.Console.PrintWarning(msg)             
            else:
                doc = FreeCAD.activeDocument()
                if sel[0].TypeId != 'App::Part' and sel[0].TypeId != 'PartDesign::Body':
                    for o in sel:
                        if o.TypeId != 'App::Part' and o.TypeId != 'PartDesign::Body':
                            copy_subobject(doc,o,'copy')
                else:
                    deep_copy(doc,'flat','copy')
                    FreeCADGui.ActiveDocument.getObject(sel[0].Name).Visibility=False
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select ONE Part Design Next object\nor one or more objects to be copied!")
            FreeCAD.Console.PrintWarning("Select ONE Part Design Next object\nor one or more objects to be copied!\n")             
        
FreeCADGui.addCommand('ksuToolsDeepCopy',ksuToolsDeepCopy())
#####
def mk_str_u(input):
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
###
make_compound = False

# import FreeCAD as app,FreeCADGui as gui

# from FreeCAD import app
# from FreeCAD import gui


def deep_copy(doc,compound='flat',suffix='(copy)'):
    #FreeCAD.Console.PrintMessage(compound)
    for sel_object in FreeCADGui.Selection.getSelectionEx():
        pName=deep_copy_part(doc, sel_object.Object, compound,suffix)
    return pName

def deep_copy_part(doc, part, compound='flat',suffix='(copy)'):
    if part.TypeId != 'App::Part' and part.TypeId != 'PartDesign::Body':
        # Part is not a part, return.
        return
    
    #FreeCAD.Console.PrintWarning(compound)
    make_compound=compound
    copied_subobjects = []
    copied_subobjects_Names = []
    #print (get_all_subobjects(part))
    for o in get_all_subobjects(part):
        if o.Name not in copied_subobjects_Names:
            if FreeCADGui.ActiveDocument.getObject(o.Name).Visibility:
                vis=True
                for Container in o.InListRecursive:
                    if not (FreeCADGui.ActiveDocument.getObject(Container.Name).Visibility):
                        vis=False
                if vis:
                    copied_subobjects_Names.append(o.Name)
                    copied_subobjects += copy_subobject(doc, o,suffix)
                    copied_subobjects_Names.append(o.Name)
    if doc.ActiveObject is not None:
        pName = doc.ActiveObject.Name
    else:
        pName= 'None'
    
    if make_compound=='compound':
        compound = doc.addObject('Part::Compound', mk_str_u(part.Label)+suffix)
        compound.Links = copied_subobjects
        pName = doc.ActiveObject.Name
    elif make_compound=='part':
        doc.addObject('App::Part',mk_str_u(part.Label)+'_')
        #FreeCAD.Console.PrintMessage(doc.ActiveObject.Label)
        actobj=doc.ActiveObject
        for uplvlobj in actobj.InListRecursive:
            if uplvlobj.TypeId=='App::Part':
                pName=uplvlobj.Name
        #pName=doc.ActiveObject.Name
        for obj in copied_subobjects:
            #doc.getObject(pName).addObject(doc.getObject(obj.Name))
            #FreeCAD.Console.PrintMessage(doc.getObject(pName))
            #FreeCAD.Console.PrintMessage(doc.getObject(obj.Name))
            doc.getObject(pName).addObject(doc.getObject(obj.Name))
        #FreeCAD.Console.PrintMessage(doc.ActiveObject.Label)
    doc.recompute()
    return pName

def get_all_subobjects(o):
    """Recursively get all subobjects
    
    Subobjects of objects having a Shape attribute are not included otherwise each
    single feature of the object would be copied. The result is that bodies,
    compounds, and the result of boolean operations will be converted into a
    simple copy of their shape.
    """
    # Depth-first search algorithm.
    discovered = []
    # We do not need an extra copy for stack because OutList is already a copy.
    stack = o.OutList
    while stack:
        v = stack.pop(0)
        if v not in discovered:
            discovered.append(v)
            if not hasattr(v, 'Shape'):
                stack += v.OutList
    return discovered


    
def get_all_subobjects_old(o):
    """Recursively get all subobjects
    
    Subobjects of objects having a Shape attribute are not included otherwise each
    single feature of the object would be copied. The result is that bodies,
    compounds, and the result of boolean operations will be converted into a
    simple copy of their shape.
    """
    if hasattr(o, 'Shape'):
        return []
    # With the assumption that the attribute InList is ordered, only add the
    # subobject if o is the direct parent, i.e. the first in InList.
    l = [so for so in o.OutList if so.InList and so.InList[0] is o]
    for subobject in l:
        l += get_all_subobjects(subobject)
    return l


def copy_subobject(doc, o,suffix='(copy)'):
    copied_object = []
    if not hasattr(o, 'Shape') or o.TypeId == 'Sketcher::SketchObject' or o.Shape.isNull():
        return copied_object
    vo_o = o.ViewObject
    try:
        copy = doc.addObject('Part::Feature', o.Name + '_Shape')
        copy.Shape = o.Shape
        #copy.Label = 'Copy of ' + o.Label
        if suffix=='_':
            copy.Label = mk_str_u(o.Label)+suffix
        else:
            copy.Label = mk_str_u(o.Label)+'.'+suffix
        #copy.Placement = get_recursive_inverse_placement(o).inverse()
        copy.Placement = o.getGlobalPlacement()

        vo_copy = copy.ViewObject
        vo_copy.ShapeColor = vo_o.ShapeColor
        vo_copy.LineColor = vo_o.LineColor
        vo_copy.PointColor = vo_o.PointColor
        vo_copy.DiffuseColor = vo_o.DiffuseColor
        vo_copy.Transparency = vo_o.Transparency
    except AttributeError:
        pass
    else:
        copied_object = [copy]
    return copied_object

def get_recursive_inverse_placement(o):
    # We browse the parent in reverse order so we have to multipy the inverse
    # placements and return the inverse placement.
    # Note that we cannot rely on o.InListRecursive because the order there is
    # not reliable.
    # TODO: see if this cannot be replaced with o.getGlobalPlacement().
    p = o.Placement.inverse()
    parent = o.getParentGeoFeatureGroup()
    if parent:
        p = p.multiply(get_recursive_inverse_placement(parent))
    return p
##
def toggle_highlight_subtree(objs):
    def addsubobjs(obj,totoggleset):
        totoggle.add(obj)
        for subobj in obj.OutList:
            addsubobjs(subobj,totoggleset)

    import FreeCAD
    totoggle=set()
    for obj in objs:
        addsubobjs(obj,totoggle)
    checkinlistcomplete =False
    while not checkinlistcomplete:
        for obj in totoggle:
            if (obj not in objs) and (frozenset(obj.InList) - totoggle):
                totoggle.toggle(obj)
                break
        else:
            checkinlistcomplete = True
    obj_tree=objs[1:len(objs)]
    for obj in totoggle:
        if 'Compound' not in FreeCADGui.ActiveDocument.getObject(obj.Name).TypeId: # and 'App::Part' not in Gui.ActiveDocument.getObject(obj.Name).TypeId:
            if 'Part' in obj.TypeId:
                if obj not in obj_tree:
                    FreeCADGui.Selection.addSelection(obj)
                else:
                    FreeCADGui.Selection.removeSelection(obj)
        else:
            if hide_compound==True:
                FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False

#####
def toggle_visibility_subtree(objs):
    def addsubobjs(obj,totoggleset):
        totoggle.add(obj)
        for subobj in obj.OutList:
            addsubobjs(subobj,totoggleset)

    import FreeCAD
    totoggle=set()
    for obj in objs:
        addsubobjs(obj,totoggle)
    checkinlistcomplete =False
    while not checkinlistcomplete:
        for obj in totoggle:
            if (obj not in objs) and (frozenset(obj.InList) - totoggle):
                totoggle.toggle(obj)
                break
        else:
            checkinlistcomplete = True
    for obj in totoggle:
        if 'Compound' not in FreeCADGui.ActiveDocument.getObject(obj.Name).TypeId:
            if 'Part' in obj.TypeId or 'Sketch' in obj.TypeId:
            #if 'Part::Feature' in obj.TypeId or 'App::Part' in obj.TypeId:
                #if obj.Visibility==True:
                if FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility==True:
                    #obj.Document.getObject(obj.Name).Visibility=False
                    FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False
                else:
                    FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=True
        else:
            if hide_compound==True:
                FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility=False

#####
class ksuToolsRemoveFromTree:
    "ksu tools Remove from Tree"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'TreeItemOutMinus.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu tools Remove from Tree" ,
                     'ToolTip' : "Remove Object(s) from Container Tree\nkeeping Placement\nFirst Selection is the Container"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            doc=FreeCAD.ActiveDocument
            if "App::Part" in doc.getObject(sel[0].Name).TypeId:
                base=doc.getObject(sel[0].Name)
                for o in sel:
                    if o.Name != sel[0].Name:
                        #o_glob_plac = o.getGlobalPlacement()
                        if hasattr(base, "OutList"):
                            if o in base.OutList:
                                base.removeObject(o)
                            else:
                                for item in base.OutListRecursive:
                                    if hasattr(item, "OutList"):
                                        if o in item.OutList:
                                            item.removeObject(o)
                                            o.Placement = item.Placement.multiply(o.Placement)
                        #o.Placement = o_glob_plac
                        o.Placement = base.Placement.multiply(o.Placement)
                        for item in base.InListRecursive:
                            #fcc_prn(item.Label)
                            if item.TypeId == 'App::Part' or item.TypeId == 'PartDesign::Body':
                                doc.getObject(item.Name).addObject(doc.getObject(o.Name))                
            else:
                #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
                reply = QtGui.QMessageBox.information(None,"Warning", "Select one Container and some object(s) to be Removed from the Tree.")
                FreeCAD.Console.PrintWarning("Select one Container and some object(s) to be Removed from the Tree.\n")
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one Container and some object(s) to be Removed from the Tree.")
            FreeCAD.Console.PrintWarning("Select one Container and some object(s) to be Removed from the Tree.\n")
                
FreeCADGui.addCommand('ksuToolsRemoveFromTree',ksuToolsRemoveFromTree())

#####
class ksuToolsAddToTree:
    "ksu tools Add to Tree"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'TreeItemInPlus.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu tools Add to Tree" ,
                     'ToolTip' : "Add Object(s) to Container Tree\nkeeping Placement\nFirst Selection is the Container"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            doc=FreeCAD.ActiveDocument
            if "App::Part" in doc.getObject(sel[0].Name).TypeId:
                base=doc.getObject(sel[0].Name)
                for o in sel:
                    if o.Name != sel[0].Name:
                        if hasattr(base, "OutList"):
                            for item in base.InListRecursive:
                                if item.TypeId == 'App::Part' or item.TypeId == 'PartDesign::Body':
                                    o.Placement = item.Placement.inverse().multiply(o.Placement)
                                    #s=o.Shape.copy()
                                    #Part.show(s)
                        o.Placement = base.Placement.inverse().multiply(o.Placement)
                        #s1=o.Shape.copy()
                        #Part.show(s1)
                        doc.getObject(sel[0].Name).addObject(doc.getObject(o.Name))
            else:
                #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
                reply = QtGui.QMessageBox.information(None,"Warning", "Select one Container and some object(s) to be Added to the Tree.")
                FreeCAD.Console.PrintWarning("Select one Container and some object(s) to be Added to the Tree.\n")
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one Container and some object(s) to be Added to the Tree.")
            FreeCAD.Console.PrintWarning("Select one Container and some object(s) to be Added to the Tree.\n")
        
FreeCADGui.addCommand('ksuToolsAddToTree',ksuToolsAddToTree())

#####
def toggle_transparency_subtree(objs):
    def addsubobjs(obj,totoggleset):
        totoggle.add(obj)
        for subobj in obj.OutList:
            addsubobjs(subobj,totoggleset)

    import FreeCAD
    doc=FreeCADGui.ActiveDocument
    totoggle=set()
    for obj in objs:
        addsubobjs(obj,totoggle)
    checkinlistcomplete =False
    while not checkinlistcomplete:
        for obj in totoggle:
            if (obj not in objs) and (frozenset(obj.InList) - totoggle):
                try:
                    totoggle.toggle(obj)
                    break
                except:
                    FreeCAD.Console.PrintWarning('totoggle not allowed\n')
        else:
            checkinlistcomplete = True
    for obj in totoggle:
        #if 'App::Part' not in obj.TypeId and 'Part::Feature' in obj.TypeId:
        if 'App::Part' not in obj.TypeId and 'Part' in obj.TypeId:
            #if obj.Visibility==True:
            if doc.getObject(obj.Name).Transparency == 0:
                #obj.Document.getObject(obj.Name).Visibility=False
                doc.getObject(obj.Name).Transparency = 70
            else:
                doc.getObject(obj.Name).Transparency = 0
##
class ksuToolsTransparencyToggle:
    "ksu tools Transparency Toggle"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'transparency_toggle.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Transparency Toggle" ,
                     'ToolTip' : "Selection Transparency Toggle"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            doc=FreeCADGui.ActiveDocument
            for obj in sel:
                if "App::Part" not in obj.TypeId:
                    if doc.getObject(obj.Name).Transparency == 0:
                        doc.getObject(obj.Name).Transparency = 70
                    else:
                        doc.getObject(obj.Name).Transparency = 0
                else:
                    toggle_transparency_subtree(FreeCADGui.Selection.getSelection())
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one or more object(s) to change its transparency!")
            FreeCAD.Console.PrintWarning("Select one or more object(s) to change its transparency!\n")             

FreeCADGui.addCommand('ksuToolsTransparencyToggle',ksuToolsTransparencyToggle())

#####

##
class ksuToolsHighlightToggle:
    "ksu tools Highlight Toggle"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'select_toggle.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Highlight Toggle" ,
                     'ToolTip' : "Selection Highlight Toggle"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            toggle_highlight_subtree(FreeCADGui.Selection.getSelection())
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one or more object(s) to be highlighted!")
            FreeCAD.Console.PrintWarning("Select one or more object(s) to be highlighted!\n")             

FreeCADGui.addCommand('ksuToolsHighlightToggle',ksuToolsHighlightToggle())

#####
class ksuToolsVisibilityToggle:
    "ksu tools Visibility Toggle"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'visibility_toggle.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Visibility Toggle" ,
                     'ToolTip' : "Selection Visibility Toggle"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            toggle_visibility_subtree(FreeCADGui.Selection.getSelection())
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one or more object(s) to toggle visibility!")
            FreeCAD.Console.PrintWarning("Select one or more object(s) to toggle visibility!\n")             

FreeCADGui.addCommand('ksuToolsVisibilityToggle',ksuToolsVisibilityToggle())

#####
class ksuToolsCheckSolid:
    "ksu tools Check Solid property"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'ShapeInfo_check.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu Check Solid property" ,
                     'ToolTip' : "Check Solid property\nToggle suffix"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
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
            def i_say(msg):
                FreeCAD.Console.PrintMessage(msg)
                FreeCAD.Console.PrintMessage('\n')
            
            def i_sayw(msg):
                FreeCAD.Console.PrintWarning(msg)
                FreeCAD.Console.PrintWarning('\n')
                
            def i_sayerr(msg):
                FreeCAD.Console.PrintError(msg)
                FreeCAD.Console.PrintWarning('\n')
            ##
            if len(sel)<1:
                    msg="Select one or more object(s) to be checked!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else:
                non_solids=''
                solids=''
                for o in sel:
                    if hasattr(o,"Shape"):
                        if '.[compsolid]' in o.Label or '.[solid]' in o.Label or '.[shell]' in o.Label\
                                 or '.[compound]' in o.Label:
                            o.Label=mk_str(o.Label).replace('.[solid]','').replace('.[shell]','').replace('.[compsolid]','').replace('.[compound]','')
                        else:
                            if len(o.Shape.Solids)>0:
                                i_say(mk_str(o.Label)+' Solid object(s) NBR : '+str(len(o.Shape.Solids)))
                                solids+=mk_str(o.Label)+'<br>'
                                if '.[solid]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[solid]'
                            else:
                                i_sayerr(mk_str(o.Label)+' object is a NON Solid')
                                non_solids+=mk_str(o.Label)+'<br>'
                            if len(o.Shape.Shells)>0:
                                i_say(mk_str(o.Label)+' Shell object(s) NBR : '+str(len(o.Shape.Shells)))
                                if '.[shell]' not in o.Label and '.[solid]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[shell]'
                            if len(o.Shape.Compounds)>0:
                                i_say(mk_str(o.Label)+' Compound object(s) NBR : '+str(len(o.Shape.Compounds)))
                                if '.[compound]' not in o.Label and '.[solid]' not in o.Label and '.[shell]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[compound]'
                            if len(o.Shape.CompSolids)>0:
                                i_say(mk_str(o.Label)+' CompSolids object(s) NBR : '+str(len(o.Shape.CompSolids)))
                                if '.[compsolid]' not in o.Label and '.[solid]' not in o.Label and '.[shell]' not in o.Label\
                                    and '.[compound]' not in o.Label:
                                    o.Label=mk_str(o.Label)+'.[compsolid]'
                    else:
                        FreeCAD.Console.PrintWarning("Select object with a \"Shape\" to be checked!\n")
                # if len (non_solids)>0:
                #     reply = QtGui.QMessageBox.information(None,"Warning", 'List of <b>NON Solid</b> object(s):<br>'+non_solids)
                # if len (solids)>0:
                #     reply = QtGui.QMessageBox.information(None,"Info", 'List of <b>Solid</b> object(s):<br>'+solids)
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one or more object(s) to be checked!")
            FreeCAD.Console.PrintWarning("Select one or more object(s) to be checked!\n")             

FreeCADGui.addCommand('ksuToolsCheckSolid',ksuToolsCheckSolid())

#####
def toggleAlly(tree, item, collapse):
    if collapse == False:
        tree.expandItem(item)
    elif collapse == True:  
        tree.collapseItem(item)
    for i in range(item.childCount()):
        print(item.child(i).text(0))
        if 'Origin' not in item.child(i).text(0):
            toggleAlly(tree, item.child(i), collapse)
##


class ksuToolsToggleTreeView:
    "ksu tools Toggle Tree View"
 
    def GetResources(self):
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'expand_all.svg') , # the name of a svg file available in the resources
                     'MenuText': "ksu tools Expand/Collapse Tree View" ,
                     'ToolTip' : "ksu tools Expand/Collapse Tree View"}
 
    def IsActive(self):
        return True
 
    def Activated(self):
        # do something here...
        if FreeCADGui.Selection.getSelection():
            ##
            sel=FreeCADGui.Selection.getSelection()
            ##
            if len(sel)!=1:
                    msg="Select one expandable tree object to be expanded/compressed!\n"
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)             
            else:
                import expTree;reload_lib(expTree)
                expTree.toggle_Tree()
        else:
            #FreeCAD.Console.PrintError("Select elements from dxf imported file\n")
            reply = QtGui.QMessageBox.information(None,"Warning", "Select one expandable tree object to be expanded/compressed!")
            FreeCAD.Console.PrintWarning("Select one expandable tree object to be expanded/compressed!\n")             

FreeCADGui.addCommand('ksuToolsToggleTreeView',ksuToolsToggleTreeView())

#####
class ksuToolsAligner:
    "ksu tools Aligner"
    
    def GetResources(self):
        mybtn_tooltip ="Manipulator tools \'Aligner\'"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Align.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            import Aligner;reload_lib(Aligner)

FreeCADGui.addCommand('ksuToolsAligner',ksuToolsAligner())

#####
class ksuToolsMover:
    "ksu tools Mover"
    
    def GetResources(self):
        mybtn_tooltip ="Manipulator tools \'Mover\'"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Mover.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            import Mover;reload_lib(Mover)

FreeCADGui.addCommand('ksuToolsMover',ksuToolsMover())
#####
class ksuToolsCaliper:
    "ksu tools Caliper"
    
    def GetResources(self):
        mybtn_tooltip ="Manipulator tools \'Caliper\'"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Caliper.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        combined_path = '\t'.join(sys.path)
        if 'Manipulator' in combined_path:
            import Caliper;reload_lib(Caliper)

FreeCADGui.addCommand('ksuToolsCaliper',ksuToolsCaliper())
#####
class ksuToolsMergeSketches:
    "ksu tools Merge Sketches"
    
    def GetResources(self):
        mybtn_tooltip ="Merge Sketches"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Sketcher_MergeSketch.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if FreeCADGui.Selection.getSelection():
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        FreeCADGui.runCommand('Sketcher_MergeSketches')
        for s in FreeCADGui.Selection.getSelection():
            FreeCADGui.ActiveDocument.getObject(s.Name).Visibility=False
        
FreeCADGui.addCommand('ksuToolsMergeSketches',ksuToolsMergeSketches())
###
class ksuToolsEditPrefs:
    "ksu tools Edit Preferences"
    
    def GetResources(self):
        mybtn_tooltip ="Edit Preferences"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Preferences-Edit.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        #import kicadStepUptools
        FreeCADGui.runCommand("Std_DlgPreferences")
        
FreeCADGui.addCommand('ksuToolsEditPrefs',ksuToolsEditPrefs())

#####
class ksuRemoveTimeStamp:
    "ksu  Remove TimeStamp"
    
    def GetResources(self):
        mybtn_tooltip ="Remove TimeStamp from Labels"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'remove_TimeStamp.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        doc = FreeCAD.ActiveDocument
        if doc is not None:
            if FreeCADGui.Selection.getSelection():
                sel=FreeCADGui.Selection.getSelection()
                if len(sel)==1:        
                    return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # removing TimeStamp ...
        doc = FreeCAD.ActiveDocument
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            if len(sel)!=1:
                msg="Select one tree object to remove its Label TimeStamps!\n"
                reply = QtGui.QMessageBox.information(None,"Warning", msg)
                FreeCAD.Console.PrintWarning(msg)             
            else:
                #msgBox = QtGui.QMessageBox()
                #msgBox.setText("This will remove ALL TimeStamps from selection objects.\nIt cannot be ondone.")
                #msgBox.setInformativeText("Do you want to continue?")
                #msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                #msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
                ret = QtGui.QMessageBox.warning(None, ("Warning"),
                               ("This will remove ALL TimeStamps from selection objects.\nDo you want to continue?"),
                               QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                               QtGui.QMessageBox.Cancel)
                #ret = msgBox.exec_()
                if ret == QtGui.QMessageBox.Ok:
                    for ob in sel:
                    #for o in doc.Objects:
                        #print (ob.Name,ob.Label,ob.TypeId)    
                        if ob.TypeId == 'App::Part' or ob.TypeId == 'App::LinkGroup':
                            o_list = ob.OutListRecursive
                            for o in o_list:
                                #print (o.Label)
                                if (hasattr(o, 'Shape')) \
                                        and ('Axis' not in o.Label and 'Plane' not in o.Label and 'Sketch' not in o.Label):
                                    if o.Label.rfind('_') < o.Label.rfind('['):
                                        ts = o.Label[o.Label.rfind('_')+1:o.Label.rfind('[')]
                                        #print (len(ts))
                                        if len(ts) == 8:
                                            o.Label=o.Label[:o.Label.rfind('_')]+o.Label[o.Label.rfind('['):]
                                    else:
                                        ts = o.Label[o.Label.rfind('_')+1:]
                                        #print (len(ts))
                                        if len(ts) == 8:
                                            o.Label=o.Label[:o.Label.rfind('_')]
                                    #print (o.Label)
                            for o in o_list:
                                if ('App::Link' in o.TypeId):
                                    o.Label = o.LinkedObject.Label
                    FreeCAD.Console.PrintWarning('removed Time Stamps\n')
                elif ret == QtGui.QMessageBox.Cancel:
                    FreeCAD.Console.PrintMessage('Operation Aborted\n')                
        else:
            msg="Select one tree object to remove its Label TimeStamps!\n"
            reply = QtGui.QMessageBox.information(None,"Warning", msg)
            FreeCAD.Console.PrintWarning(msg)             

FreeCADGui.addCommand('ksuRemoveTimeStamp',ksuRemoveTimeStamp())
###
class ksuRemoveSuffix:
    "ksu  Remove Suffix"
    
    def GetResources(self):
        mybtn_tooltip ="Remove \'custom\' Suffix from Labels"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'RemoveSuffix.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        doc = FreeCAD.ActiveDocument
        if doc is not None:
            if FreeCADGui.Selection.getSelection():
                sel=FreeCADGui.Selection.getSelection()
                if len(sel)==1:        
                    return True

    def Activated(self):
        # removing TimeStamp ...
        doc = FreeCAD.ActiveDocument
        if FreeCADGui.Selection.getSelection():
            sel=FreeCADGui.Selection.getSelection()
            if len(sel)!=1:
                msg="Select one tree object to remove its Label Suffix!\n"
                reply = QtGui.QMessageBox.information(None,"Warning", msg)
                FreeCAD.Console.PrintWarning(msg)             
            else:
                import exchangePositions;reload_lib(exchangePositions)
                #msgBox = QtGui.QMessageBox()
                #msgBox.setText("This will remove ALL TimeStamps from selection objects.\nIt cannot be ondone.")
                #msgBox.setInformativeText("Do you want to continue?")
                #msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                #msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
                #ret = QtGui.QMessageBox.warning(None, ("Warning"),
                # message box
                rdlg = exchangePositions.RemoveSuffixDlg()
                #msg_box = QtGui.QMessageBox()
                #msg_box.setWindowTitle("Warning")
                #msg_box.setText("This will remove ALL Suffix \'.stp\', \'.step\' from selection objects.\nDo you want to continue?")
                ##layout = msg_box.layout()
                #msg_box.txtInp = QtGui.QLineEdit()
                ##layout.addWidget(msg_box.txtInp)
                #gl = QtGui.QVBoxLayout()
                #gl.addWidget(msg_box.txtInp)
                #msg_box.setLayout(gl) 
                #msg_box.setInformativeText('Informative text.')
                #msg_box.setDetailedText("Detailed text.")
                ##msg_box.DetailedText.setTextInteractionFlags (QtCore.Qt.TextEditorInteraction)  #(QtCore.Qt.NoTextInteraction) # (QtCore.Qt.TextSelectableByMouse)
                #msg_box.setIcon(QtGui.QMessageBox.Critical)
                #msg_box.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                #msg_box.setDefaultButton(QtGui.QMessageBox.Cancel)
                #
                #ret = msg_box.exec_()
                
                ret = rdlg.exec_()
                
                # ret = QtGui.QMessageBox.warning(None, ("Warning"),
                #                ("This will remove ALL Suffix \'.stp\', \'.step\' from selection objects.\nDo you want to continue?"),
                #                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                #                QtGui.QMessageBox.Cancel)
                #ret = msgBox.exec_()
                # print(ret)
                # print (rdlg.le.text())
                filtering=rdlg.le.text()
                if ret: # == QtGui.QMessageBox.Ok:
                    for ob in sel:
                    #for o in doc.Objects:
                        #print (ob.Name,ob.Label,ob.TypeId)    
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
                                    #o.Label = re.sub(rdlg.le.text()+'$', '', o.Label, flags=re.IGNORECASE)
                                    #print(o.Label[:o.Label.rfind (filtering)])
                                    if o.Label.rfind (filtering) != -1:
                                        o.Label = o.Label[:o.Label.rfind (filtering)]
                                    #o.Label = re.sub('.stp', '', o.Label, flags=re.IGNORECASE)
                                    #o.Label = re.sub('.step', '', o.Label, flags=re.IGNORECASE)
                                    #print (o.Label)
                                if o.TypeId == 'App::Part' or o.TypeId == 'App::LinkGroup':
                                    #o.Label = re.sub(rdlg.le.text()+'$', '', o.Label, flags=re.IGNORECASE)
                                    fixfiltering = filtering.replace('.','_')
                                    #print (fixfiltering)
                                    #print(o.Label[:o.Label.rfind (fixfiltering)])
                                    if o.Label.rfind (fixfiltering) != -1:
                                        o.Label = o.Label[:o.Label.rfind (fixfiltering)]
                                    #o.Label = re.sub('_stp', '', o.Label, flags=re.IGNORECASE)
                                    #o.Label = re.sub('_step', '', o.Label, flags=re.IGNORECASE)
                                    #o.Label = re.sub('.stp', '', o.Label, flags=re.IGNORECASE)
                                    #o.Label = re.sub('.step', '', o.Label, flags=re.IGNORECASE)                              
                            for o in o_list:
                                if (o.TypeId == 'App::Link'):
                                    o.Label = o.LinkedObject.Label
                    FreeCAD.Console.PrintWarning('removed Suffix \''+filtering+'\' \n')
                elif ret == 0: #== QtGui.QMessageBox.Cancel:
                    msg='Operation Aborted\n'
                    FreeCAD.Console.PrintMessage(msg)
                    reply = QtGui.QMessageBox.information(None,"Warning", msg)
                    FreeCAD.Console.PrintWarning(msg)                    
        else:
            msg="Select one tree object to remove its Label Suffix!\n"
            reply = QtGui.QMessageBox.information(None,"Warning", msg)
            FreeCAD.Console.PrintWarning(msg)             

FreeCADGui.addCommand('ksuRemoveSuffix',ksuRemoveSuffix())

#####
class ksuToolsExplode:
    "ksu tools Explode"
    
    def GetResources(self):
        mybtn_tooltip ="ksu Tools PCB Explode\nSelect the top container of a kicad PCB to exlode it"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Explode_Pcb.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
 
    def Activated(self):
        # do something here...
        import explode
        explode.runExplodeGui()
        #import explode;reload_lib(explode)

FreeCADGui.addCommand('ksuToolsExplode',ksuToolsExplode())
#####
class ksuToolsDefeaturingTools:
    "ksu tools DefeaturingTools"
    
    def GetResources(self):
        mybtn_tooltip ="Defeaturing Tools from Defeaturing WorkBench"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'DefeaturingTools.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        combined_path = '\t'.join(sys.path)
        if 'Defeaturing' in combined_path:
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        combined_path = '\t'.join(sys.path)
        if 'Defeaturing' in combined_path:
            import DefeaturingTools;reload_lib(DefeaturingTools)

FreeCADGui.addCommand('ksuToolsDefeaturingTools',ksuToolsDefeaturingTools())
#####
class ksuToolsRemoveSubTree:
    "ksu tools Remove Sub Tree"
    
    def GetResources(self):
        mybtn_tooltip ="Remove Sub Tree"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'RemoveSubtree.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        from PySide import QtGui, QtCore
        reply = QtGui.QMessageBox.question(None, "DelTree","Remove Sub Tree?\n[Undo WILL NOT work!]", QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Ok:
            #print('OK clicked.')
            import kicadStepUptools
            kicadStepUptools.removesubtree(FreeCADGui.Selection.getSelection())
        else:
            FreeCAD.Console.PrintMessage('Cancel clicked.')
FreeCADGui.addCommand('ksuToolsRemoveSubTree',ksuToolsRemoveSubTree())
####
class ksuToolsAddTracks:
    "ksu tools Add Tracks"
    
    def GetResources(self):
        mybtn_tooltip ="ksu tools Add Tracks\nNB: it could be a very intensive loading!"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'tracks.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        import tracks
        tracks.addtracks()

FreeCADGui.addCommand('ksuToolsAddTracks',ksuToolsAddTracks())
#####
class ksuToolsAddSilks:
    "ksu tools Add Silks"
    
    def GetResources(self):
        mybtn_tooltip ="ksu tools Add Silks from kicad exported DXF\nNB: it could be a very intensive loading!"
        return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Silks.svg') , # the name of a svg file available in the resources
                     'MenuText': mybtn_tooltip ,
                     'ToolTip' : mybtn_tooltip}
 
    def IsActive(self):
        return True
        #else:
        #    self.setToolTip("Grayed Tooltip!")
        #    print(self.ObjectName)
        #    grayed_tooltip="Grayed Tooltip!"
        #    mybtn_tooltip=grayed_tooltip
 
    def Activated(self):
        # do something here...
        import makefacedxf
        if makefacedxf.checkDXFsettings():
            makefacedxf.makeFaceDXF()
        else:
            msg = """<b>DXF import setting NOT as required.</b><br>Please check to have selected:<br>
            - DXF Legacy Importer<br>
            - DXF Join Geometries<br>
            - DXF Create Simple Part Shapes<br>
            in DXF Preferences Import options"""
            reply = QtGui.QMessageBox.information(None,"Warning", msg)

FreeCADGui.addCommand('ksuToolsAddSilks',ksuToolsAddSilks())
#####
class ksuExcDemo:
    exFile = None

    def __init__(self, exFile):
        self.exFile = str(exFile)
        self.ext    = self.exFile[self.exFile.rfind('.'):].lower()
        #print self.ext
    
    # 'hierarchy_nav.svg' for Demo
    #'Pixmap'  : os.path.join( ksuWB_icons_path , 'hierarchy_nav.svg') ,

    def GetResources(self):
        if 'pdf' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'datasheet.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}
        elif 'kicad_pcb' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importPCB.svg'), #'importBoard.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}
        elif 'kicad_mod' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importFP.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}
        elif 'fcstd' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'Freecad.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}        
        elif 'dxf' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , '2D-frame.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}        
        elif 'step' in self.ext:
            return {'Pixmap'  : os.path.join( ksuWB_icons_path , 'importStep.svg') ,
                    'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}                    
        else:
            return {'MenuText': str(self.exFile),
                    'ToolTip' : "Demo files"}

    def Activated(self):
        FreeCAD.Console.PrintWarning('opening ' + self.exFile + "\r\n")
        import os, sys
        # So we can open the "Open File" dialog
        mw = FreeCADGui.getMainWindow()

        # Start off defaulting to the Examples directory
        ksu_base_path = ksu_locator.module_path()
        exs_dir_path = os.path.join(ksu_base_path, 'demo')
        abs_ksu_path = ksu_locator.abs_module_path()
        # Append this script's directory to sys.path
        sys.path.append(os.path.dirname(exs_dir_path))

        # We've created a library that FreeCAD can use as well to open CQ files
        fnameDemo=(os.path.join(exs_dir_path, self.exFile))
        demo_model='dpak-to252.step'
        stepfname=(os.path.join(exs_dir_path, 'shapes',demo_model))
        ext = os.path.splitext(os.path.basename(fnameDemo))[1]
        nme = os.path.splitext(os.path.basename(fnameDemo))[0]
        FC_majorV=int(float(FreeCAD.Version()[0]))
        FC_minorV=int(float(FreeCAD.Version()[1]))

        if ext.lower()==".pdf":
            import subprocess, sys
            if sys.platform == "linux" or sys.platform == "linux2":
                # linux
                subprocess.call(["xdg-open", fnameDemo])
            if sys.platform == "darwin":
                # osx
                cmd_open = 'open '+fnameDemo
                os.system(cmd_open) #win, osx
            else:
                # win
                subprocess.Popen([fnameDemo],shell=True)
        elif ext.lower()==".kicad_pcb" or ext.lower()==".kicad_mod":
            #FreeCAD.Console.PrintMessage(abs_ksu_path + "\r\n")
            #FreeCAD.Console.PrintMessage(stepfname + "\r\n")
            #FreeCAD.Console.PrintMessage(exs_dir_path + "\r\n")
            import kicadStepUptools
            #    reload( kicadStepUptools )
            if reload_Gui:
                reload_lib( kicadStepUptools )
            from kicadStepUptools import open, create_axis #onLoadBoard, onLoadFootprint
            if ext.lower()==".kicad_mod":
                dname= (demo_model).split('.')[0].replace('-','_')
                doc = FreeCAD.newDocument(dname)
                dname=doc.Name
                #print dname
                FreeCAD.setActiveDocument(dname)
                FreeCAD.ActiveDocument=FreeCAD.getDocument(dname)
                FreeCADGui.ActiveDocument=FreeCADGui.getDocument(dname)
                #doc=FreeCAD.newDocument((demo_model).split('.')[0].replace('-','_'))
                #FreeCAD.setActiveDocument(doc)
                import ImportGui
                ImportGui.insert(stepfname,doc.Name)
                FreeCADGui.activeDocument().activeView().viewAxonometric()
                open (fnameDemo)
                if FreeCAD.ActiveDocument.getObject("axis") is None:
                    create_axis()
            else:
                open (fnameDemo)
            #docL=FreeCAD.ActiveDocument.Label
        elif ext.lower()==".fcstd":
            if FC_majorV==0 and FC_minorV <17:
                fnameDemo=fnameDemo.rstrip(ext)+'-fc16'+ ext
                FreeCAD.Console.PrintWarning('opening ' + fnameDemo + "\r\n")
            FreeCAD.open(fnameDemo)
            if 'footprint' not in fnameDemo:
                FreeCADGui.activeDocument().activeView().viewAxonometric()
        elif ext.lower()==".step":
            if FC_majorV==0 and FC_minorV <17:
                fnameDemo=fnameDemo.rstrip(ext)+'-fc16'+ ext
                FreeCAD.Console.PrintWarning('opening ' + fnameDemo + "\r\n")
            import ImportGui
            ImportGui.open(fnameDemo)
            FreeCADGui.activeDocument().activeView().viewAxonometric()
            FreeCADGui.SendMsgToActiveView("ViewFit")
        elif ext.lower()==".dxf":
            #import ImportGui
            import importDXF
            importDXF.open(fnameDemo)
            #ImportGui.open(fnameDemo)
            #FreeCADGui.activeDocument().activeView().viewAxonometric()
            FreeCADGui.SendMsgToActiveView("ViewFit")
        #if ext==".pdf":
        #    subprocess.Popen([file],shell=True)
        
        #import ImportGui
        #ImportGui.open(os.path.join(exs_dir_path, self.exFile))
        #ImportCQ.open(os.path.join(exs_dir_path, self.exFile))

##
