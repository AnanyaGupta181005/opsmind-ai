import os
import re
import logging
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------
# 1. Logging Configuration
# ------------------------------------------------------------
# Using logging instead of print statements for cleaner output
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# ------------------------------------------------------------
# 2. File Paths (Relative or Environment Variable-Based)
# ------------------------------------------------------------
# Avoiding hard-coded personal paths
LOGFILE = os.getenv("SERVER_LOG_PATH", "server_raw.log")
OUTPUT_FILE = "clean_logs.csv"

# ------------------------------------------------------------
# 3. Validate File Existence
# ------------------------------------------------------------
if not os.path.exists(LOGFILE):
    logging.error(f"Log file not found: {LOGFILE}")
    raise FileNotFoundError("The specified log file does not exist.")

logging.info("Starting log analysis...")

# ------------------------------------------------------------
# 4. Compile a more robust regex pattern
# ------------------------------------------------------------
# Pattern explained:
# - Matches timestamps YYYY-MM-DD HH:MM:SS
# - Matches an IP address (supports 0–255 ranges loosely)
pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?(\d{1,3}(?:\.\d{1,3}){3})"
)

records = []

# ------------------------------------------------------------
# 5. Stream logs line-by-line (memory efficient)
# ------------------------------------------------------------
with open(LOGFILE, "r") as f:
    for line in f:
        match = pattern.search(line)
        if match:
            timestamp_str = match.group(1)
            ip = match.group(2)

            # Safe timestamp parsing with error handling
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logging.warning(f"Skipping invalid timestamp: {timestamp_str}")
                continue

            records.append({
                "timestamp": timestamp,
                "ip": ip
            })

# ------------------------------------------------------------
# 6. Convert to DataFrame
# ------------------------------------------------------------
df = pd.DataFrame(records)

if df.empty:
    logging.warning("No valid logs were parsed. Exiting safely.")
else:
    # Extract hour
    df["hour"] = df["timestamp"].dt.hour

    # Busiest hour (safe check)
    try:
        busiest_hour = df["hour"].value_counts().idxmax()
        logging.info(f"Busiest hour detected: {busiest_hour}:00")
    except ValueError:
        logging.warning("No hour data found. Skipping busiest hour calculation.")

    # --------------------------------------------------------
    # 7. Export CSV without disclosing sensitive paths
    # --------------------------------------------------------
    df.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"Cleaned log data saved to '{OUTPUT_FILE}'")

logging.info("Log analysis completed successfully.")
