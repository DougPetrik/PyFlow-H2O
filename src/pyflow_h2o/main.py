import tkinter as tk

import configparser
import os

# this script's file path
app_dir = os.path.dirname(os.path.abspath(__file__))

# initialize config reader
config_parser = configparser.RawConfigParser()
config_file_path = os.path.join(app_dir, 'config.ini')
config_parser.read(config_file_path)

def read_config(parser_instance, setting, attribute):
    return config_parser.get(setting, attribute)

class Main(tk.Frame):
    def __init__(self, parent):
        self.parent = parent
        self.width = read_config(config_parser, 'RESOLUTION', 'width')
        self.height = read_config(config_parser, 'RESOLUTION', 'height')
        self.canvas = tk.Canvas(parent.frame, width=self.width, height=self.height)


class MenuBar:
    def __init__(self, parent):
        self.parent = parent
        self.menubar = tk.Menu(self.parent)
        self.create()

    def create(self):
        self.parent.config(menu = self.menubar)

    def add_menu(self, menuname, commands):
        menu = tk.Menu(self.menubar, tearoff=0)

        for command in commands:
            menu.add_command(label = command[0], command= command[1])

        self.menubar.add_cascade(label=menuname, menu=menu)

class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent, *args, **kwargs)

        self.main  = Main(self)
        self.main.canvas.pack()
        self.initUI()

    def initUI(self):
        self.parent.title('PyFlow H2O')
        self.menubar = MenuBar(self.parent)
        self.filemenu = self.menubar.add_menu('File',commands=[('Open', None)])


if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root).pack(side='top', fill='both', expand=True)
    root.mainloop()

