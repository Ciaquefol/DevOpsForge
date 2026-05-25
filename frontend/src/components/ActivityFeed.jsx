import { useEffect, useState } from "react";
import { activityWsUrl, apiFetch } from "../api";

export default function ActivityFeed() {
    const [events, setEvents] = useState([]);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        apiFetch("/activity?limit=30").then(setEvents).catch(console.error);

        const ws = new WebSocket(activityWsUrl());
        ws.onopen = () => setConnected(true);
        ws.onclose = () => setConnected(false);
        ws.onmessage = (msg) => {
            const event = JSON.parse(msg.data);
            setEvents((prev) => [event, ...prev].slice(0, 50));
        };
        return () => ws.close();
    }, []);

    return (
        <section className="panel">
            <div className="panel__head">
                <h2>Активность команды</h2>
                <span className={`badge ${connected ? "badge--ok" : "badge--off"}`}>
                    {connected ? "Live" : "Offline"}
                </span>
            </div>
            <ul className="activity-list">
                {events.map((e) => (
                    <li key={`${e.id}-${e.created_at}`} className="activity-item">
                        <span className="activity-item__type">{e.event_type}</span>
                        <span className="activity-item__msg">{e.message}</span>
                        <span className="activity-item__meta">
                            {e.actor} · {new Date(e.created_at).toLocaleString()}
                        </span>
                    </li>
                ))}
                {events.length === 0 && <li className="muted">Событий пока нет</li>}
            </ul>
        </section>
    );
}
