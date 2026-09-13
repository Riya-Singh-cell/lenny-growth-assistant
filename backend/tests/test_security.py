import pytest
from app.security.sanitizer import sanitize_html


def test_sanitize_removes_script_tags():
    malicious = "<div><h1>Growth Framework</h1><script>alert('pwned');</script><p>Safe text</p></div>"
    cleaned = sanitize_html(malicious)
    assert "<script>" not in cleaned
    assert "alert('pwned')" not in cleaned
    assert "Growth Framework" in cleaned
    assert "Safe text" in cleaned


def test_sanitize_removes_inline_event_handlers():
    malicious = '<button onclick="stealCookies()" onmouseover="hack()" style="color: red;">Click</button>'
    cleaned = sanitize_html(malicious)
    assert "onclick" not in cleaned.lower()
    assert "onmouseover" not in cleaned.lower()
    assert "stealCookies" not in cleaned


def test_sanitize_blocks_dangerous_protocols():
    malicious = '<a href="javascript:alert(1)">Click Me</a><a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">Payload</a>'
    cleaned = sanitize_html(malicious)
    assert "javascript:" not in cleaned.lower()
    assert "data:text/html" not in cleaned.lower()


def test_sanitize_preserves_safe_html_and_css():
    safe_html = """
    <div class="card" style="background-color: #f3f4f6; padding: 20px; border-radius: 8px;">
        <h2>The 3 Pillars of PLG</h2>
        <table border="1">
            <thead>
                <tr><th>Stage</th><th>Metric</th></tr>
            </thead>
            <tbody>
                <tr><td>Activation</td><td>Time to Value (TTV)</td></tr>
            </tbody>
        </table>
        <p>Grounded in Elena Verna's frameworks.</p>
    </div>
    """
    cleaned = sanitize_html(safe_html)
    assert "The 3 Pillars of PLG" in cleaned
    assert "Time to Value (TTV)" in cleaned
    assert "<table" in cleaned
    assert "background-color" in cleaned
    assert "border-radius" in cleaned


def test_sanitize_empty_and_none_input():
    assert sanitize_html("") == ""
    assert sanitize_html("   ") == ""
    assert sanitize_html(None) == ""
