from datetime import datetime

from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
from selenium import webdriver
import os
import cv2
import numpy as np
from matplotlib import pyplot as plt
import threading
import puzzleSolver

#variables used by createSamples module
#pageURL : url of the authentication page
#imgName : name attribute of image [right click puzzle -> inspect element -> name attribute ..] typically of form xxxxxxxximage
#refreshID : id attribute of refresh icon [right click refresh icon -> inspect element -> id attribute ..] typically of form xxxxxxxxchange

#path variables
fileSeparator = "\\"
captchaDir = os.path.dirname(os.path.realpath(__file__)) + fileSeparator + "captcha_source" +  fileSeparator
puzzleDir = os.path.dirname(os.path.realpath(__file__)) + fileSeparator + "captcha_puzzle" +  fileSeparator
pieceDir = os.path.dirname(os.path.realpath(__file__)) + fileSeparator + "captcha_piece" +  fileSeparator


class WindowFinder:
    #Class to find and make focus on a particular Native OS dialog/Window
    def __init__ (self):
        self._handle = None

    def find_window(self, class_name, window_name = None):
        #Pass a window class name & window name directly if known to get the window
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        #Call back func which checks each open window and matches the name of window using reg ex
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) != None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        #This function takes a string as input and calls EnumWindows to enumerate through all open windows
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground(self):
        #Get the focus on the desired open window
        win32gui.SetForegroundWindow(self._handle)




def createSamples(_pageURL, _chrome_options=None, nSamples=1):
    if(_chrome_options is None):
        _chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(chrome_options=_chrome_options)
    driver.get(_pageURL)
    assert "Authorize with Captcha" in driver.title
    driver.refresh()
    oldTag = ""
    count = 0

    
    if(nSamples is None or nSamples <= 0):
        nSamples = 1
    #Get 1000 captchas for sample
    while(count != nSamples):   
        imageElement = driver.find_element_by_xpath("//img[contains(@name,'image')]")
        imageSource = imageElement.get_attribute("src")

        #to determine if new image has been loaded or not
        if(oldTag != imageSource):
            oldTag = imageSource
            imageFileName = "captcha" + datetime.now().strftime('%H%M%S') + ".png"
            
            #urrlib doesn't allow to save to different folder, so moving is necessary (or so it seems)
            urllib.request.urlretrieve(oldTag, imageFileName)
            os.rename(imageFileName, os.path.join(captchaDir, imageFileName))
            
            count += 1;
            
            #click on refresh to get the next image
            refreshElement = driver.find_element_by_xpath("//a[contains(@id,'change')]")
            refreshElement.click()
        else:
            #if next image hasn't been loaded yet, then wait for some time.
            #currently it is 3 seconds, reduce it based on your network connection speed.
            time.sleep(3)
    
    return driver
    


