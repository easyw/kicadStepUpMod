# -*- coding: utf-8 -*-
#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2018 Maurice                                            *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

from __future__ import print_function
__title__ =  "FreeCAD Zip STEP IGES importer"
__author__ = "Maurice"
__url__ =    "http://www.freecadweb.org"


import os,zipfile,FreeCAD,tempfile,sys

___ZipVersion___ = "1.0.2"

try:
    import __builtin__ as builtin #py2
except:
    import builtins as builtin  #py3


if open.__module__ in ['__builtin__','io']:
    pyopen = open # because we'll redefine open below


def open(filename):
    "called when freecad wants to open a file"
    docname = (os.path.splitext(os.path.basename(filename))[0]).encode("utf8")
    doc = FreeCAD.newDocument(docname)
    doc.Label = decode(docname)
    FreeCAD.ActiveDocument = doc
    read(filename)
    return doc
    

def insert(filename,docname):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc
    read(filename)
    return doc


def decode(name):
    "decodes encoded strings"
    try:
        decodedName = (name.decode("utf8"))
    except UnicodeDecodeError:
        try:
            decodedName = (name.decode("latin1"))
        except UnicodeDecodeError:
            FreeCAD.Console.PrintError(translate("Zip import","Error: Couldn't determine character encoding"))
            decodedName = name
    return decodedName


def read(filename):
    "reads the file and creates objects in the active document"
    #import importZip; reload(importZip)
    print("open Zip STEP version "+___ZipVersion___)
        
    z = zipfile.ZipFile(filename)
    l = z.printdir()
    #il = z.infolist()
    nl = z.namelist()
    print("file list: ", nl)
    import ImportGui, FreeCADGui
    
    for f in nl:
        if '.stp' in f.lower() or '.step' in f.lower(): #\
                    #or '.igs' in f.lower() or '.iges' in f.lower():
            file_content = z.read(f)
            #sfe = z.extract(f)
            #print ('extracted ',sfe)
            print ('extracted ', f)
            # fname=os.path.splitext(os.path.basename(filename))[0]
            # ext = os.path.splitext(os.path.basename(filename))[1]
            fname=f
            print('fname ',f)
            tempdir = tempfile.gettempdir() # get the current temporary directory
            tempfilepath = os.path.join(tempdir,fname) # + ext)
            z.extract(fname, tempdir)
            doc=FreeCAD.ActiveDocument
            ImportGui.insert(tempfilepath,doc.Name)
            FreeCADGui.SendMsgToActiveView("ViewFit")
            try:
                os.remove(tempfilepath)
            except OSError:
                FreeCAD.Console.PrintError("error on removing "+tempfilepath+" file")
            pass
        elif '.fcstd' in f.lower(): #\
            fname=f
            tempdir = tempfile.gettempdir() # get the current temporary directory
            tempfilepath = os.path.join(tempdir,fname) # + ext)
            z.extract(fname, tempdir)
            doc=FreeCAD.ActiveDocument
            i=0
            for obj in FreeCAD.ActiveDocument.Objects:
                i+=1
            if i==0:
                FreeCAD.closeDocument(doc.Name)            
            FreeCAD.open(tempfilepath)
            #ImportGui.insert(tempfilepath,doc.Name)
            FreeCADGui.SendMsgToActiveView("ViewFit")
            try:
                os.remove(tempfilepath)
            except OSError:
                FreeCAD.Console.PrintError("error on removing "+tempfilepath+" file")
            pass
            