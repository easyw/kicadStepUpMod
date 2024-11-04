# -*- coding: utf-8 -*-
# ****************************************************************************


global ksuWBpath
import ksu_locator, os

ksuWBpath = os.path.dirname(ksu_locator.__file__)

# font_color = "<font color=black>"

import FreeCAD, FreeCADGui

# paramGet = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
# if 'dark' in paramGet.GetString("StyleSheet").lower(): #we are using a StyleSheet
# font_color = "<font color=ghostwhite>"
from PySide import QtGui
from TranslateUtils import translate

font_color = "<font color=" + FreeCADGui.getMainWindow().palette().text().color().name() + ">"

# FreeCADGui.getMainWindow().palette().background().color()
# help_txt="""<font color=GoldenRod><b>kicad StepUp version """+verKSU+"""</font></b><br>"""

help_txt = translate(
    "Help",
    "<b>Kicad StepUp</b> is a tool set to easily <b>collaborate between kicad pcb EDA</b> (board and 3D parts) as STEP models <b>and FreeCAD MCAD</b> modeler.<br>\n",
)
help_txt += translate(
    "Help",
    "<b>StepUp</b> can also be used <b>to align 3D model to kicad footprint</b>.<br>\n"
    "The artwork can be used for MCAD interchange and collaboration, and for enclosure design.<br>\n"
    "The 3D visualization of components on board assemblies in kicad 3dviewer, will be the same in your mechanical software, \n"
    "because of the STEP interchange format.<br>\n"
    "It is also possible to <b>Update a pcb Edge from a FC Sketcher.</b><br>\n"
    "<b>configuration options:</b><br>Configuration options are located in the preferences system of FreeCAD, which is located in the Edit menu -&gt; Preferences.<br>\n"
    "Starter Guide: "
    "<a href='https://github.com/easyw/kicadStepUpMod/blob/master/demo/kicadStepUp-cheat-sheet.pdf'  target='_blank'>kicadStepUp-cheat-sheet.pdf</a><br>\n"
    "ECAD-MCAD-collaboration: "
    "<a href='https://github.com/easyw/kicadStepUpMod/blob/master/demo/ECAD-MCAD-collaboration.pdf'  target='_blank'>ECAD-MCAD-collaboration.pdf</a><br><br>\n",
)
# pdf_name = "kicadStepUp-starter-Guide.pdf"
# # help_txt+="starter Guide:<br><a href='"+ksuWBpath+os.sep+"demo"+os.sep+pdf_name+"' target='_blank'>"+pdf_name+"</a><br>"
# help_txt += translate(
#     "Help", "starter Guide:<br><a href='{}demo{}{}' target='_blank'>{}demo{}{}</a><br>"
# ).format(ksuWBpath.rstrip("."), os.sep, pdf_name, ksuWBpath.rstrip("."), os.sep, pdf_name)
# ##   "Help", "starter Guide:<br><a href='{}{}demo{}{}' target='_blank'>{}{}demo{}{}</a><br>"
# html_name = "readme.html"
# help_txt += translate(
#      "Help", "KiCAD StepUp ReadMe:<br><a href='file:///{}{}' target='_blank'>{}{}</a><br>"
#  ).format(ksuWBpath.rstrip("."), html_name, ksuWBpath.rstrip("."), html_name)
help_txt += translate(
    "Help",
    "<b>Note:</b> each button has its own <b>Tooltip</b><br>\n"
    "useful buttons:<br><b>Load kicad Board directly</b> -> will load kicad board and parts in FreeCAD coming from kicad '.kicad_pcb' file<br>\n"
    "<b>Load kicad Footprint module</b> -> will load directly kicad footprint in FreeCAD to easily align the 3D model to footprint<br>\n"
    "<a href='https://youtu.be/eMdX3R9ni7g?t=843'  target='_blank'>Load kicad Footprint module in 3D FreeCAD environment</a><br>\n"
    "<b>Export to kicad STEP & scaled VRML</b> -> will convert MCAD model to STEP and VRML to be used by Kicad and kicad StepUp<br>\n"
    "<b>   -> VRML can be multipart;<br>   -> STEP must be single part</b><br>(<i>'Part Boolean Union'</i> or <i>'Part Makecompound'</i>)<br>\n"
    "<i>assign material to selected colors and your VRML 3D models will have nice shiny effects</i><br>\n"
    "<b>Push pcb Sketch to kicad_pcb Edge</b> -> will push pcb Sketch to kicad_pcb Edge in your design; it can be done with an empty or with an existing pcb Edge<br>\n"
    "<a href='https://youtu.be/eMdX3R9ni7g?t=1050' target='_blank'>Push a complex pcb Sketch from FreeCAD to kicad_pcb Edge board</a>\n"
    "<br>for a more detailed help have a look at <br><b>kicadStepUp-starter-Guide.pdf</b><br>\n"
    "or just follow the <b>YouTube video tutorials</b> <br><a href='https://youtu.be/h6wMU3lE_sA'  target='_blank'>kicadStepUp basics</a><br>\n"
    "<a href='https://youtu.be/O6vr8QFnYGw' target='_blank'>kicadStepUp STEP alignment to Kicad footprint</a><br>"
    "<a href='https://youtu.be/6R6UEUScjgA' target='_blank'>ECAD MCAD Collaboration and Synchronization</a><br>"
    "<a href='https://github.com/easyw/kicadStepUpMod' target='_blank'>check always the latest release of kicadStepUp</a><br>"
    "Designing in kicad native 3d-viewer will produce a fully aligned STEP MCAD version \n"
    "with the same view of kicad 3d render.<br>\n"
    "Moreover, KiCad StepUp tool set <b>will let you to load the kicad footprint inside FreeCAD and align the 3D part with a visual real time feedback \n"
    "of the 3d model and footprint reciprocal position.</b><br>\n"
    "With this tool is possible to download a part from on-line libraries, align the model to kicad footprint \n"
    "and export the model to wrl, for immediate 3d-viewer alignment in pcbnew.<br>\n"
    "Now the two words are connected for a better collaboration; just <b>design in kicad EDA</b> and transfer \n"
    "the artwork to <b>MCAD (FreeCAD)</b> smoothly.<br>\n"
    "<b>The workflow is very simple</b> and maintains the usual way to work with kicad:<br>\n"
    "Add models to your library creating 3D models in FreeCAD, or getting models from online libs \n"
    "or from the parametric 3D lib expressly done to kicad <a href='https://github.com/easyw/kicad-3d-models-in-freecad' target='_blank'>kicadStepUp 3D STEP models generator</a><br>\n"
    "Once you have your 3D MCAD model, <b>you need to have a copy of that in STEP and VRML format.</b> <br>\n"
    "(with the latest kicad release you can only have STEP model, VRML is not needed anymore, but <b>it is possible\n"
    " to mix VRML, STEP and IGES format</b>)<br>\n"
    "Just exporting the model with FreeCAD and put your model in the same folder in which \n"
    "normally you are used to put vrml models; the script will assembly the MCAD board and models as in 3d-viewer of kicad.\n"
    "<br><b>NB<br>STEP model has to be fused in single object</b><br>(Part Boolean Union of objects)\n"
    "<br><b>or a Compoud</b> (Part Makecompound of objects)</b>\n"
    "<hr><b>enable 'Report view' Panel to see helping messages</b>\n"
    "<br>",
)
