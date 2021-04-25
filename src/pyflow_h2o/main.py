import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import askopenfilename
import tkinter.ttk as ttk

from functools import partial
import sys
import sqlite3
from ctypes import *
import configparser
import os

# windows display scaling compatibility
windll.shcore.SetProcessDpiAwareness(1)

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

        # create model tables
        self.create_table(sql_create_pipes_table)
        self.create_table(sql_create_nodes_table)

        self.count_cols()

    def create_table(self, create_table_sql):
        ''' adds table to open database / model '''
        try:
            cursor = self.db.cursor()
            cursor.execute(create_table_sql)
            self.db.commit()
            cursor.close()
        except:
            pass

    def count_cols(self):
        # count the number of columns in each database table
        self.node_col_count = self.db.cursor().execute("SELECT count(*) FROM pragma_table_info('nodes')").fetchall()[0][0]
        self.pipe_col_count = self.db.cursor().execute("SELECT count(*) FROM pragma_table_info('pipes')").fetchall()[0][0]
        self.db.cursor().close()

    def load_model(self):
        ''' fetches model data and draws them on canvas '''

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

        # get count of columns
        self.count_cols()

class Main(tk.Frame):
    def __init__(self, parent):
        ''' reads config file and creates main canvas '''
        self.parent = parent
        self.width = read_config(config_parser, 'RESOLUTION', 'width')
        self.pane_width = 250
        self.canvas_width = int(self.width) - self.pane_width
        self.height = read_config(config_parser, 'RESOLUTION', 'height')
        self.create()


    def create(self):

        # create the main frame
        self.main_frame = tk.Frame(self.parent, width=self.width, height=self.height)

        # create the canvas
        self.canvas = tk.Canvas(self.main_frame, width=self.canvas_width, height=self.height, bg='light blue')
        self.canvas.bind('<Button-1>', self.action_leftclick)

        # add canvas scroll bars
        self.xsb = tk.Scrollbar(self.canvas, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.xsb.set)
        self.canvas.configure(scrollregion=(0,0,1000,1000))
        self.canvas.bind('<ButtonPress-2>', self.scroll_start)
        self.canvas.bind('<B2-Motion>', self.scroll_move)

        # add the side pane
        self.side_pane = tk.Frame(self.main_frame, width=self.pane_width, height=self.height, bg='white', highlightbackground='black', highlightthickness=1)

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def draw_node(self, id, x, y):
        ''' Draw node onto the canvas '''
        # TODO: apply legend (upcoming feat)
        r = 5 # node radius
        self.canvas.create_oval(x-r, y-r, x+r, y+r, tag=('all','node',id), fill='black')

    def draw_line(self, id, x1, y1, x2, y2):
        # TODO: apply legend (upcoming feat)
        pipe_width = 3 # pipe width
        self.canvas.create_line(x1, y1, x2, y2, tag=('all','pipe', id), fill='black', width=pipe_width)

    def action_leftclick(self, event):
        ''' handles canvas click events '''
        if self.parent.mode == 'node' and self.parent.draw_mode == 'add':
            new_node = ['0' for _ in range(0,self.parent.model.node_col_count)] # blank list for inserting into database
            new_node[-2] = event.x
            new_node[-1] = event.y

            # get the next availabile unique node id
            cursor = self.parent.model.db.cursor()
            cursor.execute('SELECT max(id) FROM nodes')
            max_id = cursor.fetchall()

            if max_id[0][0] is None:
                new_node[0] = 1 # blank model, start id from 0
            else:
                new_node[0] = max_id[0][0] + 1 # pick next availabile id number

            # draw the new node
            self.draw_node(f'n-{new_node[0]}', event.x, event.y)

            # insert new node into database
            new_node_sql = ', '.join(str(i) for i in new_node)
            cursor.execute(f'INSERT INTO nodes VALUES({new_node_sql})')
            self.parent.model.db.commit()
            cursor.close()

        elif self.parent.mode == 'node' and self.parent.draw_mode == 'delete':
            try:
                # get list of canvas objects below cursor
                items = event.widget.find_overlapping(event.x, event.y, event.x, event.y)

                # determine if a node is present
                for item in items:
                    if 'n' in self.canvas.gettags(item)[2]: # check if mouse is over a node
                        node_tag = self.canvas.gettags(item)[2]
                        node_id = node_tag.split('-')[1]
                        break

                # check if node is connected to any pipes
                sql = f'''
                       SELECT count(nodes.id)
                       FROM nodes
                       INNER JOIN pipes on
                         (nodes.node_name = pipes.node1
                         or
                         nodes.node_name = pipes.node2)
                       WHERE nodes.id = {node_id}
                       '''
                leg_count = self.parent.model.db.cursor().execute(sql).fetchall()[0][0]

                if leg_count == 0:
                    # delete node from canvas
                    self.canvas.delete(node_tag)

                    # delete node from database
                    delete_node_sql = f'DELETE FROM nodes WHERE ID = {node_id}'
                    self.parent.model.db.cursor().execute(delete_node_sql)
                    self.parent.model.db.commit()
                    self.parent.model.db.cursor().close()


            except:
                pass

        elif self.parent.mode == 'pipe' and self.parent.draw_mode == 'add':
            if self.parent.drawing is False:
                try:
                    items = event.widget.find_overlapping(event.x, event.y, event.x, event.y)

                    # determine if a node is present
                    for item in items:
                        if 'n' in self.canvas.gettags(item)[2]:  # check if mouse is over a node
                            node_tag = self.canvas.gettags(item)[2]
                            node_id = node_tag.split('-')[1]
                            break
                except:
                    pass

            elif self.parent.drawing == True:
                pass

        else:
            pass

    def draw_new_pipe(self, event):
        x, y = event.x, event.y
        if canvas.old_coord

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

