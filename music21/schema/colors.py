# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         colors.py
# Purpose:      Abstract colors
#
# Authors:      Guillaume Bagan
#               Mathieu Giraud
#               Richard Groult
#               Emmanuel Leguy
#
# Copyright:    Copyright © 2013-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
# ------------------------------------------------------------------------------
'''
This modules provides an abstraction of RGB colors, with an optional correspondance to terminal ANSI colors.
The colors may then both used on :class:`~music21.schema.svg`, :class:`~music21.schema.web`, and :class:`~music21.schema.lily`  outputs.
'''

import unittest


class Color(object):
    _DOC_ATTR = {
        'r': '''
           red
            ''',
        'g': '''
           green
            ''',
        'b': '''
           blue
            ''',
        'ansi': '''
           ansi code
            '''
    }

    def __init__(self, r, g, b, ansi=''):
        self.r = r
        self.g = g
        self.b = b
        self.ansi = ansi

    @classmethod
    def fromHex(cls, hexa):
        '''
        >>> from music21.schema import colors
        >>> colors.Color.fromHex('#ff6432').hex
        '#ff6432'
        '''
        r = int(hexa[1:3], 16)
        g = int(hexa[3:5], 16)
        b = int(hexa[5:7], 16)
        return Color(r, g, b)

    @property
    def hex(self):
        '''
        >>> from music21.schema import colors
        >>> colors.Color(255, 100, 50).hex
        '#ff6432'
        '''
        return "#%02x%02x%02x" % (self.r, self.g, self.b)

    @property
    def float(self):
        '''
        >>> from music21.schema import colors
        >>> colors.Color(255, 100, 50).float
        (0.99609375, 0.390625, 0.1953125)
        '''
        return (float(self.r) / 256, float(self.g) / 256, float(self.b) / 256)

    @property
    def scheme(self):
        '''
        Returns a schemed-encoded string of the color, useable by Lilypond.

        >>> from music21.schema import colors
        >>> colors.Color(255, 100, 50).scheme
        '#(rgb-color 1.00 0.39 0.20)'
        '''
        return "#(rgb-color %.2f %.2f %.2f)" % self.float

    def mix(self, alpha, other=None):
        '''
        Mixes the color with the 'other' color, with a 'alpha' XXXX

        >>> from music21.schema import colors
        >>> colors.Color(0, 0, 0).mix(0.5).hex
        '#7f7f7f'
        >>> colors.Color(0, 0, 0).mix(0.5, colors.Color(64, 255, 0)).hex
        '#207f00'
        '''
        if other is None:
            other = Color(255, 255, 255)
        r = self.r * alpha + other.r * (1 - alpha)
        g = self.g * alpha + other.g * (1 - alpha)
        b = self.b * alpha + other.b * (1 - alpha)
        return Color(r, g, b, self.ansi)

    def __str__(self):
        '''
        >>> from music21.schema import colors
        >>> print(colors.Color(255, 100, 50))
        Color(#ff6432\033[0m)
        '''
        return "Color(%s%s%s)" % (self.ansi, self.hex, Style.RESET_ALL)


CSI = '\033['


def codeToChars(code):
    return CSI + str(code) + 'm'


class AnsiCodes(object):
    BLACK = None
    RED = None
    GREEN = None
    YELLOW = None
    BLUE = None
    MAGENTA = None
    CYAN = None
    WHITE = None
    RESET = None
    RESET_ALL = None

    def __init__(self, codes):
        for name in dir(codes):
            if not name.startswith('_'):
                value = getattr(codes, name)
                setattr(self, name, codeToChars(value))


class AnsiFore(object):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    RESET = 39

    def __init__(self):
        pass


class AnsiBack(object):
    '''
    >>> from music21.schema import colors
    >>> print(colors.AnsiBack().BLACK)
    40
    '''
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47
    RESET = 49

    def __init__(self):
        pass


class AnsiStyle(object):
    BRIGHT = 1
    DIM = 2
    NORMAL = 22
    RESET_ALL = 0

    def __init__(self):
        pass

Fore = AnsiCodes(AnsiFore)
Back = AnsiCodes(AnsiBack)
Style = AnsiCodes(AnsiStyle)

RED = Color(255, 0, 0, Fore.RED)
GREEN = Color(0, 255, 0, Back.GREEN)
BLUE = Color(0, 0, 255, Fore.BLUE)
YELLOW = Color(255, 200, 0, Back.YELLOW)
WHITE = Color(255, 255, 255, Back.WHITE)
BLACK = Color(0, 0, 0, Fore.BLACK)


# -----------------------------------------------------------------------------
class Test(unittest.TestCase):
    def setUp(self):
        pass

    def testConstant(self):
        self.assertEqual(RED.hex, '#ff0000')
        self.assertEqual(GREEN.hex, '#00ff00')

# -----------------------------------------------------------------------------
_DOC_ORDER = [Color, AnsiCodes, AnsiStyle, AnsiFore, AnsiBack]

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
