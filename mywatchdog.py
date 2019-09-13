#!/usr/bin/python3

import os.path
import time

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

watchdog_time = 180 # 3 Min
watch_time = time.time()
while True:

    if (time.time() - watch_time) > watchdog_time:
        watch_time = time.time()
        if os.path.isfile("mywatchdog.txt"):
            print("file exists")
            os.remove("mywatchdog.txt")
        else:
            print("File doesn't exists")
            restart_pi()

