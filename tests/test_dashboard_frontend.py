from pathlib import Path


def test_dashboard_files_exist():
    dashboard_dir = Path("dashboard")
    assert (dashboard_dir / "index.html").exists(), "dashboard/index.html must exist"
    assert (dashboard_dir / "websocket.js").exists(), "dashboard/websocket.js must exist"
    assert (dashboard_dir / "app.js").exists(), "dashboard/app.js must exist"
    assert (dashboard_dir / "api.js").exists(), "dashboard/api.js must exist"


def test_dashboard_html_structure():
    html_content = Path("dashboard/index.html").read_text(encoding="utf-8")
    assert 'id="connectionStatus"' in html_content
    assert 'id="statusText"' in html_content
    assert 'id="feedList"' in html_content
    assert 'id="itemCount"' in html_content
    assert 'id="backendSummaryCard"' in html_content
    assert 'id="backendHealthVal"' in html_content
    assert 'src="./app.js"' in html_content or 'src="app.js"' in html_content


def test_api_js_contains_health_and_endpoint_helpers():
    api_content = Path("dashboard/api.js").read_text(encoding="utf-8")
    assert "getApiBaseUrl" in api_content
    assert "fetchHealth" in api_content
    assert "fetchEndpoint" in api_content
    assert "/health" in api_content


def test_websocket_js_contains_url_builder_and_client():
    js_content = Path("dashboard/websocket.js").read_text(encoding="utf-8")
    assert "getWebSocketUrl" in js_content
    assert "/api/v1/ws/events" in js_content
    assert "DashboardWebSocketClient" in js_content
    assert "wss:" in js_content
    assert "ws:" in js_content


def test_app_js_handles_event_and_alert_types():
    app_content = Path("dashboard/app.js").read_text(encoding="utf-8")
    assert "event.created" in app_content
    assert "alert.created" in app_content
    assert "handleIncomingMessage" in app_content
    assert "createFeedItemElement" in app_content
    assert "loadRestData" in app_content
    assert "/api/v1/alerts" in app_content
    assert "/api/v1/cameras" in app_content
    assert "/api/v1/anpr/logs" in app_content
    assert "/api/v1/analytics/summary" in app_content
    # Confirm unsafe innerHTML is not used
    assert "innerHTML" not in app_content
    assert "textContent" in app_content


def test_create_feed_item_element_escapes_html_payload():
    """Verify in a headless JS runtime that HTML tags in message/event_type are treated as text."""
    import subprocess
    import shutil

    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js runtime not installed on host")

    script = """
    // Minimal mock of DOM for Node testing
    class ElementMock {
        constructor(tagName) {
            this.tagName = tagName;
            this.className = "";
            this.classList = {
                add: (c) => { this.className += " " + c; }
            };
            this.style = {};
            this.children = [];
            this.textContent = "";
        }
        appendChild(child) {
            this.children.push(child);
        }
    }

    global.document = {
        createElement: (tag) => new ElementMock(tag)
    };

    import('./dashboard/app.js').then(({ createFeedItemElement }) => {
        const payload = {
            type: "alert.created",
            alert_id: "<script>alert('id')</script>",
            event_id: "<img src=x onerror=alert('x')>",
            priority: "HIGH",
            status: "<b>ACTIVE</b>",
            message: "<script>alert('pwned')</script>"
        };

        const element = createFeedItemElement(payload);
        
        // Find message element
        const msgEl = element.children.find(c => c.className === "item-message");
        if (!msgEl || msgEl.textContent !== "<script>alert('pwned')</script>") {
            console.error("Message was not preserved as textContent:", msgEl);
            process.exit(1);
        }

        // Find details element
        const detailsEl = element.children.find(c => c.className === "item-details");
        if (!detailsEl || !detailsEl.textContent.includes("<script>alert('id')</script>")) {
            console.error("Details were not preserved as textContent:", detailsEl);
            process.exit(1);
        }

        // Ensure innerHTML is never created or set on the mock
        if (element.innerHTML !== undefined) {
            console.error("innerHTML property was found on element");
            process.exit(1);
        }

        console.log("SUCCESS");
    }).catch(err => {
        console.error(err);
        process.exit(1);
    });
    """

    res = subprocess.run([node_bin, "--input-type=module", "-e", script], capture_output=True, text=True)
    assert res.returncode == 0, f"Node test failed: {res.stderr}\n{res.stdout}"
    assert "SUCCESS" in res.stdout


def test_load_rest_data_handles_success_and_failures_gracefully():
    """Verify loadRestData updates DOM elements safely on REST success and handles failures without throwing."""
    import subprocess
    import shutil

    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js runtime not installed on host")

    script = """
    class ElementMock {
        constructor(id) {
            this.id = id;
            this.textContent = "";
            this.style = {};
        }
    }

    const elements = {
        "backendHealthVal": new ElementMock("backendHealthVal"),
        "backendHealthModule": new ElementMock("backendHealthModule"),
        "backendStatusBadge": new ElementMock("backendStatusBadge"),
        "restStatusMessage": new ElementMock("restStatusMessage"),
        "persistedAlertsVal": new ElementMock("persistedAlertsVal"),
        "camerasCountVal": new ElementMock("camerasCountVal"),
        "analyticsSummaryVal": new ElementMock("analyticsSummaryVal"),
        "anprLogsVal": new ElementMock("anprLogsVal")
    };

    global.document = {
        getElementById: (id) => elements[id] || null
    };

    // Test 1: Successful /health fetch
    global.fetch = async (url) => {
        if (url.endsWith('/health')) {
            return {
                ok: true,
                status: 200,
                json: async () => ({ status: "healthy", module: "Person 6 Backend" })
            };
        }
        return {
            ok: false,
            status: 404,
            json: async () => ({ detail: "Not Found" })
        };
    };

    import('./dashboard/app.js').then(async ({ loadRestData }) => {
        await loadRestData();
        if (elements.backendHealthVal.textContent !== "HEALTHY") {
            console.error("Expected HEALTHY, got:", elements.backendHealthVal.textContent);
            process.exit(1);
        }
        if (elements.backendStatusBadge.textContent !== "Online") {
            console.error("Expected Online status badge, got:", elements.backendStatusBadge.textContent);
            process.exit(1);
        }

        // Test 2: Network failure during fetch
        global.fetch = async () => {
            throw new Error("Network connection refused");
        };

        await loadRestData();
        if (elements.backendHealthVal.textContent !== "Offline / Unreachable") {
            console.error("Expected Offline, got:", elements.backendHealthVal.textContent);
            process.exit(1);
        }

        console.log("REST_TEST_SUCCESS");
    }).catch(err => {
        console.error(err);
        process.exit(1);
    });
    """

    res = subprocess.run([node_bin, "--input-type=module", "-e", script], capture_output=True, text=True)
    assert res.returncode == 0, f"Node test failed: {res.stderr}\n{res.stdout}"
    assert "REST_TEST_SUCCESS" in res.stdout
