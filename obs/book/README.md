Markdown Export
================

These scripts export the content of [Open Bible
Stories](http://door43.org/en/obs/01-the-creation) in (nearly) print-ready formats.

PDF (pdf)
---------

* Exported files are Adobe Portable Document format formatted according to
  a template and typeset with advanced typesetting rules. This output will be
  higher quality that generating your own PDF's from the other document
  formats.
* Run `$ pdf_export.sh -h` to see detailed options.
* Multiple languages can be run at once bu specifying multiple `-l LANG` flags

OpenDocument (odt)
------------------

* Exported text is OpenDocument (.odt) and formatted according to a template.
* Run command with language code to process: `$ odt_export.sh en` or `$ odt_export.sh "en fa"`.
* Exported content is available via the Door43 media manager, (`exports/<langcode>/obs/odt`)

Word (docx)
-----------

