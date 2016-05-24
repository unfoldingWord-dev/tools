# Door43 Tools

### NOTICE: These files have been moved to the _uw_tools_ library
* git_wrapper.py
* smartquotes.pu
* update_catalog.py

### NOTICE: These files have been moved to the _uw-publish_ project:
* json_tn_export.py - renamed to export_tn_tw_tq.py
* usfm_tS_import.py - renamed to import_bible.py

-----

We are now using the issue tracker in the Door43 repo for manages tasks:
https://github.com/unfoldingWord-dev/Door43/issues.

Door43 tools for rendering and exporting Door43 pages and media. Project Homepage: http://door43.org/en/dev/tools.

The directory structure is organized like this: `<Door43 project>/<tool>`. This is so that tools 
designed to process specific projects can be easily organized and used. Tools that work across all projects are 
located in the top-level `general_tools` directory.

### Installing _uw_tools_ and other Python dependencies

    pip install -r requirements.txt
    