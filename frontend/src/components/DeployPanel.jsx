import { useEffect, useState } from "react";
import { apiFetch, getActor } from "../api";

const STATUS_LABELS = {
    pending: "Ожидание",
    cloning: "Клонирование",
    building: "Сборка",
    deploying: "Развёртывание",
    success: "Успех",
    failed: "Ошибка",
    rolled_back: "Откат",
};

export default function DeployPanel() {
    const [deployments, setDeployments] = useState([]);
    const [appName, setAppName] = useState("demo-app");
    const [repoUrl, setRepoUrl] = useState("https://github.com/octocat/Hello-World.git");
    const [branch, setBranch] = useState("master");
    const [loading, setLoading] = useState(false);
    const [selected, setSelected] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [taskId, setTaskId] = useState("");

    const load = () => apiFetch("/deployments?limit=20").then(setDeployments).catch(console.error);

    useEffect(() => {
        load();
        apiFetch("/tasks").then(setTasks).catch(console.error);
        const t = setInterval(load, 5000);
        return () => clearInterval(t);
    }, []);

    useEffect(() => {
        if (!taskId) return;
        const task = tasks.find((t) => String(t.id) === taskId);
        if (task?.repo_url) setRepoUrl(task.repo_url);
        if (task?.git_branch) setBranch(task.git_branch);
    }, [taskId, tasks]);

    const startDeploy = async () => {
        setLoading(true);
        try {
            await apiFetch("/deployments", {
                method: "POST",
                body: JSON.stringify({
                    app_name: appName,
                    repo_url: repoUrl,
                    branch,
                    initiated_by: getActor(),
                    task_id: taskId ? Number(taskId) : null,
                }),
            });
            load();
        } catch (e) {
            alert(e.message);
        } finally {
            setLoading(false);
        }
    };

    const rollback = async (id) => {
        if (!confirm("Выполнить откат к предыдущей стабильной версии?")) return;
        try {
            await apiFetch(`/deployments/${id}/rollback?initiated_by=${encodeURIComponent(getActor())}`, {
                method: "POST",
            });
            load();
        } catch (e) {
            alert(e.message);
        }
    };

    return (
        <section>
            <div className="panel">
                <h2>Автоматизированный деплой</h2>
                <p className="muted">Git → сборка контейнера → обновление сервиса</p>
                <div className="deploy-form">
                    <select className="input input--select" value={taskId} onChange={(e) => setTaskId(e.target.value)}>
                        <option value="">Без привязки к задаче</option>
                        {tasks.map((t) => (
                            <option key={t.id} value={t.id}>
                                #{t.id} {t.title} {t.git_branch ? `(${t.git_branch})` : ""}
                            </option>
                        ))}
                    </select>
                    <input className="input" value={appName} onChange={(e) => setAppName(e.target.value)} placeholder="Имя приложения" />
                    <input className="input input--wide" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="URL репозитория" />
                    <input className="input" value={branch} onChange={(e) => setBranch(e.target.value)} placeholder="Ветка" />
                    <button className="button button--primary" onClick={startDeploy} disabled={loading}>
                        {loading ? "Запуск..." : "Задеплоить"}
                    </button>
                </div>
            </div>

            <div className="panel">
                <h3>История развёртываний</h3>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Приложение</th>
                            <th>Версия</th>
                            <th>Статус</th>
                            <th>Кто</th>
                            <th>Время</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {deployments.map((d) => (
                            <tr key={d.id} className={selected === d.id ? "row-selected" : ""}>
                                <td>{d.id}</td>
                                <td>{d.app_name}</td>
                                <td>{d.version || "—"}</td>
                                <td><span className={`status status--${d.status}`}>{STATUS_LABELS[d.status] || d.status}</span></td>
                                <td>{d.initiated_by}</td>
                                <td>{new Date(d.started_at).toLocaleString()}</td>
                                <td>
                                    <button className="button button--ghost" onClick={() => setSelected(d.id)}>Лог</button>
                                    {(d.status === "success" || d.status === "failed") && (
                                        <button className="button button--danger" onClick={() => rollback(d.id)}>Rollback</button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {selected && (
                    <pre className="log-view">
                        {deployments.find((d) => d.id === selected)?.log_output || "Лог пуст"}
                    </pre>
                )}
            </div>
        </section>
    );
}
