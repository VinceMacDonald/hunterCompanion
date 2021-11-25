# Import the required libraries
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance, ImageOps, ImageFilter
import mysql.connector as mysql
import pyautogui
from datetime import datetime
from screen_search import *
from win10toast import ToastNotifier
import time
import cv2
import pytesseract
import os
import re
import json
import threading
from oauth2client.service_account import ServiceAccountCredentials
import simpleaudio as sa
import requests
import pytz
import numpy as np
from random import randint
# Gspread Docs: https://docs.gspread.org/en/latest/user-guide.html
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Create an instance of tkinter frame or window
win=Tk()
win.title("Hunter Companion")
win.iconbitmap("favicon.ico")
# Set the size of the window
#win.geometry("300x500")

### SETUP
# Loading config file
with open('config.json', 'r') as f:
    config = json.loads(f.read())

# Global Vars
utc = pytz.UTC
currentCompId = None
currentCompName = None
currentCompStart = None
currentCompEnd = None
currentCompAnimals = []
currentCompAllowedWeapons = []
compLabels = {"animal":[],"hunter":[],"score":[],"killdate":[],"prize":[]}
current_timezone = pytz.timezone(config["timezone"])

search = Search("trigger.png")

reserveCuatroColinas = Search("reserves/cuatro.png")
reserveHirschfelden = Search("reserves/hirschfelden.png")
reserveLaytonLake = Search("reserves/layton.png")
reserveMedvedTaiga = Search("reserves/medved.png")
reserveParqueFernando = Search("reserves/fernando.png")
reserveSilverRidgePeaks = Search("reserves/silverridge.png")
reserveTeAwaroa = Search("reserves/teawaroa.png")
reserveVurhongaSavanna = Search("reserves/vurhonga.png")
reserveYukonValley = Search("reserves/yukon.png")
reserveRanchoArroyo = Search("reserves/arroyo.png")

toaster = ToastNotifier()
# for image capturing
thresh = 245
fn = lambda x : 255 if x > thresh else 0

#################################
def get_green_letters(img):
    # Scale image up
    width, height = img.size
    img = img.resize((round(width*2), round(height*2))) # WIDTH +100%

    pixels = img.load() # create the pixel map
    for i in range(img.size[0]): # for every pixel:
        for j in range(img.size[1]):
            px = pixels[i,j]
            if px[1] < 200:
                pixels[i,j] = (255,255,255) # change to white
            else:
                pixels[i,j] = (167,255,103) # change to green
    
    # It converts the BGR color space of image to HSV color space
    data = np.array(img)
    #data = cv2.resize(data, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    hsv = cv2.cvtColor(data, cv2.COLOR_BGR2HSV)

    lower_color = np.array([21,79,203])
    upper_color = np.array([95, 255, 255])
    mask = cv2.inRange(hsv, lower_color, upper_color)
     
    # The black region in the mask has the value of 0,
    # so when multiplied with original image removes all non-blue regions
    result = cv2.bitwise_and(data, data, mask = mask)
    
    # Get Image from Result
    im2 = Image.fromarray(result)

    # Convert to B&W
    enhancer = ImageEnhance.Color(im2)
    im2 = enhancer.enhance(0.1)
    im2 = ImageEnhance.Contrast(im2)
    im2 = im2.enhance(4.0)
    im2 = im2.convert('L').point(fn, mode='1')
    im2 = im2.convert('L')
    im2 = ImageOps.invert(im2)
    im2 = im2.convert('1')
    im2 = im2.convert("RGB")
    im2 = im2.filter(ImageFilter.BoxBlur(1))
    return im2

def get_white_letters(img):
    width, height = img.size
    img = img.resize((round(width*1.4), round(height*1.4))) # WIDTH +40%
    pixels = img.load() # create the pixel map
    for i in range(img.size[0]): # for every pixel:
        for j in range(img.size[1]):
            if pixels[i,j] <= (230,230,230): # if not white
                pixels[i,j] = (0, 0, 0) # change to black
    im2 = ImageOps.invert(img)
    im2 = im2.convert('1')
    im2 = im2.convert("RGB")
    return im2

