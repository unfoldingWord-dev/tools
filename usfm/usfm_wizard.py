# -*- coding: utf-8 -*-
# Wizard style, GUI interface for USFM file processing
#

import configmanager
import tkinter
from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import messagebox
import os
import re
import sys
import time
import threading
import g_selectProcess
import g_txt2USFM
import g_verifyUSFM
import g_UsfmCleanup
import g_MarkParagraphs
import g_verifyManifest
import g_usfm2usx
from txt2USFM import main
from verifyUSFM import main
from usfm_cleanup import main
from mark_paragraphs import main
from revertChanges import main
from usfm2usx import main
from verifyManifest import main

app_version = "1.1.0"

class UsfmWizard(tkinter.Tk):
    def __init__(self):
        super().__init__()

        self.title('USFM Wizard')
        self.config = configmanager.ToolsConfigManager()
        mainframe = Frame(self, height=600, width=1040)
        mainframe.grid(column=0, row=0, sticky="nsew")
        
        self.titleframe = Title_Frame(parent=mainframe, controller=self, height=25)
        self.titleframe.grid(row=0, column=0, sticky="nsew")
        self._build_steps(mainframe)
        self.process = 'SelectProcess'
        self.activate_step('SelectProcess')
        self.bind('<<ScriptMessage>>', self.onScriptMessage)
        self.bind('<<ScriptProgress>>', self.onScriptProgress)
        self.bind('<<ScriptEnd>>', self.onScriptEnd)
        self.progress_lock = threading.Lock()

    def _build_steps(self, mainframe):
        self.steps = {}
        for S in (g_selectProcess, g_txt2USFM, g_verifyUSFM, g_UsfmCleanup, g_MarkParagraphs, g_verifyManifest,
                   g_usfm2usx):
            # stepname = S.stepname
            stepclass = getattr(sys.modules[S.__name__], S.stepname)
            step = stepclass(mainframe, mainapp=self)   # create an instance of the class
            self.steps[S.stepname] = step
        for child in self.winfo_children():
            child.grid_configure(padx=25, pady=5)

    def execute_script(self, module, count):
        self.titleframe.start_progress(count)
        self.titleframe.tkraise()
        self.progress = ""
        self.current_script_module = sys.modules[module]
        target = getattr(self.current_script_module, "main")
        self.thread = threading.Thread(target=target, args=(self, ))
        self.thread.start()
        self.titleframe.increment_progress(0)

    def onScriptMessage(self, event):
        with self.progress_lock:
            copystr = self.progress
            self.progress = ""
        if copystr:
            self.current_step.onScriptMessage(copystr)

    def onScriptProgress(self, event):
        self.onScriptMessage(event)
        self.titleframe.increment_progress()

    def onScriptEnd(self, event):
        time.sleep(0.2)     # show completeness this much longer before removing progress bar
        self.thread.join()
        with self.progress_lock:
            copystr = self.progress
            self.progress = ""
        self.current_step.onScriptEnd(copystr)
        self.titleframe.stop_progress()

    def set_process(self, selection):
        self.process = selection

    # Activates the previous step
    def step_back(self):
        gotostep = None
        match self.current_step.name():
            case 'MarkParagraphs':
                gotostep = 'UsfmCleanup'
            case 'Txt2USFM':
                gotostep = 'SelectProcess'
            case 'Usfm2Usx':
                gotostep = 'VerifyUSFM'
            case 'UsfmCleanup':
                gotostep = 'VerifyUSFM'
            case 'VerifyManifest':
                gotostep = 'MarkParagraphs'
            case 'VerifyUSFM':
                if self.process in {'Usfm2Usx', 'VerifyUSFM'}:
                    gotostep = 'SelectProcess'
                else:
                    gotostep = 'Txt2USFM'
        if gotostep:
            self.activate_step(gotostep)

    # Activates the next step, based the current process and what step we just finished.
    def step_next(self, copyparms=None):
        gotostep = None
        match self.current_step.name():
            case 'MarkParagraphs':
                gotostep = 'VerifyManifest'
            case 'SelectProcess':
                if self.process == 'Usfm2Usx':
                    gotostep = 'VerifyUSFM'
                else:
                    gotostep = self.process
            case 'Txt2USFM':
                gotostep = 'VerifyUSFM'
            case 'UsfmCleanup':
                gotostep = 'MarkParagraphs'
            case 'VerifyUSFM':
                if self.process == 'Usfm2Usx':
                    gotostep = 'Usfm2Usx'
                else:
                    gotostep = 'UsfmCleanup'
        if gotostep:
            self.activate_step(gotostep, copyparms)

    # I intend to bypass the stepname indirection at some point.
    def activate_step(self, stepname, copyparms=None):
        self.current_step = self.steps[stepname]
        self.titleframe.step_label['text'] = self.current_step.title()
        section = self.config.get_section(stepname)
        if copyparms:
            for parm in copyparms:
                section[parm] = copyparms[parm]
            self.config.write_section(stepname, section)
        self.current_step.show(section)

    # Called by one of the GUI modules.
    # Saves the specified values in the config file.
    def save_values(self, stepname, values):
        self.config.write_section(stepname, values)

class Title_Frame(Frame):
    def __init__(self, parent, controller, height):
        super().__init__(parent)
        self.step_label = ttk.Label(self, font='TKHeadingFont')
        self.step_label.grid(row=1, column=1, padx=(0,25))
        self.progressbar = ttk.Progressbar(self, length=235, orient='horizontal', mode='determinate')

    def start_progress(self, n):
        self.progressbar['maximum'] = n
        self.progressbar.grid(row=1, column=2, sticky="ew")
        # self.update()   # this may be unnecessary after I get the threads going
    def increment_progress(self, delta=1):
        self.progressbar['value'] += delta
    def stop_progress(self):
        self.progressbar.stop()
        self.progressbar.grid_forget()

def create_menu(wizard):
    wizard.option_add('*tearOff', FALSE)  # essential to have a normal menu
    menubar = Menu(wizard)
    menu_file = Menu(menubar)
    menubar.add_cascade(menu=menu_file, label='File')
    menu_file.add_command(label='Exit', command=exit_wizard)
    menu_help = Menu(menubar)
    menubar.add_cascade(menu=menu_help, label='Help')
    menu_help.add_command(label='Documentation', command=read_the_docs)
    menu_help.add_command(label='About', command=about)
    wizard['menu'] = menubar

def read_the_docs(*args):
    os.startfile(r'https://wycliffeassociatesinc-my.sharepoint.com/:w:/g/personal/larry_versaw_wycliffeassociates_org/EVOk8ijgv-hOkdNo2T--mmsBhlNzHiwDd2v3JQ44XN_Ciw?e=y6ww9j')
def about(*args):
    configpath = wizard.config.config_path()
    messagebox.showinfo(title='About USFM Wizard', message=f"Version {app_version}",
                        detail=f"Config file: {configpath}")
def exit_wizard(*args):
    wizard.destroy()
    # It would be nice if I killed any threads that are still running here.

if __name__ == "__main__":
    wizard = UsfmWizard()
    create_menu(wizard)
    # wizard.attributes("-topmost", 1)
    wizard.mainloop()
