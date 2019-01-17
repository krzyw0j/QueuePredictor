from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors.
    This function just prints them, but you can
    make it do anything.
    """
    print(e)


#scraper

import json
import time, threading
import os
import datetime

periodicInterval = 15
address = "http://rezerwacje.duw.pl/status_kolejek/query.php?status"
dataFileName = "data"
initDataFileName = "initData.json"

cityNames = ['Wrocław', 'Jelenia Góra', 'Legnica', 'Wałbrzych']

lasts = {}

def getQueryJson():
    raw_json = simple_get(address)
    print(str(raw_json))
    if raw_json is None:
        return None
    return json.loads(raw_json)


fakeJsonIterator = 0
dayNumber = -1

def fakeGetQueryJson():
    global fakeJsonIterator
    json = getQueryJson()
    json["result"]['Wrocław'][0]["tickets_served"] = fakeJsonIterator
    fakeJsonIterator = fakeJsonIterator + 1
    return json

def init():
    global newDirectory
    global dayNumber

    now = datetime.datetime.now()

    newDirectory = str(now.day) + "." + f"{now.month:02d}"
    if not os.path.exists(newDirectory):
        os.makedirs(newDirectory)

    dayNumber = now.day
    json = getQueryJson()

    if json is None:
        return

    for city in json["result"].keys():
        lasts[city] = []

        for item in json["result"][city]:
            lasts[city].append((item["tickets_served"], item["registered_tickets"]))

    with open(newDirectory + "/" +initDataFileName, 'w', encoding="utf-8") as file:
        file.write(str(json))

    if json["result"].keys() == 4:
        print("Success of init")
    update()

def update():
    global newDirectory
    global dayNumber
    print("update:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    json = getQueryJson() #fakeGetQueryJson()

    if json is not None:

        for city in json["result"].keys():

            if city in lasts:
                for index, item in enumerate(json["result"][city]):
                    if lasts[city][index] != (item["tickets_served"], item["registered_tickets"]):
                        print("Exist changes")
                        print(item)
                        print(lasts[city][index])
                        print((item["tickets_served"], item["registered_tickets"]))

                        with open(newDirectory + "/" + dataFileName, 'a', encoding="utf-8") as file:
                            newJson = {"data" : item, "time" : time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
                            file.write(str(newJson)+"\n")

                        lasts[city][index] = (item["tickets_served"], item["registered_tickets"])
            else:
                #new city in update
                lasts[city] = []
                for item in json["result"][city]:
                    lasts[city].append((item["tickets_served"], item["registered_tickets"]))

    if datetime.datetime.now().day == dayNumber:
        threading.Timer(periodicInterval, update).start()
    else:
        print("New day!!!")
        init()

init()