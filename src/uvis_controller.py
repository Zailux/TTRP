"""This is the Uvis Controller module.

This module does stuff.
"""

import logging
import queue
import random
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from functools import partial, wraps

import matplotlib.animation
import matplotlib.pyplot as plt
import pandas as pd
import serial
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image

#sys.path.insert(1, '..\\')
from src.aurora import Aurora, Handle, HandleManager
from src.config import Configuration
from src.helper import Helper
from src.uvis_model import Examination, Record, UltraVisModel
from src.uvis_view import UltraVisView
from src.Calibrator import Calibrator

global hp
global _cfg
hp = Helper()
_cfg = Configuration()


SUM_MAXHEIGHT = 4
SUM_TITLE_PADY = 5

class UltraVisController:

    def __init__(self, debug_mode=False):

        #Create Model and View
        self.root = tk.Tk()

        self.calibrator = Calibrator()

        self.model = UltraVisModel()
        self.view = UltraVisView(self.root,debug_mode=debug_mode)

        #Controller Attributes
        self._debug = debug_mode
        self.hm = None
        self.aua = None

        self.__initObservers()
        self.__initBackgroundQueue()

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
        self.initAurora(self.ser)
        self.initFunctionality()
        self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)


    #Closing Method and bind to root Window
    def __on_closing(self):

        if (hasattr(self.view,'appFrame')):
             #Close FrameGrabber
            self.view.USImgLabel.after_cancel(self.view._FrameGrabberJob)
            self.view.cap.release()

            #Close Tracking + Matplotanimation
            if (self.aua_active):
                if(self.aua.get_sysmode()=='TRACKING'):
                    self.stopTracking = True
                    self.view.navCanvas._tkcanvas.after_cancel(self.view._Canvasjob)
                    with self.aua._lock:
                        self.aua.tstop()


        self.quitEvent.set()
        self.ser.close()

        #Bug that plt.close also closes the TKinter Windows!
        if (hasattr(self.view,'fig')):
            plt.close(fig=self.view.fig)
        logging.info("Good Night Cruel World :D")
        self.root.quit()
        self.root.destroy()

    def run (self):
        self.root.mainloop()

    def __initBackgroundQueue(self):
        self.q = queue.Queue(maxsize=8)
        self.quitEvent = threading.Event()
        def processQueue(self):
            logging.info("Initialize Queue")
            x = 0
            while (not self.quitEvent.is_set() or not self.q.empty()):

                if (self.q.empty()):
                    if (x%5==0):
                        logging.debug("Waiting for Event")
                    x += 1
                    time.sleep(1.5)
                    continue

                func = self.q.get()
                thread = threading.Thread(target=func)

                logging.info(f"Start {thread.getName()}: process {func.__name__}()")
                time.sleep(0.25)
                thread.start()
                thread.join()
                self.q.task_done()
                logging.info(thread.getName()+" is finished - Alive: "+str(thread.is_alive()))
                logging.debug(f'Current pipeline: {self.q.qsize()} items')

            logging.info("Queue is closed")

        q_Thread = threading.Thread(target=processQueue,daemon=True,args=(self,),name="Q-Thread")
        q_Thread.start()

    def __initObservers(self):

        self.model.register(key="set_current_workitem",observer=self.refreshWorkItem)



    def initAurora(self,ser):

        logging.info("Initialize Aurorasystem - Try connecting to Aurorasystem")



        widgets = self.view.menuFrame.winfo_children()
        self.aua_active = False
        try:
            self.aua = Aurora(ser)

        except serial.SerialException as e:
            logging.warning("serial.SerialException: "+str(e))
            #self.disableWidgets(widgets)
            self.view.reinitAuaBut.pack(side=tk.TOP, pady=(0, 0),padx=(10), fill="both")
            self.view.reinitAuaBut["state"] = 'normal'
            self.view.reinitAuaBut["command"] = lambda: self.initAurora(self.ser)
            return
        except Warning as w:
            logging.exception(str(w))
            #self.disableWidgets(widgets)
            self.view.reinitAuaBut.pack(side=tk.TOP, pady=(0, 0),padx=(10), fill="both")
            self.view.reinitAuaBut["state"] = 'normal'
            self.view.reinitAuaBut["command"] = lambda: self.initAurora(self.ser)
            return

        self.aua_active = True
        logging.info("Connection success")
        self.aua.register("set_sysmode",self.refreshSysmode)
        self.enableWidgets(widgets)
        self.view.reinitAuaBut.grid_forget()

        logging.info("Reset Aurorasystem")
        self.aua.reset_and_init_system()

        self.addFuncDebug()

        logging.info("Initialize Aurorasystem - done")




    #   -----Aurora Setup Functionality  ------#

    def activateHandles(self):
        # todo Gesamtprozess nach Guide (siehe Aurora API)
        logging.info("Activate Handles - Acquiring Lock")

        success = True
        with self.aua._lock:
            try:
                logging.info("All allocated Ports")
                phsr_string = self.aua.phsr()

                self.hm = HandleManager(phsr_string)
                handles = self.hm.get_handles()

                # print("handles 02")
                # Occupied handles but not initialized or enabled
                # self.aua.phsr(2)

                # Alle Port-Handles Initialisieren
                # Alle Port-Hanldes aktivieren
                logging.info(str(self.hm.get_numhandles())+" Handles identified")
                logging.info("Initializing Port-Handles")


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
                logging.warning(str(w))
                success=False
                #maybe solve via states in show menu Later
                self.view.activateHandleBut.pack(side=tk.TOP, pady=(0, 0),padx=(10), fill="both")

        logging.info("Activate Handles - finished with NO_ERRORS" if success else "Activate Handles - finished with ERRORS")


    #---- App Frame functionality tracking and saving----#

    def startstopTracking(self):
        #Bug self.aua can't deal with concurrent calls !


        if (self.aua.get_sysmode()=='SETUP'):
            with self.aua._lock:
                self.aua.tstart(40)

            #Thread starte Thread und gebe den AppFrame GUI die Daten
            self.stopTracking = False
            self.tracking_Thread = threading.Thread(target=self.trackHandles,daemon=True,name="tracking_Thread")
            self.tracking_Thread.start()
            self.view._Canvasjob = self.view.navCanvas._tkcanvas.after(2000,func=self.view.build_coordinatesystem)


        elif(self.aua.get_sysmode()=='TRACKING'):
            self.stopTracking = True
            self.view.navCanvas._tkcanvas.after_cancel(self.view._Canvasjob)
            self.tracking_Thread.join()

            with self.aua._lock:
                self.aua.tstop()

    def trackHandles(self):

        #Stop as soon the event is set
        #Verringern der Update Data frequenz

        logging.info(threading.current_thread().name+" has started tracking")

        freq = 0.01
        while(not self.stopTracking):
            t0 = datetime.now()
            with self.aua._lock:
                #NEEDS TO BE FIXED
                bx = True
                if bx:
                    header, data = self.aua.bx()
                    if self.hm.updateHandlesBX(header, data):
                        self.setNavCanvasData()
                else:
                    tx = self.aua.tx()
                    self.hm.updateHandles(tx)
                    self.setNavCanvasData()
            time.sleep(freq)

            t1 = datetime.now()
            #print (t1-t0)

        self.stopTracking = False
        logging.info(threading.current_thread().name+" has stopped!")

    def setNavCanvasData(self):
        x,y,z,a,b,c = [],[],[],[],[],[]
        av_color = ['yellow','red','green','blue']
        color = []
        num_handle = self.hm.get_numhandles()
        if (num_handle is not 4):
            logging.warning(f'There are {num_handle} handles identified. Is that correct?')
            color = color[:num_handle]

        handles = self.hm.get_handles()
        #Might change for Items, if the specific request of handle object is neccessary.

        for i,handle in enumerate(handles.values()):
            if (handle.MISSING is None):
                print("asdfasdfadfs")
                break

            if (handle.MISSING is False):
                # TODO only for uvis sensor
                if (i == 0):
                    transformed = self.calibrator.transform_backward([handle.Tx, handle.Ty, handle.Tz])
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

        logging.debug(f'x values: {x}')

        self.view.navCanvasData = (x,y,z,a,b,c,color)

    #Position is saving Record and Handles
    def saveRecord(self):
        if (not self.aua.get_sysmode()=='TRACKING'):
            logging.info("This functionality is only available during tracking. Please Start Tracking")
            return

        self.view.saveUSImg()
        img = self.view.savedImg.copy()
        img = img.resize(self.view.og_imgsize, Image.ANTIALIAS)

        dt = datetime.now()
        tmpstamp = dt.strftime("%a, %d-%b-%Y (%H:%M:%S)")

        # Description atrtibute, aus der GUI
        # Gets Current Workitem and accesses its Examination
        workitem = self.model.get_current_workitem()
        E_ID = workitem["Examination"].E_ID
        rec = Record(date=tmpstamp,E_ID=E_ID)
        img_name = f'{rec.R_ID[4:]}_img'
        handles = self.hm.get_handles(real_copy=True)


        if (self.validatePosition(handles)):

            #try saving image and the record
            try:
                path = self.model.save_PIL_image(img=img,img_name=img_name)
                rec.US_img=path
                self.model.save_record(record=rec)
            except IOError as e:
                raise Warning("Error during saving the image. \nErrorMessage:"+str(e))
            except ValueError as e:
                #Konnte Aufzeichnung nicht speichern. Please try again with SAME DATA!
                return

            #try saving corresponding Position
            try:
                self.model.save_position(R_ID=rec.R_ID, handles=handles)
            except ValueError as e:
                #Konnte handles nicht speichern. Please try again with SAME DATA?!
                pass

            self.model.set_current_workitem(rec)
            self.model.set_current_workitem(handles.values())

    def validatePosition(self, handles):
        #Validate Handles for saving
        #Check for Missing Handles, check for correct frameID
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
            logging.error("Trying to save Position with missing Handles: "+str(missID)+". Please use valid Data")

        return validSave


    #----GUI Related ----#

    def new_examination(self):
        self.view.build_newExam_frame(master=self.view.rightFrame)
        self.view.show_menu(menu='new_examination')
        self.view.continueBut["command"] = self.setup_handles

    def validate_new_examination(self):
        #if there is future validation necessary e.g. Patient data is required, you need to implement it here
        doctor = self.view.doctorEntry.get()
        patient = self.view.patientEntry.get()
        examitem = self.view.examItemTextbox.get("1.0",'end-1c')
        created = self.view.createdEntry.get()

        params = {"E_ID" :None, "doctor":doctor, "patient":patient, "examitem":examitem, "created":created}
        new_exam = Examination(**params)
        logging.debug(f'Exam Data - {new_exam}')

        #Due to no validation as of now,
        validExam = True

        return validExam,new_exam

    def setup_handles(self):

        #save exam procudere should be actually somewhere else ...
        validExam,new_exam = self.validate_new_examination()
        if (validExam):
            try:
                self.model.save_examination(examination=new_exam)
                self.model.set_current_workitem(obj=new_exam)
            except ValueError as e:
                msg = "Could not save Examination. See logs for details."
                self.view.setInfoMessage(msg)
                return
        else:
            logging.error(f'Invalid Examinationdata')
            return

        self.view.build_setup_frame(master=self.view.rightFrame)
        self.view.show_menu(menu='setup')
        self.addSetupHandlesFunc()

        #load Menu but still disabled.
        if (self.aua_active):
            self.q.put(self.activateHandles)



        #wenn sucessfull dann enable button. Und hole dir Handledaten
        #Else zeige zurückbutton und läd den Basescreen again.

    def validate_setuphandles(self,handle_index=None):

        last_index = self.hm.get_numhandles() - 1 if self.hm is not None else 3
        setuphandles = self.view.setupHandleFrames
        isValid = None
        #Check all handles and start next App part
        if handle_index is None:

            valid_list = []
            for setuphandle in setuphandles:
                valid_list.append(setuphandle['valid'])

            if False in valid_list:
                self.view.set_setup_instruction("Sie müssen zuerst alle Spulen anschließen bevor Sie Untersuchung beginnen können")
                logging.info(f"Invalid Setuphandles. See List: {valid_list}")
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
                self.view.instructionLabel["bg"] = "SpringGreen"
                self.view.set_setup_instruction("Einrichtung der Spulen abgeschlossen. Sie können mit der Untersuchung beginnen :)")
                setuphandle["frame"]["bg"] = 'white'
                children = setuphandle["frame"].winfo_children()
                hp.disableWidgets(children,disable_all=True)
                isValid = True
                return isValid
        else:
            raise ValueError(f"Invalid Handle_index: {handle_index}.")

    def start_examination(self):
        is_valid_setuphandles = self.validate_setuphandles()
        if (is_valid_setuphandles):
            handles = self.hm.get_handles().values()
            setuphandles =self.view.setupHandleFrames
            for i,pair in enumerate(zip(handles,setuphandles)):
                handle,setuphandle = pair
                entry = setuphandle["ref_entry"]
                refname = entry.get()
                handle.setReferenceName(refname)

            self.view.build_app_frame(master=self.view.rightFrame)
            self.view.show_menu(menu='app')
            self.view.continueBut = self.finalize_examination
        else:
            return


    def setTargetPos(self,handles=None):
        logging.info("Set Target Position")
        pos = [0.0, 0.0, 0.0]

        num_handle = self.hm.getNum_Handles()
        if (num_handle is not 4):
            logging.warning(f'There are {num_handle} handles identified. Is that correct?')
        else:
            handles = self.hm.getHandles() if not handles else handles
            current_pos = [handles['0A'].Tx, handles['0A'].Ty, handles['0A'].Tz]
            #current_ori = self.calibrator.quaternion_to_rotation_matrix(handles['0A'].Q0, handles['0A'].Qx, handles['0A'].Qy, handles['0A'].Qz)
            #print(current_ori)

            a, b, c = self.calibrator.quaternion_to_rotations(handles['0A'].Q0, handles['0A'].Qx, handles['0A'].Qy, handles['0A'].Qz)

            pos = self.calibrator.transform_backward(current_pos)

            self.view.navigationvis.set_target_pos(pos[0], pos[1])
            self.view.navigationvis.set_target_ori(a, b, c)


    def calibrate_coordsys(self,handles = None):
        logging.info("Calibrate Coordination System")

        handles = self.hm.getHandles() if not handles else handles

        num_handle = self.hm.getNum_Handles()
        if (num_handle != 4):
            logging.warning(f'There are {num_handle} handles identified. Need 4 to calibrate!')
        else:
            a = [handles['0B'].Tx, handles['0B'].Ty, handles['0B'].Tz] # becken rechts
            b = [handles['0C'].Tx, handles['0C'].Ty, handles['0C'].Tz] # becken links
            c = [handles['0D'].Tx, handles['0D'].Ty, handles['0D'].Tz] # brustbein

            self.calibrator.set_trafo_matrix(a,b,c)


    #Muss Logik einbauen, dass das System dabei auch resettet wird &
    # das GUI etc. korrekt gestoppt wird
    def cancel_examination(self, save=False):
        self.view.build_mainscreen_frame(master=self.view.rightFrame)
        self.view.show_menu()

    def validate_examination(self):
        isValid = None

        workitem = self.model.get_current_workitem()
        if not workitem["Records"]:
            isValid = False
        elif False:
            #another Validation
            pass

        if (isValid is None):
            isValid = True

        return isValid

    def finalize_examination(self):
        isValidExam = self.validate_examination()
        if (isValidExam):

            try:
                new_E_ID = self.model.persist_workitem()
            except ValueError as e:
                msg = "Could not save Examination. See logs for details."
                self.view.setInfoMessage(msg)
                logging.error(str(e))
                return

            self.model.load_workitem(new_E_ID)
            self.view.build_summary_frame(master=self.view.rightFrame)
            self.view.show_menu(menu='summary')
            self.build_summary()

            # TODO THAT!
            if self.aua.getSysmode() == "TRACKING":
                self.q.put(self.startstopTracking)
                #ggf. rauskomment

        else:
            msg = f'Can\'t finish Examination, without any Records. Please create Records first.'
            logging.info(msg)
            print(msg)
            self.view.setInfoMessage(msg=msg,type='ERROR')
            return

    def build_summary(self):

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


    def _debugfunc(self):
        self.model.load_workitem('E-2')
        self.view.build_summary_frame(master=self.view.rightFrame)
        self.view.show_menu(menu='summary')
        self.build_summary()






    def openExamination(self):
        self.view.buildOpenExamFrame(master=self.view.rightFrame)
        self.view.showMenu(menu='open_examination')
        lastE_ID = self.model.t_examination.tail().index.tolist()
        self.view.lastE_IDs["text"] += '\n\n'+str(lastE_ID)
        self.view.examID_entry.bind('<Return>', func=self.startNavigation)

        if self.aua.getSysmode() == 'SETUP':
            self.q.put(self.activateHandles)

    # TODO wurde für präsentation mal erstellt, soltle aber nochmal überarbeitet und
    # dokumentiert werden.
    def startNavigation(self,event=None):
        E_ID = str(self.view.examID_entry.get())

        if not E_ID:
            logging.info('E_ID Empty ! Please give correct input')
            return

        self.view.buildNavigationFrame(master=self.view.rightFrame)
        self.view.showMenu(menu='navigation')

        logging.info(f'Loading Examination {E_ID} for Navigation')
        self.model.loadWorkitem(E_ID)

        workitem = self.model.get_current_workitem()

        exam_object, records_list, positions_list = workitem.values()

        #Loads first Position
        R_ID = records_list[0].R_ID
        pos = self.model.getPosition(R_ID,as_dict=True)
        logging.debug(pos)
        self.loadPositiontoNavigation(position=pos)

        #Recalibrate for current position difference

        logging.info("Navigation is ready. Please start Tracking and calibrating")




    def loadPositiontoNavigation(self,position):
        #Important use the dict Version of the Position
        logging.debug("Calibrate and transform data before saving")
        self.calibrate_coordsys(handles=position)
        self.setTargetPos(handles=position)

    def initFunctionality(self):

        self.view.newExamiBut["command"] = self.newExamination
        self.view.openExamiBut["command"] = self.openExamination

        self.view.newExamiBut["command"] = self.new_examination

        self.view.startExamiBut["command"] = self.start_examination
        self.view.activateHandleBut["command"] =lambda: self.q.put(self.activateHandles)

        self.view.saveRecordBut["command"] = lambda: self.q.put(self.saveRecord)
        self.view.trackBut["command"] = lambda: self.q.put(self.startstopTracking)
        self.view.finishExamiBut["command"] = self.finalize_examination

        self.view.mainMenuBut["command"] = self.cancelExamination

        self.view.startNaviBut["command"] = self.startNavigation
        self.view.calibrateBut["command"] = self.calibrate_coordsys
        self.view.targetBut["command"] = self.setTargetPos

        self.view.cancelBut["command"] = self.cancelExamination

        self.view.NOBUTTONSYET["command"] = self._debugfunc
        #lambda: print("NO FUNCTIONALITY YET BUT I'LL GET U soon :3 <3")


    def addSetupHandlesFunc(self):

        frames = self.view.setupHandleFrames
        #Partial muss genutzt werden, weil der Parameter hochgezählt wird.
        for i,frame_data in enumerate(frames):
            #frame,handlename,ref_entry,button,valid = frame_data.values()
            button = frame_data["button"]
            button["command"] = partial(self.validate_setuphandles, handle_index=i)


    def _debugfunc(self):
        self.model.loadWorkitem('E-2')
        self.view.buildSummaryFrame(master=self.view.rightFrame)
        self.view.showMenu(menu='summary')
        self.buildSummaryContent()

    #----Debugging Related ----#
    def writeCmd2AUA(self,event):

        try:
            command = self.view.cmdEntry.get()
            self.aua.readsleep = float(self.view.sleeptimeEntry.get())
            if (len(self.view.expec.get())==0):
                a = False
            else:
                a = self.view.expec.get()

            logging.debug("Execute command: "+command)
            self.aua.write_cmd(command,expect=a)
            self.view.cmdEntry.delete(0, 'end')

        except Warning as e:
            logging.exception("An FATAL occured: "+str(e))

    def testFunction(self):
        with self.aua._lock:
            self.aua.beep(2)


    def addFuncDebug(self):
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





    def enableWidgets(self,childList):
        for child in childList:
            if (child.winfo_class() == 'Frame'):
                self.enableWidgets(child.winfo_children())
                continue

            if (child.winfo_class() in ['Button','Entry']):
                child.configure(state='normal')

    def disableWidgets(self,childList):
        for child in childList:
            if (child.winfo_class() == 'Frame'):
                self.disableWidgets(child.winfo_children())
                continue

            if (child.winfo_class() in ['Button','Entry']):
                child.configure(state='disabled')





    def refreshSysmode(self):
        if (hasattr(self.view,'sysmodeLabel')):
            mode = self.aua.getSysmode()
            self.view.sysmodeLabel["text"] = "Operating Mode: "+str(mode)
        else:
            self.view.rightFrame.after(2000,self.refreshSysmode)

    # TODO WIP
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
