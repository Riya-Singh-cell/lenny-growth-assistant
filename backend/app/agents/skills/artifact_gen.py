import re
import logging
from typing import List, Dict, Any, Optional
from app.llm.base import LLMProvider, LLMMessage
from app.retrieval.retriever import RetrievedChunk
from app.security.sanitizer import sanitize_html

logger = logging.getLogger("lenny.skills.artifact_gen")

ARTIFACT_SYSTEM_PROMPT = """You are an expert product architect and UI designer specializing in high-density executive frameworks and visual artifacts for product leaders and founders.

Your job is to generate either a complete, beautifully styled HTML/CSS artifact OR an exhaustive Markdown artifact based on user requests and transcript evidence.

GUIDELINES FOR ARTIFACT GENERATION:
1. **Format Selection**:
   - If the user asks for HTML, visual, card, interactive layout, or dashboard: output complete self-contained HTML with embedded `<style>` block.
   - If the user asks for Markdown or a document: output structured, high-density Markdown with tables, callout blocks, and checklists.
2. **HTML/CSS Visual Standards**:
   - Modern, executive aesthetic (dark slate/navy or crisp light theme, clean typography, rounded cards, subtle borders, flex/grid layouts).
   - Zero JavaScript (do NOT write `<script>` tags or event handlers; use semantic CSS for styling).
   - Self-contained and responsive.
3. **Strict Grounding**:
   - All framework metrics, heuristics, and principles must be grounded in the provided Lenny Podcast transcript sources.
4. **Output Tagging**:
   - Wrap your complete generated artifact in standard triple backticks with either `html` or `markdown` syntax tag.
   - For HTML: ```html\n<div class="artifact-container">...</div>\n```
   - For Markdown: ```markdown\n# Title\n...```
"""


class ArtifactSkill:
    """
    Dedicated skill for generating isolated Markdown or styled HTML/CSS artifacts.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate_artifact(
        self,
        prompt: str,
        retrieved_chunks: List[RetrievedChunk],
        target_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates an artifact, sanitizes it, and returns structured metadata.
        """
        # Determine format if not explicitly set
        if not target_type:
            if any(k in prompt.lower() for k in ["html", "visual", "card", "dashboard", "css"]):
                target_type = "html"
            else:
                target_type = "markdown"

        context_summary = "\n\n".join([
            f"From {c.title} (Guest: {c.guest or 'Lenny'}):\n{c.text[:400]}..."
            for c in retrieved_chunks[:4]
        ])

        user_content = f"""Generate a comprehensive product artifact for:
"{prompt}"

Target Format: {target_type.upper()}

GROUNDED TRANSCRIPT CONTEXT:
============================
{context_summary or 'Use standard Lenny Podcast growth heuristics.'}
============================

Requirements:
- If HTML: Include modern styling in a <style> block. Do not use <script>.
- If Markdown: Include clear sections, comparative tables, and checklists.
- Make it immediately actionable and visually clean.
"""

        messages = [LLMMessage(role="user", content=user_content)]

        logger.info("ArtifactSkill generating %s artifact with '%s'", target_type, self.llm.provider_name)
        response = await self.llm.generate(
            messages=messages,
            system_prompt=ARTIFACT_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=2500
        )

        raw_output = response.content

        # Extract artifact code from code fences if present
        artifact_content = raw_output
        title = "Growth Framework Artifact"

        # Try to extract code fence
        code_fence_pattern = re.compile(r"```(?:html|markdown)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
        match = code_fence_pattern.search(raw_output)
        if match:
            artifact_content = match.group(1).strip()

        # Extract title if possible
        title_match = re.search(r"<h[12][^>]*>(.*?)</h[12]>", artifact_content, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r"^#\s+(.+)$", artifact_content, re.MULTILINE)
        if title_match:
            title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()

        # Sanitize if HTML
        sanitized_content = None
        if target_type == "html":
            sanitized_content = sanitize_html(artifact_content)
        else:
            sanitized_content = artifact_content

        return {
            "title": title[:100],
            "type": target_type,
            "raw_content": artifact_content,
            "sanitized_content": sanitized_content,
            "provider": self.llm.provider_name,
            "model": self.llm.model_name
        }
