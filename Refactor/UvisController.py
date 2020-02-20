# -*- coding: latin-1 -*-
from __future__ import print_function

#from UvisModel import UltraVisModel,
from UvisView import UltraVisView

import tkinter as tk

import serial
import threading
#import os
#import sys
# import logging or threadsafe logging etc. 
#from Observable import Observable



#GlobaleVariablen Definition
global firstClick 
global firstTime
firstClick = False
firstTime = False

BUTTON_WIDTH = 25



class UltraVisController:

    def __init__(self):
        
        #Create Model and View
        self.root = tk.Tk()
       
        #model = UltraVisModel()
        view = UltraVisView(self.root)
        
        #Init Aurorasystem + Serial COnfig
        ser = serial.Serial()
        ser.port = 'COM5'
        ser.baudrate = 9600
        ser.parity = serial.PARITY_NONE
        ser.bytesize = serial.EIGHTBITS
        ser.stopbits = serial.STOPBITS_ONE
        ser.xonxoff = False
        ser.timeout = 2

        #self.ser.open()

        #self.safe_handle = Handle("safe","none")
        #handle_1, 2 3 and 0

        

        # Configure the buttons
        '''
        self.ultraVisView.buttonReset.config(command=self.onResetSystemClicked)
        self.ultraVisView.buttonInitSystem.config(command=self.onInitSystemClicked)
        self.ultraVisView.buttonStartStopTracking.config(command=self.onStartStopTrackingClicked)
        self.ultraVisView.buttonSaveRefPosition.config(command=self.onSaveRefPosClicked)'''

    def run (self):
        self.root.mainloop()

'''        
    def onInitSystemClicked(self):
        print("Init")
        # ser.send_break()  # zwingend noetig
        thread.start_new_thread(self.InitSystem, ())

    def InitSystem(self):
        self.ser.write(b'RESET \r')
        time.sleep(1)
        self.ser.write(b'INIT \r')
        time.sleep(1)
        self.readSerial()
        self.activateHandles()
        thread.exit()

    def activateHandles(self):
        # todo
        print("All allocated Ports")
        self.ser.write(b'PHSR 00\r')
        time.sleep(1)
        reply = self.readSerial_Return()
        print("Reply is:")
        print(reply)

        # Anzahl der Handles aus der Antwort ermitteln
        number_handles = 0
        handles = []
        number_handles = int(reply[0:2])

        # Nur noch den interessanten Teil des Replys beachten (nach den ersten zwei Zeichen)
        reply = reply[2:]

        i = 0
        while i < number_handles:
            # String zu einem Handle auslesen
            h = reply[0:5]
            # ID und status von einander trennen
            h_id = h[0:2]
            h_state = h[2:3]
            # Liste mit ID und Status des Handle erstellen
            hx = [h_id, h_state]
            # Das Handle (als kleine Liste) an die gro�e HandlesListe anf�gen
            handles.append(hx)
            # Den Teil der Antwort l�schen, der uninteressant geworden ist
            reply = reply[5:]
            i += 1

        # print("handles 02")
        # ser.write(b'PHSR 02\r')
        # time.sleep(1)
        # readSerial(ser)

        # Alle Port-Handles Initialisieren
        # Alle Port-Hanldes aktivieren
        print("Initializing Port-Handles")
        ii = 0
        while ii < len(handles):
            h_id_b = bytes(handles[ii][0].encode('utf-8'))
            b = b'PINIT ' + h_id_b + b'\r'
            print("Initialisiere " + str(b))
            self.ser.write(b)
            time.sleep(2)
            self.readSerial()

            c = b'PENA ' + h_id_b + b'D\r'
            print("Activating " + str(b))
            self.ser.write(c)
            time.sleep(2)
            self.readSerial()

            ii += 1

        # Pr�fen, ob noch Handles falsch belegt sind
        # print("handles 03")
        # ser.write(b'PHSR 03\r')
        # time.sleep(1)
        # readSerial(ser)


    def readSerial(self):
        print(self.readSerial_Return())

    def readSerial_Return(self):
        out = ''
        r = "\r"
        found = False

        while not found:
            try:
                while self.ser.in_waiting > 0:
                    out += self.ser.read_all().decode()
            except Exception as e:
                print(str(e))
            if len(out) > 0 and out.find(r, 0, len(out)) != -1:
                found = True
        return out

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