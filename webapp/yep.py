import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np 
import pickle
import RPi.GPIO as GPIO
from time import sleep
import datetime
import logging 

logging.basicConfig(filename="std.log", 
					format='%(asctime)s %(message)s'
                    )

#Let us Create an object 
logger=logging.getLogger() 

#Now we are going to Set the threshold of logger to DEBUG 
logger.setLevel(logging.DEBUG) 

relay_pin = [26]
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, 0)

with open('labels', 'rb') as f:
	dict = pickle.load(f)
	f.close()

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30
rawCapture = PiRGBArray(camera, size=(640, 480))

face_cascade=cv2.CascadeClassifier(cv2.data.haarcascades +"haarcascade_frontalface_default.xml")
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

font = cv2.FONT_HERSHEY_SIMPLEX
now = datetime.datetime.now()
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	frame = frame.array
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	faces = face_cascade.detectMultiScale(gray, scaleFactor = 1.5, minNeighbors = 5)
	for (x, y, w, h) in faces:
		roiGray = gray[y:y+h, x:x+w]

		id_, conf = recognizer.predict(roiGray)

		for name, value in dict.items():
			if value == id_:
				
				logger.info("Success: " + name + " " + '/home/pi/webapp/zip/' + name + ".zip")
				print("Success: " + name)
			  


		if conf <= 70:
			GPIO.output(relay_pin, 1)
			cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
			cv2.putText(frame, name + str(conf), (x, y), font, 2, (0, 0 ,255), 2,cv2.LINE_AA)
			print ("Failure")
			time = str(datetime.datetime.now().time())
			camera.capture('/home/pi/webapp/failures/'+ str(time) + ".png")		
			logger.info("Failure: " + "Fail" + " " + '/home/pi/webapp/failures/'+ str(time) + ".png")

		else:
			GPIO.output(relay_pin, 0)

	cv2.imshow('frame', frame)
	key = cv2.waitKey(1)

	rawCapture.truncate(0)

	if key == 27:
		break

cv2.destroyAllWindows()