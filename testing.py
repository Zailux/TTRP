from ultraVisGui import UltraVisController
import tkinter as tk

class Uvisproto(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.hi_there = tk.Button(self)
        self.hi_there["text"] = "Hello World\n(click me)"
        self.hi_there["command"] = self.say_hi
        self.hi_there.pack(side="top")

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.pack(side="bottom")


        self.myLabel = tk.Label(self)
        self.myLabel["text"] = "Noobies"
        self.myLabel.pack(side="top")

    def say_hi(self):
        print(self.quit.config())
#Methods

def openfile():
    myFile = tk.filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
    print (myFile)


root = tk.Tk()
app = Uvisproto(master=root)

app.mainloop()






