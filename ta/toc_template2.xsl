<?xml version="1.0" encoding="UTF-8"?>
<!--
    Creates a TOC for all headers with roman numbering for h1 and decimal numbering for all others.
-->

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:outline="http://wkhtmltopdf.org/outline"
  xmlns="http://www.w3.org/1999/xhtml"
>

<xsl:output doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
  doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
  method="html"
  encoding="utf-8"
  indent="yes"
/>


<xsl:strip-space elements="*"/>

<!-- Title -->
<xsl:variable name="tocTitle">Table of Contents</xsl:variable>

<!-- "Invisible" marker for special entries -->
<xsl:variable name="tableOfFiguresMarker">&#8204;&#8204;&#8204;</xsl:variable>
<xsl:variable name="tableOfTablesMarker">&#8204;&#8204;</xsl:variable>
<xsl:variable name="tableOfLiteratureMarker">&#8204;</xsl:variable>
<xsl:variable name="zwnj">&#8204;</xsl:variable>

  <xsl:template match="outline:outline">
    <html>
      <head>
        <title><xsl:value-of select="$tocTitle"/></title>
        <!-- No external stylesheets can be used :-( -->
        <style type="text/css">
          body {
              font-size: 10pt;
              width: 14cm;
              padding: 0cm 3cm 0cm 4cm;
              margin: 0;
              border: none;
              border-width: 0;
              background-color: white; /* Transparent background */
              counter-reset: tableOf;
              width: 100%;
          }
          p.tocHeader {
              color: rgba(23, 51, 107, 255);
              font-weight: 100;
              font-size: 200%;
              margin-bottom: 1em;
          }
          .toc {
              margin-left: -1.5em;
          }
          a.tocLink {
              color: black;
              text-decoration: none;
          }

          /**************************
              Alignments
          ***************************/
          ul, li {
            width: 100%;
          }

          /* First level */
          ol>li {
              margin-left: 0em;
              margin-top: 1.5em;
              font-weight: 100;
          }

          ol>li:before {
              margin-left: -1.5em;
              float: left;
          }

          /* Standard for all */
          ol>li>ol,
          ol>li>ol>li>ol,
          ol>li>ol>li>ol>li>ol,
          ol>li>ol>li>ol>li>ol>li>ol {
              margin-left: -1.5em; /* Correlates with the font size!! */
          }

          /* Second level */
          ol>li>ol>li {
              margin-left: 0em;
              margin-top: 0em;
          }
          ol>li>ol>li:before {
              margin-left: -1.4em;
              float: left;
          }

          /* Third level */
          ol>li>ol>li>ol>li {
              margin-left: 0.9em;
              margin-top: 0em;
          }
          ol>li>ol>li>ol>li:before {
              margin-left: -2.2em;
              float: left;
          }

          /* Fourth level */
          ol>li>ol>li>ol>li>ol>li {
              margin-left: 1.6em;
              margin-top: 0em;
          }
          ol>li>ol>li>ol>li>ol>li:before {
              margin-left: -2.9em;
              float: left;
          }

          /* Fifth level */
          ol>li>ol>li>ol>li>ol>li>ol>li {
              margin-left: 2.3em;
              margin-top: 0em;
          }
          ol>li>ol>li>ol>li>ol>li>ol>li:before {
              margin-left: -3.6em;
              float: left;
          }

          /* Sixth level */
          ol>li>ol>li>ol>li>ol>li>ol>li>ol>li {
              margin-left: 3.0em;
              margin-top: 0em;
          }
          ol>li>ol>li>ol>li>ol>li>ol>li>ol>li:before {
              margin-left: -4.4em;
              float: left;
          }


          /**************************
              Numbering
          ***************************/
          /* First level */
          ol {
              counter-reset: li1;
              list-style-type: none;
          }
          ol>li:before {
              counter-increment: li1;
              content: counter(li1, upper-roman)".";
          }

          /* Second level */
          ol>li>ol {
              counter-reset: li2;
              list-style-type: none;
          }
          ol>li>ol>li:before {
              counter-increment: li2;
              content: counter(li2)".";
          }

          /* Third level Ebene */
          ol>li>ol>li>ol {
              counter-reset: li3;
              list-style-type: none;
          }
          ol>li>ol>li>ol>li:before {
              counter-increment: li3;
              content: counter(li2)"."counter(li3);
          }

          /* Fourth level */
          ol>li>ol>li>ol>li>ol {
              counter-reset: li4;
              list-style-type: none;
          }
          ol>li>ol>li>ol>li>ol>li:before {
              counter-increment: li4;
              content: counter(li2)"."counter(li3)"."counter(li4);
          }

          /* Fifth level */
          ol>li>ol>li>ol>li>ol>li>ol {
              counter-reset: li5;
              list-style-type: none;
          }
          ol>li>ol>li>ol>li>ol>li>ol>li:before {
              counter-increment: li5;
              content: counter(li2)"."counter(li3)"."counter(li4)"."counter(li5);
          }

          /* Sixth level */
          ol>li>ol>li>ol>li>ol>li>ol>li>ol {
              counter-reset: li6;
              list-style-type: none;
          }
          ol>li>ol>li>ol>li>ol>li>ol>li>ol>li:before {
              counter-increment: li6;
              content: counter(li2)"."counter(li3)"."counter(li4)"."counter(li5)"."counter(li6);
          }


          /**************************
              Special numbering for additional entries
          ***************************/
          li.to_figures, li.to_tables, li.to_literature {
              counter-increment: tableOf;
          }
          li.to_figures:before, li.to_tables:before, li.to_literature:before {
              content: counter(tableOf, upper-alpha);
          }


          /**************************
              Dot-Styles
          ***************************/
          li ol {
              margin-top: -1em;
          }
          li {
              line-height: 1.3em;
              margin-bottom: -1em;
          }
          .section {
              background-color: white;
              padding: 0 1em 0.25em 0;
              page-break-inside: avoid;
          }
          .dots {
              position: relative;
              top: -1.3em;
              white-space: nowrap;
              overflow-x: hidden;
              z-index: -999;
          }
          .dots:before {
              float: right;
              content:
                ".&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;"
                ".&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;"
                ".&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;"
                ".&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;.&#160;&#160;";
          }
          .pageNr {
              float: right;
              width: 2.3em;
              text-align: right;
              background-color: white;
          }
        </style>
      </head>
      <body>
        <p class="tocHeader"><xsl:value-of select="$tocTitle"/></p>
        <ol class="toc"><xsl:apply-templates select="outline:item/outline:item"/></ol>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="outline:item">
    <li>
      <xsl:choose>
        <xsl:when test="contains(@title, $tableOfFiguresMarker)">
          <xsl:attribute name="class">to_figures</xsl:attribute>
        </xsl:when>
        <xsl:when test="contains(@title, $tableOfTablesMarker)">
          <xsl:attribute name="class">to_tables</xsl:attribute>
        </xsl:when>
        <xsl:when test="contains(@title, $tableOfLiteratureMarker)">
          <xsl:attribute name="class">to_literature</xsl:attribute>
        </xsl:when>
      </xsl:choose>
      <xsl:if test="@title!=''">
        <!-- Überschrifteneintrag -->
        <span class="section">
          <xsl:element name="a">
            <xsl:attribute name="class">tocLink</xsl:attribute>
            <xsl:if test="@link">
              <xsl:attribute name="href"><xsl:value-of select="@link"/></xsl:attribute>
            </xsl:if>
            <xsl:if test="@backLink">
              <xsl:attribute name="name"><xsl:value-of select="@backLink"/></xsl:attribute>
            </xsl:if>
            <xsl:value-of select="translate(@title, $zwnj, '')" />
          </xsl:element>
        </span>
        <!-- Seitennummer -->
        <span class="pageNr"><xsl:value-of select="@page" /></span>
        <!-- Punkte -->
        <div class="dots"></div>
      </xsl:if>
      <xsl:if test="count(child::*[1]) > 0">
        <ol class="leaders">
          <xsl:apply-templates select="outline:item"/>
        </ol>
      </xsl:if>
    </li>
  </xsl:template>

</xsl:stylesheet>
