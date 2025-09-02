from scrapestorm_client import list_tasks, create_task
from ai_agent import ask_ai
from utils import find_suitable_task

def run_agent(user_request: str):
    print(f"🔍 Checking tasks for: {user_request}")
    tasks = list_tasks()
    task = find_suitable_task(tasks, user_request)

    if task:
        print(f"✅ Found existing task: {task['name']}")
        return task

    print("No suitable task found. Asking AI...")
    ai_result = ask_ai(user_request)

    if not ai_result["url"]:
        print("AI failed to suggest URL.")
        return None

    print(f"⚡ Creating new task for {ai_result['url']}")
    new_task = create_task(user_request, ai_result["url"], ai_result["fields"])
    print(f"Created task: {new_task['id']}")
    return new_task

if __name__ == "__main__":
    user_request = "Scrape latest laptops from Amazon"
    run_agent(user_request)
