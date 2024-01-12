# -*- coding: utf-8 -*-
# Implements Txt2USFM and Text2USFM_Frame, which are the controller and frame
# for operating the txt2USFM.py script.
# GUI interface for merging BTTW text files and converting to USFM

from tkinter import *
from tkinter import ttk
from tkinter import font
from idlelib.tooltip import Hovertip
import os
import g_util

stepname = 'Txt2USFM'   # equals the main class name in this module

class Txt2USFM:
    def __init__(self, mainframe, mainapp):
        self.main_frame = mainframe
        self.mainapp = mainapp
        self.frame = Text2USFM_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def show(self, values):
        self.values = values
        self.frame.show_values(values)
        self.frame.tkraise()

    def title(self):
        return "Step 1: Convert text files to USFM"

    def onExecute(self, values):
        self.values = values
        count = g_util.count_folders(values['source_dir'], f"{values['language_code']}_[\w][\w][\w].*_reg|_ulb$")
        self.mainapp.execute_script("txt2USFM", count)
        self.frame.clear_status()
    def onNext(self):
        copyparms = {'language_code': self.values['language_code'], 'source_dir': self.values['target_dir']}
        self.mainapp.activate_step("VerifyUSFM", copyparms)
    def onSkip(self):
        self.mainapp.activate_step("VerifyUSFM")

    # Called by the main app.
    # Displays the specified string in the message area.
    def onScriptMessage(self, progress):
        self.frame.show_progress(progress)

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if not status:
            status = f"The conversion is done.\nAdvance to USFM verification and cleanup."
        self.frame.show_progress(status)
        self.frame.onScriptEnd()
                
class Text2USFM_Frame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.language_code = StringVar()
        self.source_dir = StringVar()
        self.target_dir = StringVar()
        for var in (self.language_code, self.source_dir, self.target_dir):
            var.trace_add("write", self._onChangeEntry)
        for col in [2,3,4]:
            self.columnconfigure(col, weight=1)   # keep column 1 from expanding
        self.rowconfigure(88, minsize=170, weight=1)  # let the message expand vertically

        self.language_code_label = ttk.Label(self, text="Language code:", width=20)
        self.language_code_label.grid(row=3, column=1, sticky=(W,E,N), pady=2)
        self.language_code_entry = ttk.Entry(self, width=20, textvariable=self.language_code)
        self.language_code_entry.grid(row=3, column=2, sticky=W)
        self.source_dir_label = ttk.Label(self, text="Location of text files:", width=20)
        self.source_dir_label.grid(row=4, column=1, sticky=(W,E), pady=2)
        self.source_dir_entry = ttk.Entry(self, width=40, textvariable=self.source_dir)
        self.source_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        self.target_dir_label = ttk.Label(self, text="Location for .usfm files:", width=20)
        self.target_dir_label.grid(row=5, column=1, sticky=(W,E), pady=2)
        self.target_dir_entry = ttk.Entry(self, width=40, textvariable=self.target_dir)
        self.target_dir_entry.grid(row=5, column=2, columnspan=3, sticky=W)

        self.message_area = Text(self, height=10, width=30, wrap="none")
        self.message_area['borderwidth'] = 2
        self.message_area['relief'] = 'sunken'
        self.message_area['background'] = 'grey97'
        self.message_area.grid(row=88, column=1, columnspan=5, sticky='nsew', pady=6)
        ys = ttk.Scrollbar(self, orient = 'vertical', command = self.message_area.yview)
        ys.grid(column = 5, row = 88, sticky = 'ns')
        self.message_area['yscrollcommand'] = ys.set

        self.execute_button = ttk.Button(self, text="CONVERT",
                                          command=self._onExecute, padding=5)
        self.execute_button['padding'] = (5, 5) # internal padding!
        self.execute_button.grid(row=99, column=2, sticky=(W,N,S)) # padx=10, pady=5)
        self.execute_button_Tip = Hovertip(self.execute_button, hover_delay=500,
                text="Run the conversion script now.")

        self.opentarget_button= ttk.Button(self, text="Open usfm folder", command=self._onOpenTargetDir)
        self.opentarget_button.grid(row=99, column=3, sticky=(W,N,S))  # padx=10, pady=5

        self.next_button = ttk.Button(self, text="Skip this step", command=self._onSkip, padding=10)
        self.next_button.grid(row=99, column=4, sticky=(N,S,E)) # , padx=0, pady=5)

        # for child in parent.winfo_children():
        #     child.grid_configure(padx=25, pady=5)
        self.language_code_entry.focus()

    # Called when the frame is first activated. Populate the initial values.
    def show_values(self, values):
        self.values = values
        self.language_code.set(values['language_code'])
        self.source_dir.set(values['source_dir'])
        self.target_dir.set(values['target_dir'])
        self._set_button_status()

    # Displays status message from the running script.
    def show_progress(self, status):
        self.message_area.insert('end', status + '\n')
        self.message_area.see('end')
        self.execute_button['state'] = DISABLED

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.opentarget_button['state'] = NORMAL
        self.execute_button['state'] = NORMAL

    # Called by the controller when script execution begins.
    def clear_status(self):
        self.message_area['state'] = NORMAL   # enables insertions to message area
        self.message_area.delete('1.0', 'end')

    # Caches the current parameters in self.values and calls the mainapp to save them in the config file.
    def _save_values(self):
        self.values['language_code'] = self.language_code.get()
        self.values['source_dir'] = self.source_dir.get()
        self.values['target_dir'] = self.target_dir.get()
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onExecute(self, *args):
        self._save_values()
        self.controller.onExecute(self.values)
        self.next_button['text'] = "Next step"
        self.next_button['command'] = self._onNext
    def _onChangeEntry(self, *args):
        self._set_button_status()
    def _onOpenTargetDir(self, *args):
        self._save_values()
        os.startfile(self.values['target_dir'])
    def _onSkip(self, *args):
        self._save_values()
        self.controller.onSkip()
    def _onNext(self, *args):
        self._save_values()
        self.controller.onNext()
    def _set_button_status(self):
        good_sourcedir = os.path.isdir(self.source_dir.get())
        self.execute_button['state'] = NORMAL if self.language_code.get() and good_sourcedir and self.target_dir.get() else DISABLED
        self.opentarget_button['state'] = NORMAL if os.path.isdir(self.target_dir.get()) else DISABLED
