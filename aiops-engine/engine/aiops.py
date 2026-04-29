import os
import time
import json
import requests
import numpy as np
import logging

from engine.ml import detect, train, pattern, predict_failure
from engine.rca import ai_rca, learn_incident
from engine.alerting import intelligent_alert
from engine.capacity import predict_capacity
from engine.remediation import remediate
from engine.runbook import runbook

from config import PROM_URL, LOOP_INTERVAL

LOKI_URL = "http://loki:3100/loki/api/v1/query"

# ===============================
# 🔹 LOGGING
# ===============================
LOG_PATH = "/app/logs/aiops.log"
os.makedirs("/app/logs", exist_ok=True)

logger = logging.getLogger("aiops")
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

file_handler = logging.FileHandler(LOG_PATH)
stream_handler = logging.StreamHandler()

formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.propagate = False

logger.info("🔥 AIOps logging initialized")

# ===============================
# 🔹 SLA
# ===============================
total_requests = 0
successful_requests = 0

def calculate_sla():
    if total_requests == 0:
        return 100.0
    return round((successful_requests / total_requests) * 100, 2)

# ===============================
# 🔹 CONTROL
# ===============================
last_action_time = 0
last_decision = None
ACTION_COOLDOWN = 30

# ===============================
# 🔹 SAFE JSON
# ===============================
def convert(obj):
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return str(obj)

# ===============================
# 🔹 PROM METRICS
# ===============================
def metric(q):
    try:
        r = requests.get(PROM_URL, params={"query": q}, timeout=3)
        res = r.json().get("data", {}).get("result", [])
        if res:
            return float(res[0]["value"][1])
        return 0.0
    except Exception as e:
        logger.error(f"Metric error: {e}")
        return 0.0

# ===============================
# 🔥 LOKI ERROR RATE
# ===============================
def get_error_rate():
    try:
        query = 'count_over_time({job="aiops-engine"} |= "error" [1m])'
        r = requests.get(LOKI_URL, params={"query": query}, timeout=3)
        res = r.json().get("data", {}).get("result", [])

        if res:
            return float(res[0]["value"][1])
        return 0.0
    except Exception as e:
        logger.error(f"Loki error: {e}")
        return 0.0

# ===============================
# 🔥 TRACE LATENCY (SIMULATED)
# ===============================
def get_trace_latency():
    try:
        base = metric('rate(http_request_duration_seconds_sum[10s])')
        return base * 1.2
    except:
        return 0.0

# ===============================
# 🔹 DATA COLLECTION
# ===============================
def collect():
    return np.array([
        metric('rate(process_cpu_seconds_total[10s]) * 100'),
        metric('rate(http_request_duration_seconds_sum[10s])'),
        metric('rate(http_requests_total[10s])'),
        get_error_rate(),
        get_trace_latency()
    ])

# ===============================
# 🔹 DECISION ENGINE
# ===============================
def intelligent_decision(x, anomaly, failure, capacity, rca):

    cpu, latency, requests, error_rate, trace = x

    if rca == "SERVICE_DOWN":
        return "RESTART"

    if failure == "HIGH_RISK":
        return "PREEMPTIVE_RESTART"

    if error_rate > 10:
        return "RESTART"

    if anomaly:
        if cpu > 70 and latency > 1:
            return "SCALE"
        if cpu > 80:
            return "RESTART"
        if capacity == "SCALE_UP":
            return "SCALE"

    return "NO_ACTION"

# ===============================
# 🔹 MAIN LOOP
# ===============================
def run():
    global total_requests, successful_requests
    global last_action_time, last_decision

    logger.info("🚀 AIOps Engine Running")

    while True:
        try:
            x = collect()

            # Prevent invalid data crash
            if len(x) != 5:
                logger.warning(f"Invalid data shape: {x}")
                time.sleep(LOOP_INTERVAL)
                continue

            anomaly, score = detect(x)
            train()

            p = pattern(x)
            failure = predict_failure(x)

            capacity_info = predict_capacity()
            capacity = capacity_info.get("status", "UNKNOWN") if isinstance(capacity_info, dict) else "UNKNOWN"

            rca = ai_rca(x)

            # SLA
            total_requests += 1
            if not anomaly:
                successful_requests += 1
            sla = calculate_sla()

            alert = intelligent_alert(x, anomaly, score, rca)

            decision = intelligent_decision(x, anomaly, failure, capacity, rca)

            steps = runbook(decision, rca)

            current_time = time.time()

            if decision != "NO_ACTION":
                if decision == last_decision:
                    action = "SKIPPED_DUPLICATE"
                elif current_time - last_action_time < ACTION_COOLDOWN:
                    action = "SKIPPED_COOLDOWN"
                else:
                    action = remediate(decision)
                    last_action_time = current_time
                    last_decision = decision
            else:
                action = "NO_ACTION"

            if anomaly:
                learn_incident(x, decision)

            log_data = {
                "type": "aiops_event",
                "cpu": x[0],
                "latency": x[1],
                "requests": x[2],
                "error_rate": x[3],
                "trace_latency": x[4],
                "anomaly": anomaly,
                "pattern": p,
                "failure": failure,
                "capacity": capacity_info,
                "rca": rca,
                "decision": decision,
                "action": action,
                "sla": sla
            }

            logger.info(json.dumps(log_data, default=convert))

        except Exception as e:
            logger.error(f"Engine loop error: {e}")

        time.sleep(LOOP_INTERVAL)