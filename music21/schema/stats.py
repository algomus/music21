# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         stats.py
# Purpose:      Compare analysis schemas
#
# Authors:      Guillaume Bagan
#               Nicolas Guiomard-Kagan
#               Mathieu Giraud
#               Richard Groult
#               Emmanuel Leguy
#
# Copyright:    Copyright © 2013-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
# ------------------------------------------------------------------------------

'''
This module provides statistics when comparing analysis schemas
(:class:`~music21.stream.Score` containing analysis labels (:class:`~music21.schema.Label`)).
TODO XXXXXX
'''

import unittest

import music21.stream
import music21.schema

from music21 import environment
_MOD = 'schema/stats.py'
environLocal = environment.Environment(_MOD)

import math
from collections import defaultdict

TP = 'TP'
FP = 'FP'
FN = 'FN'
TP_FP = 'TP+FP'
TP_FN = 'TP+FN'
SENS = 'sensitivity'
PREC = 'precision'
F1 = 'F1'


class Counts(object):
    '''
    Handle counts of true positives (TP), false positive (FP) and false negative (FN) elements,
    and compute precision/recall measures.

        >>> import music21.schema.stats
        >>> c = music21.schema.stats.Counts()
        >>> c.counts['TP'] = 1
        >>> c.counts['FP'] = 3
        >>> c.counts['FN'] = 5
        >>> c.compute()
        >>> print(c)
        TP:   1   FP:   3   FN:   5  sens:  1/  6   16.7%  prec:  1/  4   25.0%  F1: 0.200
        >>> c.d['TP']
        1
        >>> c.d['TP+FP']
        4
        >>> round(c.d['sensitivity'], 5)
        16.66667
    '''

    _DOC_ATTR = {
        'counts': '''
            a `dict` of counts.\
            The keys are ``"TP"``, ``"FP"``, and ``"FN"`` ;
            ''',
        'd': '''
            a `dict`, with these counts expanded with some statistics measures.\
            Defaut keys are ``"TP"``, ``"FP"``, and ``"FN"`` (see :meth:`~music21.schema.stats.Counts.compute()`);
            '''
    }

    def __init__(self):
        self.d = {}
        self.counts = {}
        for key in [TP, FP, FN]:
            self.d[key] = None
            self.counts[key] = 0

    def compute(self):
        '''
        Given :attr:`~music21.schema.stats.Counts.counts`,
        computes :attr:`~music21.schema.stats.Counts.d`:
        add the keys ``"TP+FP"``, ``"TP+FN"``, ``"sensitivity"``, ``"precision"``, and ``"F1"``.

        Also works if the input dictionary are iterables, such as streams of labels.
        In this case, it takes the length of the inputs for the counts.
        '''

        def intOrLen(x):
            return x if isinstance(x, int) else len(x)

        nbTP = intOrLen(self.counts[TP])
        nbFP = intOrLen(self.counts[FP])
        nbFN = intOrLen(self.counts[FN])

        sens = float(nbTP) / float(nbTP + nbFN) if nbTP + nbFN > 0 else float('NaN')
        prec = float(nbTP) / float(nbTP + nbFP) if nbTP + nbFP > 0 else float('NaN')

        f1 = 2 * sens * prec / (sens + prec) if sens + prec > 0 else float('NaN')

        self.d = {
            TP: nbTP, FP: nbFP, FN: nbFN,
            TP_FP: nbTP + nbFP,
            TP_FN: nbTP + nbFN,
            SENS: sens * 100, PREC: prec * 100,
            F1: f1
        }

    def __str__(self):
        s = "TP: %(TP)3s   FP: %(FP)3s   FN: %(FN)3s" % self.d

        if SENS in self.d and not math.isnan(self.d[SENS]):
            s += "  sens:%(TP)3d/%(TP+FN)3d %(sensitivity)6.1f%%" % self.d

        if PREC in self.d and not math.isnan(self.d[PREC]):
            s += "  prec:%(TP)3d/%(TP+FP)3d %(precision)6.1f%%" % self.d

        if F1 in self.d and not math.isnan(self.d[F1]):
            s += "  F1: %(F1)3.3f" % self.d

        return s


def matchingPart(part1, schema2):
    '''
    Given a :class:`~music21.stream.Part` `part1` and a :class:`~music21.stream.Score`  `schema2`,
    returns a :class:`~music21.stream.Part` in the `schema2` whose id matches `part1.id`.
    If there is no such part, create a new (empty) one.

    >>> import music21.schema.stats
    >>> p1 = music21.stream.Part()
    >>> p2 = music21.stream.Part()
    >>> p1.id = 'S'; p2.id = 'A'
    >>> score = music21.stream.Score()
    >>> score.append(p1)
    >>> score.append(p2)
    >>> p = music21.stream.Part()
    >>> p.id = 'S'
    >>> music21.schema.stats.matchingPart(p, score) == p1
    True
    >>> p.id = 'B'
    >>> music21.schema.stats.matchingPart(p, score) #doctest: +ELLIPSIS
    <music21.stream.Part 0x...>
    '''

    part2matching = None
    for part2 in schema2.parts:
        if part2.id == part1.id:
            part2matching = part2
    if part2matching is None:
        part2matching = music21.stream.Part()

