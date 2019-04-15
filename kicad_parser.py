#!/usr/bin/python
# -*- coding: utf-8 -*-
#****************************************************************************

from __future__ import (absolute_import, division,
        print_function, unicode_literals)
#from builtins import *
# from future.utils import iteritems

from collections import defaultdict
from math import sqrt, atan2, degrees, sin, cos, radians, pi, hypot
import traceback
import FreeCAD
import FreeCADGui
import Part
from FreeCAD import Console,Vector,Placement,Rotation
import DraftGeomUtils,DraftVecUtils
import Path

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from kicadStepUptools import KicadPCB,SexpList

__kicad_parser_version__ = '1.1.2'
print('kicad_parser_version '+__kicad_parser_version__)


try:  #maui
  basestring
except NameError:
  basestring = str
try:  #maui
    xrange
except NameError:
    xrange = range
    

def updateGui():
    try:
        FreeCADGui.updateGui()
    except Exception:
        pass

class FCADLogger:
    def __init__(self, tag):
        self.tag = tag
        self.levels = { 'error':0, 'warning':1, 'info':2,
                'log':3, 'trace':4 }

    def _isEnabledFor(self,level):
        return FreeCAD.getLogLevel(self.tag) >= level

    def isEnabledFor(self,level):
        return self._isEnabledFor(self.levels[level])

    def trace(self,msg):
        if self._isEnabledFor(4):
            FreeCAD.Console.PrintLog(msg+'\n')
            updateGui()

    def log(self,msg):
        if self._isEnabledFor(3):
            FreeCAD.Console.PrintLog(msg+'\n')
            updateGui()

    def info(self,msg):
        if self._isEnabledFor(2):
            FreeCAD.Console.PrintMessage(msg+'\n')
            updateGui()

    def warning(self,msg):
        if self._isEnabledFor(1):
            FreeCAD.Console.PrintWarning(msg+'\n')
            updateGui()

    def error(self,msg):
        if self._isEnabledFor(0):
            FreeCAD.Console.PrintError(msg+'\n')
            updateGui()

logger = FCADLogger('fcad_pcb')

def getActiveDoc():
    if FreeCAD.ActiveDocument is None:
        return FreeCAD.newDocument('kicad_fcad')
    return FreeCAD.ActiveDocument

def fitView():
    try:
        FreeCADGui.ActiveDocument.ActiveView.fitAll()
    except Exception:
        pass

def isZero(f):
    return round(f,DraftGeomUtils.precision())==0

def makeColor(*color):
    if len(color)==1:
        if isinstance(color[0],basestring):
            color = int(color[0],0)
        else:
            color = color[0]
        r = float((color>>24)&0xFF)
        g = float((color>>16)&0xFF)
        b = float((color>>8)&0xFF)
    else:
        r,g,b = color
    return (r/255.0,g/255.0,b/255.0)

def makeVect(l):
    return Vector(l[0],-l[1],0)

def getAt(at):
    v = makeVect(at)
    return (v,0) if len(at)==2 else (v,at[2])

def product(v1,v2):
    return Vector(v1.x*v2.x,v1.y*v2.y,v1.z*v2.z)

def make_rect(size,params=None):
    _ = params 
    return Part.makePolygon([product(size,Vector(*v))
        for v in ((-0.5,-0.5),(0.5,-0.5),(0.5,0.5),(-0.5,0.5),(-0.5,-0.5))])

def make_circle(size,params=None):
    _ = params
    return Part.Wire(Part.makeCircle(size.x*0.5))

def make_oval(size,params=None):
    _ = params
    if size.x == size.y:
        return make_circle(size)
    if size.x < size.y:
        r = size.x*0.5
        size.y -= size.x
        s  = ((0,0.5),(-0.5,0.5),(-0.5,-0.5),(0,-0.5),(0.5,-0.5),(0.5,0.5))
        a = (0,180,180,360)
    else:
        r = size.y*0.5
        size.x -= size.y
        s = ((-0.5,0),(-0.5,-0.5),(0.5,-0.5),(0.5,0),(0.5,0.5),(-0.5,0.5))
        a = (90,270,-90,-270)
    pts = [product(size,Vector(*v)) for v in s]
    return Part.Wire([
            Part.makeCircle(r,pts[0],Vector(0,0,1),a[0],a[1]),
            Part.makeLine(pts[1],pts[2]),
            Part.makeCircle(r,pts[3],Vector(0,0,1),a[2],a[3]),
            Part.makeLine(pts[4],pts[5])])

def make_roundrect(size,params):
    rratio = 0.25
    try:
        rratio = params.roundrect_rratio
        if rratio >= 0.5:
            return make_oval(size)
    except Exception:
        logger.warning('round rect pad has no rratio')

    if size.x < size.y:
        r = size.x*rratio
    else:
        r = size.y*rratio
    n = Vector(0,0,1)
    sx = size.x*0.5
    sy = size.y*0.5
    return Part.Wire([
            Part.makeCircle(r,Vector(sx-r,sy-r),n,0,90),
            Part.makeLine(Vector(sx-r,sy),Vector(r-sx,sy)),
            Part.makeCircle(r,Vector(r-sx,sy-r),n,90,180),
            Part.makeLine(Vector(-sx,sy-r),Vector(-sx,r-sy)),
            Part.makeCircle(r,Vector(r-sx,r-sy),n,180,270),
            Part.makeLine(Vector(r-sx,-sy),Vector(sx-r,-sy)),
            Part.makeCircle(r,Vector(sx-r,r-sy),n,270,360),
            Part.makeLine(Vector(sx,r-sy),Vector(sx,sy-r))])

def make_custom(size,params):
    _ = size
    width = 0
    try:
        pts = params.primitives.gr_poly.pts
        if 'width' in pts:
            width = pts.width
        points = SexpList(pts.xy)
        # close the polygon
        points._append(pts.xy._get(0))
        logger.info('polyline points: {}'.format(len(points)))
    except Exception:
        raise RuntimeError('Cannot find polyline points in custom pad')

    wire = Part.makePolygon([makeVect(p) for p in points])
    if width:
        wire = Path.Area(Offset=width*0.5).add(wire).getShape()
    return wire


def makeThickLine(p1,p2,width):
    length = p1.distanceToPoint(p2)
    line = make_oval(Vector(length+2*width,2*width))
    p = p2.sub(p1)
    a = -degrees(DraftVecUtils.angle(p))
    line.translate(Vector(length*0.5))
    line.rotate(Vector(),Vector(0,0,1),a)
    line.translate(p1)
    return line

