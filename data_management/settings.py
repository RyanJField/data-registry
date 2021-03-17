import configparser
import os

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.environ['HOME'], 'config.ini'))
