import subprocess
import csv
import time
from datetime import datetime
import os

OUTPUT_FILE = "metrics.csv"
INTERVAL = 5  # seconds between readings

# Run adb commands safely
def adb_shell(cmd):
    try:
        result = subprocess.check_output(f"adb shell {cmd}", shell=True, stderr=subprocess.DEVNULL)
        return result.decode("utf-8", errors="ignore").strip()
    except subprocess.CalledProcessError:
        return "none"

def adb(cmd):
    try:
        result = subprocess.check_output(f"adb {cmd}", shell=True, stderr=subprocess.DEVNULL)
        return result.decode("utf-8", errors="ignore").strip()
    except subprocess.CalledProcessError:
        return "none"

def get_cpu_usage():
    cpu_info = adb_shell("top -n 1 -b | head -10")
    return cpu_info if cpu_info else "none"

def get_mem_usage():
    mem = adb_shell("cat /proc/meminfo | head -5")
    return mem if mem else "none"

def get_battery_status():
    batt = adb_shell("dumpsys battery | grep level")
    return batt if batt else "none"

def get_temperature():
    temp = adb_shell("dumpsys battery | grep temperature")
    return temp if temp else "none"

def get_running_apps():
    apps = adb_shell("dumpsys activity | grep 'Run #' | head -5")
    return apps if apps else "none"

def get_network_stats():
    net = adb_shell("cat /proc/net/dev | grep wlan0")
    return net if net else "none"

def get_logcat_sample():
    logs = adb("logcat -d -t 10 | tail -n 5")
    adb("logcat -c")  # clear after reading
    return logs if logs else "none"

def initialize_csv():
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "cpu_usage",
                "mem_usage",
                "battery_level",
                "temperature",
                "running_apps",
                "network_stats",
                "log_sample"
            ])

def append_metrics():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = get_cpu_usage()
    mem = get_mem_usage()
    batt = get_battery_status()
    temp = get_temperature()
    apps = get_running_apps()
    net = get_network_stats()
    logs = get_logcat_sample()

    row = [timestamp, cpu, mem, batt, temp, apps, net, logs]

    with open(OUTPUT_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    print(f"[+] Logged at {timestamp}")

def main():
    initialize_csv()
    print("📊 Starting ADB data collection... Press Ctrl+C to stop.\n")
    try:
        while True:
            append_metrics()
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n🛑 Data collection stopped. File saved as metrics.csv")

if __name__ == "__main__":
    main()