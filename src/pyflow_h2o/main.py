import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import askopenfilename
from functools import partial
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
        self.mode = 'View/Select'

        # build new database tables or load existing file
        self.init_db(filepath)


    def init_db(self, filepath):

        # open a database in memory - working db
        self.open_db(":memory:")

        if filepath == None:
            self.filepath = None
            self.new_db()
        elif os.path.exists(filepath):
            self.filepath = filepath
            source = sqlite3.connect(filepath)
            source.backup(self.db) # copy contents from local file to memory
            source.close()
            self.load_model() # TODO: verify if this is working if sys argument
        else:
            self.filepath = None
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
                                 length real,
                                 flow real,
                                 flow_direction integer,
                                 v real,
                                 Re real,
                                 f real,
                                 n_exp real
                                 );
                                 """

        sql_create_nodes_table = """
                                 CREATE TABLE IF NOT EXISTS nodes (
                                 id integer PRIMARY KEY,
                                 node_name text,
                                 attr1 text,
                                 attr2 text,
                                 attr3 text,
                                 attr4 text,
                                 attr5 text,
                                 pressure real,
                                 head real,
                                 head_known integer,
                                 inflow real,
                                 inflow_known integer,
                                 x real,
                                 y real
                                 );
                                 """

        self.create_table(sql_create_pipes_table)
        self.create_table(sql_create_nodes_table)

    def create_table(self, create_table_sql):
        ''' adds table to open database / model '''
        try:
            cursor = self.db.cursor()
            cursor.execute(create_table_sql)
            self.db.commit()
            cursor.close()
        except:
            pass

    def load_model(self):
        ''' draws nodes and pipes on canvas '''

        # draw nodes
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM nodes')
        for node in cursor:
            self.parent.main.draw_node(f'n-{node[0]}', node[-2], node[-1])

        # draw pipes
        sql_get_pipes = '''
                        SELECT 
                            pipes.id, 
                            pipes.pipe_name, 
                            pipes.node1, 
                            pipes.node2, 
                            pipes.attr1, 
                            pipes.attr2, 
                            pipes.attr3, 
                            pipes.attr4, 
                            pipes.attr5, 
                            pipes.nominal_diameter, 
                            pipes.internal_diameter, 
                            pipes.length, 
                            pipes.flow, 
                            pipes.flow_direction, 
                            pipes.v, 
                            pipes.Re, 
                            pipes.f, 
                            pipes.n_exp, 
                            q1.x1, 
                            q1.y1, 
                            q2.x2, 
                            q2.y2 
                        FROM
                            pipes
                        INNER JOIN 
                            (
                            SELECT pipes.id, 
                                nodes.x as x1, 
                                nodes.y as y1 
                            FROM pipes 
                            INNER JOIN nodes on pipes.node1 = nodes.node_name
                            ) q1 on pipes.id = q1.id
                        INNER JOIN 
                            (
                            SELECT pipes.id, 
                                nodes.x as x2, 
                                nodes.y as y2
                            FROM pipes 
                            INNER JOIN nodes on pipes.node2 = nodes.node_name
                            ) q2 on pipes.id = q2.id
                        '''
        cursor.execute(sql_get_pipes)
        for pipe in cursor:
            self.parent.main.draw_line(f'p-{pipe[0]}', pipe[-4], pipe[-3], pipe[-2], pipe[-1])

        cursor.close()

class Main(tk.Frame):
    def __init__(self, parent):
        ''' reads config file and creates main canvas '''
        self.parent = parent
        self.width = read_config(config_parser, 'RESOLUTION', 'width')
        self.height = read_config(config_parser, 'RESOLUTION', 'height')
        self.canvas = tk.Canvas(parent.frame, width=self.width, height=self.height)

    def draw_node(self, id, x, y):
        ''' Draw node onto the canvas '''
        # TODO: apply legend (upcoming feat)
        r = 5 # node radius
        self.canvas.create_oval(x-r, y-r, x+r, y+r, tag=('node',id), fill='black')

    def draw_line(self, id, x1, y1, x2, y2):
        # TODO: apply legend (upcoming feat)
        pipe_width = 3 # pipe width
        self.canvas.create_line(x1, y1, x2, y2, tag=('pipe', id), fill='black', width=pipe_width)


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

class Button:
    def __init__(self, parent, text):
        self.parent = parent
        self.text = text
        self.create()

    def create(self):
        self.button = tk.Button(self.parent.frame, text=self.text)

class TopFrame:
    def __init__(self, parent):
        self.parent = parent
        self.width = read_config(config_parser, 'RESOLUTION', 'width')
        self.height = 16 # pixels
        self.create()

    def create(self):
        self.frame = tk.Frame(self.parent.parent, width=self.width, height=self.height)


class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ''' main tkinter window '''
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent, *args, **kwargs)
        self.top_frame = TopFrame(self)
        self.top_frame.frame.pack()

        # Create model instance
        try:
            self.model = Model(self, sys.argv[1])
        except:
            self.model = Model(self, None)

        # create canvas
        self.initUI()

    def save(self, save_type):
        ''' write the current model to disk '''
        # TODO: add check if database is not saved
        files = [('PyFlow H2O model','*.pfh'),
                 ('All Files', '*.*')]
        if save_type == 'SAVE':
            if self.model.filepath is None:
                saveas_file = asksaveasfilename(filetypes=files, defaultextension=files)
            else:
                saveas_file = self.model.filepath
        elif save_type == 'SAVE_AS':
            saveas_file = asksaveasfilename(filetypes=files, defaultextension=files)


        if saveas_file != '': # if user did not cancel the save as function
            if os.path.exists(saveas_file): # delete existing file
                os.remove(saveas_file)
            conn = sqlite3.connect(saveas_file)
            with conn:
                for line in self.model.db.iterdump():
                    if line not in ('BEGIN;', 'COMMIT;'): # let python handle transactions
                        conn.execute(line)
            conn.commit()
            self.model.filepath = saveas_file


    def open(self):
        files = [('PyFlow H2O model', '*.pfh'),
                 ('All Files', '*.*')]
        print('hello')
        open_file = askopenfilename(filetypes=files)


        if open_file != '': # if user did not cancel the file open function
            self.model.db.close()
            self.model.init_db(open_file)


    def initUI(self):
        ''' Initializes main window title and menu bar'''

        self.parent.title('PyFlow H2O')

        self.menubar = MenuBar(self.parent)

        file_commands = [
                        ('New Model', None),
                        ('Open...', self.open),
                        ('Save', partial(self.save, 'SAVE')),
                        ('Save as...', partial(self.save, 'SAVE_AS')),
                        ('Quit', on_closing)
                        ]

        edit_commands = [
                        ('Undo', None),
                        ('Redo', None)
                        ]

        view_commands = [
                        ]

        mode_commands = [
                        ('View/Select', None),
                        ('Draw Nodes', None),
                        ('Draw Pipes', None),
                        ('Draw Valves', None),
                        ('Draw Pumps', None)
                        ]

        self.filemenu = self.menubar.add_menu('File', commands=file_commands)
        self.editmenu = self.menubar.add_menu('Edit', commands=edit_commands)
        self.viewmenu = self.menubar.add_menu('View', commands=view_commands)
        self.modemenu = self.menubar.add_menu('Mode', commands=mode_commands)

        # create quick button menu for testing
        self.button = Button(self, 'hello')
        self.button.button.pack(side='left', anchor='nw')

        # create canvas
        self.main = Main(self)
        self.main.canvas.pack()



def on_closing():
    ''' Prompts user if they want to quit '''
    # TODO: add check if model has been saved or not
    if messagebox.askokcancel('Quit', 'Do you want to quit?'):
        try:
            app.model.db.close()
        except:
            pass
        root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root).pack(side='top', fill='both', expand=True)
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()

