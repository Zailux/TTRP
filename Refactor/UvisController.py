from UvisModel import UltraVisModel,Aufzeichnung
from UvisView import UltraVisView
import logging
import time
import pandas as pd
from datetime import datetime
import random
import tkinter as tk

import serial
import functools
import threading
import queue
#import os

# import logging or threadsafe logging etc. 
#from Observable import Observable
import sys

#TTRP.AuroraAPI is an temporary Solution. Should be same folder later
sys.path.insert(1, 'd:\\Nam\\Docs\\Uni\\Master Projekt\\Track To Reference\\WP\\TTRP')
from AuroraAPI import Aurora, Handle, HandleManager

from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.animation
from mpl_toolkits.mplot3d import Axes3D



#GlobaleVariablen Definition
BUTTON_WIDTH = 25



# Idee anstatt beim jeweiligen Methoden aufruf self.q.put methoden name rein zuschreiben,
# über einen Wrapper beim Funktionsaufruf dies zu tun. 
def toQueue(func):

    @functools.wraps(func)
    def q_wrapper(*args, **kwargs):
        #args[0].q.put( [func,*args,**kwargs] )
        pass
     
    return q_wrapper


class UltraVisController:

    def __init__(self):
        
        #Logging Configuration
        format = "%(asctime)s - %(threadName)s|%(levelname)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
        self._Logger = logging.getLogger()
        #self._Logger.setLevel(logging.DEBUG)

        #Create Model and View
        self.root = tk.Tk()
       
        self.model = UltraVisModel()
        self.view = UltraVisView(self.root)
        
        #Controller Attributes
        self.debug_start = True
        self.hm = None
        self.aua = None

        self.initBackgroundQueue()
        
        #Init Aurorasystem + Serial COnfig
        self.ser = serial.Serial()
        self.ser.port = 'COM8'
        self.ser.baudrate = 9600
        self.ser.parity = serial.PARITY_NONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.xonxoff = False
        self.ser.timeout = 2

        #Tries to initalize Aurora and Adds Functionaly based on state
        self.initAurora(self.ser)
    
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


    #Closing Method and bind to root Window
    def on_closing(self):
        #Close FrameGrabber
        self.view.USImgLabel.after_cancel(self.view._FrameGrabberJob)
        self.view.cap.release()
        
        #Close Tracking + Matplotanimation
        if (self.aua_active):
            if(self.aua.getSysmode()=='TRACKING'):
                self.stopTracking = True
                self.view.navCanvas._tkcanvas.after_cancel(self.view._Canvasjob)
                with self.aua._lock:
                    self.aua.tstop()
        
        self.quitEvent.set()
        #logging.debug("TRACKING THREAD ALIVE?: "+str(self.tracking_Thread.is_alive))
        self.ser.close()

        #Bug that plt.close also closes the TKinter Windows!
        plt.close(fig=self.view.fig)
        logging.info("Good Night Cruel World :D")
        self.root.quit()
        self.root.destroy()

    def run (self):
        self.root.mainloop()

    def initBackgroundQueue(self):
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

    def initAurora(self,ser,extended=None):
        if (extended == None):
            extended = self.debug_start

        
        widgets = self.view.t2_debugFrame.winfo_children()
        self.aua_active = False
        try:
            self.aua = Aurora(ser)

        except serial.SerialException as e:
            logging.warning("serial.SerialException: "+str(e))
            self.disableWidgets(widgets)
            self.view.auaReInitBut.grid(row=7,padx=(1,1),sticky=tk.NSEW)
            self.view.auaReInitBut["state"] = 'normal'
            self.view.auaReInitBut["command"] = lambda: self.initAurora(self.ser,extended=self.debug_start)
            return
        except Warning as w:
            logging.exception(str(w))
            self.disableWidgets(widgets)
            self.view.auaReInitBut.grid(row=7,padx=(1,1),sticky=tk.NSEW)
            self.view.auaReInitBut["state"] = 'normal'
            self.view.auaReInitBut["command"] = lambda: self.initAurora(self.ser,extended=self.debug_start)
            return

        self.aua_active = True
        self.aua.register("Sysmode",self.refreshSysmode)
        self.enableWidgets(widgets)
        self.view.auaReInitBut.grid_forget()
       
        self.aua.resetandinitSystem()
        
        self.addFuncDebug()

        if (extended):
            self.q.put(self.activateHandles)
            self.addFuncTracking()


    #   -----Aurora Functionality  ------#

    def activateHandles(self):
        # todo Gesamtprozess nach Guide (siehe Aurora API)
        logging.info("Activate Handles - Acquiring Lock")

        with self.aua._lock:
            try: 
                #print("All allocated Ports")
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

        
        logging.info("Activate Handles done")


    def startstopTracking(self):
        #Bug self.aua can't deal with concurrent calls !
       
        
        if (self.aua.getSysmode()=='SETUP'):
            with self.aua._lock:
                self.aua.tstart(40)

            #Thread starte Thread und gebe den AppFrame GUI die Daten
            self.stopTracking = False
            self.tracking_Thread = threading.Thread(target=self.trackHandles,daemon=True,name="tracking_Thread")
            self.tracking_Thread.start()
            self.view._Canvasjob = self.view.navCanvas._tkcanvas.after(1500,func=self.view.buildCoordinatesystem)
            

        elif(self.aua.getSysmode()=='TRACKING'):
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
        

    
    def savePosition(self):
        if (not self.aua.getSysmode()=='TRACKING'):
            logging.info("This functionality is only available during tracking. Please Start Tracking")
            return

        self.view.saveUSImg()

        dt = datetime.now()
        tmpstamp = dt.strftime("%a, %d-%b-%Y (%H:%M:%S)")        
        #to do: description auf gui ziehen 

        aufz = Aufzeichnung(date=tmpstamp)

        #Stops the current refresh and changing of Positional data 
        #self.navAnim.event_source.stop()
        handles = self.hm.getHandles()

        if (self.validatePosition(handles)):
            #saving position Frame and Handles 

            #Save Image to Filesystem and prepare Imagepath image
            img = self.view.savedImg.copy()
            img = img.resize(self.view.og_imgsize, Image.ANTIALIAS)
            filename = f'{aufz.A_ID[4:]}_img'
            imgpath = 'TTRP/data/img/'+filename+'.png'
            
            try:
                img.save(imgpath)
                aufz.US_img=imgpath
                self.model.saveAufzeichnung(aufzeichnung=aufz)
            except IOError as e:
                raise Warning("Error during saving the image. \nErrorMessage:"+str(e))
            except ValueError as e:
                #Konnte Aufzeichnung nicht speichern. Please try again with SAME DATA!
                pass
            
            try:
                self.model.savePosition(A_ID=aufz.A_ID, handles=handles)
            except ValueError as e:
                #Konnte handles nicht speichern. Please try again with SAME DATA?!
                pass
           
            


    def cleanSavingProcess(self, aufzeichnung):
        pass


           
 
            
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
            
            if (h.frame_id not in frameID and frameID):
                validSave = False

            frameID.append(h.frame_id)


        if (not validSave):
            logging.error("Trying to save Position with missing Handles: "+str(missID)+". Please use valid Data")

        return validSave
            

               




    def writeCmd2AUA(self,event):
           
        try:
            command = self.view.cmdEntry.get()
            self.aua.readsleep = float(self.view.sleeptimeEntry.get())
            if (len(self.view.expec.get())==0):
                a = False
            else:
                a = self.view.expec.get()

            logging.debug("Execute command: "+command)
            self.aua.writeCMD(command,expect=a)
            self.view.cmdEntry.delete(0, 'end')

        except Warning as e:
            logging.exception("An FATAL occured: "+str(e))   
            
    def testFunction(self):
        with self.aua._lock:
            self.aua.beep(2)

    #----GUI Related ----#
    def addFuncDebug(self):
        #Menu
        #self.view.initBut["command"] = self.beep
        self.view.readBut["command"] = self.aua.readSerial
        self.view.resetBut["command"] = self.aua.resetandinitSystem
        self.view.testBut["command"] = self.testFunction
        self.view.handleBut["command"] = self.activateHandles
        #self.view.restartBut["command"] = self.restart
        self.view.quitBut["command"] = self.root.destroy
        

        #DebugCMD
        self.view.cmdEntry.bind('<Return>', func=self.writeCmd2AUA)
        self.view.sleeptimeEntry.bind('<Return>', func=self.writeCmd2AUA)
        self.view.expec.bind('<Return>', func=self.writeCmd2AUA)

    def addFuncTracking(self):
        self.view.saveBut["command"] = lambda: self.q.put(self.savePosition)
        self.view.trackBut["command"] = lambda: self.q.put(self.startstopTracking)
    


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
        self.view.sysmodeLabel["text"] = "Operating Mode: "+self.aua.getSysmode()
        

