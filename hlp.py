# -*- coding: utf-8 -*-
#****************************************************************************


global ksuWBpath
import ksu_locator, os

ksuWBpath = os.path.dirname(ksu_locator.__file__)


#help_txt="""<font color=GoldenRod><b>kicad StepUp version """+verKSU+"""</font></b><br>"""
help_txt="""<font color=black>"""
help_txt+="""<b>Kicad StepUp</b> is a tool set to easily <b>collaborate between kicad pcb EDA</b> (board and 3D parts) as STEP models <b>and FreeCAD MCAD</b> modeler.<br>"""
help_txt+="""</font>"""
help_txt+="<font color=black>"
help_txt+="<b>StepUp</b> can also be used <b>to align 3D model to kicad footprint</b>.<br>"
help_txt+="The artwork can be used for MCAD interchange and collaboration, and for enclosure design.<br>"
help_txt+="The 3D visualization of components on board assemblies in kicad 3dviewer, will be the same in your mechanical software, "
help_txt+="because of the STEP interchange format.<br>"
help_txt+="It is also possible to <b>Update a pcb Edge from a FC Sketcher.</b><br>"
pdf_name='kicadStepUp-starter-Guide.pdf'
help_txt+="<b>configuration options:</b><br>Configuration options are located in the preferences system of FreeCAD, which is located in the Edit menu -&gt; Preferences.<br>"
help_txt+="starter Guide:<br><a href='"+ksuWBpath+os.sep+"demo"+os.sep+pdf_name+"' target='_blank'>"+pdf_name+"</a><br>"
help_txt+="<b>Note:</b> each button has its own <b>Tooltip</b><br>"
help_txt+="useful buttons:<br><b>Load kicad Board directly</b> -> will load kicad board and parts in FreeCAD coming from kicad '.kicad_pcb' file<br>"
help_txt+="<b>Load kicad Footprint module</b> -> will load directly kicad footprint in FreeCAD to easily align the 3D model to footprint<br>"
help_txt+="<b>Export to kicad STEP & scaled VRML</b> -> will convert MCAD model to STEP and VRML to be used by Kicad and kicad StepUp<br>"
help_txt+="<b>   -> VRML can be multipart;<br>   -> STEP must be single part</b><br>(<i>'Part Boolean Union'</i> or <i>'Part Makecompound'</i>)<br>"
help_txt+="<i>assign material to selected colors and your VRML 3D models will have nice shiny effects</i><br>"
help_txt+="<b>Push pcb Sketch to kicad_pcb Edge</b> -> will push pcb Sketch to kicad_pcb Edge in your design; it can be done with an empty or with an existing pcb Edge<br>"
help_txt+="<br>for a more detailed help have a look at <br><b>kicadStepUp-starter-Guide.pdf</b><br>"
help_txt+="or just follow the <b>YouTube video tutorials</b> <br><a href='https://youtu.be/h6wMU3lE_sA'  target='_blank'>kicadStepUp basics</a><br>"
help_txt+="<a href='https://youtu.be/O6vr8QFnYGw' target='_blank'>kicadStepUp STEP alignment to Kicad footprint</a><br>"
help_txt+="<a href='https://github.com/easyw/kicadStepUpMod' target='_blank'>check always the latest release of kicadStepUp</a><br><br>"
help_txt+="Designing in kicad native 3d-viewer will produce a fully aligned STEP MCAD version "
help_txt+="with the same view of kicad 3d render.<br>"
help_txt+="Moreover, KiCad StepUp tool set <b>will let you to load the kicad footprint inside FreeCAD and align the 3D part with a visual real time feedback "
help_txt+="of the 3d model and footprint reciprocal position.</b><br>"
help_txt+="With this tool is possible to download a part from on-line libraries, align the model to kicad footprint "
help_txt+="and export the model to wrl, for immediate 3d-viewer alignment in pcbnew.<br>"
help_txt+="Now the two words are connected for a better collaboration; just <b>design in kicad EDA</b> and transfer "
help_txt+="the artwork to <b>MCAD (FreeCAD)</b> smoothly.<br>"
help_txt+="<b>The workflow is very simple</b> and maintains the usual way to work with kicad:<br>"
help_txt+="Add models to your library creating 3D models in FreeCAD, or getting models from online libs "
help_txt+="or from the parametric 3D lib expressly done to kicad <a href='https://github.com/easyw/kicad-3d-models-in-freecad' target='_blank'>kicadStepUp 3D STEP models generator</a><br>"
help_txt+="Once you have your 3D MCAD model, <b>you need to have a copy of that in STEP and VRML format.</b> <br>"
help_txt+="(with the latest kicad release you can only have STEP model, VRML is not needed anymore, but <b>it is possible"
help_txt+=" to mix VRML, STEP and IGES format</b>)<br>"        
help_txt+="Just exporting the model with FreeCAD and put your model in the same folder in which "
help_txt+="normally you are used to put vrml models; the script will assembly the MCAD board and models as in 3d-viewer of kicad."       
help_txt+="<br><b>NB<br>STEP model has to be fused in single object</b><br>(Part Boolean Union of objects)"
help_txt+="<br><b>or a Compoud</b> (Part Makecompound of objects)</b>"
help_txt+="<hr><b>enable 'Report view' Panel to see helping messages</b>"
help_txt+="</font><br>"
  