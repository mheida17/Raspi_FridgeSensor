#!/usr/bin/python

#generic imports
import time
import os

#imports for email
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.parser import HeaderParser
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate
from email import encoders

#imports for temperature
#import Adafruit_DHT

with open("email_password.txt", 'r') as file:
  USERNAME, PASSWORD = file.read().split(" ")
#update to accept more than a single email from file
mail_list = []
with open("destination_email_list.txt", 'r') as file:
  mail_list.append(file.read())

email_time_sec = 68400 # 7 pm in seconds
record_freq = 60
#sensor_1 = sensor_2 = Adafruit_DHT.DHT22
pin_1 = 17
pin_2 = 23
DATAFILE = "temperature_data.txt"

##########################################
#FUNCTION TO RECORD TEMPERATURE
##########################################

def record_temperature(file_name):
  try:
    humidity_1, temperature_1 = (1, 2) #Adafruit_DHT.read_retry(sensor_1, pin_1) #round to nearest int
    humidity_2, temperature_2 = (3, 4) #Adafruit_DHT.read_retry(sensor_2, pin_2) #round to nearest int
    file_name.write("%d/%d - %d:%d:%d Ambient Temp %d Ambient Humidity %d Fridge Temp %d\r\n" % \
      (time.localtime(time.time()).tm_mon, time.localtime(time.time()).tm_mday, \
        time.localtime(time.time()).tm_hour, time.localtime(time.time()).tm_min, \
          time.localtime(time.time()).tm_sec, temperature_1, humidity_1, temperature_2))
  except RuntimeError as e:
    file_name.write("Error reading sensor!\r\n")
  

##########################################
#FUNCTION TO SEND EMAILS
##########################################

def send_email(mail_list):
  for email_address in mail_list:
    files = []
    files.append(DATAFILE)
    text = "{}/{} Sensor Readings".format(time.localtime(time.time()).tm_mon,\
      time.localtime(time.time()).tm_mday)
    assert type(files)==list 
    msg = MIMEMultipart()
    msg['Subject'] = text
    msg['From'] = USERNAME
    msg['To'] = email_address
    msg.attach ( MIMEText(text) )

    for file in files:
      part = MIMEBase('application', "octet-stream")
      part.set_payload(open(file,"rb").read())
      encoders.encode_base64(part)
      part.add_header('Content-Disposition', 'attachment; filename="%s"'\
        % os.path.basename(file))
      msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo_or_helo_if_needed()
    server.starttls()
    server.ehlo_or_helo_if_needed()
    server.login(USERNAME,PASSWORD)
    server.sendmail(USERNAME, email_address, msg.as_string())
    server.quit()

##########################################
# MAIN FUNCTION
##########################################
test_var = 0
while True:
  # add something to record powerup time
  # add reboot message to the file for every boot
  # add a manual reboot every 7 days
  file_name = open(DATAFILE, "a+")
  record_temperature(file_name)
  file_name.close()

  # add the uptime to the file before emailing
  if test_var == 10:
    send_email(mail_list)
    os.remove(DATAFILE)
    test_var = 0
  test_var += 1
  time.sleep(5)
