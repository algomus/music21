# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         lily.py
# Purpose:      Render scores with analysis schema with Lilypond
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
This module provides a Lilypond output for a score with an analysis schema
(:class:`~music21.stream.Score` containing :class:`~music21.schema.Label`).
'''

import copy
import unittest


from music21.base import Music21Object
from music21 import environment
_MOD = 'schema/lily.py'
environLocal = environment.Environment(_MOD)
# Objects to be translated by LilypondConverter.appendM21ObjectToContext()


class BoxStart(Music21Object):
    def __init__(self, text, color):
        Music21Object.__init__(self, text, color)
        self.text = text
        self.color = color


class BoxEnd(Music21Object):
    pass


class Mark(Music21Object):
    def __init__(self, text, color):
        Music21Object.__init__(self)
        self.text = text
        self.color = color


class LilySchema(object):
    '''
    Prepare a the :class:`~music21.stream.Score` `score`
    contaning :class:`~music21.schema.Label` for Lilypond rendering
    using the :class:`~music21.schema.style` `styleSheet`.

    A subset of the labels `filterFunction` can be selected, such as in:
    filterFunction = (lambda label: label.kind in ['bli', 'bla'])
    '''

    DOC_ATTR = {
        'score': '''
            the :class:`~music21.stream.Score`
            '''
    }

    def __init__(self, score, styleSheet, filterFunction=None, defaultPartId='B'):
        self.score = copy.deepcopy(score)

        # Defaut part, for 'global' labels
        # TODO: better mechanism to visualize a Label (with length) that is not assigned to a part
        defaultPart = self.score.parts[0]
        for part in self.score.parts:
            if part.id == defaultPartId:
                defaultPart = part

        environLocal.printDebug(["default", defaultPart.id])

        # Prepare the labels
        for part in self.score.parts:
            targetPart = part if len(part.flat.notes) else defaultPart
            for label in targetPart.getElementsByClass('Label'):
                if filterFunction:
                    if not filterFunction(label):
                        continue
                self._insertLabelInPart(label, targetPart, styleSheet)

    def _insertLabelInPart(self, label, part, styleSheet):
        startOffset = label.offset
        startMeasure = part.getElementsByOffset(offsetStart=startOffset, mustBeginInSpan=False, classList=['Measure'])[0]

        if label.duration.quarterLength == 0:
            color = styleSheet[label.kind].color
            mark = Mark(label.tag, color.scheme)
            startMeasure.insert(startOffset - startMeasure.offset, mark)
        else:
            if len(label.getOverlappingLabels(part)) > 1:
                environLocal.warn('Label %s is ignored, as it overlaps other labels. LilySchema() only handles non-overlapping labels.' % label,
                                  "lily.py: LilySchema: _insertLabelInPart")
                return

            color = styleSheet[label.kind].color
            boxStart = BoxStart(label.tag, color.scheme)
            boxStart.priority = -10
            startMeasure.insert(startOffset - startMeasure.offset, boxStart)

            endOffset = label.offset + label.duration.quarterLength
            # endMeasure = self._measureThatContainsOffset(part, endOffset)
            endMeasure = part.getElementsByOffset(offsetStart=endOffset,
                                                  offsetEnd=endOffset + 1,
                                                  mustBeginInSpan=False,
                                                  classList=['Measure']
                                                  )[0]
            boxEnd = BoxEnd()
            boxEnd.priority = -10
            endMeasure.insert(endOffset - endMeasure.offset, boxEnd)

    def show(self, fmt=None, app=None, **keywords):
        return self.score.show(fmt, app)


# -----------------------------------------------------------------------------
class Test(unittest.TestCase):

    def setUp(self):
        pass

# -----------------------------------------------------------------------------
_DOC_ORDER = [LilySchema, BoxStart, BoxEnd, Mark]

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
