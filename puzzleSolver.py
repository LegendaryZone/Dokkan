from __future__ import division
from collections import namedtuple
import numpy as np
import cv2
import math
import heapq as hq
import argparse
import os


#SOME GLOBAL VARS
#Change the unique image directory as per your config.
VFMODE      = 1
SOLVEMODE   = 2
HOMMODE     = 3
MIN_MATCH_COUNT = 10
fileSeparator = "\\"
puzzleDir = os.path.dirname(os.path.realpath(__file__)) + fileSeparator + "captcha_puzzle" + fileSeparator
COMPLETED_DIR = puzzleDir + "completedPuzzle" + fileSeparator + "ping"
pieceDir = os.path.dirname(os.path.realpath(__file__)) + fileSeparator + "captcha_piece" +  fileSeparator


def get_key(item):
    return(item[0])

def getNearestPoints(points):
    point = []
    heap = []
    pt = namedtuple('pt', 'x y')
    for i in range(len(points)):
        point.append(pt(points[i][0], points[i][1]))
    
    point = sorted(point, key=get_key)
    visited_index = []
    find_min(0, len(point) - 1, point, heap, visited_index)
    try:
        dist, (x, y) = hq.heappop(heap)
    except IndexError:
        return None
    return (x,y)

def find_min(start, end, point, heap, visited_index):
    if len(point[start:end + 1]) & 1:
        mid = start + ((len(point[start:end + 1]) + 1) >> 1)
    else:
        mid = start + (len(point[start:end + 1]) >> 1)
        if start in visited_index:
            start = start + 1
        if end in visited_index:
            end = end - 1
    if len(point[start:end + 1]) > 3:
        if start < mid - 1:
            distance1 = math.sqrt((point[start].x - point[start + 1].x) ** 2 + (point[start].y - point[start + 1].y) ** 2)
            distance2 = math.sqrt((point[mid].x - point[mid - 1].x) ** 2 + (point[mid].y - point[mid - 1].y) ** 2)
            if distance1 < distance2:
                hq.heappush(heap, (distance1, ((point[start].x, point[start].y), (point[start + 1].x, point[start + 1].y))))
            else:
                hq.heappush(heap, (distance2, ((point[mid].x, point[mid].y), (point[mid - 1].x, point[mid - 1].y))))
            visited_index.append(start)
            visited_index.append(start + 1)
            visited_index.append(mid)
            visited_index.append(mid - 1)
            find_min(start, mid, point, heap, visited_index)
        if mid + 1 < end:
            distance1 = math.sqrt((point[mid].x - point[mid + 1].x) ** 2 + (point[mid].y - point[mid + 1].y) ** 2)
            distance2 = math.sqrt((point[end].x - point[end - 1].x) ** 2 + (point[end].y - point[end - 1].y) ** 2)
            if distance1 < distance2:
                hq.heappush(heap, (distance1, ((point[mid].x, point[mid].y), (point[mid + 1].x, point[mid + 1].y))))
            else:
                hq.heappush(heap, (distance2, ((point[end].x, point[end].y), (point[end - 1].x, point[end - 1].y))))
            visited_index.append(end)
            visited_index.append(end - 1)
            visited_index.append(mid)
            visited_index.append(mid + 1)
            find_min(mid, end, point, heap, visited_index)