def getAnimalName(text):
    animal = ""
    if text.find("CARIB") > -1 or text.find("BOU") > -1:
        animal = "Caribou"
    if text.find("MOOS") > -1:
        animal = "Moose"
    if text.find("BECEITE") > -1:
        animal = "Beceite Ibex"
    if text.find("GREDOS") > -1:
        animal = "Gredos Ibex"
    if text.find("RONDA") > -1:
        animal = "Ronda Ibex"
    if text.find("SPANISH") > -1:
        animal = "Spanish Ibex"
    if text.find("BOAR") > -1:
        animal = "Wild Boar"
    if text.find("BEAR") > -1 and text.find("G") > -1:
        animal = "Grizzly Bear"
    if text.find("AXIS") > -1:
        animal = "Axis Deer"
    if text.find("BIGHORN") > -1:
        animal = "Bighorn Sheep"
    if text.find("BEAR") > -1 and text.find("ACK") > -1:
        animal = "Black Bear"
    if text.find("BLACKBUCK") > -1:
        animal = "Blackbuck"
    if text.find("BLACKTAIL") > -1:
        animal = "Blacktail Deer"
    if text.find("WILDEBEEST") > -1:
        animal = "Blue Wildebeest"
    if text.find("GOOSE") > -1 or text.find("CANADA") > -1:
        animal = "Canada Goose"
    if text.find("CAPE BUFFALO") > -1:
        animal = "Cape Buffalo"
    if text.find("CHAMOIS") > -1:
        animal = "Chamois"
    if text.find("CINNAMON") > -1:
        animal = "Cinnamon Teal"
    if text.find("COYOTE") > -1:
        animal = "Coyote"
    if text.find("BEAR") > -1 and text.find("N") > -1:
        animal = "Eurasian Brown Bear"
    if text.find("LYNX") > -1:
        animal = "Eurasian Lynx"
    if (text.find("BISON") > -1 or text.find("BISUN") > -1) and text.find("EURO") > -1:
        animal = "European Bison"
    if text.find("EUROPEAN HARE") > -1:
        animal = "European Hare"
    if text.find("EUROPEAN RABBIT") > -1:
        animal = "European Rabbit"
    if text.find("FALLOW") > -1:
        animal = "Fallow Deer"
    if text.find("ERAL") > -1 and text.find("G") > -1:
        animal = "Feral Goat"
    if text.find("ERAL") > -1 and text.find("P") > -1:
        animal = "Feral Pig"
    if text.find("GEMSBOK") > -1:
        animal = "Gemsbok"
    if text.find("GRAY WOLF") > -1:
        animal = "Gray Wolf"
    if text.find("DUCK") > -1 and text.find("QU") > -1:
        animal = "Harlequin Duck"
    if text.find("MOUFLON") > -1:
        animal = "Iberian Mouflon"
    if text.find("IBERIAN WOLF") > -1:
        animal = "Iberian Wolf"
    if text.find("JACKRABBIT") > -1:
        animal = "Jackrabbit"
        if text.find("LOPE") > -1:
            animal = "Antelope Jackrabbit"
    if text.find("KUDU") > -1:
        animal = "Lesser Kudu"
    if text.find("LION") > -1:
        animal = "Lion"
    if text.find("MALLARD") > -1:
        animal = "Mallard"
    if text.find("MOUNTAIN GOAT") > -1:
        animal = "Mountain Goat"
    if text.find("MOUNTAIN LION") > -1:
        animal = "Mountain Lion"
    if text.find("MULE DEER") > -1:
        animal = "Mule Deer"
    if (text.find("BISON") > -1 or text.find("BISUN") > -1) and text.find("AIN") > -1:
        animal = "Plains Bison"
    if text.find("PRONGHORN") > -1:
        animal = "Pronghorn"
    if text.find("PUMA") > -1:
        animal = "Puma"
    if text.find("RED DEER") > -1:
        animal = "Red Deer"
    if text.find("RED FOX") > -1:
        animal = "Red Fox"
    if text.find("EINDEE") > -1:
        animal = "Reindeer"
    if text.find("ROCKY") > -1:
        animal = "Rocky Mountain Elk"
    if text.find("ROE DEER") > -1:
        animal = "Roe Deer"
    if text.find("VELT") > -1:
        animal = "Roosevelt Elk"
    if text.find("SCRUB HARE") > -1:
        animal = "Scrub Hare"
    if text.find("MUSK DEER") > -1:
        animal = "Siberian Musk Deer"
    if text.find("JACKAL") > -1:
        animal = "Side-Striped Jackal"
    if text.find("SIKA") > -1 or text.find("SIRA") > -1 or text.find("KADEER") > -1:
        animal = "Sika Deer"
    if text.find("SPRINGBOK") > -1:
        animal = "Springbok"
    if text.find("URKEY") > -1:
        animal = "Turkey"
        if text.find("ANDE") > -1:
            animal = "Rio Grande Turkey"
    if text.find("WARTHOG") > -1:
        animal = "Warthog"
    if text.find("WATER") > -1 and text.find("BUF") > -1:
        animal = "Water Buffalo"
    if text.find("WHITE") > -1 and text.find("DEER") > -1:
        animal = "Whitetail Deer"
    if text.find("MEX") > -1:
        animal = "Mexican Bobcat"
    if text.find("RED") > -1 and text.find("PEC") > -1:
        animal = "Collared Peccary"
    if text.find("HEAS") > -1:
        animal = "Ring-Necked Pheasant"
    return animal
#################################
def getAnimal(img, th):
    global thresh
    thresh = th
    text = pytesseract.image_to_string(img)
    text = text.upper()
    animal = getAnimalName(text)
    if animal == "" and th < 254:
        return getAnimal(img, 254)
    return animal
#################################
def getMedal(img, th):
    global thresh
    thresh = th
    text = pytesseract.image_to_string(img)
    text = text.upper()
    medal = getMedalName(text)
    if medal == "" and th < 254:
        return getMedal(img, 254)
    return medal
#################################
def getMedalName(text):
    medalScore = ""
    if text.find("NO") > -1:
        medalScore = "None"
    if text.find("BRO") > -1:
        medalScore = "Bronze"
    if text.find("ER") > -1:
        medalScore = "Silver"
    if text.find("OLD") > -1:
        medalScore = "Gold"
    if text.find("DIA") > -1:
        medalScore = "Diamond"
    return medalScore
#################################
def getTrophyScore(img, th):
    global thresh
    thresh = th
    text = pytesseract.image_to_string(img)
    text = re.sub("[^0-9.]", "", text)
    try:
        trophyRating = float(text.strip())
    except:
        trophyRating = 0

    return trophyRating

def getWeapon(img, th):
    global thresh
    thresh = th
    text = pytesseract.image_to_string(img)
    text = text.upper()
    weapon = getWeaponName(text)
    if weapon == "" and th < 254:
        return getWeapon(img, 254)
    return weapon

def getDistance(img, th):
    global thresh
    thresh = th
    text = pytesseract.image_to_string(img)
    text = re.sub("[^0-9.]", "", text)
    try:
        sd = float(text.strip())
    except:
        sd = 0
    return sd

