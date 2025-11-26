// Smart Task Analyzer Frontend
// Handles task input, validation, API calls, and rendering results.

const API_BASE = "http://127.0.0.1:8000/api/tasks/";

const state = {
  tasks: [],
  lastAnalyzed: [],
};

function $(selector) {
  return document.querySelector(selector);
}

function setStatus(message, type = "") {
  const el = $("#status");
  if (!el) return;
  el.textContent = message || "";
  el.className = `status ${type}`;
}

function parseDependencies(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean)
    .map((v) => (isNaN(Number(v)) ? v : Number(v)));
}

function collectTaskFromForm() {
  const title = $("#title").value.trim();
  const dueDate = $("#due_date").value;
  const estimatedHours = $("#estimated_hours").value;
  const importance = $("#importance").value;
  const depInput = $("#dependencies").value;

  if (!title || !dueDate || !estimatedHours || !importance) {
    setStatus("Please fill in all required fields.", "error");
    return null;
  }

  if (Number(importance) < 1 || Number(importance) > 10) {
    setStatus("Importance must be between 1 and 10.", "error");
    return null;
  }

  const task = {
    id: state.tasks.length + 1,
    title,
    due_date: dueDate,
    estimated_hours: Number(estimatedHours),
    importance: Number(importance),
    dependencies: parseDependencies(depInput),
  };

  return task;
}

function renderTasks(tasks, fromSuggestion = false) {
  const container = $("#task-list");
  if (!container) return;

  if (!tasks || tasks.length === 0) {
    container.classList.add("empty-state");
    container.innerHTML =
      "<p>No tasks to display yet. Add tasks and analyze them to see priorities.</p>";
    return;
  }

  container.classList.remove("empty-state");

  const cards = tasks
    .map((task) => {
      const score = task.priority_score ?? task.score ?? 0;
      let priorityClass = "priority-low";
      if (score >= 7.5) priorityClass = "priority-high";
      else if (score >= 4.5) priorityClass = "priority-medium";

      const components = task.score_components || {};
      const explanation = task.explanation || "No explanation provided.";

      return `
        <article class="task-card">
          <div>
            <div class="task-header">
              <div class="task-title">
                ${task.id ? `<span>#${task.id}</span> &mdash; ` : ""}${task.title || "Untitled task"}
              </div>
              <span class="task-score-pill ${priorityClass}">
                <span>Score</span>
                <strong>${score.toFixed ? score.toFixed(2) : score}</strong>
              </span>
            </div>
            <div class="task-meta">
              <span>📅 <strong>Due:</strong> ${task.due_date || "n/a"}</span>
              <span>⏱ <strong>Effort:</strong> ${task.estimated_hours ?? "n/a"}h</span>
              <span>⭐ <strong>Importance:</strong> ${task.importance ?? "n/a"}</span>
              <span>🔗 <strong>Deps:</strong> ${
                (task.dependencies && task.dependencies.length) || 0
              }</span>
            </div>
          </div>
          <div>
            <div class="components-row">
              <span>Urgency: ${components.urgency ?? "-"}</span>
              <span>Importance: ${components.importance ?? "-"}</span>
              <span>Effort: ${components.effort ?? "-"}</span>
              <span>Deps: ${components.dependencies ?? "-"}</span>
            </div>
          </div>
          <div class="task-explanation">
            ${fromSuggestion ? "<strong>Why this is suggested:</strong> " : ""}
            ${explanation}
          </div>
        </article>
      `;
    })
    .join("");

  container.innerHTML = cards;
}

async function analyzeTasks() {
  if (state.tasks.length === 0) {
    setStatus("Please add at least one task before analyzing.", "error");
    return;
  }

  const strategy = $("#strategy").value;

  setStatus("Analyzing tasks...", "success");
  $("#analyze-btn").disabled = true;
  $("#suggest-btn").disabled = true;

  try {
    const res = await fetch(`${API_BASE}analyze/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        tasks: state.tasks,
        strategy,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Unexpected error analyzing tasks.");
    }

    const data = await res.json();
    const analyzed = data.tasks || [];
    state.lastAnalyzed = analyzed;

    renderTasks(analyzed);

    if (data.circular_dependencies && data.circular_dependencies.length) {
      setStatus(
        `Analyzed ${analyzed.length} tasks. Warning: detected circular dependencies: ${JSON.stringify(
          data.circular_dependencies
        )}`,
        "error"
      );
    } else {
      setStatus(`Analyzed ${analyzed.length} tasks using "${strategy}" strategy.`, "success");
    }
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Failed to analyze tasks.", "error");
  } finally {
    $("#analyze-btn").disabled = false;
    $("#suggest-btn").disabled = false;
  }
}

async function suggestTasks() {
  const strategy = $("#strategy").value;
  const tasksToSend = state.lastAnalyzed.length ? state.lastAnalyzed : state.tasks;

  if (!tasksToSend.length) {
    setStatus("No tasks analyzed yet. Please analyze tasks first.", "error");
    return;
  }

  setStatus("Fetching suggestions...", "success");
  $("#analyze-btn").disabled = true;
  $("#suggest-btn").disabled = true;

  try {
    const res = await fetch(`${API_BASE}suggest/?strategy=${encodeURIComponent(strategy)}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tasks: tasksToSend }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Unexpected error suggesting tasks.");
    }

    const data = await res.json();
    const top = data.top_tasks || [];
    renderTasks(top, true);
    setStatus(`Showing top ${top.length} suggested tasks.`, "success");
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Failed to fetch suggestions.", "error");
  } finally {
    $("#analyze-btn").disabled = false;
    $("#suggest-btn").disabled = false;
  }
}

function wireEvents() {
  const form = $("#task-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const task = collectTaskFromForm();
    if (!task) return;
    state.tasks.push(task);
    setStatus(`Added task "${task.title}".`, "success");
    form.reset();
    renderTasks(state.tasks);
  });

  $("#clear-tasks").addEventListener("click", () => {
    state.tasks = [];
    state.lastAnalyzed = [];
    renderTasks([]);
    setStatus("Cleared all tasks.", "success");
  });

  $("#load-bulk").addEventListener("click", () => {
    const raw = $("#bulk-json").value.trim();
    if (!raw) {
      setStatus("Paste a JSON array of tasks to load.", "error");
      return;
    }
    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        throw new Error("JSON must be an array of tasks.");
      }
      state.tasks = parsed.map((t, idx) => ({
        id: idx + 1,
        title: t.title || `Task ${idx + 1}`,
        due_date: t.due_date || null,
        estimated_hours: t.estimated_hours ?? null,
        importance: t.importance ?? null,
        dependencies: t.dependencies || [],
      }));
      renderTasks(state.tasks);
      setStatus(`Loaded ${state.tasks.length} tasks from JSON.`, "success");
    } catch (err) {
      console.error(err);
      setStatus(err.message || "Invalid JSON.", "error");
    }
  });

  $("#analyze-btn").addEventListener("click", () => {
    analyzeTasks();
  });

  $("#suggest-btn").addEventListener("click", () => {
    suggestTasks();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  wireEvents();
  renderTasks([]);
});

