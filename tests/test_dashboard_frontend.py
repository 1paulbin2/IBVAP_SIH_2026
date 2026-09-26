from pathlib import Path


def test_dashboard_files_exist():
    dashboard_dir = Path("dashboard")
    assert (dashboard_dir / "index.html").exists(), "dashboard/index.html must exist"
    assert (dashboard_dir / "websocket.js").exists(), "dashboard/websocket.js must exist"
    assert (dashboard_dir / "app.js").exists(), "dashboard/app.js must exist"


def test_dashboard_html_structure():
    html_content = Path("dashboard/index.html").read_text(encoding="utf-8")
    assert 'id="connectionStatus"' in html_content
    assert 'id="statusText"' in html_content
    assert 'id="feedList"' in html_content
    assert 'id="itemCount"' in html_content
    assert 'src="./app.js"' in html_content or 'src="app.js"' in html_content


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

