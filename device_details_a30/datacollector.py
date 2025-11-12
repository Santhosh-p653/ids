import subprocess
import csv
import re
import datetime
import os

# --- Configuration ---
CSV_FILE = 'mobile_ids_data.csv'
ADB_PATH = 'adb' # Assumes 'adb' is in your system PATH. If not, use the full path.

# --- 1. Utility Functions ---

def run_adb_shell(command):
    """Executes an ADB shell command and returns the output string."""
    try:
        # Use subprocess.run to execute the command and capture output
        result = subprocess.run(
            [ADB_PATH, 'shell', command],
            capture_output=True,
            text=True,
            check=True, # Raise an error if the command fails
            timeout=10 # Max time to wait for command
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running ADB command '{command}': {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print(f"ADB command '{command}' timed out.")
        return None
    except FileNotFoundError:
        print(f"Error: ADB executable not found. Check if '{ADB_PATH}' is correct or in PATH.")
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
        
        return None # No device found
    except Exception as e:
        print(f"Could not check devices: {e}")
        exit(1)

# --- 2. Feature Extraction Functions ---

def extract_cpu_features(cpuinfo_dump):
    """Parses dumpsys cpuinfo to get key CPU metrics."""
    features = {}
    
    # Example 1: Total CPU Usage
    # Pattern: '##% TOTAL: ##% user + ##% kernel + ...'
    match = re.search(r'(\d+\.\d+)% TOTAL:', cpuinfo_dump)
    features['Total_CPU_Usage_Pct'] = float(match.group(1)) if match else 0.0

    # Example 2: Top Process CPU Usage (Simple heuristic - find the first non-system/non-idle process)
    top_process_match = re.search(r'^\s*(\d+\.\d+)%\s+(\d+)/\w+\s*:\s*(.*)', cpuinfo_dump, re.MULTILINE)
    features['Top_Process_CPU_Pct'] = float(top_process_match.group(1)) if top_process_match else 0.0
    
    return features

def extract_mem_features(meminfo_dump):
    """Parses /proc/meminfo to get memory metrics."""
    features = {}
    
    # Example: Free Memory (in kB)
    match = re.search(r'MemFree:\s+(\d+)\s+kB', meminfo_dump)
    features['MemFree_kB'] = int(match.group(1)) if match else 0
    
    # You would also extract MemTotal, etc., to calculate ratios here
    
    return features

def extract_net_features(netstats_dump):
    """Parses dumpsys netstats for total network usage."""
    features = {}
    
    # Look for total received/transmitted bytes (Xt and Dev sections are too complex for a simple example)
    # This is a simplified example; actual netstats parsing is complex due to UID grouping
    rx_match = re.search(r'rxBytes=(\d+)', netstats_dump)
    tx_match = re.search(r'txBytes=(\d+)', netstats_dump)
    
    features['Total_Rx_Bytes'] = int(rx_match.group(1)) if rx_match else 0
    features['Total_Tx_Bytes'] = int(tx_match.group(1)) if tx_match else 0
    
    return features

# --- 3. Main Collection and Writing Logic ---

def collect_and_write_data(serial):
    """Runs all ADB commands, extracts features, and writes to CSV."""
    
    # Use the specific serial for all commands
    global ADB_PATH
    ADB_PATH = f'{ADB_PATH} -s {serial}' 
    
    print(f"Collecting data for device: {serial}...")

    # A. Execute all required ADB commands and store the RAW output
    raw_data = {}
    raw_data['Time_Stamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Commands you defined in your script
    raw_data['cpuinfo'] = run_adb_shell("dumpsys cpuinfo")
    raw_data['meminfo'] = run_adb_shell("cat /proc/meminfo")
    raw_data['netstats'] = run_adb_shell("dumpsys netstats")
    raw_data['batterystats'] = run_adb_shell("dumpsys batterystats")
    raw_data['logcat'] = run_adb_shell("logcat -d -t 2000")
    
    # Skip if any critical command failed
    if any(v is None for k, v in raw_data.items() if k != 'Time_Stamp'):
        print("Skipping write to CSV due to failed ADB command(s).")
        return

    # B. Extract Features from RAW output
    feature_row = {'Device_Serial': serial, 'Time_Stamp': raw_data['Time_Stamp']}
    
    feature_row.update(extract_cpu_features(raw_data['cpuinfo']))
    feature_row.update(extract_mem_features(raw_data['meminfo']))
    feature_row.update(extract_net_features(raw_data['netstats']))
    
    # Example of a simple Logcat feature: Error Count
    error_count = raw_data['logcat'].upper().count('/E') + raw_data['logcat'].upper().count('/F')
    feature_row['Logcat_Error_Count'] = error_count
    
    # C. Write to CSV
    
    # Check if file exists to determine if header is needed
    file_exists = os.path.exists(CSV_FILE)
    
    # Dynamically generate fieldnames from the features dictionary
    fieldnames = list(feature_row.keys())

    with open(CSV_FILE, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader() # Write header only once
            
        writer.writerow(feature_row)
        
    print(f"Successfully appended 1 row to {CSV_FILE}")
    print("--------------------------------------------------")

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting Mobile IDS Data Collection Script...")
    
    # 1. Find device
    serial_number = get_device_serial()
    
    if not serial_number:
        print("Fatal: No ADB device connected.")
    else:
        # 2. Collect and write
        collect_and_write_data(serial_number)
        
        # Optional: Add a loop here to collect data periodically
        # import time
        # while True:
        #     collect_and_write_data(serial_number)
        #     time.sleep(300) # Wait 5 minutes