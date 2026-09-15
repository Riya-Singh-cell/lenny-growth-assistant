# Objective

Preserve safe inline CSS in generated HTML artifacts while retaining the existing HTML allowlist and security restrictions.

# Agent Instruction

The coding agent was instructed to fix only the two failing HTML/CSS sanitization tests, use Bleach's supported CSS sanitizer mechanism, allow a narrow safe CSS property set, add the required dependency if missing, and avoid changing tests or unrelated application code.

# Agent Outcome

The initial test result was 38 passed and 2 failed:

- `tests/test_security.py::test_sanitize_preserves_safe_html_and_css`
- `tests/test_skills.py::test_artifact_skill_html_generation_and_sanitization`

Both failures showed that the `style` attribute survived as an empty attribute, so safe declarations such as `background-color` and `color: #2563eb;` were removed. Bleach also reported that a `style` attribute was specified without a CSS sanitizer.

The correction uses `bleach.css_sanitizer.CSSSanitizer` with an explicit allowlist of safe properties required by artifact cards and layouts, then passes that sanitizer to `bleach.clean()`. `tinycss2` is declared in the backend requirements because it is required by Bleach's CSS parsing path. Existing HTML tags, attributes, URL protocols, prohibited-element removal, event-handler removal, and CSS defanging rules were preserved.

# Verification

The two focused tests passed after the correction. The full backend suite then passed with 40 passed, 0 failed, and 26 warnings.

# Failure / Correction

- **Failure:** Safe inline styles were stripped, producing `style=""`.
- **Why:** Bleach was allowing the `style` attribute without a configured CSS sanitizer.
- **Correction requested:** Configure `CSSSanitizer` with a narrow property allowlist and pass it to `bleach.clean()`; ensure `tinycss2` is available.
- **Verification:** Both named tests passed and the full suite completed with 40 passing tests. The remaining warnings were existing framework deprecation warnings, not sanitizer failures.
