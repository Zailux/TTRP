"""Uvis helper Module

The helper module contains methods, which helps with
easier GUI Handling.

Available Classes
    Helper Class
    Scrollable Frame Class
"""

import tkinter as tk
from tkinter import ttk


class Helper():
    """ The helper class easier GUI Handling in uvis_controller and uvis_view
      
    Attributes: 
        None yet
    """

    def __init__(self):
        pass
    
    #Tkinter helper
    
    def setRow(self,num):
        self.row = num
    
    def getnextRow(self):
        nextRow = self.row
        self.row +=1
        
        return nextRow

    def getReadOnlyWidget(self,master,value,max_length):
        val = str(value)
        widget = None

        if(len(val)>max_length):
            widget = tk.Text(master,bd=3) 
            widget.insert('1.0',str(value)) 
            widget.configure(state='disabled') 
           
        else:
            widget = tk.Entry(master,bd=3)
            widget.insert(0,str(value))
            widget.configure(state='readonly') 

        return widget

    def enableWidgets(self,childList,enable_all=False):
        for child in childList:
            if (child.winfo_class() == 'Frame'):
                self.enableWidgets(child.winfo_children())
                continue

            if (child.winfo_class() in ['Button','Entry'] or enable_all):
                child.configure(state='normal')

    def disableWidgets(self,childList,disable_all=False):
        for child in childList:
            if (child.winfo_class() == 'Frame'):
                self.disableWidgets(child.winfo_children())
                continue

            if (child.winfo_class() in ['Button','Entry'] or disable_all):
                child.configure(state='disabled')


    def packChildren(self,childList,side,fill,padx,pady):
        for child in childList:
            child.pack(side=side,fill=fill,padx=padx,pady=pady)


#Not working ATM
class ScrollableFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        #self.configure(background="yellow")
        master.columnconfigure(0,weight=95)
        master.columnconfigure(1,weight=1)
        master.rowconfigure(0,weight=1)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0,column=0,sticky=tk.NSEW)
        scrollbar.grid(row=0,column=1,sticky=tk.NSEW)
