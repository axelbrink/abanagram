# Based on: https://pythonprogramming.net/object-oriented-programming-crash-course-tkinter/

__author__ = "Axel Brink"

import tkinter as tk
from tkinter import Grid
import tkinter.constants as const
from tkinter import messagebox
import abanagram

LARGE_FONT = ("Verdana", 12)

# import tkinter
# top = tkinter.Tk()
# # Code to add widgets will go here...
# top.mainloop()

class AbanagramGui(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        frame = AnagramPage(container, self)
        self.frames[AnagramPage] = frame

        frame.grid(row=0, column=0, sticky="nsew")

        self.title("Abanagram")
        #self.winfo_toplevel().title(

        self.menubar = tk.Menu(self)

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Exit", command=self.destroy)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=self.on_menu_about)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

        self.config(menu=self.menubar)

        self.show_frame(AnagramPage)

    def on_menu_about(self, event=None):
        messagebox.showinfo("About Abanagram", "Abanagram\nBy Axel Brink\n2017\nUses word lists of OpenTaal.")

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class AnagramPage(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent, width=300, height=500)

        self.root = self.winfo_toplevel()
        Grid.columnconfigure(self, 0, weight=0)
        Grid.columnconfigure(self, 1, weight=1)
        Grid.columnconfigure(self, 2, weight=0)
        Grid.rowconfigure(self, 0, weight=0)
        Grid.rowconfigure(self, 1, weight=0)
        Grid.rowconfigure(self, 2, weight=1)
        Grid.rowconfigure(self, 3, weight=0)
        self.grid(row=0, column=0, sticky=const.N + const.S + const.E + const.W)

        self.inputlabel = tk.Label(self, text="Input:", justify=tk.constants.LEFT)
        self.inputlabel.grid(row=0, column=0, sticky=const.N + const.E)

        self.entry = tk.Entry(self)
        #self.entry.pack(pady=10, padx=10, side=tk.constants.TOP, fill=tk.constants.X)
        self.entry.grid(row=0, column=1, columnspan=2, sticky=const.N + const.E + const.W)
        self.entry.focus_set()
        self.entry.bind('<Return>', (lambda e: self.startbutton.invoke()))

        self.maxwordslabel = tk.Label(self, text="Max number of words:", justify=const.LEFT)
        #self.maxwordslabel.pack(side=tk.constants.TOP)
        self.maxwordslabel.grid(row=1, column=0, sticky=const.N + const.E)

        self.maxwordsentry = tk.Entry(self)
        #self.maxwordsentry.pack(side=tk.constants.RIGHT)
        self.maxwordsentry.grid(row=1, column=1, sticky=const.N + const.E + const.W)

        self.startbutton = tk.Button(self, text="Start", command=self.on_start)
        #self.startbutton.pack(side=tk.constants.TOP)
        self.startbutton.grid(row=1, column=2)

        self.resultlist = ScrollListBox(self, parent)
        #self.resultlist.pack(pady=10, padx=10, side=tk.constants.TOP, expand=1, fill=tk.constants.BOTH)
        self.resultlist.grid(row=2, column=0, columnspan=3, sticky=const.N + const.S + const.E + const.W)

        self.statuslabel = tk.Label(self, text="Abanagram by Axel Brink. Ready.", justify=tk.constants.LEFT)
        #self.label.pack(side=tk.constants.TOP)
        self.statuslabel.grid(row=3, columnspan=2)

        #self.pack()
        #self.pack_propagate(0) # tell frame not to let its children control its size

        #self.grid_propagate(0)

        self.anagramfinder = abanagram.AnagramFinder(result_callback=self.add_result, status_callback=self.status_update)



    def on_start(self, event=None):
        #self.label.config(text="Ja! " + self.entry.get())
        self.statuslabel.config(text="Searching for anagrams of '" + self.entry.get() + "'...")

        self.root.config(cursor="wait")
        self.root.update()

        self.resultlist.listbox.delete(0, tk.constants.END)
        self.anagramfinder.search(self.entry.get(), int(self.maxwordsentry.get()))
        self.statuslabel.config(text="Ready.")
        #for i in range(50):
        #    self.add_result("Abc " + str(i))

    def add_result(self, result):
        self.resultlist.listbox.insert(tk.constants.END, result)
        self.update()

    def status_update(self, text):
        self.statuslabel.config(text=text)
        if text.startswith("Done"):
            self.root.config(cursor="")


class ScrollListBox(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.scrollbar = tk.Scrollbar(self, orient=tk.constants.VERTICAL)
        self.listbox = tk.Listbox(self, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side=tk.constants.RIGHT, fill=tk.constants.Y)
        self.listbox.pack(side=tk.constants.LEFT, fill=tk.constants.BOTH, expand=1)


app = AbanagramGui()
app.mainloop()