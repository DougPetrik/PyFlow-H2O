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



