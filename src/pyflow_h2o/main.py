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


class MainApplication(tk.Frame):
    def __init__(self, parent,*args, **kwargs):
        self.parent = parent
        self.frame = tk.Frame.__init__(self, parent, *args, **kwargs)


if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root).pack(side='top', fill='both', expand=True)
    root.mainloop()

