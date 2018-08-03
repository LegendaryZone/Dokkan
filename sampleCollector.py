from datetime import datetime
import time
import os
import urllib.request
import math
import cv2
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

import puzzleSolver
import settings


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
            os.rename(imageFileName, os.path.join(settings.CAPTCHADIR, imageFileName))        
            count += 1
            
            #click on refresh to get the next image
            refreshElement = driver.find_element_by_xpath("//a[contains(@id,'change')]")
            refreshElement.click()
        else:
            #if next image hasn't been loaded yet, then wait for some time.
            #currently it is 3 seconds, reduce it based on your network connection speed.
            time.sleep(3)
    driver.close()

def movePieceToPuzzle(_driver, _piece, _GP, _P1, _P2):
    gx1, gy1 = _GP
    x2, y2 = _P1
    #print("Piece Coord : " + str(_P2[0]) + "," + str(_P2[1]))
    # x2 = x2 + _P2[0] - 50
    # y2 = y2 + _P2[1] - 50
    actionChains = ActionChains(_driver)
    actionChains.move_to_element(_piece)
    actionChains.perform()
    actionChains.click_and_hold(_piece)

    xOffset = 0
    yOffset = 0
    speed = 5

    """Slant movement as far as possible."""
    if(gx1 < x2):
        slope = math.ceil((y2 - gy1) / (x2 - gx1))
        if(slope == 0):
            slope = -1
        if(slope > 0):
            slope *= -1
        xOffset = 1 * speed
        while(gx1 <= x2 and gy1 >= y2):
            actionChains.move_by_offset(xOffset, slope * speed)
            gx1 += xOffset
            gy1 += slope * speed
        actionChains.move_by_offset(gx1 - x2, slope * speed)
        gy1 += slope * speed
    elif(gx1 > x2):
        slope = math.ceil((y2 - gy1) / (x2 - gx1))
        if(slope == 0):
            slope = -1
        if(slope > 0):
            slope *= -1
        xOffset = -1 * speed
        while(x2 <= gx1 and gy1 >= y2):
            actionChains.move_by_offset(xOffset, slope * speed)
            gx1 += xOffset
            gy1 += slope * speed
        actionChains.move_by_offset(x2 - gx1, slope * speed)
        gy1 += slope * speed

    """Remaining distance by robotic"""
    if(gy1 > y2):
        yOffset = -1 * speed
        while(gy1 >= y2):
            actionChains.move_by_offset(0, yOffset)
            gy1 += yOffset
        actionChains.move_by_offset(0, y2 - gy1)
    elif(gy1 < y2):
        yOffset = 1 * speed
        while(gy1 <= y2):
            actionChains.move_by_offset(0, yOffset)
            gy1 += yOffset
        actionChains.move_by_offset(0, gy1 - y2)
    
    actionChains.release()
    actionChains.perform()

def postProcessCaptcha(capDir):
    directory = os.fsencode(capDir)

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        image_path = os.path.join(settings.CAPTCHADIR, filename)
        if filename.endswith(".png"): 
            img = cv2.imread(image_path)           
            height, width, channels = img.shape
            if(img is not None):
                puzzle = img[0:214, 0:320]
                cv2.imwrite(os.path.join(settings.PUZZLEDIR, filename), puzzle)
                
                if(width == 840):
                    piece1 = img[5:105, 325:425]
                    piece1Name = os.path.splitext(filename)[0] + "_piece1.png"
                    cv2.imwrite(os.path.join(settings.PIECEDIR, piece1Name), piece1)
                    piece2 = img[5:105, 460:560]
                    piece2Name = os.path.splitext(filename)[0] + "_piece2.png"
                    cv2.imwrite(os.path.join(settings.PIECEDIR, piece2Name), piece2)
                elif(width == 540):
                    piece = img[5:105, 325:425]
                    cv2.imwrite(os.path.join(settings.PIECEDIR, filename), piece)
                os.remove(image_path)              
            continue
        else:
            continue    

if __name__ == '__main__':
    createSamples("http://localhost/Captcha.html")
    postProcessCaptcha(settings.CAPTCHADIR)

def solveCaptcha(_pageURL, _mode=settings.SOLVEMODE):
    driver = settings.BROWSER
    driver.get(_pageURL)
    assert "Authorize with Captcha" in driver.title
    
    GP = None
    GP2 = None
    P1 = None
    P2 = None
    SP1 = None
    SP2 = None
    firstPiece = None
    secondPiece = None

    while True:
        driver.refresh()

        imageElement = driver.find_element_by_xpath("//img[contains(@name,'image')]")
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
        image = cv2.imread('screenshot.png', True)

        cropped = image[loc['y']:loc['y'] + 214 , loc['x']:loc['x'] + 320]    
        puzzlePath = os.path.join(settings.PUZZLEDIR, imageFileName) 
        cv2.imwrite(puzzlePath, cropped)
        
        pieces = pieceElement.find_elements_by_tag_name("div")
        style = pieces[0].get_attribute("style")
        allPieces = pieces[0].find_elements_by_tag_name("div")
        firstPiece = allPieces[0]
        firstText = [x.strip() for x in style.split(';')]
        top = [x.strip() for x in firstText[-3].split(':')][-1]
        left = [x.strip() for x in firstText[-2].split(':')][-1]
        gy1 = top[:-2]
        gx1 = left[:-2] 
        GP = (int(gx1), int(gy1))

        #print("{}, {}".format(gx1, gy1))

        floc = firstPiece.location
        fpCropped = image[floc['y']:floc['y'] + 100 , floc['x']:floc['x'] + 100]
        cv2.imwrite(imageFileName, cropped)
        if(len(allPieces) == 2):
            #print("Second Jigsaw!!")
            piece1Name = os.path.splitext(imageFileName)[0] + "_piece1.png"
            piece1Path = os.path.join(settings.PIECEDIR, piece1Name)
            cv2.imwrite(piece1Path, fpCropped)

            secondPiece = allPieces[1]
            sloc = secondPiece.location
            spCropped = image[sloc['y']:sloc['y'] + 100, sloc['x']:sloc['x'] + 100]
            piece2Name = os.path.splitext(imageFileName)[0] + "_piece2.png"
            piece2Path = os.path.join(settings.PIECEDIR, piece2Name)


            cv2.imwrite(piece2Path, spCropped)
        else:
            piece1Path = os.path.join(settings.PIECEDIR, imageFileName)
            cv2.imwrite(piece1Path, fpCropped) 

        P1, P2 = puzzleSolver.getResultCoordinates(puzzlePath, piece1Path, mode=_mode)
        if(piece2Path is not None):
            SP1, SP2 = puzzleSolver.getResultCoordinates(puzzlePath, piece2Path, mode=_mode)

        #Clean up if mode is SOLVEMODE
        if(_mode == settings.SOLVEMODE):
            os.remove('screenshot.png')
            os.remove(puzzlePath)
            os.remove(imageFileName)
            os.remove(piece1Path)      
            if(piece2Path is not None):
                os.remove(piece2Path)
        if(P1 is not None and P2 is not None):
            if(piece2Path is not None):
                if(SP1 is not None and SP2 is not None):
                    break
            else:
                break

    movePieceToPuzzle(driver, firstPiece, GP, P1, P2)
    if GP2 is not None:
        movePieceToPuzzle(driver, secondPiece, GP2, SP1, SP2)

    #Submit the puzzle and wait for result
    driver.find_element_by_xpath("/html/body/div/form/button").click()