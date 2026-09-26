import { DashboardWebSocketClient } from "./websocket.js";

let totalItems = 0;

export function formatTimestamp(ts) {
    if (!ts) return new Date().toLocaleTimeString();
    try {
        const d = new Date(ts);
        return isNaN(d.getTime()) ? String(ts) : d.toLocaleTimeString();
    } catch {
        return String(ts);
    }
}

export function createFeedItemElement(payload) {
    const item = document.createElement("div");
    item.className = "feed-item";

    const msgType = payload.type || "unknown";
    const timestamp = payload.timestamp;
    const timeStr = formatTimestamp(timestamp);

    // Header row (.item-top)
    const topRow = document.createElement("div");
    topRow.className = "item-top";

    const titleGroup = document.createElement("div");

    const timeSpan = document.createElement("span");
    timeSpan.className = "item-time";
    timeSpan.textContent = timeStr;

    if (msgType === "alert.created") {
        item.classList.add("alert-item");
        const priority = payload.priority ? String(payload.priority).toUpperCase() : "";
        if (priority) {
            item.classList.add(`priority-${priority}`);
        }

        const typeBadge = document.createElement("span");
        typeBadge.className = "item-type";
        typeBadge.style.color = "#ef4444";
        typeBadge.textContent = "ALERT";
        titleGroup.appendChild(typeBadge);

        if (priority) {
            const priorityBadge = document.createElement("span");
            priorityBadge.className = "item-priority";
            priorityBadge.textContent = priority;
            titleGroup.appendChild(priorityBadge);
        }

        topRow.appendChild(titleGroup);
        topRow.appendChild(timeSpan);
        item.appendChild(topRow);

        if (payload.message) {
            const messageEl = document.createElement("div");
            messageEl.className = "item-message";
            messageEl.textContent = String(payload.message);
            item.appendChild(messageEl);
        }

        const detailsEl = document.createElement("div");
        detailsEl.className = "item-details";
        detailsEl.textContent = `Alert ID: ${payload.alert_id ?? "-"} | Event ID: ${payload.event_id ?? "-"} | Status: ${payload.status ?? "-"}`;
        item.appendChild(detailsEl);

    } else if (msgType === "event.created") {
        const typeBadge = document.createElement("span");
        typeBadge.className = "item-type";
        typeBadge.style.color = "#38bdf8";
        typeBadge.textContent = "EVENT";
        titleGroup.appendChild(typeBadge);

        if (payload.event_type) {
            const eventTypeSpan = document.createElement("span");
            eventTypeSpan.style.fontWeight = "500";
            eventTypeSpan.style.fontSize = "0.85rem";
            eventTypeSpan.style.marginLeft = "0.5rem";
            eventTypeSpan.style.color = "#cbd5e1";
            eventTypeSpan.textContent = String(payload.event_type);
            titleGroup.appendChild(eventTypeSpan);
        }

        topRow.appendChild(titleGroup);
        topRow.appendChild(timeSpan);
        item.appendChild(topRow);

        const detailsEl = document.createElement("div");
        detailsEl.className = "item-details";
        detailsEl.textContent = `Event ID: ${payload.event_id ?? "-"} | Camera: ${payload.camera_id ?? "-"}`;
        item.appendChild(detailsEl);

    } else {
        const typeBadge = document.createElement("span");
        typeBadge.className = "item-type";
        typeBadge.textContent = String(msgType);
        titleGroup.appendChild(typeBadge);

        topRow.appendChild(titleGroup);
        topRow.appendChild(timeSpan);
        item.appendChild(topRow);

        const detailsEl = document.createElement("div");
        detailsEl.className = "item-details";
        try {
            detailsEl.textContent = typeof payload === "object" ? JSON.stringify(payload) : String(payload);
        } catch {
            detailsEl.textContent = String(payload);
        }
        item.appendChild(detailsEl);
    }

    return item;
}

export function handleIncomingMessage(payload, feedContainer, emptyPlaceholder, counterElement) {
    if (!feedContainer) return;

    if (emptyPlaceholder && emptyPlaceholder.style.display !== "none") {
        emptyPlaceholder.style.display = "none";
    }

    const itemElement = createFeedItemElement(payload);
    feedContainer.prepend(itemElement);

    totalItems += 1;
    if (counterElement) {
        counterElement.textContent = `${totalItems} item${totalItems === 1 ? "" : "s"}`;
    }
}

export function updateConnectionUI(statusBadge, statusText, isConnected, label = null) {
    if (!statusBadge || !statusText) return;
    if (isConnected) {
        statusBadge.classList.add("connected");
        statusText.textContent = label || "Connected";
    } else {
        statusBadge.classList.remove("connected");
        statusText.textContent = label || "Disconnected";
    }
}

export function initDashboard() {
    const statusBadge = document.getElementById("connectionStatus");
    const statusText = document.getElementById("statusText");
    const feedContainer = document.getElementById("feedList");
    const emptyPlaceholder = document.getElementById("emptyFeedMessage");
    const counterElement = document.getElementById("itemCount");

    const client = new DashboardWebSocketClient({
        path: "/api/v1/ws/events",
        onOpen: () => {
            updateConnectionUI(statusBadge, statusText, true, "Live");
        },
        onClose: () => {
            updateConnectionUI(statusBadge, statusText, false, "Disconnected (Reconnecting...)");
        },
        onError: () => {
            updateConnectionUI(statusBadge, statusText, false, "Connection Error");
        },
        onMessage: (payload) => {
            handleIncomingMessage(payload, feedContainer, emptyPlaceholder, counterElement);
        }
    });

    client.connect();
    return client;
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initDashboard);
    } else {
        initDashboard();
    }
}
