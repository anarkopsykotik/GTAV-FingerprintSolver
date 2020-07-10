import tkinter as tk
import numpy as np
import cv2
import win32gui
from ctypes import windll
import imutils
import subprocess
import time
import mss
import sys
import os 
from matplotlib import pyplot as plt
from PIL import Image, ImageTk, ImageGrab
import glob

class UI(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # create a prompt, an input box, an output label,
        # and a button to do the computation
        self.prompt = tk.Label(self, text="Grab image from GTA and launch analysis", anchor="w")
        #self.entry = tk.Entry(self)
        self.imgResult = tk.Label(self)
        self.submit = tk.Button(self, text="SOLVE", command = self.analyse)
        #self.submit = tk.Button(self, text="GET SCREEN", command = self.getGTAScreen)

        # lay the widgets out on the screen. 
        self.prompt.pack(side="top", fill="x")
        #self.entry.pack(side="top", fill="x", padx=20)
        self.submit.pack(side="bottom")
        self.imgResult.pack(side="bottom")
        

    def getGTAScreen(self):
        #list_of_files = glob.glob(self.entry.get() + "\*.jpg" ) # * means all if need specific format then *.csv
        im = ImageGrab.grabclipboard()
        #latest_file = max(list_of_files, key=os.path.getctime)
        #print(latest_file)
        return im       

    def analyse(self):
        latestScreen = self.getGTAScreen()
        #image = cv2.imread(latestScreen)
        image = cv2.cvtColor(np.array(latestScreen), cv2.COLOR_BGR2RGB)
        #image = cv2.cv2.fromarray(latestScreen)
        #image = cv2.imread('test3.jpg')
        copy = image.copy()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray,40,255,cv2.THRESH_BINARY)[1]
        cnts = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        ROI_number = 0
        fingerpartsOptions = []
        fingerpartsOptionsBounds = []

        #for each contour found, check size/coord
        #to get the fingerprint and options. Also get the corresponding rectangles to draw
        foundSolutionsCoord = []
        closeSolutionsCoord = []
        rightAnswers=[]
        for c in cnts:
            x,y,w,h = cv2.boundingRect(c)
            ROI = image[y:y+h, x:x+w]
            
            if (w > 400 and h > 400 and abs(w-h)<20):#select the fingerpritn to match
                #print("got fingerprint",x)
                cv2.rectangle(copy,(x,y),(x+w,y+h),(36,255,12),2)
                fingerprintImg = ROI
            if (w > 110 and x < 860 and abs(w-h)<5): #those are the options
                coord = x,y
                #print(coord)

                if(coord not in foundSolutionsCoord and coord not in closeSolutionsCoord):
                    #print("appended")
                    foundSolutionsCoord.append(coord)
                    closeSolutionsCoord.append((x-1,y)) #ugly, find cleaner way
                    closeSolutionsCoord.append((x-1,y-1))
                    closeSolutionsCoord.append((x,y-1))
                    closeSolutionsCoord.append((x+1,y))
                    closeSolutionsCoord.append((x+1,y+1))
                    closeSolutionsCoord.append((x,y+1))
                    #print(closeSolutionsCoord)
                    #foundSolutionsCoord.append(coord2) #todo fixme add it better
                    cv2.rectangle(copy,(x,y),(x+w,y+h),(255,1,1),2)
                    #print("potential solution", w,"-",h,"-","-",x,"-",y)
                    cv2.rectangle(copy,(x,y),(x+w,y+h),(255,1,12),2)
                    fingerpartsOptions.append(ROI)
                    fingerpartsOptionsBounds.append(c)
                    ROI_number += 1
        #print (len(fingerpartsOptions))
        scalingVals = [0.75, 0.8]
        for scale in scalingVals:
            i=0
            resized = imutils.resize(fingerprintImg, width = int(fingerprintImg.shape[1] * scale))
            for option in fingerpartsOptions:
                optName= "option" + str(i)
                option = cv2.Canny(option, 50, 200)
                (tH, tW) = option.shape[:2]
                # resize the image according to the scale, and keep track
                # of the ratio of the resizing
                r = fingerprintImg.shape[1] / float(resized.shape[1])
                # detect edges in the resized, grayscale image and apply template
                # matching to find the template in the image
                edged = cv2.Canny(resized, 50, 200)
                result = cv2.matchTemplate(edged, option, cv2.TM_CCOEFF)
                (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)

                #compute the (x, y) coordinates
                # of the bounding box based on the resized ratio
                (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
                (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
                # draw a bounding box around the detected result and display the image
                if(maxVal>31000000): #TODO select 4 highest instead of above val
                    print(maxVal)
                    #cv2.rectangle(fingerprintImg, (startX, startY), (endX, endY), (0, 0, 255), 2)
                    #draw correct solutions
                    x,y,w,h = cv2.boundingRect(fingerpartsOptionsBounds[i])
                    answer = maxVal,x,y,w,h
                    rightAnswers.append(answer)
                    #cv2.rectangle(copy,(x,y),(x+w,y+h),(36,255,12),2)
                i+=1

        if(len(rightAnswers) <= 4):
            for answer in rightAnswers:
                maxVal,x,y,w,h=answer
                cv2.rectangle(copy,(x,y),(x+w,y+h),(36,255,12),2)
        else:
            highestVal=0
            vals=[]
            for answer in rightAnswers:
                maxVal,x,y,w,h=answer
                vals.append(maxVal)
            while(len(vals) > 4):
                vals.remove(min(vals))
            for answer in rightAnswers:
                maxVal,x,y,w,h=answer
                if(maxVal in vals):
                    cv2.rectangle(copy,(x,y),(x+w,y+h),(36,255,12),2)
            
        #display result

        #resize result for easier read
        resultResize = imutils.resize(copy, width = int(fingerprintImg.shape[1] * 0.4))

        # Convert the Image object into a TkPhoto object
        imUI = Image.fromarray(resultResize)
        imgtk = ImageTk.PhotoImage(image=imUI) 

        # Put it in the display window
        self.imgResult.image = imgtk
        self.imgResult.configure(image=imgtk)

        #cv2.imshow('copy', copy)
        #cv2.imshow("Image", fingerprintImg)

if __name__ == "__main__":
    root = tk.Tk()
    UI(root).pack(fill="both", expand=True)
    root.mainloop()