def getWeaponName(text):
    weap = ""
    if text.find("DOC") > -1:
        weap = ".223 Docent"
    if text.find("GER") > -1:
        weap = "Ranger .243"
    if text.find("UNT") > -1:
        weap = ".270 Huntsman"
    if text.find("GENT") > -1:
        weap = "7mm Regent Magnum"
    if text.find("MAS") > -1:
        weap = "Rangemaster 338"
    if text.find("MOD") > -1:
        weap = "Miller Model 1891"
    if text.find("WH") > -1:
        weap = "Whitlock Model 86"
    if text.find("ACH") > -1:
        weap = "Coachmate Lever .45-70"
    if text.find("LR") > -1:
        if text.find("AND") > -1:
            weap = "Andersson .22LR"    
        else:
            weap = "Virant .22LR"
    if text.find("KING") > -1:
        weap = "King 470DB"
    if text.find("KH") > -1:
        weap = "Solokhin MN1890"
    if text.find("CAN") > -1:
        weap = ".300 Canning Magnum"
    if text.find("CY") > -1:
        weap = "Vasquez Cyclone .45"
    if text.find("ECK") > -1:
        if text.find("G") > -1:
            weap = "Strecker SxS 20G"
        else:
            weap = "Eckers .30-06"  
    if text.find("MART") > -1:
        weap = "Martensson 6.5mm"
    if text.find("CAP") > -1:
        weap = "Hudzik .50 Caplock"
    if text.find("WAN") > -1:
        weap = "M1 Iwaniec"
    if text.find("SHA") > -1:
        weap = "Caversham Steward 12G"
    if text.find("TORE") > -1:
        weap = "Cacciatore 12G"
    if text.find("NOR") > -1:
        weap = "Nordin 20SA"
    if text.find("GRE") > -1:
        weap = "Grelck Drilling Rifle"
    if text.find("LONG") > -1:
        weap = "Alexander Longbow"
    if text.find("BEAR") > -1:
        weap = "Bearclaw Lite CB-60"
    if text.find("SPO") > -1:
        if text.find("CB") > -1:
            weap = "Crosspoint CB-165"
        else:
            weap = "F.L. Sporter .303"      
    if text.find("HAW") > -1:
        weap = "Hawk Edge CB-70"
    if text.find("RECU") > -1:
        weap = "Houyi Recurve Bow"
    if text.find("KO") > -1:
        weap = "Koter CB-65 Bow"
    if text.find("RAZ") > -1:
        weap = "Razorback Lite CB-60"
    if text.find("PAN") > -1:
        weap = ".44 Panther Magnum"
    if text.find("FO") > -1:
        weap = "Focoso 357"
    if text.find("MANG") > -1:
        weap = "Mangiafico 410/45 Colt"
    if text.find("RH") > -1:
        weap = "Rhino 454"
    if text.find("STRAD") > -1:
        weap = ".270 Stradivarius"
    return weap

def dropdown_reserve_updated(*args):
    global selectedAnimal
    #print(f"Selected Reserve:  '{selectedReserve.get()}'")
    dropAnimals = OptionMenu(frame, selectedAnimal, *animalsByReserve[selectedReserve.get()])
    selectedAnimal.set(animalsByReserve[selectedReserve.get()][0])
    dropAnimals.grid(row=1, column=1)
    dropAnimals["menu"].config(bg="white")


def dropdown_animal_updated(*args):
    global selectedAnimal, lblAnimalStatClassVal, lblAnimalStatMaxWeightVal, lblAnimalStatWeightTrackVal
    myAnimal = selectedAnimal.get()
    db = mysql.connect(
        host="52.53.69.28",
        user="huntercotw",
        password="6VoI4wkBOOFa98dE",
        database="hunter"
    )
    cur = db.cursor(dictionary=True)
    cur.execute('SELECT * FROM `animals` WHERE animalName = "'+myAnimal+'"')
    rows = cur.fetchall()
    if len(rows) > 0:
        try:
            lblAnimalStatClassVal["text"] = str(rows[0]["animalClass"])
            lblAnimalStatMaxWeightVal["text"] = str(rows[0]["maxWeight"]) + " KG"
            lblAnimalStatWeightTrackVal["text"] = str(rows[0]["maxTrackWeight"]) + " KG"
        except NameError:
            print("")
    cur.close()
    db.close()

def check_for_comp():
    global utc, currentCompId, currentCompName, compLabels, currentCompStart, currentCompEnd, currentCompAnimals, currentCompAllowedWeapons
    curdatetime = datetime.now(tz=pytz.utc) # Server saves dates in UTC
    db = mysql.connect(
        host="52.53.69.28",
        user="huntercotw",
        password="6VoI4wkBOOFa98dE",
        database="hunter"
    )
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM `competitions` WHERE 1 ORDER BY endTime DESC LIMIT 1")
    rows = cur.fetchall()
    if len(rows) > 0:
        if curdatetime < utc.localize(rows[0]["endTime"]) and curdatetime >= utc.localize(rows[0]["startTime"]):
            # Comp has started
            compStartDate = pytz.utc.localize(rows[0]["startTime"])
            compEndDate = pytz.utc.localize(rows[0]["endTime"])
            compStartDateLocal = compStartDate.astimezone(current_timezone)
            compStartDateLocal = compStartDateLocal.strftime("%a, %b.%d %I:%M%p")
            compEndDateLocal = compEndDate.astimezone(current_timezone)
            compEndDateLocal = compEndDateLocal.strftime("%a, %b.%d %I:%M%p")
            lblCompTitle["text"] = rows[0]["compName"] + "\n" + str(compStartDateLocal) + " - " + str(compEndDateLocal)
            currentCompId = rows[0]["id"]
            currentCompName = rows[0]["compName"]
            currentCompStart = rows[0]["startTime"]
            currentCompEnd = rows[0]["endTime"]
            # Figure out animals and prizes and add labels
            js = json.loads(rows[0]["prizes"])
            currentCompAllowedWeapons = js[0]['allowedWeapons']
            i = 0
            for j in js:
                curRow = 21 + i
                currentCompAnimals.append(j["animal"])
                compLabels["animal"].append(i)
                compLabels["animal"][i] = {}
                compLabels["animal"][i]["element"] = Label(frame, text=j["animal"])
                compLabels["animal"][i]["element"].grid(row=curRow, column=0)

                compLabels["hunter"].append(i)
                compLabels["hunter"][i] = {}
                compLabels["hunter"][i]["element"] = Label(frame, text="-")
                compLabels["hunter"][i]["element"].grid(row=curRow, column=1)

                compLabels["score"].append(i)
                compLabels["score"][i] = {}
                compLabels["score"][i]["element"] = Label(frame, text="-")
                compLabels["score"][i]["element"].grid(row=curRow, column=2)

                compLabels["killdate"].append(i)
                compLabels["killdate"][i] = {}
                compLabels["killdate"][i]["element"] = Label(frame, text="-")
                compLabels["killdate"][i]["element"].grid(row=curRow, column=3)

                compLabels["prize"].append(i)
                compLabels["prize"][i] = {}
                compLabels["prize"][i]["element"] = Label(frame, text=j["prize"])
                compLabels["prize"][i]["element"].grid(row=curRow, column=4)
                i = i + 1
            # Thread for comp update
            t2 = threading.Thread(target=update_competition)
            t2.daemon = True
            t2.start()
        else:
            # Thread for check for comps in 10 mins
            time.sleep(600)
            t2 = threading.Thread(target=check_for_comp)
            t2.daemon = True
            t2.start()
    cur.close()
    db.close()

