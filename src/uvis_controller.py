"""
The uvis_controller module contains the major logic of the application.
:class:`UltraVisController` implements the logic.
"""

import logging
import os
import queue
import random
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from functools import partial
from itertools import zip_longest
from pathlib import Path
from tkinter.font import Font

import pandas as pd
import serial
from cv2 import cv2
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image, ImageTk

from src.aurora import Aurora, Handle, HandleManager
from src.Calibrator import Calibrator
from src.config import Configuration
from src.helper import Helper
from src.uvis_model import (Comparison, Evaluation, Examination, Record,
                            UltraVisModel)
from src.uvis_view import UltraVisView


# Module Configs and helper classes
global hp
global _cfg
hp = Helper()
_cfg = Configuration()
logger = _cfg.LOGGER

SUM_MAXHEIGHT = 4
SUM_TITLE_PADY = 5

class UltraVisController:
    """
    :param bool debug_mode:
        Enables debug functionality in the app.
        The main.py normally sets this parameter.

    The UltraVisController class controls the application flow and connects all
    modules of the uvis app.
    """

    def __init__(self, debug_mode=False):

        #Create Model and View
        self.root = tk.Tk()

        self.calibrator = Calibrator()
        self.target_calibrator = Calibrator()
        self.model = UltraVisModel()
        #self._do_data_evaluation()
        self.view = UltraVisView(self.root, debug_mode=debug_mode)

        #Controller Attributes
        self._debug = debug_mode
        self.hm = None
        self.aua = None

        self._initObservers()
        self._initBackgroundQueue()

        #Init Aurorasystem + Serial COnfig
        self.ser = serial.Serial()
        self.ser.port = _cfg.COM
        self.ser.baudrate = 9600
        self.ser.parity = serial.PARITY_NONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.xonxoff = False
        self.ser.timeout = 2

        #Tries to initalize Aurora and Adds Functionaly based on state
        self.init_aurora(self.ser)
        self.init_button_func()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """
        Closing method when the root window is closed.
        Stops all relevant processing for a clean exit.
        """
        if (hasattr(self.view, 'examination_frame')):
             #Close FrameGrabber
            self.view.USimg_lb.after_cancel(self._framegrabber_job)
            self.cap.release()

            #Close Tracking + Matplotanimation
            if (self.aua_active):
                if(self.aua.get_sysmode()=='TRACKING'):
                    self.stopTracking = True
                    #self.view.navCanvas._tkcanvas.after_cancel(self.view._Canvasjob)
                    with self.aua._lock:
                        self.aua.tstop()

        self.quitEvent.set()
        self.ser.close()

        #Bug that plt.close also closes the TKinter Windows!
        if (hasattr(self.view,'fig')):
            pass
            #plt.close(fig=self.view.fig)
        logger.info("Good Night Cruel World :D")
        self.root.quit()
        self.root.destroy()

    def run (self):
        """Starts the tkinter mainloop after :func:`__init__`."""
        self.root.mainloop()

    def _initBackgroundQueue(self):
        """ Initializes a :class:`threading.Queue` in the background for parallel processing (e.g. :func:`init_aurora`)"""

        self.q = queue.Queue(maxsize=8)
        self.quitEvent = threading.Event()
        def processQueue(self):
            logger.info("Initialize Queue")
            x = 0
            while (not self.quitEvent.is_set() or not self.q.empty()):

                if (self.q.empty()):
                    #if (x%5==0):
                        #logger.debug("Waiting for Event")
                    x += 1
                    time.sleep(1.5)
                    continue

                func = self.q.get()
                thread = threading.Thread(target=func)

                logger.info(f"Start {thread.getName()}: process {func.__name__}()")
                time.sleep(0.25)
                thread.start()
                thread.join()
                self.q.task_done()
                logger.info(thread.getName()+" is finished - Alive: "+str(thread.is_alive()))
                logger.debug(f'Current pipeline: {self.q.qsize()} items')

            logger.info("Queue is closed")

        q_Thread = threading.Thread(target=processQueue,daemon=True,args=(self,),name="Q-Thread")
        q_Thread.start()

    def _initObservers(self):
        self.model.register(key="set_current_workitem", observer=self.refreshWorkItem)

    def _init_framegrabber(self):
        self.cap = cv2.VideoCapture(_cfg.VID_INPUT)

    def init_aurora(self, ser):
        """Initializes the NDI Aurora system (see for details :class:`aurora.Aurora`).

        :param serial.Serial ser:
            The Serial object configured to the NDI Aurora System.
        """

        logger.info("Initialize Aurorasystem - Try connecting to Aurorasystem")

        widgets = self.view.menu_frame.winfo_children()
        self.aua_active = False
        try:
            self.aua = Aurora(ser, debug_mode=self._debug)
        except serial.SerialException as e:
            logger.warning("serial.SerialException: "+str(e))
            #self.disable_widgets(widgets)
            self.view.reinit_aua_but.pack(side=tk.TOP, pady=(0, 0),padx=(10), fill="both")
            self.view.reinit_aua_but["state"] = 'normal'
            self.view.reinit_aua_but["command"] = lambda: self.init_aurora(self.ser)
            return
        except Warning as w:
            logger.exception(str(w))
            #self.disable_widgets(widgets)
            self.view.reinit_aua_but.pack(side=tk.TOP, pady=(0, 0),padx=(10), fill="both")
            self.view.reinit_aua_but["state"] = 'normal'
            self.view.reinit_aua_but["command"] = lambda: self.init_aurora(self.ser)
            return

        logger.info("Connection success")
        self.aua_active = True
        self.aua.register("set_sysmode", self.refresh_sysmode)
        hp.enable_widgets(widgets)
        self.view.reinit_aua_but.pack_forget()

        logger.info("Reset Aurorasystem")
        self.aua.reset_and_init_system()

        self.addFuncDebug()
        logger.info("Initialize Aurorasystem - done")

    #   -----Aurora Setup Functionality  ------#

    def activateHandles(self):
        """Initializes and activated the handles in order to start tracking. See NDI Aurora API Guide for more details."""

        # todo Gesamtprozess nach Guide (siehe Aurora API)
        logger.info("Activate Handles - Acquiring Lock")

        success = True
        with self.aua._lock:
            try:
                logger.info("All allocated Ports")
                phsr_string = self.aua.phsr()

                self.hm = HandleManager(phsr_string)
                handles = self.hm.get_handles()

                # print("handles 02")
                # Occupied handles but not initialized or enabled
                # self.aua.phsr(2)

                # Alle Port-Handles Initialisieren
                # Alle Port-Hanldes aktivieren
                logger.info(str(self.hm.get_numhandles())+" Handles identified")
                logger.info("Initializing Port-Handles")


                for h_id in handles :
                    self.aua.pinit(handles[h_id])
                    self.aua.pena(handles[h_id],'D')

                # Pr�fen, ob noch Handles falsch belegt sind
                # self.aua.phsr(3)
                # print("handles 03")
                # ser.write(b'PHSR 03\r')
                # time.sleep(1)
                # readSerial(ser)

                time.sleep(0.5)

            except Warning as w:
                logger.warning(str(w))
                success=False
                #maybe solve via states in show menu Later
                self.view.activate_handle_but.pack(side=tk.TOP, pady=(0, 0),padx=(10), fill="both")

        logger.info("Activate Handles - finished with NO_ERRORS" if success else "Activate Handles - finished with ERRORS")


    #---- App Frame functionality tracking and saving----#

    def startstopTracking(self):
        """Starts / Stops the current tracking process of the Aurora System"""

        if (self.aua.get_sysmode()=='SETUP'):
            with self.aua._lock:
                self.aua.tstart(40)

            #Thread starte Thread und gebe den AppFrame GUI die Daten
            self.stopTracking = False
            self.tracking_Thread = threading.Thread(target=self.track_handles,daemon=True,name="tracking_Thread")
            self.tracking_Thread.start()
            self.view.build_position_summary
            if hasattr(self.view, 'nav_canvas'):
                self.view._Canvasjob = self.view.nav_canvas._tkcanvas.after(2000,func=self.view.build_coordinatesystem)

        elif(self.aua.get_sysmode()=='TRACKING'):
            self.stopTracking = True
            if hasattr(self.view, 'nav_canvas'):
                self.view.nav_canvas._tkcanvas.after_cancel(self.view._Canvasjob)
            self.tracking_Thread.join()

            with self.aua._lock:
                self.aua.tstop()

    def track_handles(self):
        """Acquires the handle data from the Aurora system. Data is available from the :class:`aurora.Handlemanager`.
        Can either be done with `bx` or `tx`. Use `bx` for faster processing.
        """
        #Stop as soon the event is set
        #Verringern der Update Data frequenz

        logger.info(threading.current_thread().name+" has started tracking")
        perma_plot = False
        freq = 0.01
        missing = False
        while(not self.stopTracking):
            t0 = datetime.now()
            with self.aua._lock:
                bx = True
                if bx:
                    header, data = self.aua.bx()
                    if self.hm.update_handlesBX(header, data):
                        self.setNavCanvasData()
                        if missing:
                            missing = False
                            logger.info(f"All Handles are now active! :-)")
                    else:
                        missing = True
                        miss = self.hm.get_missing_handles()
                        logger.info(f"MISSING HANDLE! {miss}")
                    if perma_plot:
                        self.refresh_position_data() # TODO Takes HALF A SECOND !!! Performance Killer
                else:
                    #TX can be removed for readability. BX is better generally speakin
                    tx = self.aua.tx()
                    self.hm.update_handles(tx)
                    self.setNavCanvasData()
                    self.refresh_position_data()
            time.sleep(freq)
            t1 = datetime.now()
            #logger.debug(t1-t0)

        self.stopTracking = False
        logger.info(threading.current_thread().name+" has stopped!")

    def refresh_position_data(self):
        """Refreshes and visualizes the tracking data in tabular form. See :func:`UltraVisView.build_position_summary`."""

        #av_color = ['yellow','red','green','blue']
        #color = []
        #num_handle = self.hm.get_numhandles()
        #if (num_handle is not 4):
            #logger.warning(f'There are {num_handle} handles identified. Is that correct?')
            #color = color[:num_handle]
        t0=datetime.now()

        position = self.hm.get_handles(real_copy=True)
        handle_rows = self.view.position_summary_widgets

        # TODO das iterieren durch die Objekte kostet mega viel Zeit
        for row, handle in zip(handle_rows, position.values()):
            for widget, value in zip(row, handle.__dict__.values()):

                value_text = tk.StringVar()
                value_text.set(value)
                if widget.winfo_class() == 'Entry':
                    #widget.delete(0, tk.END)
                    widget.configure(textvariable=value_text)
                elif widget.winfo_class() == 'Text':
                    widget.delete(0, tk.END)
                    logger.info("Dumbass")
                    widget.insert(0, value)
                else:
                    logger.debug(f'Wrong class? {widget.winfo_class()}')
        t2= datetime.now()

        #logger.debug(f'Display shit {(t2-t0)}')

    #Example of using the hm data +TODO Should be renamed imo.
    def setNavCanvasData(self):
        """Transforms the handle data to the correct reference system with the :class:`Calibrator` and then
        provides the data to the view (:class:`NavigationVisualizer` to be precise)."""

        x,y,z,a,b,c = [],[],[],[],[],[]
        av_color = ['yellow','red','green','blue']
        color = []
        num_handle = self.hm.get_numhandles()
        if (num_handle is not 4):
            logger.warning(f'There are {num_handle} handles identified. Is that correct?')
            color = color[:num_handle]

        handles = self.hm.get_handles()
        #Might change for Items, if the specific request of handle object is neccessary.

        for i,handle in enumerate(handles.values()):
            if (handle.MISSING is None):
                logger.debug("Please check.")
                break

            if (handle.MISSING is False):
                # TODO only for uvis sensor
                if (i == 0):
                    transformed = self.calibrator.transform_backward([float(handle.Tx), float(handle.Ty), float(handle.Tz)])
                    x.append(transformed[0])
                    y.append(transformed[1])
                    z.append(transformed[2])

                    temp_a, temp_b, temp_c = self.calibrator.quaternion_to_rotations(handle.Q0, handle.Qx, handle.Qy, handle.Qz)
                    a.append(temp_a)
                    b.append(temp_b)
                    c.append(temp_c)
                else:
                    x.append(handle.Tx)
                    y.append(handle.Ty)
                    z.append(handle.Tz)

                color.append(av_color[i])

        #logger.debug(f'x values: {x}')

        self.view.navcanvas_data = (x,y,z,a,b,c,color)

    #Position is saving Record and Handles
    # TODO RENAME THIS METHOD, IT IS THE SAME IN THE MODEL AN CONFUSING!!!
    def save_record(self):
        """Acquires record data (ultrasound image, current date etc.) in an :class:`uvis_model.Record` object
        and persist the data with the :class:`uvis_model.UltraVisModel`."""

        if (not self.aua.get_sysmode()=='TRACKING'):
            logger.info("This functionality is only available during tracking. Please Start Tracking")
            return

        # Save the Image
        cv2image = cv2.cvtColor(self.grabbed_frame, cv2.COLOR_BGR2RGBA)
        self.view.saved_img = Image.fromarray(cv2image)
        self.view.refresh_saved_img()
        img = self.view.saved_img.copy()
        img = img.resize(self.orignal_imgsize, Image.ANTIALIAS)

        dt = datetime.now()
        tmpstamp = dt.strftime("%a, %d-%b-%Y (%H:%M:%S)")

        # Description atrtibute, aus der GUI
        # Gets Current Workitem and accesses its Examination
        workitem = self.model.get_current_workitem()
        E_ID = workitem["Examination"].E_ID
        rec = Record(date=tmpstamp, E_ID=E_ID)
        img_name = f'{rec.R_ID[4:]}_img'
        handles = self.hm.get_handles(real_copy=True)

        if (self.validatePosition(handles)):

            #try saving image and the record
            try:
                path = self.model.save_PIL_image(img=img, img_name=img_name)
                rec.US_img=path
                self.model.save_record(record=rec)
            except IOError as e:
                raise Warning("Error during saving the image. \nErrorMessage:"+str(e))
            except ValueError as e:
                #Konnte Aufzeichnung nicht speichern. Please try again with SAME DATA!
                return False

            #try saving corresponding Position
            try:
                self.model.save_position(R_ID=rec.R_ID, handles=handles)
            except ValueError as e:
                #Konnte handles nicht speichern. Please try again with SAME DATA?!
                return False

            self.model.set_current_workitem(rec)
            self.model.set_current_workitem(handles.values())
            return True

    def validatePosition(self, handles):
        """Validates the 4 handles ("position") before saving. It checks the frameID and missing handles."""
        handles = handles
        validSave = True
        missID = []
        frameID = []
        for h_id in handles:
            h = handles[h_id]
            if(h.MISSING):
                validSave = False
                missID.append(h_id)
            #check for ID and frameID must not be empty
            if ((h.frame_id not in frameID) and not not frameID):
                validSave = False
            frameID.append(h.frame_id)
        if (not validSave):
            logger.error("Trying to save Position with missing Handles: "+str(missID)+". Please use valid Data")
        return validSave

    #----GUI Related ----#

    def new_examination(self):
        """Starts the GUI for new examinations."""
        self.view.build_newExam_frame(master=self.view.right_frame)
        self.view.show_menu(menu='new_examination')
        self.view.continue_but["command"] = self.setup_handles

    def validate_new_examination(self):
        """
        :returns: isValid indicator, :class:`uvis_model.Examination`

        :rtype: bool, :class:`uvis_model.Examination`

        Validates the data from the "new examination" frame and returns :class:`uvis_model.Examination` object."""
        #if there is future validation necessary e.g. Patient data is required, you need to implement it here
        doctor = self.view.doctor_entry.get()
        patient = self.view.patient_entry.get()
        examitem = self.view.exam_item_textbox.get("1.0",'end-1c')
        created = self.view.created_entry.get()

        params = {"E_ID" :None, "doctor":doctor, "patient":patient, "examitem":examitem, "created":created}
        new_exam = Examination(**params)
        logger.debug(f'Exam Data - {new_exam}')

        #Due to no validation as of now,
        validExam = True

        return validExam, new_exam

    def setup_handles(self):
        """Validates the examination meta data and starts the GUI for "setup handles"."""
        #save exam procudere should be actually somewhere else ...
        validExam, new_exam = self.validate_new_examination()
        if (validExam):
            try:
                self.model.save_examination(examination=new_exam)
                self.model.set_current_workitem(obj=new_exam)
            except ValueError as e:
                msg = "Could not save Examination. See logs for details."
                self.view.set_info_message(msg)
                return
        else:
            logger.error(f'Invalid Examinationdata')
            return

        self.view.build_setup_frame(master=self.view.right_frame)
        self.view.show_menu(menu='setup')
        self.addSetupHandlesFunc()

        #Starts activating the handles in the background. So system calibration can be done.
        if (self.aua_active):
            self.q.put(self.activateHandles)

    def validate_setuphandles(self, handle_index=None):
        """
        :param int handle_index: index of 0-3 or :const:`None`

        :return: isValid indicator.

        :rtype: bool

        :exception ValueError:
            Will be raised when handle_index are out of range or incorrect.

        Validates the data from the "setup handles" frame.
        """

        last_index = self.hm.get_numhandles() - 1 if self.hm is not None else 3
        setuphandles = self.view.setuphandle_frames
        isValid = None

        #Check all handles and start next App part
        if handle_index is None:

            valid_list = []
            for setuphandle in setuphandles:
                valid_list.append(setuphandle['valid'])

            if False in valid_list and not self._debug:
                self.view.set_setup_instruction("Sie müssen zuerst alle Spulen anschließen bevor Sie Untersuchung beginnen können")
                logger.info(f"Invalid Setuphandles. See List: {valid_list}")
                isValid = False
            else:
                isValid = True

            return isValid

        #Check Single Index
        elif handle_index <= last_index:

            # check handle Data
            setuphandle = setuphandles[handle_index]
            entry = setuphandle["ref_entry"]
            ref_value = entry.get()

            if (len(str(ref_value)) is not 0):
                setuphandle["valid"] = True
            else:
                self.view.set_setup_instruction("Bitte tragen Sie einen Referenznamen für die Spule ein")
                isValid = False
                return isValid

            if (handle_index != last_index):
                self.view.set_current_setuphandle(handle_index+1)
            else:
                self.view.instruction_lb["bg"] = "SpringGreen"
                self.view.set_setup_instruction("Einrichtung der Spulen abgeschlossen. Sie können mit der Untersuchung beginnen :)")
                setuphandle["frame"]["bg"] = 'white'
                children = setuphandle["frame"].winfo_children()
                hp.disable_widgets(children,disable_all=True)
                isValid = True
                return isValid
        else:
            raise ValueError(f"Invalid Handle_index: {handle_index}.")

    def start_examination(self):
        """Starts the GUI for the "examination"."""
        is_valid_setuphandles = self.validate_setuphandles()
        if (is_valid_setuphandles):
            handles = self.hm.get_handles().values()
            setuphandles = self.view.setuphandle_frames
            for i,pair in enumerate(zip(handles, setuphandles)):
                handle, setuphandle = pair
                entry = setuphandle["ref_entry"]
                refname = entry.get()
                handle.set_reference_name(refname)

            self.view.build_examination_frame(master=self.view.right_frame)
            self.view.show_menu(menu='examination')
            #self.target_img_frame.bind('<Configure>', lambda refr: self.refresh_img_for_lb(frame=self.navgrid_frame))
            self._init_framegrabber()
            self.capture_framegrabber(label=self.view.USimg_lb)
            self.view.refresh_imgsize(self.view.grid_frame)
            self.view.continue_but["command"] = partial(self.q.put, self.finalize_examination)
        else:
            return

    def capture_framegrabber(self, label, ms_delay=35):
        """
        :param tkinter.Label label: The tkinter label in which the video source is rendered.

        :param int ms_delay: The refresh rate for the video stream.

        :returns: Returns the scheduler_id for canceling the frame grabber job with the after_cancel method.

        Starts a background process for continuously refreshing the given label, with the grabbed image.
        The label must be a :class:`tkinter.Label` object. For the delay the :func:`tkinter.Label.after` method
        is used.
        """
        if (not isinstance(label, tk.Label)):
            raise TypeError (f'Expected {tk.Label} for parameter label \
                               but got {type(label)} instead.')

        _, self.grabbed_frame = self.cap.read()
        #self.frame = cv2.flip(frame, 1)
        if self.grabbed_frame is None:
            logger.warning("Empty Frame - No device was found")
            label["text"] = "EMPTY FRAME \n No device was found"
            label.after(10000, self.capture_framegrabber, label, ms_delay)
            return
        if (label.master.winfo_height() == 1):
            cv2image = cv2.cvtColor(self.grabbed_frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            self.orignal_imgsize = img.size
            label.after(1500, self.capture_framegrabber, label, ms_delay)
            return

        cv2image = cv2.cvtColor(self.grabbed_frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        if (self.view.img_size is not None):
            img = img.resize(self.view.img_size, Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(image=img)

        label.imgtk = imgtk
        label.configure(image=imgtk)

        self._framegrabber_job = label.after(
            ms_delay, self.capture_framegrabber, label, ms_delay)

    def calibrate_coordsys(self, calibrator=None, handles=None):
        """
        :param Calibrator calibrator: Preconfigured calibrator object or :const:`None`.

        :param dict handles: A dictionary containing :class:`aurora.Handle` objects :const:`None`.

        Calibrates by default the reference coordinate system of the application.
        An individual :class:`Calibrator` object can also be given (e.g. for loading recorded data).
        """
        if (calibrator is None and self.aua.get_sysmode() != 'TRACKING'):
            logger.warning("Please start tracking before calibrating.")
            return
        logger.info("Calibrate Coordinate System")
        cali = self.calibrator if not calibrator else calibrator
        handles = self.hm.get_handles() if not handles else handles

        num_handle = self.hm.get_numhandles()
        if (num_handle != 4):
            logger.warning(f'There are {num_handle} handles identified. Need 4 handles for calibration!')
        else:
            a = [handles['0B'].Tx, handles['0B'].Ty, handles['0B'].Tz] # becken rechts
            b = [handles['0C'].Tx, handles['0C'].Ty, handles['0C'].Tz] # becken links
            c = [handles['0D'].Tx, handles['0D'].Ty, handles['0D'].Tz] # brustbein

            trafo_param = [a,b,c]
            for i, vector in enumerate(trafo_param):
                trafo_param[i] = hp.to_float(vector)
            cali.set_trafo_matrix(a,b,c, log_matrix=True)

    def set_target_pos(self, calibrator=None, handles=None):
        """
        :param Calibrator calibrator: Preconfigured calibrator object or :const:`None`.

        :param dict handles: A dictionary containing :class:`aurora.Handle` objects or :const:`None`.

        By default it sets a target in the navigation visualzation for the current reference coordinate system.
        Alternatively it is used to load a Record and set that data as a target.
        """
        logger.info("Set Target Position")
        pos = [0.0, 0.0, 0.0]
        cali = self.calibrator if not calibrator else calibrator
        handles = self.hm.get_handles() if not handles else handles

        num_handle = self.hm.get_numhandles()
        if (num_handle is not 4):
            logger.warning(f'There are {num_handle} handles identified. Is that correct?')
        else:
            current_pos = hp.to_float([handles['0A'].Tx, handles['0A'].Ty, handles['0A'].Tz])
            #current_ori = self.calibrator.quaternion_to_rotation_matrix(handles['0A'].Q0, handles['0A'].Qx, handles['0A'].Qy, handles['0A'].Qz)
            #print(current_ori)

            a, b, c = cali.quaternion_to_rotations(handles['0A'].Q0, handles['0A'].Qx, handles['0A'].Qy, handles['0A'].Qz)
            pos = cali.transform_backward(current_pos)

            self.view.navigationvis.set_target_pos(pos[0], pos[1])
            self.view.navigationvis.set_target_ori(a, b, c)

    # TODO Muss Logik einbauen, dass das System dabei auch resettet wird &
    # das GUI etc. korrekt gestoppt wird
    def cancel_examination(self, save=False):
        """Cancels current workflow and loads the main menu frame."""
        self.view.build_mainscreen_frame(master=self.view.right_frame)
        self.view.show_menu()

    def validate_examination(self):
        """Validates the data from the "examination" frame. """
        isValid = True

        workitem = self.model.get_current_workitem()
        #Check whether record is in workitem.
        if not workitem["Records"]:
            isValid = False
        elif False:
            #another Validation
            pass

        return isValid

    # doppel klick soll verhindert werden, maybe über check, current menu
    def finalize_examination(self):
        """Starts the GUI for the "examination summary", after persisting the current workitem."""
        isValidExam = self.validate_examination()
        if (isValidExam):

            try:
                new_E_ID = self.model.persist_workitem()
            except ValueError as e:
                msg = "Could not save Examination. See logs for details."
                self.view.set_info_message(msg)
                logger.error(str(e))
                return

            if self.aua.get_sysmode() == "TRACKING":
                self.startstopTracking()
            self.model.load_workitem(new_E_ID)
            self.view.build_summary_frame(master=self.view.right_frame)
            self.view.show_menu(menu='summary')
            self.build_summary()
            #self.model.clear_temp_data()

        else:
            msg = f'Can\'t finish Examination, without any Records. Please create Records first.'
            logger.info(msg)
            self.view.set_info_message(msg=msg,type='ERROR')
            return

    def build_summary(self):
        """Build the summary for "examination summary" frame."""
        exam, records, handles = self.model.get_current_workitem().values()
        summary_frame = self.view.summary_content_frame
        summary_frame.columnconfigure(0, weight=1)

        hp.set_row(0)
        r = hp.get_next_row()

        summary_frame.rowconfigure(r, weight=1)
        exam_summary = self.view.build_exam_summary(master=summary_frame, exam=exam)
        exam_summary.grid(row=r, column=0, sticky=tk.NSEW, pady=5)

        for i,rec in enumerate(records):
            b = hp.get_next_row()
            summary_frame.rowconfigure(b, weight=2)
            record_summary = self.view.build_record_summary(master=summary_frame, record=rec)
            record_summary.grid(row=b, column=0, sticky=tk.NSEW, pady=5)

            row = hp.get_next_row()
            summary_frame.rowconfigure(row,weight=2)
            position_summary = self.view.build_position_summary(master=summary_frame, position=handles[i])
            position_summary.grid(row=row,column=0, sticky=tk.NSEW, pady=5, ipadx=5)

    def open_examination(self):
        """Starts the GUI for the "open examination" frame."""
        self.view.build_openexam_frame(master=self.view.right_frame)
        self.view.show_menu(menu='open_examination')
        lastE_ID = self.model.t_examination.tail().index.tolist()
        self.view.lastE_IDs["text"] += '\n\n'+str(lastE_ID)
        self.view.examID_entry.bind('<Return>', func=self.start_navigation)

        if self.aua.get_sysmode() == 'SETUP':
            self.q.put(self.activateHandles)

    def start_navigation(self, event=None):
        """:param buttonevent event: Defaults to :const:`None`. Param is necessary for \<Enter\> event.

        Starts the GUI for the "navigation" frame and loads the first record as a target for navigation."""

        E_ID = str(self.view.examID_entry.get())
        if not E_ID:
            logger.error('E_ID Empty ! Please use a valid E_ID')
            return

        self.view.build_navigation_frame(master=self.view.right_frame)
        self.view.show_menu(menu='navigation')
        self.view.switch_imgsrc_but["state"] = 'disabled'
        self.view.accept_record_but["state"] = 'disabled'

        logger.info(f'Initialize frame grabber for navigation')
        self._init_framegrabber()
        self.capture_framegrabber(label=self.view.USimg_lb)
        self.view.refresh_imgsize(self.view.navgrid_frame)

        logger.info(f'Loading Examination {E_ID} for Navigation')
        self.model.load_workitem(E_ID)
        workitem = self.model.get_current_workitem()
        exam_object, records_list, positions_list = workitem.values()

        menu_list = []
        for rec in records_list:
            menu_list.append(rec.R_ID)
        self.view.set_target_menu(menu_list)

        #Loads the first record it found for the Examination
        self.set_target_from_record(record=records_list[0])

        #Recalibrate for current position difference
        logger.info("Navigation is ready. Please start Tracking and calibrating")

    def set_target_from_record(self, record=None, R_ID=None):
        """
        :param uvis_model.Record record: :class:`uvis_model.Record` object to be loaded or :const:`None`.

        :param str R_ID: R_ID like "R-0" to be loaded or :const:`None`.

        Sets the target for an navigation based on an record.
        As input it can either use the R-ID or an :class:`uvis_model.Record` Object.

        """

        if not(isinstance(record, Record)) and R_ID is not None:
            if hasattr(R_ID, '__call__'):
                R_ID = R_ID()
            record = self.model.get_record(R_ID=R_ID)
            if not record:
                raise ValueError(f'Could not find Record with R_ID {R_ID}')

        logger.info(f'Set Target from record {record.R_ID}')
        handles = self.model.get_position(record.R_ID, as_dict=True)
        logger.debug(handles)
        #Important use the dict Version of the Position / Handles
        self.calibrate_coordsys(calibrator=self.target_calibrator, handles=handles)
        self.set_target_pos(calibrator=self.target_calibrator, handles=handles)

        #Load Target Image
        filename = record.US_img
        img = self.model.get_img(filename=filename)
        self.view.refresh_img_for_lb(img=img, lb=self.view.target_img_lb)

    def nav_save_record(self):
        """The same as :func:`save_record` but for the navigation process."""
        if not self.save_record():
            logger.error("Couldn't save record. Please try again.")
            return False
        self.refresh_position_data()
        self.view.accept_record_but["state"] = 'normal'
        if self.view.USimg_frame.winfo_ismapped():
            self.view.switch_imgsrc()

    def nav_accept_record(self):
        """ Accepts the temporary record and persists it to the database.
        It also compares the records and displays statistics"""


        curr_target_R_ID = self.view.target_var.get()
        workitem = self.model.get_current_workitem()
        exam_object, records_list, positions_list = workitem.values()
        last_rec = records_list[-1]
        logger.debug(f"Last Record is {last_rec.R_ID}")
        try:
            new_R_ID = self.model.save_record(last_rec, persistant=True)
            self.view.accept_record_but["state"] = 'disabled'
        except ValueError as e:
            logger.error(f"Couldn't persist {last_rec.R_ID}. Please try again!")
            return False

        # remove all temp records from E_ID or rather the whole dataset
        self.model.clear_temp_data()

        self.model.load_workitem(exam_object.E_ID)

        a = self.model.get_current_workitem()

        logger.info(f"Compare Current: {curr_target_R_ID} with new R_ID: {new_R_ID}")

        target_record = self.model.get_record(R_ID=curr_target_R_ID)
        nav_record = self.model.get_record(R_ID=new_R_ID)

        try:
            self.model.compare_records(target_record, nav_record)
            df = self.model.t_comparison
            self.view.set_statistics_table(df)
        except ValueError as e:
            logger.error(f"Couldn't compare data. Please try again!")

    def clean_navigation(self):
        """TODO"""

        # Removes records made during comparing, will all be deleted
        # when cancel is triggered.

        # also remove the comparison values for the E_ID !
        pass

    def open_evaluation(self):
        """Starts the GUI for the "open evaluation" frame"""
        self.view.build_openeval_frame(master=self.view.right_frame)
        self.view.show_menu(menu='open_evaluation')
        self.view.load_eval_but["command"] = self.evaluate_examination
        eval_list = self.model.t_comparison['E_ID'].unique()
        self.view.set_eval_menu(eval_list)

    def evaluate_examination(self):
        """Starts the GUI for the "evaluate examination" frame"""
        # Zeige die Tabelle mit den Daten
        # Gebe neben den einzelnen Werte, auch die Gesamtergebnisse zurück.
        self.view.build_evaluation_frame(master=self.view.right_frame)
        self.view.show_menu(menu='evaluate_examination')

        E_ID = self.view.eval_opts_var.get()
        comp_df = self.model.get_comparison(Eval_ID=E_ID)
        self.view.set_statistics_table(comp_df)

        if not E_ID in self.model.t_evaluation.index:
            self.model.evaluate_comparison_data(df=comp_df)
            eval_df = self.model.t_evaluation.loc[E_ID]
        else:
            eval_df = self.model.t_evaluation.loc[E_ID]

        # Tabelle Darstellen mit Ergebnissen

        print("Donus")


    def init_button_func(self):
        """Sets for all buttons the functionality.
        The buttons are defined in :func:`UltraVisView.build_menu_frame`."""
        self.view.new_exam_but["command"] = self.new_examination
        self.view.open_exam_but["command"] = self.open_examination
        self.view.open_eval_but["command"] = self.open_evaluation

        self.view.new_exam_but["command"] = self.new_examination

        self.view.start_exam_but["command"] = self.start_examination
        self.view.activate_handle_but["command"] =lambda: self.q.put(self.activateHandles)

        self.view.save_record_but["command"] = lambda: self.q.put(self.save_record)
        self.view.track_but["command"] = lambda: self.q.put(self.startstopTracking)
        self.view.finish_exam_but["command"] = lambda: self.q.put(self.finalize_examination)

        self.view.mainmenu_but["command"] = self.cancel_examination

        self.view.start_navigation_but["command"] = self.start_navigation
        self.view.calibrate_but["command"] = self.calibrate_coordsys
        self.view.target_but["command"] = partial(self.set_target_from_record, R_ID=self.view.target_var.get)
        self.view.switch_imgsrc_but["command"] = self.view.switch_imgsrc
        self.view.nav_save_record_but["command"] = lambda: self.q.put(self.nav_save_record)
        self.view.accept_record_but["command"] = lambda: self.q.put(self.nav_accept_record)

        self.view.cancel_but["command"] = self.cancel_examination

        self.view.NOBUTTONSYET["command"] = self._debugfunc
        #lambda: print("NO FUNCTIONALITY YET BUT I'LL GET U soon :3 <3")

    def addSetupHandlesFunc(self):
        """Sets the button functionality for the setuphandles frame."""
        frames = self.view.setuphandle_frames
        #Partial muss genutzt werden, weil der Parameter hochgezählt wird.
        for i,frame_data in enumerate(frames):
            #frame,handlename,ref_entry,button,valid = frame_data.values()
            button = frame_data["button"]
            button["command"] = partial(self.validate_setuphandles, handle_index=i)

    def refresh_sysmode(self):
        """Displays the current Operating mode of the NDI Aurora System. Modes are 'Setup' and 'Tracking'.
        For more details please read the official NDI Aurora API Guide."""
        if (hasattr(self.view,'sysmode_lb')):
            mode = self.aua.get_sysmode()
            color = 'black'
            if (mode == 'SETUP'):
                color = 'FloralWhite'
            elif (mode == 'TRACKING'):
                color = 'SpringGreen'
            self.view.sysmode_lb.configure(
                text="Operating Mode: "+str(mode),
                bg=color)
        else:
            self.view.right_frame.after(2000,self.refresh_sysmode)

    # TODO not finished
    def refreshWorkItem(self):

        infotext = f'Current Workitem\n'

        workitem = self.model.get_current_workitem()

        exam,records,handles = workitem.values()
        infotext += f'\nExamination-ID: {exam.E_ID}\n{exam.__dict__}\n'


        for i, rec in enumerate(records):
            infotext +=f'\nRecord-ID: {rec.R_ID}\n{rec.__dict__}\n'

            try:
                position = handles[i]
                infotext +=f'\nPositiondata {i}\n'
                for h in position:
                    infotext += f'Handle {h.ID}-{h.refname}: {h.__dict__}\n'
            except IndexError as e:
                continue

        #self.view.workitemdataLabel["text"] = infotext

    def _debugfunc(self):
        """Internal method for testing all kinds of code"""
        self.view.build_examination_frame(master=self.view.right_frame)
        self.view.show_menu(menu='examination')

    # Data Auswertung
    # Needs better integration into the application
    def _do_data_evaluation(self):
        """Evaluates the current Ground Truth datasets and display the boxplots."""
        df0 = self.model.hb_records #human layman
        df1 = self.model.heb_records # human expert
        base = self.model.calculate_baseline() # system base accuracy
        base_human_laie = self.model.calculate_baseline(df0)
        base_human_expert = self.model.calculate_baseline(df1)

        arrow = list(zip_longest(base, base_human_laie, base_human_expert))
        columns = ["G_0 System Error", "G_1 Human Error Layman", "G_1 Human Error Expert"]
        self.model.display_boxplot(arrow, columns)



    #---- Debugging Related. ----#
    def writeCmd2AUA(self, event):
        """Writes a serial Command to the NDI Aurora System"""
        try:
            command = self.view.cmdEntry.get()
            self.aua.readsleep = float(self.view.sleeptimeEntry.get())
            if (len(self.view.expec.get())==0):
                a = False
            else:
                a = self.view.expec.get()

            logger.debug("Execute command: "+command)
            self.aua.write_cmd(command,expect=a)
            self.view.cmdEntry.delete(0, 'end')

        except Warning as e:
            logger.exception("An FATAL occured: "+str(e))

    def testFunction(self):
        """Tests a function for the debugging GUI"""
        with self.aua._lock:
            self.aua.beep(2)

    def addFuncDebug(self):
        """Adds the button functionality for the debugging GUI"""
        #Menu
        #self.view.initBut["command"] = self.beep
        self.view.readBut["command"] = self.aua.read_serial
        self.view.resetBut["command"] = self.aua.reset_and_init_system
        self.view.testBut["command"] = self.testFunction
        self.view.handleBut["command"] = self.activateHandles
        #self.view.restartBut["command"] = self.restart
        self.view.quitBut["command"] = self.root.destroy


        #DebugCMD
        self.view.cmdEntry.bind('<Return>', func=self.writeCmd2AUA)
        self.view.sleeptimeEntry.bind('<Return>', func=self.writeCmd2AUA)
        self.view.expec.bind('<Return>', func=self.writeCmd2AUA)