#     environLocal.printDebug(["part1", part1.id, "part2", part2matching.id])
    return part2matching


class SchemaDiff(object):
    '''
    Dictionary (see :attr:`~music21.schema.stats.SchemaDiff.diff`) of three schemas
    showing the differences between two schemas.

    Labels which kind is in the string list ``kindsIgnore`` are ignored.
    `kind` XXX
    '''

    _DOC_ATTR = {
        'basename': '''
            the basename
            ''',
        'kinds': '''
            XXX list of kind (string) if the computed scores XXX
            ''',
        'kindsIgnore': '''
            string list of ignore kind
            ''',
        'diff': '''
            a `dict`. The keys are ``"TP"``, ``"FP"``, and ``"FN"`` ;\
            the values are :class:`~music21.stream.Score` (only) containing :class:`~music21.schema.Label,\
            see :meth:`~music21.schema.stats.SchemaDiff.compareSchemas()`
            '''
    }

    def __init__(self, basename, kinds=None, kindsIgnore=None):

        self.basename = basename
        self.kinds = kinds if kinds else []
        self.kindsIgnore = kindsIgnore if kindsIgnore else []

        self._startDeltaOffset = None
        self._endDeltaOffset = None

        # Initialize scores for storing the diffs
        self.diff = {}
        for key in [TP, FP, FN]:
            self.diff[key] = music21.stream.Score()
            self.diff[key].id = '%s-%s' % (basename, key)

    @property
    def startDeltaOffset(self):
        return self._startDeltaOffset

    @startDeltaOffset.setter
    def startDeltaOffset(self, value):
        if self._startDeltaOffset is not None and self._startDeltaOffset != value:
            environLocal.warn("startDeltaOffset(value=%s): startDeltaOffset is already set with other value %d" % (value, self._startDeltaOffset))
        self._startDeltaOffset = value

    @property
    def endDeltaOffset(self):
        return self._endDeltaOffset

    @endDeltaOffset.setter
    def endDeltaOffset(self, value):
        if self._endDeltaOffset is not None and self._endDeltaOffset != value:
            environLocal.warn("endDeltaOffset(value=%s): endDeltaOffset is already set with other value %d" % (value, self._endDeltaOffset))
        self._endDeltaOffset = value

    def compareParts(
            self,
            part1,
            part2,
            startDeltaOffset=0,
            endDeltaOffset=0,
            checkTag=False,
            # match_function = music21.schema.Label.compare
    ):
        '''
        Compares  :class:`~music21.schema.Label` in the :class:`~music21.stream.Part` `part1` and `part2`, and return a dict.

        To compare two Label `label1` and `label2` in `part1` and `part2`,
        the method uses `label1.compare(label2, startDeltaOffset, endDeltaOffset, checkTag)`
        (see :meth:`~music21.schema.Label.compare()`)

        >>> import  music21.stream
        >>> from music21.schema import Label
        >>> a1 = music21.stream.Part()
        >>> a2 = music21.stream.Part()
        >>> # 1 TP
        >>> a1.insert(Label(offset=1, duration=1, kind='kind', tag='tag1_1'))
        >>> a2.insert(Label(offset=1, duration=1, kind='kind', tag='tag2_1'))
        >>> # 1 FP
        >>> a1.insert(Label(offset=10, duration=1, kind='kind', tag='tag1_2'))
        >>> # 1 FN
        >>> a2.insert(Label(offset=30, duration=1, kind='kind', tag='tag2_2'))
        >>> dictRes = music21.schema.stats.SchemaDiff('Compare').compareParts(a1, a2)
        >>> dictRes['TP'].show('text')
        {1.0} <music21.schema.Label kind tag1_1 None offset=1.0 duration=1.0>
        >>> dictRes['FP'].show('text')
        {10.0} <music21.schema.Label kind tag1_2 None offset=10.0 duration=1.0>
        >>> dictRes['FN'].show('text')
        {30.0} <music21.schema.Label kind tag2_2 None offset=30.0 duration=1.0>
        '''

        # Initialize parts for storing the diffs
        diff = {}
        for key in [TP, FP, FN]:
            diff[key] = music21.stream.Part()
            diff[key].id = '%s-%s' % (part1.id, key)

        usedLabel2s = set()

        # Labels in part1 are either true (TP) or false (FP) positives
        part1Labels = part1.getElementsByClass('Label')
        part2Labels = part2.getElementsByClass('Label')
        for label1 in part1Labels:

            if label1.kind in self.kindsIgnore:
                continue

            if not label1.kind in self.kinds:
                self.kinds.append(label1.kind)

            found = False
            for label2 in part2Labels:

                if label2.kind in self.kindsIgnore:
                    continue

                if label2 in usedLabel2s:
                    match = False
                else:
                    match = music21.schema.Label.compare(label1, label2,
                                                         startDeltaOffset=startDeltaOffset,
                                                         endDeltaOffset=endDeltaOffset,
                                                         checkTag=checkTag)
                if match:
                    # environLocal.printDebug(["match", "\t", label1, "\t", label2])
                    usedLabel2s.add(label2)
                    found = True
                    break

            if found:
                diff[TP].insert(label1.offset, label1)
                environLocal.printDebug("%8s :: %s :: %s" % (self.basename, diff[TP].id, label1))
            else:
                diff[FP].insert(label1.offset, label1)
                environLocal.printDebug("%8s :: %s :: %s" % (self.basename, diff[FP].id, label1))

        # Remaining Labels in part2 are false negatives (FN)
        for label2 in part2Labels:

            if label2.kind in self.kindsIgnore:
                continue

            if not label2.kind in self.kinds:
                self.kinds.append(label2.kind)

            if label2 not in usedLabel2s:
                diff[FN].insert(label2.offset, label2)
                environLocal.printDebug("%8s :: %s :: %s" % (self.basename, diff[FN].id, label2))

        # Output stat by voice
        # print "   %-8s ==>" % part1.id, STATS_FORMAT % stats_compute(diff)

        return diff

    def compareSchemas(self, schema1, schema2,
                       startDeltaOffset=0, endDeltaOffset=0,
                       cumulativeDiff=None):
        '''
        Compares :class:`~music21.schema.Label` in two :class:`~music21.stream.Score` `schema1` and `schema2`
        (part by part, the id of the parts must matches, see :meth:`~music21.schema.stats.matchingPart()` ), and
        computes :attr:`~music21.schema.stats.SchemaDiff.diff`.
        If `cumulativeDiff` is given (another :class:`~music21.schema.stats.SchemaDiff`), adds my diff to his diff

        XXX startDeltaOffset, endDeltaOffset XXX

        Also returns :attr:`~music21.schema.stats.SchemaDiff.diff`

        >>> import  music21.stream
        >>> from music21.schema import Label
        >>> s0 = music21.stream.Score()
        >>> s0.insert(0, music21.stream.Part()); s0.parts[0].id = 'A'
        >>> s0.insert(1, music21.stream.Part()); s0.parts[1].id = 'B'
        >>> s1 = music21.stream.Score()
        >>> s1.insert(0, music21.stream.Part()); s1.parts[0].id = 'A'
        >>> s1.insert(1, music21.stream.Part()); s1.parts[1].id = 'B'
        >>> # 1 TP
        >>> s0.parts[0].insert(Label(offset=1, duration=1, kind='a', tag='tag1_1'))
        >>> s1.parts[0].insert(Label(offset=1, duration=1, kind='a', tag='tag2_1'))
        >>> # 1 FP
        >>> s0.parts[0].insert(Label(offset=10, duration=1, kind='b', tag='tag1_2'))
        >>> # 1 FN
        >>> s1.parts[1].insert(Label(offset=30, duration=1, kind='a', tag='tag2_2'))
        >>> dictRes = music21.schema.stats.SchemaDiff('test_simple').compareSchemas(s0, s1)
        >>> dictRes['TP'].show('text')
        {0.0} <music21.stream.Part A-TP>
            {1.0} <music21.schema.Label a tag1_1 None offset=1.0 duration=1.0>
        {0.0} <music21.stream.Part B-TP>
        <BLANKLINE>
        >>> dictRes['FP'].show('text')
        {0.0} <music21.stream.Part A-FP>
            {10.0} <music21.schema.Label b tag1_2 None offset=10.0 duration=1.0>
        {0.0} <music21.stream.Part B-FP>
        <BLANKLINE>
        >>> dictRes['FN'].show('text')
        {0.0} <music21.stream.Part A-FN>
        <BLANKLINE>
        {0.0} <music21.stream.Part B-FN>
            {30.0} <music21.schema.Label a tag2_2 None offset=30.0 duration=1.0>
         '''

        self.startDeltaOffset = startDeltaOffset
        self.endDeltaOffset = endDeltaOffset

        # Compare part by part
        for part1 in schema1.parts:

            part2 = matchingPart(part1, schema2)
            partDiff = self.compareParts(part1, part2,
                                         startDeltaOffset, endDeltaOffset)

            # Store the diff in the global diff
            for key in [TP, FP, FN]:
                self.diff[key].insert(partDiff[key])
                if cumulativeDiff:
                    cumulativeDiff.diff[key].insert(partDiff[key])

        return self.diff

    def __getCountsOfKind(self, diffFlatDict, kind):
        '''
        XXX used to avoid "self.diff[key].flat.getElementsByClass('Label')" many times XXX
        '''
        counts = Counts()
        for key in diffFlatDict:
            for label in diffFlatDict[key]:
                if label.kind == kind or kind is None:
                    counts.counts[key] += 1
        counts.compute()
        return counts

    def getCountsOfKind(self, kind=None):
        '''
        Returns a :class:`~music21.schema.stats.Counts` XXX,
        which counts in :attr:`~music21.schema.stats.SchemaDiff.diff` the number of labels
        of the given `kind` (all kinds if `kind` is `None`).

        >>> import  music21.stream
        >>> from music21.schema import Label
        >>> s0 = music21.stream.Score()
        >>> s0.insert(0, music21.stream.Part()); s0.parts[0].id = 'A'
        >>> s0.insert(1, music21.stream.Part()); s0.parts[1].id = 'B'
        >>> s1 = music21.stream.Score()
        >>> s1.insert(0, music21.stream.Part()); s1.parts[0].id = 'A'
        >>> s1.insert(1, music21.stream.Part()); s1.parts[1].id = 'B'
        >>> # 1 TP
        >>> s0.parts[0].insert(Label(offset=1, duration=1, kind='a', tag='tag1_1'))
        >>> s1.parts[0].insert(Label(offset=1, duration=1, kind='a', tag='tag2_1'))
        >>> # 1 FP
        >>> s0.parts[0].insert(Label(offset=10, duration=1, kind='b', tag='tag1_2'))
        >>> # 1 FN
        >>> s1.parts[1].insert(Label(offset=30, duration=1, kind='a', tag='tag2_2'))
        >>> shemDif = music21.schema.stats.SchemaDiff('simple_test')
        >>> dictRes = shemDif.compareSchemas(s0, s1)
        >>> print(shemDif.getCountsOfKind())
        TP:   1   FP:   1   FN:   1  sens:  1/  2   50.0%  prec:  1/  2   50.0%  F1: 0.500
        '''
        
        diffFlatDict = {}
        for key in self.diff:
            diffFlatDict[key] = self.diff[key].flat.getElementsByClass('Label')
        return self.__getCountsOfKind(diffFlatDict, kind)

    def getStatsByKind(self, tag=''):
        '''
        Returns a string summarizing :attr:`~music21.schema.stats.SchemaDiff.diff`, kind by kind

        >>> import  music21.stream
        >>> from music21.schema import Label
        >>> s0 = music21.stream.Score()
        >>> s0.insert(0, music21.stream.Part()); s0.parts[0].id = 'A'
        >>> s0.insert(1, music21.stream.Part()); s0.parts[1].id = 'B'
        >>> s1 = music21.stream.Score()
        >>> s1.insert(0, music21.stream.Part()); s1.parts[0].id = 'A'
        >>> s1.insert(1, music21.stream.Part()); s1.parts[1].id = 'B'
        >>> # 1 TP
        >>> s0.parts[0].insert(Label(offset=1, duration=1, kind='a', tag='tag1_1'))
        >>> s1.parts[0].insert(Label(offset=1, duration=1, kind='a', tag='tag2_1'))
        >>> # 1 FP
        >>> s0.parts[0].insert(Label(offset=10, duration=1, kind='b', tag='tag1_2'))
        >>> # 1 FN
        >>> s1.parts[1].insert(Label(offset=30, duration=1, kind='a', tag='tag2_2'))
        >>> shemDif = music21.schema.stats.SchemaDiff('Compare')
        >>> dictRes = shemDif.compareSchemas(s0, s1)
        >>> print(shemDif.getStatsByKind())
          startDeltaOffset=0 - endDeltaOffset=0
            a        ==> TP:   1   FP:   0   FN:   1  sens:  1/  2   50.0%  prec:  1/  1  100.0%  F1: 0.667
            b        ==> TP:   0   FP:   1   FN:   0  prec:  0/  1    0.0%
            :::::::: ==> TP:   1   FP:   1   FN:   1  sens:  1/  2   50.0%  prec:  1/  2   50.0%  F1: 0.500
        <BLANKLINE>
        '''

        s = " %s startDeltaOffset=%s - endDeltaOffset=%s\n" % (tag, self.startDeltaOffset, self.endDeltaOffset)

        diffFlatDict = {}
        for key in self.diff:
            diffFlatDict[key] = self.diff[key].flat.getElementsByClass('Label')

        for kind in self.kinds + [None]:
