import subprocess
import csv
import re
import datetime
import os

# --- Configuration ---
CSV_FILE = 'mobile_ids_data.csv'
ADB_PATH = r'C:\platform-tools\adb.exe'  # Full path to adb.exe

# --- 1. Utility Functions ---

def run_adb_shell(command, serial):
    """Executes an ADB shell command for the given serial and returns the output string."""
    try:
        result = subprocess.run(
            [ADB_PATH, '-s', serial, 'shell', command],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running ADB command '{command}': {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print(f"ADB command '{command}' timed out.")
        return None
    except FileNotFoundError:
        print(f"Error: ADB executable not found. Check path '{ADB_PATH}'.")
        exit(1)

def get_device_serial():
    """Finds the serial of the first connected device."""
    try:
        devices_output = subprocess.run(
            [ADB_PATH, 'devices'],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip().split('\n')
        
        for line in devices_output[1:]:
            if line.endswith('device'):
                return line.split('\t')[0]
        return None
    except Exception as e:
        print(f"Could not check devices: {e}")
        exit(1)

# --- 2. Feature Extraction Functions ---

def extract_cpu_features(cpuinfo_dump):
    """Parses dumpsys cpuinfo to get key CPU metrics."""
    features = {}
    match = re.search(r'(\d+\.\d+)% TOTAL:', cpuinfo_dump)
    features['Total_CPU_Usage_Pct'] = float(match.group(1)) if match else 0.0

    top_process_match = re.search(r'^\s*(\d+\.\d+)%\s+(\d+)/\w+\s*:\s*(.*)', cpuinfo_dump, re.MULTILINE)
    features['Top_Process_CPU_Pct'] = float(top_process_match.group(1)) if top_process_match else 0.0
    
    return features

def extract_mem_features(meminfo_dump):
    """Parses /proc/meminfo to get memory metrics."""
    features = {}
    match = re.search(r'MemFree:\s+(\d+)\s+kB', meminfo_dump)
    features['MemFree_kB'] = int(match.group(1)) if match else 0
    match_total = re.search(r'MemTotal:\s+(\d+)\s+kB', meminfo_dump)
    features['MemTotal_kB'] = int(match_total.group(1)) if match_total else 0
    if features['MemTotal_kB'] > 0:
        features['Free_Mem_Pct'] = round((features['MemFree_kB'] / features['MemTotal_kB']) * 100, 2)
    else:
        features['Free_Mem_Pct'] = 0.0
    return features

def extract_net_features(netstats_dump):
    """Parses dumpsys netstats for total network usage."""
    features = {}
    rx_match = re.search(r'rxBytes=(\d+)', netstats_dump)
    tx_match = re.search(r'txBytes=(\d+)', netstats_dump)
    features['Total_Rx_Bytes'] = int(rx_match.group(1)) if rx_match else 0
    features['Total_Tx_Bytes'] = int(tx_match.group(1)) if tx_match else 0
    return features

# --- 3. Main Collection and Writing Logic ---

def collect_and_write_data(serial):
    """Runs all ADB commands, extracts features, and writes to CSV."""
    print(f"Collecting data for device: {serial}...\n")

    raw_data = {}
    raw_data['Time_Stamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Gather raw system info via ADB
    raw_data['cpuinfo'] = run_adb_shell("dumpsys cpuinfo", serial)
    raw_data['meminfo'] = run_adb_shell("cat /proc/meminfo", serial)
    raw_data['netstats'] = run_adb_shell("dumpsys netstats", serial)
    raw_data['batterystats'] = run_adb_shell("dumpsys batterystats", serial)
    raw_data['logcat'] = run_adb_shell("logcat -d -t 2000", serial)

    if any(v is None for k, v in raw_data.items() if k != 'Time_Stamp'):
        print("Skipping write to CSV due to failed ADB command(s).")
        return

    # Extract summarized features
    feature_row = {
        'Device_Serial': serial,
        'Time_Stamp': raw_data['Time_Stamp']
    }
    feature_row.update(extract_cpu_features(raw_data['cpuinfo']))
    feature_row.update(extract_mem_features(raw_data['meminfo']))
    feature_row.update(extract_net_features(raw_data['netstats']))

    error_count = raw_data['logcat'].upper().count('/E') + raw_data['logcat'].upper().count('/F')
    feature_row['Logcat_Error_Count'] = error_count

    # Write to CSV
    file_exists = os.path.exists(CSV_FILE)
    fieldnames = list(feature_row.keys())

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(feature_row)

    print(f"✅ Successfully appended 1 row to {CSV_FILE}")
    print("--------------------------------------------------")

# --- Main Execution ---
if __name__ == '__main__':
    print("🚀 Starting Mobile IDS Data Collection Script...\n")

    serial_number = get_device_serial()

    if not serial_number:
        print("❌ Fatal: No ADB device connected.")
    else:
        collect_and_write_data(serial_number)
        print("✅ Collection completed successfully!")
        # Optional continuous loop:
        # import time
        # while True:
        #     collect_and_write_data(serial_number)
        #     time.sleep(300)