from ultraVisGui import UltraVisController
from UvisModel import UltraVisModel, Handle
from UvisView import UltraVisView
import tkinter as tk
import serial
import time


class Uvisproto(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("TTR: Track To Reference")
        self.pack(fill=tk.BOTH, expand=tk.TRUE)
        self.master.geometry("700x500")

        self.model = UltraVisModel()
        self.ser = self.model.getSerial()


        self.create_widgets()


    def create_widgets(self):
        self.initBut = tk.Button(self)
        self.initBut["text"] = "INIT Serial"
        self.initBut["command"] = self.startSerial
        self.initBut.pack(side="top")

        self.readBut = tk.Button(self)
        self.readBut["text"] = "READ Serial"
        self.readBut["command"] = self.readSerial
        self.readBut.pack(side="top")

        self.resetBut = tk.Button(self)
        self.resetBut["text"] = "Reset Serial"
        self.resetBut["command"] = self.resetSerial
        self.resetBut.pack(side="top")

        self.testBut = tk.Button(self)
        self.testBut["text"] = "Test Serial"
        self.testBut["command"] = self.testSerial
        self.testBut.pack(side="top")

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.pack(side="bottom")


        

    def startSerial(self):
        try: 
            self.ser.open()
            print("ser is open")
        except Exception as e:
            print("error open serial port: " + str(e))     

    def readSerial(self):
        out = ''
        #out = self.ser.read(1)  
        out = self.ser.read_until()
        print(out)
        print("done read")

    def resetSerial(self):
        self.ser = self.model.getSerial()
        self.ser.close()

    
    def testSerial(self):
        print(self.ser.name) 
        self.ser.write( b'BOGUS \r')
        time.sleep(1)
        self.readSerial()
        self.ser.write( b'RESET \r')
        time.sleep(1)
        self.readSerial()
        self.ser.write(b'INIT \r')
        time.sleep(1)
        self.readSerial()


#time.sleep(1)

root = tk.Tk()
app = Uvisproto(master=root)

app.mainloop()






