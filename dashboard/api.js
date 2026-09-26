/**
 * IBVAP Dashboard REST API Client
 *
 * Provides functions to fetch persisted operational data from the backend.
 * Gracefully handles failures without throwing uncaught exceptions to caller.
 */

export function getApiBaseUrl() {
    if (typeof window === "undefined" || !window.location) {
        return "http://localhost:8000";
    }
    return window.location.origin;
}

export async function fetchHealth() {
    try {
        const url = `${getApiBaseUrl()}/health`;
        const res = await fetch(url, { headers: { "Accept": "application/json" } });
        if (!res.ok) {
            return { ok: false, status: res.status, error: `HTTP ${res.status}` };
        }
        const data = await res.json();
        return { ok: true, data };
    } catch (err) {
        return { ok: false, error: err.message || "Network error" };
    }
}

/**
 * Generic safe fetch helper for optional/future endpoints
 */
export async function fetchEndpoint(endpointPath) {
    try {
        const url = `${getApiBaseUrl()}${endpointPath}`;
        const res = await fetch(url, { headers: { "Accept": "application/json" } });
        if (!res.ok) {
            return { ok: false, status: res.status, error: `HTTP ${res.status}` };
        }
        const data = await res.json();
        return { ok: true, data };
    } catch (err) {
        return { ok: false, error: err.message || "Network error" };
    }
}