class TopFrame:
    def __init__(self, parent):
        self.parent = parent
        self.width = read_config(config_parser, 'RESOLUTION', 'width')
        self.height = 16 # pixels
        self.create()

    def create(self):
        self.frame = tk.Frame(self.parent.parent, width=self.width, height=self.height, bg='white')

class Ribbon:
    def __init__(self, parent, height):
        self.parent = parent
        self.width = read_config(config_parser, 'RESOLUTION', 'width')
        self.height = height
        self.create()

    def create(self):
        self.frame = tk.Frame(self.parent, width=self.width, height=self.height, bg='white', highlightthickness=0, bd=0)

class Ribbon_Button:
    def __init__(self, parent, image_path, image_path_selected, command):
        self.parent = parent
        self.width = 32
        self.frame_width = self.width
        self.height = 32
        self.frame_height = self.height
        self.create(image_path, image_path_selected, command)

    def create(self, image_path, image_path_selected, command):
        # note - image_path must be r string
        self.photoimage = tk.PhotoImage(file = image_path)
        self.photoimage_select = tk.PhotoImage(file = image_path_selected)
        self.frame = tk.Frame(self.parent, width=self.frame_width, height=self.frame_height, highlightthickness=0, bg='white')
        self.frame.pack(side='left', anchor='e', expand=False)
        self.frame.button = tk.Button(self.frame, width=self.width, height=self.height, image=self.photoimage, command=command,
                                highlightthickness=1, bd=0, relief='sunken', bg='white')
        self.frame.button.pack(expand=True, fill=None)

        self.frame.button.bind('<Enter>', self.on_enter)
        self.frame.button.bind('<Leave>', self.on_leave)

    def on_enter(self, event):
        self.frame.button.configure(relief='raised')
        #self.button.configure(highlightbackground='black', highlightthickness=2, bd=0)

    def on_leave(self, event):
        self.frame.button.configure(relief='sunken')
        #self.button.configure(highlightbackground=None, highlightthickness=1, bd=0)

