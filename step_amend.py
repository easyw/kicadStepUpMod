# -*- coding: utf-8 -*-
# ****************************************************************************
# *  Copyright (c) 2018 Maurice <easyw@katamail.com>                         *
# *                                                                          *
# *  StepZ Import Export compressed STEP files for FreeCAD                   *
# *  License: LGPLv2+                                                        *
# *                                                                          *
# ****************************************************************************

# workaround for unicode in gzipping filename
# OCC7 doesn't support non-ASCII characters at the moment
# https://forum.freecad.org/viewtopic.php?t=20815


# import FreeCAD
# import FreeCADGui
import shutil
import os
import re
# import ImportGui
# import PySide
# from PySide import QtCore
# from PySide import QtGui
import tempfile
import sys

# support both gz and zipfile archives
# Catia seems to use gz, Inventor zipfile
# improved import, open and export


import gzip as gz
import builtins
import importlib
import io

import zipfile as zf

__version__ = "1.0.0"

def transp_rmv(filename):
    
    # sayz(filename)
    found_transp_issue=False
    ext = os.path.splitext(os.path.basename(filename))[1]
    fname = os.path.splitext(os.path.basename(filename))[0]
    basepath = os.path.split(filename)[0]
    if 'stpz' in ext.lower():
        filepath = os.path.join(basepath, fname + ".stp")
        tempdir = tempfile.gettempdir()  # get the current temporary directory
        tempfilepath = os.path.join(tempdir, fname + ".stp")

        if 0: # zf.is_zipfile(filename):
            with zf.ZipFile(filename, "r") as fz:
                file_names = fz.namelist()
                for fn in file_names:
                    # sayz(fn)
                    # with fz.open(fn) as zfile:
                    fiz_content=[]
                    with fz.open(fn) as fiz:
                    # with open(fn, "rb") as fiz:
                        for line in fiz:
                            if (b'SURFACE_STYLE_TRANSPARENT(1.);' in line):
                                line = re.sub(b'SURFACE_STYLE_TRANSPARENT\(1.\)',b'SURFACE_STYLE_TRANSPARENT(0.)',line)
                            fiz_content.append(line)
                            #foz.writestr(line)
                    #with zf.ZipFile(filename, "w") as foz:
                    with zf.ZipFile(filename, "w") as foz:
                        for line in fiz_content:
                            foz.write(line, compress_type=compression)
                    # zf.ZipFile.writestr(filename,fiz_content)  
                    #with zf.ZipFile(filename, "w") as foz:
                    #    foz.write(fiz_content)
            # sayz(tempfilepath + ' zip amended')
        elif 1: #try:
            found_transp_issue=False
            with gz.open(filename, "rb") as figz:
                with gz.open(tempfilepath, 'wb') as fogz:
                    for line in figz:
                        if (b'SURFACE_STYLE_TRANSPARENT(1.);' in line):
                            #print(line)
                            line = re.sub(b'SURFACE_STYLE_TRANSPARENT\(1.\)',b'SURFACE_STYLE_TRANSPARENT(0.)',line)
                            found_transp_issue=True
                            #print(line)
                        fogz.write(line)
            # sayz(tempfilepath + ' gz amended')
            if os.path.exists(filename) and found_transp_issue:
                shutil.move(tempfilepath, filename)
                #sayz(filename + ' written')

        else: # except:
            pass
    elif 'stp' in ext.lower() or 'step' in ext.lower():
        found_transp_issue=False
        filepath = os.path.join(basepath, fname + ext)
        tempdir = tempfile.gettempdir()  # get the current temporary directory
        tempfilepath = os.path.join(tempdir, fname + ext)
        with open(filename, "rb") as fi:
            with open(tempfilepath, 'wb') as fo:
                for line in fi:
                    if (b'SURFACE_STYLE_TRANSPARENT(1.);' in line):
                        #print(line)
                        line = re.sub(b'SURFACE_STYLE_TRANSPARENT\(1.\)',b'SURFACE_STYLE_TRANSPARENT(0.)',line)
                        found_transp_issue=True
                        #print(line)
                    fo.write(line)        
        # sayz(tempfilepath + ' step amended')
        if os.path.exists(filename) and found_transp_issue:
            shutil.move(tempfilepath, filename)
            #sayz(filename + ' written')
    return found_transp_issue
###