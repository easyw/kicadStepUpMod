# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Cad\Progetti_K\3D-FreeCad-tools\explode.ui'
#
# Created: Fri Sep 21 14:09:48 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

__version__ = "v1.0.1"

import FreeCAD, FreeCADGui
from PySide import QtCore, QtGui
from sys import platform as _platform

global s  # selection observer
global instance_nbr, explode_dwg
instance_nbr=0

# window GUI dimensions parameters
wdsExpx=300;wdsExpy=130
pt_osx=False
if _platform == "linux" or _platform == "linux2":
    # linux
    sizeX=wdsExpx;sizeY=wdsExpy-22+34 #516 #536
else:
    sizeX=wdsExpx;sizeY=wdsExpy-22 #482#502
if _platform == "darwin":
    pt_osx=True
##   # MAC OS X
##elif _platform == "win32":
##   # Windows

toBeReset = None

###
class expSelectionObserver:
    def addSelection(self,document, object, element, position):
        """Add single object to selection. Usually gets called when selecting in the 3d view"""
        global explode_dwg
        sel = FreeCADGui.Selection.getSelection()
        if len (sel)== 1:
            if 'App::Part' in sel[0].TypeId:
                explode_dwg.ui.hSlider_explode.setEnabled(True)
        else:
            explode_dwg.ui.hSlider_explode.setEnabled(False)
        # FreeCAD.Console.PrintMessage(document+"\n")
        # FreeCAD.Console.PrintMessage(object+"\n")
        # FreeCAD.Console.PrintMessage(element+"\n")
        # FreeCAD.Console.PrintMessage(str(position)+"\n")
        # ...

    def removeSelection(self,document, object, element):
        """Remove single object from selection. Usually gets called when deselecting in the 3d view"""
        global explode_dwg
        sel = FreeCADGui.Selection.getSelection()
        if len (sel)== 1:
            if 'App::Part' in sel[0].TypeId:
                explode_dwg.ui.hSlider_explode.setEnabled(True)
        else:
            explode_dwg.ui.hSlider_explode.setEnabled(False)
        #FreeCAD.Console.PrintMessage(document+"\n")
        #FreeCAD.Console.PrintMessage(object+"\n")
        #FreeCAD.Console.PrintMessage(element+"\n")
        # ...

    def setSelection(self,document):
        """Add one or more objects to selection. Usually gets called when selecting in the tree view"""
        global explode_dwg
        sel = FreeCADGui.Selection.getSelection()
        if len (sel)== 1:
            if 'App::Part' in sel[0].TypeId:
                explode_dwg.ui.hSlider_explode.setEnabled(True)
        else:
            explode_dwg.ui.hSlider_explode.setEnabled(False)
        #FreeCAD.Console.PrintMessage(document+"\n")
        #selection=Gui.Selection.getSelection(document)
        # ...

    def clearSelection(self,document):
        """Remove all objects of the given document from the selection"""
        global explode_dwg
        sel = FreeCADGui.Selection.getSelection()
        if len (sel)== 1:
            if 'App::Part' in sel[0].TypeId:
                explode_dwg.ui.hSlider_explode.setEnabled(True)
        else:
            explode_dwg.ui.hSlider_explode.setEnabled(False)
        #FreeCAD.Console.PrintMessage(document+"\n")
        # ...
###

###########################################
class Ui_explode_dwg(object):
    def setupUi(self, explode_dwg):
        explode_dwg.setObjectName("explode_dwg")
        explode_dwg.resize(303, 141)
        explode_dwg.setLayoutDirection(QtCore.Qt.LeftToRight)
        explode_dwg.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        explode_dwg.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.mainGroup = QtGui.QGroupBox(self.dockWidgetContents)
        self.mainGroup.setGeometry(QtCore.QRect(4, 0, 293, 69))
        self.mainGroup.setTitle("Explode 3D PCB")
        self.mainGroup.setObjectName("mainGroup")
        self.gridLayoutWidget_13 = QtGui.QWidget(self.mainGroup)
        self.gridLayoutWidget_13.setGeometry(QtCore.QRect(8, 24, 277, 37))
        self.gridLayoutWidget_13.setObjectName("gridLayoutWidget_13")
        self.gridLayout_15 = QtGui.QGridLayout(self.gridLayoutWidget_13)
        self.gridLayout_15.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_15.setHorizontalSpacing(1)
        self.gridLayout_15.setVerticalSpacing(2)
        self.gridLayout_15.setObjectName("gridLayout_15")
        self.hSlider_explode = QtGui.QSlider(self.gridLayoutWidget_13)
        self.hSlider_explode.setToolTip("Explode PCB (in mm)")
        self.hSlider_explode.setOrientation(QtCore.Qt.Horizontal)
        self.hSlider_explode.setObjectName("hSlider_explode")
        self.gridLayout_15.addWidget(self.hSlider_explode, 0, 0, 1, 1)
        self.pb_Close = QtGui.QPushButton(self.dockWidgetContents)
        self.pb_Close.setGeometry(QtCore.QRect(196, 72, 93, 28))
        self.pb_Close.setToolTip("Exit")
        self.pb_Close.setText("Exit")
        self.pb_Close.setObjectName("pb_Close")
        self.pb_Reset = QtGui.QPushButton(self.dockWidgetContents)
        self.pb_Reset.setGeometry(QtCore.QRect(12, 72, 93, 28))
        self.pb_Reset.setToolTip("Reset")
        self.pb_Reset.setText("Reset")
        self.pb_Reset.setObjectName("pb_Reset")
        explode_dwg.setWidget(self.dockWidgetContents)

        self.retranslateUi(explode_dwg)
        QtCore.QMetaObject.connectSlotsByName(explode_dwg)
    #def retranslateUi(self, explode_dwg):
    #    explode_dwg.setWindowTitle(QtGui.QApplication.translate("explode_dwg", "Explode 3D PCB", None, QtGui.QApplication.UnicodeUTF8))
