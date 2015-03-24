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
# Copyright:    Copyright © 2012-2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
# ------------------------------------------------------------------------------
'''
Example of using the music21.schema module to display key analysis result on each measure
(KrumhanslSchmuckler) in svg, web and plot.
A score without music is parallely updated to show that analysis schemas does
not depend on actual music.
'''
from music21.analysis.discrete import KrumhanslSchmuckler, DiscreteAnalysisException
from music21.schema import style, svg, ansi, Label, web
from music21.schema.colors import Color, Back
from music21.stream import Measure, Part, Score
from music21 import corpus
from music21.graph import PlotSchema

_DOC_IGNORE_MODULE_OR_PACKAGE = True

def main():
    piece = corpus.parse('bwv66.6')

    pieceWithoutMusic = Score()
    processor = KrumhanslSchmuckler()

    for part in piece.parts:
        partWithoutMusic = Part()

        for m in part.getElementsByClass(Measure):
            try:
                solution = processor.getSolution(m)
                t = solution.name
                k = 'key-major' if 'major' in t else 'key-minor'
            except DiscreteAnalysisException:
                t = "?"
                k = ''
            keyLabel = Label(offset=m.offset, duration=m.duration, kind=k, tag=t)
            part.insert(keyLabel)
            partWithoutMusic.insert(keyLabel)

        pieceWithoutMusic.insert(partWithoutMusic)

    svgSchema = svg.SvgSchemaSet()
    keyStyle = style.StyleSheet()
    keyStyle.addStyle('key-major', {'color': Color(0, 255, 0, Back.GREEN)})
    keyStyle.addStyle('key-minor', {'color': Color(255, 200, 0, Back.YELLOW)})

    svgSchema.addSchema(piece, keyStyle)

    # svg
    svgSchema.save('example-keyAnalysis.svg')
    print(ansi.AnsiSchema(piece, keyStyle))

    # web
    webSchema = web.WebSchemaSet(piece, keyStyle, name="KrumhanslSchmuckler on each measure")
    webSchema.save('example-keyAnalysis.html')

    # web, displaying pieceWithoutMusic - note that we do not follow the correct measures here
    webSchema = web.WebSchemaSet(pieceWithoutMusic, keyStyle, name="KrumhanslSchmuckler on each measure, without music")
    webSchema.save('example-keyAnalysis-withoutMusic.html')

    # plot
    plotSchema = PlotSchema(piece, style=keyStyle, figureSize=[20, 2])
    plotSchema.process()


if __name__ == '__main__':
    main()