def update_competition():
    global utc, currentCompId, currentCompName, currentCompStart, currentCompEnd, compLabels, currentCompAnimals, current_timezone, currentCompAllowedWeapons
    db = mysql.connect(
        host="52.53.69.28",
        user="huntercotw",
        password="6VoI4wkBOOFa98dE",
        database="hunter"
    )
    cur = db.cursor(dictionary=True)

    i = 0
    for a in compLabels["animal"]:
        compAnimal = a["element"]["text"]
        cur.execute('SELECT * FROM `kills` WHERE competitionId="'+currentCompId+'" AND animal="'+compAnimal+'" ORDER BY trophyScore DESC')
        rows = cur.fetchall()
        if len(rows) > 0:
            # Update Labels
            compLabels["hunter"][i]["element"]["text"] = rows[0]["hunter"]
            compLabels["score"][i]["element"]["text"] = rows[0]["trophyScore"]

            dto = pytz.utc.localize(rows[0]["killdate"])
            localized_timestamp = dto.astimezone(current_timezone)
            localized_timestamp = localized_timestamp.strftime("%Y-%m-%d %H:%M:%S")

            compLabels["killdate"][i]["element"]["text"] = localized_timestamp
        i = i + 1

    # Check if Comp Ended and reset everything
    curdatetime = datetime.now(tz=pytz.utc) # Server saves dates in UTC
    if curdatetime > utc.localize(currentCompEnd):
        # Comp has ended
        lblCurrentCompHeader.configure(foreground="red")
        lblCompTitle.configure(foreground="red")
        lblCompAnimal.configure(foreground="red")
        lblCompHunter.configure(foreground="red")
        lblCompScore.configure(foreground="red")
        lblCompWhen.configure(foreground="red")
        lblCompPrize.configure(foreground="red")
        i = 0
        for a in compLabels["animal"]:
            compLabels["animal"][i]["element"].configure(foreground="red")
            compLabels["hunter"][i]["element"].configure(foreground="red")
            compLabels["score"][i]["element"].configure(foreground="red")
            compLabels["killdate"][i]["element"].configure(foreground="red")
            compLabels["prize"][i]["element"].configure(foreground="red")
            i = i + 1
        currentCompId = None
        currentCompName = None
        currentCompStart = None
        currentCompEnd = None
        currentCompAnimals = []
        currentCompAllowedWeapons = []

    else:
        # Comp is still active, update again in 30 secs
        time.sleep(30)
        t2 = threading.Thread(target=update_competition)
        t2.daemon = True
        t2.start()
    cur.close()
    db.close()

