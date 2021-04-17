import tkinter as tk
from tkinter import messagebox
import os
import sys
import sqlite3

# TODO
#import windll

#windll.shcore.SetProcessDpiAwareness(1)

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

class Model:
    def __init__(self, parent, filepath):
        self.parent = parent

        if filepath == None:
            self.model_path = None
            self.open_db(":memory:")
            self.new_db()
        elif os.path.exists(filepath):
            self.model_path = filepath
            self.open_db(filepath)
        else:
            self.model_path = None
            self.open_db(":memory:")
            self.new_db()

    def open_db(self, connect_string):
        self.db = sqlite3.connect(connect_string)

    def new_db(self):
        ''' if no model file is provided, build database tables '''
        sql_create_pipes_table = """
                                 CREATE TABLE IF NOT EXISTS pipes (
                                 id integer PRIMARY KEY,
                                 pipe_name text,
                                 node1 text,
                                 node2 text,
                                 attr1 text,
                                 attr2 text,
                                 attr3 text,
                                 attr4 text,
                                 attr5 text,
                                 nominal_diameter integer,
                                 internal_diameter real,
                                 flow real,
                                 flow_direction integer
                                 );
                                 """



        self.create_table(sql_create_pipes_table)

    def create_table(self, create_table_sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(create_table_sql)
        except:
            pass

class Main(tk.Frame):
    def __init__(self, parent):
        ''' reads config file and creates main canvas '''
        self.parent = parent
        self.width = read_config(config_parser, 'RESOLUTION', 'width')
        self.height = read_config(config_parser, 'RESOLUTION', 'height')
        self.canvas = tk.Canvas(parent.frame, width=self.width, height=self.height)


class MenuBar:
    def __init__(self, parent):
        ''' class to handle initialization of menubars '''
        self.parent = parent
        self.menubar = tk.Menu(self.parent)
        self.create()

    def create(self):
        self.parent.config(menu = self.menubar)

    def add_menu(self, menuname, commands):
        ''' creates a drop down menu '''
        menu = tk.Menu(self.menubar, tearoff=0)

        for command in commands:
            menu.add_command(label = command[0], command= command[1])

        self.menubar.add_cascade(label=menuname, menu=menu)


class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ''' main tkinter window '''
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent, *args, **kwargs)

        # Create model instance
        try:
            self.model = Model(self, sys.argv[1])
        except:
            self.model = Model(self, None)

        # create canvas
        self.main  = Main(self)
        self.main.canvas.pack()
        self.initUI()
        #self.initModel(self.model_path)




    def initUI(self):
        ''' Initializes main window title and menu bar'''

        self.parent.title('PyFlow H2O')
        self.menubar = MenuBar(self.parent)

        file_commands = [
                        ('New Model', None),
                        ('Open...', None),
                        ('Quit', on_closing)
                        ]

        edit_commands = [
                        ('Undo', None),
                        ('Redo', None)
                        ]

        view_commands = [
                        ]

        mode_commands = [
                        ('Viewing Mode', None),
                        ('Drawing Mode', None)
                        ]

        self.filemenu = self.menubar.add_menu('File', commands=file_commands)
        self.editmenu = self.menubar.add_menu('Edit', commands=edit_commands)
        self.viewmenu = self.menubar.add_menu('View', commands=view_commands)
        self.modemenu = self.menubar.add_menu('Mode', commands=mode_commands)


def on_closing():
    ''' Prompts user if they want to quit '''
    # TODO: add check if model has been saved or not
    if messagebox.askokcancel('Quit', 'Do you want to quit?'):
        try:
            app.model.db.db.close()
        except:
            pass
        root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root).pack(side='top', fill='both', expand=True)
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()

