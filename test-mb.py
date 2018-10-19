
from PySide import QtGui, QtCore

# msg_box = QtGui.QMessageBox()
# msg_box.setWindowTitle("Warning")
# msg_box.setText("This will remove ALL Suffix \'.stp\', \'.step\' from selection objects.\nDo you want to continue?")
# #layout = msg_box.layout()
# txtInp = QtGui.QLineEdit(msg_box)
# #layout.addWidget(msg_box.txtInp)
# gl = QtGui.QVBoxLayout()
# gl.addWidget(msg_box.txtInp)
# msg_box.setLayout(gl) 
# msg_box.setInformativeText('Informative text.')
# msg_box.setDetailedText("Detailed text.")
# #msg_box.Text.setTextInteractionFlags (QtCore.Qt.TextEditorInteraction)  #(QtCore.Qt.NoTextInteraction) # (QtCore.Qt.TextSelectableByMouse)
# msg_box.setIcon(QtGui.QMessageBox.Critical)
# msg_box.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
# msg_box.setDefaultButton(QtGui.QMessageBox.Cancel)
# 
# ret = msg_box.exec_()


import sys
from PySide.QtCore import SIGNAL
from PySide.QtGui import QDialog, QApplication, QPushButton, QLineEdit, QFormLayout, QLabel, QStyle

if 0:
    class Form(QDialog):
        
        def __init__(self, parent=None):
            
            super(Form, self).__init__(parent)       
            #self.setWindowIcon(self.style().standardIcon(QStyle.SP_DirIcon))
            #QtGui.QIcon(QtGui.QMessageBox.Critical))
            self.txt =  QLabel()
            self.txt.setText("This will remove ALL Suffix from selection objects.  .\nDo you want to continue?\n\n\'suffix\'")
            self.le = QLineEdit()
            self.le.setObjectName("suffix_filter")
            self.le.setText(".step")
    
            self.pb = QPushButton()
            self.pb.setObjectName("OK")
            self.pb.setText("OK") 
    
            self.pbC = QPushButton()
            self.pbC.setObjectName("Cancel")
            self.pbC.setText("Cancel") 
    
            layout = QFormLayout()
            layout.addWidget(self.txt)
            layout.addWidget(self.le)
            layout.addWidget(self.pb)
            layout.addWidget(self.pbC)
    
            self.setLayout(layout)
            self.connect(self.pb, SIGNAL("clicked()"),self.OK_click)
            self.connect(self.pbC, SIGNAL("clicked()"),self.Cancel_click)
            self.setWindowTitle("Warning ...")
            
    
        def OK_click(self):
            # shost is a QString object
            filtered = self.le.text()
            print (filtered)
            self.close()
        def Cancel_click(self):
            # shost is a QString object
            filtered = '.stp'
            print (filtered)
            self.close()
    
    
    #app = QApplication(sys.argv)
    form = Form()
    #form.setIcon(QtGui.QMessageBox.Critical)
    form.show()
    form.exec_()
    #app.exec_()


if 1:
    import sys
    from PySide.QtCore import *
    from PySide.QtGui import *
    class Widget(QDialog):
        
        def __init__(self, parent= None):
            super(Widget, self).__init__(parent, QtCore.Qt.WindowStaysOnTopHint)    
            #QtGui.QMainWindow.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)
            #icon = style.standardIcon(
            #    QtGui.QStyle.SP_MessageBoxCritical, None, widget)
            #self.setWindowIcon(self.style().standardIcon(QtGui.QStyle.SP_MessageBoxCritical))
            #self.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MessageBoxCritical))
            #self.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
            #QtGui.QIcon(QtGui.QMessageBox.Critical))
            #icon = QtGui.QIcon()
            #icon.addPixmap(QtGui.QPixmap("icons/157-stats-bars.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            #Widget.setWindowIcon(icon)
            
            self.txt =  QLabel()
            self.txt.setText("This will remove ALL Suffix from selection objects.  \nDo you want to continue?\n\n\'suffix\'")
            self.le = QLineEdit()
            self.le.setObjectName("suffix_filter")
            self.le.setText(".step")
        
            self.pb = QPushButton()
            self.pb.setObjectName("OK")
            self.pb.setText("OK") 
            
            self.pbC = QPushButton()
            self.pbC.setObjectName("Cancel")
            self.pbC.setText("Cancel") 
        
            layout = QVBoxLayout()
            layout.addWidget(self.txt)
            layout.addWidget(self.le)
            layout.addWidget(self.pb)
            layout.addWidget(self.pbC)
        
            self.setWindowTitle("Warning ...")
            #self.setWindowIcon(self.style().standardIcon(QtGui.QStyle.SP_MessageBoxCritical))
            
            # btn_folder = QPushButton("Folder")
            # btn_folder.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
            # 
            # btn_one = QPushButton("Play")
            # btn_one.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            # 
            # btn_two = QPushButton("Stop")
            # btn_two.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            # 
            # btn_three = QPushButton("Pause")
            # btn_three.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            
            #layout = QHBoxLayout()
            #layout.addWidget(btn_folder)
            #layout.addWidget(btn_one)
            #layout.addWidget(btn_two)
            #layout.addWidget(btn_three)
            
            self.setLayout(layout)
            #self.setLayout(layout)
            self.connect(self.pb, SIGNAL("clicked()"),self.OK_click)
            self.connect(self.pbC, SIGNAL("clicked()"),self.Cancel_click)
        
        def OK_click(self):
            # shost is a QString object
            filtered = self.le.text()
            print (filtered)
            self.close()
        def Cancel_click(self):
            # shost is a QString object
            filtered = '.stp'
            print (filtered)
            self.close()
                
    
    #mw = FreeCADGui.getMainWindow()
    #dialog = Widget(mw)
    dialog = Widget()
    #dialog.setWindowIcon(dialog.style().standardIcon(QtGui.QStyle.SP_MessageBoxCritical))  #non py3 ok
    
    #my_dialog = QDialog(self) 
    #my_dialog.exec_()
    dialog.show()
    #dialog.setModal(True)
    #dialog.exec_()