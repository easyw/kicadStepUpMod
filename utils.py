#-*- coding: utf-8 -*-
import re
import binascii

def make_string(input):
    if isinstance(input, str):
        return input
    return input.encode('utf-8')

def make_unicode(input):
    if isinstance(input, str):
        return input
    return input.decode('utf-8')

def crc_gen(data):
    # Replace non-ascii characters with '_'
    content=re.sub(r'[^\x00-\x7F]+','_', data)
    return u'_' + make_unicode(hex(binascii.crc_hqx(content.encode('utf-8'), 0))[2:])
