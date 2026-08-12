import os
import random
import subprocess

# --- Configuration ---
RECEIVER_IP = '192.168.103.10'   # The IP of the destination Raspberry Pi
RECEIVER_USER = 'pi'             # The username on the destination Pi
DESTINATION_PATH = '/home/pi/'   # Where to save the file on the receiver
DUMMY_FILE = 'dummy_data.txt'
FILE_SIZE_BYTES = 1024 * 1024   # 10 MB

# 1. Generate the dummy file
print("[STATUS] Generating 1MB dummy file...")
with open(DUMMY_FILE, 'w') as f:
    chunk = "".join(random.choice(['0', '1']) for _ in range(1024))
    for _ in range(FILE_SIZE_BYTES // 1024):
        f.write(chunk)
print("[STATUS] File generated.")

# 2. Send the file using SCP (Piggybacking on the receiver's SSH service)
print(f"[STATUS] Sending {DUMMY_FILE} to {RECEIVER_USER}@{RECEIVER_IP}...")

# Build the scp command
PI_PASSWORD = 'PiSatNetwork'  # Put the Pi password here

scp_command = [
    "sshpass", "-p", PI_PASSWORD,
    "scp",
    "-o", "StrictHostKeyChecking=no",
    DUMMY_FILE, 
    f"{RECEIVER_USER}@{RECEIVER_IP}:{DESTINATION_PATH}"
]

try:
    # Run the command
    subprocess.run(scp_command, check=True)
    print(f"[SUCCESS] File successfully sent to {RECEIVER_IP}!")
except subprocess.CalledProcessError as e:
    print(f"[ERROR] Failed to send file. Make sure SSH is enabled on the receiving Pi. Details: {e}")
except FileNotFoundError:
    print("[ERROR] The 'scp' command was not found on this system.")