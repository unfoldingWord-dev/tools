# -*- coding: utf-8 -*-
# GUI interface for verifying manifest.yaml file and readiness of resource container.
#

from tkinter import *
from tkinter import ttk
from tkinter import font
# from tkinter import filedialog
from idlelib.tooltip import Hovertip
import g_util
import g_step
import os
import subprocess
import time

stepname = 'VerifyManifest'   # equals the main class name in this module

class VerifyManifest(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Verify manifest.yaml")
        self.frame = VerifyManifest_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def onExecute(self, values):
        self.values = values
        self.mainapp.execute_script("verifyManifest", 1)
        self.frame.clear_status()

class VerifyManifest_Frame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.source_dir = StringVar()
        self.source_dir.trace_add("write", self._onChangeEntry)
        self.columnconfigure(2, weight=1)   # keep column 1 from expanding
        self.rowconfigure(88, minsize=170, weight=1)  # let the message expand vertically

        source_dir_label = ttk.Label(self, text="Location of resource:", width=27)
        source_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        self.source_dir_entry = ttk.Entry(self, width=43, textvariable=self.source_dir)
        self.source_dir_entry.grid(row=4, column=2, sticky=W)
        file_Tip = Hovertip(self.source_dir_entry, hover_delay=500,
             text="Folder where manifest.yaml and other files to be submitted reside")
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=4, sticky=W, padx=0)

        self.message_area = Text(self, height=10, width=30, wrap="none")
        self.message_area['borderwidth'] = 2
        self.message_area['relief'] = 'sunken'
        self.message_area['background'] = 'grey97'
        self.message_area.grid(row=88, column=1, columnspan=4, sticky='nsew', pady=6)
        ys = ttk.Scrollbar(self, orient = 'vertical', command = self.message_area.yview)
        ys.grid(row = 88, column = 5, sticky = 'ns')
        self.message_area['yscrollcommand'] = ys.set
        xs = ttk.Scrollbar(self, orient = 'horizontal', command = self.message_area.xview)
        xs.grid(row=89, column = 1, columnspan=4, sticky = 'ew')
        self.message_area['xscrollcommand'] = xs.set

        prev_button = ttk.Button(self, text="Previous step", command=self._onBack)
        prev_button.grid(row=99, column=1, sticky=(W,N,S))  #, pady=5)

        self.execute_button = ttk.Button(self, text="VERIFY",
                                          command=self._onExecute, padding=5)
        self.execute_button['padding'] = (5, 5) # internal padding!
        self.execute_button.grid(row=99, column=2, sticky=(W,N,S))  #, padx=10, pady=5)
        self.execute_button_Tip = Hovertip(self.execute_button, hover_delay=500,
                text="Verify readiness of manifest.yaml and the whole resource.")

        next_button = ttk.Button(self, text="Next Step")
        next_button.grid(row=99, column=4, sticky=(N,S,E))
        next_button['state']  = DISABLED
        next_button_Tip = Hovertip(next_button, hover_delay=500, text="Not implemented")

    def show_values(self, values):
        self.values = values
        self.source_dir.set(values['source_dir'])
        self._set_button_status()

    # Displays status messages from the running script.
    def show_progress(self, status):
        self.message_area.insert('end', status + '\n')
        self.message_area.see('end')
        self.execute_button['state'] = DISABLED

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.execute_button['state'] = NORMAL

    # Called by the controller when script execution begins.
    def clear_status(self):
        self.message_area['state'] = NORMAL   # enables insertions to message area
        self.message_area.delete('1.0', 'end')

    def _save_values(self):
        self.values['source_dir'] = self.source_dir.get()
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onExecute(self, *args):
        self._save_values()
        self.controller.onExecute(self.values)

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onChangeEntry(self, *args):
        self._set_button_status()

    def _onBack(self, *args):
        self._save_values()
        self.controller.onBack()

    def _set_button_status(self):
        good_source = os.path.isdir(self.source_dir.get())
        self.execute_button['state'] = NORMAL if good_source else DISABLED
