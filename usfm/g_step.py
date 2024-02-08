# -*- coding: utf-8 -*-
# Base class for graphical user interface classes for USFM steps.

from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
import os
import g_util

class Step:
    def __init__(self, mainframe, mainapp, stepname, title):
        self.main_frame = mainframe
        self.mainapp = mainapp
        self.stepname = stepname
        self.steptitle = title
        self.frame = None

    def show(self, values):
        self.values = values
        self.frame.show_values(values)
        self.frame.tkraise()

    def title(self):
        return self.steptitle
    def name(self):
        return self.stepname

    def onBack(self):
        self.mainapp.step_back()
    # Advance to next step, defaulting the values of the named parameters, if any.
    def onNext(self, *parms):
        copyparms = {parm: self.values[parm] for parm in parms} if parms else None
        self.mainapp.step_next(copyparms)

    def onExecute(self):
        pass

    # Called by the main app.
    # Displays the specified string in the message area.
    def onScriptMessage(self, progress):
        self.frame.show_progress(progress)

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if status:
            self.frame.show_progress(status)
        self.frame.onScriptEnd()

    # Prompts the user for a folder, using the parent of the specified default folder as the starting point.
    # Sets dirpath to the selected folder, or leaves it unchanged if the user cancels.
    def askdir(self, dirpath: StringVar):
        initdir = dirpath.get()
        if os.path.isdir(initdir):
            initdir = os.path.dirname(initdir)
        path = filedialog.askdirectory(initialdir=initdir, mustexist=False, title = "Select Folder")
        if path:
            dirpath.set(path)

    # Prompts the user to locate a usfm file in the specified source_dir.
    # Sets filename to the selected file, or leaves it unchanged if the user cancels.
    def askusfmfile(self, source_dir: StringVar, filename: StringVar):
        path = filedialog.askopenfilename(initialdir=source_dir.get(), title = "Select usfm file",
                                           filetypes=[('Usfm file', '*.usfm')])
        if path:
            filename.set(os.path.basename(path))
