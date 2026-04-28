import os

# ===============================
# 🔹 PROMETHEUS
# ===============================
PROM_URL = os.getenv(
    "PROM_URL",
    "http://prometheus:9090/api/v1/query"
)

PROM_WINDOW = os.getenv("PROM_WINDOW", "10s")

# ===============================
# 🔹 ML SETTINGS
# ===============================
ANOMALY_CONTAMINATION = float(
    os.getenv("ANOMALY_CONTAMINATION", 0.1)
)

MIN_TRAINING_SAMPLES = int(
    os.getenv("MIN_TRAINING_SAMPLES", 20)
)

ZERO_ACTIVITY_THRESHOLD = float(
    os.getenv("ZERO_ACTIVITY_THRESHOLD", 0.05)
)

# ===============================
# 🔹 ALERTING
# ===============================
ALERT_COOLDOWN = int(
    os.getenv("ALERT_COOLDOWN", 60)
)

# ===============================
# 🔹 AUTOMATION
# ===============================
ANSIBLE_PATH = os.getenv(
    "ANSIBLE_PATH",
    "/ansible"
)

AIRFLOW_URL = os.getenv(
    "AIRFLOW_URL",
    "http://airflow:8080"
)

RUNDECK_URL = os.getenv(
    "RUNDECK_URL",
    "http://rundeck:4440"
)

ENABLE_RUNDECK = os.getenv("ENABLE_RUNDECK", "false").lower() == "true"
ENABLE_AIRFLOW = os.getenv("ENABLE_AIRFLOW", "true").lower() == "true"

# ===============================
# 🔹 MLFLOW
# ===============================
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://mlflow:5000"
)

# ===============================
# 🔹 SPARK
# ===============================
SPARK_MODE = os.getenv(
    "SPARK_MODE",
    "local"
)

# ===============================
# 🔹 LOGGING
# ===============================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

LOG_PATH = os.getenv(
    "LOG_PATH",
    "/app/logs/aiops.log"
)

# ===============================
# 🔹 ENGINE
# ===============================
LOOP_INTERVAL = int(
    os.getenv("LOOP_INTERVAL", 5)
)

# ===============================
# 🔹 SLA
# ===============================
SLA = {
    "cpu": float(os.getenv("SLA_CPU", 80)),
    "latency": float(os.getenv("SLA_LATENCY", 2)),
    "errors": int(os.getenv("SLA_ERRORS", 5))
}