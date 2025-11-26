from datetime import datetime, date

def urgency_score(due_date: str) -> float:
    today = date.today()
    due = datetime.strptime(due_date, "%Y-%m-%d").date()
    days_left = (due - today).days

    if days_left < 0:
        return 10
    elif days_left == 0:
        return 9
    elif days_left <= 3:
        return 8
    elif days_left <= 7:
        return 6
    elif days_left <= 14:
        return 4
    else:
        return 2

def importance_score(value: int) -> float:
    return max(1, min(10, value))

def effort_score(hours: float) -> float:
    if hours <= 1:
        return 9
    elif hours <= 3:
        return 7
    elif hours <= 6:
        return 5
    else:
        return 3

def final_priority(task: dict) -> dict:
    u = urgency_score(task["due_date"])
    i = importance_score(task["importance"])
    e = effort_score(task["hours"])
    final = (u + i + e) / 3
    return {
        "urgency": u,
        "importance": i,
        "effort": e,
        "final_score": round(final, 2)
    }

task = {
    "title": "Submit Assignment",
    "due_date": "2025-12-01",
    "importance": 8,
    "hours": 2
}

print(final_priority(task))
