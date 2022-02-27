#!/usr/bin/env python

import RPi.GPIO as GPIO
import datetime
import smbus
import time
import sys
import LCD1602 as LCD
import dropbox
import os.path
import signal
from mfrc522 import SimpleMFRC522


#Token Access for Dropbox
accessToken = '' #add the token from dropbox
dbx=dropbox.Dropbox(accessToken)

#File Directory
localIDPath = '/home/pi/Documents/Hotel_Room_Management/identification.txt'
dbIDPath = '/TPJ655Project/identification.txt'
localLogPath = '/home/pi/Documents/Hotel_Room_Management/log.txt'
dbLogPath = '/TPJ655Project/log.txt'

#GPIO Variable Declaration
redGPIO = 17
greenGPIO = 27
blueGPIO = 22

buzzer = 5

greenButtonGPIO = 21
redButtonGPIO = 6

#PWM Frequency for RGB LED
Freq = 100

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#Setup GPIO Pins
GPIO.setup(greenButtonGPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(redButtonGPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(buzzer, GPIO.OUT)
GPIO.setup(redGPIO, GPIO.OUT)
GPIO.setup(greenGPIO, GPIO.OUT)
GPIO.setup(blueGPIO, GPIO.OUT)

RED = GPIO.PWM(redGPIO, Freq)
GREEN = GPIO.PWM(greenGPIO, Freq)
BLUE = GPIO.PWM(blueGPIO, Freq)

#Interrupt Functions
def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def greenCallBack(channel):
    print("Green Button Pressed!")
    LCD.init_lcd()
    LCD.print_lcd(2, 0, 'Program Mode')
    LCD.print_lcd(1, 1, 'Pls scan card')
    yellowOn()
    print('\n-----Program Mode-----')
    print('Pls scan card')
    time.sleep(1)
    global programFlag
    programFlag = True
    
def redCallBack(channel):
    print("Red Button Pressed!")
    LCD.init_lcd()
    LCD.print_lcd(2, 0, 'Delete Mode')
    LCD.print_lcd(1, 1, 'Pls scan card')
    yellowOn()
    print('\n-----Delete Mode-----')
    print('Pls scan card')
    time.sleep(1)
    global removeFlag
    removeFlag = True

#Interrupt Detect
GPIO.add_event_detect(greenButtonGPIO, GPIO.FALLING,callback=greenCallBack, bouncetime=2000)
GPIO.add_event_detect(redButtonGPIO, GPIO.FALLING,callback=redCallBack, bouncetime=2000)
signal.signal(signal.SIGINT, signal_handler)

#Get Current Time
def getTime():
    return datetime.datetime.now()

#RGB LED Setup Functions
def yellowOn():
    GREEN.start(100)
    RED.start(100)

def yellowOff():
    GREEN.start(0)
    RED.start(0)
    
def greenOn():
    GREEN.start(100)
    
def greenOff():
    GREEN.start(0)

def redOn():
    RED.start(100)
    
def redOff():
    RED.start(0)

def buzzerOn():
    GPIO.output(buzzer, True)

def buzzerOff():
    GPIO.output(buzzer, False)

#File Control Functions
#Store log to log.txt File
def logStore(info):
    try:
        f = open("log.txt", "a")
        f.write('\n')
        f.write(info)
    finally:
        f.close()

#Check ID File in Dropbox
def ckIDFileDB():
    try:
        dbx.files_download_to_file(localIDPath, dbIDPath)
        print('ID File Downloaded from Dropbox!')
        return True;
    except:
        print('No ID File in Dropbox!')
        return False;

#Check ID File in Local
def ckIDFileLocal():
    if os.path.isfile('identification.txt'):
        return True
    else:
        return False

#Check Log File in Dropbox
def ckLogFileDB():
    try:
        dbx.files_download_to_file(localLogPath, dbLogPath)
        print('Log File Downloaded from Dropbox!')
        return True;
    except:
        print('No Log File in Dropbox!')
        return False;

#Check Log File in Local
def ckLogFileLocal():
    if os.path.isfile('log.txt'):
        return True
    else:
        return False

#Upload ID File to Dropbox
def uploadDB():
    with open('identification.txt','rb') as f:
        dbx.users_get_current_account()
        #dbx.files_delete(dbIDPath)
        dbx.files_upload(f.read(), dbIDPath)
    f.close()
    print('ID File is Uploaded to Dropbox!')

#Upload Log File to Dropbox
def uploadLog():
    with open('log.txt','rb') as f:
        dbx.users_get_current_account()
        #dbx.files_delete(dbLogPath)
        dbx.files_upload(f.read(), dbLogPath)
    f.close()
    print('Log File is Uploaded to Dropbox!')   

#Create ID File and Initial&Store First ID Number to ID File in Local
def crtIDFileLocal():
    try:
        f = open("identification.txt", "a")
        print('New ID File is Created in local!')
    finally:
        f.close()

#Create Log File in Local
def crtLogFileLocal():
    try:
        f = open("log.txt", "a")
        print('New log file is created in local!')
    finally:
        f.close()

#Use RFID Reader to Read Card
def scanID():
    LCD.print_lcd(1, 1, 'Pls scan card')
    print('Pls scan card')
    reader = SimpleMFRC522()
    id, text = reader.read()
    time.sleep(2)
    return id

#Check Scaned Card ID with ID Stored in ID File
def ckID(scanedID):
    try:
        f = open("identification.txt", "r+")
        validIDs = f.read().splitlines()
        if str(scanedID) in validIDs:
            print(str(scanedID) + ' Exists')
            logStore('Access Succeed ' + str(scanedID) + ' ' + str(getTime().strftime("%m-%d %H:%M:%S")))
            dbx.files_delete(dbLogPath)
            uploadLog()
            return True
        else:
            print(str(scanedID) + ' Not Exists')
            logStore('Invalid Card ' + str(scanedID) + ' ' + str(getTime().strftime("%m-%d %H:%M:%S")))
            dbx.files_delete(dbLogPath)
            uploadLog()
            return False
    finally:
        f.close()

#Delete Scaned Card ID from ID File
def deleteID(scanedID):
    try:
        f = open("identification.txt", "r+")
        validIDs = f.read().splitlines()
        cardID = str(scanedID)
        yellowOff()
        if cardID in validIDs:
            greenOn()
            validIDs.remove(str(scanedID))
            os.remove('identification.txt')
            try:
                f = open("identification.txt","a")
                for validID in validIDs:
                    f.write(validID)
                    f.write('\n')
                LCD.init_lcd()
                LCD.print_lcd(1, 0, "Card Deleted!")
                LCD.print_lcd(2, 1, cardID)
                time.sleep(3)
        
                print(cardID + ' Deleted')
                logStore('Deleted ' + str(scanedID) + ' ' + str(getTime().strftime("%m-%d %H:%M:%S")))
                dbx.files_delete(dbLogPath)
                uploadLog()
            finally:
                dbx.files_delete(dbIDPath)
                f.close()
                uploadDB()
                greenOff() 
        else:
            LCD.init_lcd()
            LCD.print_lcd(1, 0, "Card Not Exist")
            LCD.print_lcd(1, 1, "Cannot Delete")
            redOn()
            buzzerOn()
            print('Cannot Delete ID That Is Not Exists')
            time.sleep(3)
            redOff()
            buzzerOff()
    finally:
        f.close()
        

#Store Scaned Card ID to ID File
def addID(scanedID):
    if not ckID(scanedID):
        try:
            f = open("identification.txt", "a")
            cardID = str(scanedID)
            f.write(cardID)
            f.write('\n')
            
            LCD.init_lcd()
            LCD.print_lcd(1, 0, "Card Assigned!")
            LCD.print_lcd(2, 1, cardID)
            time.sleep(3)
            
            print(cardID + ' assigned')
            logStore('Assigned ' + str(scanedID) + ' ' + str(getTime().strftime("%m-%d %H:%M:%S")))
            dbx.files_delete(dbLogPath)
            uploadLog()
        finally:
            dbx.files_delete(dbIDPath)
            f.close()
            uploadDB()
            yellowOff()
    else:
        yellowOff()
        LCD.init_lcd()
        LCD.print_lcd(0, 0, "Already Assigned")
        LCD.print_lcd(0, 1, 'Cannot Do Again')
        redOn()
        buzzerOn()
        time.sleep(1)
        
        print('Existed Card Cannot be Assign Again!')
        logStore('Assign Failed ' +  str(scanedID) + ' ' +  str(getTime().strftime("%m-%d %H:%M:%S")))
        dbx.files_delete(dbLogPath)
        uploadLog()
        redOff()
        buzzerOff()
        

if __name__ == "__main__":
    print('\n-----Initialization-----')

#Set Value for Flags of Buttons' Interrupts
    programFlag = False
    removeFlag = False
    
#LCD1602 Screen Initialization
    LCD.init_lcd()  
    LCD.turn_light(1)
    LCD.print_lcd(4, 0, "Welcome")
    LCD.print_lcd(1, 1, getTime().strftime("%m-%d %H:%M:%S"))
    print(getTime().strftime("%Y-%m-%d %H:%M:%S"))
    time.sleep(3)

#RGB LED Initialization
    LCD.init_lcd()
    LCD.print_lcd(3, 0, 'RGB LED')
    LCD.print_lcd(2, 1, 'Initializing')
    print('RGB LED Initializing')
    redOn()
    time.sleep(0.5)
    redOff()
    time.sleep(0.5)
    greenOn()
    time.sleep(0.5)
    greenOff()
    time.sleep(0.5)
    yellowOn()
    time.sleep(0.5)
    yellowOff()
    
#Buzzer Initialization
    buzzerOff()

#Log File and ID File Initialization
    if not ckLogFileDB():
        if ckLogFileLocal():
            uploadLog()
        else:
            crtLogFileLocal()
            uploadLog()
            
    if not ckIDFileDB():
        if ckIDFileLocal():
            uploadDB()
        else:
            crtIDFileLocal()
            uploadDB()

#Get into Normal Mode
    while True:
        LCD.init_lcd()
        LCD.print_lcd(2, 0, 'Normal Mode')
        print('\n-----Normal Mode-----')
        scanedID = scanID()
        ckIDFileDB()
        if programFlag == True:
            addID(scanedID)
            programFlag = False
        elif removeFlag == True:
            deleteID(scanedID)
            removeFlag = False
        else:
            if ckID(scanedID):
                LCD.init_lcd()
                LCD.print_lcd(1, 0, "Access Succeed!")
                LCD.print_lcd(4, 1, getTime().strftime("%H:%M:%S"))
                print('Access Succeed!')
                greenOn()
                time.sleep(3)
                greenOff()
            else:
                LCD.init_lcd()
                LCD.print_lcd(1, 0, "Invalid Card!")
                LCD.print_lcd(4, 1, getTime().strftime("%H:%M:%S"))
                print('Invalid Card!')
                redOn()
                buzzerOn()
                time.sleep(3)
                redOff()
                buzzerOff()
        