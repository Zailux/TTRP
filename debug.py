from UvisModel import UltraVisModel
from UvisView import UltraVisView
from AuroraAPI import Aurora, Handle, HandleFactory
import threading
import tkinter as tk
from tkinter import ttk
import serial
import time
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
        ser.timeout = 1

        t_aua = threading.Thread(target=self.initAurora(ser),name="Aurora_Init_thread",daemon=True)
        t_aua.start()
        

        #Define Tabroot Notebook
        self.tabControl = ttk.Notebook(self.master)
        
        #Define Frames
        self.mainFrame = tk.Frame(self.tabControl, bg="grey")
        self.mainFrame.rowconfigure(0, weight=1)
        self.mainFrame.columnconfigure(0, weight=80)
        self.mainFrame.columnconfigure(1, weight=1)

        self.leftFrame = tk.Frame(self.mainFrame, bg="green")
        self.rightFrame = tk.Frame(self.mainFrame, bg="blue")

        self.leftFrame.grid(row=0, column=0, pady=8, padx=8, sticky=tk.NSEW)
        self.rightFrame.grid(row=0, column=1, pady=8, padx=8, sticky=tk.NSEW)
       
        self.build_widgets(self.leftFrame)
        self.build_rightWidges()

        #Tab2
        self.tab2 = tk.Frame(self.tabControl, bg="yellow")
        

        self.mainFrame.pack(fill=tk.BOTH, expand=tk.TRUE)

        self.tabControl.add(self.mainFrame, text='Tab 1')
        self.tabControl.add(self.tab2, text='Tab 2')
        self.tabControl.pack(fill=tk.BOTH, expand=tk.TRUE)

        self.master.geometry("700x500")

        self.model = UltraVisModel()
        
        

       
    def initAurora(self,ser):
        self.aua = Aurora(ser)
        self.aua.reset
        self.aua.init
        


        #build_widgets()
    def build_widgets(self,lFrame):
        self.initBut = tk.Button(lFrame)
        self.initBut["text"] = "INIT Serial"
        self.initBut["command"] = self.aua.init  

        self.readBut = tk.Button(lFrame)  
        self.readBut["text"] = "READ Serial"
        self.readBut["command"] = self.aua.readSerial
    
        self.resetBut = tk.Button(lFrame)
        self.resetBut["text"] = "Reset Serial"
        self.resetBut["command"] = self.aua.reset
        
        self.testBut = tk.Button(lFrame)
        self.testBut["text"] = "Test Serial"
        #self.testBut["command"] = self.testSerial

        self.handleBut = tk.Button(lFrame)
        self.handleBut["text"] = "Activate Handles"
        self.handleBut["command"] = self.activateHandles
        

        self.quit = tk.Button(lFrame, text="QUIT", fg="red",
                    command=self.master.destroy)
        

        #Pack-Geomanager for Leftframe
        self.initBut.pack(side=tk.TOP)
        self.readBut.pack(side=tk.TOP)
        self.resetBut.pack(side=tk.TOP)
        self.testBut.pack()
        self.handleBut.pack()
        self.quit.pack()
    
      

        
    def build_rightWidges(self):
        self.cmdEntry = tk.Entry(self.rightFrame,bd =5, text="...cmd")
        self.cmdEntry.pack(side=tk.TOP)
        self.cmdEntry.bind('<Return>', func=self.writeCmd2AUA)



    # Controller Functionality

    def activateHandles(self):
        # todo
        print("All allocated Ports")
        
        phsr_string = self.aua.phsr()

        factory = HandleFactory(phsr_string)
        handles = factory.getHandles()

        # print("handles 02")
        # Occupied handles but not initialized or enabled
        # self.aua.phsr(2)

        # Alle Port-Handles Initialisieren
        # Alle Port-Hanldes aktivieren
        print("Initializing Port-Handles")
                
        for handle in handles :
            
            self.aua.pinit(handle)
            self.aua.pena(handle,'D')

            


        # Pr�fen, ob noch Handles falsch belegt sind
        # self.aua.phsr(3)
        # print("handles 03")
        # ser.write(b'PHSR 03\r')
        # time.sleep(1)
        # readSerial(ser)    

    def startTracking(self):
        self.aua.tstart(40)
        
        #self.transformationData()

    def startstopTracking(self):
        if (self.aua.sysmode=='SETUP'):
            thread.start_new(self.aua.tstart, ())
        else:
            self.aua.tstop

 

        

    def writeCmd2AUA(self,event):
           
        try:
            command = self.cmdEntry.get()
            print("Execute command: "+command)
            self.aua.writeCMD(command)
            self.cmdEntry.delete(0, 'end')

        except Exception as e:
            print("An FATAL occured: "+str(e))
        

            



root = tk.Tk()
app = Uvisproto(master=root)

app.mainloop()