def solveCaptcha(_pageURL, _chrome_options=None, _mode=2):
    if(_chrome_options is None):
        #print('Chrome options is none')
        _chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(chrome_options=_chrome_options)
    driver.get(_pageURL)
    assert "Authorize with Captcha" in driver.title
    
    while True:
        driver.refresh()

        imageElement = driver.find_element_by_xpath("//img[contains(@name,'image')]")
        imageSource = imageElement.get_attribute("src")
        #print("Image URL : {}".format(imageSource))
        refreshElement = driver.find_element_by_xpath("//a[contains(@id,'change')]")
        pieceElement = driver.find_element_by_xpath("//div[contains(@id,'pieces')]")
        refreshID = refreshElement.get_attribute("id")
        hideScript = "document.getElementById('" + str(refreshID) + "').style.display = 'none';"
        showScript = "document.getElementById('" + str(refreshID) + "').style.display = 'block';"
        driver.execute_script(hideScript)
        imageFileName = "captcha" + datetime.now().strftime('%j%H%M%S') + ".png"

        puzzlePath = None
        piece1Path = None
        piece2Path = None

        driver.save_screenshot('screenshot.png')
        driver.execute_script(showScript)
        loc = imageElement.location
        width = 320
        height = 214
        image = cv2.imread('screenshot.png', True)

        cropped = image[loc['y']:loc['y'] + 214 , loc['x']:loc['x'] + 320]    
        puzzlePath = os.path.join(puzzleDir, imageFileName) 
        cv2.imwrite(puzzlePath, cropped)
        os.remove('screenshot.png')
        pieces = pieceElement.find_elements_by_tag_name("div")
        style = pieces[0].get_attribute("style")
        allPieces = pieces[0].find_elements_by_tag_name("div")
        firstPiece = allPieces[0]
        firstText = [x.strip() for x in style.split(';')]
        top = [x.strip() for x in firstText[-3].split(':')][-1]
        left = [x.strip() for x in firstText[-2].split(':')][-1]
        y1 = top[:-2]
        x1 = left[:-2] 
        print("{}, {}".format(x1,y1))
        pieceImage = firstPiece.find_elements_by_tag_name("img")[0]
        actionChains = ActionChains(driver)


        floc = firstPiece.location
        fpCropped = image[floc['y']:floc['y'] + 100 , floc['x']:floc['x'] + 100]
        cv2.imwrite(imageFileName, cropped)
        if(len(allPieces) == 2):
            #print("Second Jigsaw!!")
            piece1Name = os.path.splitext(imageFileName)[0] + "_piece1.png"
            piece1Path = os.path.join(pieceDir, piece1Name)
            cv2.imwrite(piece1Path, fpCropped)

            secondPiece = allPieces[1]
            sloc = secondPiece.location
            spCropped = image[sloc['y']:sloc['y'] + 100 , sloc['x']:sloc['x'] + 100]
            piece2Name = os.path.splitext(imageFileName)[0] + "_piece2.png"
            piece2Path = os.path.join(pieceDir, piece2Name)


            cv2.imwrite(piece2Path, spCropped)
        else:
            piece1Path = os.path.join(pieceDir, imageFileName)
            cv2.imwrite(piece1Path, fpCropped) 

        x2 , y2 = puzzleSolver.getResultCoordinates(puzzlePath, piece1Path, piece2Path, mode=_mode)
        os.remove(puzzlePath)
        os.remove(imageFileName)
        os.remove(piece1Path)
        
        if(piece2Path is not None):
            os.remove(piece2Path)
        if(x is not None and y is not None):
            break
    actionChains.move_to_element(firstPiece)
    actionChains.perform()
    actionChains.click_and_hold(firstPiece)
    
    actionChains.move_to_element(firstPiece)
    actionChains.perform()
    actionChains.click_and_hold(firstPiece)
    
    if(x2 != x1):
        slope = (y2 - y1)/(x2 - x1)
        while(x1 != x2):
            actionChains.move_by_offset(1, slope)
            x2 
            
    else:
        while(y1 != y2):
            actionChains.move_by_offset(0, -1)
            y2 -= 1
        
    

    actionChains.release()
    actionChains.perform()
    driver.find_element_by_xpath("/html/body/div/form/button").click()
    return (driver, (x,y))
    
    
def postProcessCaptcha(capDir):   
    directory = os.fsencode(capDir)

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        image_path = os.path.join(captchaDir, filename)
        if filename.endswith(".png"): 
            img = cv2.imread(image_path)           
            height, width, channels = img.shape
            if(img is not None):
                puzzle = img[0:214, 0:320]
                cv2.imwrite(os.path.join(puzzleDir, filename), puzzle)
                
                if(width == 840):
                    piece1 = img[5:105, 325:425]
                    piece1Name = os.path.splitext(filename)[0] + "_piece1.png"
                    cv2.imwrite(os.path.join(pieceDir, piece1Name), piece1)
                    piece2 = img[5:105, 460:560]
                    piece2Name = os.path.splitext(filename)[0] + "_piece2.png"
                    cv2.imwrite(os.path.join(pieceDir, piece2Name), piece2)
                elif(width == 540):
                    piece = img[5:105, 325:425]
                    cv2.imwrite(os.path.join(pieceDir, filename), piece)
                os.remove(image_path)              
            continue
        else:
            continue

if __name__ == '__main__':
    driver = createSamples("http://localhost/Captcha.html")
    driver.close()
    postProcessCaptcha(captchaDir)











