# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         web.py
# Purpose:      Render analysis schema on a web page, including music21j score snippets
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
This module provides a web output for a score with an analysis schema
(:class:`~music21.stream.Score` containing :class:`~music21.schema.Label`).
It uses :class:`~music21.schema.svgSchema` and adds score snippets rendered with music21j.
'''

from music21.schema import svg
from music21.tinyNotation import TinyNotationWriter

from music21 import environment
_MOD = 'schema/web.py'
environLocal = environment.Environment(_MOD)

HEADER_INCLUDES = '''
   <script src="http://code.jquery.com/jquery.js"></script>
   <script data-main='http://web.mit.edu/music21/music21j/src/music21' src='http://web.mit.edu/music21/music21j/ext/require/require.js'></script>
<style type="text/css">

.webSchemaSet {
  width: 1050px; // See svgSchemaSet.WIDTH
  margin: 20px;
}

.scorelabel {
  font-family: Verdana, Arial, Helvetica, sans-serif;
  font-size: 11px;
  color:#fffffff;
  float: left;
  width: 200px;
  height: 70px;
}

.scorecanvas {
height: 70px;
}

.clickablelabel:hover {
  cursor: pointer;
}

.clickablelabel rect, .score {
  border-style: solid;
  border-color: #FFFFFF;
  border-width: 3px;
}

.selected rect {
  stroke: #555;
  stroke-width: 3px;
}

.mouseover rect, .clickablelabel:hover rect {
  fill: #fef8ba;
}

.scoremouseover {
  background-color: #fef8ba;
}

</style>
'''

SCRIPT_JS = '''
   <script>
   $(function() {
      var MAX_SELECTED = 5;

      var selected = {};
      var nbSelected = 0;
      var mouseover = null;

      /* Update all elements */
      function updateAll() {
          $('.clickablelabel').each(function() {
             this.setAttribute("class", "clickablelabel");
          });

          $('.score').each(function() {
             this.setAttribute("class", "score");
          });
          $('.score').hide();

          for (number in selected) {
              if (selected[number]) {
                  $('#label'+number)[0].setAttribute("class","clickablelabel selected");
                  $('#score'+number).show();
              }
          }
          if (mouseover !== null) {
              $('#label'+mouseover)[0].setAttribute("class","clickablelabel selected mouseover")
              $('#score'+mouseover)[0].setAttribute("class","score scoremouseover");
          }
      }

       /* Update one element */
       function update(number) {
           if (selected[number]) {
               $('#label'+number)[0].setAttribute("class","clickablelabel selected " + (mouseover == number ? "mouseover" : ""))
               $('#score'+number).show()
               $('#score'+number)[0].setAttribute("class", "score" + (mouseover == number ? " scoremouseover" : ""))
           } else {
               $('#label'+number)[0].setAttribute("class","clickablelabel " + (mouseover == number ? "mouseover" : ""))
               $('#score'+number).hide()
           }
      }

      function showSchema(name) {
          basename = name.split('_')[1];
          $('.schemadiv').hide();
          $('#' + basename).show();
          updateAll();
      };

      $('.schemabutton').click(function() {
          basename = this.id.split('schemabutton')[1];
          showSchema(basename);
      });

      $('.clickablelabel').click(function() {
          number = this.id.split('label')[1];
          if (selected[number]) {
              selected[number] = undefined;
              nbSelected -= 1;
              mouseover = null;
          }
          else if (nbSelected < MAX_SELECTED) {
              selected[number] = 1;
              nbSelected += 1
              mouseover = number;
          }
          update(number);

      }).mouseenter(function() {
          number = this.id.split('label')[1];
          if (selected[number]) {
              mouseover = number;
              update(number);
          }
      }).mouseleave(function() {
          number = this.id.split('label')[1];
          if (selected[number]) {
              mouseover = null;
              update(number);
          }
      });

      $('.score').mouseenter(function() {
         number = this.id.split('score')[1];
         mouseover = number;
         update(number);
      }).mouseleave(function() {
         number = this.id.split('score')[1];
         mouseover = null;
         update(number);
      });
      //showSchema(0);
      $('.schemadiv').hide();
      $('.visible-first').show();
      updateAll();
   });
   </script>