def update_latest_kills():
    global current_timezone
    db = mysql.connect(
        host="52.53.69.28",
        user="huntercotw",
        password="6VoI4wkBOOFa98dE",
        database="hunter"
    )
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM `kills` WHERE 1 ORDER BY killdate DESC LIMIT 5")
    rows = cur.fetchall()

    # Check if each exists: 'a' in vars() or 'a' in globals()

    if len(rows) > 0:
        lblRecentKillHunterVal0["text"] = rows[0]["hunter"]
        lblRecentKillAnimalVal0["text"] = rows[0]["animal"]
        lblRecentKillWeaponVal0["text"] = rows[0]["weapon"]
        lblRecentKillDistanceVal0["text"] = rows[0]["distance"]
        lblRecentKillScoreVal0["text"] = rows[0]["trophyScore"]
        dto = pytz.utc.localize(rows[0]["killdate"])
        localized_timestamp = dto.astimezone(current_timezone)
        localized_timestamp = localized_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        lblRecentKillWhenVal0["text"] = localized_timestamp

    if len(rows) > 1:
        lblRecentKillHunterVal1["text"] = rows[1]["hunter"]
        lblRecentKillAnimalVal1["text"] = rows[1]["animal"]
        lblRecentKillWeaponVal1["text"] = rows[1]["weapon"]
        lblRecentKillDistanceVal1["text"] = rows[1]["distance"]
        lblRecentKillScoreVal1["text"] = rows[1]["trophyScore"]
        dto = pytz.utc.localize(rows[1]["killdate"])
        localized_timestamp = dto.astimezone(current_timezone)
        localized_timestamp = localized_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        lblRecentKillWhenVal1["text"] = localized_timestamp

    if len(rows) > 2:
        lblRecentKillHunterVal2["text"] = rows[2]["hunter"]
        lblRecentKillAnimalVal2["text"] = rows[2]["animal"]
        lblRecentKillWeaponVal2["text"] = rows[2]["weapon"]
        lblRecentKillDistanceVal2["text"] = rows[2]["distance"]
        lblRecentKillScoreVal2["text"] = rows[2]["trophyScore"]
        dto = pytz.utc.localize(rows[2]["killdate"])
        localized_timestamp = dto.astimezone(current_timezone)
        localized_timestamp = localized_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        lblRecentKillWhenVal2["text"] = localized_timestamp

    if len(rows) > 3:
        lblRecentKillHunterVal3["text"] = rows[3]["hunter"]
        lblRecentKillAnimalVal3["text"] = rows[3]["animal"]
        lblRecentKillWeaponVal3["text"] = rows[3]["weapon"]
        lblRecentKillDistanceVal3["text"] = rows[3]["distance"]
        lblRecentKillScoreVal3["text"] = rows[3]["trophyScore"]
        dto = pytz.utc.localize(rows[3]["killdate"])
        localized_timestamp = dto.astimezone(current_timezone)
        localized_timestamp = localized_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        lblRecentKillWhenVal3["text"] = localized_timestamp

    if len(rows) > 4:
        lblRecentKillHunterVal4["text"] = rows[4]["hunter"]
        lblRecentKillAnimalVal4["text"] = rows[4]["animal"]
        lblRecentKillWeaponVal4["text"] = rows[4]["weapon"]
        lblRecentKillDistanceVal4["text"] = rows[4]["distance"]
        lblRecentKillScoreVal4["text"] = rows[4]["trophyScore"]
        dto = pytz.utc.localize(rows[4]["killdate"])
        localized_timestamp = dto.astimezone(current_timezone)
        localized_timestamp = localized_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        lblRecentKillWhenVal4["text"] = localized_timestamp

    cur.close()
    db.close()
    # Only check for an updated list every 30 secs
    time.sleep(30)
    t1 = threading.Thread(target=update_latest_kills)
    t1.daemon = True
    t1.start()

def new_top_trophy(comp, top):
    lblKingCompImage.grid_remove()
    lblKingTopImage.grid_remove()
    if top:
        lblKingTopImage.grid()
        if comp:
            lblKingCompImage.grid()
        try:
            wave_obj = sa.WaveObject.from_wave_file('monsterkill.wav')
            play_obj = wave_obj.play()
            #play_obj.wait_done()  # Wait until sound has finished playing
        except Exception as e:
            print("An exception occurred: ", e)
    elif comp:
        lblKingCompImage.grid()
        try:
            wave_obj = sa.WaveObject.from_wave_file('hail.wav')
            play_obj = wave_obj.play()
            #play_obj.wait_done()  # Wait until sound has finished playing
        except Exception as e:
            print("An exception occurred: ", e) 

