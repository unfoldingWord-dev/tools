# -*- coding: utf-8 -*-
# GUI interface for automated USFM file cleanup
#

from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
from idlelib.tooltip import Hovertip
import g_util
import g_step
import os
import time

stepname = 'UsfmCleanup'   # equals the main class name in this module

class UsfmCleanup(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "USFM Cleanup")
        self.frame = UsfmCleanup_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def onNext(self):
        super().onNext('source_dir', 'filename')
    
    def onExecute(self, values):
        self.values = values    # redundant, they were the same dict to begin with
        count = 1
        if not values['filename']:
            count = g_util.count_files(values['source_dir'], ".*sfm$")
        self.mainapp.execute_script("usfm_cleanup", count)
        self.frame.clear_status()

    # Runs the revertChanges script to revert usfm_cleanup changes.
    def revertChanges(self):
        sec = {'source_dir': self.values['source_dir'],
               'backupExt': ".usfm.orig",
               'correctExt': ".usfm"}
        self.mainapp.save_values('RevertChanges', sec)
        self.mainapp.execute_script("revertChanges", 1)
        self.frame.clear_status()

class UsfmCleanup_Frame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.source_dir = StringVar()
        self.filename = StringVar()
        self.std_titles = StringVar()
        for var in (self.filename, self.source_dir):
            var.trace_add("write", self._onChangeEntry)
        self.enable = [BooleanVar(value = False) for i in range(8)]
        self.enable[3].trace_add("write", self._onChangeQuotes)
        self.enable[4].trace_add("write", self._onChangeQuotes)

        source_dir_label = ttk.Label(self, text="Location of .usfm files:", width=20)
        source_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        self.source_dir_entry = ttk.Entry(self, width=45, textvariable=self.source_dir)
        self.source_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=3, sticky=E)

        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=5, column=1, sticky=W, pady=2)
        self.file_entry = ttk.Entry(self, width=24, textvariable=self.filename)
        self.file_entry.grid(row=5, column=2, sticky=W)
        file_Tip = Hovertip(self.file_entry, hover_delay=500,
             text="Leave filename blank to clean all .usfm files in the folder.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=5, column=2, sticky=E)
        
        subheadingFont = font.Font(size=10, slant='italic')     # normal size is 9
        enable_label = ttk.Label(self, text="Enable these fixes?", font=subheadingFont)
        enable_label.grid(row=10, column=1, columnspan=2, sticky=W, pady=(4,2))

        enable1_checkbox = ttk.Checkbutton(self, text='Spaces', variable=self.enable[1],
                                             onvalue=True, offvalue=False)
        enable1_checkbox.grid(row=11, column=1, sticky=W)
        enable1_Tip = Hovertip(enable1_checkbox, hover_delay=500,
             text="Add spaces between comma/period/colon and a letter (recommended for most languages).")

        enable2_checkbox = ttk.Checkbutton(self, text='Punctuation', variable=self.enable[2],
                                             onvalue=True, offvalue=False)
        enable2_checkbox.grid(row=11, column=2, sticky=W)
        enable2_Tip = Hovertip(enable2_checkbox, hover_delay=500,
             text="Fix double periods, doubled angle brackets, other \"safe\" substitutions (recommended for most languages).")

        self.enable3_checkbox = ttk.Checkbutton(self, text='Double quotes          ', variable=self.enable[3],
                                             onvalue=True, offvalue=False)
        self.enable3_checkbox.grid(row=11, column=3, sticky=W)
        enable3_Tip = Hovertip(self.enable3_checkbox, hover_delay=500,
             text="Promote straight double quotes to curly quotes.")
        self.grid_columnconfigure(2, minsize=40, weight=1)

        self.enable4_checkbox = ttk.Checkbutton(self, text='All straight quotes', variable=self.enable[4],
                                             onvalue=True, offvalue=False)
        self.enable4_checkbox.grid(row=11, column=4, sticky=W)
        enable4_Tip = Hovertip(self.enable4_checkbox, hover_delay=500,
             text="Promote single and double straight quotes to curly quotes, except word-medial.")

        enable5_checkbox = ttk.Checkbutton(self, text='Capitalization', variable=self.enable[5],
                                             onvalue=True, offvalue=False)
        enable5_checkbox.grid(row=12, column=1, sticky=W)
        enable5_Tip = Hovertip(enable5_checkbox, hover_delay=500,
             text="Enforce capitalization of the first word in sentences, disregarding footnotes.")

        enable6_checkbox = ttk.Checkbutton(self, text='\s5 markers', variable=self.enable[6],
                                             onvalue=True, offvalue=False)
        enable6_checkbox.grid(row=12, column=2, sticky=W)
        enable6_Tip = Hovertip(enable6_checkbox, hover_delay=500,
             text="Remove \s5 markers (recommended for all text except GLs).")

        enable7_checkbox = ttk.Checkbutton(self, text='Section titles', variable=self.enable[7],
                                             onvalue=True, offvalue=False)
        enable7_checkbox.grid(row=12, column=3, sticky=W)
        enable7_Tip = Hovertip(enable7_checkbox, hover_delay=500,
             text="Mark obvious section titles with \s")

        self.message_area = Text(self, height=14, width=30, wrap="none")
        self.message_area['borderwidth'] = 2
        self.message_area['relief'] = 'sunken'
        self.message_area['background'] = 'grey97'
        self.message_area.grid(row=88, column=1, columnspan=4, sticky='nsew', pady=6)
        ys = ttk.Scrollbar(self, orient = 'vertical', command = self.message_area.yview)
        ys.grid(column = 5, row = 88, sticky = 'ns')
        self.message_area['yscrollcommand'] = ys.set

        prev_button = ttk.Button(self, text="<<<", command=self._onBack)
        prev_button.grid(row=99, column=1, sticky=(W,N,S))  #, pady=5)
        prev_button_Tip = Hovertip(prev_button, hover_delay=500, text="Verify usfm")

        self.execute_button = ttk.Button(self, text="CLEAN", command=self._onExecute)
        self.execute_button.grid(row=99, column=2, sticky=(W,N,S))  #, padx=0, pady=5)
        self.execute_button['padding'] = (5, 5) # internal padding!
        self.execute_button_Tip = Hovertip(self.execute_button, hover_delay=500,
                text="Run the USFM cleanup script now.")

        self.undo_button = ttk.Button(self, text="Undo", command=self._onUndo)
        self.undo_button_Tip = Hovertip(self.undo_button, hover_delay=500,
                text=f"Restore any and all .usfm.orig backup files.")

        next_button = ttk.Button(self, text=">>>", command=self._onNext)
        next_button.grid(row=99, column=4, sticky=(N,S,E))  #, padx=0, pady=5)
        next_button_Tip = Hovertip(next_button, hover_delay=500, text="Mark paragraphs")

    def show_values(self, values):
        self.values = values
        self.source_dir.set(values.get('source_dir', fallback=""))
        self.filename.set(values.get('filename', fallback=""))
        for i in range(len(self.enable)):
            configvalue = f"enable{i}"
            self.enable[i].set( values.get(configvalue, fallback = False))
        self._set_button_status()

    # Displays status messages from the running script.
    def show_progress(self, status):
        self.message_area.insert('end', status + '\n')
        self.message_area.see('end')
        self.execute_button['state'] = DISABLED
        self.execute_button['state'] = DISABLED

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.execute_button['state'] = NORMAL
        self.undo_button.grid(row=99, column=3, sticky=(W,N,S))  #, padx=0, pady=5)
        self.undo_button['padding'] = (5, 5) # internal padding!

    # Called by the controller when script execution begins.
    def clear_status(self):
        self.message_area['state'] = NORMAL   # enables insertions to message area
        self.message_area.delete('1.0', 'end')

    def _onChangeQuotes(self, *args):
        if promote_all := self.enable[4].get():    # promote all straight quotes
            self.enable[3].set(True)
        self.enable3_checkbox.state(['disabled'] if promote_all else ['!disabled'])
        if not self.enable[3].get():
            self.enable[4].set(False)

    def _save_values(self):
        self.values['source_dir'] = self.source_dir.get()
        self.values['filename'] = self.filename.get()
        for si in range(len(self.enable)):
            configvalue = f"enable{si}"
            self.values[configvalue] = str(self.enable[si].get())
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.source_dir.get(), title = "Select usfm file",
                                           filetypes=[('Usfm file', '*.usfm')])
        if path:
            self.filename.set(os.path.basename(path))
    def _onChangeEntry(self, *args):
        self._set_button_status()
    def _onBack(self, *args):
        self._save_values()
        self.controller.onBack()
    def _onUndo(self, *args):
        self._save_values()
        self.controller.revertChanges()
    def _onNext(self, *args):
        self._save_values()
        self.controller.onNext()

    def _onExecute(self, *args):
        self._save_values()
        self.controller.onExecute(self.values)
    def _onOpenIssues(self, *args):
        self._save_values()
        path = os.path.join(self.values['source_dir'], "issues.txt")
        os.startfile(path)

    def _set_button_status(self):
        good_source = os.path.isdir(self.source_dir.get())
        self.undo_button['state'] = NORMAL if good_source else DISABLED
        if good_source and self.filename.get():
            path = os.path.join(self.source_dir.get(), self.filename.get())
            good_source = os.path.isfile(path)
        self.execute_button['state'] = NORMAL if good_source else DISABLED
