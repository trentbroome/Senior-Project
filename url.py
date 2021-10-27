from flask import Flask, render_template, redirect, url_for, request, session, flash, redirect, logging, request, send_file
from picamera.array import PiRGBArray
from picamera import PiCamera
from flask_sqlalchemy import SQLAlchemy
from PIL import Image 
import pickle
import shutil
import numpy as np
import cv2 as cv
import os
import sys

app = Flask(__name__)


camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30

rawCapture = PiRGBArray(camera, size = (640, 480))
face_cascade=cv.CascadeClassifier(cv.data.haarcascades +"haarcascade_frontalface_default.xml")


path = "/home/pi/webapp/images"
image_names = os.listdir(path)
   
   
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Users.sqlite3'
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))

@app.route("/")
def index():
    return render_template("index.html")



@app.route("/login",methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]
        
        login = Users.query.filter_by(username=uname, password=passw).first()
        if login is not None:
            return redirect(url_for("termProjectMain"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']

        register = Users(username = uname, email = mail, password = passw)
        db.session.add(register)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("Register.html")
    
    
    
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


@app.route('/home', methods = ['GET', 'POST'])
def home():
    return render_template('termProjectMain.html')

@app.route('/addDeleteFaces', methods = ['POST', 'GET'])
def addDeleteFaces():
    return render_template('addDeleteFaces.html', Faces = Faces.query.all())
    
@app.route('/new', methods = ['GET', 'POST'])
def new():
   if request.method == 'POST':
      if not request.form['name'] or not request.form['userType']:
         flash('Please enter all the fields', 'error')
      else:
         Face = Faces(request.form['name'], request.form['userType'])
         
         db.session.add(Face)
         db.session.commit()
         flash('Record was successfully added')
         return redirect(url_for('addDeleteFaces'))
   return render_template('addFace.html')

   
   
@app.route('/listdir', methods = ['POST', 'GET'])
def postdir():
    return render_template('testCamera.html', len = len(image_names), image_names = image_names)
    
@app.route("/image")
def getImage():
  rawCapture = PiRGBArray(camera, size = (640, 480))

  name = input("What's his/her Name? ")
  dirName = "./images/" + name + ".zip"
  os.makedirs(dirName)
  count = 1
  for frame in PiCamera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    if count > 30:
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

          return render_template('addDeleteFaces.html')
    
@app.route("/trainImages")
def train():
    face_cascade=cv2.CascadeClassifier(cv2.data.haarcascades +"haarcascade_frontalface_default.xml")
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    baseDir = os.path.dirname(os.path.abspath(__file__))
    imageDir = os.path.join(baseDir, "images")

    currentId = 1
    labelIds = {}
    yLabels = []
    xTrain = []

    for root, dirs, files in os.walk(imageDir):
        print(root, dirs, files)
        for file in files:
            print(file)
            if file.endswith("png") or file.endswith("jpg"):
                path = os.path.join(root, file)
                label = os.path.basename(root)
                print(label)

                if not label in labelIds:
                    labelIds[label] = currentId
                    print(labelIds)
                    currentId += 1

                id_ = labelIds[label]
                pilImage = Image.open(path).convert("L")
                imageArray = np.array(pilImage, "uint8")
                faces = face_cascade.detectMultiScale(imageArray, scaleFactor=1.1, minNeighbors=5)

                for (x, y, w, h) in faces:
                    roi = imageArray[y:y+h, x:x+w]
                    xTrain.append(roi)
                    yLabels.append(id_)

    with open("labels", "wb") as f:
        pickle.dump(labelIds, f)
        f.close()

    recognizer.train(xTrain, np.array(yLabels))
    recognizer.save("trainer.yml")
    print(labelIds)
     
@app.route('/download')
def downloadFile ():
    path = "/home/pi/webapp/images/Seth Nurmi/Seth Nurmi1.jpg"
    return send_file(path, as_attachment=True)
    
@app.route('/delete')
def face_delete():
    # Directory name 
    directory = "Seth Nurmi.zip"
        
    # Parent Directory 
    parent = "/home/pi/webapp/images"
        
    # Path 
    path = os.path.join(parent, directory) 
        
    # removing directory
    shutil.rmtree(path)
    return redirect(url_for('addDeleteFaces'))

@app.route('/savedFaces', methods = ['GET', 'POST'])
def savedFaces():
	return render_template('savedFaces.html', len = len(image_names), image_names = image_names, as_attachment=True, Faces = Faces.query.all())
@app.route('/faceLogs', methods = ['GET', 'POST'])
def faceLogs():
	return render_template('faceLogs.html')

def logs():
    
@app.route('/settings', methods = ['GET', 'POST'])
def settings():
	return render_template('settingsSecurity.html')
	
if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    app.run(debug=False, host='0.0.0.0')
    
