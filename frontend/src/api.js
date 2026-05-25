// Dev (npm run dev): /api -> Vite proxy -> backend :8000
// Docker/nginx: VITE_API_URL=http://localhost/api in .env
function resolveApiBase() {
    const env = import.meta.env.VITE_API_URL;
    if (import.meta.env.DEV) {
        // npm run dev: Vite proxy /api -> :8000 (ignore Docker .env without port 8000)
        if (!env || !env.includes(":8000")) return "/api";
    }
    return env || "http://127.0.0.1:8000/api";
}

export const API_BASE = resolveApiBase();

function apiWsBase() {
    if (import.meta.env.DEV && API_BASE === "/api") {
        const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
        return `${proto}//${window.location.host}/api`;
    }
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL.replace(/^http/, "ws").replace(/\/$/, "");
    }
    return "ws://127.0.0.1:8000/api";
}

export function getActor() {
    return localStorage.getItem("devopsforge_actor") || "devops";
}

export function setActor(name) {
    localStorage.setItem("devopsforge_actor", name);
}

export async function apiFetch(path, options = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || JSON.stringify(err));
    }
    if (res.status === 204) return null;
    return res.json();
}

export async function checkBackendHealth() {
    const urls = [];
    if (API_BASE === "/api" || import.meta.env.DEV) {
        urls.push("/health");
    }
    urls.push("http://127.0.0.1:8000/health");

    for (const url of urls) {
        try {
            const res = await fetch(url);
            if (res.ok) return true;
        } catch {
            /* try next */
        }
    }
    return false;
}

export function activityWsUrl() {
    return `${apiWsBase()}/ws/activity`;
}

export function metricsWsUrl() {
    return `${apiWsBase()}/ws/metrics`;
}