#           counts = self.getCountsOfKind(kind)
            counts = self.__getCountsOfKind(diffFlatDict, kind)
            s += " %s   %-8s ==> %s\n" % (tag, kind if kind else '::::::::', counts)

        return s

    def __str__(self):
        return self.getStatsByKind()
# ------------------------------------------------------------------------------

class MutualInformationSchema(object):

    def __init__(self, schema1, schema2, affectation=(lambda label: label.tag), **kwargs):

        '''
        Compute entropy scores as defined by (Lukashevich, ISMIR 2008)

        Labels are compared through Label.compare(**kwargs) -- by default, only start and end are checked
        The affectation of Labels is the 'tag' of each label, but it can be changed by passing another function.

        so: over-segmentation score ==> information provided by schema1, knowing schema2
        su: under-segmentation score ==> information provided by schema2, knowing schema1
        '''

        nbLabels = defaultdict(int)  # nbLabels([i,j]) : number of Labels being simultaneously in the part 'i' of 'schema1' and in the part 'j' of 'schema2'
        nbLabels1 = defaultdict(int)  # nbLabels1[i]    : number of Labels in the part 'i' of 'schema1'
        nbLabels2 = defaultdict(int)  # nbLabels2[j]    : number of Labels in the part 'j' of 'schema2'
        parts1 = []
        parts2 = []
        nbAllLabels = 0

        # Iterate over all labels and build counts of Labels
        # This could be more efficient, by sorting first all the labels

        for part1 in schema1:
            for label1 in part1.getElementsByClass('Label'):
                found = False
                for part2 in schema2:
                    for label2 in part2.getElementsByClass('Label'):
                        if label1.compare(label2, **kwargs):
                            nbLabels[(affectation(label1), affectation(label2))] += 1
                            nbLabels1[affectation(label1)] += 1
                            nbLabels2[affectation(label2)] += 1
                            nbAllLabels += 1

                            if affectation(label1) not in parts1:
                                parts1.append(affectation(label1))
                            if affectation(label2) not in parts2:
                                parts2.append(affectation(label2))

                            found = True
                            break
                if not found:
                    environLocal.warn('! Label %s has no equivalent in the other schema' % label1, 'stats.py: MutualInformationSchema: __init__')

        self.nbLabels = nbLabels

        # Compute distributions
        pA = {}
        pE = {}
        pAE = {}
        pEA = {}

        for i in parts1:
            for j in parts2:
                pAE[(i, j)] = float(nbLabels[(i, j)]) / nbLabels2[j]
                pEA[(j, i)] = float(nbLabels[(i, j)]) / nbLabels1[i]

        for i in parts1:
            pA[i] = float(nbLabels1[i]) / nbAllLabels
        for j in parts2:
            pE[j] = float(nbLabels2[j]) / nbAllLabels

        # Compute conditionnal entropies
        temp = 0
        for i in parts1:
            result = 0
            for j in parts2:
                if pEA[(j, i)] > 0:
                    result += pEA[(j, i)] * math.log(pEA[(j, i)], 2)
            temp += pA[i] * result
        self.hEA = -temp

        temp = 0
        for j in parts2:
            result = 0
            for i in parts1:
                if pAE[(i, j)] > 0:
                    result += pAE[(i, j)] * math.log(pAE[(i, j)], 2)
            temp += pE[j] * result
        self.hAE = -temp

        # Compute scores
        if len(parts2) > 1:
            self.so = 1 - (self.hEA / math.log(len(parts2), 2))
        else:
            self.so = 1

        if len(parts1) > 1:
            self.su = 1 - (self.hAE / math.log(len(parts1), 2))
        else:
            self.su = 1

    def __str__(self):
        return 'hEA: %.3f, hAE: %.3f, so: %.3f, su: %.3f' % (self.hEA, self.hAE, self.so, self.su)


