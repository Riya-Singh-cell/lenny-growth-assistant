import pytest
from app.security.sanitizer import sanitize_html


def test_sanitize_removes_script_tags():
    malicious = "<div><h1>Growth Framework</h1><script>alert('pwned');</script><p>Safe text</p></div>"
    cleaned = sanitize_html(malicious)
    assert "<script>" not in cleaned
    assert "alert('pwned')" not in cleaned
    assert "Growth Framework" in cleaned
    assert "Safe text" in cleaned


def test_sanitize_removes_onclick_and_onload_handlers():
    malicious = '<div onload="evilLoad()"><button onclick="stealCookies()" onmouseover="hack()">Click</button></div>'
    cleaned = sanitize_html(malicious)
    assert "onclick" not in cleaned.lower()
    assert "onload" not in cleaned.lower()
    assert "onmouseover" not in cleaned.lower()
    assert "stealCookies" not in cleaned
    assert "evilLoad" not in cleaned


def test_sanitize_blocks_javascript_protocol():
    malicious = '<a href="javascript:alert(1)">Click Me</a><a href="JAVASCRIPT:alert(2)">Capitalized</a>'
    cleaned = sanitize_html(malicious)
    assert "javascript:" not in cleaned.lower()


def test_sanitize_blocks_data_text_html():
    malicious = '<a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">Payload</a>'
    cleaned = sanitize_html(malicious)
    assert "data:text/html" not in cleaned.lower()


def test_sanitize_strips_svg_event_handlers():
    malicious = (
        '<svg onload="alert(\'svg_xss\')" width="100" height="100">'
        '<circle cx="50" cy="50" r="40" onmouseover="hackCircle()" />'
        '<animate attributeName="href" values="javascript:alert(1)" />'
        '</svg>'
    )
    cleaned = sanitize_html(malicious)
    assert "onload" not in cleaned.lower()
    assert "onmouseover" not in cleaned.lower()
    assert "hackCircle" not in cleaned
    assert "<animate" not in cleaned.lower()
    assert "javascript:" not in cleaned.lower()


def test_sanitize_strips_dangerous_iframe_content():
    malicious = '<div><h3>Card</h3><iframe src="https://attacker.com/malicious.html">Fallback text</iframe></div>'
    cleaned = sanitize_html(malicious)
    assert "<iframe" not in cleaned.lower()
    assert "attacker.com" not in cleaned


def test_sanitize_handles_entity_encoded_payloads():
    # HTML decimal and hex entity encoded javascript: payloads
    malicious = '<a href="jav&#x09;ascript:alert(1)">Link 1</a><a href="&#106;&#97;vascript:alert(2)">Link 2</a>'
    cleaned = sanitize_html(malicious)
    assert "javascript:" not in cleaned.lower()
    assert "alert(1)" not in cleaned
    assert "alert(2)" not in cleaned


def test_sanitize_blocks_css_edge_cases():
    # expression(), @import, and behavior:
    malicious = """
    <style>
      @import url('https://evil.com/style.css');
      body { width: expression(alert('xss')); behavior: url(evil.htc); }
      .bg { background: url('javascript:alert(1)'); }
    </style>
    <div style="width: expression(alert(2));">Test</div>
    """
    cleaned = sanitize_html(malicious)
    assert "@import" not in cleaned
    assert "expression(" not in cleaned.lower()
    assert "behavior:" not in cleaned.lower()
    assert "javascript:" not in cleaned.lower()


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
