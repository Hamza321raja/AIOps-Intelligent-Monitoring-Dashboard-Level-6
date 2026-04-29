import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

incident_memory = []


# ===============================
# 🔹 LEARN FROM INCIDENTS
# ===============================
def learn_incident(x, label):
    incident_memory.append((x, label))


# ===============================
# 🔹 RULE-BASED RCA (UPDATED)
# ===============================
def rule_based_rca(x):

    # 🔥 SAFE INDEXING (NO UNPACK ERROR)
    cpu = x[0]
    latency = x[1]
    requests = x[2]
    error_rate = x[3]
    trace = x[4]

    if cpu > 80 and latency > 1:
        return "CPU_BOTTLENECK"

    if latency > 2 and requests > 200:
        return "TRAFFIC_SPIKE"

    if requests == 0:
        return "SERVICE_DOWN"

    if cpu < 10 and latency > 1:
        return "IDLE_BUT_SLOW"

    # 🔥 NEW (ADVANCED RCA)
    if error_rate > 10:
        return "APPLICATION_ERROR"

    if trace > latency * 1.5:
        return "DEPENDENCY_LATENCY"

    return None


# ===============================
# 🔹 MEMORY-BASED RCA
# ===============================
def memory_rca(x):
    if len(incident_memory) < 5:
        return None

    try:
        X = np.array([i[0] for i in incident_memory])
        labels = [i[1] for i in incident_memory]

        sim = cosine_similarity([x], X)[0]
        idx = np.argmax(sim)

        if sim[idx] > 0.8:
            return labels[idx]

    except Exception:
        return None

    return None


# ===============================
# 🔹 FINAL RCA ENGINE
# ===============================
def ai_rca(x):

    # 1. Rule-based RCA
    rule = rule_based_rca(x)
    if rule:
        return rule

    # 2. Memory-based RCA
    mem = memory_rca(x)
    if mem:
        return mem

    return "UNKNOWN"