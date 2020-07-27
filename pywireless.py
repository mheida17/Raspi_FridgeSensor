import os

#'\' is used to splite pythone line
ipaddress = os.popen("ifconfig wlan0 \
                     | grep 'inet' \
                     | awk -F: '{print $2}' \
                     | awk '{print $1}'").read()
ssid = os.popen("iwconfig wlan0 \
                | grep 'ESSID' \
                | awk '{print $4}' \
                | awk -F\\\" '{print $2}'").read()

print("ssid: " + ssid)
print("ipaddress: " + ipaddress)
essid = os.popen("iwgetid -r").read()
print(essid)
