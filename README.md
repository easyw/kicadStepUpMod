kicadStepUp-WB
==============

![icon](Resources/icons/kicad-StepUp-tools-WB.svg)

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

KiCad **StepUp tools** are a FreeCAD Macro and a FreeCAD WorkBench to help in **Mechanical Collaboration** between **KiCad EDA** and **FreeCAD** or a **Mechanical CAD**.

**KiCad StepUp features:** 

- **load kicad board and parts in FreeCAD and export it to STEP** (or IGES) for a full ECAD MCAD collaboration
- **load kicad_mod footprint in FreeCAD to easy and precisely align the mechanical model to kicad footprint**
- **convert the STEP 3D model of parts, board, enclosure to VRML with Materials properties** for the best use in kicad
- **check interference and collisions** for enclosure and footprint design 
- **design a new pcb Edge with FreeCAD Sketcher and PUSH it to an existing kicad_pcb Board** 
- **PULL a pcb Edge from a kicad_pcb Board**, edit it in FC Sketcher and PUSH it back to kicad
- **design a new footprint in FreeCAD to get the power of Sketch in footprints**
- **generate Blender compatible VRML files**

Please see [KiCad Info forum](https://forum.kicad.info/search?q=step) or [FreeCAD forum](https://forum.freecadweb.org/viewtopic.php?f=24&t=14276) to discuss or report issues regarding this Addon.

![screenshot](https://cdn.hackaday.io/images/7537561443908546062.png)


Installing
----------

Download and install your corresponding version of FreeCAD from [wiki Download page](http://www.freecadweb.org/wiki/Download) and either install

- automatically using the [FreeCAD Add-on Manager](https://github.com/FreeCAD/FreeCAD-addons) (bundled in to 0.17 dev version under Tools Menu)
- manually by copying the kicadStepUpMod folder to the Mod sub-directory of the FreeCAD application.

StepUp Cheat sheet
------------------

[kicad StepUp Cheat sheet](https://github.com/easyw/kicadStepUpMod/raw/master/demo/kicadStepUp-cheat-sheet.pdf)

### Requirements

- **FreeCAD** **0.17 >= 11707**, **0.18**, **0.19**, **0.20**, **0.21**

- **KiCAD** **5.1**, **6.x**, **7 nigthly** (partially supported)

### Known issues

- on Linux FreeCAD Snap and Flatpack you may need to use 'mount bind' to have access to KiCad 3D models path

### License

[GNU AFFERO GENERAL PUBLIC LICENSE](https://www.gnu.org/licenses/agpl-3.0.en.html)
