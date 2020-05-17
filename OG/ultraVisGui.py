# -*- coding: latin-1 -*-
from __future__ import print_function
# from visual import *
import tkinter as tk
import time

from cv2 import cv2
# import imutils
import serial
import _thread as thread

from PIL import Image
from PIL import ImageTk

from Observable import Observable

import matplotlib
matplotlib.use('Tkagg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


#GlobaleVariablen Definition
global firstClick 
global firstTime
firstClick = False
firstTime = False

BUTTON_WIDTH = 25


class UltraVisModel:
    def __init__(self):
        self.activeUser = Observable()

        self.tracking = Observable()

    def setActiveUser(self, activeUser):
        self.activeUser.set(activeUser)


class UltraVisView(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.master = master
        self.master.title("TTR: Track To Reference")
        self.master.wm_state('zoomed')

        self.master.focus_force()

        self.mainFrame = tk.Frame(self.master)
        # Configure the tab - that the frames inside adjust dynamically
        self.mainFrame.rowconfigure(0, weight=1)
        self.mainFrame.columnconfigure(0, weight=80)
        self.mainFrame.columnconfigure(1, weight=1)

        self.leftFrame = tk.Frame(self.mainFrame)
        self.rightFrame = tk.Frame(self.mainFrame)

        self.leftFrame.grid(row=0, column=0, pady=8, padx=8, sticky=tk.NSEW)
        self.rightFrame.grid(row=0, column=1, pady=8, padx=8, sticky=tk.NSEW)

        self.buildLeftFrame()
        self.buildRightFrame()

        self.mainFrame.pack(fill=tk.BOTH, expand=tk.TRUE)

    def buildLeftFrame(self):
        self.upperFrameLeft = tk.Frame(self.leftFrame)
        self.lowerFrameLeft = tk.Frame(self.leftFrame)

        # self.rightFrame.rowconfigure(0, weight=1)
        # self.rightFrame.rowconfigure(1, weight=1)
        # self.rightFrame.columnconfigure(1, weight=1)

        self.upperFrameLeft.grid(row=0, column=0, sticky=tk.NSEW)
        self.upperFrameLeft.columnconfigure(0, weight=1)
        self.lowerFrameLeft.grid(row=1, column=0, sticky=tk.NSEW)
        self.lowerFrameLeft.columnconfigure(0, weight=1)

        # self.buttonReset = tk.Button(self.upperFrame, text="test", width=BUTTON_WIDTH)
        # self.buttonReset.grid(row=0, column=0, pady=8)
        self.imageFrame = tk.Frame(self.upperFrameLeft)
        self.imageFrame.grid(row=0, column=0, padx=10, pady=2, sticky=tk.NSEW)
        self.lmain = tk.Label(self.imageFrame, width=490, height=378)
        self.lmain.grid(row=0, column=0, sticky=tk.NSEW)
        self.lmain.pack_propagate(0)

        self.cap = cv2.VideoCapture(0)
        self.Capture_FrameGrabber()

        self.screenshot = tk.Frame(self.lowerFrameLeft)
        self.screenshot.grid(row=0, column=0, padx=10, pady=2, sticky=tk.NSEW)
        self.screenshotmain = tk.Label(self.screenshot, width=490, height=378)
        self.screenshotmain.grid(row=0, column=0, sticky=tk.NSEW)
        self.screenshotmain.pack_propagate(0)

    def Capture_FrameGrabber(self):
        _, frame = self.cap.read()
        self.frame = cv2.flip(frame, 1)
        cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(10, self.Capture_FrameGrabber)

        # Slider window (slider controls stage position)
        # self.sliderFrame = tk.Frame(self.upperFrameLeft, width=600, height=100)
        # self.sliderFrame.grid(row=600, column=0, padx=10, pady=2)

    def buildRightFrame(self):
        # self.rightFrame.rowconfigure(0, weight=1)
        # self.rightFrame.rowconfigure(1, weight=1)
        # self.rightFrame.columnconfigure(1, weight=1)
        self.upperFrameRight = tk.Frame(self.rightFrame)
        self.lowerFrameRight = tk.Frame(self.rightFrame)
        self.upperFrameRightLeft = tk.Frame(self.upperFrameRight)
        self.upperFrameRightRight = tk.Frame(self.upperFrameRight)

        self.upperFrameRight.grid(row=0, column=0, sticky=tk.NSEW)
        self.upperFrameRightLeft.grid(row=0, column=0, sticky=tk.NSEW)
        self.upperFrameRightRight.grid(row=0, column=1, sticky=tk.NSEW)
        self.lowerFrameRight.grid(row=2, column=0, sticky=tk.NSEW)

        self.buttonReset = tk.Button(self.upperFrameRightLeft, text="Reset System", width=BUTTON_WIDTH)
        self.buttonReset.grid(row=0, column=0, pady=8, sticky=tk.EW)

        self.buttonInitSystem = tk.Button(self.upperFrameRightLeft, text="Initalize System", width=BUTTON_WIDTH)
        self.buttonInitSystem.grid(row=1, column=0, pady=8, sticky=tk.EW)

        self.buttonStartStopTracking = tk.Button(self.upperFrameRightLeft, text="Start/Stop Tracking", width=BUTTON_WIDTH)
        self.buttonStartStopTracking.grid(row=2, column=0, pady=8)

        self.buttonSaveRefPosition = tk.Button(self.upperFrameRightLeft, text="Save Ref. Position", width=BUTTON_WIDTH)
        self.buttonSaveRefPosition.grid(row=3, column=0, pady=8)

        # Bilder f�r x-Achse
        self.x_links_orange = Image.open("x-links-orange.jpg")
        self.x_links_orange = ImageTk.PhotoImage(self.x_links_orange)
        self.x_links_rot = Image.open("x-links-rot.jpg")
        self.x_links_rot = ImageTk.PhotoImage(self.x_links_rot)
        self.x_rechts_orange = Image.open("x-rechts-orange.jpg")
        self.x_rechts_orange = ImageTk.PhotoImage(self.x_rechts_orange)
        self.x_rechts_rot = Image.open("x-rechts-rot.jpg")
        self.x_rechts_rot = ImageTk.PhotoImage(self.x_rechts_rot)
    

        #Bilder f�r Rotation auf x-Achse
        self.x_achse_kippen_links_orange = Image.open("x-achse-kippen-links-orange.jpg")
        self.x_achse_kippen_links_orange = ImageTk.PhotoImage(self.x_achse_kippen_links_orange)
        self.x_achse_kippen_links_rot = Image.open("x-achse-kippen-links-rot.jpg")
        self.x_achse_kippen_links_rot = ImageTk.PhotoImage(self.x_achse_kippen_links_rot)
        self.x_achse_kippen_rechts_orange = Image.open("x-achse-kippen-rechts-orange.jpg")
        self.x_achse_kippen_rechts_orange = ImageTk.PhotoImage(self.x_achse_kippen_rechts_orange)
        self.x_achse_kippen_rechts_rot = Image.open("x-achse-kippen-rechts-rot.jpg")
        self.x_achse_kippen_rechts_rot = ImageTk.PhotoImage(self.x_achse_kippen_rechts_rot)

        #Bilder f�r y-Achse
        self.y_vorne_orange = Image.open("y-vorne-orange.jpg")
        self.y_vorne_orange = ImageTk.PhotoImage(self.y_vorne_orange)
        self.y_vorne_rot = Image.open("y-vorne-rot.jpg")
        self.y_vorne_rot = ImageTk.PhotoImage(self.y_vorne_rot)
        self.y_hinten_orange = Image.open("y-hinten-orange.jpg")
        self.y_hinten_orange = ImageTk.PhotoImage(self.y_hinten_orange)
        self.y_hinten_rot = Image.open("y-hinten-rot.jpg")
        self.y_hinten_rot = ImageTk.PhotoImage(self.y_hinten_rot)

        # Bilder f�r Rotation auf y-Achse
        self.y_achse_kippen_links_orange = Image.open("y-achse-kippen-links-orange.jpg")
        self.y_achse_kippen_links_orange = ImageTk.PhotoImage(self.y_achse_kippen_links_orange)
        self.y_achse_kippen_links_rot = Image.open("y-achse-kippen-links-rot.jpg")
        self.y_achse_kippen_links_rot = ImageTk.PhotoImage(self.y_achse_kippen_links_rot)
        self.y_achse_kippen_rechts_orange = Image.open("y-achse-kippen-rechts-orange.jpg")
        self.y_achse_kippen_rechts_orange = ImageTk.PhotoImage(self.y_achse_kippen_rechts_orange)
        self.y_achse_kippen_rechts_rot = Image.open("y-achse-kippen-rechts-rot.jpg")
        self.y_achse_kippen_rechts_rot = ImageTk.PhotoImage(self.y_achse_kippen_rechts_rot)

        #Bilder f�r z-Achse
        self.z_oben_orange = Image.open("z-oben-orange.jpg")
        self.z_oben_orange = ImageTk.PhotoImage(self.z_oben_orange)
        self.z_oben_rot = Image.open("z-oben-rot.jpg")
        self.z_oben_rot = ImageTk.PhotoImage(self.z_oben_rot)
        self.z_unten_orange = Image.open("z-unten-orange.jpg")
        self.z_unten_orange = ImageTk.PhotoImage(self.z_unten_orange)
        self.z_unten_rot = Image.open("z-unten-rot.jpg")
        self.z_unten_rot = ImageTk.PhotoImage(self.z_unten_rot)

        # Bilder f�r Rotation auf z-Achse
        self.z_achse_kippen_links_orange = Image.open("z-achse-kippen-links-orange.jpg")
        self.z_achse_kippen_links_orange = ImageTk.PhotoImage(self.z_achse_kippen_links_orange)
        self.z_achse_kippen_links_rot = Image.open("z-achse-kippen-links-rot.jpg")
        self.z_achse_kippen_links_rot = ImageTk.PhotoImage(self.z_achse_kippen_links_rot)
        self.z_achse_kippen_rechts_orange = Image.open("z-achse-kippen-rechts-orange.jpg")
        self.z_achse_kippen_rechts_orange = ImageTk.PhotoImage(self.z_achse_kippen_rechts_orange)
        self.z_achse_kippen_rechts_rot = Image.open("z-achse-kippen-rechts-rot.jpg")
        self.z_achse_kippen_rechts_rot = ImageTk.PhotoImage(self.z_achse_kippen_rechts_rot)

        # Bilder f�r Eigen-Rotation
        self.self_rot_links_orange = Image.open("self-rot-links-orange.jpg")
        self.self_rot_links_orange = ImageTk.PhotoImage(self.self_rot_links_orange)
        self.self_rot_links_rot = Image.open("self-rot-links-rot.jpg")
        self.self_rot_links_rot = ImageTk.PhotoImage(self.self_rot_links_rot)
        self.self_rot_rechts_orange = Image.open("self-rot-rechts-orange.jpg")
        self.self_rot_rechts_orange = ImageTk.PhotoImage(self.self_rot_rechts_orange)
        self.self_rot_rechts_rot = Image.open("self-rot-rechts-rot.jpg")
        self.self_rot_rechts_rot = ImageTk.PhotoImage(self.self_rot_rechts_rot)

        # Bild als Ziel
        self.ziel = Image.open("ziel.jpg")
        self.ziel = ImageTk.PhotoImage(self.ziel)

        # Frame f�r X-Achse
        self.x_achse = tk.Frame(self.upperFrameRightRight, width=25, height=25)
        self.x_achse.grid(row=0, column=0, pady=8)
        self.x_achse_label = tk.Label(self.x_achse)
        self.x_achse_label.pack()
        self.x_links_orange_label = tk.Label(self.x_achse, image=self.x_links_orange)
        self.x_links_rot_label = tk.Label(self.x_achse, image=self.x_links_rot)
        self.x_rechts_orange_label = tk.Label(self.x_achse, image=self.x_rechts_orange)
        self.x_rechts_rot_label = tk.Label(self.x_achse, image=self.x_rechts_rot)
        self.x_ziel_label = tk.Label(self.x_achse, image=self.ziel)

        # self.x_achseImage = tk.Label(self.x_achse)
        # self.x_achseImage.grid(row=0, column=0)

        # Frame f�r X-Rotation
        self.x_rotation = tk.Frame(self.upperFrameRightRight, width=25, height=25)
        self.x_rotation.grid(row=1, column=0, pady=8)
        self.x_rotationImage = tk.Label(self.x_rotation)
        self.x_rotationImage.grid(row=0, column=0)

        # Frame f�r Y-Achse
        self.y_achse = tk.Frame(self.upperFrameRightRight, width=25, height=25)
        self.y_achse.grid(row=0, column=1, pady=8)
        self.y_achseImage = tk.Label(self.y_achse)
        self.y_achseImage.grid(row=0, column=0)

        # Frame f�r Y-Rotation
        self.y_rotation = tk.Frame(self.upperFrameRightRight, width=25, height=25)
        self.y_rotation.grid(row=1, column=1, pady=8)
        self.y_rotationImage = tk.Label(self.y_rotation)
        self.y_rotationImage.grid(row=0, column=0)

        # Frame f�r Z-Achse
        self.z_achse = tk.Frame(self.upperFrameRightRight, width=25, height=25)
        self.z_achse.grid(row=0, column=2, pady=8)
        self.z_achseImage = tk.Label(self.z_achse)
        self.z_achseImage.grid(row=0, column=0)

        # Frame f�r Z-Rotation
        self.z_rotation = tk.Frame(self.upperFrameRightRight, width=25, height=25)
        self.z_rotation.grid(row=1, column=2, pady=8)
        self.z_rotationImage = tk.Label(self.z_rotation)
        self.z_rotationImage.grid(row=0, column=0)

        # Frame f�r Eigen-Rotation
        self.self_rotation = tk.Frame(self.upperFrameRightRight, width=25, height=25)
        self.self_rotation.grid(row=0, column=3, pady=8)
        self.self_rotationImage = tk.Label(self.self_rotation)
        self.self_rotationImage.grid(row=0, column=0)

        # Koordinatensystem erstellen
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlim(-200, 200)
        self.ax.set_xlabel("X")
        self.ax.set_ylim(-300, 300)
        self.ax.set_ylabel("Y")
        self.ax.set_zlim(100, 600)
        self.ax.set_zlabel("Z")

        self.handle_0 = self.ax.quiver(1, 1, 1, 0.2, 0.3, 0.4, length=0.0, color="red", pivot="tip")
        self.handle_0_text = self.ax.text3D(0, 0, 0, "")
        self.handle_1 = self.ax.quiver(0, 0, 0, 0, 0, 0, length=0.0, color="blue", pivot="tip")
        self.handle_1_text = self.ax.text3D(0, 0, 0, "")
        self.handle_2 = self.ax.quiver(0, 0, 0, 0, 0, 0, length=0.0, color="green", pivot="tip")
        self.handle_2_text = self.ax.text3D(0, 0, 0, "")
        self.handle_3 = self.ax.quiver(0, 0, 0, 0, 0, 0, length=0.0, color="black", pivot="tip")
        self.handle_3_text = self.ax.text3D(0, 0, 0, "")
        self.safe_handle = self.ax.quiver(0, 0, 0, 0, 0, 0, length=0.0, pivot="tip")
        self.safe_handle_text = self.ax.text3D(0, 0, 0, "")
        self.scatty = self.ax.scatter(0, 0, 0, s=0)

        # Frame erstellen + Koordinatensystem anzeigen
        self.navigationCanvas = FigureCanvasTkAgg(self.fig, self.lowerFrameRight)
        #self.navigationCanvas.show()
        self.navigationCanvas.draw()
        self.navigationCanvas.get_tk_widget().grid(row=0, column=0, pady=8, sticky=tk.NSEW)


class UltraVisController:

    def __init__(self):

        


        # global recieve
        # recieve = True

        # global box_list
        # box_list = [box(size=vector(0, 0, 0), pos=vector(0, 0, 0), color=color.red),
        #             box(size=vector(0, 0, 0), pos=vector(0, 0, 0), color=color.blue),
        #             box(size=vector(0, 0, 0), pos=vector(0, 0, 0), color=color.cyan),
        #             box(size=vector(0, 0, 0), pos=vector(0, 0, 0), color=color.green)]

        # Definition der seriellen Schnittstelle
        # self.safed_handle_strings = []
        # self.safe_handle_string = []
        self.handle_0_ID = None
        self.handle_0_Q0 = None
        self.handle_0_Qx = None
        self.handle_0_Qy = None
        self.handle_0_Qz = None
        self.handle_0_Tx = None
        self.handle_0_Ty = None
        self.handle_0_Tz = None
        self.handle_0_Err = None

        self.safe_handle_0_ID = None
        self.safe_handle_0_Q0 = None
        self.safe_handle_0_Qx = None
        self.safe_handle_0_Qy = None
        self.safe_handle_0_Qz = None
        self.safe_handle_0_Tx = None
        self.safe_handle_0_Ty = None
        self.safe_handle_0_Tz = None
        self.safe_handle_0_Err = None

        self.handle_1_ID = None
        self.handle_1_Q0 = None
        self.handle_1_Qx = None
        self.handle_1_Qy = None
        self.handle_1_Qz = None
        self.handle_1_Tx = None
        self.handle_1_Ty = None
        self.handle_1_Tz = None
        self.handle_1_Err = None

        self.handle_2_ID = None
        self.handle_2_Q0 = None
        self.handle_2_Qx = None
        self.handle_2_Qy = None
        self.handle_2_Qz = None
        self.handle_2_Tx = None
        self.handle_2_Ty = None
        self.handle_2_Tz = None
        self.handle_2_Err = None

        self.handle_3_ID = None
        self.handle_3_Q0 = None
        self.handle_3_Qx = None
        self.handle_3_Qy = None
        self.handle_3_Qz = None
        self.handle_3_Tx = None
        self.handle_3_Ty = None
        self.handle_3_Tz = None
        self.handle_3_Err = None

        self.ser = serial.Serial()
        self.ser.port = 'COM5'
        self.ser.baudrate = 9600
        self.ser.parity = serial.PARITY_NONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.xonxoff = False

        self.ser.open()
        self.root = tk.Tk()
        self.root.geometry(self.centerWindow(self.root, 850, 460))

        # Create Model
        self.ultraVisModel = UltraVisModel()

        # Create View
        self.ultraVisView = UltraVisView(self.root)

        # Configure the buttons
        self.ultraVisView.buttonReset.config(command=self.onResetSystemClicked)
        self.ultraVisView.buttonInitSystem.config(command=self.onInitSystemClicked)
        self.ultraVisView.buttonStartStopTracking.config(command=self.onStartStopTrackingClicked)
        self.ultraVisView.buttonSaveRefPosition.config(command=self.onSaveRefPosClicked)

        # Defining a closing method (when the user clicks on X in the top right corner)
        def on_closing():
            self.ultraVisView.lmain.after_cancel(self.ultraVisView.Capture_FrameGrabber)
            self.ser.write(b'TSTOP \r')
            self.readSerial()
            self.ser.close()
            self.root.quit()
            self.root.destroy()

        # Connect the closing method with the root window
        self.root.protocol("WM_DELETE_WINDOW", on_closing)

    def run(self):
        self.root.mainloop()

    def centerWindow(self, toplevel, width, height):
        toplevel.update_idletasks()
        w = toplevel.winfo_screenwidth()
        h = toplevel.winfo_screenheight()
        size = (width, height)
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        return ("%dx%d+%d+%d" % (size + (x, y)))

    def log(self, logMsg):
        print(str(logMsg))

    def log_err(self, logMsg):
        print("Error" + str(logMsg))

    def onResetSystemClicked(self):
        print("Reset")
        self.ser.send_break()  # zwingend n�tig

    def onInitSystemClicked(self):
        print("Init")
        # ser.send_break()  # zwingend n�tig
        thread.start_new_thread(self.InitSystem, ())

    def InitSystem(self):
        self.ser.write(b'RESET \r')
        time.sleep(1)
        self.ser.write(b'INIT \r')
        time.sleep(1)
        self.readSerial()
        self.activateHandles()
        thread.exit()


    def onStartStopTrackingClicked(self):
        global firstClick
        
        if firstClick == False:
            print("Start Tracking")
            #global firstClick
            firstClick = True
            # print(firstClick)
            thread.start_new(self.StartTracking, ())
        else:
            print("Stop Tracking")
            #global firstClick
            firstClick = False
            # print(firstClick)
            self.ser.write(b'TSTOP \r')
            self.readSerial()

    def StartTracking(self):
        self.ser.write(b'TSTART 40\r')
        self.readSerial()
        time.sleep(1)
        self.transformationData()
        self.readSerial()

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

    def transformationData(self):
        global firstTime
        global firstClick
        # recs = 0
        sent = False
        stop = False

        # status.put('running')

        while firstClick:
            # print("firstClick")
            # while not stop:
            # com = command.get()
            # if com == 'stop':
            #     stop = True
            #     break
            # if com == 'point':
            #     #todo letzten punkt in points speichern
            #     pass
            if sent:
                # print("if send true")
                try:
                    # print("vor dem if")
                    if self.ser.in_waiting > 0:
                        # test_out = ser.read_all()
                        test_out = self.readSerial_Return()
                        if firstTime == True:
                            #global firstTime
                            firstTime = False
                            # print(firstTime)

                            sent = False
                        else:
                            #global firstTime
                            firstTime = True
                            # print(firstTime)
                            # print("Type: " + str(type(test_out)) + " | " + str(test_out))

                            self.safe_met_handle_string(test_out)

                            # ser.reset_input_buffer()
                            sent = False

                    else:
                        # print("NO Data in ser")
                        pass
                except Exception as e:
                    print(str(e))
                # time.sleep(0.1)
            else:
                self.ser.write(b'TX 0001\r')
                sent = True
        # status.put('stopped')
        thread.exit()

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

    def insert_dash(self, string, index):
        return string[:index] + '.' + string[index:]

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

    def Navigation(self):
        if self.safe_handle_0_ID is not None:
            if self.safe_handle_0_Tx + 50.0 < self.handle_0_Tx:
                if self.ultraVisView.x_achse.winfo_children()[0] != self.ultraVisView.x_links_rot_label:
                    # print("hallo")
                    self.ultraVisView.x_achse.winfo_children()[0].pack_forget()
                    self.ultraVisView.x_links_rot_label.pack()
                # if self.ultraVisView.x_achseImage.cget("image") is not self.ultraVisView.x_links_rot:
                #     self.ultraVisView.x_achseImage.configure(image=self.ultraVisView.x_links_rot)
                    # print("Pfeil rot zeigt nach links")
            elif self.safe_handle_0_Tx + 5.0 < self.handle_0_Tx:
                if self.ultraVisView.x_achse.winfo_children()[0] != self.ultraVisView.x_links_orange_label:
                    # print("sina")
                    self.ultraVisView.x_achse.winfo_children()[0].pack_forget()
                    self.ultraVisView.x_links_orange_label.pack()
                # if self.ultraVisView.x_achseImage.cget("image") is not self.ultraVisView.x_links_orange:
                #     self.ultraVisView.x_achseImage.configure(image=self.ultraVisView.x_links_orange)
                    # print("Pfeil orange zeigt nach links")
            elif self.safe_handle_0_Tx - 50.0 > self.handle_0_Tx:
                if self.ultraVisView.x_achse.winfo_children()[0] != self.ultraVisView.x_rechts_rot_label:
                    # print("wie")
                    self.ultraVisView.x_achse.winfo_children()[0].pack_forget()
                    self.ultraVisView.x_rechts_rot_label.pack()
                # if self.ultraVisView.x_achseImage.cget("image") is not self.ultraVisView.x_rechts_rot:
                #     self.ultraVisView.x_achseImage.configure(image=self.ultraVisView.x_rechts_rot)
                    # print("Pfeil rot zeigt nach rechts")
            elif self.safe_handle_0_Tx - 5.0 > self.handle_0_Tx:
                if self.ultraVisView.x_achse.winfo_children()[0] != self.ultraVisView.x_links_orange_label:
                    # print("gehts")
                    self.ultraVisView.x_achse.winfo_children()[0].pack_forget()
                    self.ultraVisView.x_links_orange_label.pack()
                # if self.ultraVisView.x_achseImage.cget("image") is not self.ultraVisView.x_rechts_orange:
                #     self.ultraVisView.x_achseImage.configure(image=self.ultraVisView.x_rechts_orange)
                    # print("Pfeil orange zeigt nach rechts")
            else:
                if self.ultraVisView.x_achse.winfo_children()[0] != self.ultraVisView.x_ziel_label:
                    # print("?")
                    self.ultraVisView.x_achse.winfo_children()[0].pack_forget()
                    # print("komm hier her")
                    self.ultraVisView.x_ziel_label.grid(row=0, column=0)
                    # print("??")
               # if self.ultraVisView.x_achseImage.cget("image") is not self.ultraVisView.ziel:
                #    self.ultraVisView.x_achseImage.configure(image=self.ultraVisView.ziel)
                 #   print("Ziel erreicht f�r x")

            if self.safe_handle_0_Ty + 50.0 < self.handle_0_Ty:
                if self.ultraVisView.y_achseImage.cget("image") is not self.ultraVisView.y_vorne_rot:
                    self.ultraVisView.y_achseImage.configure(image=self.ultraVisView.y_vorne_rot)
                    # print("Pfeil rot zeigt nach vorne")
            elif self.safe_handle_0_Ty + 5.0 < self.handle_0_Ty:
                if self.ultraVisView.y_achseImage.cget("image") is not self.ultraVisView.y_vorne_orange:
                    self.ultraVisView.y_achseImage.configure(image=self.ultraVisView.y_vorne_orange)
                    # print("Pfeil orange zeigt nach vorne")
            elif self.safe_handle_0_Ty - 50.0 > self.handle_0_Ty:
                if self.ultraVisView.y_achseImage.cget("image") is not self.ultraVisView.y_hinten_rot:
                    self.ultraVisView.y_achseImage.configure(image=self.ultraVisView.y_hinten_rot)
                    # print("Pfeil rot zeigt nach hinten")
            elif (self.safe_handle_0_Ty - 5.0) > self.handle_0_Ty:
                if self.ultraVisView.y_achseImage.cget("image") is not self.ultraVisView.y_hinten_orange:
                    self.ultraVisView.y_achseImage.configure(image=self.ultraVisView.y_hinten_orange)
                    # print("Pfeil orange zeigt nach hinten")
            else:
                if self.ultraVisView.y_achseImage.cget("image") is not self.ultraVisView.ziel:
                    self.ultraVisView.y_achseImage.configure(image=self.ultraVisView.ziel)
                    # print("Ziel erreicht f�r y")

            if self.safe_handle_0_Tz + 50.0 < self.handle_0_Tz:
                if self.ultraVisView.z_achseImage.cget("image") is not self.ultraVisView.z_unten_rot:
                    self.ultraVisView.z_achseImage.configure(image=self.ultraVisView.z_unten_rot)
                    # print("Pfeil rot zeigt nach oben")
            elif self.safe_handle_0_Tz + 5.0 < self.handle_0_Tz:
                if self.ultraVisView.z_achseImage.cget("image") is not self.ultraVisView.z_unten_orange:
                    self.ultraVisView.z_achseImage.configure(image=self.ultraVisView.z_unten_orange)
                    # print("Pfeil orange zeigt nach oben")
            elif self.safe_handle_0_Tz - 50.0 > self.handle_0_Tz:
                if self.ultraVisView.z_achseImage.cget("image") is not self.ultraVisView.z_oben_rot:
                    self.ultraVisView.z_achseImage.configure(image=self.ultraVisView.z_oben_rot)
                    # print("Pfeil rot zeigt nach unten")
            elif self.safe_handle_0_Tz - 5.0 > self.handle_0_Tz:
                if self.ultraVisView.z_achseImage.cget("image") is not self.ultraVisView.z_oben_orange:
                    self.ultraVisView.z_achseImage.configure(image=self.ultraVisView.z_oben_orange)
                    # print("Pfeil orange zeigt nach unten")
            else:
                if self.ultraVisView.z_achseImage.cget("image") is not self.ultraVisView.ziel:
                    self.ultraVisView.z_achseImage.configure(image=self.ultraVisView.ziel)
                    # print("Ziel erreicht f�r z")

            if self.safe_handle_0_Qx + 0.5 < self.handle_0_Qx:
                if self.ultraVisView.x_rotationImage.cget("image") is not self.ultraVisView.x_achse_kippen_links_rot:
                    self.ultraVisView.x_rotationImage.configure(image=self.ultraVisView.x_achse_kippen_links_rot)
                    # print("Pfeil rot rotiert um x-achse nach links")
            elif self.safe_handle_0_Qx + 0.1 < self.handle_0_Qx:
                if self.ultraVisView.x_rotationImage.cget("image") is not self.ultraVisView.x_achse_kippen_links_orange:
                    self.ultraVisView.x_rotationImage.configure(image=self.ultraVisView.x_achse_kippen_links_orange)
                    # print("Pfeil orange rotiert um x-achse nach links")
            elif self.safe_handle_0_Qx - 0.5 > self.handle_0_Qx:
                if self.ultraVisView.x_rotationImage.cget("image") is not self.ultraVisView.x_achse_kippen_rechts_rot:
                    self.ultraVisView.x_rotationImage.configure(image=self.ultraVisView.x_achse_kippen_rechts_rot)
                    # print("Pfeil rot rotiert um x-achse nach rechts")
            elif self.safe_handle_0_Qx - 0.1 > self.handle_0_Qx:
                if self.ultraVisView.x_rotationImage.cget("image") is not self.ultraVisView.x_achse_kippen_rechts_orange:
                    self.ultraVisView.x_rotationImage.configure(image=self.ultraVisView.x_achse_kippen_rechts_orange)
                    # print("Pfeil orange rotiert um x-achse nach rechts")
            else:
                if self.ultraVisView.x_rotationImage.cget("image") is not self.ultraVisView.ziel:
                    self.ultraVisView.x_rotationImage.configure(image=self.ultraVisView.ziel)
                    # print("Ziel erreicht f�r x-Rotation")

            if self.safe_handle_0_Qy + 0.5 < self.handle_0_Qy:
                if self.ultraVisView.y_rotationImage.cget("image") is not self.ultraVisView.y_achse_kippen_links_rot:
                    self.ultraVisView.y_rotationImage.configure(image=self.ultraVisView.y_achse_kippen_links_rot)
                    # print("Pfeil rot rotiert um y-achse nach links")
            elif self.safe_handle_0_Qy + 0.1 < self.handle_0_Qy:
                if self.ultraVisView.y_rotationImage.cget("image") is not self.ultraVisView.y_achse_kippen_links_orange:
                    self.ultraVisView.y_rotationImage.configure(image=self.ultraVisView.y_achse_kippen_links_orange)
                    # print("Pfeil orange rotiert um y-achse nach links")
            elif self.safe_handle_0_Qy - 0.5 > self.handle_0_Qy:
                if self.ultraVisView.y_rotationImage.cget("image") is not self.ultraVisView.y_achse_kippen_rechts_rot:
                    self.ultraVisView.y_rotationImage.configure(image=self.ultraVisView.y_achse_kippen_rechts_rot)
                    # print("Pfeil rot rotiert um y-achse nach rechts")
            elif self.safe_handle_0_Qy - 0.1 > self.handle_0_Qy:
                if self.ultraVisView.y_rotationImage.cget("image") is not self.ultraVisView.y_achse_kippen_rechts_orange:
                    self.ultraVisView.y_rotationImage.configure(image=self.ultraVisView.y_achse_kippen_rechts_orange)
                    # print("Pfeil orange rotiert um y-achse nach rechts")
            else:
                if self.ultraVisView.y_rotationImage.cget("image") is not self.ultraVisView.ziel:
                    self.ultraVisView.y_rotationImage.configure(image=self.ultraVisView.ziel)
                    # print("Ziel erreicht f�r y-Rotation")

            if self.safe_handle_0_Qz + 0.5 < self.handle_0_Qz:
                if self.ultraVisView.z_rotationImage.cget("image") is not self.ultraVisView.z_achse_kippen_links_rot:
                    self.ultraVisView.z_rotationImage.configure(image=self.ultraVisView.z_achse_kippen_links_rot)
                    # print("Pfeil rot rotiert um z-achse nach links")
            elif self.safe_handle_0_Qz + 0.1 < self.handle_0_Qz:
                if self.ultraVisView.z_rotationImage.cget("image") is not self.ultraVisView.z_achse_kippen_links_orange:
                    self.ultraVisView.z_rotationImage.configure(image=self.ultraVisView.z_achse_kippen_links_orange)
                    # print("Pfeil orange rotiert um z-achse nach links")
            elif self.safe_handle_0_Qz - 0.5 > self.handle_0_Qz:
                if self.ultraVisView.z_rotationImage.cget("image") is not self.ultraVisView.z_achse_kippen_rechts_rot:
                    self.ultraVisView.z_rotationImage.configure(image=self.ultraVisView.z_achse_kippen_rechts_rot)
                    # print("Pfeil rot rotiert um z-achse nach rechts")
            elif self.safe_handle_0_Qz - 0.1 > self.handle_0_Qz:
                if self.ultraVisView.z_rotationImage.cget("image") is not self.ultraVisView.z_achse_kippen_rechts_orange:
                    self.ultraVisView.z_rotationImage.configure(image=self.ultraVisView.z_achse_kippen_rechts_orange)
                    # print("Pfeil orange rotiert um z-achse nach rechts")
            else:
                if self.ultraVisView.z_rotationImage.cget("image") is not self.ultraVisView.ziel:
                    self.ultraVisView.z_rotationImage.configure(image=self.ultraVisView.ziel)
                    # print("Ziel erreicht f�r z-Rotation")

            if self.safe_handle_0_Q0 + 0.5 < self.handle_0_Q0:
                if self.ultraVisView.self_rotationImage.cget("image") is not self.ultraVisView.self_rot_links_rot:
                    self.ultraVisView.self_rotationImage.configure(image=self.ultraVisView.self_rot_links_rot)
                    # print("Pfeil rot rotiert nach links um sich selbst")
            elif self.safe_handle_0_Q0 + 0.1 < self.handle_0_Q0:
                if self.ultraVisView.self_rotationImage.cget("image") is not self.ultraVisView.self_rot_links_orange:
                    self.ultraVisView.self_rotationImage.configure(image=self.ultraVisView.self_rot_links_orange)
                    # print("Pfeil orange rotiert nach links um sich selbst")
            elif self.safe_handle_0_Q0 - 0.5 > self.handle_0_Q0:
                if self.ultraVisView.self_rotationImage.cget("image") is not self.ultraVisView.self_rot_rechts_rot:
                    self.ultraVisView.self_rotationImage.configure(image=self.ultraVisView.self_rot_rechts_rot)
                    # print("Pfeil rot rotiert nach rechts um sich selbst")
            elif self.safe_handle_0_Q0 - 0.1 > self.handle_0_Q0:
                if self.ultraVisView.self_rotationImage.cget("image") is not self.ultraVisView.self_rot_rechts_orange:
                    self.ultraVisView.self_rotationImage.configure(image=self.ultraVisView.self_rot_rechts_orange)
                    # print("Pfeil orange rotiert nach rechts um sich selbst")
            else:
                if self.ultraVisView.self_rotationImage.cget("image") is not self.ultraVisView.ziel:
                    self.ultraVisView.self_rotationImage.configure(image=self.ultraVisView.ziel)
                    # print("Ziel erreicht f�r Q0")

        # self.ultraVisView.upperFrameRightRight.after(10, self.Navigation)

    def koordinatenSystem(self):
        if self.handle_0_ID is not None:
            self.ultraVisView.handle_0.remove()
            self.ultraVisView.handle_0 = self.ultraVisView.ax.quiver(self.handle_0_Tx, self.handle_0_Ty,
                                                                     self.handle_0_Tz, self.handle_0_Qx,
                                                                     self.handle_0_Qy, self.handle_0_Qz,
                                                                     length=150.0, color="blue",
                                                                     pivot="tip")
            self.ultraVisView.handle_0_text.remove()
            self.ultraVisView.handle_0_text = self.ultraVisView.ax.text(self.handle_0_Tx+10, self.handle_0_Ty,
                                                                        self.handle_0_Tz, "Sensor 1", color="blue")
        if self.handle_1_ID is not None:
            self.ultraVisView.handle_1.remove()
            self.ultraVisView.handle_1 = self.ultraVisView.ax.quiver(self.handle_1_Tx, self.handle_1_Ty,
                                                                     self.handle_1_Tz, self.handle_1_Qx,
                                                                     self.handle_1_Qy, self.handle_1_Qz,
                                                                     length=150.0, color="red",
                                                                     pivot="tip")
            self.ultraVisView.handle_1_text.remove()
            self.ultraVisView.handle_1_text = self.ultraVisView.ax.text(self.handle_1_Tx + 10, self.handle_1_Ty,
                                                                        self.handle_1_Tz, "Sensor 2", color="red")
        if self.handle_2_ID is not None:
            self.ultraVisView.handle_2.remove()
            self.ultraVisView.handle_2 = self.ultraVisView.ax.quiver(self.handle_2_Tx, self.handle_2_Ty,
                                                                     self.handle_2_Tz, self.handle_2_Qx,
                                                                     self.handle_2_Qy, self.handle_2_Qz,
                                                                     length=150.0, color="green",
                                                                     pivot="tip")
            self.ultraVisView.handle_2_text.remove()
            self.ultraVisView.handle_2_text = self.ultraVisView.ax.text(self.handle_2_Tx + 10, self.handle_2_Ty,
                                                                        self.handle_2_Tz, "Sensor 3", color="green")
        if self.handle_3_ID is not None:
            self.ultraVisView.handle_3.remove()
            self.ultraVisView.handle_3 = self.ultraVisView.ax.quiver(self.handle_3_Tx, self.handle_3_Ty,
                                                                     self.handle_3_Tz, self.handle_3_Qx,
                                                                     self.handle_3_Qy, self.handle_3_Qz,
                                                                     length=150.0, color="purple",
                                                                     pivot="tip")
            self.ultraVisView.handle_3_text.remove()
            self.ultraVisView.handle_3_text = self.ultraVisView.ax.text(self.handle_3_Tx + 10, self.handle_3_Ty,
                                                                        self.handle_3_Tz, "Sensor 4", color="purple")
        if self.safe_handle_0_Tx is not None:
            self.ultraVisView.safe_handle.remove()
            self.ultraVisView.safe_handle = self.ultraVisView.ax.quiver(self.safe_handle_0_Tx, self.safe_handle_0_Ty,
                                                                        self.safe_handle_0_Tz, self.safe_handle_0_Qx,
                                                                        self.safe_handle_0_Qy, self.safe_handle_0_Qz,
                                                                        length=150.0, pivot="tip",
                                                                        color="black")
            self.ultraVisView.safe_handle_text.remove()
            self.ultraVisView.safe_handle_text = self.ultraVisView.ax.text(self.safe_handle_0_Tx + 10,
                                                                           self.safe_handle_0_Ty,
                                                                           self.safe_handle_0_Tz, "Ref", color="black")
            self.ultraVisView.scatty.remove()
            self.ultraVisView.scatty = self.ultraVisView.ax.scatter(self.safe_handle_0_Tx, self.safe_handle_0_Ty,
                                                                    self.safe_handle_0_Tz, s=10, c="black")

        self.ultraVisView.navigationCanvas.draw()

        # self.Navigation()

        # plt.show()
    # def koordinatenSystem(self):
    #     scene = display(width=600, height=600, center=(0, 300, 0), forward=(2, 0, 2))
    #     mybox = box(pos=(0, -17, 0), length=400, height=34, width=600, color=color.white, opacity=1)
    #     # Text_Aurora = text(text='AURORA', pos=vector(0, 0, 0), color=color.blue)
    #     # Einzeichung des Koordinatensystems
    #     xaxis = arrow(pos=(0, 0, 0), axis=(220, 0, 0), shaftwidth=1, headwidth=10, headlength=20,
    #                   color=color.magenta)
    #     xaxis = arrow(pos=(0, 0, 0), axis=(-220, 0, 0), shaftwidth=1, headwidth=10, headlength=20,
    #                   color=color.magenta)
    #     zaxis = arrow(pos=(0, 0, 0), axis=(0, 610, 0), shaftwidth=1, headwidth=10, headlength=20,
    #                   color=color.green)
    #     yaxis = arrow(pos=(0, 0, 0), axis=(0, 0, 320), shaftwidth=1, headwidth=10, headlength=20,
    #                   color=color.blue)
    #     yaxis = arrow(pos=(0, 0, 0), axis=(0, 0, -320), shaftwidth=1, headwidth=10, headlength=20,
    #                   color=color.blue)
    #     img = Image.new(scene)
    #     imgtk = ImageTk.PhotoImage(image=img)
    #     self.ultraVisView.sina.image = imgtk
    #     self.ultraVisView.sina.configure(image=imgtk)
    #     self.ultraVisView.sina.after(10, self.koordinatenSystem())

    # mybox = box(pos=vector(0, -17, 0), length=400, height=34, width=600, color=color.white, opacity=1)
    # # Text_Aurora = text(text='AURORA', pos=vector(0, 0, 0), color=color.blue)
    # # Einzeichung des Koordinatensystems
    # xaxis = arrow(pos=vector(0, 0, 0), axis=vector(220, 0, 0), shaftwidth=1, headwidth=10, headlength=20,
    #               color=color.magenta)
    # xaxis = arrow(pos=vector(0, 0, 0), axis=vector(-220, 0, 0), shaftwidth=1, headwidth=10, headlength=20,
    #               color=color.magenta)
    # zaxis = arrow(pos=vector(0, 0, 0), axis=vector(0, 610, 0), shaftwidth=1, headwidth=10, headlength=20,
    #               color=color.green)
    # yaxis = arrow(pos=vector(0, 0, 0), axis=vector(0, 0, 320), shaftwidth=1, headwidth=10, headlength=20,
    #               color=color.blue)
    # yaxis = arrow(pos=vector(0, 0, 0), axis=vector(0, 0, -320), shaftwidth=1, headwidth=10, headlength=20,
    #               color=color.blue)

    # self.ultraVisView.rmain.scene = scene

    # # Bildgroe�e definieren + Ausrichtung des Koordinatensystems
    # scene.height = 600
    # scene.width = 600
    # scene.center = vector(0, 300, 0)
    # scene.forward = vector(2, 0, 2)