# ------------------------------------------------------------------------------


class TestCount(unittest.TestCase):
    def setUp(self):
        self.c = Counts()
        self.c.counts[TP] = 1
        self.c.counts[FP] = 3
        self.c.counts[FN] = 5

    def testCompute(self):
        d = {TP: None, FP: None, FN: None}
        self.assertEqual(self.c.d, d)

        self.c.compute()
        sens = (1 / float(1 + 5))
        prec = (1 / float(1 + 3))
        f1 = 2 * sens * prec / (sens + prec)

        d = {
            TP: 1, FP: 3, FN: 5,
            TP_FP: 1 + 3,
            TP_FN: 1 + 5,
            SENS: sens * 100,
            PREC: prec * 100,
            F1: f1
        }

        self.assertEqual(self.c.d, d)

    def testStr(self):
        self.c.compute()
        self.assertRegexpMatches(str(self.c), "TP: ...   FP: ...   FN: ...  sens:.../...   ....%  prec:.../...   ....%  F1: .....")


class TestComparePartsSimple(unittest.TestCase):
    def setUp(self):
        pass

    def testSimple2LabelsTP(self):
        from music21.schema import Label

        a1 = music21.stream.Part()
        a2 = music21.stream.Part()

        # 1 FP
        a1.insert(Label(offset=1, duration=1, kind='kind', tag='tag1_1'))
        a2.insert(Label(offset=1, duration=1, kind='kind', tag='tag2_1'))

        dictRes = music21.schema.stats.SchemaDiff('testSimple2LabelsTP').compareParts(a1, a2)
        self.assertEqual((len(dictRes[TP]), len(dictRes[FP]), len(dictRes[FN])), (1, 0, 0))

    def testSimple2LabelsFPFN(self):
        from music21.schema import Label

        a1 = music21.stream.Part()
        a2 = music21.stream.Part()

        # 1 FP
        a1.insert(Label(offset=1, duration=1, kind='kind', tag='tag1_1'))
        a2.insert(Label(offset=2, duration=1, kind='kind', tag='tag2_1'))

        dictRes = music21.schema.stats.SchemaDiff('testSimple2LabelsFPFN').compareParts(a1, a2)
        self.assertEqual((len(dictRes[TP]), len(dictRes[FP]), len(dictRes[FN])), (0, 1, 1))


