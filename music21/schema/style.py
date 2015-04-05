# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         style.py
# Purpose:      Stylesheets for music21.schema rendering
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
This module provides classes to choose how to render schemas
(:class:`~music21.stream.Score` containing :class:`~music21.schema.Label`)
using :class:`~music21.schema.svg.SvgSchema`, :class:`~music21.schema.svg.SvgSchemaSet`,
:class:`~music21.schema.web.WebSchemaSet`,
:class:`~music21.schema.lily.LilySchema`, or
:class:`~music21.schema.ansi.AnsiSchema`.
'''
import unittest

from music21.schema.colors import Color
from music21 import environment
_MOD = 'schema/style.py'
environLocal = environment.Environment(_MOD)

from music21.schema import svg


DEFAULT_STYLE_KIND = 'default'

defaultStyleDict = {

    # Global
    'colorBackground': Color(240, 240, 240),
    'exportOpacity': True,       # if False, do not export 'opacity', but rather mixes Colors with the 'colorBackground'
                                 # (some .svg backends do not like opacities)


    # Label
    'color': Color(128, 128, 128),   # color of the Label
    'colorOpacity': 1.0,             # opacity on the color of the Label (and not on other things, such as text in a Box)
    'opacity': 1.0,                  # opacity of the whole Label

    'svg': svg.Box,
    'zIndex': 10,
    'fontSize': 12,
    'fontFamily': 'Helvetica',

    # svg.Box
    'boxHeight': 18,
    'boxRoundedCorners': 3,
    'boxStrokeColor': None,
    'boxTextXPadding': 5,             # padding inside the box
    'boxTextColor': Color(0, 0, 0),

    # svg.VerticalLine
    'verticalLineWidth': 4,
    'verticalLineRoundedCorners': 3,

    # svg.Triangle
    'trianglePosition': 'bottom',    # top, bottom, inLine
    'triangleDirection': 'up',       # up, down
    'triangleYPadding': 2,           # additional padding between top/bottom of the diagram and the triangle
    'triangleScale': 1.0,

    # SvgLine
    'lineAllowOverlaps': True,       # if False, overlaping Boxes will be shifted in svg output
    'lineDisplayName': False,
    'lineNameWidth': 40,
    'lineHalfSpacing': 4,            # Half spacing between Lines. Top : one half, Middle : two halves, Bottom : one half

    # Graduations
    'graduationKey': 'bar-number',   # bar-number, offset
}


class StyleSheet(object):
    '''
    Handles a stylesheet

    >>> from music21.schema import style
    >>> mystyleSheet = style.StyleSheet()
    >>> mystyleSheet.addStyle('a', {'opacity': 0.3, 'zIndex': 2})
    >>> mystyleSheet['a'].opacity
    0.3
    >>> mystyleSheet['a'].zIndex
    2
    >>> mystyleSheet['a'].fontSize
    12
    >>> mystyleSheet.addStyle('b', {'fontSize': 10, 'zIndex':3}, parent='a')
    >>> mystyleSheet['b'].opacity
    0.3
    >>> mystyleSheet['b'].zIndex
    3
    >>> mystyleSheet['b'].fontSize
    10
    '''
    def __init__(self):
        '''
        >>> from music21.schema import style
        >>> mystyleSheet = style.StyleSheet()
        '''
        self._styles = {}
        self.addStyle(DEFAULT_STYLE_KIND, defaultStyleDict, parent=None)

    def addStyle(self, kind, d=None, parent=DEFAULT_STYLE_KIND):
        '''
        Adds a Style for :class:`~music21.schema.Label` having kind `kind` (string) :
        defined by `d` (dictionary),
        the parent's kind is `parent` (string).

        >>> from music21.schema import style
        >>> mystyleSheet = style.StyleSheet()
        >>> mystyleSheet.addStyle('a', {'opacity': 0.3})
        '''
        parentStyle = None
        if parent:
            parentStyle = self._styles[parent]
        self._styles[kind] = Style(kind, d, parentStyle)

    def __getitem__(self, kind):
        '''
        >>> from music21.schema import style
        >>> mystyleSheet = style.StyleSheet()
        >>> print(mystyleSheet['default'])
        /default
        >>> print(mystyleSheet['foo'])
        /default
        '''
        if kind in self._styles:
            return self._styles[kind]
        else:
            if kind is not None:
                environLocal.warn("! Unknown style kind '%s', back to default" % kind, "style.py: StyleSheet: __getitem__")
            return self._styles[DEFAULT_STYLE_KIND]


class Style(object):
    '''
    The style for :class:`~music21.schema.Label` having kind `kind` (string) :
    defined by `d` (dictionary),
    the parent's kind is `parent` (string).

    >>> import music21
    >>> from music21.schema import style
    >>> # music21.schema.style.defaultStyleDict
    >>> mystyle = style.Style(style.DEFAULT_STYLE_KIND, {'opacity': 0.3, 'fontSize': 12})

    '''
    _DOC_ATTR = {
        'kind': '''
            a string
            ''',
        'parentKind': '''
            a string, the parent kind.
            '''
    }

    def __init__(self, kind, d, parent=None):
        self.kind = kind
        self.parentKind = parent

        self._dict = {}

        # Warn when some keys are not in the default style
        if d and kind != DEFAULT_STYLE_KIND:
            for k in d:
                try:
                    self.__getattr__(k)
                except AttributeError:
                    environLocal.warn("! Unknown style property '%s' in Style '%s'" % (k, str(self)), "style.py: Style: __init__")

        # Initialize self._dict
        if d:
            self._dict = d if d else {}

    def __nonzero__(self):
        return len(self._dict) > 0

    def __setitem__(self, attribute, val):
        self._dict[attribute] = val

    def __getitem__(self, attribute, val):
        return self._dict[attribute]

    def __getattr__(self, attribute, recursive=True):
        '''
        >>> from music21.schema import style
        >>> mystyle = style.Style(style.DEFAULT_STYLE_KIND, {'exportOpacity': False, 'foo': 1})
        >>> print(mystyle)
        /default
        >>> mystyle.exportOpacity
        False
        >>> mystyle.foo
        1
        >>> mystyle.bar
        Traceback (most recent call last):
        ...
        AttributeError: 'bar' not defined in /default
        >>> myotherstyle = style.Style('other', {'exportOpacity': True, 'bar': 2}, mystyle)
        >>> print(myotherstyle)
        /default/other
        >>> myotherstyle.exportOpacity
        True
        >>> myotherstyle.foo
        1
        >>> myotherstyle.bar
        2

        '''

        if attribute in self.__dict__:
            return self.__dict__[attribute]

        if attribute == 'opacity' and recursive:
            if self.exportOpacity:
                attr = self.__getattr__('opacity', False)
            else:
                attr = 1.0

        elif attribute == 'colorAfterOpacity':
            mix = self.color.mix(self.colorOpacity, self.colorBackground)
            if self.exportOpacity:
                attr = mix
            else:
                attr = mix.mix(self.__getattr__('opacity', False), self.colorBackground)

        elif attribute in self._dict:
            attr = self._dict[attribute]

        elif self.parentKind:
            attr = getattr(self.parentKind, attribute)

        else:
            raise AttributeError("'%s' not defined in " % attribute + str(self))

        return attr

    def __str__(self):
        return '%s/%s' % (self.parentKind if self.parentKind else '', self.kind)


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def setUp(self):
        pass

# -----------------------------------------------------------------------------
_DOC_ORDER = [StyleSheet, Style]

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
