================================
Python S-Expression Object Model
================================

There are many variants of `S-Expression <https://en.wikipedia.org/wiki/S-expression>`_.  
This module here only deals with the *prefix notation*, where the first element
of an expression is expected to be an operator, which is referred to as the
``<key>`` in this module. The module provides a parser `SexpParser` that
converts a python list-based expression into a python object model. Each
expression in the list-based S-Expression representation is defined as a
recursive ``list`` representation in the form of ::

    [ <line number>, <key>, <value>... ]

where there may be none or multiple ``<values>`` of either an atom (i.e. plain
string) or another list-based S-Expression. `SexpParser` assumes the ``<key>``
here is a plain string. The ``<line number>`` not being part of the
conventional S-Expression is only here for debugging purpose

function `parseSexp()` can be used to convert plain text form S-Expression into
the list-based representation

The class `Sexp` is the top class for objects representing a parsed
expression.

If you only need a non-semantic-checking parser, you can use `SexpParser` as
it is.  For the usage of the object model produced by `SexpParser`, see the
project `here <http://github.com/realthunder/kicad_parser>`_.

To construct a semantic checking parser, see the sample code `here <test.py>`_. 
More details can be found in the code document `here <sexp_parser.py>`_
