# DRAFT file: not part of main app, used for testing task creation logic

import os
import time
import json
import logging
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv
from googlesearch import search

# Replace with actual Groq client library import if different
# Example used earlier: from groq import Groq
try:
    from groq import Groq
except Exception:
    Groq = None  # We'll guard for missing client

# ---- Config / env ----
load_dotenv()

# ---- Logging ----
LOG_PATH = os.getenv("LOG_PATH", "logs/agentic_scraper.log")
os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
)
logger = logging.getLogger("agentic_scraper")


# ---- Groq LLM wrapper ----
class GroqLLM:
    def __init__(self, api_key: str, model: str):
        if Groq is None:
            raise RuntimeError("Groq client library not installed or import failed.")
        self.client = Groq(api_key=api_key)
        self.model = model

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        """
        messages: [{"role": "user", "content": "..."}]
        Returns the assistant text
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        # depends on actual response shape; adapt if different
        try:
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.exception("Unexpected Groq response shape")
            raise


# ---- ScrapeStorm helpers ----
def _headers():
    headers = {"Content-Type": "application/json"}
    return headers


def list_tasks() -> List[Dict[str, Any]]:
    try:
        r = requests.get(f"{SCRAPESTORM_BASE}/task/list", headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        logger.exception("Failed to list tasks")
        return []


def create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal wrapper - adapt payload shape to your ScrapeStorm instance.
    Pass 'name' and 'url' at least. You can include more fields to configure pagination etc.
    """
    try:
        r = requests.post(f"{SCRAPESTORM_BASE}/task/create", headers=_headers(), json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        logger.exception("Failed to create task")
        raise


def start_task(task_id: str) -> Dict[str, Any]:
    try:
        r = requests.post(f"{SCRAPESTORM_BASE}/task/start/{task_id}", headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        logger.exception("Failed to start task")
        raise


def stop_task(task_id: str) -> Dict[str, Any]:
    try:
        r = requests.post(f"{SCRAPESTORM_BASE}/task/stop/{task_id}", headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        logger.exception("Failed to stop task")
        return {}


def get_task_results(task_id: str, page: int = 1, size: int = 20) -> List[Dict[str, Any]]:
    try:
        params = {"page": page, "size": size}
        r = requests.get(f"{SCRAPESTORM_BASE}/task/result/{task_id}", headers=_headers(), params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        logger.exception("Failed to fetch task results")
        return []


# ---- Agent behaviors ----
def ask_llm_to_build_query(llm: GroqLLM, goal: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    history_json = json.dumps(history or [], ensure_ascii=False)[:2000]  # keep short
    prompt = (
        f"Goal: {goal}\n"
        f"Past attempts (trimmed): {history_json}\n"
        "Return a short focused web search query (one line). If the goal is already complete, return only: DONE"
    )
    return llm.chat([{"role": "user", "content": prompt}])


def ask_llm_pick_url(llm: GroqLLM, goal: str, candidates: List[str]) -> str:
    prompt = (
        f"Goal: {goal}\n"
        f"Here are candidate URLs:\n" + "\n".join(candidates) + "\n\n"
        "Return exactly one URL (the best candidate for scraping)."
    )
    return llm.chat([{"role": "user", "content": prompt}])


def ask_llm_task_name(llm: GroqLLM, goal: str) -> str:
    prompt = (
        f"User request: {goal}\n"
        "Return a short snake_case task name suitable for this scraping job (no spaces)."
    )
    return llm.chat([{"role": "user", "content": prompt}])


def ask_llm_task_payload(llm: GroqLLM, goal: str, chosen_url: str) -> Dict[str, Any]:
    """
    Use LLM to propose a minimal task payload.
    You should review this payload before using in production.
    """
    prompt = (
        f"User request: {goal}\n"
        f"Chosen URL: {chosen_url}\n"
        "Propose a JSON object with at least 'name' and 'url' to create a ScrapeStorm task. "
        "Include common sensible defaults for pagination and list item selection if possible. "
        "Return ONLY valid JSON."
    )
    text = llm.chat([{"role": "user", "content": prompt}], temperature=0.0)
    # LLM should return JSON; safe-guard parsing
    try:
        payload = json.loads(text)
        return payload
    except Exception:
        logger.warning("LLM returned non-JSON payload; falling back to minimal payload.")
        # fallback
        return {"name": ask_llm_task_name(llm, goal), "url": chosen_url}


def ask_llm_extract_schema(llm: GroqLLM, items: List[Dict[str, Any]], schema_example: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Provide the LLM raw text/records and ask for normalized JSON according to a schema_example
    schema_example: e.g. {"name":"", "price":"", "status":"", "mileage":"", "description":""}
    """
    # Keep sample size bounded (LLM token limits)
    items_snippet = json.dumps(items[:50], ensure_ascii=False)  # limit to first 50 items
    prompt = (
        f"I have raw scraped records: {items_snippet}\n\n"
        f"Normalize these into a JSON array of objects using this schema: {json.dumps(schema_example, ensure_ascii=False)}.\n"
        "Return valid JSON only (an array)."
    )
    text = llm.chat([{"role": "user", "content": prompt}], temperature=0.0)
    try:
        normalized = json.loads(text)
        # Ensure list of dicts
        if isinstance(normalized, list):
            return normalized
        else:
            logger.warning("Normalized payload not a list; wrapping into list.")
            return [normalized]
    except Exception:
        logger.exception("Failed to parse LLM normalized JSON.")
        return []


# ---- Top-level orchestrator ----
def agentic_scrape(
    goal: str,
    record_limit: int = DEFAULT_RECORD_LIMIT,
    page_size: int = 20,
    llm: Optional[GroqLLM] = None
) -> List[Dict[str, Any]]:
    if not llm:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY env var not set.")
        llm = GroqLLM(api_key=GROQ_API_KEY, model=GROQ_MODEL)

    logger.info("Agent started for goal: %s", goal)

    history = []
    # 1) Ask LLM for search query
    query = ask_llm_to_build_query(llm, goal, history)
    if query.strip().upper() == "DONE":
        logger.info("LLM declared goal completed: DONE")
        return []

    logger.info("LLM search query: %s", query)

    # 2) Perform web search (googlesearch)
    candidates = []
    try:
        candidates = list(search(query, num_results=10, unique=True, lang=SEARCH_LANG))
    except Exception:
        logger.exception("Search failed; proceeding with empty candidate list.")

    if not candidates:
        logger.warning("No candidates found by search; ask LLM for a direct URL")
        # fallback: ask LLM for an explicit URL
        chosen_url = llm.chat([{"role": "user", "content": f"User request: {goal}\nProvide the main website URL to scrape."}])
    else:
        # 3) Ask LLM to pick best URL
        chosen_url = ask_llm_pick_url(llm, goal, candidates)

    chosen_url = chosen_url.strip()
    logger.info("Chosen URL: %s", chosen_url)

    # 4) Map to a task name
    task_name = ask_llm_task_name(llm, goal).strip() or f"task_{int(time.time())}"
    logger.info("Task name: %s", task_name)

    # 5) Check for existing task
    tasks = list_tasks()
    existing = None
    for t in tasks:
        try:
            if str(t.get("name", "")).lower() == task_name.lower():
                existing = t
                break
        except Exception:
            continue

    if existing:
        task_id = existing.get("id") or existing.get("_id") or existing.get("task_id")
        logger.info("Using existing task: %s (id=%s)", task_name, task_id)
    else:
        # 6) Ask LLM to propose create payload (or fallback to minimal)
        payload = ask_llm_task_payload(llm, goal, chosen_url)
        # Ensure we have name & url
        payload.setdefault("name", task_name)
        payload.setdefault("url", chosen_url)
        logger.info("Creating new task with payload: %s", json.dumps(payload, ensure_ascii=False))
        created = create_task(payload)
        task_id = created.get("id") or created.get("_id") or created.get("task_id")
        logger.info("Created task id: %s", task_id)

    # 7) Start the task
    start_task(task_id)
    logger.info("Started task id: %s", task_id)

    # 8) Poll results page by page, stop when we reach record_limit
    all_records: List[Dict[str, Any]] = []
    page = 1
    consecutive_empty = 0
    while len(all_records) < record_limit:
        results = get_task_results(task_id, page=page, size=page_size)
        if not results:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                logger.info("No more results after several attempts; breaking.")
                break
            logger.info("No results on page %d; retrying after wait.", page)
            time.sleep(2)
            continue

        consecutive_empty = 0
        # Results shape may be list or object with 'data' field; try to handle both
        if isinstance(results, dict):
            maybe_list = results.get("data") or results.get("records") or results.get("items")
            results_list = maybe_list if isinstance(maybe_list, list) else []
        elif isinstance(results, list):
            results_list = results
        else:
            results_list = []

        logger.info("Fetched %d records on page %d", len(results_list), page)
        all_records.extend(results_list)
        page += 1
        # small backoff
        time.sleep(1)

    # Trim to requested limit
    all_records = all_records[:record_limit]
    logger.info("Collected %d records (limit %d)", len(all_records), record_limit)

    # 9) Optionally stop the ScrapeStorm task to avoid running long jobs (controlled behavior)
    try:
        logger.info("Stopping task id: %s to save resources.", task_id)
        stop_task(task_id)
    except Exception:
        logger.warning("Failed to stop task; ignoring.")

    # 10) Post-process: structured extraction with LLM
    # Example schema: user can provide their own; here's a sample car schema
    schema_example = {"name": "", "price": "", "status": "", "mileage": "", "description": ""}

    normalized = ask_llm_extract_schema(llm, all_records, schema_example)
    logger.info("Normalized records count: %d", len(normalized))

    return normalized


# ---- Example usage ----
if __name__ == "__main__":
    goal_text = "Get the latest Mazda car listings in Saudi Arabia with name, price, status, mileage"
    try:
        if not GROQ_API_KEY:
            raise RuntimeError("Set GROQ_API_KEY in your environment.")
        llm = GroqLLM(api_key=GROQ_API_KEY, model=GROQ_MODEL)
        results = agentic_scrape(goal_text, record_limit=40, llm=llm)
        print("Final normalized results (sample):")
        print(json.dumps(results[:10], indent=2, ensure_ascii=False))
    except Exception as exc:
        logger.exception("Agent failed: %s", exc)
