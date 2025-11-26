from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .scoring import TaskScorer


def _normalize_tasks(raw_tasks):
    """
    Ensure each task has a stable identifier and expected keys.
    Operates defensively: missing fields are handled later by TaskScorer.
    """
    normalized = []
    for idx, task in enumerate(raw_tasks):
        if not isinstance(task, dict):
            # Skip completely invalid entries
            continue

        task_copy = task.copy()

        # Ensure an id exists so dependency graphs are stable
        if "id" not in task_copy:
            task_copy["id"] = idx + 1

        # Default shape – values can still be None/invalid and are handled by scorer
        task_copy.setdefault("title", f"Task {task_copy['id']}")
        task_copy.setdefault("due_date", None)
        task_copy.setdefault("estimated_hours", None)
        task_copy.setdefault("importance", None)
        task_copy.setdefault("dependencies", [])

        # Normalise dependencies to a list
        deps = task_copy.get("dependencies") or []
        if not isinstance(deps, list):
            deps = [deps]
        task_copy["dependencies"] = deps

        normalized.append(task_copy)
    return normalized


@api_view(["POST"])
def analyze_tasks(request):
    """
    Analyze and sort tasks by priority.

    Expected payload:
    {
        "tasks": [ { ...task fields... } ],
        "strategy": "smart_balance" | "fastest_wins" | "high_impact" | "deadline_driven"
    }
    """
    try:
        raw_tasks = request.data.get("tasks", [])
        strategy = request.data.get("strategy", "smart_balance")

        if not isinstance(raw_tasks, list) or not raw_tasks:
            return Response({"error": "No tasks provided"}, status=status.HTTP_400_BAD_REQUEST)

        scorer = TaskScorer(strategy=strategy)
        tasks = _normalize_tasks(raw_tasks)

        # Detect circular dependencies
        cycles = scorer.detect_circular_dependencies(tasks)

        scored_tasks = []
        for task in tasks:
            score_data = scorer.score_task(task, tasks)
            explanation = scorer.generate_explanation(task, score_data)

            enriched = task.copy()
            enriched["priority_score"] = score_data.get("score")
            enriched["score_components"] = score_data.get("components")
            enriched["explanation"] = explanation

            scored_tasks.append(enriched)

        # Sort by score descending
        scored_tasks.sort(key=lambda t: (t.get("priority_score") or 0), reverse=True)

        return Response(
            {
                "strategy": strategy,
                "tasks": scored_tasks,
                "circular_dependencies": [list(c) for c in cycles],
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        return Response(
            {"error": "Failed to analyze tasks", "details": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def suggest_tasks(request):
    """
    Suggest top 3 tasks to work on today.

    Query params:
        strategy: optional strategy name (defaults to smart_balance)
    Body (optional for flexibility in local usage):
        { "tasks": [...] }
    """
    try:
        # Allow both GET-with-body (for convenience) and query-only.
        raw_tasks = request.data.get("tasks") or request.query_params.get("tasks")
        strategy = request.query_params.get("strategy", "smart_balance")

        if not raw_tasks:
            return Response(
                {
                    "top_tasks": [],
                    "message": "No tasks provided – please analyze tasks first or provide a task list.",
                },
                status=status.HTTP_200_OK,
            )

        if isinstance(raw_tasks, str):
            # If tasks are passed as JSON string via query param
            import json

            raw_tasks = json.loads(raw_tasks)

        if not isinstance(raw_tasks, list):
            return Response(
                {"error": "Invalid tasks format – expected a list of tasks."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scorer = TaskScorer(strategy=strategy)
        tasks = _normalize_tasks(raw_tasks)

        scored = []
        for task in tasks:
            score_data = scorer.score_task(task, tasks)
            explanation = scorer.generate_explanation(task, score_data)
            enriched = task.copy()
            enriched["priority_score"] = score_data.get("score")
            enriched["score_components"] = score_data.get("components")
            enriched["explanation"] = explanation
            scored.append(enriched)

        scored.sort(key=lambda t: (t.get("priority_score") or 0), reverse=True)
        top_tasks = scored[:3]

        return Response(
            {
                "strategy": strategy,
                "top_tasks": top_tasks,
                "count": len(top_tasks),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        return Response(
            {"error": "Failed to suggest tasks", "details": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def health_check(request):
    """Simple health-check endpoint for smoke tests."""
    return Response({"status": "ok"}, status=status.HTTP_200_OK)