'''        
   

    def safe_met_handle_string(self, test_out):
        Anz_Sensoren = int(test_out[0:2])
        test_out = test_out[2:]
        iii = 0
        while iii < Anz_Sensoren:
            if "MISSING" in test_out[0:15]:
                test_out = test_out[32:101]
                iii += 1
            else:
                # String zu einem Sensor
                self.handle_string = test_out[0:69]
                if self.handle_string[1:2] == "A":
                    self.handle_0_ID = self.handle_string[1:2]
                    self.handle_0_Q0 = float(self.insert_dash(self.handle_string[2:8], 2))
                    self.handle_0_Qx = float(self.insert_dash(self.handle_string[8:14], 2))
                    self.handle_0_Qy = float(self.insert_dash(self.handle_string[14:20], 2))
                    if self.handle_string[20] == '-':
                        self.handle_0_Qz = float(self.insert_dash(self.handle_string[21:26], 1))
                    elif self.handle_string[20] == '+':
                        self.handle_0_Qz = float(self.insert_dash('-' + self.handle_string[21:26], 2))
                    self.handle_0_Tx = float(self.insert_dash(self.handle_string[26:33], 5))
                    self.handle_0_Ty = float(self.insert_dash(self.handle_string[33:40], 5))
                    self.handle_0_Tz = float(self.insert_dash(self.handle_string[41:47], 4))
                    self.handle_0_Err = float(self.insert_dash(self.handle_string[47:59], 2))

                if self.handle_string[1:2] == "B":
                    # print("gute nacht sina")
                    self.handle_1_ID = self.handle_string[1:2]
                    self.handle_1_Q0 = float(self.insert_dash(self.handle_string[2:8], 2))
                    self.handle_1_Qx = float(self.insert_dash(self.handle_string[8:14], 2))
                    self.handle_1_Qy = float(self.insert_dash(self.handle_string[14:20], 2))
                    if self.handle_string[20] == '-':
                        self.handle_1_Qz = float(self.insert_dash(self.handle_string[21:26], 1))
                    elif self.handle_string[20] == '+':
                        self.handle_1_Qz = float(self.insert_dash('-' + self.handle_string[21:26], 2))
                    self.handle_1_Tx = float(self.insert_dash(self.handle_string[26:33], 5))
                    self.handle_1_Ty = float(self.insert_dash(self.handle_string[33:40], 5))
                    self.handle_1_Tz = float(self.insert_dash(self.handle_string[41:47], 4))
                    self.handle_1_Err = float(self.insert_dash(self.handle_string[47:59], 2))
                if self.handle_string[1:2] == "C":
                    self.handle_2_ID = self.handle_string[1:2]
                    self.handle_2_Q0 = float(self.insert_dash(self.handle_string[2:8], 2))
                    self.handle_2_Qx = float(self.insert_dash(self.handle_string[8:14], 2))
                    self.handle_2_Qy = float(self.insert_dash(self.handle_string[14:20], 2))
                    if self.handle_string[20] == '-':
                        self.handle_2_Qz = float(self.insert_dash(self.handle_string[21:26], 1))
                    elif self.handle_string[20] == '+':
                        self.handle_2_Qz = float(self.insert_dash('-' + self.handle_string[21:26], 2))
                    self.handle_2_Tx = float(self.insert_dash(self.handle_string[26:33], 5))
                    self.handle_2_Ty = float(self.insert_dash(self.handle_string[33:40], 5))
                    self.handle_2_Tz = float(self.insert_dash(self.handle_string[41:47], 4))
                    self.handle_2_Err = float(self.insert_dash(self.handle_string[47:59], 2))
                if self.handle_string[1:2] == "D":
                    self.handle_3_ID = self.handle_string[1:2]
                    self.handle_3_Q0 = float(self.insert_dash(self.handle_string[2:8], 2))
                    self.handle_3_Qx = float(self.insert_dash(self.handle_string[8:14], 2))
                    self.handle_3_Qy = float(self.insert_dash(self.handle_string[14:20], 2))
                    if self.handle_string[20] == '-':
                        self.handle_3_Qz = float(self.insert_dash(self.handle_string[21:26], 1))
                    elif self.handle_string[20] == '+':
                        self.handle_3_Qz = float(self.insert_dash('-' + self.handle_string[21:26], 2))
                    self.handle_3_Tx = float(self.insert_dash(self.handle_string[26:33], 5))
                    self.handle_3_Ty = float(self.insert_dash(self.handle_string[33:40], 5))
                    self.handle_3_Tz = float(self.insert_dash(self.handle_string[41:47], 4))
                    self.handle_3_Err = float(self.insert_dash(self.handle_string[47:59], 2))

                self.koordinatenSystem()
                test_out = test_out[70:]
                iii += 1

    def onSaveRefPosClicked(self):
        # print("Clicked save ref")
        self.safe_handle_0_ID = self.handle_0_ID
        self.safe_handle_0_Q0 = self.handle_0_Q0
        self.safe_handle_0_Qx = self.handle_0_Qx
        self.safe_handle_0_Qy = self.handle_0_Qy
        self.safe_handle_0_Qz = self.handle_0_Qz
        self.safe_handle_0_Tx = self.handle_0_Tx
        self.safe_handle_0_Ty = self.handle_0_Ty
        self.safe_handle_0_Tz = self.handle_0_Tz
        self.safe_handle_0_Err = self.handle_0_Err

        cv2image = cv2.cvtColor(self.ultraVisView.frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.ultraVisView.screenshotmain.imgtk = imgtk
        self.ultraVisView.screenshotmain.configure(image=imgtk)
'''

#TEMPORÄR!!!
controller = UltraVisController()
controller.run()