class TestCompareParts(unittest.TestCase):

    def setUp(self):
        from music21.schema import Label

        self.a0 = music21.stream.Part()
        self.a0.id = 'S'
        self.a0.insert(Label(offset=5, kind='cad', tag='cad'))
        self.a0.insert(Label(offset=10, duration=4, kind='a', tag='a'))
        self.a0.insert(Label(offset=20, duration=4, kind='b', tag='b_oc1'))
        self.a0.insert(Label(offset=30, duration=4, kind='b', tag='b_oc2'))
        self.a0.insert(Label(offset=40, duration=4, kind='b', tag='b_oc3'))

        self.a1 = music21.stream.Part()
        self.a1.id = 'A'
        self.a1.insert(Label(offset=9, kind='cad', tag='cad'''))
        self.a1.insert(Label(offset=10, duration=4, kind='a', tag='a'''))
        self.a1.insert(Label(offset=20, duration=6, kind='b', tag='b_oc1'''))
        self.a1.insert(Label(offset=38, duration=4, kind='b', tag='b_oc3'''))

    def testStr(self):   # FIXME: test a revoir
        schemadiff = music21.schema.stats.SchemaDiff('test_str')
        schemadiff.diff[TP] = self.a0
        schemadiff.diff[FP] = self.a1
        out = '''  startDeltaOffset=None - endDeltaOffset=None\n\
    :::::::: ==> TP:   5   FP:   4   FN:   0  sens:  5/  5  100.0%  prec:  5/  9   55.6%  F1: 0.714
'''
        self.assertEqual(str(schemadiff), out)

    def testEquals(self):
        diff = music21.schema.stats.SchemaDiff('testEquals')
        dictRes = diff.compareParts(self.a0, self.a0)
        self.assertEqual((len(dictRes[TP]), len(dictRes[FP]), len(dictRes[FN])), (len(self.a0), 0, 0))

    def testDeltastartDefault(self):
        schemadiff = music21.schema.stats.SchemaDiff('testDeltastartDefault')
        schemadiff.diff = schemadiff.compareParts(self.a0, self.a1)
        self.assertEqual((len(schemadiff.diff[TP]), len(schemadiff.diff[FP]), len(schemadiff.diff[FN])), (1, 4, 3))

        self.assertEqual(schemadiff.diff[TP][0], self.a0[1])

        self.assertEqual(schemadiff.diff[FP][0], self.a0[0])
        self.assertEqual(schemadiff.diff[FP][1], self.a0[2])
        self.assertEqual(schemadiff.diff[FP][2], self.a0[3])
        self.assertEqual(schemadiff.diff[FP][3], self.a0[4])

        self.assertEqual(schemadiff.diff[FN][0], self.a1[0])
        self.assertEqual(schemadiff.diff[FN][1], self.a1[2])
        self.assertEqual(schemadiff.diff[FN][2], self.a1[3])

    def testDeltastartDefaultEndDeltaOffset1000(self):
        schemadiff = music21.schema.stats.SchemaDiff('testDeltastartDefaultEndDeltaOffset1000')
        schemadiff.diff = schemadiff.compareParts(self.a0, self.a1, endDeltaOffset=1000)
        self.assertEqual((len(schemadiff.diff[TP]), len(schemadiff.diff[FP]), len(schemadiff.diff[FN])), (2, 3, 2))  # FIXME: test a completer comme testDeltastartDefaultEndDeltaOffset1000 ?

    def testDeltaStart3DeltaEnd16(self):
        deltaOffset = 3
        schemadiff = music21.schema.stats.SchemaDiff('testDeltaStart3DeltaEnd16')
        schemadiff.diff = schemadiff.compareParts(self.a0, self.a1, startDeltaOffset=deltaOffset, endDeltaOffset=16)

        self.assertEqual((len(schemadiff.diff[TP]), len(schemadiff.diff[FP]), len(schemadiff.diff[FN])), (3, 2, 1))

        self.assertTrue(schemadiff.diff[TP][0].compare(self.a0[1], startDeltaOffset=deltaOffset))
        self.assertTrue(schemadiff.diff[TP][1].compare(self.a0[2], startDeltaOffset=deltaOffset))
        self.assertTrue(schemadiff.diff[TP][2].compare(self.a0[4], startDeltaOffset=deltaOffset))

        self.assertTrue(schemadiff.diff[FP][0].compare(self.a0[0], startDeltaOffset=deltaOffset))
        self.assertTrue(schemadiff.diff[FP][1].compare(self.a0[3], startDeltaOffset=deltaOffset))

        self.assertTrue(schemadiff.diff[FN][0].compare(self.a1[0], startDeltaOffset=deltaOffset))

    def testDeltaStartDefaultWithTwoLabelsAtSameOffsetDeltaEnd1000(self):
        from music21.schema import Label
        self.a0.insert(Label(offset=20, duration=4, kind='b', tag='b_oc1""'))

        schemadiff = music21.schema.stats.SchemaDiff('testDeltaStartDefaultWithTwoLabelsAtSameOffsetDeltaEnd1000')
        schemadiff.diff = schemadiff.compareParts(self.a0, self.a1, endDeltaOffset=1000)
        self.assertEqual((len(schemadiff.diff[TP]), len(schemadiff.diff[FP]), len(schemadiff.diff[FN])), (2, 4, 2))  # FIXME: test a completer comme testDeltastartDefaultEndDeltaOffset1000 ?


