""" Watchdog Program To Make Sure Another Program Is Not Frozen """
#!/usr/bin/python3

#import os.path
import os
import time

##########################################
# FUNCTION TO RESTART RASPI
##########################################
def restart_pi():
    """ Restarts the Raspberry Pi """
    os.system("sudo shutdown -r now")

##########################################
# UOPDATE LOG FILE MESSAGE
##########################################
def logfile_message(message, data_file):
    """ Logs the current time to the watchdog file """
    file_name = open(data_file, "a+")
    file_name.write(
        "%s  %s \r\n"
        % (
            time.strftime("%b %d - %H:%M:%S"),
            message
        )
    )
    file_name.close()
    print(message)

##########################################
#     MAIN LOOP
##########################################
def main():
    """ Main Function """
    data_file = "temperature_data.txt"
    watchdog_period_sec = 600 # Checks every 10 Min
    watch_time_sec = time.time() # INIT WATCH TIME

    while True:
        time.sleep(0.9)

        if time.localtime(time.time()).tm_sec == 50 \
           and (time.time() - watch_time_sec) > watchdog_period_sec:

            watch_time_sec = time.time()
            if os.path.isfile("mywatchdog.txt"):  # Does watchdog.txt file exist
                print("file exists")
                os.remove("mywatchdog.txt")
                time.sleep(watchdog_period_sec)
            else:
                print("File doesn't exists")
                logfile_message("WATCHDOG AUTO REBOOT", data_file)
                restart_pi()

if __name__ == "__main__":
    main()
