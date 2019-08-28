#!/usr/bin/python3

# generic imports
import time
import os
import sys
#import requests
#import urllib3
import socket
#from urllib.request import urlopen

# imports for email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# imports for temperature
if sys.platform != "darwin":
    RASPI_BOOL = True
    import Adafruit_DHT

    SENSOR_1 = SENSOR_2 = Adafruit_DHT.DHT22
else:
    RASPI_BOOL = False

# Globals
with open("email_password.txt", "r") as file:
    SRC_USERNAME, SRC_PASSWORD = file.read().split(" ")
# update to accept more than a single email from file
with open("destination_email_list.txt", "r") as file:
    MAIL_LIST = [line.split(", ") for line in file.readlines()]

PIN_1 = 17   #Ambient
PIN_2 = 23   #Remote
DATAFILE = "temperature_data.txt"
BOOT_TIME = time.time()
Internet_time = time.time()
TEST_INTERNET_IN_SEC = 25	#Must be greater than 4 sec or considered a DoS.

##########################################
# FUNCTION TO RECORD TEMPERATURE
##########################################

def record_temperature():
    try:
        if RASPI_BOOL:
            humidity_1, temperature_1 = Adafruit_DHT.read_retry(SENSOR_1, PIN_1)
            humidity_2, temperature_2 = Adafruit_DHT.read_retry(SENSOR_2, PIN_2)
        else:
            humidity_1 = humidity_2 = temperature_1 = temperature_2 = None
        if humidity_1 is None or temperature_1 is None:
            humidity_1 = 100
            temperature_1 = 100
        if humidity_2 is None or temperature_2 is None:
            humidity_2 = 100
            temperature_2 = 100
    except RuntimeError:
        FILE_NAME.write("Error reading sensor!\r\n")
    else:
        if temperature_1 is None:
            temperature_1 = 100
        if temperature_2 is None:
            temperature_2 = 100
    temperature_1 = (temperature_1 -3)* 9 / 5.0 + 32
    temperature_2 = temperature_2 * 9 / 5.0 + 32
    FILE_NAME.write(
        "%s Ambient Temp %d Ambient Humidity %d Fridge Temp %d\r\n"
        % (
            time.strftime("%b %d - %H:%M:%S"),
            temperature_1,
            humidity_1,
            temperature_2,
        )
    )

##########################################
# FUNCTION TO ADD UPTIME TO FILE
##########################################

def add_uptime_to_file():
    uptime = time.time() - BOOT_TIME
    days = int(uptime / 86400)
    hours = int(uptime % 86400 / 3600)
    minutes = int(uptime % 3600 / 60)
    seconds = int(uptime % 60)
    with open(DATAFILE, "r+") as data_file:
        data_file.write(
            "Total Uptime (D:H:M:S) = %d:%d:%02d:%02d \r\n" % (days, hours, minutes, seconds)
        )

##########################################
# MESSAGE
##########################################
def network_message(message):
    FILE_NAME = open(DATAFILE, "a+")
    FILE_NAME.write(
        "%s  %s \r\n"
        % (
            time.strftime("%b %d - %H:%M:%S"),
            message,
        )
    )
    FILE_NAME.close()
    print(message)

##########################################
#  Function to check internet / wifi
##########################################
def check_internet(url):
#    timeout=1
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('www.google.com',80))
#        _ = requests.get(url, timeout=timeout)
        message="Internet status is up"
        return message
#    except requests.ConnectionError:
    except:
        message="Internet status is down"
    return message

##########################################
# FUNCTION TO SEND EMAILS
##########################################

def send_email():
    for email_address in MAIL_LIST[0]:
        files = []
        files.append(DATAFILE)
        text = "{}/{} Sensor Readings".format(
            time.localtime(time.time()).tm_mon, time.localtime(time.time()).tm_mday
        )
        msg = MIMEMultipart()
        msg["Subject"] = text
        msg["From"] = SRC_USERNAME
        msg["To"] = email_address
        msg.attach(MIMEText(text))
        print("email_address")
        print(email_address)
        print("--------")
        for data_file in files:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(open(data_file, "rb").read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                'attachment; filename="%s"' % os.path.basename(data_file),
            )
            msg.attach(part)
            server = smtplib.SMTP("smtp.gmail.com:587")
            server.ehlo_or_helo_if_needed()
            server.starttls()
            server.ehlo_or_helo_if_needed()
            server.login(SRC_USERNAME, SRC_PASSWORD)
            server.sendmail(SRC_USERNAME, email_address, msg.as_string())
            server.quit()


##########################################
# FUNCTION TO RESTART RASPI
##########################################
def restart_pi():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    print("Entered restart subroutine REBOOTING")
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)

##########################################
# MAIN FUNCTION
##########################################
EMAIL_SENT_TODAY = False
MEASUREMENT_TAKEN = False
url='http://www.google.com/'
#url='http://time.google.com/'
message="Rebooting / Starting up"
network_message(message)  # adds reboot message on bootup
new_message = check_internet(url)

while True: 

    if (time.time()-Internet_time) > TEST_INTERNET_IN_SEC:
        t=time.time()
        new_message = check_internet(url)
        Internet_time = time.time()
        print("Internet testing took",int((Internet_time-t)*1000),"msec")
    if message != new_message:
        network_message(new_message)
        message = new_message
    # TODO: start using unix time to simplify the conditional statements
    if time.localtime(time.time()).tm_sec == 0 and not MEASUREMENT_TAKEN:
        FILE_NAME = open(DATAFILE, "a+")
        record_temperature()
        FILE_NAME.close()
        MEASUREMENT_TAKEN = True
    elif time.localtime(time.time()).tm_sec != 0 and MEASUREMENT_TAKEN:
        MEASUREMENT_TAKEN = False
    # add the uptime to the file before emailing
    if time.localtime(time.time()).tm_hour == 18 and not EMAIL_SENT_TODAY and message =="Internet status is up":
         add_uptime_to_file()
         send_email()
         os.remove(DATAFILE)
         with open(DATAFILE, "a+") as data_file:
             data_file.write(
             "x\r\n"
             )
         EMAIL_SENT_TODAY = True
    elif time.localtime(time.time()).tm_hour == 19 and EMAIL_SENT_TODAY:
        EMAIL_SENT_TODAY = False
