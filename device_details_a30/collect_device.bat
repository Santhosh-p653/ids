@echo off
:: collect_device.bat
set TIMESTAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTDIR=%CD%\adb_collect_%TIMESTAMP%
mkdir "%OUTDIR%"

:: pick device (first)
for /f "skip=1 tokens=1,2" %%a in ('adb devices') do (
  if "%%b"=="device" set SERIAL=%%a & goto :gotdevice
)
echo No device found. Run adb devices.
goto :eof
:gotdevice
echo Using device %SERIAL%
set ADB=adb -s %SERIAL%

%ADB% shell getprop > "%OUTDIR%\getprop.txt"
%ADB% shell cat /proc/cpuinfo > "%OUTDIR%\proc_cpuinfo.txt" 2>nul
%ADB% shell cat /proc/meminfo > "%OUTDIR%\proc_meminfo.txt" 2>nul
%ADB% shell dumpsys meminfo > "%OUTDIR%\dumpsys_meminfo.txt" 2>nul
%ADB% logcat -d -t 2000 > "%OUTDIR%\logcat.txt" 2>nul
%ADB% exec-out screencap -p > "%OUTDIR%\screen.png" 2>nul

echo Attempting dmesg...
%ADB% shell dmesg > "%OUTDIR%\dmesg.txt" 2>nul || echo dmesg failed > "%OUTDIR%\dmesg_err.txt"

echo Done. Files in %OUTDIR%
pause