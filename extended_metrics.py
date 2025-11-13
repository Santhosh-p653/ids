import subprocess
import csv
import time
import re
from datetime import datetime
import os

CSV_FILE = "ids_metrics.csv"
INTERVAL = 5  # seconds between readings

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
    output = adb("dumpsys activity activities")
    match = re.search(r"mResumedActivity:.*? ([\w\.]+)/", output)
    return match.group(1) if match else "Unknown"

def get_cpu_cores():
    output = adb("cat /proc/cpuinfo")
    cores = len(re.findall(r"processor\s*:", output))
    return cores if cores else 0

def get_memory_kb():
    output = adb("cat /proc/meminfo")
    match = re.search(r"MemAvailable:\s*(\d+)", output) or re.search(r"MemFree:\s*(\d+)", output)
    return int(match.group(1)) if match else None

def get_battery_info():
    output = adb("dumpsys battery")
    level = re.search(r"level[:=]\s*(\d+)", output)
    temp = re.search(r"temperature[:=]\s*(\d+)", output)
    voltage = re.search(r"voltage[:=]\s*(\d+)", output)

    battery_level = int(level.group(1)) if level else None
    temperature = (int(temp.group(1)) / 10) if temp else None
    voltage = (int(voltage.group(1)) / 1000) if voltage else None

    return battery_level, temperature, voltage

def get_wifi_ssid():
    output = adb("dumpsys wifi")
    match = re.search(r'SSID: "(.*?)"', output)
    return match.group(1) if match else "Unknown"

def collect_metrics():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    app = get_foreground_app()
    cpu = get_cpu_cores()
    mem = get_memory_kb()
    batt, temp, volt = get_battery_info()
    wifi = get_wifi_ssid()

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

def convert_to_binary_features(metrics):
    return {
        "suspicious_app": int(metrics["app"] in ["com.risky.app", "com.unknown.source"]),
        "high_cpu_cores": int(metrics["cpu_cores"] > 8),
        "low_memory": int(metrics["memory_kb"] is not None and metrics["memory_kb"] < 500000),
        "low_battery": int(metrics["battery_%"] is not None and metrics["battery_%"] < 20),
        "high_temperature": int(metrics["temperature_°C"] is not None and metrics["temperature_°C"] > 40),
        "abnormal_voltage": int(metrics["voltage_V"] is not None and (metrics["voltage_V"] < 3.5 or metrics["voltage_V"] > 4.5)),
        "unknown_wifi": int(metrics["wifi_ssid"] not in ["HomeNetwork", "OfficeNetwork", "Varsha💖"])
    }

def combine_metrics(metrics):
    binary = convert_to_binary_features(metrics)
    return {**metrics, **binary}

def save_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def main():
    print("🔐 Starting Android IDS Metrics Collector...")
    print(f"Saving to: {os.path.abspath(CSV_FILE)}\nPress Ctrl+C to stop.\n")

    try:
        while True:
            metrics = collect_metrics()
            combined = combine_metrics(metrics)
            save_to_csv(combined)
            print(f"✅ Logged: {combined}")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n🛑 Stopped. Data saved in ids_metrics.csv.")

if __name__ == "__main__":
    print("Saving to:", os.getcwd())
    main()
