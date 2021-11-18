from flask import Flask, render_template, redirect, url_for, request, session, flash, redirect, logging, request, send_file
from flask_sqlalchemy import SQLAlchemy
from PIL import Image 
import pickle
from picamera.array import PiRGBArray
from picamera import PiCamera
from readLines import *
from camera import *
import numpy as np
import cv2 as cv
import os
import sys
import shutil
import logging 
app = Flask(__name__)
def LastNlines():
    fname = 'std.log'
    N = 10
    # opening file using with() method
    # so that file get closed
    # after completing work
    with open("std.log") as file:
         
        # loop to read iterate
        # last n lines and print it
        for line in (file.readlines() [-10:]):
            print(line, end ='')
    
        
            

 
