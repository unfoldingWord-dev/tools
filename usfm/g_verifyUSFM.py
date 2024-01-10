# -*- coding: utf-8 -*-
# GUI interface for USFM file verification
#

from tkinter import *
from tkinter import ttk
from tkinter import font
from idlelib.tooltip import Hovertip
import g_util
import os
import time

stepname = 'VerifyUSFM'   # equals the main class name in this module

class VerifyUSFM:
    def __init__(self, mainframe, mainapp):
        self.main_frame = mainframe
        self.mainapp = mainapp
        self.frame = VerifyUSFM_Frame(self.main_frame, self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def title(self):
        return "Step 2: Verify USFM"

    def show(self, values):
        self.values = values
        self.frame.show_values(values)
        self.frame.tkraise()

    def onBack(self):
        self.mainapp.activate_step('Txt2USFM')
    def onNext(self):
        copyparms = {'source_dir': self.values['source_dir']}
        self.mainapp.activate_step("UsfmCleanup", copyparms)

    def onExecute(self, values):
        self.values = values    # redundant, they were the same dict to begin with
        count = 1
        if not values['filename']:
            count = g_util.count_files(values['source_dir'], ".*sfm$")
        self.mainapp.execute_script("verifyUSFM", count)
        self.frame.clear_status()

    # Called by the main app.
    # Displays the specified string in the message area.
    def onScriptProgress(self, progress: str):
        self.frame.show_progress(progress)

    # Called by the main app.
    def onScriptEnd(self, status: str):
        self.frame.show_progress(status)
        self.frame.onScriptEnd()

class VerifyUSFM_Frame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.language_code = StringVar()
        self.source_dir = StringVar()
        self.filename = StringVar()
        self.std_titles = StringVar()
        for var in (self.language_code, self.source_dir, self.filename):
            var.trace_add("write", self._onChangeEntry)
        self.suppress = [BooleanVar(value = False) for i in range(12)]

        language_code_label = ttk.Label(self, text="Language code:", width=20)
        language_code_label.grid(row=3, column=1, sticky=(W,E,N), pady=2)
        language_code_entry = ttk.Entry(self, width=20, textvariable=self.language_code)
        language_code_entry.grid(row=3, column=2, sticky=W)
        source_dir_label = ttk.Label(self, text="Location of .usfm files:", width=20)
        source_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        source_dir_entry = ttk.Entry(self, width=40, textvariable=self.source_dir)
        source_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=5, column=1, sticky=W, pady=2)
        file_entry = ttk.Entry(self, width=20, textvariable=self.filename)
        file_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        file_Tip = Hovertip(file_entry, hover_delay=500,
             text="Leave filename blank to verify all .usfm files in the folder.")
        std_titles_label = ttk.Label(self, text="Standard chapter title:", width=20)
        std_titles_label.grid(row=6, column=1, sticky=W, pady=2)
        std_titles_entry = ttk.Entry(self, width=20, textvariable=self.std_titles)
        std_titles_entry.grid(row=6, column=2, columnspan=3, sticky=W)
        
        subheadingFont = font.Font(size=10, slant='italic')     # normal size is 9
        suppressions_label = ttk.Label(self, text="Suppress these warnings?", font=subheadingFont)
        suppressions_label.grid(row=10, column=1, columnspan=2, sticky=W, pady=(4,2))

        suppress1_checkbox = ttk.Checkbutton(self, text='Numbers', variable=self.suppress[1],
                                             onvalue=True, offvalue=False)
        suppress1_checkbox.grid(row=11, column=1, sticky=W)
        suppress1_Tip = Hovertip(suppress1_checkbox, hover_delay=500,
             text="Suppress all warnings about numbers. (possible verse number in verse, space in number, number prefix/suffix, etc.)")
        suppress2_checkbox = ttk.Checkbutton(self, text=r'No \p after \c', variable=self.suppress[2],
                                             onvalue=True, offvalue=False)
        suppress2_checkbox.grid(row=11, column=2, sticky=W)
        suppress2_Tip = Hovertip(suppress2_checkbox, hover_delay=500,
             text=r"Suppress warnings about missing paragraph marker before verse 1. (needed by PTX-Print)")
        suppress3_checkbox = ttk.Checkbutton(self, text=r'Punctuation', variable=self.suppress[3],
                                             onvalue=True, offvalue=False)
        suppress3_checkbox.grid(row=11, column=3, sticky=W)
        suppress3_Tip = Hovertip(suppress3_checkbox, hover_delay=500,
             text=r"Suppress warnings about punctuation")
        suppress4_checkbox = ttk.Checkbutton(self, text=r'Useless markers', variable=self.suppress[4],
                                             onvalue=True, offvalue=False)
        suppress4_checkbox.grid(row=11, column=4, sticky=W)
        suppress4_Tip = Hovertip(suppress4_checkbox, hover_delay=500,
             text=r"Suppress warnings about useless markers before section/title markers")
        suppress5_checkbox = ttk.Checkbutton(self, text=r'Verse counts', variable=self.suppress[5],
                                             onvalue=True, offvalue=False)
        suppress5_checkbox.grid(row=12, column=1, sticky=W)
        suppress5_Tip = Hovertip(suppress5_checkbox, hover_delay=500,
             text=r"Suppress checks for verse counts")
        suppress6_checkbox = ttk.Checkbutton(self, text=r'Straight quotes', variable=self.suppress[6],
                                             onvalue=True, offvalue=False)
        suppress6_checkbox.grid(row=12, column=2, sticky=W)
        suppress6_Tip = Hovertip(suppress6_checkbox, hover_delay=500,
             text=r"Suppress warnings about straight double and single quotes")

        suppress7_checkbox = ttk.Checkbutton(self, text=r'Straight single quotes', variable=self.suppress[7],
                                             onvalue=True, offvalue=False)
        suppress7_checkbox.grid(row=12, column=3, sticky=W)
        suppress7_Tip = Hovertip(suppress4_checkbox, hover_delay=500,
             text=r"Suppress warnings about straight single quotes  (report straight double quotes only)")
        
        suppress8_checkbox = ttk.Checkbutton(self, text=r'Book titles', variable=self.suppress[8],
                                             onvalue=True, offvalue=False)
        suppress8_checkbox.grid(row=12, column=4, sticky=W)
        suppress8_Tip = Hovertip(suppress8_checkbox, hover_delay=500,
             text=r"Suppress warnings about UPPER CASE BOOK TITLES")
        
        suppress9_checkbox = ttk.Checkbutton(self, text=r'ASCII content', variable=self.suppress[9],
                                             onvalue=True, offvalue=False)
        suppress9_checkbox.grid(row=13, column=1, sticky=W)
        suppress9_Tip = Hovertip(suppress9_checkbox, hover_delay=500,
             text=r"Suppress warnings about ASCII content")
        
        suppress10_checkbox = ttk.Checkbutton(self, text=r'Capitalization', variable=self.suppress[10],
                                             onvalue=True, offvalue=False)
        suppress10_checkbox.grid(row=13, column=2, sticky=W)
        suppress10_Tip = Hovertip(suppress10_checkbox, hover_delay=500,
             text=r'Suppress "First word not capitalized" warnings; report totals only')
        
        suppress11_checkbox = ttk.Checkbutton(self, text=r'Paragraph termination', variable=self.suppress[11],
                                             onvalue=True, offvalue=False)
        suppress11_checkbox.grid(row=13, column=3, sticky=W)
        suppress11_Tip = Hovertip(suppress11_checkbox, hover_delay=500,
             text=r'Suppress "Punctuation missing at end of paragraph" warnings; report totals only')

        self.message_area = Text(self, height=10, width=30, wrap="none")
        self.message_area['borderwidth'] = 2
        self.message_area['relief'] = 'sunken'
        self.message_area['background'] = 'grey97'
        self.message_area.grid(row=88, column=1, columnspan=4, sticky='nsew', pady=6)
        ys = ttk.Scrollbar(self, orient = 'vertical', command = self.message_area.yview)
        ys.grid(column = 5, row = 88, sticky = 'ns')
        self.message_area['yscrollcommand'] = ys.set

        prev_button = ttk.Button(self, text="Previous Step", command=self._onBack)
        prev_button.grid(row=99, column=1, sticky=(W,N,S))  #, pady=5)
        prev_button_Tip = Hovertip(prev_button, hover_delay=500, text="Text file conversion to USFM")

        self.execute_button = ttk.Button(self, text="VERIFY", command=self._onExecute)
        self.execute_button.grid(row=99, column=2, sticky=(W,N,S))  #, padx=0, pady=5)
        self.execute_button['padding'] = (5, 5) # internal padding!
        execute_button_Tip = Hovertip(self.execute_button, hover_delay=500, text="Check the USFM files now.")

        self.issues_button= ttk.Button(self, text="Open issues file", command=self._onOpenIssues)

        next_button = ttk.Button(self, text="Next Step", command=self._onNext)
        next_button.grid(row=99, column=4, sticky=(N,S,E))  #, padx=0, pady=5)
        next_button_Tip = Hovertip(next_button, hover_delay=500, text="Automated USFM file cleanup")

        # for child in parent.winfo_children():
            # child.grid_configure(padx=25, pady=5)
        
    def show_values(self, values):
        self.values = values
        self.language_code.set(values.get('language_code', fallback=""))
        self.source_dir.set(values.get('source_dir', fallback=""))
        self.filename.set(values.get('filename', fallback=""))
        self.std_titles.set(values.get('standard_chapter_title', fallback=""))
        for si in range(len(self.suppress)):
            configvalue = f"suppress{si}"
            self.suppress[si].set( values.get(configvalue, fallback = False))
        self._set_button_status()

    # Displays status messages from the running script.
    def show_progress(self, status):
        self.message_area.insert('end', status + '\n')
        self.message_area.see('end')
        self.execute_button['state'] = DISABLED
        self.issues_button['state'] = DISABLED

    def onScriptEnd(self):
        issuespath = os.path.join(self.values['source_dir'], "issues.txt")
        if os.path.isfile(issuespath):
            if time.time() - os.path.getmtime(issuespath) < 10:     # issues.txt is recent
                self.message_area.insert('end', "issues.txt contains the list of issues found.\n")
                self.message_area.insert('end', "Make corrections using your text editor, or go to\n  Next Step to do automated cleanup.\n")
                self.message_area.see('end')
                self.issues_button.grid(row=99, column=3, sticky=(W,N,S))
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.execute_button['state'] = NORMAL
        self.issues_button['state'] = NORMAL

    # Called by the controller when script execution begins.
    def clear_status(self):
        self.message_area['state'] = NORMAL   # enables insertions to message area
        self.message_area.delete('1.0', 'end')

    # Copies current values from GUI into self.values dict, and calls mainapp to save
    # them to the configuration file.
    def _save_values(self):
        self.values['language_code'] = self.language_code.get()
        self.values['source_dir'] = self.source_dir.get()
        self.values['filename'] = self.filename.get()
        self.values['standard_chapter_title'] = self.std_titles.get()
        for si in range(len(self.suppress)):
            configvalue = f"suppress{si}"
            self.values[configvalue] = str(self.suppress[si].get())
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onExecute(self, *args):
        self._save_values()
        self.execute_button['state'] = DISABLED
        self.controller.onExecute(self.values)
    def _onChangeEntry(self, *args):
        self._set_button_status()
    def _onBack(self, *args):
        self._save_values()
        self.controller.onBack()
    def _onNext(self, *args):
        self._save_values()
        self.controller.onNext()
    def _onOpenIssues(self, *args):
        self._save_values()
        path = os.path.join(self.values['source_dir'], "issues.txt")
        os.startfile(path)

    def _set_button_status(self):
        good_source = os.path.isdir(self.source_dir.get())
        if good_source and self.filename.get():
            path = os.path.join(self.source_dir.get(), self.filename.get())
            good_source = os.path.isfile(path)
        self.execute_button['state'] = NORMAL if self.language_code.get() and good_source else DISABLED
