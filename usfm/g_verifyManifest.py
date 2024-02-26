# -*- coding: utf-8 -*-
# GUI interface for verifying manifest.yaml file and readiness of resource container.
#

from tkinter import *
from tkinter import ttk
from tkinter import font
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
        self.expectAscii = BooleanVar(value = False)
        for col in (2,3):
            self.columnconfigure(col, weight=1)   # keep column 1 from expanding
        self.columnconfigure(4, minsize=82)
        self.rowconfigure(88, minsize=170, weight=1)  # let the message expand vertically

        source_dir_label = ttk.Label(self, text="Location of resource: ")
        source_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        self.source_dir_entry = ttk.Entry(self, width=49, textvariable=self.source_dir)
        self.source_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        file_Tip = Hovertip(self.source_dir_entry, hover_delay=500,
             text="Folder where manifest.yaml and other files to be submitted reside")
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=4, sticky=W)

        expectAscii_checkbox = ttk.Checkbutton(self, text=r'Expect ASCII', variable=self.expectAscii,
                                             onvalue=True, offvalue=False)
        expectAscii_checkbox.grid(row=5, column=1, sticky=W)
        expectAscii_Tip = Hovertip(expectAscii_checkbox, hover_delay=500,
             text=r"Suppress warnings about ASCII book titles, etc")

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

    def show_values(self, values):
        self.values = values
        self.source_dir.set(values.get('source_dir', fallback = ""))
        self.expectAscii.set(values.get('expectascii', fallback = False))

        # Create buttons
        self.controller.showbutton(1, "<<<", tip="Previous step", cmd=self._onBack)
        self.controller.showbutton(2, "VERIFY", tip="Verify readiness of manifest.yaml and the whole resource.",
                                   cmd=self._onExecute)
        self.controller.showbutton(3, "Open manifest", tip="Opens manifest.yaml in your default editor",
                                   cmd=self._onOpenManifest)
        self.controller.showbutton(4, "Open folder", tip="Opens the resource folder", cmd=self._onOpenSourceDir)
        self.controller.showbutton(5, ">>>", tip="Not implemented")
        self.controller.enablebutton(5, False)
        self._set_button_status()

    # Displays status messages from the running script.
    def show_progress(self, status):
        self.message_area.insert('end', status + '\n')
        self.message_area.see('end')
        self.controller.enablebutton(2, False)

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.enablebutton(2, True)

    # Called by the controller when script execution begins.
    def clear_status(self):
        self.message_area['state'] = NORMAL   # enables insertions to message area
        self.message_area.delete('1.0', 'end')

    def _save_values(self):
        self.values['source_dir'] = self.source_dir.get()
        self.values['expectascii'] = str(self.expectAscii.get())
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onExecute(self, *args):
        self._save_values()
        self.controller.onExecute(self.values)

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onChangeEntry(self, *args):
        self._set_button_status()

    def _onOpenManifest(self, *args):
        self._save_values()
        path = os.path.join(self.values['source_dir'], "manifest.yaml")
        os.startfile(path)
    def _onOpenSourceDir(self, *args):
        self._save_values()
        os.startfile(self.values['source_dir'])

    def _onBack(self, *args):
        self._save_values()
        self.controller.onBack()

    def _set_button_status(self):
        self.controller.enablebutton(2, os.path.isdir(self.source_dir.get()))