def drawMatches(img1, kp1, img2, kp2, matches):
    
    #get image1 dimensions
    rows1 = img1.shape[0]
    cols1 = img1.shape[1]
    
    #failsafe for both grayscale(single channel) and colored images (3 channels) 
    chan1 = None   
    try:
        chan1 = img1.shape[2]
    except IndexError:
        chan1 = 1
    
    #get image2 dimensions
    rows2 = img2.shape[0]
    cols2 = img2.shape[1]
        
    out = None
    if(chan1 == 1):
        out = np.zeros((max([rows1,rows2]),cols1+cols2, 3), dtype='uint8')
        # Place the first image to the left
        out[:rows1,:cols1] = np.dstack([img1, img1, img1])

        # Place the next image to the right of it
        out[:rows2,cols1:] = np.dstack([img2, img2, img2])
    elif(chan1 == 3):
        out = np.zeros((max([rows1,rows2]),cols1+cols2, chan1), dtype='uint8')
        out[:rows1,:cols1] = np.dstack([img1])
        out[:rows2,cols1:] =  np.dstack([img2])

    # For each pair of points we have between both images
    # draw circles, then connect a line between them
    puzzlePoints = []
    jigsawPoints = []
    blueColor = (255, 0, 0)
    previousP1 = None
    previousP2 = None
    for mat in matches:
        # Get the matching keypoints for each of the images
        img1_idx = mat.queryIdx
        img2_idx = mat.trainIdx

        (x1,y1) = kp1[img1_idx].pt
        (x2,y2) = kp2[img2_idx].pt
        
        p1 = (int(x1),int(y1))
        p2 = (int(x2),int(y2))
        
        if(previousP1 != p1 and previousP2 != p2):
            previousP1 = p1
            previousP2 = p2
            puzzlePoints.append(p2)
            jigsawPoints.append(p1)
            #debug mode
            #print(str(p1) + "->" + str(p2)) 
            cv2.circle(out, (int(x1), int(y1)), 4, blueColor, 1)   
            cv2.circle(out, (int(x2)+cols1,int(y2)), 4, blueColor, 1)      
            cv2.line(out, (int(x1), int(y1)), (int(x2)+cols1,int(y2)), blueColor, 1)
    
    puzzleResult = None
    if(len(puzzlePoints) > 2):
        puzzleResult = getNearestPoints(puzzlePoints)
    else:
        puzzleResult = (puzzlePoints)
    
    if(puzzleResult is None):
        return (None, None, None)
    
    jigSawResult = None
    if(len(jigsawPoints) > 2):     
        jigSawResult = getNearestPoints(jigsawPoints)
    else:
        jigSawResult = (jigsawPoints)
    
    if(jigSawResult is None):
        return (None, None, None)
    
    return (out,puzzleResult, jigSawResult)

def verifyImage(img1, img2, mode=SOLVEMODE):
    # Detect the SIFT key points and compute the descriptors for the two images
    sift = cv2.xfeatures2d.SIFT_create()
    keyPoints1, descriptors1 = sift.detectAndCompute(img1, None)
    keyPoints2, descriptors2 = sift.detectAndCompute(img2, None)

    # Create brute-force matcher object
    bf = cv2.BFMatcher()

    # Match the descriptors
    matches = bf.knnMatch(descriptors1, descriptors2, k=2)
    goodMatches = []

    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            goodMatches.append(m)

    
    if(mode == VFMODE):
        return len(goodMatches)  
    else:
        if(len(goodMatches) > 0):
            result, puzzleCoord, pieceCoord = drawMatches(img1, keyPoints1, img2, keyPoints2, goodMatches)
            if(result is None or puzzleCoord is None or pieceCoord is None):
                return (None, None, None, None)
            if len(goodMatches) >= MIN_MATCH_COUNT:
                # Get the possible solution coordinates
                sourcePoints = np.float32([ keyPoints1[m.queryIdx].pt for m in goodMatches ]).reshape(-1, 1, 2)
                destinationPoints = np.float32([ keyPoints2[m.trainIdx].pt for m in goodMatches ]).reshape(-1, 1, 2)

                # Obtain the homography matrix
                M, mask = cv2.findHomography(sourcePoints, destinationPoints, method=cv2.RANSAC, ransacReprojThreshold=5.0)
                matchesMask = mask.ravel().tolist()

                #for dealing with colored images.
                h = 0
                w = 0
                c = 0
                try:
                    h, w = img1.shape
                except ValueError:
                    h, w, c = img1.shape

                corners = np.float32([ [0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0] ]).reshape(-1, 1, 2)
                transformedCorners = cv2.perspectiveTransform(corners, M)

                #to get the generalized area where the puzzle couldbe
                img2 = cv2.polylines(img2, [np.int32(transformedCorners)], True, (255, 255, 255), 2, cv2.LINE_AA)
                return None, img2, puzzleCoord, pieceCoord
            else:
                #print('Insufficient match found to draw solution area')
                return result, None, puzzleCoord, pieceCoord
        else:
            return (None, None, None, None)
        
