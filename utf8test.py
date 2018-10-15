#!/usr/bin/python
# -*- coding: utf-8 -*-

import FreeCAD
import sys, os, re

def check_type(input):
    if (sys.version_info > (3, 0)):  #py3
        if isinstance(input, str):
            print('string')
            return
        else:
            print('not string')
            return
    else: #py2
        if type(input) != unicode:
            print('string py2')
            return
        else:
            print('not string py2')
            return

def make_string(input):
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

def make_unicode(input):
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
prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
models3D_prefix = prefs.GetString('prefix3d_1')
print (models3D_prefix)
check_type(models3D_prefix)
pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
last_pcb_path = pg.GetString("last_pcb_path")
print(last_pcb_path)
pg.SetString("last_pcb_path",make_string(models3D_prefix))
print ('writing done')
check_type(last_pcb_path)
model1 = '10rx.wrl'
model_u=u'Würfel1.stp'
fullpath = os.path.join(make_unicode(last_pcb_path), make_unicode(model_u))
#fullpath3 = os.path.join(last_pcb_path, model_u)
print (fullpath)
check_type(fullpath)

newfullpath2 = make_unicode(fullpath)
print (newfullpath2)
check_type(newfullpath2)
if os.path.exists(newfullpath2):
    print('file found MAKE UNICODE')
else:
    print ('ERROR')

#fullpath = re.sub("\\", "/", fullpath)
fullpath = fullpath.replace('\\','/')
print (fullpath)
check_type(fullpath)
if os.path.exists(fullpath):
    print('file found')
else:
    print ('ERROR')
newfullpath = make_string(fullpath)
print (newfullpath)
check_type(newfullpath)
if os.path.exists(newfullpath):
    print('file found')
else:
    print ('ERROR')

fullpath = fullpath.replace('/','\\')
print (fullpath)
check_type(fullpath)
if os.path.exists(fullpath):
    print('file found')
else:
    print ('ERROR')
    
 