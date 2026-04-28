import requests
import logging
import time

from config import AIRFLOW_URL, RUNDECK_URL

logger = logging.getLogger("orchestration")


# ===============================
# 🔹 GENERIC REQUEST HANDLER
# ===============================
def safe_post(url, payload=None, retries=2):

    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=5)

            if r.status_code in [200, 201]:
                return True, r.text

            logger.warning(f"HTTP {r.status_code}: {r.text}")

        except Exception as e:
            logger.error(f"Request error: {e}")

        time.sleep(1)

    return False, None


# ===============================
# 🔹 AIRFLOW ORCHESTRATION
# ===============================
def trigger_airflow(action):

    payload = {
        "conf": {
            "action": action
        }
    }

    success, res = safe_post(
        f"{AIRFLOW_URL}/api/v1/dags/aiops_remediation/dagRuns",
        payload
    )

    if success:
        logger.info("Airflow triggered successfully")
        return "AIRFLOW_TRIGGERED"

    return "AIRFLOW_FAILED"


# ===============================
# 🔹 RUNDECK ORCHESTRATION
# ===============================
def trigger_rundeck(action):

    payload = {
        "argString": f"-action {action}"
    }

    success, res = safe_post(
        f"{RUNDECK_URL}/api/41/job/aiops/run",
        payload
    )

    if success:
        logger.info("Rundeck triggered successfully")
        return "RUNDECK_TRIGGERED"

    return "RUNDECK_FAILED"


# ===============================
# 🔹 MAIN ORCHESTRATOR
# ===============================
def orchestrate(action):

    # 🔥 smart routing
    if action in ["RESTART", "PREEMPTIVE_RESTART"]:
        return trigger_rundeck(action)

    if action == "SCALE":
        return trigger_airflow(action)

    return "NO_ORCHESTRATION"