################################################################################################
        explode_dwg.setWindowTitle("Explode 3D PCB")
        self.pb_Close.clicked.connect(onCloseExp)
        self.pb_Reset.clicked.connect(onReset)
        self.hSlider_explode.valueChanged.connect(SlideValueChange)
        self.hSlider_explode.setEnabled(False)
        self.hSlider_explode.setToolTip("Explode PCB\nSelect the top container of a kicad PCB to exlode it")

    def retranslateUi(self, explode_dwg):
        pass
##############################################################

def explode_pcb(pos):
    doc = FreeCAD.ActiveDocument
    docG = FreeCADGui.ActiveDocument
    sc = 2.0
    sel = FreeCADGui.Selection.getSelection()
    if len(sel) == 1:
        if 'App::Part' in sel[0].TypeId:
            for o in sel[0].OutListRecursive:
                if o.Label == 'Pcb':
                    if (pos != 0):
                        docG.getObject(o.Name).Transparency=70
                    else:
                        docG.getObject(o.Name).Transparency=0
                if o.Label == 'Top':
                    o.Placement.Base.z=pos
                if o.Label == 'Bot':
                    o.Placement.Base.z=-pos
                if o.Label == 'TopV':
                    o.Placement.Base.z=pos*sc
                if o.Label == 'BotV':
                    o.Placement.Base.z=-pos*sc
            return sel[0]
        #return None

def SlideValueChange():
    global toBeReset, explode_dwg
    pos = explode_dwg.ui.hSlider_explode.sliderPosition()
    #print('moving',pos)
    toBeReset = explode_pcb(pos)
#
def onReset():
    global toBeReset, explode_dwg
    print ('Imploding')
    sel = FreeCADGui.Selection.getSelection()
    if len (sel) == 0 and toBeReset is not None:
        try:
            FreeCADGui.Selection.addSelection(toBeReset)
        except:
            pass
    explode_dwg.ui.hSlider_explode.setValue(0)
    explode_pcb(0)
#
def onCloseExp():
    global s, explode_dwg
    
    onReset()
    """closing dialog"""
    print('closing')
    try:
        FreeCADGui.Selection.removeObserver(s)
        print('observer removed')
    except:
        print('observer not removed')
    explode_dwg.deleteLater()
#
##

def Exp_singleInstance():
    app = QtGui.QApplication #QtGui.qApp
    for i in app.topLevelWidgets():
        #i_say (str(i.objectName()))
        if i.objectName() == "ksuExplode":
            #i_say (str(i.objectName()))
            #i.close()
            #i.deleteLater()
            #i_say ('closed')
            return False
    t=FreeCADGui.getMainWindow()
    dw=t.findChildren(QtGui.QDockWidget)
    #say( str(dw) )
    for i in dw:
        #i_say (str(i.objectName()))
        if str(i.objectName()) == "ksuExplode": #"kicad StepUp 3D tools":
            #i_say (str(i.objectName())+' docked')
            #i.deleteLater()
            return False
    return True
##

def Exp_centerOnScreen ():
    '''centerOnScreen()
    Centers the window on the screen.'''
    # sayw(widg.width());sayw(widg.height())
    # sayw(widg.pos().x());sayw(widg.pos().y())
    resolution = QtGui.QDesktopWidget().screenGeometry()
    xp=(resolution.width() / 2) - sizeX/2 # - (KSUWidget.frameSize().width() / 2)
    yp=(resolution.height() / 2) - sizeY/2 # - (KSUWidget.frameSize().height() / 2))
    # xp=widg.pos().x()-sizeXMax/2;yp=widg.pos().y()#+sizeY/2
    explode_dwg.setGeometry(xp, yp, sizeX, sizeY)
##

def runExplodeGui():
    global explode_dwg
    doc=FreeCAD.ActiveDocument
    
    if Exp_singleInstance():
        global s
        
        explode_dwg = QtGui.QDockWidget()
        explode_dwg.ui = Ui_explode_dwg()
        explode_dwg.ui.setupUi(explode_dwg)
        explode_dwg.setObjectName("ksuExplode")
        explode_dwg.raise_()
        explode_dwg.setFeatures( QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable ) # | QtGui.QDockWidget.DockWidgetClosable )
        
        #RHDockWidget.destroyed.connect(onDestroy)
        #explode_dwg.visibilityChanged.connect(onClickClose)
            
        ExpMw = FreeCADGui.getMainWindow()                 # PySide # the active qt window, = the freecad window since we are inside it
        ExpMw.addDockWidget(QtCore.Qt.RightDockWidgetArea,explode_dwg)
        explode_dwg.setFloating(True)  #undock
        #RHDockWidget.resize(sizeX,sizeY)
        Exp_centerOnScreen()
        s=expSelectionObserver()
        FreeCADGui.Selection.addObserver(s)
        
        onReset()
        #explode_dwg.ui.Version.setText(__version__)
    
    #else:
        #raising up
        explode_dwg.activateWindow()
        explode_dwg.raise_()
        sel = FreeCADGui.Selection.getSelection()
        if len (sel)== 1:
            if 'App::Part' in sel[0].TypeId:
                explode_dwg.ui.hSlider_explode.setEnabled(True)
            else:
                explode_dwg.ui.hSlider_explode.setEnabled(False)


#if __name__ == "__main__":
#    import sys
#    app = QtGui.QApplication(sys.argv)
#    explode_dwg = QtGui.QDockWidget()
#    ui = Ui_explode_dwg()
#    ui.setupUi(explode_dwg)
#    explode_dwg.show()
#    sys.exit(app.exec_())


