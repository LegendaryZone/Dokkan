"""Global Settings module"""
import os
import cv2
from selenium import webdriver
#To notify the module importing this module whether someone else already initialized it or not.
global INITIALIZED
INITIALIZED = 0
global BROWSER
BROWSER = None
global ATTEMPTS
ATTEMPTS = 0
global FIRSTTIMER
FIRSTTIMER = True
def init():
    """Loads all the completed images for later processing"""
    global INITIALIZED
    INITIALIZED = 1
    global VFMODE
    VFMODE = 1 
    global SOLVEMODE
    SOLVEMODE = 2
    global HOMMODE
    HOMMODE = 3
    global MIN_MATCH_COUNT
    MIN_MATCH_COUNT = 10
    global CURR_FILE_LOC
    CURR_FILE_LOC = os.path.dirname(os.path.realpath(__file__))
    global CAPTCHADIR
    CAPTCHADIR = CURR_FILE_LOC + "\\captcha_source\\"
    global PUZZLEDIR
    PUZZLEDIR = CURR_FILE_LOC + "\\captcha_puzzle\\"
    global COMPLETED_DIR
    COMPLETED_DIR = PUZZLEDIR + "completedPuzzle\\ping"
    global PIECEDIR
    PIECEDIR = CURR_FILE_LOC + "\\captcha_piece\\"
    global IMAGELIST
    IMAGELIST = []         
    directory = os.fsencode(COMPLETED_DIR)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        image_path = os.path.join(COMPLETED_DIR, filename)
        if filename.endswith(".png"):
            sample = cv2.imread(image_path)
            IMAGELIST.append(sample)
        else:
            continue

def init_browser(_chrome_options):
    global BROWSER
    BROWSER = webdriver.Chrome(chrome_options=_chrome_options)