def makeArc(center,start,angle):
    p = start.sub(center)
    r = p.Length
    a = -degrees(DraftVecUtils.angle(p))
    # NOTE: KiCAD pcb geometry runs in clockwise, while FreeCAD is CCW. So the
    # resulting arc below is the reverse of what's specified in kicad_pcb
    arc = Part.makeCircle(r,center,Vector(0,0,1),a-angle,a)
    arc.reverse();
    return arc

def findWires(edges):
    try:
        return [Part.Wire(e) for e in Part.sortEdges(edges)]
    except AttributeError:
        msg = 'Missing Part.sortEdges.'\
            'You need newer FreeCAD (0.17 git 799c43d2)'
        logger.error(msg)
        raise AttributeError(msg)

def getFaceCompound(shape,wire=False):
    objs = []
    for f in shape.Faces:
        selected = True
        for v in f.Vertexes:
            if not isZero(v.Z):
                selected = False
                break
        if not selected:
            continue

        ################################################################
        ## TODO: FreeCAD curve.normalAt is not implemented
        ################################################################
        # for e in f.Edges:
            # if isinstance(e.Curve,(Part.LineSegment,Part.Line)): continue
            # if not isZero(e.normalAt(Vector()).dot(Vector(0,0,1))):
                # selected = False
                # break
        # if not selected: continue

        if not wire:
            objs.append(f)
            continue
        for w in f.Wires:
            objs.append(w)
    if not objs:
        raise ValueError('null shape')
    return Part.makeCompound(objs)


def unpack(obj):
    if not obj:
        raise ValueError('null shape')

    if isinstance(obj,(list,tuple)) and len(obj)==1:
        return obj[0]
    return obj


def getKicadPath():
    if sys.platform != 'win32':
        path='/usr/share/kicad/modules/packages3d'
        if not os.path.isdir(path):
            path = '/usr/local/share/kicad/modules/packages3d'
        return path

    import re
    confpath = os.path.join(os.path.abspath(os.environ['APPDATA']),'kicad')
    kicad_common = os.path.join(confpath,'kicad_common')
    if not os.path.isfile(kicad_common):
        logger.warning('cannot find kicad_common')
        return None
    with open(kicad_common,'rb') as f:
        content = f.read()
    match = re.search(r'^\s*KISYS3DMOD\s*=\s*([^\r\n]+)',content,re.MULTILINE)
    if not match:
        logger.warning('no KISYS3DMOD found')
        return None

    return match.group(1).rstrip(' ')

_model_cache = {}

def clearModelCache():
    _model_cache = {}

def recomputeObj(obj):
    obj.recompute()
    obj.purgeTouched()

def loadModel(filename):
    mtime = None
    try:
        mtime = os.path.getmtime(filename)
        obj = _model_cache[filename]
        if obj[2] == mtime:
            logger.info('model cache hit');
            return obj
        else:
            logger.info('model reload due to time stamp change');
    except KeyError:
        pass
    except OSError:
        return

    import ImportGui
    doc = getActiveDoc()
    if not os.path.isfile(filename):
        return
    count = len(doc.Objects)
    dobjs = []
    try:
        ImportGui.insert(filename,doc.Name)
        dobjs = doc.Objects[count:]
        obj = doc.addObject('Part::Compound','tmp')
        obj.Links = dobjs
        recomputeObj(obj)
        dobjs = [obj]+dobjs
        obj = (obj.Shape.copy(),obj.ViewObject.DiffuseColor,mtime)
        _model_cache[filename] = obj
        return obj
    except Exception as ex:
        logger.error('failed to load model: {}'.format(ex))
    finally:
        for o in dobjs:
            doc.removeObject(o.Name)

