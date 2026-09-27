/**
 * IBVAP Realtime WebSocket Client for Dashboard
 *
 * Connects to /api/v1/ws/events and delivers decoded JSON payloads
 * ('event.created', 'alert.created') to subscriber callbacks.
 */

export function getWebSocketUrl(path = "/api/v1/ws/events") {
    if (typeof window === "undefined" || !window.location) {
        return `ws://localhost:8000${path}`;
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    return `${protocol}//${host}${path}`;
}

export class DashboardWebSocketClient {
    constructor(options = {}) {
        this.url = options.url || getWebSocketUrl(options.path || "/api/v1/ws/events");
        this.onMessage = options.onMessage || (() => {});
        this.onOpen = options.onOpen || (() => {});
        this.onClose = options.onClose || (() => {});
        this.onError = options.onError || (() => {});
        this.reconnectInterval = options.reconnectInterval || 3000;
        this.autoReconnect = options.autoReconnect ?? true;

        this.ws = null;
        this._isClosedExplicitly = false;
        this._reconnectTimer = null;
    }

    connect() {
        this._isClosedExplicitly = false;
        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = (event) => {
                if (this.onOpen) this.onOpen(event);
            };

            this.ws.onmessage = (event) => {
                let parsed = null;
                try {
                    parsed = JSON.parse(event.data);
                } catch (err) {
                    parsed = { type: "raw", data: event.data };
                }
                if (this.onMessage) {
                    this.onMessage(parsed);
                }
            };

            this.ws.onclose = (event) => {
                if (this.onClose) this.onClose(event);
                if (!this._isClosedExplicitly && this.autoReconnect) {
                    this._scheduleReconnect();
                }
            };

            this.ws.onerror = (error) => {
                if (this.onError) this.onError(error);
            };
        } catch (err) {
            if (this.onError) this.onError(err);
            if (!this._isClosedExplicitly && this.autoReconnect) {
                this._scheduleReconnect();
            }
        }
    }

    _scheduleReconnect() {
        if (this._reconnectTimer) return;
        this._reconnectTimer = setTimeout(() => {
            this._reconnectTimer = null;
            if (!this._isClosedExplicitly) {
                this.connect();
            }
        }, this.reconnectInterval);
    }

    disconnect() {
        this._isClosedExplicitly = true;
        if (this._reconnectTimer) {
            clearTimeout(this._reconnectTimer);
            this._reconnectTimer = null;
        }
        if (this.ws) {
            try {
                this.ws.close();
            } catch (e) {
                // ignore close errors
            }
            this.ws = null;
        }
    }
}
