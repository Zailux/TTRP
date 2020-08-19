"""This is the Uvis View module.

This module does stuff.
"""

import logging
import os
import threading
import time
import tkinter as tk
import sys
from datetime import datetime
from functools import partial, wraps
from tkinter import ttk
from tkinter.font import Font

import matplotlib
matplotlib.use('Tkagg')
import matplotlib.animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cv2 import cv2
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from pandastable import Table
from PIL import Image, ImageTk

#sys.path.insert(1, '..\\')
from src.aurora import Handle
from src.config import Configuration
from src.helper import Helper, ScrollableFrame
from src.NavigationVisualizer import NavigationVisualizer
from src.uvis_model import Examination, Record


global hp
hp = Helper()
global _cfg
_cfg = Configuration()
logger = _cfg.LOGGER

global BUTTON_WIDTH
BUTTON_WIDTH = 25
BUTTON_FONT = {'family':'Open Sans', 'size':10}
DEFAULT_FONT_OPTIONS = {'family':'Open Sans'}
SUM_MAXHEIGHT = 4
SUM_TITLE_PADY = 5



#   --- Decorators  --- #

# application frames will clear the self.rightframe first before
# displaying their gui


def clear_frame(func):
    '''
    The decorator clears the master (tk.Frame Object) of its children
    when the build_frame method is called.
    The build_frame method must be called with the 'master' keyword.
        Example: myframe = self.build_frame(master=parent_frame).
    '''
    @wraps(func)
    def buildFrame_wrapper(*args, **kwargs):
        master = kwargs['master']
        if (not isinstance(master, tk.Frame)):
            logger.critical(
                f"Misusage of clear_frame Decorator. Objecttype {type(master)} is incorrect.\nDebuginfo {args, kwargs}")
            return func(*args, **kwargs)
        else:
            frame = master.winfo_children()
            if (len(frame) is not 0):
                frame[0].destroy()
        return func(*args, **kwargs)

    return buildFrame_wrapper