class KicadFcad:
    def __init__(self,filename=None,debug=False,**kwds):
        self.prefix = ''
        self.indent = '  '
        self.make_sketch = False
        self.sketch_use_draft = False
        self.sketch_radius_precision = -1
        self.holes_cache = {}
        self.work_plane = Part.makeCircle(1)
        self.active_doc_uuid = None
        self.sketch_constraint = True
        self.sketch_align_constraint = False
        self.merge_holes = not debug
        self.merge_pads = not debug
        self.merge_vias = not debug
        self.zone_merge_holes = not debug
        self.add_feature = True
        ## self.part_path = getKicadPath() # maui not used
        self.hole_size_offset = 0.001
        if filename is None:
            filename = '/home/thunder/pwr.kicad_pcb'
        if not os.path.isfile(filename):
            raise ValueError("file not found");
        self.filename = filename
        self.colors = {
                'board':makeColor("0x3A6629"),
                'pad':{0:makeColor(219,188,126)},
                'zone':{0:makeColor(200,117,51)},
                'track':{0:makeColor(200,117,51)},
                'copper':{0:makeColor(200,117,51)},
        }
        #'pad':{0:makeColor(204,204,204)}, 'pad':{0:makeColor(102,70,0)}, 'pad':{0:makeColor(179,68,21)},
        #'zone':{0:makeColor(0,80,0)}, 'zone':{0:makeColor(199,144,28)},
        #'track':{0:makeColor(0,120,0)},
        self.layer_type = 0

        for key,value in dict.items(kwds): #iteritems(kwds):  #maui
            if not hasattr(self,key):
                raise ValueError('unknown parameter "{}"'.format(key))
            setattr(self,key,value)

        self.pcb = KicadPCB.load(self.filename)

        # This will be override by setLayer. It's here just to make syntax
        # checker happy
        self.layer = 'F.Cu'

        self.setLayer(self.layer_type)

    def setLayer(self,layer):
        #print(layer)
        # print(self.pcb.layers)
        try:
            layer = int(layer)
        except:
            for layer_type in self.pcb.layers:
                if self.pcb.layers[layer_type][0] == layer:
                # if layer in self.pcb.layers[layer_type][0]:
                    self.layer = layer
                    self.layer_type = int(layer_type)
                    return
            raise KeyError('layer {} not found'.format(layer))
        else:
            if str(layer) not in self.pcb.layers:
                raise KeyError('layer {} not found'.format(layer))
            self.layer_type = layer
            self.layer = self.pcb.layers[str(layer)][0]


    def _log(self,msg,*arg,**kargs):
        level = 'info'
        if kargs:
            if 'level' in kargs:
                level = kargs['level']
        if logger.isEnabledFor(level):
            getattr(logger,level)('{}{}'.format(self.prefix,msg.format(*arg)))


    def _pushLog(self,msg=None,*arg,**kargs):
        if msg:
            self._log(msg,*arg,**kargs)
        if 'prefix' in kargs:
            prefix = kargs['prefix']
            if prefix is not None:
                self.prefix = prefix
        self.prefix += self.indent


    def _popLog(self,msg=None,*arg,**kargs):
        self.prefix = self.prefix[:-len(self.indent)]
        if msg:
            self._log(msg,*arg,**kargs)

    def _makeLabel(self,obj,label):
        if self.layer:
            obj.Label = '{}#{}'.format(obj.Name,self.layer)
        if label is not None:
            obj.Label += '#{}'.format(label)

    def _makeObject(self,otype,name,
            label=None,links=None,shape=None):
        doc = getActiveDoc()
        obj = doc.addObject(otype,name)
        self._makeLabel(obj,label)
        if links is not None:
            setattr(obj,links,shape)
            for s in shape if isinstance(shape,(list,tuple)) else (shape,):
                if hasattr(s,'ViewObject'):
                    s.ViewObject.Visibility = False
            if hasattr(obj,'recompute'):
                recomputeObj(obj)
        return obj

    def _makeSketch(self,objs,name,label=None):
        if self.sketch_use_draft:
            import Draft
            getActiveDoc()
            nobj = Draft.makeSketch(objs,name=name,autoconstraints=True,
                delete=True,radiusPrecision=self.sketch_radius_precision)
            self._makeLabel(nobj,label)
            return nobj

        from Sketcher import Constraint

        StartPoint = 1
        EndPoint = 2

        doc = getActiveDoc()

        nobj = doc.addObject("Sketcher::SketchObject", '{}_sketch'.format(name))
        self._makeLabel(nobj,label)
        nobj.ViewObject.Autoconstraints = False

        radiuses = {}
        constraints = []

        def addRadiusConstraint(edge):
            try:
                if self.sketch_radius_precision<0:
                    return
                if self.sketch_radius_precision==0:
                    constraints.append(Constraint('Radius',
                            nobj.GeometryCount-1, edge.Curve.Radius))
                    return
                r = round(edge.Curve.Radius,self.sketch_radius_precision)
                constraints.append(Constraint('Equal',
                    radiuses[r], nobj.GeometryCount-1))
            except KeyError:
                radiuses[r] = nobj.GeometryCount-1
                constraints.append(Constraint('Radius',nobj.GeometryCount-1,r))
            except AttributeError:
                pass

        for obj in objs if isinstance(objs,(list,tuple)) else (objs,):
            if isinstance(obj,Part.Shape):
                shape = obj
            else:
                shape = obj.Shape
            norm = DraftGeomUtils.getNormal(shape)
            if not self.sketch_constraint:
                for wire in shape.Wires:
                    for edge in wire.OrderedEdges:
                        nobj.addGeometry(DraftGeomUtils.orientEdge(
                            edge,norm,make_arc=True))
                continue

            for wire in shape.Wires:
                last_count = nobj.GeometryCount
                edges = wire.OrderedEdges
                for edge in edges:
                    nobj.addGeometry(DraftGeomUtils.orientEdge(
                        edge,norm,make_arc=True))

                    addRadiusConstraint(edge)

                for i,g in enumerate(nobj.Geometry[last_count:]):
                    if edges[i].Closed:
                        continue
                    seg = last_count+i
                    if self.sketch_align_constraint:
                        if DraftGeomUtils.isAligned(g,"x"):
                            constraints.append(Constraint("Vertical",seg))
                        elif DraftGeomUtils.isAligned(g,"y"):
                            constraints.append(Constraint("Horizontal",seg))

                    if seg == nobj.GeometryCount-1:
                        if not wire.isClosed():
                            break
                        g2 = nobj.Geometry[last_count]
                        seg2 = last_count
                    else:
                        seg2 = seg+1
                        g2 = nobj.Geometry[seg2]

                    end1 = g.value(g.LastParameter)
                    start2 = g2.value(g2.FirstParameter)
                    if DraftVecUtils.equals(end1,start2) :
                        constraints.append(Constraint(
                            "Coincident",seg,EndPoint,seg2,StartPoint))
                        continue
                    end2 = g2.value(g2.LastParameter)
                    start1 = g.value(g.FirstParameter)
                    if DraftVecUtils.equals(end2,start1):
                        constraints.append(Constraint(
                            "Coincident",seg,StartPoint,seg2,EndPoint))
                    elif DraftVecUtils.equals(start1,start2):
                        constraints.append(Constraint(
                            "Coincident",seg,StartPoint,seg2,StartPoint))
                    elif DraftVecUtils.equals(end1,end2):
                        constraints.append(Constraint(
                            "Coincident",seg,EndPoint,seg2,EndPoint))

            if obj.isDerivedFrom("Part::Feature"):
                objs = [obj]
                while objs:
                    obj = objs[0]
                    objs = objs[1:] + obj.OutList
                    doc.removeObject(obj.Name)

        nobj.addConstraint(constraints)
        recomputeObj(nobj)
        return nobj

    def _makeCompound(self,obj,name,label=None,fit_arcs=False,
            fuse=False,add_feature=False,force=False):

        obj = unpack(obj)
        if not isinstance(obj,(list,tuple)):
            if not force and (
               not fuse or obj.TypeId=='Path::FeatureArea'):
                return obj
            obj = [obj]

        if fuse:
            return self._makeArea(obj,name,label=label,fit_arcs=fit_arcs)

        if add_feature or self.add_feature:
            return self._makeObject('Part::Compound',
                    '{}_combo'.format(name),label,'Links',obj)

        return Part.makeCompound(obj)


    def _makeArea(self,obj,name,offset=0,op=0,fill=None,label=None,
                force=False,fit_arcs=False,reorient=False,workplane=False):
        if fill is None:
            fill = 2
        elif fill:
            fill = 1
        else:
            fill = 0

        if not isinstance(obj,(list,tuple)):
            obj = (obj,)

        if self.add_feature:

            if not force and obj[0].TypeId == 'Path::FeatureArea' and (
                obj[0].Operation == op or len(obj[0].Sources)==1) and \
                obj[0].Fill == fill:

                ret = obj[0]
                if len(obj) > 1:
                    ret.Sources = list(ret.Sources) + list(obj[1:])
            else:
                if name != 'copper':  #maui to avoid makefacebullseye
                    ret = self._makeObject('Path::FeatureArea',
                                            '{}_area'.format(name),label)
                    ret.Sources = obj
                    ret.Operation = op
                    ret.Fill = fill
                    ret.Offset = offset
                    ret.Coplanar = 0
                    if workplane:
                        ret.WorkPlane = self.work_plane
                    ret.FitArcs = fit_arcs
                    ret.Reorient = reorient
                    for o in obj:
                        o.ViewObject.Visibility = False
                else:  #maui make compound
                    # if self.layer == 'F.Cu':
                    if 'F.Cu' in self.layer:
                        deltaz = 0.02 # 20 micron
                    else:
                        deltaz = -0.02 # 20 micron
                    FreeCAD.activeDocument().addObject("Part::Compound",'{}_area'.format(name))
                    for o in obj:
                        if 'pads' in o.Label:
                            o.Placement.Base.z+=2*deltaz
                        if 'zone' in o.Label:
                            o.Placement.Base.z+=deltaz
                    FreeCAD.activeDocument().ActiveObject.Links = obj
                    ret = FreeCAD.activeDocument().ActiveObject
            recomputeObj(ret)
        else:
            ret = Path.Area(Fill=fill,FitArcs=fit_arcs,Coplanar=0)
            if workplane:
                ret.setPlane(self.work_plane)
            for o in obj:
                ret.add(o,op=op)
            if offset:
                ret = ret.makeOffset(offset=offset)
            else:
                ret = ret.getShape()
        return ret


    def _makeWires(self,obj,name,offset=0,fill=False,label=None,
            fit_arcs=False,workplane=False):

        if self.add_feature:
            if self.make_sketch:
                obj = self._makeSketch(obj,name,label)
            elif isinstance(obj,Part.Shape):
                obj = self._makeObject('Part::Feature', '{}_wire'.format(name),
                        label,'Shape',obj)
            elif isinstance(obj,(list,tuple)):
                objs = []
                comp = []
                for o in obj:
                    if isinstance(o,Part.Shape):
                        comp.append(o)
                    else:
                        objs.append(o)
                if comp:
                    comp = Part.makeCompound(comp)
                    objs.append(self._makeObject('Part::Feature',
                            '{}_wire'.format(name),label,'Shape',comp))
                obj = objs

        if fill or offset:
            return self._makeArea(obj,name,offset=offset,fill=fill,
                    fit_arcs=fit_arcs,label=label,workplane=workplane)
        else:
            return self._makeCompound(obj,name,label=label)


    def _makeSolid(self,obj,name,height,label=None,fit_arcs=True):

        obj = self._makeCompound(obj,name,label=label,
                                    fuse=True,fit_arcs=fit_arcs)

        if not self.add_feature:
            return obj.extrude(Vector(0,0,height))

        nobj = self._makeObject('Part::Extrusion',
                                    '{}_solid'.format(name),label)
        nobj.Base = obj
        nobj.Dir = Vector(0,0,height)
        obj.ViewObject.Visibility = False
        recomputeObj(nobj)
        return nobj


    def _makeFuse(self,objs,name,label=None,force=False):
        obj = unpack(objs)
        if not isinstance(obj,(list,tuple)):
            if not force:
                return obj
            obj = [obj]

        name = '{}_fuse'.format(name)

        if self.add_feature:
            self._log('making fuse {}...',name)
            obj =  self._makeObject('Part::MultiFuse',name,label,'Shapes',obj)
            self._log('fuse done')
            return obj

        solids = []
        for o in obj:
            solids += o.Solids;

        if solids:
            self._log('making fuse {}...',name)
            obj = solids[0].multiFuse(solids[1:])
            self._log('fuse done')
            return obj


    def _makeCut(self,base,tool,name,label=None):
        base = self._makeFuse(base,name,label=label)
        tool = self._makeFuse(tool,'drill',label=label)
        name = '{}_drilled'.format(name)
        self._log('making cut {}...',name)
        if self.add_feature:
            cut = self._makeObject('Part::Cut',name,label=label)
            cut.Base = base
            cut.Tool = tool
            base.ViewObject.Visibility = False
            tool.ViewObject.Visibility = False
            recomputeObj(cut)
            cut.ViewObject.ShapeColor = base.ViewObject.ShapeColor
        else:
            cut = base.cut(tool)
        self._log('cut done')
        return cut


    def _place(self,obj,pos,angle=None):
        if not self.add_feature:
            if angle:
                obj.rotate(Vector(),Vector(0,0,1),angle)
            obj.translate(pos)
        else:
            r = Rotation(Vector(0,0,1),angle) if angle else Rotation()
            obj.Placement = Placement(pos,r)
            obj.purgeTouched()


    def makeBoard(self,shape_type='solid',thickness=None,fit_arcs=True,
            holes=True, minHoleSize=0,ovalHole=True,prefix=''):

        edges = []

        self._pushLog('making board...',prefix=prefix)
        self._log('making {} lines',len(self.pcb.gr_line))
        for l in self.pcb.gr_line:
            if l.layer != 'Edge.Cuts':
                continue
            edges.append(Part.makeLine(makeVect(l.start),makeVect(l.end)))

        self._log('making {} arcs',len(self.pcb.gr_arc))
        for l in self.pcb.gr_arc:
            if l.layer != 'Edge.Cuts':
                continue
            # for gr_arc, 'start' is actual the center, and 'end' is the start
            edges.append(makeArc(makeVect(l.start),makeVect(l.end),l.angle))

        if not edges:
            self._popLog('no board edges found')
            return

        wires = findWires(edges)

        if not thickness:
            thickness = self.pcb.general.thickness

        holes = self._cutHoles(None,holes,None,
                        minSize=minHoleSize,oval=ovalHole)

        def _wire(fill=False):
            obj = self._makeWires(wires,'board',fill=fill)
            if not holes:
                return obj

            return self._makeArea((obj,holes),'board',
                            op=1,fill=fill,fit_arcs=fit_arcs)

        def _face():
            return _wire(True)

        def _solid():
            return self._makeSolid(_face(),'board',thickness,
                    fit_arcs = fit_arcs)

        try:
            func = locals()['_{}'.format(shape_type)]
        except KeyError:
            raise ValueError('invalid shape type: {}'.format(shape_type))

        obj = func()
        if self.add_feature:
            if hasattr(obj.ViewObject,'MapFaceColor'):
                obj.ViewObject.MapFaceColor = False
            obj.ViewObject.ShapeColor = self.colors['board']

        self._popLog('board done')
        fitView();
        return obj


    def makeHoles(self,shape_type='wire',minSize=0,maxSize=0,
            oval=False,prefix='',offset=0.0,npth=0,thickness=None):

        self._pushLog('making holes...',prefix=prefix)

        holes = defaultdict(list)
        ovals = defaultdict(list)

        width=0
        def _wire(obj,name,fill=False):
            return self._makeWires(obj,name,fill=fill,label=width)

        def _face(obj,name):
            return _wire(obj,name,True)

        def _solid(obj,name):
            return self._makeWires(obj,name,fill=True,label=width,fit_arcs=True)

        try:
            func = locals()['_{}'.format(shape_type)]
        except KeyError:
            raise ValueError('invalid shape type: {}'.format(shape_type))

        oval_count = 0
        count = 0
        skip_count = 0
        if not offset:
            offset = self.hole_size_offset;
        for m in self.pcb.module:
            m_at,m_angle = getAt(m.at)
            for p in m.pad:
                if 'drill' not in p:
                    continue
                if p[1]=='np_thru_hole':
                    if npth<0:
                        skip_count += 1
                        continue
                    ofs = abs(offset)
                else:
                    if npth>0:
                        skip_count += 1
                        continue
                    ofs = -abs(offset)
                drill_present=False  #maui
                #print (p.drill)
                try:
                    tmp=p.drill[0]
                    drill_present=True
                except:
                    print('drill size missing');
                if drill_present:
                    #print (p.drill)
                    if 'oval' in str(p.drill).split(',')[0]:  #py3 dict workaround
                    #if p.drill.oval:
                        if not oval:
                            continue
                        try:
                            #print (p.drill[1])
                            #stop
                            size = Vector(p.drill[0],p.drill[1])
                        except:
                            size = Vector(p.drill[0],p.drill[0])                       
                        #size = Vector(p.drill[0],p.drill[1])
                        w = make_oval(size+Vector(ofs,ofs))
                        ovals[min(size.x,size.y)].append(w)
                        oval_count += 1
                    elif p.drill[0]>=minSize and \
                            (not maxSize or p.drill[0]<=maxSize):
                        w = make_circle(Vector(p.drill[0]+ofs))
                        holes[p.drill[0]].append(w)
                        count += 1
                    else:
                        skip_count += 1
                        continue
                else:
                    skip_count += 1
                    continue
                at,angle = getAt(p.at)
                angle -= m_angle;
                if not isZero(angle):
                    w.rotate(Vector(),Vector(0,0,1),angle)
                w.translate(at)
                if m_angle:
                    w.rotate(Vector(),Vector(0,0,1),m_angle)
                w.translate(m_at)
        self._log('pad holes: {}, skipped: {}',count+skip_count,skip_count)
        if oval:
            self._log('oval holes: {}',oval_count)

        if npth<=0:
            skip_count = 0
            ofs = -abs(offset)
            for v in self.pcb.via:
                drill_present=False  #maui
                try:
                    tmp=v.drill
                    drill_present=True
                except:
                    print('drill size missing');
                if drill_present:
                    #print (p.drill)
                    ##if 'oval' in str(p.drill).split(',')[0]:  #py3 dict workaround
                    if v.drill>=minSize and (not maxSize or v.drill<=maxSize):
                        w = make_circle(Vector(v.drill+ofs))
                        holes[v.drill].append(w)
                        w.translate(makeVect(v.at))
                    else:
                        skip_count += 1
                else:
                    skip_count += 1
            self._log('via holes: {}, skipped: {}',len(self.pcb.via),skip_count)

        self._log('total holes added: {}',
                count+oval_count+len(self.pcb.via)-skip_count)

        objs = []
        if holes or ovals:
            if self.merge_holes:
                for o in ovals.values():
                    objs += o
                for o in holes.values():
                    objs += o
                objs = func(objs,"holes")
            else:
                for r in ((ovals,'oval'),(holes,'hole')):
                    if not r[0]:
                        continue
                    for (width,rs) in dict.items(r[0]): #iteritems(r[0]):  #maui
                        objs.append(func(rs,r[1]))

            if not npth:
                label=None
            elif npth>0:
                label='npth'
            else:
                label='th'

            if shape_type == 'solid':
                if not thickness:
                    thickness = self.pcb.general.thickness+0.02
                    pos = -0.01
                else:
                    pos = 0.0
                objs = self._makeSolid(objs,'holes',thickness,label=label)
                self._place(objs,FreeCAD.Vector(0,0,pos))
            else:
                objs = self._makeCompound(objs,'holes',label=label)

        self._popLog('holes done')
        return objs


    def _cutHoles(self,objs,holes,name,label=None,fit_arcs=False,
                    minSize=0,maxSize=0,oval=True,npth=0,offset=0.0):
        if not holes:
            return objs

        if not isinstance(holes,(Part.Feature,Part.Shape)):
            hit = False
            if self.holes_cache is not None:
                key = '{}.{}.{}.{}.{}.{}'.format(
                        self.add_feature,minSize,maxSize,oval,npth,offset)
                doc = getActiveDoc();
                if self.add_feature and self.active_doc_uuid!=doc.Uid:
                    self.holes_cache.clear()
                    self.active_doc_uuid = doc.Uid

                try:
                    holes = self.holes_cache[key]
                    if self.add_feature:
                        # access the object's Name to make sure it is not
                        # deleted
                        self._log("fetch holes '{}' "
                            "from cache".format(holes.Name))
                    else:
                        self._log("fetch holes from cache")
                    hit = True
                except Exception:
                    pass

            if not hit:
                self._pushLog()
                holes = self.makeHoles(shape_type='wire',prefix=None,npth=npth,
                    minSize=minSize,maxSize=maxSize,oval=oval,offset=offset)
                self._popLog()

                if isinstance(self.holes_cache,dict):
                    self.holes_cache[key] = holes

        if not objs:
            return holes

        objs = (self._makeCompound(objs,name,label=label),holes)
        return self._makeArea(objs,name,op=1,label=label,fit_arcs=fit_arcs)


    def makePads(self,shape_type='face',thickness=0.05,holes=False,
            fit_arcs=True,prefix=''):

        self._pushLog('making pads...',prefix=prefix)

        def _wire(obj,name,label=None,fill=False):
            return self._makeWires(obj,name,fill=fill,label=label)

        def _face(obj,name,label=None):
            return _wire(obj,name,label,True)

        _solid = _face

        try:
            func = locals()['_{}'.format(shape_type)]
        except KeyError:
            raise ValueError('invalid shape type: {}'.format(shape_type))

        # print('layer...',self.layer)
        
        layer_match = '*.{}'.format(self.layer.replace('"','').split('.')[-1]) #removing extra double quotes from layer

        objs = []

        count = 0
        skip_count = 0
        for i,m in enumerate(self.pcb.module):
            ref = ''
            for t in m.fp_text:
                if t[0] == 'reference':
                    ref = t[1]
                    break;
            m_at,m_angle = getAt(m.at)
            pads = []
            count += len(m.pad)
            for j,p in enumerate(m.pad):
                try:
                    if self.layer not in p.layers \
                        and layer_match not in p.layers \
                        and '*' not in p.layers:
                        skip_count+=1
                        continue
                except:
                    skip_count+=1
                    continue
                #for pd in m.pad:
                #    print(pd)
                if self.layer not in p.layers \
                    and layer_match not in p.layers \
                    and '*' not in p.layers:
                    skip_count+=1
                    continue
                shape = p[2]
                #print(shape)
                if shape == 'trapezoid': #maui
                    shape= 'rect'
                    logger.warning('trapezoid pad converted to rect')
                try:
                    make_shape = globals()['make_{}'.format(shape)]
                except KeyError:
                    raise NotImplementedError(
                            'pad shape {} not implemented\n'.format(shape))

                w = make_shape(Vector(*p.size),p)
                at,angle = getAt(p.at)
                angle -= m_angle;
                if not isZero(angle):
                    w.rotate(Vector(),Vector(0,0,1),angle)
                w.translate(at)
                if not self.merge_pads:
                    pads.append(func(w,'pad',
                        '{}#{}#{}#{}'.format(i,j,p[0],ref)))
                else:
                    pads.append(w)

            if not pads:
                continue

            if not self.merge_pads:
                obj = self._makeCompound(pads,'pads','{}#{}'.format(i,ref))
            else:
                obj = func(pads,'pads','{}#{}'.format(i,ref))
            self._place(obj,m_at,m_angle)
            objs.append(obj)

        via_skip = 0
        vias = []
        for i,v in enumerate(self.pcb.via):
            if self.layer not in v.layers:
                via_skip += 1
                continue
            w = make_circle(Vector(v.size))
            w.translate(makeVect(v.at))
            if not self.merge_vias:
                vias.append(func(w,'via','{}#{}'.format(i,v.size)))
            else:
                vias.append(w)

        if vias:
            if self.merge_vias:
                objs.append(func(vias,'vias'))
            else:
                objs.append(self._makeCompound(vias,'vias'))

        self._log('modules: {}',len(self.pcb.module))
        self._log('pads: {}, skipped: {}',count,skip_count)
        self._log('vias: {}, skipped: {}',len(self.pcb.via),via_skip)
        self._log('total pads added: {}',
                count-skip_count+len(self.pcb.via)-via_skip)

        if objs:
            objs = self._cutHoles(objs,holes,'pads',fit_arcs=fit_arcs)
            if shape_type=='solid':
                objs = self._makeSolid(objs,'pads', thickness,
                                    fit_arcs = fit_arcs)
            else:
                objs = self._makeCompound(objs,'pads',
                                    fuse=True,fit_arcs=fit_arcs)
            self.setColor(objs,'pad')

        self._popLog('pads done')
        fitView();
        return objs


    def setColor(self,obj,otype):
        if not self.add_feature:
            return
        try:
            color = self.colors[otype][self.layer_type]
        except KeyError:
            color = self.colors[otype][0]
        if hasattr(obj.ViewObject,'MapFaceColor'):
            obj.ViewObject.MapFaceColor = False
        obj.ViewObject.ShapeColor = color


    def makeTracks(self,shape_type='face',fit_arcs=True,
                    thickness=0.05,holes=False,prefix=''):

        self._pushLog('making tracks...',prefix=prefix)

        width = 0
        def _line(edges,offset=0,fill=False):
            wires = findWires(edges)
            return self._makeWires(wires,'track', offset=offset,
                    fill=fill, label=width, workplane=True)

        def _wire(edges,fill=False):
            return _line(edges,width*0.5,fill)

        def _face(edges):
            return _wire(edges,True)

        _solid = _face

        try:
            func = locals()['_{}'.format(shape_type)]
        except KeyError:
            raise ValueError('invalid shape type: {}'.format(shape_type))

        tracks = defaultdict(list)
        count = 0
        for s in self.pcb.segment:
            if s.layer == self.layer:
                tracks[s.width].append(s)
                count += 1

        objs = []
        i = 0
        for (width,ss) in dict.items(tracks): #iteritems(tracks): #maui
            self._log('making {} tracks of width {:.2f}, ({}/{})',
                    len(ss),width,i,count)
            i+=len(ss)
            edges = []
            for s in ss:
                if s.start != s.end:
                    edges.append(Part.makeLine(
                        makeVect(s.start),makeVect(s.end)))
                else:
                    self._log('Line (Track) through identical points {}',
                            s.start, level="warning")
            objs.append(func(edges))

        if objs:
            objs = self._cutHoles(objs,holes,'tracks',fit_arcs=fit_arcs)

            if shape_type == 'solid':
                objs = self._makeSolid(objs,'tracks',thickness,
                                        fit_arcs=fit_arcs)
            else:
                objs = self._makeCompound(objs,'tracks',fuse=True,
                        fit_arcs=fit_arcs)

            self.setColor(objs,'track')

        self._popLog('tracks done')
        fitView();
        return objs


    def makeZones(self,shape_type='face',thickness=0.05, fit_arcs=True,
                    holes=False,prefix=''):

        self._pushLog('making zones...',prefix=prefix)

        z = None
        zone_holes = []

        def _wire(obj,fill=False):
            # NOTE: It is weird that kicad_pcb's zone fillpolygon is 0.127mm
            # thinner than the actual copper region shown in pcbnew or the
            # generated gerber. Why is this so? Is this 0.127 hardcoded or
            # related to some setup parameter? I am guessing this is half the
            # zone.min_thickness setting here.

            if not zone_holes or (
              self.add_feature and self.make_sketch and self.zone_merge_holes):
                obj = [obj]+zone_holes
            elif zone_holes:
                obj = (self._makeWires(obj,'zone_outline', label=z.net_name),
                       self._makeWires(zone_holes,'zone_hole',label=z.net_name))
                return self._makeArea(obj,'zone',offset=z.min_thickness*0.5,
                        op=1, fill=fill,label=z.net_name)

            return self._makeWires(obj,'zone',fill=fill,
                            offset=z.min_thickness*0.5,label=z.net_name)


        def _face(obj):
            return _wire(obj,True)

        _solid = _face

        try:
            func = locals()['_{}'.format(shape_type)]
        except KeyError:
            raise ValueError('invalid shape type: {}'.format(shape_type))

        objs = []
        for z in self.pcb.zone:
            try:
                if z.layer != self.layer:
                    continue
            except:
                continue
            count = len(z.filled_polygon)
            self._pushLog('making zone {}...', z.net_name)
            for idx,p in enumerate(z.filled_polygon):
                zone_holes = []
                table = {}
                pts = SexpList(p.pts.xy)

                # close the polygon
                pts._append(p.pts.xy._get(0))

                # `table` uses a pair of vertex as the key to store the index of
                # an edge.
                for i in xrange(len(pts)-1):
                    table[str((pts[i],pts[i+1]))] = i

                # This is how kicad represents holes in zone polygon
                #  ---------------------------
                #  |    -----      ----      |
                #  |    |   |======|  |      |
                #  |====|   |      |  |      |
                #  |    -----      ----      |
                #  |                         |
                #  ---------------------------
                # It uses a single polygon with coincide edges of oppsite
                # direction (shown with '=' above) to dig a hole. And one hole
                # can lead to another, and so forth. The following `build()`
                # function is used to recursively discover those holes, and
                # cancel out those '=' double edges, which will surely cause
                # problem if left alone. The algorithm assumes we start with a
                # point of the outer polygon. 
                def build(start,end):
                    results = []
                    while start<end:
                        # We used the reverse edge as key to search for an
                        # identical edge of oppsite direction. NOTE: the
                        # algorithm only works if the following assumption is
                        # true, that those hole digging double edges are of
                        # equal length without any branch in the middle
                        key = str((pts[start+1],pts[start]))
                        try:
                            i = table[key]
                            del table[key]
                        except KeyError:
                            # `KeyError` means its a normal edge, add the line.
                            results.append(Part.makeLine(
                                makeVect(pts[start]),makeVect(pts[start+1])))
                            start += 1
                            continue

                        # We found the start of a double edge, treat all edges
                        # in between as holes and recurse. Both of the double
                        # edges are skipped.
                        h = build(start+1,i)
                        if h:
                            zone_holes.append(Part.Wire(h))
                        start = i+1
                    return results

                edges = build(0,len(pts)-1)

                self._log('region {}/{}, holes: {}',idx+1,count,len(zone_holes))

                objs.append(func(Part.Wire(edges)))

            self._popLog()

        if objs:
            objs = self._cutHoles(objs,holes,'zones')
            if shape_type == 'solid':
                objs = self._makeSolid(objs,'zones',thickness,fit_arcs=fit_arcs)
            else:
                objs = self._makeCompound(objs,'zones',
                                fuse=holes,fit_arcs=fit_arcs)
            self.setColor(objs,'zone')

        self._popLog('zones done')
        fitView();
        return objs


    def isBottomLayer(self):
        return self.layer_type == 31


    def makeCopper(self,shape_type='face',thickness=0.05,fit_arcs=True,
                    holes=False, minSize= 0, z=0, prefix='',fuse=False):

        self._pushLog('making copper layer {}...',self.layer,prefix=prefix)
        holes = self._cutHoles(None,holes,None,None,False,minSize)
        #_cutHoles(self,objs,holes,name,label=None,fit_arcs=False,
        #            minSize=0,maxSize=0,oval=True,npth=0,offset=0.0)
        
        objs = []

        if shape_type=='solid':
            solid = True
            sub_fit_arcs = fit_arcs
            if fuse:
                shape_type = 'face'
        else:
            solid = False
            sub_fit_arcs = False

        for (name,offset) in (('Pads',thickness),
                              ('Tracks',0.5*thickness),
                              ('Zones',0)):

            obj = getattr(self,'make{}'.format(name))(fit_arcs=sub_fit_arcs,
                        holes=holes,shape_type=shape_type,prefix=None,
                        thickness=thickness)
            if not obj:
                continue
            if shape_type=='solid':
                ofs = offset if self.layer.startswith('F.') else -offset
                self._place(obj,Vector(0,0,ofs))
            objs.append(obj)

        if shape_type=='solid':
            self._log("makeing solid")
            obj = self._makeCompound(objs,'copper')
            self._log("done solid")
        else:
            obj = self._makeArea(objs,'copper',fit_arcs=fit_arcs)
            if 0: # maui not coloring compound
                self.setColor(obj,'copper')
            if solid:
                self._log("makeing solid")
                obj = self._makeSolid(obj,'copper',thickness)
                self._log("done solid")
                if 0: # maui not coloring compound
                    self.setColor(obj,'copper')

        self._place(obj,Vector(0,0,z))

        self._popLog('done copper layer {}',self.layer)
        fitView();
        return obj


    def makeCoppers(self,shape_type='face',fit_arcs=True,prefix='',
            holes=False,board_thickness=None,thickness=0.05,fuse=False):

        self._pushLog('making all copper layers...',prefix=prefix)

        layer_save = self.layer
        objs = []
        layers = []
        for i in xrange(0,32):
            if str(i) in self.pcb.layers:
                layers.append(i)
        if not layers:
            raise ValueError('no copper layer found')

        if not board_thickness:
            board_thickness = self.pcb.general.thickness

        z = board_thickness
        if len(layers) == 1:
            z_step = 0
        else:
            z_step = (z+thickness)/(len(layers)-1)

        if not holes:
            hole_shapes = None
        elif fuse:
            # make only npth holes
            hole_shapes = self._cutHoles(None,holes,None,npth=1)
        else:
            hole_shapes = self._cutHoles(None,holes,None)

        try:
            for layer in layers:
                self.setLayer(layer)
                copper = self.makeCopper(shape_type,thickness,fit_arcs=fit_arcs,
                                    holes=hole_shapes,z=z,prefix=None,fuse=fuse)
                objs.append(copper)
                z -= z_step
        finally:
            self.setLayer(layer_save)

        if not objs:
            self._popLog('no copper found')
            return

        if shape_type=='solid' and fuse:
            # make copper for plated through holes
            hole_coppers = self.makeHoles(shape_type='solid',prefix=None,
                oval=True,npth=-1,thickness=board_thickness+thickness)
            if hole_coppers:
                self.setColor(hole_coppers,'copper')
                self._place(hole_coppers,FreeCAD.Vector(0,0,-thickness*0.5))
                objs.append(hole_coppers);

            # connect coppers with pad with plated through holes, and fuse
            objs = self._makeFuse(objs,'coppers')
            self.setColor(objs,'copper')

            if holes:
                # make plated through holes with inward offset
                drills = self.makeHoles(shape_type='solid',prefix=None,
                        thickness=board_thickness+6*thickness,
                        oval=True,npth=-1,offset=thickness)
                if drills:
                    self._place(drills,FreeCAD.Vector(0,0,-thickness*2))
                    objs = self._makeCut(objs,drills,'coppers')
                    self.setColor(objs,'copper')

        self._popLog('done making all copper layers')
        fitView();
        return objs


    def loadParts(self,z=0,combo=False,prefix=''):

        if not os.path.isdir(self.part_path):
            raise Exception('cannot find kicad package3d directory')

        self._pushLog('loading parts on layer {}...',self.layer,prefix=prefix)
        self._log('Kicad package3d path: {}',self.part_path)

        at_bottom = self.isBottomLayer()
        if z == 0:
            if at_bottom:
                z = -0.1
            else:
                z = self.pcb.general.thickness + 0.1

        if self.add_feature or combo:
            parts = []
        else:
            parts = {}

        for (module_idx,m) in enumerate(self.pcb.module):
            if m.layer != self.layer:
                continue
            ref = '?'
            value = '?'
            for t in m.fp_text:
                if t[0] == 'reference':
                    ref = t[1]
                if t[0] == 'value':
                    value = t[1]

            m_at,m_angle = getAt(m.at)
            m_at += Vector(0,0,z)
            objs = []
            for (model_idx,model) in enumerate(m.model):
                path = os.path.splitext(model[0])[0]
                self._log('loading model {}/{} {} {} {}...',
                        model_idx,len(m.model), ref,value,model[0])
                for e in ('.stp','.STP','.step','.STEP'):
                    filename = os.path.join(self.part_path,path+e)
                    mobj = loadModel(filename)
                    if not mobj:
                        continue
                    at = product(Vector(*model.at.xyz),Vector(25.4,25.4,25.4))
                    rot = [-float(v) for v in reversed(model.rotate.xyz)]
                    pln = Placement(at,Rotation(*rot))
                    if not self.add_feature:
                        if combo:
                            obj = mobj[0].copy()
                            obj.Placement = pln
                        else:
                            obj = {'shape':mobj[0].copy(),'color':mobj[1]}
                            obj['shape'].Placement = pln
                        objs.append(obj)
                    else:
                        obj = self._makeObject('Part::Feature','model',
                            label='{}#{}#{}'.format(module_idx,model_idx,ref),
                            links='Shape',shape=mobj[0])
                        obj.ViewObject.DiffuseColor = mobj[1]
                        obj.Placement = pln
                        objs.append(obj)
                    self._log('loaded')
                    break

            if not objs:
                continue

            pln = Placement(m_at,Rotation(Vector(0,0,1),m_angle))
            if at_bottom:
                pln = pln.multiply(Placement(Vector(),
                                    Rotation(Vector(1,0,0),180)))

            label = '{}#{}'.format(module_idx,ref)
            if self.add_feature or combo:
                obj = self._makeCompound(objs,'part',label,force=True)
                obj.Placement = pln
                parts.append(obj)
            else:
                parts[label] = {'pos':pln, 'models':objs}

        if parts:
            if combo:
                parts = self._makeCompound(parts,'parts')
            elif self.add_feature:
                grp = self._makeObject('App::DocumentObjectGroup','parts')
                for o in parts:
                    grp.addObject(o)
                parts = grp

        self._popLog('done loading parts on layer {}',self.layer)
        fitView();
        return parts


    def loadAllParts(self,combo=False):
        layer = self.layer
        objs = []
        try:
            self.setLayer(0)
            objs.append(self.loadParts(combo=combo))
        except Exception as e:
            self._log('{}',e,level='error')
        try:
            self.setLayer(31)
            objs.append(self.loadParts(combo=combo))
        except Exception as e:
            self._log('{}',e,level='error')
        finally:
            self.setLayer(layer)
        fitView();
        return objs


    def make(self,copper_thickness=0.05,fit_arcs=True,load_parts=False,
            board_thickness=0, combo=True, fuseCoppers=False):

        self._pushLog('making pcb...',prefix='')

        objs = []
        objs.append(self.makeBoard(prefix=None,thickness=board_thickness))

        coppers = self.makeCoppers(shape_type='solid',holes=True,prefix=None,
                fit_arcs=fit_arcs,thickness=copper_thickness,fuse=fuseCoppers,
                board_thickness=board_thickness)

        if coppers:
            if not fuseCoppers:
                objs += coppers
            else:
                objs.append(coppers)

        if load_parts:
            objs += self.loadAllParts(combo=True)

        if combo:
            layer = self.layer
            try:
                self.layer = None
                objs = self._makeCompound(objs,'pcb')
                if self.add_feature and load_parts:
                    try:
                        objs.ViewObject.SelectionStyle = 1
                    except Exception:
                        pass
            finally:
                self.setLayer(layer)

        self._popLog('all done')
        fitView();
        return objs

def getTestFile(name):
    import glob
    if not os.path.exists(name):
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path,'tests')
        if name:
            path = os.path.join(path,name)
    else:
        path = name
    if os.path.isdir(path):
        return glob.glob(os.path.join(path,'*.kicad_pcb'))
    if os.path.isfile(path):
        return [path]
    path += '.kicad_pcb'
    if os.path.isfile(path):
        return [path]
    raise RuntimeError('Cannot find {}'.format(name))

def test(names=''):
    if not isinstance(names,(tuple,list)):
        names = [names]
    files = set()
    for name in names:
        files.update(getTestFile(name))
    for f in files:
        pcb = KicadFcad(f)
        pcb.make()
        pcb.make(fuseCoppers=True)
        pcb.add_feature = False
        Part.show(pcb.make())

