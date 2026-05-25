import { useEffect, useState } from "react";
import "./App.css";
import { checkBackendHealth, getActor, setActor } from "./api";
import ActivityFeed from "./components/ActivityFeed";
import DeployPanel from "./components/DeployPanel";
import KanbanBoard from "./components/KanbanBoard";
import MetricsDashboard from "./components/MetricsDashboard";

const TABS = [
    { id: "kanban", label: "Kanban" },
    { id: "activity", label: "Активность" },
    { id: "deploy", label: "Деплой" },
    { id: "metrics", label: "Метрики" },
];

function App() {
    const [tab, setTab] = useState("kanban");
    const [actor, setActorState] = useState(getActor());
    const [backendOk, setBackendOk] = useState(null);

    useEffect(() => {
        const probe = () =>
            checkBackendHealth()
                .then(setBackendOk)
                .catch(() => setBackendOk(false));
        probe();
        const id = setInterval(probe, 10000);
        return () => clearInterval(id);
    }, []);

    const saveActor = () => {
        setActor(actor.trim() || "devops");
        setActorState(getActor());
    };

    return (
        <div className="app-shell">
            <header className="app-header">
                <div>
                    <h1>DevOpsForge</h1>
                    <p>Мониторинг команды · Kanban · автодеплой · метрики серверов</p>
                </div>
                <div className="actor-box">
                    <input
                        className="input"
                        value={actor}
                        onChange={(e) => setActorState(e.target.value)}
                        placeholder="Ваше имя"
                    />
                    <button className="button button--ghost" onClick={saveActor}>Сохранить</button>
                </div>
            </header>

            {backendOk === null && (
                <div className="alert">Проверка связи с backend...</div>
            )}
            {backendOk === false && (
                <div className="alert alert--error">
                    Backend не отвечает. Окно «DevOpsForge Backend» должно быть открыто.
                    Проверьте: <a href="http://127.0.0.1:8000/health">http://127.0.0.1:8000/health</a>
                    {" "}(должен быть status ok). Затем обновите эту страницу (F5).
                </div>
            )}
            {backendOk === true && (
                <div className="alert alert--ok">Backend подключён</div>
            )}

            <nav className="tabs">
                {TABS.map((t) => (
                    <button
                        key={t.id}
                        className={`tab ${tab === t.id ? "tab--active" : ""}`}
                        onClick={() => setTab(t.id)}
                    >
                        {t.label}
                    </button>
                ))}
            </nav>

            <main>
                {tab === "kanban" && <KanbanBoard />}
                {tab === "activity" && <ActivityFeed />}
                {tab === "deploy" && <DeployPanel />}
                {tab === "metrics" && <MetricsDashboard />}
            </main>
        </div>
    );
}

export default App;
