#!/usr/bin/env python
'''Sample code for a semantic checking parser

Simply run ::

./test.py 

to see the error message. For more output ::

./test.py -l INFO

To parse an input file,

./test.py <filename>
'''

from sexp_parser import *
import sys
import argparse

test_data = \
'''
(module DIP-16_0 (layer F.Cu) (tedit 0)
  (fp_text reference REF** (at -11.14 0 90) (layer F.SilkS)
    (effects (font (size 1.2 1.2) (thickness 0.15)))
  )
  (fp_text oops DIP-16_0 (at 0 0) (layer F.Fab)
    (effects (font (size 1.2 1.2 oops) (thickness 0.15)))
  )
  (fp_line_opps (start -9.94 7.399999) (end 9.94 7.4) (layer F.SilkS) (width 0.15))
  (fp_line (start 9.94 7.4) (end 9.94 -7.399999) (layer F.SilkS) (width 0.15))
  (pad 16 thru_hole circle (at -8.89 -6.35) (size 1.05 1.05) (drill 0.65) (layers *.Cu *.Mask F.SilkS))
  (pad 1 thru_hole circle (at -8.89 6.35) (size 1.05 1.05) (drill 0.65) (layers *.Cu *.Mask F.SilkS))
)
'''

# All the pasreXXXX helpers are defined in sexp_parser.py. You can write your
# own following the same signature

# Expression (at x y angle) can have the optional <angle>
class ParserStrict(SexpParser):
    def _parse(self,idx,data):
        raise KeyError('unknown key')

class ParserFont(ParserStrict):
    _parse1_size = parseFloat2 # expression with two float atoms
    _parse1_thickness = parseFloat1 # expression with one float

class ParserEffects(ParserStrict):
    _parse1_font = ParserFont

class ParserText(ParserStrict):

    def _pos0_parse(self,data): # Possible values: 'reference','value','user'
        if not isinstance(data,basestring):
            raise ValueError('expects atom')
        if data not in ('reference','value','user'):
            raise ValueError('unknown text value')
        return Sexp(None,data)

    _pos1_parse = parseAtom # Second atom to be text content

    # (at ...) expression can have a third optional float for angle
    def _parse1_at(self,data):
        try:
            return parseFloat2(self,data)
        except:
            return parseFloat3(self,data)

    _parse1_layer = parseCopy1
    _parse1_effects = ParserEffects

class ParserLine(ParserStrict):
    _parse1_start = parseFloat2
    _parse1_end = parseFloat2
    _parse1_layer = parseCopy1
    _parse1_width = parseFloat1
    
    # Setup default values. You can either set the defaults in the sub-parser
    # here, Or set it at the parent parsers using tuples. See ParserModule._defaults
    _defaults = 'sub_line'

class ParserModule(ParserStrict):
    _pos0_parse = parseAtom # first value to be an atom
    _parse1_layer = parseCopy1 # sub expression with one atom
    _parse1_tedit = parseInt1 # sub expression with one integer value
    _parse_fp_text = ParserText # composite expression
    _parse_fp_line = ParserLine # composite expression

    _parse_pad = SexpParser # Feel lazy? Don't check pad expression?
                            # Just let SexpParser handle the rest


    # Setup default values. Text entry means we want that key to be a SexpList
    # even if there is none, or only one instance. 
    #
    # If The entry is a tuple, then The first element of the tuple specifies
    # the key we want for a SexpList default.  The rest elements specifies the
    # sub keys for that key we want for SexpList. Those sub keys can themselves
    # be a tuple.
    #
    # You can create arbitrary complex defaults, by using Sexp directly
    # as the default value(s). See the extreme example below. In most cases,
    # you'll be better off writing a subclass(es) to take care of its own
    # defaults
    _defaults = \
        'pad',\
        'fp_line',\
        'fp_circle',\
        'fp_arc',\
        ('fp_text',\
            ((Sexp('fp_extra'),\
                Sexp('fp_extra2')))),\
        (Sexp('extra'), \
                (Sexp('child1'),Sexp('grandchild'),'c2'),\
                'child2',\
                Sexp('child3',[1,3,4]))
    
    def __init__(self,data):
        super(ParserModule,self).__init__(data)
        if self._key != 'module': # check the root key
            raise TypeError('invalid header: {}'.format(self._key))

    @staticmethod
    def load(filename):
        with open(filename,'r') as f:
            return ParserModule(parseSexp(f.read()))


parser = argparse.ArgumentParser()
parser.add_argument("filename",nargs='?')
parser.add_argument("-l", "--log", dest="logLevel", 
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
    help="Set the logging level")
args = parser.parse_args()    
logging.basicConfig(level=args.logLevel,
        format="%(filename)s:%(lineno)s: %(levelname)s - %(message)s")

if args.filename:
    module = ParserModule.load(args.filename[0])
else:
    module = ParserModule(parseSexp(test_data))

for e in getSexpError(module):
    print(e)

print('\nkeys: ')
for k in module:
    print('\t{}: {}'.format(k,module[k]))

print('\n')
exportSexp(module,sys.stdout)


