 #!/usr/bin/python
# -*- coding: utf-8 -*-
'''
features
- convert dxf shape to poly for RF antenna generation
'''

## https://github.com/dom11990/Kicad_MakePolygon

## todo @

#done

__version__=1.1
import sys, os
import FreeCAD, FreeCADGui, Part

# class XYline:
#     def __init__(self, xs, ys, xe, ye):
#         self.start = [xs, ys]
#         self.end   = [xe, ye]
        
class XYpoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def _Equal(f1,f2, margin = (0.0001)) -> bool:
    return abs(f1-f2) < margin

#TODO: make this function fail-safe
def Lines2Polygon(lines, deleteDupes = True):
    
    sourceLines = []
    # ignore lines that are points (same start and end)
    for line in lines:
        if not (_Equal(line.start[0],line.end[0]) and _Equal(line.start[1],line.end[1])):
            sourceLines.append(line)
            
    # TODO: this dupe detection and closure detection is really slow and clunky. Consider re-writing for performance instead of readability
    
    # collect the indexes of all dupes
    dupes = []
    for idx, line in enumerate(sourceLines):
        
        for jdx, innerLine in enumerate(sourceLines):
            if(((_Equal(line.start[0], innerLine.start[0]) and  _Equal(line.start[1], innerLine.start[1]) and 
            _Equal(line.end[0], innerLine.end[0]) and  _Equal(line.end[1], innerLine.end[1])) or                   
            (_Equal(line.start[0], innerLine.end[0]) and  _Equal(line.start[1], innerLine.end[1]) and
            _Equal(line.end[0], innerLine.start[0]) and  _Equal(line.end[1], innerLine.start[1]))) and 
            jdx != idx):
                print("Duplicate found: Line1: [{},{}] [{},{}] Line2: [{},{}] [{},{}]".format(line.start[0],line.start[1],line.end[0],line.end[1],innerLine.start[0],innerLine.start[1],innerLine.end[0],innerLine.end[1]))
                # the two segments are identical or start and end positions are swapped
                # dont consider them in the polygon 
                dupes.append(jdx)
    # loop through and remove the duplicate elements from the source list
    temp = sourceLines.copy()
    sourceLines = []
    for idx, line in enumerate(temp):
        if not idx in dupes:
            # means this is a segment that does not have a dupe
            sourceLines.append(line)
    temp = None
    
    
    
    matchedLines = []
    matchedLines.append(sourceLines[0])
    del sourceLines[0]
    
    # search through the list of lines, finding another that ends or starts where the previous one ends
    while(len(sourceLines)):
        found = False
        for idx,line in enumerate(sourceLines):
            if (_Equal(line.start[0], matchedLines[-1].start[0]) and _Equal(line.start[1], matchedLines[-1].start[1])):
                # start matches start, flip the new line start stop positions
                print("wtf this should not happen")
                raise Exception("There are duplicate lines that have the same start and stop coordinates.")
    
                
            if (_Equal(line.start[0], matchedLines[-1].end[0]) and _Equal(line.start[1], matchedLines[-1].end[1])):
                found = True
                
            if (_Equal(line.end[0], matchedLines[-1].start[0]) and _Equal(line.end[1], matchedLines[-1].start[1])):
                if len(matchedLines) == 1:
                    #this can happen at the very first match. if that is the case
                    # it is likely the structure was drawn 'the other way' so it will be easier to 
                    # swap the first entry and proceed normally than to swap all subsequent entries
                    x1 = matchedLines[-1].start[0]
                    y1 = matchedLines[-1].start[1]
                    matchedLines[-1].start[0]=(matchedLines[-1].end[0])
                    matchedLines[-1].start[1]=(matchedLines[-1].end[1])
                    matchedLines[-1].end[0]=(x1)
                    matchedLines[-1].end[1]=(y1)
    
                    x1 = line.start[0]
                    y1 = line.start[1]
                    line.start[0]=(line.end[0])
                    line.start[1]=(line.end[1])
                    line.end[0]=(x1)
                    line.end[1]=(y1)
                    found = True
    
                
            if (_Equal(line.end[0], matchedLines[-1].end[0]) and _Equal(line.end[1], matchedLines[-1].end[1])):
                x1 = line.start[0]
                y1 = line.start[1]
                line.start[0]=(line.end[0])
                line.start[1]=(line.end[1])
                line.end[0]=(x1)
                line.end[1]=(y1)
                found = True
    
            if(found):
                #we found a perfect match!
                matchedLines.append(line)
                del sourceLines[idx]
                break
        
        if(not found):
            raise Exception("Structure is not fully enclosed. Check to make sure every line or arc ends perfectly on another, ultimately forming a completely enclosed structure with no crossing / self-intersection")
    
    # now check the last lines closes with the first line
    #TODO: actual do this check...though it may not be necessary. Probably, the polygon will simply come out wrong :)
    
    
    #we made it through the whole structure and it appears to be enclose
    
    # create the polygon
    ## polygon = pcbnew.DRAWSEGMENT()
    points = [] #[] #pcbnew.wxPoint_Vector()
    point = XYpoint
    
    # do the first one outside the loop since we also need the start point, not just the end point
    point = (matchedLines[0].start[0], matchedLines[0].start[1])
    points.append(point)
    point = (matchedLines[0].end[0], matchedLines[0].end[1])
    points.append(point)
    del matchedLines[0]
    
    # now just add the end points of each line
    for line in matchedLines:
        point = (line.end[0], line.end[1])
        points.append(point)
    
    # print (points)
    polypoints = points
    # polygon.SetPolyPoints(points)
        
    return polypoints #polygon
   
