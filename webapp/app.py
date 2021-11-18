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
import logging

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

class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))
    
db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login",methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]
        
        login = user.query.filter_by(username=uname, password=passw).first()
        session['logged_in'] = True

        if login is not None:
            return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']

        register = user(username = uname, email = mail, password = passw)
        db.session.add(register)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("Register.html")

path = "/home/pi/webapp/images"
image_names = os.listdir(path)
    


db.create_all()
@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()
@app.route('/home', methods = ['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('termProjectMain.html')

@app.route('/addDeleteFaces', methods = ['POST', 'GET'])
def addDeleteFaces():
    if not session.get('logged_in'):
        return render_template('login.html')
    image_names = os.listdir('/home/pi/webapp/images')
    return render_template('addDeleteFaces.html', Faces = Faces.query.all(), len = len(image_names),image_names = image_names)

    
@app.route('/new', methods = ['GET', 'POST'])
def new():
   if request.method == 'POST':
      if not request.form['name'] or not request.form['userType']:
         flash('Please enter all the fields', 'error')
      else:
         Face = Faces(request.form['name'], request.form['userType'])
         
         db.session.add(Face)
         #getImage()
         db.session.commit()
         
         
         flash('Record was successfully added')
         logging.basicConfig(filename="user.log", 
					format='%(message)s'
                )

         #Let us Create an object 
         logger=logging.getLogger() 

         #Now we are going to Set the threshold of logger to DEBUG 
         logger.setLevel(logging.DEBUG)
         
         name = request.form['name']
         dirName = "./images/" + name
         os.makedirs(dirName)
         userType = request.form['userType']
         logger.info("ID: " + name + " " + userType + " " + dirName)
         
         
         
         return redirect(url_for('addDeleteFaces'))
   return render_template('addFace.html')


   
@app.route('/listdir', methods = ['POST', 'GET'])
def postdir():
    return render_template('testCamera.html', len = len(image_names), image_names = image_names)

#name = request.form["name"]
@app.route("/image")
def getImage():
    PiCamera.resolution = (640, 480)
    PiCamera.framerate = 30
    rawCapture = PiRGBArray(PiCamera, size = (640, 480))
    face_cascade=cv.CascadeClassifier(cv.data.haarcascades +"haarcascade_frontalface_default.xml")

    name = input("What's his/her Name? ")
    dirName = "./images/" + name
    print(dirName)
    os.makedirs(dirName)
    print("Directory Created")

    count = 1
    for frame in PiCamera.capture_continuous(rawCapture, format="bgr"):
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

            return render_template('addDeleteFaces.html')
    
@app.route("/trainImages")
def train():
    face_cascade=cv.CascadeClassifier(cv.data.haarcascades +"haarcascade_frontalface_default.xml")
    recognizer = cv.face.LBPHFaceRecognizer_create()

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
    return redirect(url_for('settings'))

     
@app.route('/download')
def downloadLog ():
    mid = request.args.get('mid')
    face = Faces.query.filter_by(name=mid).first()

    path = "/home/pi/webapp/zip/" + mid + ".zip"
    return send_file(path, as_attachment=True)
    
@app.route('/download/logs')
def downloadLogs ():
    mid = request.args.get('mid')
    name = request.args.get('name')

    path = mid
    return send_file(path, as_attachment=True)
    
@app.route('/delete')
def face_delete():
    # Directory name 
    directory = ""
        
    # Parent Directory 
    parent = "/home/pi/webapp/images"
        
    # Path 
    path = os.path.join(parent, directory) 
        
    # removing directory
    shutil.rmtree(path)
    return redirect(url_for('addDeleteFaces'))
    
@app.route('/deleteRows')
def row_delete():
    mid = request.args.get('mid')
    face = Faces.query.filter_by(name=mid).delete()
    msg_text = 'Faces %s successfully removed' % str(face)
    #db.delete(face)
    db.session.commit()
    # Directory name 
    directory = mid
        
    # Parent Directory 
    parent = "/home/pi/webapp/images"
        
    # Path 
    path = os.path.join(parent, directory) 
    shutil.rmtree(path)
    flash(msg_text)
    return redirect(url_for('addDeleteFaces'))

@app.route('/savedFaces', methods = ['GET', 'POST'])
def savedFaces():
    if not session.get('logged_in'):
        return render_template('login.html')
    with open("user.log","r") as file:
        content = file.readlines()
        print(content)
        return render_template('savedFaces.html', as_attachment=True, Faces = Faces.query.all())
@app.route('/faceLogs', methods = ['GET', 'POST'])
def faceLogs():
  if not session.get('logged_in'):
        return render_template('login.html')
  with open("std.log","r") as file:
    content = file.readlines()
    print(content)


    return render_template('faceLogs.html', content = content)

@app.route('/settings', methods = ['GET', 'POST'])
def settings():
  return render_template('settingsSecurity.html')

@app.route('/settings/ChangePass', methods = ['GET', 'POST'])
def changePassword():

	return render_template('settingsChangePassword.html')
    
@app.route('/settings/EditUsers', methods = ['GET', 'POST'])
def editUsers():

	return render_template('settingsEditUsers.html')
    

if __name__ == '__main__':
    db.session.commit()
    app.run(debug=True, host='0.0.0.0')
    