'''


COMPLETE_WEBPAGE = '''
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
   <meta http-equiv="X-UA-Compatible" content="IE=9"/>
   <meta charset="UTF-8">
   <title>%s</title>
   ''' + HEADER_INCLUDES + '''
</head>
<body>
   %s
   ''' + SCRIPT_JS + '''
</body>
</html>
'''


class WebSchemaSet(object):
    def __init__(self, scoreOrListOfScores, styleSheet, name=None, withScore=True):
        self._withScore = withScore
        self._svgSchemas = []
        if not isinstance(scoreOrListOfScores, list):
            scoreOrListOfScores = [scoreOrListOfScores]
        for score in scoreOrListOfScores:
            schema = svg.SvgSchema(score, styleSheet)
            self._svgSchemas.append(schema)

        self.severalSchemas = (len(self._svgSchemas) > 1)
        self.name = str(name) if name is not None else str(self._svgSchemas[0].name)
        self.name = self.name.replace(' ', '')

    def render(self, completeWebPage=True):
        ret = svg.SvgWriter('div',
                            {
                                'class': 'webSchemaSet',
                                'id': self.name
                            })

        if self.severalSchemas:
            for i, schema in enumerate(self._svgSchemas):
                ret += '<button class="schemabutton" id="schemabutton_%s%s">%s</button>' % (self.name, i, schema.name)

        # Render the content of the schemas in .svg
        maxHighestOffset =  max([schema.highestOffset for schema in self._svgSchemas])
        renderedSchemas = [schema.render(fixedHighestOffset=maxHighestOffset) for schema in self._svgSchemas]

        # Render the schema into <div><svg>...</svg></div> of the same height/width
        maxHeight = max([schema.height for schema in self._svgSchemas])
        maxWidth = max([schema.width for schema in self._svgSchemas])

        for i, rendered in enumerate(renderedSchemas):
            div = svg.SvgWriter('div',
                                {
                                    'class': 'schemadiv' + (' visible-first' if i == 0 else ''),
                                    'id': '%s%s' % (self.name, i)
                                })
            div += rendered.renderToRoot({'width': maxWidth, 'height': maxHeight})
            ret += div

        if self._withScore:
            for schema in self._svgSchemas:

                for idVal, label, part in schema.scoreLabels:

                    # Prepare scorelabel
                    lines = []
                    if self.severalSchemas:
                        lines += [str(schema.name)]
                    if label.tag:
                        lines += [label.tag]

                    startend = '%s' % label.offset
                    if label.duration:
                        startend += ' → %s' % label.end
                    lines += [startend]

                    if label.weight is not None:
                        lines += ['%s' % label.weight]

                    # Create divs
                    score = svg.SvgWriter('div', {'class': 'score', 'id': "score%s" % idVal})
                    score += svg.SvgWriter('div', {'class': "scorelabel"}, '<br/>'.join(lines), allowSelfClosing=False)
                    score += svg.SvgWriter('div', {'id': "scorecanvas%s" % idVal}, allowSelfClosing=False)
                    ret += score

        ret = ret.render()

        if self._withScore:
            # Prepare score snippets with music21j
            script = "<script>\n"
            script += 'require(["music21"], function () {\n'

            for schema in self._svgSchemas:
                for idVal, label, part in schema.scoreLabels:
                    label.activeSite = part
                    extract = label.extractPattern()
                    if not extract:
                        continue
                    script += '  music21.tinyNotation.TinyNotation("%s").appendNewCanvas($("#scorecanvas%s"), 800, 70);\n' % \
                              (TinyNotationWriter().streamToTinyNotation(extract), idVal)
            script += '});\n\n'
            script += "</script>"

            ret += script

        if completeWebPage:
            ret = COMPLETE_WEBPAGE % (self.name, ret)

        return str(ret)

    def save(self, filename):
        environLocal.printDebug([self.name, filename])
        with open(filename, 'w') as fd:
            fd.write(self.render())
