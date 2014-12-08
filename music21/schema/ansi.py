'''
Terminal output for an analysis schema (:class:`~music21.stream.Score` containing :class:`~music21.schema.Label`).
'''

import math
import unittest


class AnsiLabel(object):
    def __init__(self, label, styleSheet):
        self.label = label

        self._styleBegin = ''
        self._styleEnd = ''

    def renderOnLine(self, xZoom, line):
        start = int(self.label.offset * xZoom)
        width = max(1, int(self.label.duration.quarterLength * xZoom))

        if self.label.duration.quarterLength:
            tag = self.label.tag
        else:
            # Label with no length, put a '+' to see precisely where it is
            tag = '+' + self.label.tag

        line.addText(start, '-' * width, self._styleBegin, self._styleEnd)
        line.addText(start, tag, self._styleBegin, self._styleEnd)


class AnsiLine(object):

    NAME_WIDTH = 10

    def __init__(self, scan, styleSheet):
        self._name = scan.id

        self._labels = []
        self.out = []

        for label in scan.getElementsByClass('Label'):
            self._labels.append(AnsiLabel(label, styleSheet))

    def addText(self, pos, text, styleBegin, styleEnd):
        for i, c in enumerate(text):
            if pos + i < len(self.out):
                self.out[pos + i] = styleBegin + c + styleEnd

    def render(self, xZoom, size):
        self.out = [' '] * size
        for label in self._labels:
            label.renderOnLine(xZoom, self)

        return '%*s %s|\n' % (AnsiLine.NAME_WIDTH, self._name, ''.join(self.out))


class AnsiSchema(object):
    '''
    An object to display a Schema using a :class:`~music21.schema.style` `styleSheet`

    >>> import music21
    >>> from music21.schema import Label
    >>> s = music21.stream.Score()
    >>> s.id = 'Score'
    >>> p = music21.stream.Part()
    >>> s.append(p)
    >>> p.id = 'S'
    >>> p.insert(Label(offset=10, duration=4, kind='a'))
    >>> p.insert(Label(offset=20, duration=4, kind='b'))
    >>> print(music21.schema.ansi.AnsiSchema(s).render())
    === Score
             S                     a-------            b-------       |
    <BLANKLINE>
    '''

    SCHEMA_WIDTH = 80

    _DOC_ATTR = {
        'name': '''
            the name
            '''
    }

    def __init__(self, score, styleSheet=None):
        self.name = score.metadata.title if score.metadata else score.id  # schema.name

        self._lines = []
        self._highestOffset = max(score.highestTime, score.highestOffset) + 3

        for scan in score.parts:
            self._lines.append(AnsiLine(scan, styleSheet))

        self._xZoom = None

    def render(self, xZoom=None):

        self._xZoom = float(self.SCHEMA_WIDTH - AnsiLine.NAME_WIDTH) / float(self._highestOffset) if self._highestOffset else 1.00

        # Round to nearest power of 2
        self._xZoom = math.pow(2, int(math.log(self._xZoom, 2)))

        if not xZoom:
            xZoom = self._xZoom

        # todo: Graduations

        out = '=== %s' % self.name
        out += '\n'

        for line in self._lines:
            out += line.render(xZoom, int(self._highestOffset * xZoom) + 1)

        return out

    def __str__(self):
        return self.render()


# -----------------------------------------------------------------------------
class Test(unittest.TestCase):

    def setUp(self):
        pass

# -----------------------------------------------------------------------------
_DOC_ORDER = [AnsiSchema, AnsiLine, AnsiLabel]

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
