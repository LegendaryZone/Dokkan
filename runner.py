import sampleCollector
from datetime import datetime
import urllib.request
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import os
import cv2
import numpy as np
from matplotlib import pyplot as plt



#
#fileSeparator = "\\"
#captchaDir = os.path.dirname(os.path.realpath(__file__)) + fileSeparator + "captcha_source" +  fileSeparator
#puzzleDir = os.path.dirname(os.path.realpath(__file__)) + fileSeparator + "captcha_puzzle" +  fileSeparator
#pieceDir = os.path.dirname(os.path.realpath(__file__)) + fileSeparator + "captcha_piece" +  fileSeparator
#
#
#
#
#
#sampleCollector.postProcessCaptcha(captchaDir)




image = cv2.imread('screenshot.png', True)
out = np.zeros((320,214,3), np.uint8)
r = cv2.selectROI("Image", image, False, False)
cv2.imshow('image', r)