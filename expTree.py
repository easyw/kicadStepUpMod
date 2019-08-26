# -*- coding: utf-8 -*-
#
# Expands selected tree and all sub trees in the tree view.
# if selected tree is already expanded this tree and all sub trees are collapsed
#
# Author: wmayer

import FreeCAD, FreeCADGui
from PySide import QtGui
#from PySide.QtGui import QTreeWidgetItemIterator

def toggleAllSel(tree, item, collapse):
    if collapse == False:
        tree.expandItem(item)
    elif collapse == True:  
        tree.collapseItem(item)
    for i in range(item.childCount()):
        #print(item.child(i).text(0))
        if 'Origin' not in item.child(i).text(0):
            toggleAllSel(tree, item.child(i), collapse)
##
def toggle_Tree():        
    mw1 = FreeCADGui.getMainWindow()
    treesSel = mw1.findChildren(QtGui.QTreeWidget)
    
    for tree in treesSel:
        items = tree.selectedItems()
        for item in items:
            if item.isExpanded() == True:
                collapse = True
                print ("collapsing")
            else:
                print ("expanding")
                collapse = False  
            toggleAllSel(tree, item, collapse)
##

def collS_Tree():        
    # collapse selected 
    mw1 = FreeCADGui.getMainWindow()
    treesSel = mw1.findChildren(QtGui.QTreeWidget)
    
    for tree in treesSel:
        items = tree.selectedItems()
        for item in items:
            if item.isExpanded() == True:
                collapse = True
                print ("collapsing")
                tree.collapseItem(item)
            #else:
            #    print ("expanding")
            #    collapse = False  
##

def expS_Tree():        
    # expand selected 
    mw1 = FreeCADGui.getMainWindow()
    treesSel = mw1.findChildren(QtGui.QTreeWidget)
    
    for tree in treesSel:
        items = tree.selectedItems()
        for item in items:
            if item.isExpanded() == False:
                collapse = False
                print ("expanding")
                tree.expandItem(item)
            #else:
            #    print ("expanding")
            #    collapse = False  
##
