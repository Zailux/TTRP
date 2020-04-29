

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
