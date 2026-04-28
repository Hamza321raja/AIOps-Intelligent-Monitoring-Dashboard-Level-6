import logging

logger = logging.getLogger("runbook")


def runbook(action, rca=None):

    if action == "SCALE":
        steps = [
            "analyze_load",
            "scale_resources",
            "verify_performance"
        ]

    elif action in ["RESTART", "PREEMPTIVE_RESTART"]:
        steps = [
            "inspect_service",
            "restart_service",
            "validate_health"
        ]

    else:
        steps = ["monitor"]

    # RCA-based enhancement
    if rca == "CPU_BOTTLENECK":
        steps.insert(1, "check_cpu_usage")

    if rca == "TRAFFIC_SPIKE":
        steps.append("enable_auto_scaling")

    for step in steps:
        logger.info(f"[RUNBOOK] {step}")

    return steps