def mainLoop():
    global search, reserveCuatroColinas, reserveHirschfelden, reserveLaytonLake, reserveMedvedTaiga, reserveParqueFernando, reserveSilverRidgePeaks, reserveTeAwaroa, reserveVurhongaSavanna, reserveYukonValley, reserveRanchoArroyo, toaster, thresh, fn, config, currentCompId, currentCompName, currentCompStart, currentCompEnd, currentCompAnimals, currentCompAllowedWeapons
    pos = search.imagesearch()

    r1 = reserveCuatroColinas.imagesearch()
    r2 = reserveHirschfelden.imagesearch()
    r3 = reserveLaytonLake.imagesearch()
    r4 = reserveMedvedTaiga.imagesearch()
    r5 = reserveParqueFernando.imagesearch()
    r6 = reserveSilverRidgePeaks.imagesearch()
    r7 = reserveTeAwaroa.imagesearch()
    r8 = reserveVurhongaSavanna.imagesearch()
    r9 = reserveYukonValley.imagesearch()
    r10 = reserveRanchoArroyo.imagesearch()

    if r1[0] != -1:
        selectedReserve.set("Cuatro Colinas")
        toaster.show_toast("Active Ranch", "Cuatro Colinas", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r2[0] != -1:
        selectedReserve.set("Hirschfelden")
        toaster.show_toast("Active Ranch", "Hirschfelden", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r3[0] != -1:
        selectedReserve.set("Layton Lake")
        toaster.show_toast("Active Ranch", "Layton Lake", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r4[0] != -1:
        selectedReserve.set("Medved Taiga")
        toaster.show_toast("Active Ranch", "Medved Taiga", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r5[0] != -1:
        selectedReserve.set("Parque Fernando")
        toaster.show_toast("Active Ranch", "Parque Fernando", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r6[0] != -1:
        selectedReserve.set("Silver Ridge Peaks")
        toaster.show_toast("Active Ranch", "Silver Ridge Peaks", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r7[0] != -1:
        selectedReserve.set("Te Awaroa")
        toaster.show_toast("Active Ranch", "Te Awaroa", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r8[0] != -1:
        selectedReserve.set("Vurhonga Savanna")
        toaster.show_toast("Active Ranch", "Vurhonga Savanna", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r9[0] != -1:
        selectedReserve.set("Yukon Valley")
        toaster.show_toast("Active Ranch", "Yukon Valley", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    if r10[0] != -1:
        selectedReserve.set("Rancho Del Arroyo")
        toaster.show_toast("Active Ranch", "Rancho Del Arroyo", icon_path="favicon.ico", duration=10)
        time.sleep(3)
    
    if pos[0] != -1:
        date = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
        myScreenshot = pyautogui.screenshot()
        screenshotFilename = config['playerName'] + "_"+str(date)+".jpg"
        myScreenshot.save(f"screenshots/"+ screenshotFilename)
        # Play sound so player knows image has been saved
        wave_obj = sa.WaveObject.from_wave_file('camera-shutter.wav')
        play_obj = wave_obj.play()
        
        # Upload screenshot for reference (in case it detects wrong)
        upfile = open(f"screenshots/"+ screenshotFilename, "rb")
        upResponse = requests.post("http://52.53.69.28/screenup.php", files = {"screenshot": upfile})

        im = Image.open(f"screenshots/" + screenshotFilename)
        im = im.convert("RGB")
        width, height = im.size
        X1 = (width - 1730) / 2
        X2 = X1  + 1730
        Y1 = (height - 970) / 2
        Y2 = Y1 + 970
        im = im.crop((X1, Y1, X2, Y2))

        # Calculating Medal Score
        medalScore = ""
        cropped_im = im.crop((0, 616, 171, 661))
        mci = get_white_letters(cropped_im)
        medalScore = getMedal(mci, 245)
        
        # Calculating Trophy Rating
        trophyRating = ""
        cropped_im = im.crop((419, 505, 497, 550))
        tci = get_green_letters(cropped_im)
        trophyRating = getTrophyScore(tci, 200)

        # Calculating Animal
        animal = ""
        cropped_im = im.crop((0, 45, 515, 120))
        aci = get_white_letters(cropped_im)
        animal = getAnimal(aci, 245)

        # Calculating Weapon
        weapon = ""
        cropped_im = im.crop((1425, 137, 1726, 173))
        wci = get_green_letters(cropped_im)
        weapon = getWeapon(wci, 245)

        # Calculating Shot Distance
        distance = 0
        cropped_im = im.crop((1653, 198, 1726, 235))
        dci = get_green_letters(cropped_im)
        distance = getDistance(dci, 245)
        
        lblKingCompImage.grid_remove()
        lblKingTopImage.grid_remove()

        lblLastKillAnimalVal['text'] = str(animal)
        lblLastKillMedalVal['text'] = medalScore
        lblLastKillTrophyVal['text'] = str(trophyRating)
        lblLastKillWeaponVal['text'] = str(weapon)
        lblLastKillDistanceVal['text'] = str(distance)

        if animal != "":
            selectedAnimal.set(str(animal))
        
        # Checking against Leaderboards
        dbk = mysql.connect(
            host="52.53.69.28",
            user="huntercotw",
            password="6VoI4wkBOOFa98dE",
            database="hunter"
        )
        curk = dbk.cursor(dictionary=True)
        toastTitle = str(animal) + " Harvested!"
        curTrophyVal = 0
        curTrophyName = "-"
        compTrophy = False
        topTrophy = False

        curk.execute('SELECT animal,hunter,trophyScore FROM `kills` WHERE competitionId="'+str(currentCompId)+'" AND animal="'+str(animal)+'" ORDER BY trophyScore DESC LIMIT 1')
        rowsTTC = curk.fetchall()
        if len(rowsTTC) > 0:
            curTrophyVal = rowsTTC[0]["trophyScore"]
            curTrophyName = rowsTTC[0]["hunter"]
            if trophyRating > float(rowsTTC[0]["trophyScore"]):
                # New Top Trophy in Comp
                compTrophy = True

        curk.execute('SELECT animal,hunter,trophyScore FROM `kills` WHERE animal="'+str(animal)+'" ORDER BY trophyScore DESC LIMIT 1')
        rowsTTA = curk.fetchall()
        if len(rowsTTA) > 0:
            if curTrophyVal == 0 and curTrophyName == "-":
                curTrophyVal = rowsTTA[0]["trophyScore"]
                curTrophyName = rowsTTA[0]["hunter"]
            if trophyRating > float(rowsTTA[0]["trophyScore"]):
                # New Top Trophy in All
                topTrophy = True

        if compTrophy or topTrophy:
            new_top_trophy(compTrophy, topTrophy)
            toastTitle = toastTitle + "\nNEW TOP TROPHY!"

        # Update database with kill
        # Only add the competition id if this is an animal in the comp
        if str(animal) in currentCompAnimals and (str(weapon) in currentCompAllowedWeapons or currentCompAllowedWeapons == []):
            ccid = currentCompId
        else:
            ccid=""
        curk.execute('INSERT INTO `kills`(`location`, `animal`, `hunter`, `trophyScore`, `medal`, `weapon`, `distance`, `screenshot`,`competitionId`) VALUES ("'+selectedReserve.get()+'","'+str(animal)+'","'+config['playerName']+'","'+str(trophyRating)+'","'+str(medalScore)+'","'+str(weapon)+'","'+str(distance)+'","'+screenshotFilename+'","'+ccid+'")')

        curk.close()
        dbk.close()

        # Popup in game notification (Toast)
        toastMsg = "Medal: " + medalScore + "\nTrophy Score: "+str(trophyRating)+"\nLeaderboard: " + str(curTrophyName) + " (" + str(curTrophyVal) + ")"
        toaster.show_toast(toastTitle, toastMsg, icon_path="favicon.ico", duration=10)

        # Wait so we don't go infinite looping
        time.sleep(10)

    t = threading.Thread(target=mainLoop)
    t.daemon = True
    t.start()

#################################

frame = LabelFrame(win, padx=10, pady=10)
frame.pack(padx=10, pady=10)

# Remote: 52.53.69.28 - huntercotw - 6VoI4wkBOOFa98dE
# Local: localhost - hunter - callwild
mydb = mysql.connect(
    host="52.53.69.28",
    user="huntercotw",
    password="6VoI4wkBOOFa98dE",
    database="hunter"
)
mycursor = mydb.cursor()
animalsByReserve = {}
animals = []
mycursor.execute("SELECT reserve, animalName FROM reserves, animals WHERE INSTR(animals.reserves, reserves.id) >= 1 ORDER BY reserves.id")
for x in mycursor:
   if x[0] not in animalsByReserve:
      animalsByReserve[x[0]] = []
   animalsByReserve[x[0]].append(x[1])
   animalsByReserve[x[0]].sort()

reserves = []
mycursor.execute("SELECT reserve from reserves ORDER BY reserve ASC")
for x in mycursor:
   reserves.append(x[0]);

mycursor.close()
mydb.close()

selectedReserve = StringVar()
selectedAnimal = StringVar()

selectedReserve.trace("w", dropdown_reserve_updated)
selectedReserve.set(reserves[0])
dropReserves = OptionMenu(frame, selectedReserve, *reserves)

selectedAnimal.trace("w", dropdown_animal_updated)
selectedAnimal.set(animalsByReserve[selectedReserve.get()][0])
dropAnimals = OptionMenu(frame, selectedAnimal, *animalsByReserve[selectedReserve.get()])

# Defining Visual Elements
lblReserve = Label(frame, text="Reserve", font='Helvetica 13')
lblAnimal = Label(frame, text="Animal", font='Helvetica 13')

lblAnimalStatClass = Label(frame, text="Class", font='Helvetica 13')
lblAnimalStatMaxWeight = Label(frame, text="Max Weight (KG)", font='Helvetica 13')
lblAnimalStatWeightTrack = Label(frame, text="Max Weight Track (KG)", font='Helvetica 13')

lblAnimalStatClassVal = Label(frame, text="0", font='Helvetica 13', fg='blue')
lblAnimalStatMaxWeightVal = Label(frame, text="0", font='Helvetica 13', fg='blue')
lblAnimalStatWeightTrackVal = Label(frame, text="0", font='Helvetica 13', fg='blue')

kingCompImage = ImageTk.PhotoImage(Image.open("crown1.png"))
lblKingCompImage = Label(frame, image=kingCompImage)

kingTopImage = ImageTk.PhotoImage(Image.open("crown2.png"))
lblKingTopImage = Label(frame, image=kingTopImage)

mySeparator1 = ttk.Separator(frame, orient='horizontal')
lblLastKillTitle = Label(frame, text="Last Kill", font='Helvetica 13 bold')
lblLastKillAnimal = Label(frame, text="Animal:", font='Helvetica 13')
lblLastKillMedal = Label(frame, text="Medal:", font='Helvetica 13')
lblLastKillTrophy = Label(frame, text="Trophy Score:", font='Helvetica 13')
lblLastKillWeapon = Label(frame, text="Weapon:", font='Helvetica 13')
lblLastKillDistance = Label(frame, text="Distance:", font='Helvetica 13')

lblLastKillAnimalVal = Label(frame, text="---")
lblLastKillTrophyVal = Label(frame, text="---")
lblLastKillMedalVal = Label(frame, text="---")
lblLastKillWeaponVal = Label(frame, text="---")
lblLastKillDistanceVal = Label(frame, text="---")

mySeparator2 = ttk.Separator(frame, orient='horizontal')

lblRecentKillTitle = Label(frame, text="Most Recent Kills", font='Helvetica 13 bold')

lblRecentKillHunter = Label(frame, text="Hunter", font='Helvetica 13')
lblRecentKillAnimal = Label(frame, text="Animal", font='Helvetica 13')
lblRecentKillScore = Label(frame, text="Score", font='Helvetica 13')
lblRecentKillWeapon = Label(frame, text="Weapon", font='Helvetica 13')
lblRecentKillDistance = Label(frame, text="Distance", font='Helvetica 13')
lblRecentKillWhen = Label(frame, text="When", font='Helvetica 13')

lblRecentKillHunterVal0 = Label(frame, text="-")
lblRecentKillAnimalVal0 = Label(frame, text="-")
lblRecentKillScoreVal0 = Label(frame, text="-")
lblRecentKillWeaponVal0 = Label(frame, text="-")
lblRecentKillDistanceVal0 = Label(frame, text="-")
lblRecentKillWhenVal0 = Label(frame, text="-")

lblRecentKillHunterVal1 = Label(frame, text="-")
lblRecentKillAnimalVal1 = Label(frame, text="-")
lblRecentKillScoreVal1 = Label(frame, text="-")
lblRecentKillWeaponVal1 = Label(frame, text="-")
lblRecentKillDistanceVal1 = Label(frame, text="-")
lblRecentKillWhenVal1 = Label(frame, text="-")

lblRecentKillHunterVal2 = Label(frame, text="-")
lblRecentKillAnimalVal2 = Label(frame, text="-")
lblRecentKillScoreVal2 = Label(frame, text="-")
lblRecentKillWeaponVal2 = Label(frame, text="-")
lblRecentKillDistanceVal2 = Label(frame, text="-")
lblRecentKillWhenVal2 = Label(frame, text="-")

lblRecentKillHunterVal3 = Label(frame, text="-")
lblRecentKillAnimalVal3 = Label(frame, text="-")
lblRecentKillScoreVal3 = Label(frame, text="-")
lblRecentKillWeaponVal3 = Label(frame, text="-")
lblRecentKillDistanceVal3 = Label(frame, text="-")
lblRecentKillWhenVal3 = Label(frame, text="-")

lblRecentKillHunterVal4 = Label(frame, text="-")
lblRecentKillAnimalVal4 = Label(frame, text="-")
lblRecentKillScoreVal4 = Label(frame, text="-")
lblRecentKillWeaponVal4 = Label(frame, text="-")
lblRecentKillDistanceVal4 = Label(frame, text="-")
lblRecentKillWhenVal4 = Label(frame, text="-")

mySeparator3 = ttk.Separator(frame, orient='horizontal')
lblCurrentCompHeader = Label(frame, text="Current Competition", font='Helvetica 13 bold')
lblCompTitle = Label(frame, text="None", font='Helvetica 13 italic', fg='blue')

lblCompAnimal = Label(frame, text="Animal", font='Helvetica 13')
lblCompHunter = Label(frame, text="Hunter", font='Helvetica 13')
lblCompScore = Label(frame, text="Score", font='Helvetica 13')
lblCompWhen = Label(frame, text="When", font='Helvetica 13')
lblCompPrize = Label(frame, text="Prize", font='Helvetica 13')

# Positioning Elements
lblReserve.grid(row=0, column=0)
dropReserves.grid(row=0, column=1)
dropReserves["menu"].config(bg="white")

lblAnimal.grid(row=1, column=0)
dropAnimals.grid(row=1, column=1)
dropAnimals["menu"].config(bg="white")

lblAnimalStatClass.grid(row=0, column=2)
lblAnimalStatClassVal.grid(row=1, column=2)

lblAnimalStatMaxWeight.grid(row=0, column=3)
lblAnimalStatMaxWeightVal.grid(row=1, column=3)

lblAnimalStatWeightTrack.grid(row=0, column=4)
lblAnimalStatWeightTrackVal.grid(row=1, column=4)

mySeparator1.grid(row=2, columnspan=100, sticky="ew", pady=10)

lblLastKillTitle.grid(row=3, column=0, columnspan=100, sticky="ew")

lblLastKillAnimalVal.grid(row=4, column=1)
lblLastKillAnimal.grid(row=4, column=0)

lblKingCompImage.grid(row=4, column=3, rowspan=3)
lblKingTopImage.grid(row=4, column=4, rowspan=3)
lblKingCompImage.grid_remove()
lblKingTopImage.grid_remove()

lblLastKillMedal.grid(row=5, column=0)
lblLastKillMedalVal.grid(row=5, column=1)

lblLastKillTrophyVal.grid(row=6, column=1)
lblLastKillTrophy.grid(row=6, column=0)

lblLastKillWeaponVal.grid(row=7, column=1)
lblLastKillWeapon.grid(row=7, column=0)

lblLastKillDistanceVal.grid(row=8, column=1)
lblLastKillDistance.grid(row=8, column=0)

mySeparator2.grid(row=9, columnspan=100, sticky="ew", pady=10)

lblRecentKillTitle.grid(row=10, column=0, columnspan=100, sticky="ew")

lblRecentKillHunter.grid(row=11, column=0)
lblRecentKillAnimal.grid(row=11, column=1)
lblRecentKillScore.grid(row=11, column=2)
lblRecentKillWeapon.grid(row=11, column=3)
lblRecentKillDistance.grid(row=11, column=4)
lblRecentKillWhen.grid(row=11, column=5)

lblRecentKillHunterVal0.grid(row=12, column=0)
lblRecentKillAnimalVal0.grid(row=12, column=1)
lblRecentKillScoreVal0.grid(row=12, column=2)
lblRecentKillWeaponVal0.grid(row=12, column=3)
lblRecentKillDistanceVal0.grid(row=12, column=4)
lblRecentKillWhenVal0.grid(row=12, column=5)

lblRecentKillHunterVal1.grid(row=13, column=0)
lblRecentKillAnimalVal1.grid(row=13, column=1)
lblRecentKillScoreVal1.grid(row=13, column=2)
lblRecentKillWeaponVal1.grid(row=13, column=3)
lblRecentKillDistanceVal1.grid(row=13, column=4)
lblRecentKillWhenVal1.grid(row=13, column=5)

lblRecentKillHunterVal2.grid(row=14, column=0)
lblRecentKillAnimalVal2.grid(row=14, column=1)
lblRecentKillScoreVal2.grid(row=14, column=2)
lblRecentKillWeaponVal2.grid(row=14, column=3)
lblRecentKillDistanceVal2.grid(row=14, column=4)
lblRecentKillWhenVal2.grid(row=14, column=5)

lblRecentKillHunterVal3.grid(row=15, column=0)
lblRecentKillAnimalVal3.grid(row=15, column=1)
lblRecentKillScoreVal3.grid(row=15, column=2)
lblRecentKillWeaponVal3.grid(row=15, column=3)
lblRecentKillDistanceVal3.grid(row=15, column=4)
lblRecentKillWhenVal3.grid(row=15, column=5)

lblRecentKillHunterVal4.grid(row=16, column=0)
lblRecentKillAnimalVal4.grid(row=16, column=1)
lblRecentKillScoreVal4.grid(row=16, column=2)
lblRecentKillWeaponVal4.grid(row=16, column=3)
lblRecentKillDistanceVal4.grid(row=16, column=4)
lblRecentKillWhenVal4.grid(row=16, column=5)

mySeparator3.grid(row=17, columnspan=100, sticky="ew", pady=10)

lblCurrentCompHeader.grid(row=18, column=0, columnspan=100, sticky="ew")
lblCompTitle.grid(row=19, column=0, columnspan=100, sticky="ew")

lblCompAnimal.grid(row=20, column=0)
lblCompHunter.grid(row=20, column=1)
lblCompScore.grid(row=20, column=2)
lblCompWhen.grid(row=20, column=3)
lblCompPrize.grid(row=20, column=4)

t = threading.Thread(target=mainLoop)
t.daemon = True
t.start()

t1 = threading.Thread(target=update_latest_kills)
t1.daemon = True
t1.start()

t2 = threading.Thread(target=check_for_comp)
t2.daemon = True
t2.start()

win.mainloop()
