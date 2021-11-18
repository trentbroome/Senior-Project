from flask import Flask, render_template, redirect, url_for, request, session, flash, redirect, logging, request, send_file
from flask_sqlalchemy import SQLAlchemy
from PIL import Image 
import pickle
from picamera.array import PiRGBArray
from picamera import PiCamera

from camera import *
import numpy as np
import cv2 as cv
import os
import sys
import shutil
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
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
    
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


        register = user(request.form['uname'], request.form['mail'], request.form['passw'])
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
         
         db.session.commit()
         getImage()
         
         
         flash('Record was successfully added')

         
         
         
         return redirect(url_for('addDeleteFaces'))
   return render_template('addFace.html')

#name = request.form["name"]
@app.route("/image")
def getImage():
    image()
    return redirect(url_for('addDeleteFaces'))
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
    path2 = "/home/pi/webapp/zip/" + directory + ".zip"
    print (path2)
    shutil.rmtree(path)
    os.remove(path2)
    flash(msg_text)
    return redirect(url_for('addDeleteFaces'))
@app.route('/deleteZip')
def deleteZip():
    mid = request.args.get('zip')
    directory = mid
        
    # Parent Directory 
    path = "/home/pi/webapp/zip/" + mid + ".zip"
    # Path 
    os.remove(path)
    flash(msg_text)
    return redirect(url_for('addDeleteFaces'))

@app.route('/loginDelete')
def loginDelete():
    mid = request.args.get('mid')
    userLogin = user.query.filter_by(username=mid).delete()
    msg_text = 'Faces %s successfully removed' % str(userLogin)
    #db.delete(face)
    db.session.commit()
    return redirect(url_for('changePassword'))
    
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
    content = file.readlines()[-10:]
    print(content)

    return render_template('faceLogs.html', content = content)

@app.route('/update_row/', methods=['GET', 'POST'])
def update_row():
    if request.method == 'POST':
        # query.get() method gets a Row by the primary_key
        record = user.query.get(request.form.get('id', type=int))
        
        # change the values you want to update
        record.username = request.form.get('name')
        record.email = request.form.get('mail')
        record.password = request.form.get('password')
        # commit changes
        db.session.commit()
    # redirect back to your main view
    return redirect(url_for('changePassword'))
    
@app.route('/updateFaces/', methods = ['GET', 'POST'])
def updateFaces():
    if request.method == 'POST':
        
        record = Faces.query.get(request.form.get('id', type=int))
        
        record.name = request.form.get('faceName')
        record.userType = request.form.get('userType')
        
        db.session.commit()
        
    return redirect(url_for('changePassword'))
@app.route('/settings', methods = ['GET', 'POST'])
def settings():
  return render_template('settingsSecurity.html')

@app.route('/settings/ChangePass', methods = ['GET', 'POST'])
def changePassword():

	return render_template('settingsChangePassword.html', user = user.query.all(), Faces = Faces.query.all())
    
@app.route('/settings/EditUsers', methods = ['GET', 'POST'])
def editUsers():

	return render_template('settingsEditUsers.html')
    

if __name__ == '__main__':
    db.session.commit()
    app.run(debug=False, host='0.0.0.0')
    
