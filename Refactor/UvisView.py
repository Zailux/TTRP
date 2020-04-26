# -*- coding: latin-1 -*-
from __future__ import print_function
# from visual import *
import tkinter as tk
from tkinter import ttk
from cv2 import cv2
from PIL import Image
from PIL import ImageTk
import time
import logging
import functools
from datetime import datetime

import matplotlib
matplotlib.use('Tkagg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

import threading

from NavigationVisualizer import NavigationVisualizer

global BUTTON_WIDTH
BUTTON_WIDTH = 25

#   --- Decorators  --- #

#application frames will clear the self.rightframe first before displaying their gui
def clearFrame(func):
    @functools.wraps(func)
    def buildFrame_wrapper(*args, **kwargs):
        master = kwargs['master']
        if (type(master) is not tk.Frame):
            logging.critical(f"Misusage of clearFrame Decorator. Objecttype {type(master)} is incorrect.\nDebuginfo {args, kwargs}")
            return func(*args, **kwargs)
        else:
            frame = master.winfo_children()
            if (len(frame) is not 0):
                frame[0].destroy()
        return func(*args, **kwargs)
     
    return buildFrame_wrapper


class UltraVisView(tk.Frame):

    def __init__(self, master,debug_mode=False):
        super().__init__(master)
        
        self.start_time = time.time()
        self._debug = debug_mode
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
        #self.t1_mainFrame.rowconfigure(1, weight=2, minsize=30)
        self.t1_mainFrame.columnconfigure(0, weight=20, uniform=1)
        self.t1_mainFrame.columnconfigure(1, weight=80, uniform=1)

        self.leftFrame = tk.Frame(self.t1_mainFrame, bg="#196666")
        self.leftFrame.rowconfigure(0, weight=1, uniform=1)
        self.leftFrame.rowconfigure(1, weight=1, uniform=1)
        self.leftFrame.columnconfigure(0,weight=1)
        self.rightFrame = tk.Frame(self.t1_mainFrame, bg = "#196666")
        self.rightFrame.rowconfigure(0, weight=1, uniform=1)
        self.rightFrame.columnconfigure(0,weight=1)
       # self.bottomFrame = tk.Frame(self.t1_mainFrame, bg="#ccccff")

        self.leftFrame.grid(row=0, column=0, pady=4, padx=4, sticky=tk.NSEW)
        self.rightFrame.grid(row=0, column=1, pady=4, padx=4, sticky=tk.NSEW)
        #self.bottomFrame.grid(row=1,column=0, columnspan=2,pady=(0,0), padx=4, sticky=tk.NSEW)

        self.buildMenuFrame(self.leftFrame)
        self.buildDetailsFrame(self.leftFrame)
        self.buildMainScreenFrame(master=self.rightFrame)
        self.showMenu()

        self.t1_mainFrame.pack(fill=tk.BOTH, expand=tk.TRUE)

    def buildMenuFrame(self,lFrame):
        
        self.menuFrame = tk.Frame(lFrame)
        self.menuTitleLabel = tk.Label(self.menuFrame, text="Menu")

        #Main Menu
        self.newExamiBut = tk.Button(self.menuFrame)  
        self.newExamiBut["text"] = "Neue Untersuchung"
        
        self.openExamiBut = tk.Button(self.menuFrame)  
        self.openExamiBut["text"] = "Untersuchung \u00F6ffnen"
        self.openExamiBut["state"] = 'disabled'

        #Setup Menu
        self.activateHandleBut = tk.Button(self.menuFrame)  
        self.activateHandleBut["text"] = "Try Activate Handles"

        #Tracking / Recording Menu
        self.trackBut = tk.Button(self.menuFrame)  
        self.trackBut["text"] = "Start/Stop Tracking"

        self.saveRecordBut = tk.Button(self.menuFrame)  
        self.saveRecordBut["text"] = "Aufzeichnung speichern"
        
        self.cancelBut = tk.Button(self.menuFrame)  
        self.cancelBut["text"] = "Abbrechen"

        self.targetBut = tk.Button(self.menuFrame)
        self.targetBut["text"] = "Set Target"

        #Misc Buttons
        self.continueBut = tk.Button(self.menuFrame)  
        self.continueBut["text"] = "Fortfahren"

        self.backBut = tk.Button(self.menuFrame)  
        self.backBut["text"] = "Zur\u00FCck"

        self.mainMenuBut = tk.Button(self.menuFrame)
        self.mainMenuBut["text"] = "Zum Hauptmenu"
        #Command, you wanna cancel and go to main menu

        self.reinitAuaBut = tk.Button(self.menuFrame)
        self.reinitAuaBut["text"] = "Reinitialize Aurora"
        self.NOBUTTONSYET = tk.Button(self.menuFrame,text="Secret Blowup Button")
        self.calibrateBut = tk.Button(self.menuFrame,text="Calibrate")
        self.startNavBut = tk.Button(self.menuFrame,text="Start Navigation")

        self.menuTitleLabel.pack(side=tk.TOP, pady=(10,2),fill="both")

        self.menuFrame.grid(row=0, column=0,padx=2,pady=2,sticky=tk.NSEW) 
    

    def showMenu(self,menu='main'):
        MENUES = ['main','new_examination','setup','app','navigation','all_debug']

        if menu not in MENUES:
            raise ValueError(f'Try showing Menu "{menu}" which was not in {MENUES}')

        children = self.menuFrame.winfo_children()
        self.cleanMenu(children)

        menu_buttons = {
            'main': [self.newExamiBut,self.openExamiBut],
            'new_examination': [self.continueBut,self.cancelBut],
            'setup': [self.NOBUTTONSYET, self.calibrateBut, self.startNavBut],
            'app': [self.trackBut,self.saveRecordBut,self.cancelBut, self.targetBut],
            'navigation':[self.NOBUTTONSYET]
        }

        for button in menu_buttons[menu]:
            button.pack(side=tk.TOP, pady=(0, 0),padx=(10), fill="both") 

        



    def cleanMenu(self,childList):
        for child in childList:
            if (child.winfo_class() == 'Frame'):
                self.cleanMenu(child.winfo_children())
                continue

            if (child.winfo_class() in ['Button'] and child.winfo_ismapped()):
                child.pack_forget()


    def buildDetailsFrame(self,lFrame):
        
        self.detailsFrame = tk.Frame(lFrame)
        #Details soll scrollbar bekommen und deswegen soll es sich nicht anhand der slaves orientieren. 
        self.detailsFrame.grid_propagate(0)

        self.detailsTitleLabel = tk.Label(self.detailsFrame, text="Details")
        self.detailsInfoLabel = tk.Label(self.detailsFrame, text=" - ")


        self.adsfBut = tk.Button(self.detailsFrame)  
        self.adsfBut["text"] = "Start/Stop Tracking"

        self.detailsTitleLabel.pack(side=tk.TOP, pady=(10,2),fill="both")
        self.detailsInfoLabel.pack(side=tk.TOP, pady=(2,2),fill="both")

        self.detailsFrame.grid(row=1, column=0,padx=2, pady=2,sticky=tk.NSEW)

    @clearFrame
    def buildMainScreenFrame(self,master):
        self.mainscreenFrame = tk.Frame(master)
        self.mainscreenFrame.rowconfigure(0, weight=1, uniform=1)
        self.mainscreenFrame.columnconfigure(0,weight=1,uniform=1)
        self.logoLabel = tk.Label(self.mainscreenFrame,text="Track to Reference Navigation\nMainscreen")
        self.logoLabel.grid(row=0,column=0,sticky=tk.NSEW)

        self.mainscreenFrame.grid(row=0, column=0,sticky=tk.NSEW) 
    
    
    @clearFrame
    def buildNewExamFrame(self,master):
        self.newExamFrame = tk.Frame(master,bg="grey", padx = 20,pady=10)
        self.newExamFrame.rowconfigure(0, weight=10, uniform=1)
        self.newExamFrame.rowconfigure(1, weight=90, uniform=1)
        self.newExamFrame.columnconfigure(0, weight=1, uniform=1)
        self.newExamFrame.columnconfigure(1, weight=1, uniform=1)

        titlelabel = tk.Label(self.newExamFrame,text="Untersuchungsdaten")
        titlelabel.grid(row=0,column=0,columnspan=2,sticky=tk.NSEW)

        dataFrame = tk.Frame(self.newExamFrame,padx=20)
        dataFrame.columnconfigure(0, weight=35,minsize=180, uniform=1)
        dataFrame.columnconfigure(1, weight=65,uniform=1)
        
        #Reihenfolge der deklaration der Widgets bestimmt Darstellungsposition
        self.doctorLabel = tk.Label(dataFrame,text="Untersuchender Arzt")
        self.doctorEntry = tk.Entry(dataFrame,bd=5)
        self.doctorEntry.insert(0,"Dr. med. vet. Baader")
        self.patientLabel = tk.Label(dataFrame,text="Patient")
        self.patientEntry = tk.Entry(dataFrame,bd=5)
        self.patientEntry.insert(0,"Herr Bach")
        self.examItemLabel = tk.Label(dataFrame,text="Untersuchungsgegenstand")
        self.examItemTextbox = tk.Text(dataFrame, bd=5)
        self.examItemTextbox.insert('1.0',"US Untersuchung am linken Lungenfl\u00FCgel\nGutartiger Tumor")
        self.createdLabel = tk.Label(dataFrame,text="Erstellt am")
        self.createdEntry = tk.Entry(dataFrame,bd=5)
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%a, %d-%b-%Y (%H:%M:%S)")
        self.createdEntry.insert(0,timestampStr)
        self.createdEntry["state"] = 'readonly'
        
        children = dataFrame.winfo_children()

        #Alle 2 Einträge wird eine neue Reihe angefangen
        row_i=0
        for i, widget in enumerate(children):
            col_i = i%2
            dataFrame.rowconfigure(row_i,weight=1,uniform=1)
            widget.grid(row=row_i,column=col_i,sticky=tk.EW)
            row_i = row_i+(i%2)

        dataFrame.grid(row=1, column=0,columnspan=2,sticky=tk.NSEW)

        self.newExamFrame.grid(row=0, column=0,sticky=tk.NSEW) 

    
    @clearFrame
    def buildSetupFrame(self,master):
        padx = 10
        
        #2x2 Matrix of Application frame
        self.setupFrame = tk.Frame(master,bg="grey",padx=10,pady=10)  

        self.setupFrame.rowconfigure(0, weight=20, uniform=1)
        self.setupFrame.rowconfigure(1, weight=5, uniform=1,minsize=15)
        self.setupFrame.rowconfigure(2, weight=10, uniform=1)
        self.setupFrame.rowconfigure(3, weight=65, uniform=1)
        self.setupFrame.columnconfigure(0, weight=1, uniform=1)
        self.setupFrame.columnconfigure(1, weight=1, uniform=1)
        self.setupFrame.columnconfigure(2, weight=1, uniform=1)
        self.setupFrame.columnconfigure(3, weight=1, uniform=1)

        self.setuptitleLabel = tk.Label(self.setupFrame, text="Einrichtung des Aurorasystems")
        self.setuptitleLabel.grid(row=0,column=0,columnspan=4, pady=(10,8),sticky=tk.NSEW)
        
        instruc_title = tk.Label(self.setupFrame, text=" - Instruction - ", font='Helvetica 11 italic')
        instruc_title.grid(row=1,column=0,columnspan=4,pady=(10,0), sticky=tk.NSEW)
        self.instructionLabel = tk.Label(self.setupFrame, text="Some Instruction", font='Helvetica 9 italic')
        self.instructionLabel.grid(row=2,column=0,columnspan=4,pady=(0,10),sticky=tk.NSEW)


        for i in range(4):
            handle_Frame = tk.Frame(self.setupFrame,bg="white",padx=10,pady=10)
            lb = tk.Label(handle_Frame, text="Spulenname")
            lb2 = tk.Label(handle_Frame, text="Referenzname")
            entry = tk.Entry(handle_Frame,bd=5)
            But = tk.Button(handle_Frame ) 
            But["text"] = "Done"
            children = handle_Frame.winfo_children()
            
            self.packChildren(children,side=tk.TOP,fill=tk.BOTH,padx=5,pady=5)
            
            handle_Frame.grid(row=3,column=i,sticky=tk.NSEW,padx=2,pady=2)
            



        
        #Anwendungslogik!
        
        handle_index = 0

        self.setupFrame.grid(row=0, column=0,padx=2,pady=2,sticky=tk.NSEW) 
        

    @clearFrame
    def buildAppFrame(self,master,nav=False):

        #Init of AppFrame Attributes
        
        self.cap = None
        self.navCanvasData = ()
        self.img_size = None
        self.savedImg = None
       
        self.appFrame = tk.Frame(master,bg="black")     
        self.appFrame.rowconfigure(0, weight=90, uniform=1)
        self.appFrame.rowconfigure(1, weight=10,minsize=125,uniform=1)  
        self.appFrame.columnconfigure(0,weight=1)
        
        
        #2x2 Matrix of Application frame
        self.gridFrame = tk.Frame(self.appFrame) 
        self.gridFrame.rowconfigure(0, weight=1, uniform=1)
        self.gridFrame.rowconfigure(1, weight=1, uniform=1)
        self.gridFrame.columnconfigure(0, weight=1, uniform=1)
        self.gridFrame.columnconfigure(1, weight=1, uniform=1)
        self.gridFrame.bind('<Configure>', self.refreshImgSize)

        #Order of the US Frame, Saved Image and Navigationframe
        self.USImgFrame = tk.Frame(self.gridFrame,bg="green")
        self.USImgFrame.rowconfigure(0, weight=1)
        self.USImgFrame.columnconfigure(0, weight=1)
        self.savedImgFrame = tk.Frame(self.gridFrame,bg="green")
        self.savedImgFrame.rowconfigure(0, weight=1)
        self.savedImgFrame.columnconfigure(0, weight=1)
        self.navFrame = tk.Frame(self.gridFrame,bg="yellow")
        self.navFrame.rowconfigure(1, weight=1)
        self.navFrame.columnconfigure(0, weight=80)
        self.navFrame.columnconfigure(1, weight=20)

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
        self.navLabel["text"] = "Navigation GUI"
        self.navLabel.grid(row=0, column=0,sticky=tk.NSEW)
        self.sysmodeLabel = tk.Label(self.navFrame)
        self.sysmodeLabel["text"] = "Operating Mode: - "
        self.sysmodeLabel.grid(row=0, column=1,sticky=tk.NSEW)

        # TODO remove test
        if nav :
            # navigation test
            self.navigationvis = NavigationVisualizer(self.navFrame)
        else:
            self.fig = plt.figure()
            self.ax = self.fig.add_subplot(111, projection='3d')
            self.ax.set_autoscale_on(False)
            self.navCanvas = FigureCanvasTkAgg(self.fig,self.navFrame)  
        
            self.buildCoordinatesystem()
        
            self.navCanvas.get_tk_widget().grid(row=1, column=0, columnspan=2, pady=8, sticky=tk.NSEW)
        self.gridFrame.grid(row=0, pady=8, padx=8, sticky=tk.NSEW)
        self.gridFrame.after_idle(self.calcUSImgSize)


        #Gallery Frame Content
        self.galleryFrame = tk.Frame(self.appFrame, bg="#99ffcc")

        self.galleryLb = tk.Label(self.galleryFrame, text="a gallery")
        self.galleryLb.pack()

        self.galleryFrame.grid(row=1,column=0, pady=(0,8), padx=8, sticky=tk.NSEW)

        self.appFrame.grid(row=0, column=0,padx=2,pady=2,sticky=tk.NSEW) 
        

    def refreshImgSize(self,event):
        self.gridFrame.after_idle(self.calcUSImgSize)  

    def Capture_FrameGrabber(self):
        _isFirstCapture = True
        _, frame = self.cap.read()
        self.frame = cv2.flip(frame, 1)

        if frame is None and _isFirstCapture: 
            logging.warning("Empty Frame - No Device was found")
            self.USImgLabel["text"] = "EMPTY FRAME \n No Device was found"
            self.USImgLabel.after(10000, self.Capture_FrameGrabber)
            return
        if (self.USImgFrame.winfo_height()==1):
            cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            self.og_imgsize = img.size
            self.USImgLabel.after(1500, self.Capture_FrameGrabber)
            return

        cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        if (self.img_size is not None):
            img = img.resize(self.img_size, Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(image=img)

        self.USImgLabel.imgtk = imgtk
        self.USImgLabel.configure(image=imgtk)
        
        self._FrameGrabberJob = self.USImgLabel.after(10, self.Capture_FrameGrabber)

        # Slider window (slider controls stage position)
        # self.sliderFrame = tk.Frame(self.upperFrameLeft, width=600, height=100)
        # self.sliderFrame.grid(row=600, column=0, padx=10, pady=2)

    def calcUSImgSize(self):
        #Get current Frame
        cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        width, height = img.size

        #Normalize Ratio of Pictures, Resize appropriatly - could be optimized.
        img_ratio = height / width
        frame_ratio = self.USImgFrame.winfo_height()/self.USImgFrame.winfo_width()
        if (frame_ratio >= img_ratio):
            new_width = (self.USImgFrame.winfo_width()-5) 
            new_height = height / width * new_width
        else:
            new_height = (self.USImgFrame.winfo_height()-5)
            new_width = width / height * new_height
        

        self.img_size = ((int(new_width), int(new_height)))   
        self.refresh_savedImg()

    def refresh_savedImg(self):
        #Refresh Saved IMG more Image possible
        if (self.savedImg is not None):
            self.savedImg = self.savedImg.resize(self.img_size, Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=self.savedImg)      
            self.savedImgLabel.imgtk = imgtk
            self.savedImgLabel.configure(image=self.savedImgLabel.imgtk)


    def buildCoordinatesystem(self):
        plt.cla()
        self.ax.set_xlabel('X')
        self.ax.set_xlim(-230, 230)
        self.ax.set_ylabel('Y')
        self.ax.set_ylim(-320, 320)
        self.ax.set_zlabel('Z')
        self.ax.set_zlim(0, -600)
        

        if (len(self.navCanvasData) is not 0):
            x,y,z,color = self.navCanvasData
            self.navigationvis.set_pos(x[0], y[0])
            #Axes3D.scatter(self.ax,xs=x,ys=y,zs=z,c=color,edgecolors='black',s=70)
            
            #self._Canvasjob = self.navCanvas._tkcanvas.after(40,func=self.buildCoordinatesystem)
        
        self.navCanvas.draw()


    def saveUSImg(self):
        cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        self.savedImg = Image.fromarray(cv2image)
        self.refresh_savedImg()

    
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






    def buildTab2(self):
        #Tab2
        self.t2_debugFrame = tk.Frame(self.tabControl, bg="grey")
        self.t2_debugFrame.rowconfigure(0, weight=1)
        self.t2_debugFrame.columnconfigure(0, weight=80)
        self.t2_debugFrame.columnconfigure(1, weight=20)

        self.t2_leftFrame = tk.Frame(self.t2_debugFrame, bg="green")
        self.t2_leftFrame.columnconfigure(0, weight=1)
        self.t2_rightFrame = tk.Frame(self.t2_debugFrame, bg="blue")
        self.t2_rightFrame.columnconfigure(0, weight=1)
        self.t2_rightFrame.columnconfigure(2, weight=1)
        self.t2_rightFrame.rowconfigure(0, weight=1)
        self.t2_rightFrame.rowconfigure(10, weight=1)

        self.t2_leftFrame.grid(row=0, column=0, pady=8, padx=8, sticky=tk.NSEW)
        self.t2_rightFrame.grid(row=0, column=1, pady=8, padx=8, sticky=tk.NSEW)
       
        self.build_DebugMenu(self.t2_leftFrame)
        self.build_DebugCMD(self.t2_rightFrame)

        self.t2_debugFrame.pack(fill=tk.BOTH, expand=tk.TRUE)

    def build_DebugMenu(self,lFrame):
        self.debugMenuLabel = tk.Label( lFrame, text="Debug Menu Options")
        self.initBut = tk.Button(lFrame)
        self.initBut["text"] = "INIT"
        
        self.readBut = tk.Button(lFrame)  
        self.readBut["text"] = "READ Serial"
            
        self.resetBut = tk.Button(lFrame)
        self.resetBut["text"] = "Reinitialize System"
                
        self.testBut = tk.Button(lFrame)
        self.testBut["text"] = "Test Something"
        
        self.handleBut = tk.Button(lFrame)
        self.handleBut["text"] = "Activate Handles"
                
        self.restartBut = tk.Button(lFrame)
        self.restartBut["text"] = "Restart Program"
        
        self.quitBut = tk.Button(lFrame, text="QUIT", fg="red")
        
        #Place-Geomanager for Leftframe
        self.debugMenuLabel.grid(row=0,padx=(1,1),sticky=tk.NSEW)
        self.initBut.grid(row=1,padx=(1,1))
        self.readBut.grid(row=2,padx=(1,1),sticky=tk.NSEW)
        self.resetBut.grid(row=3,padx=(1,1),sticky=tk.NSEW)
        self.testBut.grid(row=4,padx=(1,1),sticky=tk.NSEW)
        self.handleBut.grid(row=5,padx=(1,1),sticky=tk.NSEW)
        # self.restartBut.pack()
        self.quitBut.grid(row=6,padx=(1,1),sticky=tk.NSEW)

        

        for i,child in enumerate(lFrame.winfo_children(),start=0):   
            lFrame.rowconfigure(i, weight=1)
            if (child.winfo_class() == 'Button'):
                child["width"]= 35
                child["height"] = 2
                child.grid_propagate(0)

    def build_DebugCMD(self,rFrame):
        self.cmdLabel = tk.Label( rFrame, text="CMD")
        self.cmdEntry = tk.Entry(rFrame,bd =5)
        self.expecLabel = tk.Label( rFrame, text="Expected read ending character")
        self.expec = tk.Entry(rFrame,bd =5)
        self.sleepLabel = tk.Label( rFrame, text="Read sleep time")
        self.sleeptimeEntry = tk.Entry(rFrame,bd =5)
        self.sleeptimeEntry.insert(0,0)
        
        self.cmdLabel.grid(row=1,column = 1, pady=(10, 2),sticky=tk.EW)
        self.cmdEntry.grid(row=2,column = 1,sticky=tk.EW)
        self.expecLabel.grid(row=3,column = 1, pady=(10, 2),sticky=tk.EW)
        self.expec.grid(row=4,column = 1,sticky=tk.EW)
        self.sleepLabel.grid(row=5,column = 1, pady=(10, 2),sticky=tk.EW)
        self.sleeptimeEntry.grid(row=6,column = 1,sticky=tk.EW)


    def initImages(self):

        self.imgdir = "..\\img\\"
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
            logging.exception("File was no found, Err Img replace\n"+err)
            tkimage = self.notfoundimg    

        finally:
            return ImageTk.PhotoImage(tkimage)



    def packChildren(self,childList,side,fill,padx,pady):
        for child in childList:
            child.pack(side=side,fill=fill,padx=padx,pady=pady)


    
            