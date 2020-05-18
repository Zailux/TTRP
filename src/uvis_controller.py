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


global hp
global _cfg
hp = Helper()
_cfg = Configuration()


class UltraVisController:

    def __init__(self,debug_mode=False):
        
        #Logging Configuration
        #format = "%(asctime)s - %(threadName)s|%(levelname)s: %(message)s"
        #logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
        self._Logger = _cfg.LOGGER
        #self._Logger.setLevel(logging.DEBUG)

        #Create Model and View
        self.root = tk.Tk()
       
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

            while (not self.quitEvent.is_set() or not self.q.empty()):
                if (self.q.empty()):
                    logging.debug("Waiting for Event")
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
                handles = self.hm.getHandles()

                # print("handles 02")
                # Occupied handles but not initialized or enabled
                # self.aua.phsr(2)

                # Alle Port-Handles Initialisieren
                # Alle Port-Hanldes aktivieren
                logging.info(str(self.hm.getNum_Handles())+" Handles identified")
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
            self.view._Canvasjob = self.view.navCanvas._tkcanvas.after(1500,func=self.view.buildCoordinatesystem)
            

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
       
        freq = 0.5
        while(not self.stopTracking):

            with self.aua._lock:
                tx = self.aua.tx()
                self.hm.updateHandles(tx)
                self.setNavCanvasData()
            time.sleep(freq)

        self.stopTracking = False
        logging.info(threading.current_thread().name+" has stopped!")

    def setNavCanvasData(self):
        x,y,z = [],[],[]
        av_color = ['yellow','red','green','blue']
        color = []
        num_handle = self.hm.getNum_Handles()
        if (num_handle is not 4):
            logging.warning(f'There are {num_handle} handles identified. Is that correct?')        
            color = color[:num_handle]
        
        handles = self.hm.getHandles()
        #Might change for Items, if the specific request of handle object is neccessary.
        
        for i,handle in enumerate(handles.values()):
            if (handle.MISSING is None):
                break

            if (handle.MISSING is False):
                x.append(handle.Tx)
                y.append(handle.Ty)
                z.append(handle.Tz)
                color.append(av_color[i])
            
                
    
            
        logging.debug(f'x values: {x}')
        
        self.view.navCanvasData = (x,y,z,color)
    
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
        handles = self.hm.getHandles(real_copy=True)

        if (self.validatePosition(handles)):
            
            #try saving image and the record
            try:
                path = self.model.savePILImage(img=img,img_name=img_name)
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



    def newExamination(self):
        self.view.buildNewExamFrame(master=self.view.rightFrame)
        self.view.showMenu(menu='new_examination')
        self.view.continueBut["command"] = self.setupHandles
    

    def validateNewExamination(self):
        #if there is future validation necessary e.g. Patient data is required, you need to implement it here
        doctor = self.view.doctorEntry.get()
        patient = self.view.patientEntry.get()
        examitem = self.view.examItemTextbox.get("1.0",'end-1c')
        created = self.view.createdEntry.get()

        params = {"E_ID" :None, "doctor":doctor, "patient":patient, "examitem":examitem,"created":created}
        new_exam = Examination(**params)
        logging.debug(f'Exam Data - {new_exam}')

        #Due to no validation as of now, 
        validExam = True 
        
        return validExam,new_exam
            
    
    def setupHandles(self):
        
        #save exam procudere should be actually somewhere else ...
        validExam,new_exam = self.validateNewExamination()
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
        
        self.view.buildSetupFrame(master=self.view.rightFrame)
        self.view.showMenu(menu='setup')
        self.addSetupHandlesFunc()
        
        #load Menu but still disabled. 
        if (self.aua_active):
            self.q.put(self.activateHandles)

        

        #wenn sucessfull dann enable button. Und hole dir Handledaten
        #Else zeige zurückbutton und läd den Basescreen again. 


    def validateSetupHandles(self,handle_index=None):
        
        last_index = self.hm.getNum_Handles() - 1 if self.hm is not None else 3
        setuphandles = self.view.setupHandleFrames
        isValid = None
        #Check all handles and start next App part
        if handle_index is None:
            
            valid_list = [] 
            for setuphandle in setuphandles:
                valid_list.append(setuphandle['valid'])
            
            if False in valid_list:
                self.view.setSetupInstruction("Sie müssen zuerst alle Spulen anschließen bevor Sie Untersuchung beginnen können")
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
                self.view.setSetupInstruction("Bitte tragen Sie einen Referenznamen für die Spule ein")
                isValid = False
                return isValid

            if (handle_index != last_index):
                self.view.setCurrentSetupHandle(handle_index+1)
            else:
                self.view.instructionLabel["bg"] = "SpringGreen"
                self.view.setSetupInstruction("Einrichtung der Spulen abgeschlossen. Sie können mit der Untersuchung beginnen :)")
                setuphandle["frame"]["bg"] = 'white'
                children = setuphandle["frame"].winfo_children()
                hp.disableWidgets(children,disable_all=True)
                isValid = True
                return isValid
        else:
            raise ValueError(f"Invalid Handle_index: {handle_index}.")


    def startExamination(self):
        valid_setupHandles = self.validateSetupHandles()
        if (valid_setupHandles == False):
            return
        else:
            handles = self.hm.getHandles().values()
            setuphandles =self.view.setupHandleFrames
            for i,pair in enumerate(zip(handles,setuphandles)):
                handle,setuphandle = pair
                entry = setuphandle["ref_entry"]
                refname = entry.get()
                handle.setReferenceName(refname)

            self.view.buildAppFrame(master=self.view.rightFrame)
            self.view.showMenu(menu='app')
            self.view.continueBut = self.finalizeExamination


    #Muss Logik einbauen, dass das System dabei auch resettet wird &
    # das GUI etc. korrekt gestoppt wird   
    def cancelExamination(self,save=False):
        self.view.buildMainScreenFrame(master=self.view.rightFrame)
        self.view.showMenu()


    def validateExamination(self):
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

    def finalizeExamination(self):
        isValidExam = self.validateExamination()
        if (isValidExam):

            try:
                new_E_ID = self.model.persist_workitem()
            except ValueError as e:
                msg = "Could not save Examination. See logs for details."
                self.view.setInfoMessage(msg)
                logging.error(str(e))
                return

            self.model.load_workitem(new_E_ID)
            self.view.buildSummaryFrame(master=self.view.rightFrame)
            self.view.showMenu(menu='summary')

            frame = self.view.sumContentFrame
            
            self.view.sumContentlb["text"] = self.view.workitemdataLabel["text"]



        else:
            msg = f'Can\'t finish Examination, without any Records. Please create Records first.'
            logging.info(msg)
            self.view.setInfoMessage(msg=msg,type='ERROR')
            return
        
    #needs further rework.
    def buildSummaryContent(self):      
        
        itemcount = self.model.get_length_workitem()
        exam, records, handles = self.model.get_current_workitem().values()
        sumFrame = self.view.sumContentFrame
        sumFrame.columnconfigure(0,weight=1)
        hp.setRow(0)
        r = hp.getnextRow()
        self.buildSumExam(master=sumFrame,row_index=r,exam=exam)


        for i,rec in enumerate(records):
            row = hp.getnextRow()
            self.buildSumRecord(master=sumFrame,row_index=row,record=rec)

            row = hp.getnextRow()
            self.buildSumPosition(master=sumFrame,row_index=row,position=handles[i])


    def buildSumExam(self,master,row_index,exam):
        master.rowconfigure(row_index,weight=2,uniform=1)

        examFrame = tk.Frame(master,bg ='blue')
        examFrame.columnconfigure(0, weight=1,uniform=1)
        examFrame.columnconfigure(1, weight=2,uniform=1)
        examFrame.columnconfigure(2, weight=1,uniform=1)
        examFrame.columnconfigure(3, weight=2,uniform=1)
        examFrame.columnconfigure(4, weight=1,uniform=1)
        examFrame.columnconfigure(5, weight=2,uniform=1)
        examFrame.rowconfigure(0,weight=1,uniform=2)

        exam_title = tk.Label(examFrame,text=f'Examination - {exam.E_ID}')
        exam_title.grid(row=0,column=0,columnspan=6,sticky=tk.EW)

    
        row_i = 1
        column_i = 0

        examFrame.rowconfigure(row_i, weight=1,uniform=2)
        #Display Examination Value
        for item_index, pair in enumerate(exam.__dict__.items(),start=1):
            key,value = pair
            if item_index % 3  == 0:
                row_i += 1
                column_i = 0
                examFrame.rowconfigure(row_i, weight=1,uniform=2)
            
            lb_key = tk.Label(examFrame,text=str(key),bd=1)
            ref_value = hp.getReadOnlyWidget(master=examFrame,value=value,max_length=28)
    
            lb_key.grid(row=row_i,column=column_i,sticky=tk.EW)
            ref_value.grid(row=row_i,column=column_i+1,sticky=tk.EW)
            column_i += 2

        examFrame.grid(row=row_index,column=0,sticky=tk.NSEW,pady=5)

    def buildSumRecord(self,master,row_index,record):

        master.rowconfigure(row_index,weight=2,uniform=1)

        recordsFrame = tk.Frame(master,bg ='red')
        recordsFrame.columnconfigure(0, weight=1,uniform=1)
        recordsFrame.columnconfigure(1, weight=2,uniform=1)
        recordsFrame.columnconfigure(2, weight=1,uniform=1)
        recordsFrame.columnconfigure(3, weight=2,uniform=1)
        recordsFrame.columnconfigure(4, weight=1,uniform=1)
        recordsFrame.columnconfigure(5, weight=2,uniform=1)
        recordsFrame.rowconfigure(0,weight=1,uniform=1)

        r = record.__dict__
        rec_title = tk.Label(recordsFrame,text=f'Record - {record.R_ID}')
        rec_title.grid(row=0,column=0,columnspan=6,sticky=tk.NSEW)
        
        row_i = 1
        column_i = 0

        recordsFrame.rowconfigure(row_i, weight=1,uniform=1)
        #Display Examination Value
        for item_index,pair in enumerate(r.items(),start=1):
            key,value = pair
            if item_index % 3  == 0:
                row_i += 1
                column_i = 0
                recordsFrame.rowconfigure(row_i, weight=1,uniform=1)
            
            lb_key = tk.Label(recordsFrame,text=str(key),bd=1)
            ref_value = hp.getReadOnlyWidget(master=recordsFrame,value=value,max_length=28)
    
            lb_key.grid(row=row_i,column=column_i,sticky=tk.EW)
            ref_value.grid(row=row_i,column=column_i+1,sticky=tk.EW)
            column_i += 2

        recordsFrame.grid(row=row_index,column=0,sticky=tk.NSEW,pady=5)
        
    def buildSumPosition(self,master,row_index,position):

        master.rowconfigure(row_index,weight=2,uniform=1)

        posFrame = tk.Frame(master,bg ='yellow')
        posFrame.rowconfigure(0,weight=1,uniform=1)
        
        col_len = len(position[0].__dict__)
        pos_title = tk.Label(posFrame,text=f'Corresponding Position')
        pos_title.grid(row=0,column=0,columnspan=col_len,sticky=tk.NSEW)

        posFrame.rowconfigure(1,weight=1,uniform=1)
        for i,key in enumerate(position[0].__dict__.keys()):
                key = str(key)
                title_lb = tk.Label(posFrame,text=key,bd=2)
                posFrame.columnconfigure(i, weight=1,uniform=1)
                title_lb.grid(row=1,column=i,sticky=tk.NSEW)

        for j, handle in enumerate(position,start=2):
            
            posFrame.rowconfigure(j,weight=1,uniform=1)

            for k,val in enumerate(handle.__dict__.values()):
                val = str(val)
                handle_val = hp.getReadOnlyWidget(master=posFrame,value=val,max_length=15)
                handle_val.grid(row=j,column=k,sticky=tk.EW)

        posFrame.grid(row=row_index,column=0,sticky=tk.NSEW,pady=5)
        
     


        #Show loaded Image 
        filename = records_list[0].US_img
        imgtk = self.view.getTKImage(filename)
        
        self.view.savedImgLabel.imgtk = imgtk
        self.view.savedImgLabel.configure(image=self.view.savedImgLabel.imgtk)

        logging.info("Navigation is ready. Please start Tracking and calibrating")

    
        
    def _debugfunc(self):
        self.model.load_workitem('E-2')
        self.view.buildSummaryFrame(master=self.view.rightFrame)
        self.view.showMenu(menu='summary')
        self.buildSummaryContent()
        

    # Stub for Tobias
    def openExamination(self):

        #How to access data, from Tables
        E_ID = 'E-2'
        self.model.load_workitem(E_ID)

        workitem = self.model.get_current_workitem()

        exam_object, records_list, positions_list = workitem.values()

        print(exam_object.E_ID)
        print(records_list[0].R_ID)
        #Position is a list object, which contains 4 handle objects
        print(positions_list[0])

        # Have fun. 

    def initFunctionality(self):
        
        self.view.newExamiBut["command"] = self.newExamination

        self.view.startExamiBut["command"] = self.startExamination
        self.view.activateHandleBut["command"] =lambda: self.q.put(self.activateHandles)

        self.view.saveRecordBut["command"] = lambda: self.q.put(self.saveRecord)
        self.view.trackBut["command"] = lambda: self.q.put(self.startstopTracking)
        self.view.finishExamiBut["command"] = self.finalizeExamination

        self.view.openExamiBut["command"] = self.openExamination
        
        self.view.cancelBut["command"] = self.cancelExamination

        self.view.NOBUTTONSYET["command"] = self._debugfunc
        #lambda: print("NO FUNCTIONALITY YET BUT I'LL GET U soon :3 <3")


    def addSetupHandlesFunc(self):
        
        frames = self.view.setupHandleFrames
        #Partial muss genutzt werden, weil der Parameter hochgezählt wird. 
        for i,frame_data in enumerate(frames):
            #frame,handlename,ref_entry,button,valid = frame_data.values()
            button = frame_data["button"]
            button["command"] = partial(self.validateSetupHandles, handle_index=i)



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
            self.view.sysmodeLabel["text"] = "Operating Mode: "+self.aua.get_sysmode()
        else:
            self.view.rightFrame.after(2000,self.refreshSysmode)

    #WIP   
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
