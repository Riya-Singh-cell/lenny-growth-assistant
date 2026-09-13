# Design System & UI/UX Specification
# The Lenny Growth Assistant

## 1. UI/UX Principles

1. **Executive Clarity Over Toy Chatbot Novelty**: Designed as an internal product strategy tool for high-tempo decision makers, rather than a generic consumer chatbot.
2. **First-Class Grounding Visibility**: Evidence is not hidden behind a tiny tooltip. Citations feature episode titles, speaker attribution, timestamps, and direct YouTube video links.
3. **Artifact-Centric Productivity**: Deliverables (strategy documents, frameworks, HTML dashboards) live beside the conversation, allowing side-by-side iterative discussion and preview.
4. **Resilient Feedback Loops**: When services (Ollama, cloud LLMs, network) are offline or models are loading, the UI communicates clear diagnostic steps rather than infinite spinners or empty screens.

---

## 2. Information Architecture & Layout

The desktop application follows a three-panel split architecture:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ HEADER: Brand • Active Model (Ollama/Claude) • Health Dot • Diagnostics Button  │
├──────────────┬─────────────────────────────────┬────────────────────────────────┤
│ SIDEBAR      │ MAIN CHAT AREA                  │ ARTIFACT VIEWER (Collapsible)  │
│              │                                 │                                │
│ • New Chat   │ • Message Stream (Markdown)     │ • Title & Format Badge         │
│ • History    │ • Intent Badges                 │ • Preview / Source Tabs        │
│ • Session    │ • Collapsible Source Cards      │ • Sandboxed Iframe Preview     │
│   Titles     │ • Quick Suggestion Starters     │ • Raw Source Inspector         │
│ • Knowledge  │ • Multi-line Chat Composer      │ • Copy & Download Actions      │
│   Base Stats │                                 │ • Close Button                 │
└──────────────┴─────────────────────────────────┴────────────────────────────────┘
```

### Dimensions & Breakpoints
- **Sidebar**: Fixed 256px width (`w-64`), hidden on mobile viewports with toggle.
- **Main Chat**: Flexible width, max content width 896px (`max-w-4xl`) for optimal typographic readability (65-75 characters per line).
- **Artifact Viewer**: Fixed 480px to 560px on desktop (`w-[480px] lg:w-[560px]`), sliding in smoothly beside the chat when an artifact is generated.

---

## 3. Color System & Typography

- **Dark Theme Tokens**:
  - Background Canvas: `#0b0f19` (Deep Slate Navy)
  - Surface Card / Sidebar: `#0f172a` & `#1e293b`
  - Border Accents: `#334155`
  - Primary Brand Blue: `#2563eb` & `#3b82f6` (accent hover `#1d4ed8`)
  - Accent Indigo (Artifacts): `#6366f1`
  - Text Primary: `#f8fafc`
  - Text Secondary: `#94a3b8`
  - Success / Connected: `#10b981` (Emerald)
  - Warning / Degraded: `#f59e0b` (Amber)
  - Error / Offline: `#f43f5e` (Rose)

- **Typography**:
  - System font stack prioritizing crisp subpixel rendering: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`.
  - Monospace font stack for code, timestamps, and model tags: `"Fira Code", Monaco, Consolas, monospace`.

---

## 4. Key Interaction States (12 Intentional States)

1. **Empty Chat State**: Displays the assistant banner, purpose description, and four quick-action scenario cards ("Prioritizing Growth Experiments", "Adam Fishman on Onboarding", "Ship 30 Essay", "Visual HTML Framework").
2. **User Typing State**: Multi-line textarea expands up to 150px, keyboard shortcut prompt visible (`Enter` to submit, `Shift+Enter` for newline).
3. **Loading / Retrieval State**: Animated spinner card indicates: *"Consulting Lenny's Podcast transcripts & generating grounded response..."*
4. **Assistant Response State**: High-contrast Markdown with formatted headings, bullet lists, bold text, and code blocks.
5. **Intent Tagging**: Visual badges distinguish standard `Grounded Lenny Q&A`, `Ship 30 for 30 Skill`, and `Artifact Skill`.
6. **Sources Displayed State**: Collapsible drawer with source count pill. Expanding shows episode title, speaker, timestamp, direct YouTube playback button, and relevant snippet.
7. **Artifact Generated State**: Inline card in the chat indicates artifact creation with an *"Open in Artifact Viewer"* action button, automatically opening the side panel.
8. **Artifact Rendering Failure State**: If rendering fails, the viewer presents the raw sanitized source code with an export button.
9. **Ollama Unavailable State**: Header status dot turns amber, an error alert explains that Ollama is unreachable at `http://localhost:11434`, and provides the exact terminal command (`ollama serve`).
10. **Database Unavailable State**: Health indicator turns amber; backend automatically switches to local SQLite fallback without interrupting user workflow.
11. **No Relevant Transcript Evidence State**: Assistant honestly outputs: *"Based on the available Lenny's Podcast transcript material, there is insufficient evidence to directly answer this question."*
12. **Network Failure State**: Red alert banner with retry trigger.

---

## 5. Security & Artifact Sandbox Design

Untrusted HTML generated by LLMs is strictly prevented from executing arbitrary scripts in the parent window:
- **Server Sanitization**: Strips `<script>`, inline event handlers (`onclick`, `onload`), dangerous schemes (`javascript:`, `data:text/html`).
- **Client Iframe Sandbox**:
  ```html
  <iframe
    title="Artifact"
    srcDoc="<!DOCTYPE html>..."
    sandbox="allow-same-origin"
  />
  ```
  The sandbox forbids script execution (`allow-scripts` is intentionally omitted), cookie access, top-level navigation, and parent document DOM access.

---

## 6. Accessibility & Responsiveness

- Semantic HTML5 structure (`<header>`, `<aside>`, `<main>`, `<footer>`, `<button>`, `<textarea>`).
- Visible focus rings (`focus:ring-1 focus:ring-blue-500`) on all interactive inputs and buttons.
- Keyboard-operable tabs and modal dialogs with `Esc` key dismissal.
- High contrast ratios (exceeding WCAG 2.1 AA requirements) between text (`#f8fafc`) and dark surfaces (`#0f172a`).
