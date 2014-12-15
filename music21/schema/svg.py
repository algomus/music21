# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         svg.py
# Purpose:      Render analysis schema in .svg
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
This modules provides a .svg output for a score with an analysis schema
(:class:`~music21.stream.Score` containing :class:`~music21.schema.Label`).
The rendering details of the Labels are set by a :class:`~music21.schema.Stylesheet`,
based on the 'kind' of each Label

When they are created, SvgLabel/SvgLine/SvgSchema objects must compute the 'height' property.
Then, they may be rendered at a given 'xZoom' / 'y' position.
'''


from music21 import environment
_MOD = 'schema/svg.py'
environLocal = environment.Environment(_MOD)


from music21.schema.colors import Color
import music21.schema
import music21.stream
import math


class SvgWriter(object):
    # TODO: should we extend instead an existing xml module ?

    '''
    Renders elements according to the given zIndex.
    Render a svg element with a dictionary of attributes

    >>> from  music21.schema.svg import SvgWriter
    >>> svg_rect= SvgWriter('rect', {'x': 1, 'y': 1, 'height': 30,'width': 50, 'opacity': '0.1'})
    >>> svg_text= SvgWriter('text', {'x': 5, 'y': 20}, 'Hello')
    >>> writer = SvgWriter()
    >>> writer.add(svg_rect, 1)
    >>> writer.add(svg_text, 0)
    >>> writer.render()
    '<g ><text x="5" y="20">Hello</text>\\n<rect height="30" opacity="0.1" width="50" x="1" y="1"/></g>'

    '''

    def __init__(self, element='g', attributes=None,
                 content=None,
                 allowSelfClosing=True):  # content: text TODO
        self.element = element
        self.attributes = attributes if attributes else {}
        self.children = []
        self.content = content if content else ''
        self.allowSelfClosing = allowSelfClosing

    def add(self, element, zIndex=0):
        self.children.append((zIndex, element))

    def __iadd__(self, element):
        self.add(element)
        return self

    def getSortedChildren(self):
        '''Sort children

        >>> from  music21.schema.svg import SvgWriter
        >>> writer = SvgWriter()
        >>> writer.add("element1",1)
        >>> writer.add("element2",2)
        >>> writer.add("element3",2)
        >>> writer.add("element4",3)
        >>> writer.add("element5",0)
        >>> writer.getSortedChildren()
        ['element5', 'element1', 'element2', 'element3', 'element4']
        '''

        return [child for (_zIndex, child) in sorted(self.children, key=lambda x: x[0])]

    def render(self):
        '''
        Render into a string. This is called once by svgSchemaSet(), at the end
        '''
        s = ''
        if self.element:
            s += '<%s ' % self.element
            s += ' '.join('%s="%s"' % (k, v) for (k, v) in sorted(self.attributes.items()))
        if self.content or self.children or (not self.allowSelfClosing):
            if self.element:
                s += '>'
            s += str(self.content)
            s += '\n'.join([str(c) for c in self.getSortedChildren()])
            if self.element:
                s += '</%s>' % self.element
        else:
            # self-closing tag
            if self.element:
                s += '/>'

        return s

    def renderToRoot(self, d=None):
        '''Render the SvgWriter into a root <svg>'''

        if d is None:
            d = {}

        d['xmlns'] = "http://www.w3.org/2000/svg"
        root = SvgWriter('svg', d, self)
        return root

    def __str__(self):
        return self.render()



##############################################
#    Graphic primitives to draw Labels


class SvgLabel(object):
    '''
    Base class of a drawed Label.
    '''

    _last = 0
    hasScore = False
    noLine = True
    cssClass = 'label'

    def __init__(self, label, styleSheet):
        self.label = label
        self._style = styleSheet[label.kind]
        self.height = 0        # Height of the label
        self.heightBottom = 0  # Height to be reserved at the bottom of the schema, when the label is not placed into a line

        SvgLabel._last += 1
        self._number = SvgLabel._last

    @property
    def number(self):
        return self._number

    def start(self, xZoom):
        return SvgSchema.LINE_NAME_WIDTH + self.label.offset * xZoom

    def middle(self, xZoom):
        return SvgSchema.LINE_NAME_WIDTH + (self.label.offset + self.label.duration.quarterLength / 2) * xZoom

    def end(self, xZoom):
        return SvgSchema.LINE_NAME_WIDTH + (self.label.offset + self.label.duration.quarterLength) * xZoom

    def width(self, xZoom):
        return self.label.duration.quarterLength * xZoom


class Box(SvgLabel):

    '''
    A box attached to a Part.
    Can be used to represent a pattern, a section

    Used style properties: (TODO -> better document)
       boxHeight
       boxRoundedCorners

       boxTextXPadding
       boxTextColor
       fontSize
       fontFamily

       color
       opacity
       zIndex
    '''

    hasScore = True
    noLine = False

    def __init__(self, label, styleSheet):
        SvgLabel.__init__(self, label, styleSheet)
        self.height = self._style.boxHeight

    def render(self, svgWriter, xZoom, y, oHeight=0):

        svgCode = SvgWriter("g",
                            {
                                'id': 'label%d' % self._number,
                                'class': self.cssClass
                            })

        if self.width(xZoom):
            svgCode += SvgWriter("rect",
                                 {
                                     'x': self.start(xZoom),
                                     'y': y,
                                     'height': self._style.boxHeight,
                                     'width': self.width(xZoom),
                                     'ry': self._style.boxRoundedCorners,
                                     'fill': self._style.colorAfterOpacity.hex,
                                     'opacity': self._style.opacity,
                                 })
        svgCode += SvgWriter("text",
                             {
                                 'x': self.start(xZoom) + self._style.boxTextXPadding,
                                 'y': y + self._style.boxHeight / 2,
                                 ###
                                 # 'dominant-baseline': 'central',
                                 # is currently not supported in Inkscape : https://bugs.launchpad.net/inkscape/+bug/811862
                                 'dy': self._style.fontSize * 0.35,
                                 ###
                                 'font-size': self._style.fontSize,
                                 'font-family': self._style.fontFamily,
                                 'fill': self._style.boxTextColor.hex,
                             },
                             self.label.tag)

        svgWriter.add(svgCode, self._style.zIndex)


class GlobalBox(SvgLabel):

    '''
    A box behind the schema, spanning all voices.
    The tag is rendered at the bottom of the box.

    Used style properties: (TODO -> better document)
       fontSize
       fontFamily
       color
       opacity
       zIndex
    '''

    def render(self, svgWriter, xZoom, y, oHeight=0):

        svgCode = SvgWriter()
        svgCode += SvgWriter("rect",
                             {
                                 'x': self.start(xZoom),
                                 'y': y,
                                 'height': oHeight,
                                 'width': self.width(xZoom),
                                 'opacity': self._style.opacity,
                                 'fill': self._style.colorAfterOpacity.hex,
                             })

        if self.label.tag:
            self.heightBottom = self._style.fontSize

            svgCode += SvgWriter("text",
                             {
                                 'x': self.middle(xZoom),
                                 'y': y + oHeight + self._style.fontSize,
                                 'font-size': self._style.fontSize,
                                 'font-family': self._style.fontFamily,
                                 'text-anchor': 'middle',
                                 'style': 'fill:%s' % self._style.colorAfterOpacity.hex
                             },
                             self.label.tag)

        svgWriter.add(svgCode, self._style.zIndex)


class VerticalLine(SvgLabel):

    '''
    A vertical line that should be used to render a Label with no duration.
    The tag is rendered at the bottom of the line.

    Used style properties: (TODO -> better document)
       verticalLineWidth
       verticalLineRoundedCorners

       fontSize
       fontFamily

       color
       opacity
       zIndex
    '''

    def render(self, svgWriter, xZoom, y, oHeight=0):

        svgCode = SvgWriter()
        svgCode += SvgWriter("rect",
                             {
                                 'x': self.start(xZoom) - 2,
                                 'y': y,
                                 'height': oHeight,
                                 'width': self._style.verticalLineWidth,
                                 'ry': self._style.verticalLineRoundedCorners,
                                 'opacity': self._style.opacity,
                                 'fill': self._style.colorAfterOpacity.hex,
                             })
        if self.label.tag:
            self.heightBottom = self._style.fontSize

            svgCode += SvgWriter("text",
                                 {
                                     'x': self.start(xZoom),
                                     'y': y + oHeight + self._style.fontSize,
                                     'font-size': self._style.fontSize,
                                     'font-family': self._style.fontFamily,
                                     'text-anchor': 'middle',
                                     'style': 'fill:%s' % self._style.colorAfterOpacity.hex
                                 },
                                 self.label.tag)

        svgWriter.add(svgCode, self._style.zIndex)


class Triangle(SvgLabel):

    '''
    A triangle that should be used to render a Label with no duration.
    The triangle position and directions can be set.

    Used style properties: (TODO -> better document)
       trianglePosition
       triangleDirection
       triangleYPadding      # additional padding between top/bottom of the diagram and the triangle
       triangleScale

       fontSize
       fontFamily

       color
       opacity
       zIndex

    '''

    def __init__(self, *args, **kwargs):
        SvgLabel.__init__(self, *args, **kwargs)
        if self._style.trianglePosition == 'inLine':
            self.noLine = False

    def render(self, svgWriter, xZoom, y, oHeight=0):

        scale = self._style.triangleScale

        positionIsTop = (self._style.trianglePosition == 'top')

        if positionIsTop:
            yy = y - 4 * scale - self._style.triangleYPadding
            yDir = -1
        else:  # bottom, by default
            yy = y + oHeight + 4 * scale + self._style.triangleYPadding
            yDir = 1
            self.heightBottom = 4 * scale + self._style.triangleYPadding

        directionIsDown = (self._style.triangleDirection == 'down')

        if directionIsDown:
            yDir = -1
        else:  # bottom towards top, by default
            yDir = 1

        svgCode = SvgWriter()

        svgCode += SvgWriter("polygon",
                             {
                                 'points': '%.2f,%.2f %.2f,%.2f %.2f,%.2f' % (
                                     self.start(xZoom), yy - 4 * yDir * scale,
                                     self.start(xZoom) - 5 * scale, yy + 4 * yDir * scale,
                                     self.start(xZoom) + 5 * scale, yy + 4 * yDir * scale,),
                                 'fill': self._style.colorAfterOpacity.hex,
                             })

        if self.label.tag:

            if not positionIsTop:
                self.heightBottom = 10 * scale + self._style.fontSize * scale + self._style.triangleYPadding

            svgCode += SvgWriter("text",
                                 {
                                     'x': self.start(xZoom),
                                     'y': yy + 10 * yDir * scale,
                                     'font-size': self._style.fontSize * scale,
                                     'font-family': self._style.fontFamily,
                                     'text-anchor': 'middle',
                                     ###
                                     # 'dominant-baseline': 'central',
                                     # is currently not supported in Inkscape : https://bugs.launchpad.net/inkscape/+bug/811862
                                     'dy': self._style.fontSize * 0.35,
                                     ###
                                     'style': 'fill:%s' % self._style.colorAfterOpacity.hex
                                 },
                                 self.label.tag)

        svgWriter.add(svgCode, self._style.zIndex)





##############################################
#    SvgLine: one line of the svgSchema


class SvgLine(object):

    """"Gather several SvgLabel objects on a same 'line'."""

    def __init__(self, part, styleSheet):  # couplage fort entre SvgLine et part alors qu'on a besoin que des metadonnees (id et kind)
        # Do not enter the elements, waits for addLabel() (because some labels can be global)
        self._name = part.id  # part.name
        try:
            self._style = styleSheet[part.kind]
        except AttributeError:
            self._style = styleSheet[None]
        self._labels = []
        self._subLines = [(0, 0)]
        self.yLine = 0
        self.height = 0

    def findFreeSubLine(self, label):
        '''
        Find the first free subline for inserting the Label, or create a new one.
        Returns the index of the selected subLine.
        '''

        for i, (xLast, _height) in enumerate(self._subLines):
            if xLast <= label.label.offset:  # XXX  + EPSILON
                return i

        self._subLines.append((0, 0))
        return len(self._subLines) - 1

    def addLabel(self, label):
        # select subLine
        if self._style.lineAllowOverlaps:
            subLine = 0
        else:
            subLine = self.findFreeSubLine(label)

        # add Label
        self._labels.append((label, subLine))

        # update subLine
        (_xLast, height) = self._subLines[subLine]
        self._subLines[subLine] = (label.label.end, max(height, label.height))

        # update height
        self.height = sum([h for _, h in self._subLines])

    def render(self, svgWriter, xZoom, y, oHeight=0):
        lineY = y + self.yLine

        if self._style.lineDisplayName:
            code = SvgWriter("text",
                             {
                                 'x': SvgSchema.LINE_NAME_WIDTH - 10,
                                 'y': lineY + self.height / 2,
                                 'font-size': 10,
                                 'font-family': self._style.fontFamily,
                                 'text-anchor': "end",
                                 ###
                                 # 'dominant-baseline': 'central',
                                 # is currently not supported in Inkscape : https://bugs.launchpad.net/inkscape/+bug/811862
                                 'dy': self._style.fontSize * 0.35,
                                 ###
                             },
                             self._name)
            svgWriter.add(code, 0)

        for (label, subLine) in self._labels:
            label.render(svgWriter, xZoom, lineY + sum([h for _, h in self._subLines[:subLine]]), oHeight)


# ### one Schema

class SvgSchema(object):

    # TODO: We should move these constants to properties to the stylesheet.
    WIDTH = 1000
    LINE_NAME_WIDTH = 40  # 80 si on met les noms
    DIAG_RIGHT_MARGIN = 0
    LINE_HALF_SPACING = 4  # Half spacing between Lines. Top : one half, Middle : two halves, Bottom : one half
    HEIGHT_WHEN_EMPTY = 20
    TOP_PADDING = 3
    BOTTOM_PADDING = 3
    BAR_LINES_COLOR = Color(0, 0, 0)
    BAR_NUMBERS_COLOR = Color(0, 0, 0)

    NAME_POS_X = 10
    NAME_FONT_SIZE = 12

    def __init__(self, score, styleSheet):
        self.name = score.metadata.title if score.metadata else score.id  # schema.name
        self._lines = []

        self._height = None
        self.height = self.TOP_PADDING

        self.highestOffset = max(score.highestTime, score.highestOffset) + 3
        self._labels = []
        self._firstRatioString = _getFirstRatioString(score)
        self._styleSheet = styleSheet
        self._style = styleSheet['']
        self._scoreLabels = []

        self._xZoom = None

        for part in score.parts:
            svgLineIsEmpty = True
            line = SvgLine(part, styleSheet)

            for label in part.getElementsByClass('Label'):
                svgThisLabel = styleSheet[label.kind].svg

                l = svgThisLabel(label, styleSheet)

                if svgThisLabel.noLine:
                    self.addLabel(l)
                else:
                    line.addLabel(l)

                # Add to ._scoreLabels labels for score snippets
                if svgThisLabel.hasScore:
                    label.activeSite = part
                    if len(label.extractPattern()):
                        l.cssClass = 'clickablelabel'
                        self._scoreLabels.append((l.number, label, part))

                svgLineIsEmpty &= svgThisLabel.noLine

            if not svgLineIsEmpty:
                self.addLine(line)

        self.height += self.BOTTOM_PADDING

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        self._height = height

    @property
    def width(self):
        return self.LINE_NAME_WIDTH + self.WIDTH + self.DIAG_RIGHT_MARGIN

    @property
    def scoreLabels(self):
        return self._scoreLabels

    def addLine(self, line):
        self.height += self.LINE_HALF_SPACING
        line.yLine = self.height
        self._lines.append(line)
        self.height += line.height
        self.height += self.LINE_HALF_SPACING

    def addLabel(self, label):
        self._labels.append(label)

    def render(self, y=0, measureStream=None, fixedHighestOffset=None):
        '''
        SvgSchema rendering
        '''

        self._xZoom = float(self.WIDTH) / float(fixedHighestOffset if fixedHighestOffset is not None else self.highestOffset)
        svgWriter = SvgWriter()

        yGrid = y + self.TOP_PADDING
        oHeight = self.height - self.TOP_PADDING - self.BOTTOM_PADDING
        heightBottom = 0

        if oHeight == 0:
            oHeight = self.HEIGHT_WHEN_EMPTY
            self.height += oHeight

        for label in self._labels:
            label.render(svgWriter, self._xZoom, yGrid, oHeight)
            heightBottom = max(heightBottom, label.heightBottom)

        for line in self._lines:
            line.render(svgWriter, self._xZoom, y)

        # Place for elements that appear at the bottom
        self.height += heightBottom

        # Footer: sera recode comme une Line ajoutee seulement ici ?
        # Name, left middle
        yName = yGrid + oHeight // 2
        code = SvgWriter("text",
                         {
                             'x': SvgSchema.NAME_POS_X,
                             'y': yName,
                             'font-size': SvgSchema.NAME_FONT_SIZE,
                             'font-family': self._style.fontFamily,
                             'text-anchor': "middle",
                             'transform': "rotate(-90 10 %d)" % yName
                         },
                         self.name)
        svgWriter.add(code, 0)

        boundingBox = SvgWriter("rect",
                                {
                                    'x': 0,
                                    'y': y,
                                    'height': self.height,
                                    'width': self.width,
                                    'stroke': '#cccccc',
                                    'fill': self._style.colorBackground.hex
                                })
        svgWriter.add(boundingBox, -20)

        g = SvgWriter("g",
                      {
                          'class': 'schema',
                          'id': self.name,
                          'transform': 'translate(0,0)',
                      })
        g += svgWriter
        return g

    def save(self, filename):
        environLocal.printDebug(["SvgSchema", filename])
        root = SvgWriter('svg',
                         {
                             'xmlns': "http://www.w3.org/2000/svg",
                             'height': self.height,
                             'width': self.width,
                         })
        root += self.render()
        with open(filename, 'w') as fd:
            fd.write(root.render())



# #### several Schemas

class SvgSchemaSet(object):

    SPACE_BETWEEN_SCHEMAS = 10

    NAME_POS_X = 10
    NAME_FONT_SIZE = 16

    def __init__(self, name=''):
        self._schemas = []
        self.name = name

    @property
    def schemas(self):
        return self._schemas

    def addSchema(self, schema, style):
        svgschema = SvgSchema(schema, style)
        self._schemas.append(svgschema)

    def render(self, fixedHeight=None, measureStream=None):

        highestOffset = 0
        for s in self._schemas:
            highestOffset = max(highestOffset, s.highestOffset)
        for s in self._schemas:
            s.highestOffset = highestOffset

        ret = SvgWriter()
        height = 0
        width = 0

        if self.name:
            name = SvgWriter("text",
                             {
                                 'x': SvgSchemaSet.NAME_POS_X,
                                 'y': height + 20,
                                 'font-size': SvgSchemaSet.NAME_FONT_SIZE,
                                 'font-style': 'italic',
                                 # 'font-family': self._style.fontFamily,
                                 # 'text-anchor': "left",
                             },
                             self.name)
            ret.add(name, 0)
            height += 30

        for schema in self._schemas:
            width = schema.width
            ret += schema.render(height, measureStream)
            height += schema.height + SvgSchemaSet.SPACE_BETWEEN_SCHEMAS
        if fixedHeight is not None:
            height = fixedHeight
        else:
            height = height - SvgSchemaSet.SPACE_BETWEEN_SCHEMAS

        return ret.renderToRoot({'height': height, 'width': width}).render()

    def save(self, filename, **kwargs):
        environLocal.printDebug(["SvgSchemaSet", filename])
        with open(filename, 'w') as fd:
            fd.write(self.render(**kwargs))