class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ''' main tkinter window '''
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg='white')

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
        else:
            saveas_file = ''


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
        open_file = askopenfilename(filetypes=files)

        if open_file != '': # if user did not cancel the file open function
            self.model.db.close()
            self.main.canvas.delete('all')
            self.model.init_db(open_file)

    def change_mode(self, mode, draw_mode):
        ' Changes application mode between drawing, selecting, editing, etc.'
        self.mode = mode
        self.draw_mode = draw_mode

        # TODO: find a better way to loop through all ribbon buttons and change image
        self.clear_button_images()

        #for frame in self.ribbon.frame.children.values():
        #    button = frame.children['!button']
        #    button.configure(image=photoimage)

        if self.mode == 'select':
            self.ribbon.select_button.frame.button.configure(image=self.ribbon.select_button.photoimage_select)

        elif self.mode == 'node':
            if self.draw_mode == 'add':
                self.ribbon.add_node_button.frame.button.configure(image=self.ribbon.add_node_button.photoimage_select)
            elif self.draw_mode == 'delete':
                self.ribbon.delete_node_button.frame.button.configure(image=self.ribbon.delete_node_button.photoimage_select)
            #for button in frame:
            #    print(button)
            #print(child.children.values()[0])

        #for child in self.ribbon.frame.children.children.values():
        #    print(child)
            #child.configure(image=child.photoimage)

        #if self.mode == 'node' and self.draw_mode == 'add':
        #    print('hello')

            #self.ribbon.add_node_button.button.configure(image=self.ribbon.add_node_button.photoimage_select)

    def clear_button_images(self):
        self.ribbon.select_button.frame.button.configure(image=self.ribbon.select_button.photoimage)
        self.ribbon.add_node_button.frame.button.configure(image=self.ribbon.add_node_button.photoimage)
        self.ribbon.delete_node_button.frame.button.configure(image=self.ribbon.delete_node_button.photoimage)

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

        query_commands = [
                         ('Select...', None),
                         ('Spatial Select...', None)
                         ]

        report_commands = [
                          ]

        help_commands = [
                        ('About', None)
                        ]

        self.filemenu = self.menubar.add_menu('File', commands=file_commands)
        self.editmenu = self.menubar.add_menu('Edit', commands=edit_commands)
        self.viewmenu = self.menubar.add_menu('View', commands=view_commands)
        self.querymenu = self.menubar.add_menu('Query', commands=query_commands)
        self.reportmenu = self.menubar.add_menu('Reports', commands=report_commands)
        self.helpmenu = self.menubar.add_menu('Help', commands=help_commands)

        # create quick button menu for testing
        #self.button = Button(self, 'hello')
        #self.button.button.pack(side='left', anchor='nw')

        # create top ribbon
        self.ribbon = Ribbon(self, 32)
        self.ribbon.frame.pack(side='top', expand=False, fill='x')

        # add ribbon buttons
        self.ribbon.select_button = Ribbon_Button(self.ribbon.frame, r'View.png', r'View_Select.png',
                                                    command=partial(self.change_mode, 'select', None))
        # TODO: add query functionality
        self.ribbon.query_button = Ribbon_Button(self.ribbon.frame, r'Query.png', r'Query_Select.png',
                                                    command=None)

        # add separator
        self.add_separator(self.ribbon.frame, height=self.ribbon.height)

        self.ribbon.add_node_button = Ribbon_Button(self.ribbon.frame, r'AddNode.png', r'AddNode_Select.png',
                                                    command=partial(self.change_mode, 'node', 'add'))
        self.ribbon.delete_node_button = Ribbon_Button(self.ribbon.frame, r'DeleteNode.png', r'DeleteNode_Select.png', command=partial(self.change_mode, 'node', 'delete'))
        self.ribbon.move_node_button = Ribbon_Button(self.ribbon.frame, r'Blank.png', r'Blank.png', command=partial(self.change_mode, 'node', 'move'))

        # add separator
        self.add_separator(self.ribbon.frame, height=self.ribbon.height)

        self.ribbon.add_pipe_button = Ribbon_Button(self.ribbon.frame, r'Blank.png', r'Blank.png', command=partial(self.change_mode, 'pipe', 'add'))

        self.ribbon.delete_pipe_button = Ribbon_Button(self.ribbon.frame, r'Blank.png', r'Blank.png',
                                                    command=partial(self.change_mode, 'pipe', 'add'))

        self.ribbon.reconnect_pipe_button = Ribbon_Button(self.ribbon.frame, r'Blank.png', r'Blank.png',
                                                    command=partial(self.change_mode, 'pipe', 'reconnect'))

        # create text ribbon
        self.text_ribbon = Ribbon(self, 16)
        self.text_ribbon.frame.pack(side='top', expand=False, fill='x')

        # create main frame
        self.main = Main(self)
        self.main.main_frame.pack(side='bottom', expand=True, fill='both')
        self.main.canvas.pack(side='left', expand=True, fill='both')
        #self.main.xsb.pack(expand=False, fill='both')
        self.main.side_pane.pack(side='right', expand=False, fill='both')

        # set default mode to select
        self.change_mode('select', None)
        self.drawing = False

    def add_separator(self, frame, height):
        # method to add a vertical separator of specified height to a frame
        sep1 = tk.Frame(frame, width=8, height=height, bg='white')
        sep1.pack(side='left', expand=False, fill='x')
        sep2 = tk.Frame(frame, width=1, height=height, highlightbackground='black', highlightthickness=1, bg='white')
        sep2.pack(side='left', expand=False, fill='x')
        sep3 = tk.Frame(frame, width=8, height=height, bg='white')
        sep3.pack(side='left', expand=False, fill='x')


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

