import configparser
import os

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.expanduser('~'), 'config.ini'))
