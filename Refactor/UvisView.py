# -*- coding: latin-1 -*-
from __future__ import print_function
# from visual import *
import tkinter as tk
from tkinter import ttk
from cv2 import cv2
from PIL import Image
from PIL import ImageTk
import time

import matplotlib
matplotlib.use('Tkagg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


global BUTTON_WIDTH
BUTTON_WIDTH = 25

class UltraVisView(tk.Frame):


    def __init__(self, master):
        super().__init__(master)
        self.start_time = time.time()
        self.master = master
        self.master.title("TTR: Track To Reference")
        self.master.minsize(600,350)
        self.master.geometry(self.centerWindow(self.master, 1000, 600))
        #self.master.wm_state('zoomed')
        self.master.focus_force()


        self.tabControl = ttk.Notebook(self.master)
        self.initImages()
        self.buildTab1()
        self.buildTab2()       

        self.tabControl.add(self.t1_mainFrame, text='Navigation')
        self.tabControl.add(self.t2_debugFrame, text='Debugging')
        
        self.tabControl.pack(fill=tk.BOTH, expand=tk.TRUE)

        #Selecting Tabs
        #self.tabControl.select(self.t2_debugFrame)
    
    def centerWindow(self, toplevel, width, height):

        toplevel.update_idletasks()
        w = toplevel.winfo_screenwidth()
        h = toplevel.winfo_screenheight()
        size = (width, height)
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        return ("%dx%d+%d+%d" % (size + (x, y)))

    
    def buildTab1(self):
        #Tab 1 Two Column, Menu Column and App Column
        self.t1_mainFrame = tk.Frame(self.tabControl)
        self.t1_mainFrame.rowconfigure(0, weight=98)
        self.t1_mainFrame.rowconfigure(1, weight=2, minsize=30)
        self.t1_mainFrame.columnconfigure(0, weight=15, uniform=1)
        self.t1_mainFrame.columnconfigure(1, weight=85, uniform=1)

        self.leftFrame = tk.Frame(self.t1_mainFrame, bg="#196666")
        self.rightFrame = tk.Frame(self.t1_mainFrame, bg = "#196666")
        self.rightFrame.rowconfigure(0, weight=90, uniform=1)
        self.rightFrame.rowconfigure(1, weight=10, uniform=1)
        self.rightFrame.columnconfigure(0,weight=1)
        self.bottomFrame = tk.Frame(self.t1_mainFrame, bg="#ccccff")

        self.leftFrame.grid(row=0, column=0, pady=4, padx=4, sticky=tk.NSEW)
        self.rightFrame.grid(row=0, column=1, pady=4, padx=4, sticky=tk.NSEW)
        self.bottomFrame.grid(row=1,column=0, columnspan=2,pady=(0,0), padx=4, sticky=tk.NSEW)

        self.buildMenuFrame(self.leftFrame)
        self.buildAppFrame(self.rightFrame)
        self.buildActionFrame(self.bottomFrame)
        #
        

        self.t1_mainFrame.pack(fill=tk.BOTH, expand=tk.TRUE)

    def buildMenuFrame(self,lFrame):

        self.MenuTitleLabel = tk.Label(lFrame, text="Menu")
            
        self.saveBut = tk.Button(lFrame)  
        self.saveBut["text"] = "Aufnahme speichern"
        #self.readBut["command"] = 
        
        self.cancelBut = tk.Button(lFrame)  
        self.cancelBut["text"] = "Abbrechen"
        #self.readBut["command"] = 

        self.MenuTitleLabel.pack(side=tk.TOP, pady=(10,0),fill="both")
        self.saveBut.pack(side=tk.TOP, pady=(2, 0),padx=(10),fill="both")
        self.cancelBut.pack(side=tk.TOP, pady=(0, 0),padx=(10), fill="both")   

    def buildAppFrame(self,rFrame):

        self.appFrame = tk.Frame(rFrame,bg="black")
        
        #2x2 Matrix of Application frame
        self.appFrame.rowconfigure(0, weight=1, uniform=1)
        self.appFrame.rowconfigure(1, weight=1, uniform=1)
        self.appFrame.columnconfigure(0, weight=1, uniform=1)
        self.appFrame.columnconfigure(1, weight=1, uniform=1)
        
        #Order of the US Frame, Saved Image and Navigationframe
        self.USImgFrame = tk.Frame(self.appFrame,bg="green")
        self.USImgFrame.rowconfigure(0, weight=1)
        self.USImgFrame.columnconfigure(0, weight=1)
        self.savedImgFrame = tk.Frame(self.appFrame,bg="green")
        self.savedImgFrame.rowconfigure(0, weight=1)
        self.savedImgFrame.columnconfigure(0, weight=1)
        self.navFrame = tk.Frame(self.appFrame,bg="yellow")
        self.navFrame.rowconfigure(0, weight=1)
        self.navFrame.columnconfigure(0, weight=1)

        self.USImgFrame.grid(row=0, column=0, padx=5, pady=2,sticky=tk.NSEW )
        self.savedImgFrame.grid(row=1, column=0, padx=5, pady=2, sticky=tk.NSEW)
        self.navFrame.grid(row=0, column=1, rowspan=2, padx=5, pady=2, sticky=tk.NSEW)

        #Ultrasoundimage Content
        self.USImgLabel = tk.Label(self.USImgFrame)
        self.USImgLabel["text"] = "INITIALIZING VIDEOINPUT"
        self.USImgLabel.grid(row=0, column=0,sticky=tk.NSEW)
        self.USImgLabel.grid_propagate(0)

        self.cap = cv2.VideoCapture(0)
        self.Capture_FrameGrabber()

        #Saved Image Content
        self.savedImgLabel = tk.Label(self.savedImgFrame)
        self.savedImgLabel["text"] = "Saved Image"
        self.savedImgLabel.grid(row=0, column=0,sticky=tk.NSEW)
        
        #Navigation Frame Content
        self.navLabel = tk.Label(self.navFrame)
        self.navLabel["text"] = "Navigtion GUI"
        self.navLabel.grid(row=0, column=0,sticky=tk.NSEW)

        self.appFrame.grid(row=0, pady=8, padx=8, sticky=tk.NSEW)


        self.galleryFrame = tk.Frame(rFrame, bg="#99ffcc")
        self.galleryFrame.grid(row=1, pady=8, padx=8, sticky=tk.NSEW)

        self.galleryLb = tk.Label(self.galleryFrame, text="a gallery")
        self.galleryLb.pack()

    def buildActionFrame(self,bFrame):
            
        self.backBut = tk.Button(bFrame)  
        self.backBut["text"] = "Zurueck"
        self.backBut["width"] = 20
        #self.backBut["command"] = 
        
        self.nextBut = tk.Button(bFrame)  
        self.nextBut["text"] = "Weiter"
        self.nextBut["width"] = 20
        #self.nextBut["command"] = 

       
        self.backBut.pack(side=tk.LEFT,padx=(0),pady=0,fill="both")
        self.nextBut.pack(side=tk.RIGHT,padx=(0),pady=0, fill="both")

    def Capture_FrameGrabber(self):
        _isFirstCapture = True
        _, frame = self.cap.read()

        if frame is None and _isFirstCapture: 
            print("Empty Frame - No Device was found")
            self.USImgLabel["text"] = "EMPTY FRAME \n No Device was found"
            self.USImgLabel.after(10000, self.Capture_FrameGrabber)
            return

        if ((time.time() - self.start_time) < 2):
            self.USImgLabel.after(500, self.Capture_FrameGrabber)
            return

        self.frame = cv2.flip(frame, 1)
        cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        width, height = img.size

        #Normalize Ratio of Pictures, Resize appropriatly
        img_ratio = height / width
        frame_ratio = self.USImgFrame.winfo_height()/self.USImgFrame.winfo_width()
        if (frame_ratio >= img_ratio):
            new_width = (self.USImgFrame.winfo_width()-5) 
            new_height = height / width * new_width
        else:
            new_height = (self.USImgFrame.winfo_height()-5)
            new_width = width / height * new_height
            
        img = img.resize((int(new_width), int(new_height)), Image.ANTIALIAS)

        imgtk = ImageTk.PhotoImage(image=img)

        self.USImgLabel.imgtk = imgtk
        self.USImgLabel.configure(image=imgtk)
        self.USImgLabel.after(10, self.Capture_FrameGrabber)

        # Slider window (slider controls stage position)
        # self.sliderFrame = tk.Frame(self.upperFrameLeft, width=600, height=100)
        # self.sliderFrame.grid(row=600, column=0, padx=10, pady=2)

    def buildTab2(self):
        #Tab2
        self.t2_debugFrame = tk.Frame(self.tabControl, bg="grey")
        self.t2_debugFrame.pack(fill=tk.BOTH, expand=tk.TRUE)


    '''
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

    
        
        
        self.buildCoordinatesystem()

    def buildCoordinatesystem(self):

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

    '''

    def initImages(self):

        self.imgdir = "D:\\Nam\\Docs\\Uni\\Master Projekt\\Track To Reference\\WP\\TTRP\\img\\"
        self.notfoundimg = self.imgdir+"not-found-image.jpg"

        # Bilder f�r x-Achse
        self.x_links_orange = self.getTKImage("x-links-orange.jpg")
        self.x_links_rot = self.getTKImage("x-links-rot.jpg")
        self.x_rechts_orange = self.getTKImage("x-rechts-orange.jpg")
        self.x_rechts_rot = self.getTKImage("x-rechts-rot.jpg")
    

        #Bilder f�r Rotation auf x-Achse
        self.x_achse_kippen_links_orange = self.getTKImage("x-achse-kippen-links-orange.jpg")
        self.x_achse_kippen_links_rot = self.getTKImage("x-achse-kippen-links-rot.jpg")
        self.x_achse_kippen_rechts_orange = self.getTKImage("x-achse-kippen-rechts-orange.jpg")
        self.x_achse_kippen_rechts_rot = self.getTKImage("x-achse-kippen-rechts-rot.jpg")

        #Bilder f�r y-Achse
        self.y_vorne_orange = self.getTKImage("y-vorne-orange.jpg")
        self.y_vorne_rot = self.getTKImage("y-vorne-rot.jpg")
        self.y_hinten_orange = self.getTKImage("y-hinten-orange.jpg")
        self.y_hinten_rot = self.getTKImage("y-hinten-rot.jpg")

        # Bilder f�r Rotation auf y-Achse
        self.y_achse_kippen_links_orange = self.getTKImage("y-achse-kippen-links-orange.jpg")
        self.y_achse_kippen_links_rot = self.getTKImage("y-achse-kippen-links-rot.jpg")
        self.y_achse_kippen_rechts_orange = self.getTKImage("y-achse-kippen-rechts-orange.jpg")
        self.y_achse_kippen_rechts_rot = self.getTKImage("y-achse-kippen-rechts-rot.jpg")

        #Bilder f�r z-Achse
        self.z_oben_orange = self.getTKImage("z-oben-orange.jpg")
        self.z_oben_rot = self.getTKImage("z-oben-rot.jpg")
        self.z_unten_orange = self.getTKImage("z-unten-orange.jpg")
        self.z_unten_rot = self.getTKImage("z-unten-rot.jpg")

        # Bilder f�r Rotation auf z-Achse
        self.z_achse_kippen_links_orange = self.getTKImage("z-achse-kippen-links-orange.jpg")
        self.z_achse_kippen_links_rot = self.getTKImage("z-achse-kippen-links-rot.jpg")
        self.z_achse_kippen_rechts_orange = self.getTKImage("z-achse-kippen-rechts-orange.jpg")
        self.z_achse_kippen_rechts_rot = self.getTKImage("z-achse-kippen-rechts-rot.jpg")

        # Bilder f�r Eigen-Rotation
        self.self_rot_links_orange = self.getTKImage("self-rot-links-orange.jpg")
        self.self_rot_links_rot = self.getTKImage("self-rot-links-rot.jpg")
        self.self_rot_rechts_orange = self.getTKImage("self-rot-rechts-orange.jpg")
        self.self_rot_rechts_rot = self.getTKImage("self-rot-rechts-rot.jpg")

        # Bild als Ziel
        self.ziel = self.getTKImage("ziel.jpg")

    def getTKImage(self,filename):
        #Opens Image and translates it to TK compatible file.
        filename = self.imgdir+filename
        
        try:
            tkimage = Image.open(filename)  

        except FileNotFoundError as err:
            print("File was no found, Err Img replace\n"+err)
            tkimage = self.notfoundimg    

        finally:
            return ImageTk.PhotoImage(tkimage)