class UltraVisView(tk.Frame):

    def __init__(self, master, debug_mode=False):
        super().__init__(master)

        self.start_time = time.time()
        self._debug = debug_mode
        self.current_menu = None
        default_font = tk.font.nametofont("TkDefaultFont")
        default_font.configure(**DEFAULT_FONT_OPTIONS)
        super().option_add("*Font", default_font)

        self.master = master
        self.master.title("TTR: Track To Reference")
        self.master.minsize(600, 350)
        self.master.geometry(self._center_window(self.master, 1000, 600))
        # self.master.wm_state('zoomed')
        self.master.focus_force()

        self.tab_control = ttk.Notebook(self.master)
        # self.initImages()
        self._build_tab1()
        self._build_tab2()

        self.tab_control.add(self.t1_main_frame, text='Navigation')
        self.tab_control.add(self.t2_debugFrame, text='Debugging')

        self.tab_control.pack(fill=tk.BOTH, expand=tk.TRUE)

        # Selecting Tabs
        # self.tab_control.select(self.t2_debugFrame)

    def _center_window(self, toplevel, width, height):
        '''Returns the centered Position for the tk.Frame.geometry() function.'''
        toplevel.update_idletasks()
        w = toplevel.winfo_screenwidth()
        h = toplevel.winfo_screenheight()
        size = (width, height)
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        return ("%dx%d+%d+%d" % (size + (x, y)))

    def _build_tab1(self):
        # Tab 1 Two Column, Menu Column and App Column
        self.t1_main_frame = tk.Frame(self.tab_control)
        self.t1_main_frame.rowconfigure(0, weight=98)
        self.t1_main_frame.columnconfigure(0, weight=20, uniform=1)
        self.t1_main_frame.columnconfigure(1, weight=80, uniform=1)
        self.left_frame = tk.Frame(self.t1_main_frame, bg="#196666")
        self.left_frame.rowconfigure(0, weight=60, uniform=1)
        self.left_frame.rowconfigure(1, weight=40, uniform=1)
        self.left_frame.columnconfigure(0, weight=1)
        self.right_frame = tk.Frame(self.t1_main_frame, bg="#196666")
        self.right_frame.rowconfigure(0, weight=1, uniform=1)
        self.right_frame.columnconfigure(0, weight=1)

        self.left_frame.grid(row=0, column=0, pady=4, padx=4, sticky=tk.NSEW)
        self.right_frame.grid(row=0, column=1, pady=4, padx=4, sticky=tk.NSEW)

        self.build_menu_frame(self.left_frame)
        self.build_details_frame(self.left_frame)
        self.build_mainscreen_frame(master=self.right_frame)
        self.show_menu()

        self.t1_main_frame.pack(fill=tk.BOTH, expand=tk.TRUE)

    def build_menu_frame(self, lFrame):
        '''Build the menu frame and adds the buttons to the application'''
        self.menu_frame = tk.Frame(lFrame)
        self.menu_title_lb = tk.Label(self.menu_frame, text="Menu",
                                    font=Font(family='Open Sans', size=12))

        # Main Menu
        self.new_exam_but = tk.Button(self.menu_frame)
        self.new_exam_but["text"] = "Neue Untersuchung"
        self.open_exam_but = tk.Button(self.menu_frame)
        self.open_exam_but["text"] = "Untersuchung \u00F6ffnen"
        self.open_exam_but["state"] = 'disabled' if not self._debug else 'normal'
        self.open_eval_but = tk.Button(self.menu_frame)
        self.open_eval_but["text"] = "Datensatz auswerten"

        # Setup Menu
        self.start_exam_but = tk.Button(self.menu_frame)
        self.start_exam_but["text"] = "Untersuchung beginnen"
        self.activate_handle_but = tk.Button(self.menu_frame)
        self.activate_handle_but["text"] = "Try Activate Handles"

        # Tracking / Recording Menu
        self.track_but = tk.Button(self.menu_frame)
        self.track_but["text"] = "Start/Stop Tracking"
        self.save_record_but = tk.Button(self.menu_frame)
        self.save_record_but["text"] = "Aufzeichnung speichern"
        self.finish_exam_but = tk.Button(self.menu_frame)
        self.finish_exam_but["text"] = "Untersuchung abschließen"

        #Navigation Menu
        self.calibrate_but = tk.Button(self.menu_frame)
        self.calibrate_but["text"] = "Koordinatensystem kalibrieren"
        self.target_menu_frame = tk.Frame(self.menu_frame)
        self.target_but = tk.Button(self.target_menu_frame)
        self.target_but["text"] = "Lade Zielpunkt"
        self.target_var = tk.StringVar()
        self.target_var.set('')
        self.target_option_menu = tk.OptionMenu(self.target_menu_frame, self.target_var, ' ')

        self.nav_save_record_but = tk.Button(self.menu_frame)
        self.nav_save_record_but["text"] = "Aufnehmen"
        self.switch_imgsrc_but = tk.Button(self.menu_frame)
        self.switch_imgsrc_but["text"] = "Video-zu-Aufnahme wechseln"
        self.switch_imgsrc_but["state"] = 'disabled'
        self.accept_record_but = tk.Button(self.menu_frame)
        self.accept_record_but["text"] = "Aufzeichnung akzeptieren"
        self.accept_record_but["state"] = 'disabled'

        #Start Navigation
        self.start_navigation_but = tk.Button(self.menu_frame)
        self.start_navigation_but["text"] = "Start Navigation"

        # Finish Examination Menu
        self.save_edit_but = tk.Button(self.menu_frame)
        self.save_edit_but["text"] = "Editieren"

        # Misc Buttons
        self.continue_but = tk.Button(self.menu_frame)
        self.continue_but["text"] = "Fortfahren"
        self.cancel_but = tk.Button(self.menu_frame)
        self.cancel_but["text"] = "Abbrechen"
        self.back_but = tk.Button(self.menu_frame)
        self.back_but["text"] = "Zur\u00FCck"
        self.mainmenu_but = tk.Button(self.menu_frame)
        self.mainmenu_but["text"] = "Zum Hauptmenu"
        self.reinit_aua_but = tk.Button(self.menu_frame)
        self.reinit_aua_but["text"] = "Reinitialize Aurora"
        self.NOBUTTONSYET = tk.Button(self.menu_frame, text="Secret Blowup Button")

        for widget in self.menu_frame.winfo_children():
            if widget.winfo_class() == 'Button':
                widget["font"] = Font(**BUTTON_FONT)

        self.menu_title_lb.pack(side=tk.TOP, pady=(10, 2), fill="both")
        self.menu_frame.grid(row=0, column=0, padx=2, pady=2, sticky=tk.NSEW)

    def clean_menu(self, childList):
        '''Recursively removes the Buttons from the menu_frame'''
        for child in childList:
            if (child.winfo_class() == 'Frame'):
                self.clean_menu(child.winfo_children())
                child.forget()
                continue
            if (child.winfo_class() in ['Button', 'Menubutton'] and child.winfo_ismapped()):
                child.pack_forget()

    def show_menu(self, menu='main', states=None):
        '''Displays the corresponding menu, for an application frame.
        The menu chosen via the menu parameter will be displayed. With the
        'states' parameter the states of the buttons in the menu
        can be influences via a 0,1 sequence [0,1,1,...].
            STATES IS NOT IMPLEMENTED YET!
        '''
        # Idea to use a state "table of 0 and 1 to enable / disable Button"

        # potentially add activatehandles button
        menu_buttons = {
            'main': [self.new_exam_but, self.open_exam_but, self.open_eval_but],
            'new_examination': [self.continue_but, self.cancel_but],
            'setup': [self.start_exam_but, self.cancel_but],
            'examination': [self.track_but, self.save_record_but, self.finish_exam_but, self.cancel_but],
            'summary': [self.mainmenu_but, self.cancel_but], #self.save_edit_but,
            'open_examination': [self.start_navigation_but, self.cancel_but],
            'navigation': [self.track_but, self.calibrate_but, self.target_menu_frame, self.nav_save_record_but,
                           self.switch_imgsrc_but, self.accept_record_but, self.finish_exam_but, self.cancel_but],
            'open_evaluation': [self.cancel_but],
            'evaluate_examination': [self.NOBUTTONSYET, self.cancel_but]
        }

        if menu not in menu_buttons.keys():
            raise ValueError(
                f'Try showing Menu "{menu}" which was not in {list(menu_buttons.keys())}')

        children = self.menu_frame.winfo_children()
        self.clean_menu(children)

        for item in menu_buttons[menu]:
            item.pack(side=tk.TOP, pady=(0, 0), padx=(10), fill="both")
            if item.winfo_class() == 'Frame':
                children = item.winfo_children()
                for child in children:
                    child.pack(side=tk.LEFT, fill="both")
        self.current_menu = menu
        if (self._debug):
            self.NOBUTTONSYET.pack(side=tk.BOTTOM, pady=(0, 0),
                                   padx=(10), fill="both")

    def set_target_menu(self, records_list):
        ''' Sets the target_menu for the navigation menu. Param records_list should hold R_ID which shall be loaded'''
        self.target_var.set(records_list[0])
        self.target_option_menu['menu'].delete(0, 'end')
        for value in records_list:
            self.target_option_menu['menu'].add_command(label=value, command=tk._setit(self.target_var, value))


    def build_details_frame(self, lFrame):
        '''Builds the scrollable details_frame (ScrollableFrame object).'''
        scroll_framing = ScrollableFrame(lFrame)
        self.details_frame = scroll_framing.contentframe
        scroll_framing.grid_propagate(0)

        self.details_title_lb = tk.Label(self.details_frame, text="Details")
        self.details_info_lb = tk.Label(self.details_frame, text=" - ")
        self.workitem_data_lb = tk.Label(self.details_frame, text=" - ")

        self.details_title_lb.pack(side=tk.TOP, pady=(10, 2), fill="both")
        self.details_info_lb.pack(side=tk.TOP, pady=(2, 2), fill="both")
        self.workitem_data_lb.pack(side=tk.TOP, pady=(2, 2), fill="both")
        scroll_framing.grid(row=1, column=0, padx=2, pady=2, sticky=tk.NSEW)

    # cleaning setInfomsg?? when and how
    def set_info_message(self, msg, type='INFO'):
        OPTIONS = ['INFO', 'SUCCESS', 'ERROR']
        msg = str(msg)
        self.details_info_lb["text"] = msg

    @clear_frame
    def build_mainscreen_frame(self, master):
        '''Builds the mainscreen of the app.'''
        self.mainscreen_frame = tk.Frame(master)
        self.mainscreen_frame.rowconfigure(0, weight=1, uniform=1)
        self.mainscreen_frame.columnconfigure(0, weight=1, uniform=1)
        self.logo_lb = tk.Label(
            self.mainscreen_frame,
            text="Track to Reference Navigation\nMainscreen",
            font=('Open Sans', 26))
        self.logo_lb.grid(row=0, column=0, sticky=tk.NSEW)
        self.mainscreen_frame.grid(row=0, column=0, sticky=tk.NSEW)

    @clear_frame
    def build_newExam_frame(self, master):
        self.newExam_frame = tk.Frame(master, bg="grey", padx=20, pady=10)
        self.newExam_frame.rowconfigure(0, weight=10, uniform=1)
        self.newExam_frame.rowconfigure(1, weight=90, uniform=1)
        self.newExam_frame.columnconfigure(0, weight=1, uniform=1)
        self.newExam_frame.columnconfigure(1, weight=1, uniform=1)

        title_lb = tk.Label(self.newExam_frame, text="Untersuchungsdaten")
        title_lb.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)

        data_frame = tk.Frame(self.newExam_frame, padx=20)
        data_frame.columnconfigure(0, weight=35, minsize=180, uniform=1)
        data_frame.columnconfigure(1, weight=65, uniform=1)

        # Reihenfolge der deklaration der Widgets bestimmt Darstellungsposition
        self.doctor_lb = tk.Label(data_frame, text="Untersuchender Arzt")
        self.doctor_entry = tk.Entry(data_frame, bd=5)
        self.doctor_entry.insert(0, "Dr. med. vet. Baader")
        self.patient_lb = tk.Label(data_frame, text="Patient")
        self.patient_entry = tk.Entry(data_frame, bd=5)
        self.patient_entry.insert(0, "Herr Bach")
        self.exam_item_lb = tk.Label(data_frame, text="Untersuchungsgegenstand")
        self.exam_item_textbox = tk.Text(data_frame, bd=5)
        self.exam_item_textbox.insert(
            '1.0', "US Untersuchung am linken Lungenfl\u00FCgel\nGutartiger Tumor")
        self.created_lb = tk.Label(data_frame, text="Erstellt am")
        self.created_entry = tk.Entry(data_frame, bd=5)
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%a, %d-%b-%Y (%H:%M:%S)")
        self.created_entry.insert(0, timestampStr)
        self.created_entry["state"] = 'readonly'

        # Alle 2 Einträge wird eine neue Reihe angefangen
        children = data_frame.winfo_children()
        row_i = 0
        for i, widget in enumerate(children):
            col_i = i % 2
            data_frame.rowconfigure(row_i, weight=1, uniform=1)
            widget.grid(row=row_i, column=col_i, sticky=tk.EW)
            row_i = row_i + (i % 2)
        data_frame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)
        self.newExam_frame.grid(row=0, column=0, sticky=tk.NSEW)

    @clear_frame
    def build_setup_frame(self, master):

        # 2x2 Matrix of Application frame
        self.setup_frame = tk.Frame(master, bg="grey", padx=10, pady=10)
        self.setup_frame.rowconfigure(0, weight=20, uniform=1)
        self.setup_frame.rowconfigure(1, weight=5, uniform=1, minsize=15)
        self.setup_frame.rowconfigure(2, weight=10, uniform=1)
        self.setup_frame.rowconfigure(3, weight=65, uniform=1)
        self.setup_frame.columnconfigure(0, weight=1, uniform=1)
        self.setup_frame.columnconfigure(1, weight=1, uniform=1)
        self.setup_frame.columnconfigure(2, weight=1, uniform=1)
        self.setup_frame.columnconfigure(3, weight=1, uniform=1)

        self.setup_title_lb = tk.Label(
            self.setup_frame, text="Einrichtung des Aurorasystems")
        self.setup_title_lb.grid(
            row=0, column=0, columnspan=4, pady=(
                10, 8), sticky=tk.NSEW)

        instruc_title = tk.Label(
            self.setup_frame,
            text=" - Instruction - ",
            font='Helvetica 14 italic')
        instruc_title.grid(
            row=1, column=0, columnspan=4, pady=(
                10, 0), sticky=tk.NSEW)
        self.instruction_lb = tk.Label(
            self.setup_frame,
            text="Some Instruction",
            font='Helvetica 11 italic')
        self.instruction_lb.grid(
            row=2, column=0, columnspan=4, pady=(
                0, 10), sticky=tk.NSEW)

        self.setuphandle_frames = []
        self._current_setuphandle = None
        REFERENCEPOINT_SUGGESTIONS = [
            'Ultraschallkopf',
            'Rechter H\u00FCftknochen',
            'Linker H\u00FCftknochen',
            'Brustbein']
        for i in range(4):
            handle_Frame = tk.Frame(
                self.setup_frame, bg="white", padx=10, pady=10)
            lb = tk.Label(handle_Frame, text="Spulenname")
            lb2 = tk.Label(handle_Frame, text="Referenzname")
            ref_entry = tk.Entry(handle_Frame, bd=5)
            ref_entry.insert(0, REFERENCEPOINT_SUGGESTIONS[i])
            but = tk.Button(handle_Frame)
            but["text"] = "Done"
            valid = False

            children = handle_Frame.winfo_children()
            hp.disable_widgets(childList=children, disable_all=True)

            dic = {
                'frame': handle_Frame,
                'handlename': lb,
                'ref_entry': ref_entry,
                'button': but,
                'valid': valid}
            self.setuphandle_frames.append(dic)

            hp.pack_children(
                children,
                side=tk.TOP,
                fill=tk.BOTH,
                padx=5,
                pady=5)

            handle_Frame.grid(row=3, column=i, sticky=tk.NSEW, padx=2, pady=2)

        handle_index = 0
        self.set_current_setuphandle(handle_index)
        self.setup_frame.grid(row=0, column=0, padx=2, pady=2, sticky=tk.NSEW)

    def set_current_setuphandle(self, handle_index):
        lastindex = len(self.setuphandle_frames) - 1
        if (self._current_setuphandle is None):
            self._current_setuphandle = self.setuphandle_frames[handle_index]
        elif (handle_index <= lastindex):
            widgets = self._current_setuphandle["frame"].winfo_children()
            hp.disable_widgets(widgets, disable_all=True)
            self._current_setuphandle["frame"]["bg"] = "white"

        COLORS = ['GELBE', 'ROTE', 'GR\u00DCNE', 'BLAUE']
        HANDLENAME = None
        REFERENCEPOINT = [
            'Ultraschallkopf',
            'bspw. rechten H\u00FCftknochen',
            'bspw. linken H\u00FCftknochen',
            'bspw. Brustbein']
        INSTRUCTION = f'Bitte befestigen sie die {COLORS[handle_index]} Spule an den Punkt {REFERENCEPOINT[handle_index]}'
        COLORS = ['yellow', 'red', 'green', 'blue']

        self.set_setup_instruction(text=INSTRUCTION)
        handle_data = self.setuphandle_frames[handle_index]
        handle_data["frame"]["bg"] = COLORS[handle_index]
        children = handle_data["frame"].winfo_children()
        hp.enable_widgets(children, enable_all=True)
        self._current_setuphandle = self.setuphandle_frames[handle_index]

    def set_setup_instruction(self, text):
        text = str(text)
        self.instruction_lb["text"] = text

    @clear_frame
    def build_examination_frame(self, master):

        # Init of AppFrame Attributes
        self.navcanvas_data = ()
        self.img_size = None
        self.saved_img = None

        self.exam_frame = tk.Frame(master, bg="black")
        self.exam_frame.rowconfigure(0, weight=1)
        #self.exam_frame.rowconfigure(0, weight=90, uniform=1)
        #self.exam_frame.rowconfigure(1, weight=10, minsize=125, uniform=1)
        self.exam_frame.columnconfigure(0, weight=1)

        # 2x2 Matrix of Application frame
        self.grid_frame = tk.Frame(self.exam_frame)
        self.grid_frame.rowconfigure(0, weight=1, uniform=1)
        self.grid_frame.rowconfigure(1, weight=1, uniform=1)
        self.grid_frame.columnconfigure(0, weight=1, uniform=1)
        self.grid_frame.columnconfigure(1, weight=1, uniform=1)
        self.grid_frame.bind('<Configure>', lambda ref_lamb: self.refresh_imgsize(frame=self.grid_frame))

        # Order of the US Frame, Saved Image and Navigationframe
        self.USimg_frame = tk.Frame(self.grid_frame)
        self.USimg_frame.rowconfigure(0, weight=1)
        self.USimg_frame.columnconfigure(0, weight=1)
        self.saved_img_frame = tk.Frame(self.grid_frame)
        self.saved_img_frame.rowconfigure(0, weight=1)
        self.saved_img_frame.columnconfigure(0, weight=1)
        self.saved_img_frame.bind('<Configure>', self.refresh_saved_img)
        self.exam_data_frame = tk.Frame(self.grid_frame)
        self.exam_data_frame.rowconfigure(0, weight=0)
        self.exam_data_frame.rowconfigure(1, weight=1)
        self.exam_data_frame.columnconfigure(0, weight=1)

        self.USimg_frame.grid(row=0, column=0, padx=5, pady=2, sticky=tk.NSEW)
        self.saved_img_frame.grid(row=0, column=1, padx=5, pady=2, sticky=tk.NSEW)
        self.exam_data_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky=tk.NSEW)

        # Ultrasoundimage Content
        self.USimg_lb = tk.Label(self.USimg_frame) #LABEL for controller frame_grabber
        self.USimg_lb["text"] = "INITIALIZING VIDEOINPUT"
        self.USimg_lb.grid(row=0, column=0, sticky=tk.NSEW)
        self.USimg_lb.grid_propagate(0)

        # Saved Image Content
        self.saved_img_lb = tk.Label(self.saved_img_frame)
        self.saved_img_lb["text"] = "Saved Image"
        self.saved_img_lb.grid(row=0, column=0, sticky=tk.NSEW)

        # Examinationdata Frame Content
        self.sysmode_lb = tk.Label(self.exam_data_frame)
        self.sysmode_lb["text"] = "Operating Mode: - "
        self.sysmode_lb["font"] = ('Open Sans', 10)
        self.sysmode_lb.grid(row=0, column=0, pady=10, sticky=tk.NSEW)
        #self.sysmode_icon_lb = tk.Label(self.exam_data_frame)
        scroll_framing = ScrollableFrame(master=self.exam_data_frame)
        scroll_framing.contentframe.columnconfigure(0, weight=1)
        scroll_framing.contentframe.rowconfigure(0, weight=1)
        empty_pos = [Handle('',''), Handle('',''), Handle('',''), Handle('','')]
        self.tracking_data_frame = self.build_position_summary(master=scroll_framing.contentframe, position=empty_pos)
        self.tracking_data_frame.grid(row=0,column=0, pady=10, padx=10, sticky=tk.NSEW)
        scroll_framing.grid(row=1, column=0, sticky=tk.NSEW)

        self.grid_frame.grid(row=0, pady=8, padx=8, sticky=tk.NSEW)

        # Gallery Frame Content #TODO?
        self.gallery_frame = tk.Frame(self.exam_frame, bg="#99ffcc")
        self.gallery_lb = tk.Label(self.gallery_frame, text="a gallery")
        self.gallery_lb.pack()
        #self.gallery_frame.grid(row=1, column=0, pady=(0, 8), padx=8, sticky=tk.NSEW)
        self.exam_frame.grid(row=0, column=0, padx=2, pady=2, sticky=tk.NSEW)

    def refresh_imgsize(self, frame, event=None):
        frame.after_idle(self.calculate_US_imgsize)
        #self.grid_frame.after_idle(self.calculate_US_imgsize)

    def calculate_US_imgsize(self):
        # Get current Frame
        #cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        #img = Image.fromarray(cv2image)
        if (not hasattr(self.USimg_lb, 'imgtk')):
            self.USimg_lb.after(1500, self.calculate_US_imgsize)
            return

        img = self.USimg_lb.imgtk
        width, height = img.width(), img.height()

        # Normalize Ratio of Pictures, Resize appropriatly - could be
        # optimized.
        img_ratio = height / width
        frame_ratio = self.USimg_frame.winfo_height() / self.USimg_frame.winfo_width()
        if (frame_ratio >= img_ratio):
            new_width = (self.USimg_frame.winfo_width() - 5)
            new_height = height / width * new_width
        else:
            new_height = (self.USimg_frame.winfo_height() - 5)
            new_width = width / height * new_height

        self.img_size = ((int(new_width), int(new_height)))
        self.refresh_saved_img()

    def refresh_saved_img(self, event=None):
        # Refresh Saved IMG more Image possible
        if (self.saved_img is not None):
            self.saved_img = self.saved_img.resize(
                self.img_size, Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=self.saved_img)
            self.saved_img_lb.imgtk = imgtk
            self.saved_img_lb.configure(image=self.saved_img_lb.imgtk)

    def refresh_img_for_lb(self, event=None, img=None, lb=None):
        if not self.img_size:
            logger.debug("img_size still empty")
            lb.after(1000, self.refresh_img_for_lb, None, img, lb)
            return
        img = img.resize(self.img_size, Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(image=img)
        lb.imgtk = imgtk
        lb.configure(image=imgtk)

    def build_coordinatesystem(self):

        if (not hasattr(self,'navigationvis')):
            return

        if (len(self.navcanvas_data) is not 0):
            x,y,z,a,b,c,color = self.navcanvas_data
            self.navigationvis.set_pos(x[0], y[0])
            self.navigationvis.set_ori(a[0],b[0],c[0])
            self.navigationvis.update_All()

            self._Canvasjob = self.nav_canvas._tkcanvas.after(25,func=self.build_coordinatesystem)

        #self.nav_canvas.draw()

    '''
    def saveUSImg(self):
        cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        self.saved_img = Image.fromarray(cv2image)
        self.refresh_saved_img()
    '''

    @clear_frame
    def build_summary_frame(self, master):
        self.summaryFrame = tk.Frame(master)
        self.summaryFrame.rowconfigure(0, weight=5, uniform=1)
        self.summaryFrame.rowconfigure(1, weight=95, uniform=1)
        self.summaryFrame.columnconfigure(0, weight=1, uniform=1)
        title_lb = tk.Label(self.summaryFrame, text="Summary")
        scroll_framing = ScrollableFrame(master=self.summaryFrame)
        self.summary_content_frame = scroll_framing.contentframe

        title_lb.grid(row=0, column=0, sticky=tk.NSEW)
        scroll_framing.grid(row=1, column=0, sticky=tk.NSEW)
        self.summaryFrame.grid(row=0, column=0, sticky=tk.NSEW)

    def build_exam_summary(self, master, exam):
        ''' Builds an Exam Summary Frame
        The Frame displays the Exam Object in 3 Column pairs.
            Returns the appropriate tk.Frame Object.
        '''
        if (not isinstance(exam, Examination)):
            raise TypeError(f'Expected {Examination} for parameter record \
                              and got {type(exam)} instead.')
        exam_summary = tk.Frame(master)
        exam_summary.columnconfigure(0, weight=1,uniform=1)
        exam_summary.columnconfigure(1, weight=2,uniform=1)
        exam_summary.columnconfigure(2, weight=1,uniform=1)
        exam_summary.columnconfigure(3, weight=2,uniform=1)
        exam_summary.columnconfigure(4, weight=1,uniform=1)
        exam_summary.columnconfigure(5, weight=2,uniform=1)
        exam_summary.rowconfigure(0,weight=1)

        exam_title = tk.Label(exam_summary,text=f'Examination - {exam.E_ID}')
        exam_title.grid(row=0, column=0, columnspan=6, pady=SUM_TITLE_PADY)

        row_i = 1
        column_i = 0

        #Display Examination Value
        for item_index, pair in enumerate(exam.__dict__.items()):
            key,value = pair
            if item_index % 3  == 0:
                row_i += 1
                column_i = 0
                exam_summary.rowconfigure(row_i, weight=1)

            lb_key = tk.Label(exam_summary,text=str(key),bd=1)
            ref_value = hp.get_readonly_widget(master=exam_summary, value=value, max_length=28, max_height=SUM_MAXHEIGHT)

            lb_key.grid(row=row_i, column=column_i, sticky=tk.EW)
            ref_value.grid(row=row_i, column=column_i+1, sticky=tk.EW)
            column_i += 2

        return exam_summary

    def build_record_summary(self, master, record):
        ''' Builds an Record Summary Frame
        The Frame displays the Record Object in 3 Column pairs.
        The Record image!!!!! Display.
            Returns a tk.Frame Object.
        '''
        if (not isinstance(record, Record)):
            raise TypeError(f'Expected {Record} for parameter record \
                              and got {type(record)} instead.')
        record_summary = tk.Frame(master)
        record_summary.columnconfigure(0, weight=1,uniform=1)
        record_summary.columnconfigure(1, weight=2,uniform=1)
        record_summary.columnconfigure(2, weight=1,uniform=1)
        record_summary.columnconfigure(3, weight=2,uniform=1)
        record_summary.columnconfigure(4, weight=1,uniform=1)
        record_summary.columnconfigure(5, weight=2,uniform=1)
        record_summary.rowconfigure(0, weight=1)

        r = record.__dict__
        rec_title = tk.Label(record_summary,text=f'Record - {record.R_ID}')
        rec_title.grid(row=0,column=0,columnspan=6, pady=SUM_TITLE_PADY)

        row_i = 1
        column_i = 0
        for item_index,pair in enumerate(r.items()):
            key,value = pair
            if item_index % 3  == 0:
                row_i += 1
                column_i = 0
                record_summary.rowconfigure(row_i, weight=1, uniform=1)

            lb_key = tk.Label(record_summary, text=str(key), bd=1)
            ref_value = hp.get_readonly_widget(master=record_summary, value=value, max_length=28, max_height=SUM_MAXHEIGHT)

            lb_key.grid(row=row_i,column=column_i,sticky=tk.EW)
            ref_value.grid(row=row_i,column=column_i+1,sticky=tk.EW)
            column_i += 2

        #image
        image_lb = tk.Label(record_summary)


        return record_summary

    def build_position_summary(self, master, position):
        ''' Builds an Position Summary Frame
        The Frame displays the 4 Handles / the Position in an table format.
        Returns a tk.Frame Object.
        '''

        if (isinstance(position, dict)):
            as_list = []
            for handle in position.values():
                as_list.append(handle)
            position.clear()
            position = as_list

        if (not (all(isinstance(h, Handle) for h in position))):
            raise TypeError(f'Expected {Handle} for parameter position \
                              and got {type(h) for h in position} instead.')

        self.position_summary_widgets = []

        position_summary = tk.Frame(master)
        position_summary.rowconfigure(0, weight=0, minsize=20)

        col_len = len(position[0].__dict__)
        pos_title = tk.Label(position_summary,text=f'Corresponding Position')
        pos_title.grid(row=0,column=0,columnspan=col_len, pady=SUM_TITLE_PADY)

        position_summary.rowconfigure(1, weight=0, minsize=10)
        for i,key in enumerate(position[0].__dict__.keys()):
                key = str(key)
                title_lb = tk.Label(position_summary,text=key,bd=2,
                                    font=(Font(family='Open Sans', size=9 ,weight='bold')))
                position_summary.columnconfigure(i, weight=1,uniform=1)
                title_lb.grid(row=1,column=i,sticky=tk.EW)

        for j, handle in enumerate(position,start=2):
            #TODO changed to 0
            position_summary.rowconfigure(j,weight=1,uniform=1)
            widgets = []
            for k, val in enumerate(handle.__dict__.values()):
                val = str(val)
                handle_val = hp.get_readonly_widget(master=position_summary,value=val,max_length=15, max_height=SUM_MAXHEIGHT)
                handle_val.grid(row=j,column=k,sticky=tk.EW)
                widgets.append(handle_val)

            self.position_summary_widgets.append(widgets)

        return position_summary

    @clear_frame
    def build_openexam_frame(self,master):
        self.openExamFrame = tk.Frame(master)
        self.openExamFrame.rowconfigure(0, weight=1, uniform=1)
        self.openExamFrame.columnconfigure(0,weight=1,uniform=1)
        lb = tk.Label(self.openExamFrame,text="Geben Sie die E_ID zum oeffnen ein")
        self.examID_entry = tk.Entry(self.openExamFrame,bd=5)

        self.lastE_IDs = tk.Label(self.openExamFrame,text="Zuletzt hinzugefuegte IDs")

        lb.pack(side=tk.TOP, pady=(20, 5),padx=(10))
        self.examID_entry.pack(side=tk.TOP, pady=(10),padx=(10))
        self.lastE_IDs.pack(side=tk.TOP, pady=(10),padx=(10))
        self.openExamFrame.grid(row=0, column=0,sticky=tk.NSEW)


    # TODO bad reusage of a frames (navigation & Examination). No good solution yet.
    @clear_frame
    def build_navigation_frame(self, master):
        self.navcanvas_data = ()
        self.img_size = None
        self.saved_img = None

        scroll = ScrollableFrame(master=master, bg="red")
        self.navigation_frame = scroll.contentframe
        self.navigation_frame.rowconfigure(0, weight=1)
        self.navigation_frame.rowconfigure(1, weight=0)
        self.navigation_frame.rowconfigure(2, weight=1)
        self.navigation_frame.columnconfigure(0, weight=1)

        # 2x2 Matrix of Navgrid frame
        self.navgrid_frame = tk.Frame(self.navigation_frame)
        self.navgrid_frame.rowconfigure(0, weight=1, uniform=1)
        self.navgrid_frame.rowconfigure(1, weight=1, uniform=1)
        self.navgrid_frame.columnconfigure(0, weight=1, uniform=1)
        self.navgrid_frame.columnconfigure(1, weight=1, uniform=1)
        self.navgrid_frame.bind('<Configure>', lambda ref_lamb: self.refresh_imgsize(frame=self.navgrid_frame))
        # Order of the US Frame, Saved Image and Navigationframe
        self.USimg_frame = tk.Frame(self.navgrid_frame)
        self.USimg_frame.rowconfigure(0, weight=1)
        self.USimg_frame.columnconfigure(0, weight=1)
        self.saved_img_frame = tk.Frame(self.navgrid_frame)
        self.saved_img_frame.rowconfigure(0, weight=1)
        self.saved_img_frame.columnconfigure(0, weight=1)
        self.saved_img_frame.bind('<Configure>', self.refresh_saved_img)
        self.target_img_frame = tk.Frame(self.navgrid_frame)
        self.target_img_frame.rowconfigure(0, weight=1)
        self.target_img_frame.columnconfigure(0, weight=1)


        # Ultrasoundimage Content / Current Image
        self.USimg_lb = tk.Label(self.USimg_frame) #LABEL for controller frame_grabber
        self.USimg_lb["text"] = "INITIALIZING INPUT IMAGE"
        self.USimg_lb.grid(row=0, column=0, sticky=tk.NSEW)
        self.USimg_lb.grid_propagate(0)
        # TBD not suare yet
        self.saved_img_lb = tk.Label(self.saved_img_frame)
        self.saved_img_lb["text"] = "Recorded Image"
        self.saved_img_lb.grid(row=0, column=0, sticky=tk.NSEW)
        # Target Image Content although the variable name is the same
        self.target_img_lb = tk.Label(self.target_img_frame)
        self.target_img_lb["text"] = "Target Image"
        self.target_img_lb.grid(row=0, column=0, sticky=tk.NSEW)
        #Nav Visualizer Content
        self.navigationvis = NavigationVisualizer(self.navgrid_frame)
        self.nav_canvas = self.navigationvis.canvas

        self.USimg_frame.grid(row=0, column=0, padx=5, pady=2, sticky=tk.NSEW)
        #self.saved_img_frame.grid(row=1, column=0, padx=5, pady=2, sticky=tk.NSEW)
        self.target_img_frame.grid(row=1, column=0, padx=5, pady=2, sticky=tk.NSEW)

        self.nav_canvas.get_tk_widget().grid(row=0, column=1, rowspan=2, sticky=tk.NSEW)


        self.navgrid_frame.grid(row=0, pady=8, padx=8, sticky=tk.NSEW)
        self.navgrid_frame.after_idle(self.calculate_US_imgsize)

        self.exam_data_frame = tk.Frame(self.navigation_frame, bg='green')
        self.exam_data_frame.rowconfigure(0, weight=0)
        self.exam_data_frame.rowconfigure(1, weight=0)
        self.exam_data_frame.columnconfigure(0, weight=1)

        # Examinationdata Frame Content
        self.sysmode_lb = tk.Label(self.exam_data_frame)
        self.sysmode_lb["text"] = "Operating Mode: - "
        self.sysmode_lb["font"] = ('Open Sans', 10)
        self.sysmode_lb.grid(row=0, column=0, pady=10, sticky=tk.NSEW)
        #self.sysmode_icon_lb = tk.Label(self.exam_data_frame)

        empty_pos = [Handle('',''), Handle('',''), Handle('',''), Handle('','')]
        self.tracking_data_frame = self.build_position_summary(master=self.exam_data_frame, position=empty_pos)
        self.tracking_data_frame.grid(row=1,column=0, padx=10, sticky=tk.NSEW)

        self.exam_data_frame.grid(row=1, column=0, padx=2, pady=2, sticky=tk.NSEW)

        self.statistic_frame = self._build_statistics_table(self.navigation_frame, None)
        self.statistic_frame.grid(row=2, column=0, sticky=tk.NSEW)

        scroll.grid(row=0, column=0,sticky=tk.NSEW)


    def _build_statistics_table(self, master, title_id):
        frame = tk.Frame(master=master, bg='yellow')
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=0)
        frame.columnconfigure(0, weight=1)

        title_lb = tk.Label(frame)
        title_lb["text"] = f"Statistic for Comparing {title_id}"
        title_lb["font"] = ('Open Sans', 10)

        title_lb.grid(row=0, column=0, pady=10, sticky=tk.NSEW)

        self.statistics_table_frame = fr = tk.Frame(frame)
        self.statistics_table = None
        fr.grid(row=1, column=0, pady=10, sticky=tk.NSEW)

        return frame

    def set_statistics_table(self, df: pd.DataFrame):
        if not self.statistics_table:
            self.statistics_table = pt = Table(self.statistics_table_frame, dataframe=df,
                                                showtoolbar=False, showstatusbar=True)
            pt.show()
        else:
            self.statistics_table.redraw()

    def get_statistics_table(self):
        return self.statistics_table

    def switch_imgsrc(self):
        '''Switches between the VideoinputSource and the savedimaged frame'''
        self.switch_imgsrc_but["state"] = 'normal'
        if self.USimg_frame.winfo_ismapped():
            logger.debug("Switched to SavedImgFrame")
            self.USimg_frame.grid_forget()
            self.saved_img_frame.grid(row=0, column=0, padx=5, pady=2, sticky=tk.NSEW)
            self.switch_imgsrc_but["text"] = "Wechsel zu Video"
        elif self.saved_img_frame.winfo_ismapped():
            logger.debug("Switched to USimgframe")
            self.saved_img_frame.grid_forget()
            self.USimg_frame.grid(row=0, column=0, padx=5, pady=2, sticky=tk.NSEW)
            self.switch_imgsrc_but["text"] = "Wechsel zu Aufnahme"
        else:
            logger.debug("No Switcheruu today. Please check the call!")

    @clear_frame
    def build_openeval_frame(self,master):
        self.open_eval_frame = frame = tk.Frame(master)
        frame.rowconfigure(0, weight=1, uniform=1)
        frame.columnconfigure(0,weight=1,uniform=1)
        lb = tk.Label(frame,text="Wählen Sie eine Evaluation ID zur Auswertung aus")
        self.eval_opts_var = tk.StringVar(frame)
        self.eval_opts_var.set('')
        self.eval_option_menu = tk.OptionMenu(frame, self.eval_opts_var, ' ')

        self.load_eval_but = tk.Button(frame)
        self.load_eval_but["text"] = "Lade Auswertung"

        lb.pack(side=tk.TOP, pady=(20, 5),padx=(10))
        self.eval_option_menu.pack(side=tk.TOP, pady=(10),padx=(10))
        self.load_eval_but.pack(side=tk.TOP, pady=(10),padx=(10))
        frame.grid(row=0, column=0,sticky=tk.NSEW)

    def set_eval_menu(self, eval_list):
        '''Loads the distinct E_IDs from the comparison table into the dropdown.'''
        self.eval_opts_var.set(eval_list[-1])
        self.eval_option_menu['menu'].delete(0, 'end')
        for e_id in eval_list:
            self.eval_option_menu['menu'].add_command(label=e_id, command=tk._setit(self.eval_opts_var, e_id))

    @clear_frame
    def build_evaluation_frame(self, master):
        scroll = ScrollableFrame(master=master)
        self.eval_frame = frame = scroll.contentframe

        frame.rowconfigure(0, weight=1, uniform=1)
        frame.rowconfigure(1, weight=1, uniform=1)
        frame.columnconfigure(0,weight=1,uniform=1)

        compare_frame = self._build_statistics_table(frame, None)
        compare_frame.grid(row=2, column=0, sticky=tk.NSEW)
        scroll.grid(row=0, column=0,sticky=tk.NSEW)


    def _build_tab2(self):
        # Tab2
        self.t2_debugFrame = tk.Frame(self.tab_control, bg="grey")
        self.t2_debugFrame.rowconfigure(0, weight=1)
        self.t2_debugFrame.columnconfigure(0, weight=80)
        self.t2_debugFrame.columnconfigure(1, weight=20)

        self.t2_left_frame = tk.Frame(self.t2_debugFrame, bg="green")
        self.t2_left_frame.columnconfigure(0, weight=1)
        self.t2_right_frame = tk.Frame(self.t2_debugFrame, bg="blue")
        self.t2_right_frame.columnconfigure(0, weight=1)
        self.t2_right_frame.columnconfigure(2, weight=1)
        self.t2_right_frame.rowconfigure(0, weight=1)
        self.t2_right_frame.rowconfigure(10, weight=1)

        self.t2_left_frame.grid(row=0, column=0, pady=8, padx=8, sticky=tk.NSEW)
        self.t2_right_frame.grid(
            row=0,
            column=1,
            pady=8,
            padx=8,
            sticky=tk.NSEW)

        self.build_DebugMenu(self.t2_left_frame)
        self.build_DebugCMD(self.t2_right_frame)

        self.t2_debugFrame.pack(fill=tk.BOTH, expand=tk.TRUE)

    def build_DebugMenu(self, lFrame):
        self.debugMenuLabel = tk.Label(lFrame, text="Debug Menu Options")
        self.initBut = tk.Button(lFrame)
        self.initBut["text"] = "INIT"

        self.readBut = tk.Button(lFrame)
        self.readBut["text"] = "READ Serial"

        self.resetBut = tk.Button(lFrame)
        self.resetBut["text"] = "Reinitialize System"

        self.testBut = tk.Button(lFrame)
        self.testBut["text"] = "Test Something"

        self.handleBut = tk.Button(lFrame)
        self.handleBut["text"] = "Activate Handles"

        self.restartBut = tk.Button(lFrame)
        self.restartBut["text"] = "Restart Program"

        self.quitBut = tk.Button(lFrame, text="QUIT", fg="red")

        # Place-Geomanager for Leftframe
        self.debugMenuLabel.grid(row=0, padx=(1, 1), sticky=tk.NSEW)
        self.initBut.grid(row=1, padx=(1, 1))
        self.readBut.grid(row=2, padx=(1, 1), sticky=tk.NSEW)
        self.resetBut.grid(row=3, padx=(1, 1), sticky=tk.NSEW)
        self.testBut.grid(row=4, padx=(1, 1), sticky=tk.NSEW)
        self.handleBut.grid(row=5, padx=(1, 1), sticky=tk.NSEW)
        # self.restartBut.pack()
        self.quitBut.grid(row=6, padx=(1, 1), sticky=tk.NSEW)

        for i, child in enumerate(lFrame.winfo_children(), start=0):
            lFrame.rowconfigure(i, weight=1)
            if (child.winfo_class() == 'Button'):
                child["width"] = 35
                child["height"] = 2
                child.grid_propagate(0)

    def build_DebugCMD(self, rFrame):
        self.cmdLabel = tk.Label(rFrame, text="CMD")
        self.cmdEntry = tk.Entry(rFrame, bd=5)
        self.expecLabel = tk.Label(
            rFrame, text="Expected read ending character")
        self.expec = tk.Entry(rFrame, bd=5)
        self.sleepLabel = tk.Label(rFrame, text="Read sleep time")
        self.sleeptimeEntry = tk.Entry(rFrame, bd=5)
        self.sleeptimeEntry.insert(0, 0)

        self.cmdLabel.grid(row=1, column=1, pady=(10, 2), sticky=tk.EW)
        self.cmdEntry.grid(row=2, column=1, sticky=tk.EW)
        self.expecLabel.grid(row=3, column=1, pady=(10, 2), sticky=tk.EW)
        self.expec.grid(row=4, column=1, sticky=tk.EW)
        self.sleepLabel.grid(row=5, column=1, pady=(10, 2), sticky=tk.EW)
        self.sleeptimeEntry.grid(row=6, column=1, sticky=tk.EW)

    def initImages(self):

        imgdir = _cfg.IMGPATH
        self.notfoundimg = imgdir + "not-found-image.jpg"

        # Bilder f�r x-Achse
        self.x_links_orange = self.getImage_fromfile("x-links-orange.jpg")
        self.x_links_rot = self.getImage_fromfile("x-links-rot.jpg")
        self.x_rechts_orange = self.getImage_fromfile("x-rechts-orange.jpg")
        self.x_rechts_rot = self.getImage_fromfile("x-rechts-rot.jpg")

        # Bilder f�r Rotation auf x-Achse
        self.x_achse_kippen_links_orange = self.getImage_fromfile(
            "x-achse-kippen-links-orange.jpg")
        self.x_achse_kippen_links_rot = self.getImage_fromfile(
            "x-achse-kippen-links-rot.jpg")
        self.x_achse_kippen_rechts_orange = self.getImage_fromfile(
            "x-achse-kippen-rechts-orange.jpg")
        self.x_achse_kippen_rechts_rot = self.getImage_fromfile(
            "x-achse-kippen-rechts-rot.jpg")

        # Bilder f�r y-Achse
        self.y_vorne_orange = self.getImage_fromfile("y-vorne-orange.jpg")
        self.y_vorne_rot = self.getImage_fromfile("y-vorne-rot.jpg")
        self.y_hinten_orange = self.getImage_fromfile("y-hinten-orange.jpg")
        self.y_hinten_rot = self.getImage_fromfile("y-hinten-rot.jpg")

        # Bilder f�r Rotation auf y-Achse
        self.y_achse_kippen_links_orange = self.getImage_fromfile(
            "y-achse-kippen-links-orange.jpg")
        self.y_achse_kippen_links_rot = self.getImage_fromfile(
            "y-achse-kippen-links-rot.jpg")
        self.y_achse_kippen_rechts_orange = self.getImage_fromfile(
            "y-achse-kippen-rechts-orange.jpg")
        self.y_achse_kippen_rechts_rot = self.getImage_fromfile(
            "y-achse-kippen-rechts-rot.jpg")

        # Bilder f�r z-Achse
        self.z_oben_orange = self.getImage_fromfile("z-oben-orange.jpg")
        self.z_oben_rot = self.getImage_fromfile("z-oben-rot.jpg")
        self.z_unten_orange = self.getImage_fromfile("z-unten-orange.jpg")
        self.z_unten_rot = self.getImage_fromfile("z-unten-rot.jpg")

        # Bilder f�r Rotation auf z-Achse
        self.z_achse_kippen_links_orange = self.getImage_fromfile(
            "z-achse-kippen-links-orange.jpg")
        self.z_achse_kippen_links_rot = self.getImage_fromfile(
            "z-achse-kippen-links-rot.jpg")
        self.z_achse_kippen_rechts_orange = self.getImage_fromfile(
            "z-achse-kippen-rechts-orange.jpg")
        self.z_achse_kippen_rechts_rot = self.getImage_fromfile(
            "z-achse-kippen-rechts-rot.jpg")

        # Bilder f�r Eigen-Rotation
        self.self_rot_links_orange = self.getImage_fromfile(
            "self-rot-links-orange.jpg")
        self.self_rot_links_rot = self.getImage_fromfile("self-rot-links-rot.jpg")
        self.self_rot_rechts_orange = self.getImage_fromfile(
            "self-rot-rechts-orange.jpg")
        self.self_rot_rechts_rot = self.getImage_fromfile("self-rot-rechts-rot.jpg")

        # Bild als Ziel
        self.ziel = self.getImage_fromfile("ziel.jpg")

    def getImage_fromfile(self, filename, asTKImage=True):
        # Opens Image and translates it to TK compatible file.
        #filename = self.imgdir+filename

        try:
            tkimage = Image.open(filename)

        except FileNotFoundError as err:
            logger.exception("File was no found, Err Img replace\n" + err)
            tkimage = self.notfoundimg

        finally:
            return ImageTk.PhotoImage(tkimage) if asTKImage else tkimage