class TestComparePartsAllSameOffset(unittest.TestCase):
    def setUp(self):
        from music21.schema import Label

        self.nbLabel = 10
        self.a1 = music21.stream.Part()
        self.a2 = music21.stream.Part()

        for _ in range(0, self.nbLabel):
            self.a1.insert(Label(offset=1, duration=1, kind='kind', tag='tag'))
            self.a2.insert(Label(offset=1, duration=2, kind='kind', tag='tag1'))

    def testEquals(self):
        dictRes = music21.schema.stats.SchemaDiff('testEquals').compareParts(self.a1, self.a1)
        self.assertEqual((len(dictRes[TP]), len(dictRes[FP]), len(dictRes[FN])), (self.nbLabel, 0, 0))

    def testDefault(self):
        dictRes = music21.schema.stats.SchemaDiff('testDefault').compareParts(self.a1, self.a2)
        self.assertEqual((len(dictRes[TP]), len(dictRes[FP]), len(dictRes[FN])), (0, self.nbLabel, self.nbLabel))

    def testChecktag(self):
        dictRes = music21.schema.stats.SchemaDiff('testChecktag1').compareParts(self.a1, self.a2, endDeltaOffset=100, checkTag=False)
        self.assertEqual((len(dictRes[TP]), len(dictRes[FP]), len(dictRes[FN])), (self.nbLabel, 0, 0))

        dictRes = music21.schema.stats.SchemaDiff('testChecktag2').compareParts(self.a1, self.a2, endDeltaOffset=100, checkTag=True)
        self.assertEqual((len(dictRes[TP]), len(dictRes[FP]), len(dictRes[FN])), (0, self.nbLabel, self.nbLabel))


