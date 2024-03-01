# -*- coding: utf-8 -*-
# Implements Txt2USFM and Text2USFM_Frame, which are the controller and frame
# for operating the txt2USFM.py script.
# GUI interface for merging BTTW text files and converting to USFM

from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
from idlelib.tooltip import Hovertip
import os
import g_util
import g_step

stepname = 'Plaintext2Usfm'   # equals the main class name in this module

class Plaintext2Usfm(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Convert plain text to USFM")
        self.frame = Plaintext2Usfm_Frame(parent=mainframe, controller=self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def onExecute(self, values):
        self.values = values
        count = g_util.count_files(values['source_dir'], ".*txt$")
        self.mainapp.execute_script("plaintext2usfm", count)
        self.frame.clear_status()
    def onNext(self):
        copyparms = {'source_dir': self.values['target_dir']}
        self.mainapp.step_next(copyparms)
    def onSkip(self):
        self.mainapp.step_next()

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if not status:
            status = f"The conversion is done.\nAdvance to USFM verification and cleanup."
        self.frame.show_progress(status)
        self.frame.onScriptEnd()
                
class Plaintext2Usfm_Frame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.filename = StringVar()
        self.source_dir = StringVar()
        self.target_dir = StringVar()
        for var in (self.source_dir, self.target_dir):
            var.trace_add("write", self._onChangeEntry)
        for col in [2,3]:
            self.columnconfigure(col, weight=1)   # keep column 1 from expanding
        self.columnconfigure(4, minsize=94)
        self.rowconfigure(88, minsize=170, weight=1)  # let the message expand vertically

        source_dir_label = ttk.Label(self, text="Location of text files:", width=20)
        source_dir_label.grid(row=3, column=1, sticky=W, pady=2)
        source_dir_entry = ttk.Entry(self, width=45, textvariable=self.source_dir)
        source_dir_entry.grid(row=3, column=2, columnspan=3, sticky=W)
        target_dir_Tip = Hovertip(source_dir_entry, hover_delay=1000,
                text="Folder containing the files to be converted")
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=3, column=4, sticky=W, padx=1)

        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=4, column=1, sticky=W, pady=2)
        file_entry = ttk.Entry(self, width=20, textvariable=self.filename)
        file_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        file_Tip = Hovertip(file_entry, hover_delay=500,
             text="Leave filename blank to convert all .txt files in the folder.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=4, column=3, sticky=W, padx=14)

        target_dir_label = ttk.Label(self, text="Location for .usfm files:", width=21)
        target_dir_label.grid(row=5, column=1, sticky=W, pady=2)
        target_dir_entry = ttk.Entry(self, width=45, textvariable=self.target_dir)
        target_dir_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        target_dir_Tip = Hovertip(target_dir_entry, hover_delay=1000,
                text="Folder for the new usfm files. The folder will be created if it doesn't exist.")
        target_dir_find = ttk.Label(self, text="(may be new)")
        target_dir_find.grid(row=5, column=4, sticky=W, padx=0)

        self.message_area = Text(self, height=10, width=30, wrap="none")
        self.message_area['borderwidth'] = 2
        self.message_area['relief'] = 'sunken'
        self.message_area['background'] = 'grey97'
        self.message_area.grid(row=88, column=1, columnspan=4, sticky='nsew', pady=6)
        ys = ttk.Scrollbar(self, orient = 'vertical', command = self.message_area.yview)
        ys.grid(column = 5, row = 88, sticky = 'ns')
        self.message_area['yscrollcommand'] = ys.set

        source_dir_entry.focus()

    # Called when the frame is first activated. Populate the initial values.
    def show_values(self, values):
        self.values = values
        self.filename.set(values['filename'])
        self.source_dir.set(values['source_dir'])
        self.target_dir.set(values['target_dir'])
        
        # Create buttons
        self.controller.showbutton(1, "<<<", cmd=self._onBack)
        self.controller.showbutton(2, "CONVERT", tip="Run the conversion script now.", cmd=self._onExecute)
        self.controller.showbutton(3, "Source folder",
                                   tip="Open the folder containing the files to be converted.", cmd=self._onOpenTextDir)
        self.controller.showbutton(4, "Usfm folder", cmd=self._onOpenTargetDir)
        self.controller.showbutton(5, ">>>", tip="Verify USFM", cmd=self._onSkip)
        self._set_button_status()

    # Displays status message from the running script.
    def show_progress(self, status):
        self.message_area.insert('end', status + '\n')
        self.message_area.see('end')
        self.controller.enablebutton(2, False)

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.enablebutton(2, True)
        self.controller.enablebutton(3, True)

    # Called by the controller when script execution begins.
    def clear_status(self):
        self.message_area['state'] = NORMAL   # enables insertions to message area
        self.message_area.delete('1.0', 'end')

    # Caches the current parameters in self.values and calls the mainapp to save them in the config file.
    def _save_values(self):
        self.values['filename'] = self.filename.get()
        self.values['source_dir'] = self.source_dir.get()
        self.values['target_dir'] = self.target_dir.get()
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.source_dir.get(), title = "Select text file with Scripture text",
                                           filetypes=[('Text file', '*.txt')])
        if path:
            self.filename.set(os.path.basename(path))
    def _onChangeEntry(self, *args):
        self._set_button_status()
    def _onOpenTextDir(self, *args):
        os.startfile(self.source_dir.get())
    def _onOpenTargetDir(self, *args):
        self._save_values()
        os.startfile(self.values['target_dir'])
    def _onBack(self, *args):
        self._save_values()
        self.controller.onBack()
    def _onSkip(self, *args):
        self._save_values()
        self.controller.onSkip()
    def _onNext(self, *args):
        self._save_values()
        self.controller.onNext()
    def _onExecute(self, *args):
        self._save_values()
        self.controller.onExecute(self.values)
        self.controller.showbutton(5, ">>>", tip="Verify USFM", cmd=self._onNext)

    def _set_button_status(self):
        good_sourcedir = os.path.isdir(self.source_dir.get())
        okay = (good_sourcedir and self.target_dir.get())
        self.controller.enablebutton(2, okay)
        self.controller.enablebutton(3, good_sourcedir)
        self.controller.enablebutton(4, os.path.isdir(self.target_dir.get()))
