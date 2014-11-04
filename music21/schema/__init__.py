# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         schema.py
# Purpose:      base classes for dealing with analysis schemas
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
An analysis schema is a :class:`~music21.stream.Score` containing analysis labels
(:class:`~music21.schema.Label`) organized into several :class:`~music21.stream.Part`.
It is meant to encode different analytical annotations, either automatic or manual,
that can be made on a score.
One or several analysis schema (as for example different analyses performed by different sources (musicologists or algorithms),
or different level of analyses (fine/grain)).

Reference (in French): https://hal.archives-ouvertes.fr/hal-01135118v1
'''

import copy

import music21.stream
import music21.converter

import math

from music21.base import Music21Object
from music21.stream import Stream
from music21.duration import Duration
from music21.exceptions21 import Music21Exception
from music21.note import Rest, Note, GeneralNote

import unittest


class SchemaException(Music21Exception):
    pass


class Label(Music21Object):
    '''
    An object representing an analytic label.
    This will that be embedded into a :class:`~music21.stream.Part` of a :class:`~music21.stream.Score`
    (A label should not be emmbedded into a :class:`~music21.stream.Measure`.)

    A Label marks something at some place.
    Like all Music21Objects, a Label has thus
    - an :attr:`~music21.schema.Label.offset` attribute, that is the start offset
    - a :class:`~music21.duration.Duration`. This duration may be zero (marking an instant event)
      or not (pattern, ...). XXX

    The :attr:`~music21.schema.Label.kind` attribute is a string denoting the type of the label.
    This will be used to render the label (see :class:`~music21.schema.style`).
    The Label also stores arbitrary numerical :attr:`~music21.schema.Label.weight` (for example a XXX score XXX), and
    a :attr:`~music21.schema.Label.tag` string.
    '''

    _DOC_ATTR = {
        'offset': '''
            the start offset
            ''',
        'duration': '''
            the duration
            ''',
        'tag': '''
            arbitrary string
            ''',
        'weight': '''
            arbitrary numerical
            ''',
    }

    def __init__(self, offset=0.0, duration=None, kind='',
                 tag=None, weight=None):

        Music21Object.__init__(self)

        self._kind = None

        self.offset = offset

        if duration is None:
            self.duration = music21.duration.Duration()
        elif isinstance(duration, float) or isinstance(duration, int):
            self.duration = music21.duration.Duration(duration)
        else:
            self.duration = duration

        self.kind = kind

        self.tag = kind if tag is None else tag
        self.weight = weight

    @property
    def kind(self):
        '''
        A string denoting the type of the label.
        '''
        return self._kind

    @kind.setter
    def kind(self, value):
        if not isinstance(value, str):
            raise music21.base.ElementException('kind values must be strings.')
        self._kind = value

    @property
    def end(self):
        '''
        returns the `offset` + `duration`
        '''
        return self.offset + self.duration.quarterLength


    def __repr__(self):
        return "<music21.schema.Label %s %s %s offset=%s duration=%s>" % (self.kind, self.tag, self.weight, self.offset, self.duration.quarterLength)

