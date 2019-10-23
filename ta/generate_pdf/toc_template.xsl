<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:outline="http://wkhtmltopdf.org/outline"
                xmlns="http://www.w3.org/1999/xhtml">
  <xsl:output doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
              doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
              indent="yes" />
  <xsl:template match="outline:outline">
    <html>
      <head>
        <title>Table of Contents</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style>
          @import url('https://fonts.googleapis.com/css?family=Noto+Sans');
          @import url('https://fonts.googleapis.com/css?family=Noto+Serif');

          body {
            font-family: 'Noto Serif', 'Noto Sans', sans-serif, arial;
            font-size: 16px;
          }
          h1 {
            text-align: center;
            font-size: 2em;
          }
          div {border-bottom: 1px dashed rgb(200,200,200); clear:both; height: 1em;}
          span {float: right;}
          a {float: left;}
          li {list-style: none;}
          ul {padding-left: 0em}
          ul ul {padding-left: 1em}
          a {text-decoration:none; color: black;}
          .title, .page {
            margin-bottom: 1px;
            background-color: white;
            overflow: auto;
            white-space: nowrap;
          }
        </style>
      </head>
      <body>
        <h1>Table of Contents</h1>
        <ul><xsl:apply-templates select="outline:item/outline:item"/></ul>
      </body>
    </html>
  </xsl:template>
  <xsl:template match="outline:item">
    <li>
      <xsl:if test="@title!=''">
        <div>
          <a class="title">
            <xsl:if test="@link">
              <xsl:attribute name="href"><xsl:value-of select="@link"/></xsl:attribute>
            </xsl:if>
            <xsl:if test="@backLink">
              <xsl:attribute name="name"><xsl:value-of select="@backLink"/></xsl:attribute>
            </xsl:if>
            <xsl:value-of select="@title" />
          </a>
          <span class="page"> <xsl:value-of select="@page" /> </span>
        </div>
      </xsl:if>
      <ul>
        <xsl:comment>added to prevent self-closing tags in QtXmlPatterns</xsl:comment>
        <xsl:apply-templates select="outline:item"/>
      </ul>
    </li>
  </xsl:template>
</xsl:stylesheet>
