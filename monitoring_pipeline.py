"""
monitoring_pipeline.py
======================
⚠️  WINDOWS / PYTHON 3.13+ COMPATIBLE VERSION

Pathway only supports Linux/macOS and Python 3.10-3.12.
This file uses a pure-Python streaming engine that mirrors Pathway's
exact behavior — same logic, same output format, same architecture.

To upgrade to real Pathway on Linux/Mac (Python 3.10-3.12):
    pip install pathway==0.16.3
    Then uncomment the REAL PATHWAY CODE block at the bottom.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW PATHWAY HANDLES STREAMING (Beginner Explanation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pathway treats data as a continuous, ever-growing TABLE — not a batch.

Traditional (Batch):   [Read file] → [Process ALL rows] → [Write output]  ← one shot
Pathway (Streaming):   [Watch file] → [Process EACH NEW ROW instantly] → [Update output]  ← forever

When a new line appears in sensor_data.jsonl, Pathway:
  ① Detects the change automatically (like a database trigger)
  ② Runs your transformation/filter logic on just the new row
  ③ Emits the updated result to the output — in milliseconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHERE APACHE KAFKA FITS (Conceptual Integration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
In a production system:
  - data_stream.py → Kafka Producer → topic "env-sensors"
  - Pathway → Kafka Consumer → subscribes to "env-sensors" topic
  - Swap pw.io.jsonlines.read() with pw.io.kafka.read()
  - Everything else stays identical!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import time
import os

INPUT_FILE  = "sensor_data.jsonl"
OUTPUT_FILE = "processed_data.jsonl"

# ── Risk detection functions (equivalent to pw.apply() transforms) ───

def detect_aqi_risk(aqi: int) -> str:
    if aqi > 150:
        return "🔴 UNSAFE AIR — Avoid outdoor activity"
    elif aqi > 100:
        return "🟡 MODERATE — Sensitive groups should be cautious"
    return "🟢 GOOD — Air quality is safe"

def detect_temp_risk(temp: float) -> str:
    if temp > 40:
        return "🔴 HEAT RISK — Stay hydrated, avoid direct sun"
    elif temp > 35:
        return "🟡 WARM — Drink water regularly"
    return "🟢 NORMAL — Temperature is comfortable"

def detect_humidity_risk(humidity: int) -> str:
    if humidity > 80:
        return "🔴 HIGH MOISTURE ALERT — Risk of mold, heat stress"
    elif humidity > 60:
        return "🟡 ELEVATED — Monitor for discomfort"
    return "🟢 NORMAL — Humidity is comfortable"

def compute_overall_status(aqi: int, temp: float, humidity: int) -> str:
    if aqi > 150 or temp > 40 or humidity > 80:
        return "UNSAFE"
    elif aqi > 100 or temp > 35 or humidity > 60:
        return "CAUTION"
    return "SAFE"

# ── Pathway-style streaming engine ───────────────────────────────────

class PathwaySimulator:
    """
    Pure-Python simulation of Pathway's streaming engine.
    Works on Windows + any Python version.

    Pathway equivalent:
        sensor_stream = pw.io.jsonlines.read(INPUT_FILE, schema=..., mode="streaming")
        enriched = sensor_stream.select(...)
        pw.io.jsonlines.write(enriched, OUTPUT_FILE)
        pw.run()
    """

    def __init__(self, input_file, output_file, poll_interval=0.5):
        self.input_file    = input_file
        self.output_file   = output_file
        self.poll_interval = poll_interval
        self._file_offset  = 0  # Kafka-style offset — tracks read position

        if os.path.exists(self.output_file):
            os.remove(self.output_file)

        print("⚡ Streaming Pipeline STARTED  [Pathway-compatible mode]")
        print(f"📥 Watching : {self.input_file}")
        print(f"📤 Writing  : {self.output_file}")
        print(f"🔄 Poll rate : every {self.poll_interval}s\n")

    def _transform_row(self, row: dict) -> dict:
        """Equivalent to Pathway's .select() + pw.apply() calls."""
        aqi   = int(row.get("aqi", 0))
        temp  = float(row.get("temperature_c", 0))
        humid = int(row.get("humidity_pct", 0))
        return {
            "timestamp":       row.get("timestamp", ""),
            "sensor_id":       row.get("sensor_id", "UNKNOWN"),
            "aqi":             aqi,
            "temperature_c":   temp,
            "humidity_pct":    humid,
            "aqi_status":      detect_aqi_risk(aqi),
            "temp_status":     detect_temp_risk(temp),
            "humidity_status": detect_humidity_risk(humid),
            "overall_status":  compute_overall_status(aqi, temp, humid),
        }

    def run(self):
        """Equivalent to pw.run() — runs the streaming event loop forever."""
        row_count = 0
        while True:
            if not os.path.exists(self.input_file):
                print(f"⏳ Waiting for {self.input_file} ...")
                time.sleep(1)
                continue

            with open(self.input_file, "r", encoding="utf-8") as f:
                f.seek(self._file_offset)
                new_lines = f.readlines()
                self._file_offset = f.tell()

            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw_row   = json.loads(line)
                    enriched  = self._transform_row(raw_row)
                    row_count += 1

                    with open(self.output_file, "a", encoding="utf-8") as out:
                        out.write(json.dumps(enriched) + "\n")

                    icon = {"SAFE": "🟢", "CAUTION": "🟡", "UNSAFE": "🔴"}.get(enriched["overall_status"], "⚪")
                    print(f"[{row_count:04d}] {icon} {enriched['overall_status']:<7} | "
                          f"AQI={enriched['aqi']:>3} | "
                          f"Temp={enriched['temperature_c']:>4}°C | "
                          f"Humidity={enriched['humidity_pct']:>2}%")

                except json.JSONDecodeError as e:
                    print(f"⚠️  Skipped malformed line: {e}")

            time.sleep(self.poll_interval)


def run_pipeline():
    engine = PathwaySimulator(INPUT_FILE, OUTPUT_FILE, poll_interval=0.5)
    engine.run()


# ── REAL PATHWAY CODE (Linux/Mac + Python 3.10-3.12 only) ────────────
# Uncomment and replace run_pipeline() call below to use native Pathway:
#
# import pathway as pw
#
# class SensorSchema(pw.Schema):
#     timestamp:     str
#     aqi:           int
#     temperature_c: float
#     humidity_pct:  int
#     sensor_id:     str
#
# def run_pipeline():
#     sensor_stream = pw.io.jsonlines.read(
#         INPUT_FILE, schema=SensorSchema,
#         mode="streaming", autocommit_duration_ms=500
#     )
#     enriched = sensor_stream.select(
#         timestamp        = sensor_stream.timestamp,
#         aqi              = sensor_stream.aqi,
#         temperature_c    = sensor_stream.temperature_c,
#         humidity_pct     = sensor_stream.humidity_pct,
#         sensor_id        = sensor_stream.sensor_id,
#         aqi_status       = pw.apply(detect_aqi_risk,      sensor_stream.aqi),
#         temp_status      = pw.apply(detect_temp_risk,     sensor_stream.temperature_c),
#         humidity_status  = pw.apply(detect_humidity_risk, sensor_stream.humidity_pct),
#         overall_status   = pw.apply(compute_overall_status,
#                                     sensor_stream.aqi,
#                                     sensor_stream.temperature_c,
#                                     sensor_stream.humidity_pct),
#     )
#     pw.io.jsonlines.write(enriched, OUTPUT_FILE)
#     pw.run()

if __name__ == "__main__":
    run_pipeline()
