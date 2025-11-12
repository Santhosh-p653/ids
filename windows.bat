@echo off
adb kill-server
adb start-server
adb tcpip 5555
adb connect 192.168.23.28:5555
adb devices
pause