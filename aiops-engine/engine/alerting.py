import time

alerts = {}

def intelligent_alert(x, anomaly, score, rca=None):
    now = time.time()

    cpu, latency, requests = x

    # ===============================
    # 🔹 CORRELATED ALERT LOGIC
    # ===============================
    if anomaly:

        # 🔴 CRITICAL CONDITION (multi-metric)
        if cpu > 75 and latency > 1:
            level = "CRITICAL"
            reason = "High CPU and Latency Spike"

        # 🟠 WARNING CONDITION
        elif cpu > 60 or latency > 0.8:
            level = "WARNING"
            reason = "Resource stress detected"

        else:
            level = "INFO"
            reason = "Minor anomaly"

    else:
        return None

    # ===============================
    # 🔹 DEDUPLICATION (SMART)
    # ===============================
    key = f"{level}:{reason}"

    if key in alerts and now - alerts[key] < 60:
        return None

    alerts[key] = now

    # ===============================
    # 🔹 ALERT OUTPUT (RICH CONTEXT)
    # ===============================
    return {
        "level": level,
        "reason": reason,
        "cpu": round(cpu, 2),
        "latency": round(latency, 2),
        "requests": round(requests, 2),
        "score": round(score, 4),
        "rca": rca,
        "timestamp": now
    }