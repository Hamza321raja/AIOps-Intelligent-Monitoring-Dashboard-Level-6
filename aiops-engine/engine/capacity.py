import numpy as np
from engine.ml import history


def predict_capacity():

    # ===============================
    # 🔹 REQUIRE MINIMUM DATA
    # ===============================
    if len(history) < 20:
        return {
            "status": "UNKNOWN",
            "reason": "Not enough data"
        }

    # ===============================
    # 🔹 EXTRACT METRICS
    # ===============================
    cpu = np.array([x[0] for x in history])
    latency = np.array([x[1] for x in history])
    requests = np.array([x[2] for x in history])

    time_idx = np.arange(len(cpu))

    # ===============================
    # 🔹 TREND ANALYSIS
    # ===============================
    cpu_trend = np.polyfit(time_idx, cpu, 1)[0]
    req_trend = np.polyfit(time_idx, requests, 1)[0]

    # ===============================
    # 🔹 FORECAST (NEXT WINDOW)
    # ===============================
    forecast_cpu = cpu[-1] + cpu_trend * 5   # next 5 intervals
    forecast_req = requests[-1] + req_trend * 5

    # ===============================
    # 🔹 DECISION LOGIC
    # ===============================
    if forecast_cpu > 80 or forecast_req > 300:
        return {
            "status": "SCALE_UP",
            "forecast_cpu": round(forecast_cpu, 2),
            "forecast_requests": round(forecast_req, 2),
            "recommendation": "Increase replicas"
        }

    if forecast_cpu < 30 and forecast_req < 50:
        return {
            "status": "SCALE_DOWN",
            "forecast_cpu": round(forecast_cpu, 2),
            "forecast_requests": round(forecast_req, 2),
            "recommendation": "Reduce resources"
        }

    return {
        "status": "STABLE",
        "forecast_cpu": round(forecast_cpu, 2),
        "forecast_requests": round(forecast_req, 2),
        "recommendation": "No scaling required"
    }