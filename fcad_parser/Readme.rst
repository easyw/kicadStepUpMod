========================================
Python S-Expression Parser for KiCAD PCB
========================================

Intrudction
___________

The parser ``KicadPCB`` are written using a python S-Expression parser, the
sexp_parser_. To get this submodule, after checkout this repository, do ::

    git submodule init
    git submodule update

The ``KicadPCB`` parser shall be able to handle both ``kicad_pcb`` and
``kicad_mod`` file. The parser does not perform semantic check, though. For
that you'll need to write a large collection of sub-parsers that handle every
possible keyword. It'll be very tedious, but still easy with the help of
``SexpParser``. Check out the `sample code here`_.

.. _sexp_parser:  http://github.com/realthunder/sexp_parser
.. _sample code here: http://github.com/realthunder/sexp_parser/tree/master/test.py

Usage
_____

To get the python object model of a ``kicad_pcb`` or ``kicad_mod`` file ::
    
    from kicad_parser import KicadPCB
    pcb = KicadPCB.load(filename)

Check for error ::

    for e in pcb.getError():
        print('Error: {}'.format(e))

You can modify, add, or delete any expressions inside. You can use ``.`` to
access any non numerical keys such as ::

    pcb.general.zone

For numerical keys, and in fact, all type of keys, you can use ``[]`` ::

    pcb['layers']['0']

Or ::

    pcb.layers['0']

But not ::

    pcb.layers[0]

Because for ``(layers ( 0 F.cu single) ...)`` expression here, the ``0`` is
treated as a string key instead of an integer index. 

For multiple instances with the same key at the same level, you should access
the value by integer index, such as ::

    pcb.module[0]

For un-named values (i.e. any atom behind the key), use their appearance index
for accessing, skipping any named values. For example, to access an expression
like ``(drill oval 1.0 2.0)`` ::

    drill.oval
    drill[0] == 1.0
    drill[1] == 2.0

The 'oval' above would normally be treated as an un-named value, too. However,
``KicadPCB`` treats several special un-named values as named boolean type
value.  Their appearance in the S-Expression source means ``True``, otherwise
means ``False``. These expressions are always accessible through the object
model regardless of their appearance in the source. When doing ``export()``,
those ``False`` values will be ignored. These special values are ::

    gr_text.hide
    pad.drill.oval
    module.locked

This list is obviously not complete. But, it's easy to add your own mappings.
Check out the source code `here <kicad_pcb.py>`_

``KicadPCB`` also treats specal keyword as un-named boolean type, they are ::

    'yes', 'Yes', 'true', 'True', 'no', 'No', 'false', 'False'

To list the sub keys of a composite expression ::

    for subkey in pcb:
        print(subkey)

It will also list integer keys for un-named values if there is any.

To delete an expression ::

    del pcb.layers['0']

To create expressions, you'll need to import the general S-Expression Parser ::

    from kicad_parser import *

For multiple expressions with the same key, they will be stored into an object
of type ``sexp_parser.SexpList`` the parser will automatically create this list
object to hold the multiple instances. To check if it is a list ::

        isinstance(pcb.module,SexpList)

To add a simple expression ``(0 new.layer signal)``, ::

    pcb.layers['0'] = Sexp('0',[ 'new.layer', 'signal' ])

Note that if there is already an expression with the same key, ``=`` will not
overwrite the existing one. Instead, it will use ``SexpList`` to hold multiple
instances

To add a composite expression ::

    pcb.module[0].model = SexpParser(parseSexp(
        """(model new/model3 
            (at (xyz 1 2 3)) 
            (scale (xyz 3 5 6)) 
            (rotate (xyz 7.0 8.0 9.0)))
        """)

If you are not sure whether a key in the object model holds a single expression
or multiple instances, you can use ``SexpList`` to make sure it is a list ::

    if 'module' in pcb:
        for m in SexpList(pcb.module):
            print(m)

``KicadPCB`` will ensure several common keys to be presented even if there is
none, in which case an empty ``SexpList`` will be inserted. And if there is
only one instance, it will still be inside a ``SexpList``.  This is to spare
the pain of the boilerplate code above. The default keys are ::

    net
    net_class
        add_net
    dimension
    gr_text
    gr_line
    gr_circle
    gr_arc
    gr_curve
    segment
    via
    module
        fp_text
        fp_line
        fp_circle
        fp_arc
        pad
        model

To export the modified object model back to kicad_pcb file ::

    pcb.export(filename)

Or to output stream ::

    pcb.export(sys.stdout)

To export any ``Sexp`` ::

    exportSexp(pcb.general,sys.stdout)

See sample code `here <test.py>`_ for more details.