class TestCompareSchemas(unittest.TestCase):
    def setUp(self):
        from music21.schema import Label
        self.score0 = music21.stream.Score()

        a0 = music21.stream.Part()
        self.score0.append(a0)
        a0.id = 'S'
        a0.insert(Label(offset=10, duration=4, kind='a', tag='a_oc1'))
        a0.insert(Label(offset=20, duration=4, kind='b', tag='b_oc1'))
        a0.insert(Label(offset=30, duration=4, kind='b', tag='b_oc2'))
        a0.insert(Label(offset=40, duration=4, kind='b', tag='b_oc3'))

        a1 = music21.stream.Part()
        self.score0.append(a1)
        a1.id = 'A'
        a1.insert(Label(offset=10, duration=4, kind='a', tag='a_oc1'))
        a1.insert(Label(offset=38, duration=4, kind='b', tag='b_oc3'))

        # =====================================================================
        self.score1 = music21.stream.Score()

        a0 = music21.stream.Part()
        self.score1.append(a0)
        a0.id = 'S'
        a0.insert(Label(offset=10, duration=4, kind='a', tag='a_oc1'))
        a0.insert(Label(offset=20, duration=4, kind='b', tag='b_oc1'))
        a0.insert(Label(offset=30, duration=4, kind='b', tag='b_oc2'))

        a1 = music21.stream.Part()
        self.score1.append(a1)
        a1.id = 'A'
        a1.insert(Label(offset=20, duration=4, kind='b', tag='b_oc1'))
        a1.insert(Label(offset=38, duration=4, kind='b', tag='b_oc3'))

    def testItself(self):
        schemadiff = music21.schema.stats.SchemaDiff('testItself')
        schemadiff.compareSchemas(self.score0, self.score0)
        schemadiff.diff[TP].show('text')
        schemadiff.diff[TP].flat.show('text')
        self.assertEqual((len(schemadiff.diff[TP].flat), len(schemadiff.diff[FP].flat), len(schemadiff.diff[FN].flat)), (6, 0, 0))

    def testAnalysisAvsB(self):
        schemadiff = music21.schema.stats.SchemaDiff('testAnalysisAvsB')
        schemadiff.compareSchemas(self.score0, self.score1)
        self.assertEqual((len(schemadiff.diff[TP].flat), len(schemadiff.diff[FP].flat), len(schemadiff.diff[FN].flat)), (4, 2, 1))

    def testItselfCumulative(self):
        cumulShemDiff = music21.schema.stats.SchemaDiff('testItselfCumulative')

        schemadiff0 = music21.schema.stats.SchemaDiff('schemadiff0')
        schemadiff0.compareSchemas(self.score0, self.score0, cumulativeDiff=cumulShemDiff)
        nbTP, nbFP, nbFN = len(schemadiff0.diff[TP].flat), len(schemadiff0.diff[FP].flat), len(schemadiff0.diff[FN].flat)

        schemadiff1 = music21.schema.stats.SchemaDiff('schemadiff1')
        schemadiff1.compareSchemas(self.score1, self.score1, cumulativeDiff=cumulShemDiff)
        nbTP, nbFP, nbFN = nbTP + len(schemadiff1.diff[TP].flat), nbFP + len(schemadiff1.diff[FP].flat), nbFN + len(schemadiff1.diff[FN].flat)

        self.assertEqual((len(cumulShemDiff.diff[TP].flat), len(cumulShemDiff.diff[FP].flat), len(cumulShemDiff.diff[FN].flat)), (nbTP, nbFP, nbFN))

    def testGetCountsOfKind(self):
        schemadiff = music21.schema.stats.SchemaDiff('testGetCountsOfKind')
        schemadiff.compareSchemas(self.score0, self.score0)
        c = schemadiff.getCountsOfKind()
        self.assertEqual((c.counts[TP], c.counts[FP], c.counts[FN]), (6, 0, 0))


