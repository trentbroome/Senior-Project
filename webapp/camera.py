from flask import Flask, render_template, redirect, url_for, request, session, flash, redirect, logging, request, send_file

from picamera.array import PiRGBArray
from picamera import PiCamera
from flask_sqlalchemy import SQLAlchemy

import numpy as np
import cv2 as cv
import os
import sys
import shutil
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///face.sqlite3'
app.config['SECRET_KEY'] = "random string"
db = SQLAlchemy(app)
class Faces(db.Model):
   id = db.Column('faceID', db.Integer, primary_key = True)
   name = db.Column(db.String(100))
   userType = db.Column(db.String(50))
   

   def __init__(self, name, userType):
      self.name = name
      self.userType = userType
db.create_all()

def image():
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 30

    rawCapture = PiRGBArray(camera, size = (640, 480))
    face_cascade=cv.CascadeClassifier(cv.data.haarcascades +"haarcascade_frontalface_default.xml")

    name = request.form["name"]
    dirName = "./images/" + name
    os.makedirs(dirName)
    print("Directory Created")
        
    count = 1
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        if count > 30:
            shutil.make_archive("/home/pi/webapp/zip/" +name, "zip", "/home/pi/webapp/images/" + name)
            break
        frame = frame.array
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor = 1.5, minNeighbors = 5)
        for (x, y, w, h) in faces:
            roiGray = gray[y:y+h, x:x+w]
            fileName = dirName + "/" + name + str(count) + ".jpg"
            cv.imwrite(fileName, roiGray)
            cv.imshow("face", roiGray)
            cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            count += 1
            
        cv.imshow('frame', frame)
        key = cv.waitKey(1)
        rawCapture.truncate(0)
        
        if key == 27:
            break
    
    cv.destroyAllWindows()
    camera.close()
