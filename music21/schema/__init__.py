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

    def __eq__(self, other):
        '''
        return True iff this Label equals `other`, that is
        the offset, duration, kind, tag, and weight are equal
        '''
        if not isinstance(other, Label):
            return False

        return (
            self.offset == other.offset and
            self.duration == other.duration and
            self.kind == other.kind and
            self.tag == other.tag and
            self.weight == other.weight
        )

    def __hash__(self):
        # Enable 'label in list' with python3
        return id(self)

    def compare(
            self,
            other,
            checkKind=True,
            checkTag=False,
            startDeltaOffset=0,  # epsilon
            endDeltaOffset=0     # epsilon
    ):
        '''
        Compares this Label with `other`, possibly checking the kind (`checkKind`) and the tag (`checkTag`)
        are equal, and the difference of the start/end offsets of the labels are lower or equal
        than `startDeltaOffset`/`endDeltaOffset`

        >>> from music21.schema import Label
        >>> label = Label(offset=1, duration=4, kind="kind", tag="tag")
        >>> labelTest1 = Label(offset=1, duration=4, kind="kind", tag="otherTag")
        >>> label.compare(labelTest1)
        True
        >>> label.compare(labelTest1, checkTag=True)
        False
        >>> labelTest2 = Label(offset=1.5, duration=3.5, kind="kind", tag="otherTag")
        >>> label.compare(labelTest2)
        False
        >>> label.compare(labelTest2, startDeltaOffset=1)
        True
        >>> labelTest3 = Label(offset=1, duration=3.5, kind="otherKind", tag="otherTag")
        >>> label.compare(labelTest3)
        False
        >>> label.compare(labelTest3, checkKind=False, endDeltaOffset=0.5)
        True
        '''

        if checkKind and not self.kind == other.kind:
            return False

        if checkTag and (not self.tag == other.tag):
            return False

        if math.fabs(self.offset - other.offset) > startDeltaOffset:
            return False

        if math.fabs(self.end - other.end) > endDeltaOffset:
            return False

        return True

    def __ne__(self, other):
        '''
        return True iff this Label not equals `other`
        '''
        return not self.__eq__(other)

    def intersects(self, other):
        '''
        Returns True iff this label intersects `other`

        >>> from music21.schema import Label
        >>> label1 = Label(offset=11, duration=8)
        >>> label2 = Label(offset=30, duration=8)

        >>> label1.intersects(label2)
        False

        >>> label3 = Label(offset=15, duration=8)

        >>> label1.intersects(label3)
        True
        '''

        start1 = self.offset
        end1 = self.end
        start2 = other.offset
        end2 = other.end

        return (start2 <= start1 <= end2 or
                start2 <= end1 <= end2 or
                start1 <= start2 <= end1 or
                start1 <= end2 <= end1)

    def containsOffset(self, offset):
        '''
        Returns whether the Label contains the given `offset`

        >>> from music21.schema import Label
        >>> label = Label(offset=1, duration=4)

        >>> label.containsOffset(0.5)
        False

        >>> label.containsOffset(1.5)
        True
        '''
        # return self.offset <= offset <= self.offset + self.duration.quarterLength
        return self.offset <= offset <= self.end

    def overlapQuarterLength(self, other):
        """
        Returns the length of the overlap between this Label and `other`,
        or 0 if the labels do not overlap.
        """
        return max(0, min(self.end, other.end) - max(self.offset, other.offset))

    def getOverlappingLabels(self, stream, kindList=None,
                             startDeltaOffset=0,
                             endDeltaOffset=0):
        """
        Returns a list of labels overlapping this Label, optionally restricted to label of kinds in `kindList`
        Handle `startDeltaOffset` and `endDeltaOffset` XXX TODO: doc
        """

        overlappingLabels = []

        for other in stream.getElementsByOffset(self.offset - startDeltaOffset, self.end + endDeltaOffset,
                                                mustBeginInSpan=False, mustFinishInSpan=False,
                                                classList=['Label']):
            if (kindList is None) or (other.kind in kindList):
                overlappingLabels.append(other)

        return overlappingLabels


    def __repr__(self):
        return "<music21.schema.Label %s %s %s offset=%s duration=%s>" % (self.kind, self.tag, self.weight, self.offset, self.duration.quarterLength)

