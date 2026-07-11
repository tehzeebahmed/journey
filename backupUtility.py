import shutil
import os

def take_backup(file_name: str):
    return(shutil.copy2(file_name, file_name+'.BAK'))
