""" Records the temperature of two locations and sends the file via email """
#!/usr/bin/python3

# generic imports
import time
import os
import sys
try:
    import httplib
except:
    import http.client as httplib

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

#GPIO setup
import RPi.GPIO as GPIO
LEDpin = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(LEDpin, GPIO.OUT,initial=GPIO.HIGH) # set LED pin as output

# Globals
with open("email_password.txt", "r") as file:
    SRC_USERNAME, SRC_PASSWORD = file.read().split(" ")

# TODO: update to accept more than a single email from file
with open("destination_email_list.txt", "r") as file:
    MAIL_LIST = [line.split(", ") for line in file.readlines()]

PIN_1 = 17   #Ambient
PIN_2 = 23   #Remote
DATAFILE = "temperature_data.txt"
BOOT_TIME = time.time()
##########################################
# FUNCTION TO RECORD TEMPERATURE
##########################################
def record_temperature():
    """ Records the temperature to the data file """
    file_name = open(DATAFILE, "a+")
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
        # TODO: Will this still set the temperatures that are used below?
        file_name.write("Error reading sensor!\r\n")
    else:
        if temperature_1 is None:
            temperature_1 = 100
        if temperature_2 is None:
            temperature_2 = 100
    temperature_1 = (temperature_1 - 3) * 9 / 5.0 + 32
    temperature_2 = temperature_2 * 9 / 5.0 + 32
    file_name.write(
        "%s Ambient Temp %d Ambient Humidity %d Fridge Temp %d\r\n"
        % (
            time.strftime("%b %d - %H:%M:%S"),
            temperature_1,
            humidity_1,
            temperature_2,
        )
    )
    file_name.close()


##########################################
# FUNCTION TO ADD UPTIME TO TOP OF FILE
##########################################
def add_uptime_to_file():
    """ Adds the raspberry pi uptime to the data file """
    uptime = time.time() - BOOT_TIME
    days = int(uptime / 86400)
    hours = int(uptime % 86400 / 3600)
    minutes = int(uptime % 3600 / 60)
    seconds = int(uptime % 60)
    with open(DATAFILE, "r") as data_file:
        temp = data_file.read()
    with open(DATAFILE, 'w') as data_file:
        data_file.write(
            "\rTotal Uptime (D:H:M:S) = %d:%d:%02d:%02d \r\n" % (
                days,
                hours,
                minutes,
                seconds
            )
        )
    with open(DATAFILE, 'a') as data_file:
        data_file.write(temp)

##########################################
# UPDATE LOG FILE MESSAGE
##########################################
def network_message(message, message1):
    """ Writes reboot message to the log file """
    file_name = open(DATAFILE, "a+")
    file_name.write(
        "%s  %s %s \r\n"
        % (
            time.strftime("%b %d - %H:%M:%S"),
            message, message1
        )
    )
    file_name.close()

##########################################
# CREATE WATCHDOG FILE
##########################################
def watchdog():
    """ Creates the watchdog file to make sure we are still running """
    file_name = open("mywatchdog.txt", "w")
    file_name.write(
        "%s  %s \r\n"
        % (
            time.strftime("%b %d - %H:%M:%S"),
            " Watchdog written"
        )
    )
    file_name.close()


##########################################
#  Function to check internet / wifi
##########################################
def check_connection(url):
    """ Verifies the raspberry pi is still connected to the internet """
    conn = httplib.HTTPConnection(url, timeout=2)
    try:
#        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        sock.connect((url,80))
#        _ = requests.get(url, timeout=timeout)
        conn.request("HEAD", "/")
        conn.close()
        message = " status is up"
#    except requests.ConnectionError:
    except:
        conn.close()
        message = " status is down"
    return message

##########################################
# FUNCTION TO SEND EMAILS
##########################################
def send_email():
    """ Sends the data file via email """
    for email_address in MAIL_LIST[0]:
        files = []
        files.append(DATAFILE)
        text = "{}/{} Home Sensor Readings".format(
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
    """ Restarts the raspberry pi """
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    print("Entered restart subroutine REBOOTING")
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)

##########################################
# MAIN FUNCTION
##########################################
def main():
    """ Main function """
    email_sent_today = False
    measurement_taken = False
    #Multiple websites to reduce frequency of pings per site
    websites = [
        "www.google.com",
        "www.github.com",
        "www.bing.com",
        "www.msn.com",
        "www.yahoo.com",
        "www.amazon.com"
    ]
    ip_address = "192.168.0.1" # Internal netowrk IP
    reboot_message = "Power loss Rebooting / Starting up "
    new_wifi_status = wifi_status = "WIFI"
    internet_status = "Internet"
    network_message(reboot_message, " ") # adds reboot message on bootup
    url_index = 0 #  URL list counter
    LED_on = True
    TEST_INTERNET_IN_SEC = 10       #Must be greater than 4 sec or considered a DoS.
    INTERNET_TIME = (time.time() - (TEST_INTERNET_IN_SEC*2)) # force test first time through
    while True:
        time.sleep(0.9) # ADDED TO CUT DOWN ON CPU USAGE

        # Has internet test intreval time been exceeded?
        if (time.time()-INTERNET_TIME) \
           > TEST_INTERNET_IN_SEC:

            new_internet_status = ("Internet" + check_connection(websites[url_index]))
            INTERNET_TIME = time.time()
            # Has the internet status changed?
            if internet_status != new_internet_status:
                # Update log file with Internet connectivity status and which url used
                network_message(new_internet_status, websites[url_index])
                internet_status = new_internet_status
                new_wifi_status = "WIFI" + check_connection(ip_address)  # Check WIFI status

                # Has WIFI status changed
                if wifi_status != new_wifi_status:
                    network_message(new_wifi_status, ip_address) # Update log file
                    wifi_status = new_wifi_status

            url_index = (url_index + 1) % len(websites) # update url counter allowing for wraparound
            #Blink I'm alive LED
        if LED_on:
            GPIO.output(LEDpin, GPIO.LOW)
            LED_on = False
        else:
            GPIO.output(LEDpin, GPIO.HIGH)
            LED_on = True

        # TODO: start using unix time to simplify the conditional statements
        if time.localtime(time.time()).tm_sec == 0 and not measurement_taken:
            watchdog()  #Create watchdog file every min.
            record_temperature()
            measurement_taken = True
        elif time.localtime(time.time()).tm_sec != 0 and measurement_taken:
            measurement_taken = False

        # add the uptime to the file before emailing
        if time.localtime(time.time()).tm_hour == 18 \
           and not email_sent_today and internet_status == "Internet status is up":

            add_uptime_to_file()
            send_email()
            os.remove(DATAFILE)
            email_sent_today = True

        elif time.localtime(time.time()).tm_hour == 19 and email_sent_today:
            email_sent_today = False

if __name__ == "__main__":
    main()
