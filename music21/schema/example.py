'''
Example of using music21.schema.
'''

_DOC_IGNORE_MODULE_OR_PACKAGE = True

import copy
import unittest
import music21

import music21.converter
import music21.stream

from music21.schema import Label, style, svg, ansi, lily, web, colors
from music21.graph import PlotSchema


def buildExampleSchemas():

    # Beginning of K. 157 no 4, W. A. Mozart

    vlI = '''tinyNotation: 4/4
          c4. d8 e4 e      e8 d f e d4 r
          d4. e8 f4 f      f8 e g f e4 r
          a4. b8 c'4 c'    c'4 b a g
          g4 f e d         c4 r r2
          c'4. d'8 e'4 e'  e'8 d' f' e' d'4 r
    '''

    vc = '''tinyNotation: 4/4
          C8 C C C C C C C           GG8 GG GG GG GG4 r
          GG8 GG GG GG GG GG GG GG   C8 C C C C4 r
          F#8 F# F# F# F# F# F# F#   G8 G G G G G G G
          GG8 GG GG GG GG GG GG GG   C8 C D E F G A B
          c4 G E C                   G4 GG r2
    '''

    score = music21.stream.Score()
    score.id = "Some analysis"

    # FIXME : web and lily output should work even without makeMeasures()
    score.insert(0, music21.stream.Part(music21.converter.parse(vlI).makeMeasures()))
    score.insert(0, music21.stream.Part())
    score.insert(0, music21.stream.Part())
    score.insert(0, music21.stream.Part(music21.converter.parse(vc).makeMeasures()))

    # Labels with duration
    score.parts[0].id = "1st Violin"
    score.parts[0].insert(Label(offset=0, duration=2, kind='pattern-a', tag="a"))
    score.parts[0].insert(Label(offset=8, duration=2, kind='pattern-a', tag="a'"))
    score.parts[0].insert(Label(offset=16, duration=2, kind='pattern-a', tag="a''"))
    score.parts[0].insert(Label(offset=32, duration=2, kind='pattern-a', tag="a"))

    score.parts[1].id = "2nd Violin"

    score.parts[2].id = "Viola"
    score.parts[2].insert(Label(offset=6.5, duration=1.5, kind='pattern-d', tag="d"))
    score.parts[2].insert(Label(offset=14.5, duration=1.5, kind='pattern-d', tag="d'"))
    score.parts[2].insert(Label(offset=28.5, duration=3.5, kind='pattern-s', tag="T"))

    score.parts[3].id = "Cello"
    score.parts[3].insert(Label(offset=28.5, duration=3.5, kind='pattern-s', tag="T"))

    # score2
    score2 = copy.deepcopy(score)
    score2.id = "Another analysis"

    # Labels without duration: events, such as cadences
    part = music21.stream.Part()
    score.insert(0, part)

    part.insert(Label(offset=16, duration=8, kind='global', tag='extension'))
    part.insert(Label(offset=28, kind='cadence', tag='C:PAC'))

    part.insert(Label(offset=0, duration=8, kind='struct-1', tag='antecedent'))
    part.insert(Label(offset=8, duration=8, kind='struct-2', tag='consequent'))

    part.insert(Label(offset=37, kind='mark-1', tag='tic'))
    part.insert(Label(offset=38, kind='mark-2', tag='tac'))

    # for p in score.parts: # Should it work if the Labels are in measures ? No.
    #     p.makeMeasures(inPlace=True)

    # score.show("text")

    return score, score2


def buildExampleStyleSheet():

    mystyle = style.StyleSheet()

    # Label with a duration
    mystyle.addStyle('pattern', {'svg': svg.Box, 'opacity': 0.8, 'fontSize': 12})
    mystyle.addStyle('pattern-a', {'color': colors.Color(128, 159, 255, colors.Back.BLUE )}, parent='pattern')
    mystyle.addStyle('pattern-d', {'color': colors.Color(255,  53, 139, colors.Back.RED  )}, parent='pattern')
    mystyle.addStyle('pattern-s', {'color': colors.Color(159, 128, 255, colors.Back.GREEN)}, parent='pattern')

    mystyle.addStyle('struct-1', {'opacity': 0.4, 'svg': svg.Box, 'color': colors.Color(255, 127, 0, colors.Back.YELLOW), 'boxHeight': 10, 'fontSize': 9})
    mystyle.addStyle('struct-2', {'opacity': 0.8}, parent='struct-1')

    # Label without durations
    mystyle.addStyle('global', {'svg': svg.GlobalBox, 'zIndex': -10, 'opacity': 0.4, 'color': colors.Color(180, 180, 180)})
    mystyle.addStyle('cadence', {'svg': svg.VerticalLine, 'color': colors.RED})
    mystyle.addStyle('mark-1', {'svg': svg.Triangle})
    mystyle.addStyle('mark-2', {'svg': svg.Triangle, 'trianglePosition': 'top', 'triangleDirection': 'down'})

    return mystyle


def outputExampleSchema():

    score, score2 = buildExampleSchemas()
    styleObj = buildExampleStyleSheet()

    print("SVG:")
    # One schema in .svg
    out = svg.SvgSchema(score, styleObj)
    out.save('example-1-schema.svg')

    # Two schemas on the same .svg
    out2 = svg.SvgSchemaSet()
    out2.addSchema(score, styleObj)
    out2.addSchema(score2, styleObj)
    out2.save('example-2-schemas.svg')

    # Terminal
    print("Colored terminal ouput:")
    print(ansi.AnsiSchema(score, styleObj).render(.5))
    print(ansi.AnsiSchema(score).render())

    # Web
    print("Web:")
    web.WebSchemaSet([score, score2], styleObj).save('example.html')

    # PlotSchema
    print("PlotSchema:")
    plotSchema = PlotSchema(score, style=styleObj, figureSize=[20, 2])
    plotSchema.process()

    # Lilypond
    print("Lilypond:")
    outLily = lily.LilySchema(score, styleObj)
    outLily.write(fmt = 'lilypond', fileName = 'midi.ly', withMidiOut = True)
    outLily.show('lily.pdf')


# =============================================================================


class TestExternal(unittest.TestCase):

    def setUp(self):
        pass

if __name__ == '__main__':
    from music21 import environment
    environment.Environment()['debug'] = 1

    music21.mainTest(TestExternal, 'noDocTest')
    outputExampleSchema()
