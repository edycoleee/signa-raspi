import os
import datetime

LOG_DIR = "/home/sultan/signage/logs"
LOG_PATH = os.path.join(LOG_DIR, "signage.log")

# Pastikan folder log ada
os.makedirs(LOG_DIR, exist_ok=True)

def log(action, message):
    """Catat event ke signage.log"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {action.upper()}: {message}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"?? LOG: {line.strip()}")  # Juga print ke console untuk debugging