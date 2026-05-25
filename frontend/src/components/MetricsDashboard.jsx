import { useEffect, useState } from "react";
import { apiFetch, metricsWsUrl } from "../api";

export default function MetricsDashboard() {
    const [latest, setLatest] = useState(null);
    const [history, setHistory] = useState([]);
    const [processes, setProcesses] = useState([]);

    useEffect(() => {
        apiFetch("/metrics/history?minutes=30").then(setHistory).catch(console.error);
        apiFetch("/metrics/latest")
            .then((data) => {
                if (!data) return;
                setLatest(data);
                if (Array.isArray(data.top_processes)) setProcesses(data.top_processes);
            })
            .catch(console.error);

        const ws = new WebSocket(metricsWsUrl());
        ws.onmessage = (msg) => {
            const data = JSON.parse(msg.data);
            setLatest(data);
            setProcesses(Array.isArray(data.top_processes) ? data.top_processes : []);
            setHistory((prev) => [...prev.slice(-59), data]);
        };
        return () => ws.close();
    }, []);

    const maxCpu = Math.max(100, ...history.map((h) => h.cpu_percent || 0), 1);

    return (
        <section>
            <div className="metrics-grid">
                <div className="metric-card">
                    <span className="metric-card__label">CPU</span>
                    <span className="metric-card__value">{latest?.cpu_percent?.toFixed(1) ?? "—"}%</span>
                </div>
                <div className="metric-card">
                    <span className="metric-card__label">RAM</span>
                    <span className="metric-card__value">{latest?.memory_percent?.toFixed(1) ?? "—"}%</span>
                </div>
                <div className="metric-card">
                    <span className="metric-card__label">Память</span>
                    <span className="metric-card__value">
                        {latest ? `${latest.memory_used_mb} / ${latest.memory_total_mb} MB` : "—"}
                    </span>
                </div>
                <div className="metric-card">
                    <span className="metric-card__label">Процессы</span>
                    <span className="metric-card__value">{latest?.process_count ?? "—"}</span>
                </div>
            </div>

            <div className="panel">
                <h3>График CPU (последние замеры)</h3>
                <div className="chart-bars">
                    {history.slice(-30).map((h, i) => (
                        <div
                            key={i}
                            className="chart-bar"
                            style={{ height: `${((h.cpu_percent || 0) / maxCpu) * 100}%` }}
                            title={`${h.cpu_percent?.toFixed(1)}%`}
                        />
                    ))}
                </div>
            </div>

            <div className="panel">
                <h3>Топ процессов по CPU</h3>
                <table className="data-table">
                    <thead>
                        <tr><th>PID</th><th>Имя</th><th>CPU %</th><th>RAM %</th></tr>
                    </thead>
                    <tbody>
                        {processes.map((p) => (
                            <tr key={p.pid}>
                                <td>{p.pid}</td>
                                <td>{p.name}</td>
                                <td>{p.cpu_percent?.toFixed?.(1) ?? p.cpu_percent ?? "—"}</td>
                                <td>{p.memory_percent?.toFixed?.(1) ?? p.memory_percent ?? "—"}</td>
                            </tr>
                        ))}
                        {processes.length === 0 && (
                            <tr><td colSpan={4} className="muted">Ожидание данных...</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </section>
    );
}
