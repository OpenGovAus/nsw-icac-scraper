import os
import sys


def verify_dir(dirpath):
    if(not os.path.isdir(dirpath)):
        try:
            os.mkdir(dirpath)
        except PermissionError:
            sys.exit(f'Missing permissions to create directory {dirpath}')
