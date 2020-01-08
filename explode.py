# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Cad\Progetti_K\3D-FreeCad-tools\explode.ui'
#
# Created: Fri Sep 21 14:09:48 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

__version__ = "v1.0.5"

import FreeCAD, FreeCADGui, os
from PySide import QtCore, QtGui
from sys import platform as _platform

global s  # selection observer
global instance_nbr, explode_dwg
instance_nbr=0

# window GUI dimensions parameters
wdsExpx=300;wdsExpy=140
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
btn_iconsize=28

import ksu_locator
ksuWBpath = os.path.dirname(ksu_locator.__file__)
#sys.path.append(ksuWB + '/Gui')
ksuWB_icons_path =  os.path.join( ksuWBpath, 'Resources', 'icons')

def get_top_level (obj):
    lvl=10000
    top=None
    for ap in obj.InListRecursive:
        if hasattr(ap,'Placement') and ap.TypeId!='App::FeaturePython' and ap.TypeId!='Part::Part2DObjectPython':
            if len(ap.InListRecursive) < lvl:
                top = ap
                lvl = len(ap.InListRecursive)
    if top is None:
        if 'App::Part' in obj.TypeId or 'App::LinkGroup' in obj.TypeId:
            top = obj
    return top
###
class expSelectionObserver:
    def addSelection(self,document, object, element, position):
        """Add single object to selection. Usually gets called when selecting in the 3d view"""
        global explode_dwg
        sel = FreeCADGui.Selection.getSelection()
        if len (sel)== 1:
            tlo = get_top_level(sel[0])
            if tlo is not None:
            #if 'App::Part' in sel[0].TypeId:
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
            tlo = get_top_level(sel[0])
            if tlo is not None:
            #if 'App::Part' in sel[0].TypeId:
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
            tlo = get_top_level(sel[0])
            if tlo is not None:
            #if 'App::Part' in sel[0].TypeId:
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
            tlo = get_top_level(sel[0])
            if tlo is not None:
            #if 'App::Part' in sel[0].TypeId:
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
        explode_dwg.resize(306, 141)
        explode_dwg.setMinimumSize(QtCore.QSize(91, 48))
        explode_dwg.setLayoutDirection(QtCore.Qt.LeftToRight)
        explode_dwg.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        explode_dwg.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.mainGroup = QtGui.QGroupBox(self.dockWidgetContents)
        self.mainGroup.setGeometry(QtCore.QRect(4, 0, 293, 109))
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
        self.horizontalLayoutWidget = QtGui.QWidget(self.mainGroup)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(8, 64, 277, 41))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pb_Reset = QtGui.QPushButton(self.horizontalLayoutWidget)
        self.pb_Reset.setToolTip("Reset")
        self.pb_Reset.setText("Reset")
        self.pb_Reset.setObjectName("pb_Reset")
        self.horizontalLayout.addWidget(self.pb_Reset)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtGui.QLabel(self.horizontalLayoutWidget)
        self.label.setText("(+/- mm)")
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.step_lineEdit = QtGui.QLineEdit(self.horizontalLayoutWidget)
        self.step_lineEdit.setMaximumSize(QtCore.QSize(32, 28))
        self.step_lineEdit.setToolTip("incremental step (mm)")
        self.step_lineEdit.setObjectName("step_lineEdit")
        self.horizontalLayout.addWidget(self.step_lineEdit)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pb_Close = QtGui.QPushButton(self.horizontalLayoutWidget)
        self.pb_Close.setToolTip("Exit")
        self.pb_Close.setText("Exit")
        self.pb_Close.setObjectName("pb_Close")
        self.horizontalLayout.addWidget(self.pb_Close)
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
        icon = QtGui.QIcon()
        myicon=os.path.join( ksuWB_icons_path , 'closeSm.svg')
        icon.addPixmap(QtGui.QPixmap(myicon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pb_Close.setIcon(icon)
        #self.pb_Close.setIconSize(QtCore.QSize(btn_iconsize, btn_iconsize))
        self.pb_Close.setGeometry(QtCore.QRect(290, 72, btn_iconsize, btn_iconsize))
        self.pb_Close.setText("")
        icon = QtGui.QIcon()
        myicon=os.path.join( ksuWB_icons_path , 'Reset-to-Center.svg')
        icon.addPixmap(QtGui.QPixmap(myicon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pb_Reset.setIcon(icon)
        #self.pb_Reset.setIconSize(QtCore.QSize(btn_iconsize, btn_iconsize))
        self.pb_Reset.setGeometry(QtCore.QRect(12, 72, btn_iconsize, btn_iconsize))
        self.pb_Reset.setText("")
        self.step_lineEdit.setText("0.5")
        #self.step_lineEdit.setGeometry(QtCore.QRect(12, 12, 12, 12))
        self.step_lineEdit.setMaximumSize(QtCore.QSize(btn_iconsize*2, btn_iconsize))
        self.label.setToolTip("incremental step (mm)")

    def retranslateUi(self, explode_dwg):
        pass
##############################################################

def explode_pcb(pos):
    doc = FreeCAD.ActiveDocument
    docG = FreeCADGui.ActiveDocument
    sc = 2.0
    sel = FreeCADGui.Selection.getSelection()
    if len(sel) == 1:
        tlo = get_top_level(sel[0])
        #print (tlo.Label)
        if tlo is not None:
        #if 'App::Part' in sel[0].TypeId:
            for o in tlo.OutListRecursive:
                if 'Pcb' in o.Label:
                    if o.TypeId == 'App::Part' or o.TypeId == 'App::LinkGroup':
                        for ob in o.OutList:
                            if hasattr(ob,'Shape'):
                                if (pos != 0):
                                    docG.getObject(ob.Name).Transparency=70
                                else:
                                    docG.getObject(ob.Name).Transparency=0
                    else:
                        if hasattr(o,'Shape'):
                            if (pos != 0):
                                docG.getObject(o.Name).Transparency=70
                            else:
                                docG.getObject(o.Name).Transparency=0
                elif 'Top' in o.Label and 'TopV' not in o.Label:
                    if hasattr(o,'Placement'):
                        o.Placement.Base.z=pos
                elif 'Bot' in o.Label and 'BotV' not in o.Label:
                    if hasattr(o,'Placement'):
                        o.Placement.Base.z=-pos
                elif 'TopV' in o.Label:
                    if hasattr(o,'Placement'):
                        o.Placement.Base.z=pos*sc
                elif 'BotV' in o.Label:
                    if hasattr(o,'Placement'):
                        o.Placement.Base.z=-pos*sc
                elif 'topTracks' in o.Label or 'botTracks' in o.Label:
                    if hasattr (o, 'Shape'):
                        if (pos != 0):
                            docG.getObject(o.Name).Transparency = 50
                        else:
                            docG.getObject(o.Name).Transparency = 0
                elif 'topSilk' in o.Label or 'botSilk' in o.Label:
                    if hasattr (o, 'Shape'):
                        if (pos != 0):
                            docG.getObject(o.Name).Transparency = 30
                        else:
                            docG.getObject(o.Name).Transparency = 0
            return tlo
        #return None

def SlideValueChange():
    global toBeReset, explode_dwg
    pos = explode_dwg.ui.hSlider_explode.sliderPosition() * float(explode_dwg.ui.step_lineEdit.text())
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

def Exp_putOnTopRightCorner():
    resolution = QtGui.QDesktopWidget().screenGeometry()
    margin = 80
    xp=(resolution.width()) - sizeX -margin/5 # - (KSUWidget.frameSize().width() / 2)
    yp=(resolution.height()) - sizeY - margin # - (KSUWidget.frameSize().height() / 2))
    # xp=widg.pos().x()-sizeXMax/2;yp=widg.pos().y()#+sizeY/2
    explode_dwg.setGeometry(xp, margin, sizeX, sizeY)
    #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    #self.show()

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
        #Exp_centerOnScreen()
        Exp_putOnTopRightCorner()
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
            tlo = get_top_level(sel[0])
            if tlo is not None:
            #if 'App::Part' in sel[0].TypeId:
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


