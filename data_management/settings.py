import configparser
import os

CONFIG = configparser.ConfigParser()
if os.path.exists(os.path.join(os.path.expanduser('~'), 'config.ini')):
    CONFIG.read(os.path.join(os.path.expanduser('~'), 'config.ini'))
    REMOTE_REGISTRY = True
else:
    REMOTE_REGISTRY = False
