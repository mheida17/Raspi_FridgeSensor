#!/usr/bin/python3

#import os.path
import os
import time

##########################################
# FUNCTION TO RESTART RASPI
##########################################
def restart_pi():
     os.system("sudo shutdown -r now")


##########################################
# UOPDATE LOG FILE MESSAGE
##########################################
def logfile_message(message):
    FILE_NAME = open(DATAFILE, "a+")
    FILE_NAME.write(
        "%s  %s \r\n"
        % (
            time.strftime("%b %d - %H:%M:%S"),
            message
        )
    )
    FILE_NAME.close()
    print(message)

##########################################
#     MAIN LOOP
##########################################
DATAFILE = "temperature_data.txt"
watchdog_time = 180 # 3 Min
watch_time = time.time()  #INIT WATCH TIME
while True:

    if time.localtime(time.time()).tm_sec == 50 and (time.time() - watch_time) > watchdog_time:
        watch_time = time.time()
        if os.path.isfile("mywatchdog.txt"):  # Does watchdog.txt file exist
            print("file exists")
            os.remove("mywatchdog.txt")
        else:
            print("File doesn't exists")
            logfile_message("WATCHDOG AUTO REBOOT")
            restart_pi()
