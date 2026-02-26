@ -0,0 +1,160 @@
# 🌍 Real-Time Environmental Monitoring System
> **Hackathon-Ready** | Python + Pathway Streaming + Streamlit Dashboard

---

## 🗂️ Project Structure

```
project/
 ├── data_stream.py          ← Simulates sensor data (Kafka Producer equivalent)
 ├── monitoring_pipeline.py  ← Pathway streaming pipeline (core logic)
 ├── dashboard.py            ← Live Streamlit dashboard
 ├── requirements.txt        ← All dependencies
 └── README.md               ← You are here!

# Auto-generated at runtime:
 ├── sensor_data.jsonl       ← Raw sensor readings (stream input)
 └── processed_data.jsonl    ← Enriched data with alerts (stream output)
```

---

## 🚀 Quick Start (3 Terminals)

### Step 1 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Terminal 1: Start the Data Generator
```bash
python data_stream.py
```
You'll see sensor readings printing every 2 seconds. Leave this running.

### Step 3 — Terminal 2: Start the Pathway Pipeline
```bash
python monitoring_pipeline.py
```
Pathway watches the data file and processes each new reading in real-time.

### Step 4 — Terminal 3: Launch the Dashboard
```bash
streamlit run dashboard.py
```
Opens automatically at **http://localhost:8501** — refreshes every 3 seconds!

---

## 🔍 Risk Detection Rules

| Metric      | Threshold | Status              | Safety Advice                        |
|-------------|-----------|---------------------|--------------------------------------|
| AQI         | > 150     | 🔴 Unsafe Air       | Avoid outdoor activity               |
| AQI         | > 100     | 🟡 Moderate         | Sensitive groups be cautious         |
| AQI         | ≤ 100     | 🟢 Good             | Air quality is safe                  |
| Temperature | > 40°C    | 🔴 Heat Risk        | Stay hydrated, avoid direct sun      |
| Temperature | > 35°C    | 🟡 Warm             | Drink water regularly                |
| Temperature | ≤ 35°C    | 🟢 Normal           | Temperature is comfortable           |
| Humidity    | > 80%     | 🔴 High Moisture    | Risk of mold, heat stress            |
| Humidity    | > 60%     | 🟡 Elevated         | Monitor for discomfort               |
| Humidity    | ≤ 60%     | 🟢 Normal           | Humidity is comfortable              |

---

## ⚡ How Pathway Handles Streaming

Pathway treats data as a **live, continuously-updating table** — not a static file.

```
Traditional Batch:   Read file → Process ALL rows → Write output (one-shot)
Pathway Streaming:   Watch file → Process EACH NEW ROW instantly → Update output (continuous)
```

**Under the hood, Pathway:**
1. Opens the input file in *streaming mode*
2. Watches for new lines appended to the file
3. Triggers your transformation logic on each new row within milliseconds
4. Emits the enriched result to the output sink immediately
5. Keeps running forever — it never "finishes"

This is the same model used by Apache Kafka consumers.

---

## 🔗 Where Apache Kafka Fits

This project uses **files** to simulate the Kafka messaging pattern:

```
[data_stream.py]  →  sensor_data.jsonl  →  [Pathway]  →  processed_data.jsonl
  (Producer)           (Kafka Topic)        (Consumer)     (Output Topic)
```

**To upgrade to real Kafka** (minimal code change):

```python
# In monitoring_pipeline.py, replace:
sensor_stream = pw.io.jsonlines.read(INPUT_FILE, schema=SensorSchema, mode="streaming")

# With:
rdkafka_settings = {
    "bootstrap.servers": "localhost:9092",
    "group.id":          "env-monitor-group",
    "auto.offset.reset": "latest",
}
sensor_stream = pw.io.kafka.read(
    rdkafka_settings,
    topic="env-sensors",
    schema=SensorSchema,
    format="json"
)
```

**Full Apache Ecosystem Integration:**

| Component        | Role in This System                          |
|------------------|----------------------------------------------|
| Apache Kafka     | Message bus — replaces JSONL file transport  |
| Apache Flink     | Alternative stream processor to Pathway      |
| Apache Spark     | Batch analytics on historical sensor data    |
| Apache Airflow   | Schedule batch report generation             |
| Apache HBase     | Store long-term sensor history at scale      |

---

## 🧩 Extending This Project

**Add a new sensor metric** (e.g., CO₂):
1. In `data_stream.py` → add `"co2_ppm": random.randint(400, 2000)` to the reading dict
2. In `monitoring_pipeline.py` → add `co2_ppm: int` to `SensorSchema` and a new detect function
3. In `dashboard.py` → add a new `st.metric(...)` column

**Add email alerts:**
```python
import smtplib
if overall_status == "UNSAFE":
    # send_email_alert(...)
```

**Switch to a real database output:**
```python
# Replace pw.io.jsonlines.write with:
pw.io.postgres.write(enriched, connection_string="postgresql://...")
```

---

## 📸 Dashboard Features

- ✅ Auto-refreshes every 3 seconds
- 📊 Live trend charts for all 3 metrics
- 🚨 Color-coded alert banners (🔴🟡🟢)
- 📡 Multi-sensor support (SENSOR_A/B/C)
- 📋 Raw data table (expandable)
- ⚡ Pathway architecture explanation built-in

---

*Built for hackathons — extend freely!*
