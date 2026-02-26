"""
data_stream.py
==============
Simulates real-time environmental sensor data and writes it to a JSON file.
In a real-world setup, this would be replaced by Apache Kafka producing messages
to a topic, and Pathway would consume from that Kafka topic.

HOW IT WORKS:
- Runs in an infinite loop (like a real sensor)
- Every 2 seconds, generates random AQI, temperature, and humidity values
- Appends each reading as a JSON line to 'sensor_data.jsonl'
- The monitoring pipeline reads this file as a live stream
"""

import json
import time
import random
import os
from datetime import datetime

# ──────────────────────────────────────────────
# Output file – Pathway will watch this file
# ──────────────────────────────────────────────
OUTPUT_FILE = "sensor_data.jsonl"

def generate_sensor_reading():
    """
    Simulate one reading from an environmental sensor.
    Returns a dictionary with AQI, temperature, and humidity.
    
    In production: this data would come from real IoT sensors
    or be received from a Kafka topic.
    """
    return {
        "timestamp": datetime.now().isoformat(),          # Current time
        "aqi": random.randint(20, 250),                   # Air Quality Index (0–500 scale)
        "temperature_c": round(random.uniform(15.0, 50.0), 1),  # Celsius
        "humidity_pct": random.randint(20, 99),           # Relative humidity %
        "sensor_id": random.choice(["SENSOR_A", "SENSOR_B", "SENSOR_C"])  # Multi-sensor support
    }

def run_data_stream():
    """
    Main loop: generate and write sensor readings every 2 seconds.
    Press Ctrl+C to stop.
    """
    print("🌍 Environmental Data Stream STARTED")
    print(f"📄 Writing data to: {OUTPUT_FILE}")
    print("Press Ctrl+C to stop.\n")

    # Clear old data on startup for a fresh run
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    reading_count = 0

    while True:
        reading = generate_sensor_reading()
        reading_count += 1

        # Append the reading as a single JSON line (JSONL format)
        # Pathway's file connector reads JSONL natively
        with open(OUTPUT_FILE, "a") as f:
            f.write(json.dumps(reading) + "\n")

        # Console feedback so you can see data flowing
        print(f"[{reading_count:04d}] {reading['timestamp']} | "
              f"AQI={reading['aqi']:>3} | "
              f"Temp={reading['temperature_c']:>4}°C | "
              f"Humidity={reading['humidity_pct']:>2}%")

        time.sleep(2)  # Simulate a sensor that reads every 2 seconds

if __name__ == "__main__":
    run_data_stream()
