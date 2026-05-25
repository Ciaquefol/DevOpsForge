import { useCallback, useEffect, useState } from "react";
import { apiFetch, getActor } from "../api";

const RECIPIENT_OPTIONS = [
    { value: "", label: "Не назначен" },
    { value: "ivan.petrov", label: "Иван Петров (Backend)" },
    { value: "anna.smirnova", label: "Анна Смирнова (Frontend)" },
    { value: "sergey.volkov", label: "Сергей Волков (QA)" },
    { value: "olga.ivanova", label: "Ольга Иванова (DevOps)" },
];

const DEFAULT_REPO = "https://github.com/octocat/Hello-World.git";

export default function KanbanBoard() {
    const [tasks, setTasks] = useState([]);
    const [title, setTitle] = useState("");
    const [assignedTo, setAssignedTo] = useState("");
    const [repoUrl, setRepoUrl] = useState(DEFAULT_REPO);
    const [gitBranch, setGitBranch] = useState("");
    const [branches, setBranches] = useState([]);
    const [createGitBranch, setCreateGitBranch] = useState(false);
    const [error, setError] = useState("");
    const [search, setSearch] = useState("");
    const [historyTaskId, setHistoryTaskId] = useState(null);
    const [history, setHistory] = useState([]);

    const getRecipientLabel = (v) => {
        const o = RECIPIENT_OPTIONS.find((i) => i.value === (v || "").trim());
        return o?.label || v || "Не назначен";
    };

    const loadBranches = useCallback(async (url) => {
        try {
            const data = await apiFetch(`/git/branches?repo_url=${encodeURIComponent(url)}`);
            setBranches(data.branches || []);
        } catch {
            setBranches(["main", "master"]);
        }
    }, []);

    const loadTasks = async (attempt = 0) => {
        try {
            const data = await apiFetch("/tasks");
            setTasks(data);
            setError("");
        } catch (e) {
            if (attempt < 8) {
                setTimeout(() => loadTasks(attempt + 1), 1500);
                return;
            }
            setError("Не удалось загрузить задачи. Проверьте backend.");
            console.error(e);
        }
    };

    useEffect(() => {
        loadTasks();
        loadBranches(repoUrl);
    }, []);

    useEffect(() => {
        if (!historyTaskId) return;
        apiFetch(`/tasks/${historyTaskId}/history`).then(setHistory).catch(console.error);
    }, [historyTaskId]);

    const filterTasks = (list) => {
        const q = search.trim().toLowerCase();
        if (!q) return list;
        return list.filter(
            (t) =>
                t.title.toLowerCase().includes(q) ||
                (t.assigned_to || "").toLowerCase().includes(q) ||
                (t.git_branch || "").toLowerCase().includes(q)
        );
    };

    const todo = filterTasks(tasks.filter((t) => t.status === "todo"));
    const progress = filterTasks(tasks.filter((t) => t.status === "in_progress"));
    const done = filterTasks(tasks.filter((t) => t.status === "done"));

    const addTask = async () => {
        if (!title.trim()) {
            setError("Заголовок обязателен");
            return;
        }
        setError("");
        const saved = await apiFetch("/tasks", {
            method: "POST",
            body: JSON.stringify({
                title,
                description: "Описание задачи",
                status: "todo",
                assigned_to: assignedTo.trim() || null,
                repo_url: repoUrl.trim() || null,
                git_branch: createGitBranch ? null : gitBranch.trim() || null,
                create_git_branch: createGitBranch,
                actor: getActor(),
            }),
        });
        setTasks([...tasks, saved]);
        setTitle("");
        setAssignedTo("");
        setGitBranch("");
        setCreateGitBranch(false);
        loadBranches(repoUrl);
    };

    const linkBranch = async (task, createNew) => {
        try {
            const updated = await apiFetch(`/tasks/${task.id}/git-branch`, {
                method: "PATCH",
                body: JSON.stringify({
                    git_branch: createNew ? null : gitBranch || task.git_branch,
                    repo_url: repoUrl,
                    create_git_branch: createNew,
                    actor: getActor(),
                }),
            });
            setTasks(tasks.map((t) => (t.id === task.id ? updated : t)));
        } catch (e) {
            alert(e.message);
        }
    };

    const deleteTask = async (id) => {
        await apiFetch(`/tasks/${id}?actor=${encodeURIComponent(getActor())}`, { method: "DELETE" });
        setTasks(tasks.filter((t) => t.id !== id));
        if (historyTaskId === id) setHistoryTaskId(null);
    };

    const updateStatus = async (taskId, newStatus) => {
        const id = Number(taskId);
        const task = tasks.find((t) => t.id === id);
        if (!task || task.status === newStatus) return;
        const prev = tasks;
        setTasks(tasks.map((t) => (t.id === id ? { ...t, status: newStatus } : t)));
        try {
            await apiFetch(`/tasks/${id}/move`, {
                method: "PATCH",
                body: JSON.stringify({ status: newStatus, actor: getActor() }),
            });
        } catch {
            setTasks(prev);
        }
    };

    const handleDragStart = (e, taskId) => e.dataTransfer.setData("taskId", String(taskId));
    const handleDragOver = (e) => e.preventDefault();
    const handleDrop = (e, status) => {
        e.preventDefault();
        updateStatus(e.dataTransfer.getData("taskId"), status);
    };

    const renderCard = (task) => (
        <li
            key={task.id}
            draggable
            onDragStart={(e) => handleDragStart(e, task.id)}
            className="task-card"
        >
            <div className="task-card__head">
                <span className="task-card__title">{task.title}</span>
                <div className="task-card__actions">
                    <button type="button" className="button button--ghost" onClick={() => setHistoryTaskId(task.id)}>
                        История
                    </button>
                    <button type="button" className="button button--danger" onClick={() => deleteTask(task.id)}>
                        Удалить
                    </button>
                </div>
            </div>
            <div className="task-card__meta">
                Исполнитель: <strong>{getRecipientLabel(task.assigned_to)}</strong>
            </div>
            <div className="task-card__meta task-card__branch">
                Ветка: <strong>{task.git_branch || "не привязана"}</strong>
                {task.repo_url && <span className="muted"> ({task.repo_url.split("/").pop()?.replace(".git", "")})</span>}
            </div>
            <div className="task-card__branch-actions">
                <button type="button" className="button button--ghost" onClick={() => linkBranch(task, true)}>
                    Создать ветку
                </button>
            </div>
        </li>
    );

    return (
        <section>
            <div className="toolbar">
                <button type="button" className="button button--ghost" onClick={() => loadTasks()}>
                    Обновить
                </button>
                <input
                    className="input input--search"
                    placeholder="Поиск (название, исполнитель, ветка)..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            <div className="panel">
                <h3>Репозиторий для привязки веток</h3>
                <div className="create-form create-form--wrap">
                    <input
                        className="input input--wide"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        onBlur={() => loadBranches(repoUrl)}
                        placeholder="URL Git-репозитория"
                    />
                    <button type="button" className="button button--ghost" onClick={() => loadBranches(repoUrl)}>
                        Обновить ветки
                    </button>
                </div>
            </div>

            <div className="create-form create-form--wrap">
                <input
                    className={`input ${error ? "input--error" : ""}`}
                    placeholder="Название задачи"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addTask()}
                />
                <select className="input input--select" value={assignedTo} onChange={(e) => setAssignedTo(e.target.value)}>
                    {RECIPIENT_OPTIONS.map((o) => (
                        <option key={o.value || "u"} value={o.value}>{o.label}</option>
                    ))}
                </select>
                <select
                    className="input input--select"
                    value={gitBranch}
                    disabled={createGitBranch}
                    onChange={(e) => setGitBranch(e.target.value)}
                >
                    <option value="">Ветка (не выбрана)</option>
                    {branches.map((b) => (
                        <option key={b} value={b}>{b}</option>
                    ))}
                </select>
                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={createGitBranch}
                        onChange={(e) => setCreateGitBranch(e.target.checked)}
                    />
                    Создать ветку task/N-...
                </label>
                <button type="button" className="button button--primary" onClick={addTask}>
                    Добавить
                </button>
            </div>
            {error && <p className="error-text">{error}</p>}

            <div className="board">
                <div className="column column--todo" onDragOver={handleDragOver} onDrop={(e) => handleDrop(e, "todo")}>
                    <h2 className="column__title">К выполнению</h2>
                    <ul className="task-list">{todo.map(renderCard)}</ul>
                </div>
                <div className="column column--progress" onDragOver={handleDragOver} onDrop={(e) => handleDrop(e, "in_progress")}>
                    <h2 className="column__title">В работе</h2>
                    <ul className="task-list">{progress.map(renderCard)}</ul>
                </div>
                <div className="column column--done" onDragOver={handleDragOver} onDrop={(e) => handleDrop(e, "done")}>
                    <h2 className="column__title">Готово</h2>
                    <ul className="task-list">{done.map(renderCard)}</ul>
                </div>
            </div>

            {historyTaskId && (
                <div className="panel panel--history">
                    <div className="panel__head">
                        <h3>История задачи #{historyTaskId}</h3>
                        <button type="button" className="button button--ghost" onClick={() => setHistoryTaskId(null)}>Закрыть</button>
                    </div>
                    <ul className="history-list">
                        {history.length === 0 && <li>Нет записей</li>}
                        {history.map((h) => (
                            <li key={h.id}>
                                <strong>{h.field_name}</strong>: {h.old_value || "—"} → {h.new_value || "—"}
                                <span className="muted"> ({h.changed_by}, {new Date(h.changed_at).toLocaleString()})</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </section>
    );
}
