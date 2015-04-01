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
from music21 import tinyNotation
'''
An analysis schema is a :class:`~music21.stream.Score` containing analysis labels
(:class:`~music21.schema.Label`) organized into several :class:`~music21.stream.Part`.
It is meant to encode different analytical annotations, either automatic or manual,
that can be made on a score.
One or several analysis schema (as for example different analyses performed by different sources (musicologists or algorithms),
or different level of analyses (fine/grain)).

Scores embedding labels can be rendered in svg (:class:`~music21.schema.svg.SvgSchema` and :class:`~music21.schema.svg.SvgSchemaSet`),
possibly included in a html code with music21j extracts of the score (:class:`~music21.schema.web.WebSchemaSet`),
or with Lilypond (:class:`~music21.schema.lily.LilySchema`), or in a terminal (colored) output (:class:`~music21.schema.ansi.AnsiSchema`).

Schemas can be compared with (:class:`~music21.schema.stats.SchemaDiff`).

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

    def extractPattern(self, container=None):
        r'''

        Calls :meth:`~music21.stream.Stream.getElementsByOffset()` and reconstruct measures, clef, key, time signature information.

        >>> from music21.schema import Label
        >>> from music21 import corpus
        >>> score = corpus.parse('bach/bwv66.6')
        >>> p = score.parts[0]
        >>> p.show('text')  #doctest: +ELLIPSIS
        {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.key.KeySignature of 3 sharps, mode minor>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note C#>
            {0.5} <music21.note.Note B>
        {1.0} <music21.stream.Measure 1 offset=1.0>
        ...
        {9.0} <music21.stream.Measure 3 offset=9.0>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.note.Note A>
            {0.5} <music21.note.Note B>
            {1.0} <music21.note.Note G#>
            {2.0} <music21.note.Note F#>
            {3.0} <music21.note.Note A>
        {13.0} <music21.stream.Measure 4 offset=13.0>
            {0.0} <music21.note.Note B>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note F#>
            {3.0} <music21.note.Note E>
        {17.0} <music21.stream.Measure 5 offset=17.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note C#>
            {3.0} <music21.note.Note C#>
        {21.0} <music21.stream.Measure 6 offset=21.0>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note C#>
            {3.0} <music21.note.Note A>
        ...
        >>> label = Label(offset=11, duration=8)
        >>> p.insert(label)
        >>> extract = label.extractPattern()
        >>> extract.show('text')
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.key.KeySignature of 3 sharps, mode minor>
        {0.0} <music21.meter.TimeSignature 4/4>
        {9.0} <music21.stream.Measure 3 offset=9.0>
            {0.0} <music21.note.Rest rest>
            {2.0} <music21.note.Note F#>
            {3.0} <music21.note.Note A>
        {13.0} <music21.stream.Measure 4 offset=13.0>
            {0.0} <music21.note.Note B>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note F#>
            {3.0} <music21.note.Note E>
        {17.0} <music21.stream.Measure 5 offset=17.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note C#>
        '''

        if container is None:
            container = self.activeSite

        if container is None:
            return Stream()
        else:
            extract = container.getElementsByOffset(self.offset, self.end, mustBeginInSpan=False)
            extract = copy.deepcopy(extract)
            for label in extract.getElementsByClass('Label'):
                extract.remove(label)
            measures = extract.getElementsByClass('Measure')
            if not measures:
                # print "! Container without Measures"
                # extract.show('txt')
                return Stream()

            # Removing extra elements in first and last measure
            for measure in measures:
                for elem in measure:
                    if (
                            measure.offset + elem.offset + elem.duration.quarterLength <= self.offset or
                            measure.offset + elem.offset > self.end
                    ):
                        measure.remove(elem)

            measures[0].makeRests(splitDurationComponents=True)

            #  Adds clef / key / time signature information
            for obj in ['Clef', 'Key', 'TimeSignature', 'KeySignature']:
                # lastObj = container.flat.getElementAtOrBefore(self.offset, obj)  # FIXME: ne renvoie rien, pourquoi ?
                lastObj = container.flat.getElementsByClass(obj)
                if lastObj:
                    extract.insert(0, lastObj[0])
                    # ou bien # measures[0].insert(0, lastObj[0])
            return extract

    def __repr__(self):
        return "<music21.schema.Label %s %s %s offset=%s duration=%s>" % (self.kind, self.tag, self.weight, self.offset, self.duration.quarterLength)

# -----------------------------------------------------------------------------

class Segmentation(music21.stream.Part):

    '''A Segmentation is a succession of consecutive Labels.'''

    def __init__(self, data, constantDuration=None, secondElementIsDuration=False):
        music21.stream.Part.__init__(self)

        if constantDuration:
            self.loadPairs([(t, constantDuration) for t in data], secondElementIsDuration=True)
        else:
            self.loadPairs(data, secondElementIsDuration=secondElementIsDuration)

    def loadPairs(self, pairs, secondElementIsDuration):
        current_offset = 0
        for (tag, secondElement) in pairs:
            dur = secondElement if secondElementIsDuration else secondElement - current_offset
            label = Label(offset=current_offset, duration=dur, kind="segment-%s" % tag, tag=tag)
            self.insert(label)
            current_offset += dur



# -----------------------------------------------------------------------------

class Test(unittest.TestCase):

    def setUp(self):
        self.label = Label(offset=1, duration=4, kind="kind", tag="tag")
        self.labelTest = Label(offset=1, duration=4, kind="kind", tag="tag")

        self.vs = music21.stream.Part()
        self.vs.insert(0, music21.converter.parse('tinyNotation: 4/4 c4 d e c  c d e c   e f g2   e4 f g2  g8 a g f e4 c   g8 a g f e4 c  c4 g c2  c4 g c2'))
        self.vs.makeMeasures(inPlace=True)
        self.vs.insert(self.label)

    def testInit(self):
        labelTest2 = Label(offset=2, duration=None, kind="kind", tag="tag")
        labelTest3 = Label(offset=3, duration=music21.duration.Duration(5), kind="kind", tag="tag")
        self.assertEqual(str(labelTest2), '<music21.schema.Label kind tag None offset=2.0 duration=0.0>')
        self.assertEqual(str(labelTest3), '<music21.schema.Label kind tag None offset=3.0 duration=5.0>')

    def testStr(self):
        self.assertEqual(str(self.label), '<music21.schema.Label kind tag None offset=1.0 duration=4.0>')

    def testRepr(self):
        self.assertEqual(repr(self.label), '<music21.schema.Label kind tag None offset=1.0 duration=4.0>')

    def testKindErr(self):
        def f():
            self.label.kind = 1
        self.assertRaises(music21.base.ElementException, f)

    def testStartEnd(self):
        self.assertEqual(self.label.offset, 1.0)
        self.assertEqual(self.label.end, 5.0)

    def testContainsOffset(self):
        self.assertTrue(self.label.containsOffset(3.5))
        self.assertTrue(self.label.containsOffset(4.0))
        self.assertFalse(self.label.containsOffset(5.5))

    def testGetOverlappingLabels(self):
        self.vs[0].insert(self.label)
        labelTest2 = Label(offset=1, duration=40)
        self.assertEqual(labelTest2.getOverlappingLabels(self.vs[0]), [self.label])

    def testOverlapQuarterLength(self):
        labelA = Label(offset=1, duration=4)
        labelB = Label(offset=2, duration=5)
        labelC = Label(offset=7, duration=2)
        self.assertEqual(labelA.overlapQuarterLength(labelB), 3.0)
        self.assertEqual(labelA.overlapQuarterLength(labelC), 0.0)

    def testExtractPattern(self):
        labelA = Label(offset=3, duration=6)
        self.vs.insert(labelA)

        pattern = labelA.extractPattern()
        tw = tinyNotation.TinyNotationWriter()
        self.assertEqual(len(pattern.flat.getElementsByClass(GeneralNote)), 8)

    def testEq(self):
        self.assertEqual(self.label, self.labelTest)

    def testEqOther(self):
        self.assertNotEqual(self.label, music21.duration.Duration(5))

    def testEqNotSameKind(self):
        self.labelTest.kind = self.label.kind + "other"
        self.assertNotEqual(self.label, self.labelTest)

    def testCompare(self):
        self.assertTrue(self.label.compare(self.labelTest))

    def testCompareNotSameKind(self):
        self.labelTest.kind = self.label.kind + "other"
        self.assertTrue(self.label.compare(self.labelTest, checkKind=False))

    def testCompareNotSameTag(self):
        self.labelTest.tag = self.label.tag + "other"
        self.assertTrue(self.label.compare(self.labelTest))
        self.assertFalse(self.label.compare(self.labelTest, checkTag=True))

    def testCompareNotSameOffset(self):
        self.labelTest.offset = self.label.offset + 1
        self.labelTest.duration = music21.duration.Duration(self.label.duration.quarterLength - 1.0)

        self.assertFalse(self.label.compare(self.labelTest))
        self.assertTrue(self.label.compare(self.labelTest, startDeltaOffset=2), "%s %s" % (self.label, self.labelTest))

    def testCompareNotSameDuration(self):
        self.labelTest.duration = music21.duration.Duration(self.label.duration.quarterLength + 1.0)
        self.assertFalse(self.label.compare(self.labelTest))
        self.assertTrue(self.label.compare(self.labelTest, endDeltaOffset=2), "%s %s" % (self.label, self.labelTest))

    def testLabelEqualityShouldTakeTagsIntoAccount(self):
        self.labelTest.tag = self.label.tag + "other"
        self.assertNotEqual(self.label, self.labelTest)

    def testEqNotSameWeight(self):
        self.labelTest.weight = "other"
        self.assertNotEqual(self.label, self.labelTest)

    def testEqNotSameOffset(self):
        self.labelTest.offset = self.label.offset + 1
        self.assertNotEqual(self.label, self.labelTest)

    def testEqNotSameDuration(self):
        self.labelTest.duration = music21.duration.Duration(self.label.duration.quarterLength + 1.0)
        self.assertNotEqual(self.label, self.labelTest)


if __name__ == '__main__':
    music21.mainTest(Test)