class TestSpeed(unittest.TestCase):
    POW = 10

    def setUp(self):
        from music21.schema import Label

        self.score0 = music21.stream.Score()
        a0 = music21.stream.Part()
        self.score0.append(a0)
        a0.id = 'S'
        for i in range(0, 2 ** self.POW):
            a0.insert(Label(offset=i, duration=4, kind='%d' % i, tag='a_oc1'))

        self.score1 = music21.stream.Score()
        a1 = music21.stream.Part()
        self.score1.append(a1)
        a1.id = 'S'
        for i in range(0, 2 ** self.POW):
            a1.insert(Label(offset=i, duration=4, kind='%d' % i, tag='a_oc1'))

    def _testAnalysisAvsB(self):
        from music21.schema import speed
        speed.speed("Begin")
        schemadiff = music21.schema.stats.SchemaDiff('testAnalysisAvsB')
        speed.speed("SchemaDiff")
        schemadiff.compareSchemas(self.score0, self.score1)
        speed.speed("compareSchemas")
        self.assertEqual((len(schemadiff.diff[TP].flat), len(schemadiff.diff[FP].flat), len(schemadiff.diff[FN].flat)), (2 ** self.POW, 0, 0))
        speed.speed("assertEqual")
        _getStats = schemadiff.getStatsByKind()
        speed.speed("getStatsByKind")



class TestMutualInformationSchema(unittest.TestCase):
    def setUp(self):
        from music21.schema import Label

        self.score1 = music21.stream.Score()
        p1 = music21.stream.Part()
        self.score1.append(p1)

        p1.insert(Label(offset=10, kind='a', tag='S'))
        p1.insert(Label(offset=20, kind='a', tag='S'))
        p1.insert(Label(offset=30, kind='b', tag='S'))
        p1.insert(Label(offset=40, kind='b', tag='A'))

        self.score2 = music21.stream.Score()
        p2 = music21.stream.Part()
        self.score2.append(p2)

        p2.insert(Label(offset=10, kind='i', tag='W'))
        p2.insert(Label(offset=20, kind='i', tag='Z'))
        p2.insert(Label(offset=30, kind='j', tag='W'))
        p2.insert(Label(offset=40, kind='j', tag='Z'))

    def testOneSchemaAgainstItself(self):
        muInSh = MutualInformationSchema(self.score1, self.score1)

#         print("test_one_schema_against_itself")
        print(muInSh, muInSh.nbLabels)

        self.assertEqual((muInSh.so, muInSh.su), (1, 1))
        self.assertEqual(muInSh.nbLabels[('S', 'S')], 3)

    def testTwoSchemas(self):
        muInSh_1vs2 = MutualInformationSchema(self.score1, self.score2, checkKind=False)
        muInSh_2vs1 = MutualInformationSchema(self.score2, self.score1, checkKind=False)

        print("testTwoSchemas : we should get reverse scores when calling 1vs2 / 2vs1")
        print(muInSh_1vs2, muInSh_1vs2.nbLabels)
        print(muInSh_2vs1, muInSh_2vs1.nbLabels)

        self.assertEqual((muInSh_1vs2.so, muInSh_1vs2.su), (muInSh_2vs1.su, muInSh_2vs1.so))

        self.assertEqual(muInSh_1vs2.nbLabels[('S', 'W')], 2)
        self.assertEqual(muInSh_1vs2.nbLabels[('S', 'Z')], 1)
        self.assertEqual(muInSh_1vs2.nbLabels[('A', 'W')], 0)
        self.assertEqual(muInSh_1vs2.nbLabels[('A', 'Z')], 1)

    def testTwoSchemasOnKind(self):
        muInSh = MutualInformationSchema(self.score1, self.score2, (lambda label: label.kind), checkKind=False)
        print("test twoSchemasOnKind : perfect scores here")
        print(muInSh, muInSh.nbLabels)

        self.assertEqual((muInSh.so, muInSh.su), (1, 1))
        self.assertEqual(muInSh.nbLabels[('a', 'i')], 2)

# -----------------------------------------------------------------------------
_DOC_ORDER = [SchemaDiff, MutualInformationSchema, Counts]

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    music21.mainTest(
        TestCount,
        TestComparePartsSimple,
        TestCompareParts,
        TestComparePartsAllSameOffset,
        TestCompareSchemas,
        TestMutualInformationSchema
    )
