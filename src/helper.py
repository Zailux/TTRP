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

    def get_readonly_widget(self, master, value, max_length, max_height=None):
        val = str(value)
        widget = None


        if(len(val)>max_length):
            widget = tk.Text(master,bd=3)
            widget.insert('1.0',str(value))
            widget.configure(state='disabled')
            if max_height is not None:
                widget.configure(height=max_height)

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



class ScrollableFrame(tk.Frame):
    """ScrollableFrame
    This Class instantiates an outer base_frame. Inside that frame, it
    utilizes tk.Canvas and tk.Scrollbar to create a acrollable frame.
    Use the 'contentframe' attribute to put widgets into it.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)

        self.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        super().columnconfigure(0, weight=95)
        super().columnconfigure(1, weight=5, minsize=15)
        super().rowconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky=tk.NSEW, padx=(0,10))
        scrollbar.grid(row=0, column=1, sticky=tk.NSEW)
        canvas.configure(yscrollcommand=scrollbar.set)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.contentframe = tk.Frame(canvas)
        contentframe_id = canvas.create_window((0, 0), window=self.contentframe, anchor="nw")

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (self.contentframe.winfo_reqwidth(), self.contentframe.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if self.contentframe.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=self.contentframe.winfo_reqwidth())
                #print(scrollbar.instate(statespec=['disabled']))
        self.contentframe.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if self.contentframe.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(contentframe_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

