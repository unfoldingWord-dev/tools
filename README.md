# Door43 Tools

### NOTICE: Issues are tracked in https://github.com/unfoldingWord-dev/door43.org/issues and Wiki pages at https://github.com/unfoldingWord-dev/door43.org/wiki
### NOTICE: These files have been moved to the _uw_tools_ library
* git_wrapper.py
* smartquotes.pu
* update_catalog.py

### NOTICE: These files have been moved to the _uw-publish_ project:
* json_tn_export.py - renamed to export_tn_tw_tq.py
* usfm_tS_import.py - renamed to import_bible.py

-----


The directory structure is organized like this: `<Door43 project>/<tool>`. This is so that tools 
designed to process specific projects can be easily organized and used. Tools that work across all projects are 
located in the top-level `general_tools` directory.

### Installing _uw_tools_ and other Python dependencies

    pip install -r requirements.txt
    
Also need to install these applications:
* https://pandoc.org
* https://wkhtmltopdf.org - note that version 0.12.4 has problems with sizing text.  We are currently using version 0.12.3. 