#
#Main Module to solve the puzzle
#Has 3 possible outcome
#Outcome1:  (None, None) returned if puzzle can't be solved due to unavailability of parent image
#Outcome2:  (0, 0) returned if the given puzzle is hard to solve by solver.
#Outcome3:  (x, y) co-ordinates as to where to place the jigsaw piece in the puzzle 

def getResultCoordinates(_puzzlePath, _piecePath, _piece2Path=None, cdir=COMPLETED_DIR, mode=SOLVEMODE):
    
    puzzle = cv2.imread(_puzzlePath)
    piece1 = cv2.imread(_piecePath)

    ##Debugging
    #print("Reading : " + (pieceDir + firstPiece))
    #cv2.imshow('Piece1', piece1)
    #print("Reading : " + (puzzleDir + puzzleName))
    #cv2.imshow('Piece1', puzzle)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    piece2 = None
    parentImage = None
    parentFileName = None
    if(_piece2Path is not None):
        piece2 = cv2.imread(_piece2Path)

    #Iterate through solved puzzle directory to determine the source/parent image.                
    directory = os.fsencode(cdir)
    for file in os.listdir(directory):

        #Browsing directory for all .png images (can use bitmap too, doesnt' matter)
        filename = os.fsdecode(file)
        image_path = os.path.join(cdir, filename)
        if filename.endswith(".png"): 
            sample = cv2.imread(image_path)

            #get the number of properities that are matching between the 2 images
            #if greater than 250, then they are similar.
            nMatches = verifyImage(puzzle,sample,VFMODE)
            if(nMatches > 100):
                parentImage = sample
                parentFileName = filename
                break
            else:
                continue
        else:
            continue

    if(parentImage is None):
        #If even after iterating, a parent image is not found, then it might be new image altogether
        #Run the sampleCollector program to collect more sample of such images
        #Then create a completed puzzle from those samples and add to the existing collection of COMPLETEDIR folder
        #Re-run it
        print('No source image has been found. A new image( perhaps ?)')
        return (None, None)
    else:
        #If found , then find the co-ordinates where the puzzle piece belongs to
        
        partialSolution, solution, puzzleCoord, pieceCoord = verifyImage(piece1, sample, mode)

        result = solution
        if(solution is None):
            result = partialSolution

        #If no coordinates are found, then the puzzle is highly confusing, try next one
        if(result is None or puzzleCoord is None or pieceCoord is None):

            #Typically happens against plain vanilla images (e.g teacup and sunrise. Both are a pain in ***)
            #print("Failed to solve puzzle gainst source :" + str(parentFileName))
            return (None, None)
        else:
            #If found, output the solution location
            resultPosition1 = ((puzzleCoord[0][0] - pieceCoord[0][0]), (puzzleCoord[0][1] - pieceCoord[0][1]))
            if(len(puzzleCoord) > 1):
                resultPosition2 = ((puzzleCoord[1][0] - pieceCoord[1][0]), (puzzleCoord[1][1] - pieceCoord[1][1]))
                print("{} or {}".format(resultPosition1, resultPosition2))
            else:
                print("{}".format(resultPosition1))
            
            if(mode == HOMMODE):
                cv2.imshow('Match', result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            return resultPosition1

if __name__ == '__main__':
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser(description='Solve the puzzle for piece')
    ap.add_argument("-p", "--puzzle", required = True,
        help = "Path to the puzzle image")
    ap.add_argument("-f", "--fjigsaw", required = True,
        help = "Path to the jigsaw image")
    ap.add_argument("-s", "--sjigsaw", required = False,
        help = "Path to the second jigsaw piece (optional)")
    args = vars(ap.parse_args())


    puzzleName = args["puzzle"]
    firstPiece = args["fjigsaw"]
    secondPiece = None
    
    if(args["sjigsaw"] is not None):
        secondPiece = args["sjigsaw"]
        getResultCoordinates(_puzzlePath = (puzzleDir + puzzleName), _piecePath = (pieceDir + firstPiece), _piece2Path = (pieceDir + secondPiece))
    else:
        #getResultCoordinates(_puzzlePath = (puzzleDir + puzzleName), _piecePath = (pieceDir + firstPiece), mode=HOMMODE)
        getResultCoordinates((puzzleDir + puzzleName), (pieceDir + firstPiece))
    
    
            
            
            