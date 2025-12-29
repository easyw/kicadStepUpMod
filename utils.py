import re
import sys
import binascii

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

def crc_gen(data):
    # Replace non-ascii characters with '_'
    content=re.sub(r'[^\x00-\x7F]+','_', data)
    return u'_' + make_unicode(hex(binascii.crc_hqx(content.encode('utf-8'), 0))[2:])
