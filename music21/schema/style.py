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
'''
import unittest

from music21.schema.colors import Color
from music21 import environment
_MOD = 'schema/style.py'
environLocal = environment.Environment(_MOD)

from music21.schema import svg


DEFAULT_STYLE_KIND = 'default'

defaultStyleDict = {
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

    def __getattr__(self, attribute):                
        attr = None

        if attribute in self._dict:
            attr = self._dict[attribute]

        elif self.parentKind:
            attr = getattr(self.parentKind, attribute)

        if attr is None:
            raise AttributeError("'%s' not defined in " % attribute + str(self))
        else:
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
