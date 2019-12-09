# tX (translationConverter) Tools

All scripts here run on Python3.6 (3.7?) and up. (Tested on Python3.8 on Ubuntu Linux.)


A collection of short scripts to interface with the Door43 Content System (DCS) tX system.

tX consists of linters and converters running in Docker containers
    to convert DCS Gitea repos to Door43 web pages.
    (See https://forum.ccbt.bible/t/door43-org-tx-development-architecture/65.)

These scripts are (most generally useful to most specialized):
 - submit_Door43_tX_render.py can be given a list of DCS repos to render by activating tX
 - trigger_DCS_webhooks.py goes back a step and triggers the actual webhooks if they exist (but may require DCS admin permission)
 - submit_one_Door43_test.py allows a JSON payload to be pasted in and submitted to tX system
 - submit_Door43_tests reads JSON payloads from disk and submits them to tX system
 - submit_tX_tests.py allows a JSON payload to be submitted to only the tX (2nd) stage of the system
