import requests
from config import SCRAPESTORM_API_KEY, SCRAPESTORM_BASE_URL


def list_tasks():
    r = requests.get(f"{SCRAPESTORM_BASE_URL}/tasks")
    r.raise_for_status()
    return r.json()

def create_task(name: str, url: str, fields: list):
    payload = {
        "name": name,
        "start_url": url,
        "max_records": 100  # default limit to prevent runaway scraping
    }
    r = requests.post(f"{SCRAPESTORM_BASE_URL}/tasks", json=payload)
    r.raise_for_status()
    return r.json()
