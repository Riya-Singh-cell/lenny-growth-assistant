import re
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger("lenny.agent.router")


class AgentIntent(str, Enum):
    GROUNDED_QA = "GROUNDED_QA"
    SHIP30_ESSAY = "SHIP30_ESSAY"
    ARTIFACT_GEN = "ARTIFACT_GEN"


class IntentRouter:
    """
    Classifies user message intent into distinct agent/skill pathways:
    - GROUNDED_QA: Standard grounded Lenny Podcast Q&A
    - SHIP30_ESSAY: Specialized ~1,250 word Ship 30 for 30 essay generation
    - ARTIFACT_GEN: Isolated Markdown or HTML/CSS document/framework generation
    """

    def __init__(self):
        self.ship30_triggers = [
            r"\bship\s*30\b",
            r"\bship30\b",
            r"\b1,?250\s*words?\b",
            r"\bessay\b",
            r"\batomic essay\b",
            r"\blong-form article\b",
            r"\bpublishable (?:post|piece|essay)\b"
        ]

        self.artifact_triggers = [
            r"\bartifact\b",
            r"\bhtml(?:\/css)?\b",
            r"\bvisual framework\b",
            r"\bone-page (?:framework|summary|cheatsheet)\b",
            r"\bturn this into (?:an? )?(?:html|markdown|document|artifact)\b",
            r"\bcreate (?:an? )?(?:interactive|visual|html|standalone) (?:framework|card|dashboard|document)\b",
            r"\bgenerate (?:an? )?artifact\b",
            r"\binteractive widget\b"
        ]

    def route(self, message: str) -> AgentIntent:
        msg_lower = message.lower().strip()

        # Check Ship30 triggers first
        for pattern in self.ship30_triggers:
            if re.search(pattern, msg_lower):
                logger.info("IntentRouter classified message as SHIP30_ESSAY (pattern='%s')", pattern)
                return AgentIntent.SHIP30_ESSAY

        # Check Artifact triggers
        for pattern in self.artifact_triggers:
            if re.search(pattern, msg_lower):
                logger.info("IntentRouter classified message as ARTIFACT_GEN (pattern='%s')", pattern)
                return AgentIntent.ARTIFACT_GEN

        # Default to Grounded Q&A
        logger.info("IntentRouter classified message as GROUNDED_QA")
        return AgentIntent.GROUNDED_QA
