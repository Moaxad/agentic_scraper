def find_suitable_task(tasks, user_request: str):
    for task in tasks:
        if user_request.lower() in task.get("name", "").lower():
            return task
    return None
