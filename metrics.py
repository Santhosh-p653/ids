import subprocess
import csv
import time
import re
from datetime import datetime
import os

CSV_FILE = "metrics.csv"

def adb(command):
    """Run ADB shell command and return output."""
    try:
        result = subprocess.run(
            ["adb", "shell", command],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def get_foreground_app():
    """Get currently running foreground app."""
    output = adb("dumpsys activity activities")
    match = re.search(r"mResumedActivity:.*? ([\w\.]+)/", output)
    return match.group(1) if match else "Unknown"

def get_cpu_usage():
    """Count CPU cores from /proc/cpuinfo."""
    output = adb("cat /proc/cpuinfo")
    cores = len(re.findall(r"processor\s*:", output))
    return cores if cores else 0

def get_memory_info():
    """Get available memory (kB)."""
    output = adb("cat /proc/meminfo")
    match = re.search(r"MemAvailable:\s*(\d+)", output) or re.search(r"MemFree:\s*(\d+)", output)
    return int(match.group(1)) if match else None

def get_battery_info():
    """Get battery level, temp (°C), and voltage (V)."""
    output = adb("dumpsys battery")
    level = re.search(r"level[:=]\s*(\d+)", output)
    temp = re.search(r"temperature[:=]\s*(\d+)", output)
    voltage = re.search(r"voltage[:=]\s*(\d+)", output)

    battery_level = int(level.group(1)) if level else None
    temperature = (int(temp.group(1)) / 10) if temp else None
    voltage = (int(voltage.group(1)) / 1000) if voltage else None

    return battery_level, temperature, voltage

def get_network_info():
    """Get connected Wi-Fi SSID (if available)."""
    output = adb("dumpsys wifi | grep 'SSID'")
    match = re.search(r'SSID: "(.*?)"', output)
    return match.group(1) if match else "Unknown"

def collect_metrics():
    """Collect all system metrics."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    app = get_foreground_app()
    cpu = get_cpu_usage()
    mem = get_memory_info()
    batt, temp, volt = get_battery_info()
    wifi = get_network_info()

    return {
        "timestamp": timestamp,
        "app": app,
        "cpu_cores": cpu,
        "memory_kb": mem,
        "battery_%": batt,
        "temperature_°C": temp,
        "voltage_V": volt,
        "wifi_ssid": wifi
    }

def save_to_csv(data):
    """Save data to a single CSV file."""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def main():
    print("📱 Starting Android metrics collector...")
    print("Data will be saved to metrics.csv\nPress Ctrl+C to stop.\n")

    try:
        while True:
            metrics = collect_metrics()
            save_to_csv(metrics)
            print(f"✅ Logged: {metrics}")
            time.sleep(5)  # interval in seconds
    except KeyboardInterrupt:
        print("\n🛑 Stopped logging. All data saved in metrics.csv.")

if __name__ == "__main__":
    main()