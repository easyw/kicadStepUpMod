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

# from __future__ import print_function
__title__ =  "FreeCAD Zip STEP IGES importer"
__author__ = "Maurice"
__url__ =    "http://www.freecadweb.org"


import os,FreeCAD,tempfile,sys

___DXFVersion___ = "1.4.0"

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
    print("open DXF version "+___DXFVersion___)

    import dxf_parser
    from dxf_parser import _importDXF
    global _dxfLibrary, _dxfColorMap, _dxfReader
    from dxf_parser import _dxfLibrary
    from dxf_parser import _dxfColorMap
    from dxf_parser import _dxfReader
    import ImportGui, FreeCADGui
    
    #_importDXF.processdxf(FreeCAD.ActiveDocument, filename, getShapes=True, reComputeFlag=True)
    _importDXF.open(filename)