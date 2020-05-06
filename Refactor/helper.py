import tkinter as tk
from tkinter import ttk

class Helper():

    def __init__(self):
        pass
    
    #Tkinter helper
    
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





class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
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

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")