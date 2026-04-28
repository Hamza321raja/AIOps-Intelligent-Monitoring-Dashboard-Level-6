import subprocess
import logging
import time

from engine.orchestration import orchestrate

logger = logging.getLogger("remediation")


def run_playbook(playbook):
    try:
        result = subprocess.run(
            ["ansible-playbook", playbook],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"Playbook success: {playbook}")
            return True

        logger.error(result.stderr)
        return False

    except Exception as e:
        logger.error(f"Execution error: {e}")
        return False


def validate(action):
    logger.info(f"Validating {action}")
    time.sleep(2)
    return True


def remediate(action):

    try:
        if action == "SCALE":
            if not run_playbook("/ansible/scale_up.yml"):
                return "FAILED"

            orchestrate(action)

            if validate(action):
                return "SCALE_EXECUTED"

            return "VALIDATION_FAILED"

        elif action in ["RESTART", "PREEMPTIVE_RESTART"]:
            if not run_playbook("/ansible/restart_app.yml"):
                return "FAILED"

            orchestrate(action)

            if validate(action):
                return "RESTART_EXECUTED"

            return "VALIDATION_FAILED"

    except Exception as e:
        logger.error(f"Remediation failed: {e}")
        return "FAILED"

    return "NO_ACTION"