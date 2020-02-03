#from UvisModel import UltraVisModel
#from UvisView import UltraVisView
from AuroraAPI import Aurora, Handle, HandleManager
import threading
import tkinter as tk
from tkinter import ttk
import serial
import time
import os
import sys
# import logging or threadsafe logging etc. 




class Uvisproto(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("TTR: Track To Reference - Debug")


        #Init Aurorasystem + Serial COnfig
        ser = serial.Serial()
        ser.port = 'COM5'
        ser.baudrate = 9600
        ser.parity = serial.PARITY_NONE
        ser.bytesize = serial.EIGHTBITS
        ser.stopbits = serial.STOPBITS_ONE
        ser.xonxoff = False
        ser.timeout = 2
        #temporär
        self.initAurora(ser)
        self.activateHandles()


        #Define Tabroot Notebook
        self.tabControl = ttk.Notebook(self.master)
        
        #Define Tab 1 Frames
        self.t1_debugFrame = tk.Frame(self.tabControl, bg="grey")
        self.t1_debugFrame.rowconfigure(0, weight=1)
        self.t1_debugFrame.columnconfigure(0, weight=80)
        self.t1_debugFrame.columnconfigure(1, weight=1)

        self.leftFrame = tk.Frame(self.t1_debugFrame, bg="green")
        self.rightFrame = tk.Frame(self.t1_debugFrame, bg="blue")

        self.leftFrame.grid(row=0, column=0, pady=8, padx=8, sticky=tk.NSEW)
        self.rightFrame.grid(row=0, column=1, pady=8, padx=8, sticky=tk.NSEW)
       
        self.build_widgets(self.leftFrame)
        self.build_rightWidges()

        #Tab2
        self.t2_otherframe = tk.Frame(self.tabControl, bg="yellow")
        

        self.t1_debugFrame.pack(fill=tk.BOTH, expand=tk.TRUE)

        self.tabControl.add(self.t1_debugFrame, text='Debugging Tab 1')
        self.tabControl.add(self.t2_otherframe, text='Tab 2')
        self.tabControl.pack(fill=tk.BOTH, expand=tk.TRUE)

        self.master.geometry("800x500")

       # self.model = UltraVisModel()
        

    def initAurora(self,ser):
        try:
            self.aua = Aurora(ser)
            self.aua.resetandinitSystem()
        except serial.SerialException as e:
            print(str(e))
            return
        

    def beep(self,num=1):
        
        a = threading.Thread(name="BEEP Thread", target=self.aua.beep,args=(num,))
        if self.aua.lock.acquire(0):
            a.start()            
        else:
            print("too much beep")



        #build_widgets()

    def build_widgets(self,lFrame):
        self.initBut = tk.Button(lFrame)
        self.initBut["text"] = "Beep Serial"
        self.initBut["command"] = self.beep

        self.readBut = tk.Button(lFrame)  
        self.readBut["text"] = "READ Serial"
        self.readBut["command"] = self.aua.readSerial
    
        self.resetBut = tk.Button(lFrame)
        self.resetBut["text"] = "Reinitialize System"
        self.resetBut["command"] = self.aua.resetandinitSystem
        
        self.testBut = tk.Button(lFrame)
        self.testBut["text"] = "Test Something"
        self.testBut["command"] = self.testFunction

        self.handleBut = tk.Button(lFrame)
        self.handleBut["text"] = "Activate Handles"
        self.handleBut["command"] = self.activateHandles
        
        self.restartBut = tk.Button(lFrame)
        self.restartBut["text"] = "Restart Program"
        #self.restartBut["command"] = self.restart

        self.quit = tk.Button(lFrame, text="QUIT", fg="red",
                    command=self.master.destroy)
        

        #Pack-Geomanager for Leftframe
        self.initBut.pack(side=tk.TOP)
        self.readBut.pack(side=tk.TOP)
        self.resetBut.pack(side=tk.TOP)
        self.testBut.pack()
        self.handleBut.pack()
        # self.restartBut.pack()
        self.quit.pack()

        
    def build_rightWidges(self):
        self.cmdLabel = tk.Label( self.rightFrame, text="CMD")
        self.cmdEntry = tk.Entry(self.rightFrame,bd =5)
        self.expecLabel = tk.Label( self.rightFrame, text="Expected read ending character")
        self.expec = tk.Entry(self.rightFrame,bd =5)
        self.sleepLabel = tk.Label( self.rightFrame, text="Read sleep time")
        self.sleeptimeEntry = tk.Entry(self.rightFrame,bd =5)
        self.sleeptimeEntry.insert(0,0)
        
        self.cmdLabel.pack(side=tk.TOP, pady=(10, 2))
        self.cmdEntry.pack(side=tk.TOP)
        self.expecLabel.pack(side=tk.TOP, pady=(10, 2))
        self.expec.pack(side=tk.TOP)
        self.sleepLabel.pack(side=tk.TOP, pady=(10, 2))
        self.sleeptimeEntry.pack(side=tk.TOP)
        
        self.cmdEntry.bind('<Return>', func=self.writeCmd2AUA)
        self.sleeptimeEntry.bind('<Return>', func=self.writeCmd2AUA)
        self.expec.bind('<Return>', func=self.writeCmd2AUA)


    # Controller Functionality

    def activateHandles(self):
        # todo Gesamtprozess nach Guide (siehe Aurora API)

        try: 
            print("All allocated Ports")
            
            phsr_string = self.aua.phsr()

            self.hm = HandleManager(phsr_string)
            handles = self.hm.getHandles()

            # print("handles 02")
            # Occupied handles but not initialized or enabled
            # self.aua.phsr(2)

            # Alle Port-Handles Initialisieren
            # Alle Port-Hanldes aktivieren
            print(str(self.hm.getNum_Handles())+" Handles identified")
            print("Initializing Port-Handles")
                    
            for h_id in handles :
                self.aua.pinit(handles[h_id])
                self.aua.pena(handles[h_id],'D')

            # Pr�fen, ob noch Handles falsch belegt sind
            # self.aua.phsr(3)
            # print("handles 03")
            # ser.write(b'PHSR 03\r')
            # time.sleep(1)
            # readSerial(ser)  
            
        except Warning as w:
            print(str(w))


    def startTracking(self):
        self.aua.tstart(40)
        
        #self.transformationData()

    def startstopTracking(self):
        if (self.aua.sysmode=='SETUP'):
            pass
            #thread.start_new(self.aua.tstart, ())
        else:
            self.aua.tstop



    def writeCmd2AUA(self,event):
           
        try:
            command = self.cmdEntry.get()
            self.aua.readsleep = float(self.sleeptimeEntry.get())
            if (len(self.expec.get())==0):
                a = False
            else:
                a = self.expec.get()

            print("Execute command: "+command)
            self.aua.writeCMD(command,expect=a)
            self.cmdEntry.delete(0, 'end')

        except Warning as e:
            print("An FATAL occured: "+str(e))
        

            
    def testFunction(self):
        self.aua.tstart()
        while True:
            tx = self.aua.tx()
            self.hm.updateHandles(tx)
       
            
    
    
    '''
    def restart(self):
        b = __file__
        d = sys.executable  
        z = 'D:\\Nam\\Docs\\Uni\\Master\ Projekt\\Track\ To\ Reference\\WP\\env\\Scripts\\python.exe'
        c = os.path.abspath(__file__)
        os.execv(z, ['python'] + sys.argv)
        print("done")'''


class auroraThread(threading.Thread):
    def __init__(self, ser, name=None, daemon=None):
        threading.Thread.__init__(self)
        self.ser = ser

    def initAurora(self):
        try:
            self.aua = Aurora(self.ser)
            self.aua.reset
            self.aua.init
        except serial.SerialException as e:
            print(str(e))
            return

    
    def run(self):  
        self.waiting = True
        print("Starting "+self.name+" - "+time.ctime(time.time()))
        self.initAurora()
        while self.waiting:
            time.sleep(0.5)
    
    def beep(self, num):
        self.aua.beep(num)


root = tk.Tk()
app = Uvisproto(master=root)

app.mainloop()
