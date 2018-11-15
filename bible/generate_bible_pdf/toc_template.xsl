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
                <title>Table of Content</title>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                <style>
                    @import url(http://fonts.googleapis.com/css?family=Noto+Serif);
                    @import url(http://fonts.googleapis.com/css?family=Noto+Sans);
                    #toc {
                        text-align: center;
                        font-size: 22pt;
                        font-family: 'Noto Serif', 'Noto Sans', sans-serif;
                    }
                    * {                    
                        text-align: left;
                        font-size: 16pt;
                        line-height: 20pt;
                        font-family: 'Noto Serif', 'Noto Sans', sans-serif;
                    }
                    .toclink {
                        text-decoration:none;
                        color: black;
                    }
                    .before {
                        padding-right: 0.33em;
                        background: white;
                    }
                    .after {
                        float:right;
                        padding-left: 0.33em;
                        background: white;
                    }
                    <xsl:if test="not((@type)='xhtml')">
                    .before:before{
                        float: left;
                        width: 0;
                        font-size: 6pt;
                        white-space: nowrap;
                        content:
                        ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . "
                    }
                    </xsl:if>
                    #top {
                        width:97%;
                        overflow:hidden;
                    }
                    .tocul {
                        list-style: none outside none;
                        padding-left:1.3em;
                    }
                    uuuuul ul ul {
                        display: none;
                    }
                </style>
                <script>
                     function subst() {
                        var lang = '{{Language}}';
                        var toc = document.getElementById('toc');
                        toc.textContent = 'Table of Contents';
                    }
                </script>
            </head>
            <body onload="subst()">
                <h1 id="toc">Table of Contents</h1>
                <ul class="tocul" id="top">
                    <xsl:if test="(@type)='xhtml'">
                        <xsl:apply-templates select="outline:item/outline:item">
                            <xsl:with-param name="type" select="'xhtml'"/>
                        </xsl:apply-templates>
                    </xsl:if>

                    <xsl:if test="not((@type)='xhtml')">
                        <xsl:apply-templates select="outline:item/outline:item">
                            <xsl:with-param name="type" select="'notxhtml'"/>
                        </xsl:apply-templates>
                    </xsl:if>
                </ul>
            </body>
            <script type="text/javascript" language="javascript">
            </script>
        </html>
    </xsl:template>
    <xsl:template match="outline:item">
        <xsl:param name="type" select="'pdf'"/>
        <li>
            <xsl:if test="@title!='' and  @title!='Table of Contents' and  @title!='Contents' and  @title!='Sisällysluettelo' ">
                <div>
                    <span class="before">
                        <a class="toclink">
                            <xsl:choose>
                                <xsl:when test="@inhtmllink">
                                    <xsl:attribute name="href">
                                        <xsl:value-of select="@inhtmllink"/>
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:attribute name="href">
                                        <xsl:value-of select="@link"/>
                                    </xsl:attribute>
                                </xsl:otherwise>
                            </xsl:choose>
                            <xsl:if test="@backLink">
                                <xsl:attribute name="name">
                                    <xsl:value-of select="@backLink"/>
                                </xsl:attribute>
                            </xsl:if>
                            <xsl:value-of select="@title" />
                        </a>
                    </span>
                    <xsl:if test="$type = 'notxhtml'"> <!-- Do not display page numbers for XHTML publications -->
                        <span class="after">
                            <xsl:value-of select="@page" />
                        </span>
                    </xsl:if>
                </div>
            </xsl:if>
            <ul class="tocul">
                <xsl:comment>added to prevent self-closing tags in QtXmlPatterns</xsl:comment>
                <xsl:apply-templates select="outline:item">
                    <xsl:with-param name="type" select="$type"/>
                </xsl:apply-templates>
            </ul>
        </li>
    </xsl:template>
</xsl:stylesheet>
