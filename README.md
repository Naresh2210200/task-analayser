Smart Task Analyzer
===================

Mini application that scores and prioritizes tasks based on urgency, importance, effort, and dependencies.

This repository contains:
- Django backend with a configurable scoring algorithm
- REST API endpoints for analyzing and suggesting tasks
- Vanilla HTML/CSS/JavaScript frontend
- Unit tests for the scoring logic

---

Setup Instructions
------------------

**Prerequisites**
- Python 3.8+
- pip / virtualenv

**1. Create and activate virtual environment (optional but recommended)**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Apply migrations**

```bash
python manage.py migrate
```

**4. Run tests**

```bash
python manage.py test
```

**5. Run the development server**

```bash
python manage.py runserver
```

Backend will be available at `http://127.0.0.1:8000/`.

**6. Open the frontend**

Open `frontend/index.html` directly in your browser, or serve the `frontend/` folder with a simple static server.

---

API Overview
------------

Base URL: `http://127.0.0.1:8000/api/tasks/`

- **POST** `/analyze/`
  - Request body:
    ```json
    {
      "strategy": "smart_balance",
      "tasks": [
        {
          "id": 1,
          "title": "Fix login bug",
          "due_date": "2025-11-30",
          "estimated_hours": 3,
          "importance": 8,
          "dependencies": []
        }
      ]
    }
    ```
  - Response:
    - Sorted tasks with `priority_score`, `score_components`, and `explanation`
    - Any detected `circular_dependencies`

- **GET** `/suggest/`
  - Query params:
    - `strategy` (optional, default: `smart_balance`)
  - Body (optional):
    - `{ "tasks": [ ...same shape as above... ] }`
  - Response:
    - `top_tasks`: up to 3 highest-priority tasks with explanations

---

Algorithm Explanation
---------------------

The core priority logic is implemented in `tasks/scoring.py` via the `TaskScorer` class.  
Each task is scored on four dimensions:

- **Urgency**: derived from days until `due_date`. Overdue tasks receive the highest urgency (capped at 10); tasks due today/tomorrow are very urgent; tasks within 3–14 days get medium urgency; and far-future tasks gradually decay towards 0. Invalid or missing dates receive a neutral urgency of 5.0.
- **Importance**: user-provided `importance` on a 1–10 scale. Values are clamped between 1 and 10; invalid or missing values default to 5.0, ensuring the algorithm is resilient to bad data.
- **Effort**: based on `estimated_hours`, with **lower effort mapping to higher scores** to encourage “quick wins”. Sub‑30‑minute tasks score near 10, while multi‑day tasks drop towards 0. Negative or invalid effort values are handled gracefully and default to a neutral 5.0.
- **Dependencies**: tasks that **block other tasks** are rewarded. The algorithm counts how many tasks list a given task as a dependency and maps that count to a 0–10 range, with more dependents implying higher impact.

These four component scores are then combined into a **weighted final score**.  
Weights depend on the chosen strategy:

- **Smart Balance (default)** – balances all factors:
  - urgency: 0.35, importance: 0.30, effort: 0.10, dependencies: 0.25
- **Fastest Wins** – surfaces quick, low-effort tasks:
  - urgency: 0.20, importance: 0.20, effort: 0.50, dependencies: 0.10
- **High Impact** – optimizes for importance:
  - urgency: 0.15, importance: 0.60, effort: 0.05, dependencies: 0.20
- **Deadline Driven** – focuses on due dates:
  - urgency: 0.70, importance: 0.15, effort: 0.05, dependencies: 0.10

For each task, we compute:

\[
\text{score} = w_u \cdot \text{urgency} + w_i \cdot \text{importance} + w_e \cdot \text{effort} + w_d \cdot \text{dependencies}
\]

Scores are rounded to two decimals and returned alongside individual components.  
The **explanation generator** uses thresholds on these components and the active strategy to produce human‑readable reasons (e.g., “Due very soon or overdue”, “High importance”, “Quick win”, “Blocks other tasks”), so users understand *why* a task is prioritized.

**Circular dependency detection** is handled via depth‑first search on a task‑dependency graph.  
The algorithm builds an adjacency list from `id` → `dependencies` and tracks a recursion stack to discover cycles. Any cycle found is returned as a set of task IDs and surfaced in the `/analyze/` response, allowing the frontend to warn the user about problematic dependency graphs.

Overall, the algorithm is **configurable (via strategies)**, robust against missing/invalid fields, and intentionally designed to balance urgent work, high impact, quick wins, and dependency bottlenecks.

---

Design Decisions & Trade-offs
-----------------------------

- **No DB persistence for tasks**: the API operates on the request payload only. This keeps the solution stateless and focused on algorithm design rather than CRUD operations.
- **Plain dicts instead of Django models/serializers**: given the assignment’s emphasis on scoring and not storage, tasks are treated as JSON objects. This avoids boilerplate and keeps the core logic easy to read.
- **Strategy-based weighting**: instead of a single hard‑coded formula, the `TaskScorer` exposes multiple strategies (`smart_balance`, `fastest_wins`, `high_impact`, `deadline_driven`). This makes the behavior configurable and easy to extend with user‑specific preferences later.
- **Defensive normalization**: the backend normalizes incoming tasks (ensuring `id`, `title`, `dependencies` exist) and the scorer gracefully handles invalid or missing fields, preferring sane defaults over hard failures.
- **Explanation layer**: rather than returning only raw scores, each task includes a brief explanation derived from its component scores and strategy. This improves UX and helps users trust the algorithm.
- **Simple frontend stack**: the UI uses plain HTML/CSS/JS with `fetch` to keep the tech stack lightweight and transparent, while still demonstrating event handling, validation, loading states, and responsive layout.

---

Time Breakdown (Approximate)
----------------------------

- Problem analysis & algorithm design: ~40 minutes  
- Implementing `TaskScorer` and unit tests: ~60 minutes  
- API endpoints (`/analyze/`, `/suggest/`) and edge-case handling: ~45 minutes  
- Frontend UI (form, strategy selector, API wiring, rendering): ~60 minutes  
- Documentation, cleanup, and small refinements: ~25 minutes  

Total: ~3 hours 50 minutes

---

Bonus Challenges
----------------

- **Implemented**:
  - Circular dependency detection (exposed via `/analyze/` response).
- **Not implemented (due to time)**:
  - Dependency graph visualization
  - Date intelligence for weekends/holidays
  - Eisenhower matrix view
  - Learning system / feedback loop

These are called out as natural extension points for a future iteration.

---

Future Improvements
-------------------

- Expose **user-configurable weights** for urgency/importance/effort/dependencies (per user or per workspace).
- Persist tasks in the database with full CRUD and use Django REST Framework serializers for stronger validation.
- Add a dedicated **dependency graph view** and Eisenhower matrix visualization to complement the list view.
- Enhance calendar awareness (weekends, holidays, working hours) in the urgency calculation.
- Add more comprehensive unit/integration tests around the API layer and edge cases (e.g., very large task graphs).


"# task-analayser" 
