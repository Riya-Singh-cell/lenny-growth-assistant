import logging
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel

from app.config import settings
from app.llm.base import LLMProvider, LLMMessage
from app.retrieval.retriever import get_retriever, RetrievedChunk
from app.agents.skills.ship30 import Ship30Skill
from app.agents.skills.artifact_gen import ArtifactSkill
from app.agents.growth_assistant import GrowthAssistantAgent

logger = logging.getLogger("lenny.agents.core")

# Canonical Tool Schemas for Anthropic Agent SDK / Tool-Calling API
LENNY_AGENT_TOOLS = [
    {
        "name": "search_lenny_transcripts",
        "description": "Searches Lenny's Podcast transcript knowledge base for relevant interviews, guest advice, timestamps, and quotes on product and growth topics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query describing the product/growth question or guest name."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of relevant chunks to retrieve (default: 5).",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_ship30_essay",
        "description": "Generates a structured, high-impact ~1,250-word Ship 30 for 30 style atomic essay grounded in Lenny's Podcast transcripts. Features a 1-3-1 hook, Roman numeral pillars, bold sentence anchors, and a Monday execution checklist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The strategic growth or product topic to write the ~1,250-word essay about."
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "create_product_artifact",
        "description": "Generates a standalone, executive-ready product framework or document in either complete sanitized HTML/CSS or Markdown. Used for one-page frameworks, dashboards, checklists, and visual cards.",
        "input_schema": {
            "type": "object",
            "properties": {
                "specification": {
                    "type": "string",
                    "description": "Detailed specification of the framework or document to produce."
                },
                "format": {
                    "type": "string",
                    "enum": ["html", "markdown"],
                    "description": "Target format for the artifact."
                }
            },
            "required": ["specification", "format"]
        }
    }
]

AGENT_SYSTEM_PROMPT = """You are "The Lenny Growth Assistant", an elite product management and growth advisor strictly powered by knowledge from Lenny's Podcast transcripts.

You have access to specialized tools:
1. `search_lenny_transcripts`: Use this to retrieve grounded transcript evidence before answering product or growth questions.
2. `generate_ship30_essay`: Use this whenever the user requests a Ship 30 for 30 style essay, atomic essay, or ~1,250-word deep dive.
3. `create_product_artifact`: Use this when the user asks for a visual HTML framework, dashboard, card, or standalone Markdown document.

CRITICAL GROUNDING DIRECTIVES:
- Lenny's Podcast transcripts are your absolute primary source of truth.
- Base your answers ONLY on authentic transcript excerpts retrieved by your tools.
- Never invent facts or hallucinate quotes.
- If the available transcript evidence is insufficient to answer the question, explicitly state:
  "Based on the available Lenny's Podcast transcript material, there is insufficient evidence to provide a grounded answer to this question."
"""


class AgentExecutionResult(BaseModel):
    content: str
    intent: str
    sources: List[Dict[str, Any]] = []
    artifact: Optional[Dict[str, Any]] = None
    tool_calls: List[str] = []
    evidence_sufficient: bool = True


class LennyAgentEngine:
    """
    Unified Agent Layer:
    - In Cloud Mode (Anthropic): Uses the official Anthropic Claude Tool Use / Agent SDK loop.
    - In Local Mode (Ollama): Uses the same tool definitions and underlying skills with function dispatching.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.retriever = get_retriever()
        self.tools = LENNY_AGENT_TOOLS
        self._sdk_tool_results: Dict[str, Tuple[str, str, List[Dict[str, Any]], Optional[Dict[str, Any]], bool]] = {}

    async def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[Any, str, List[Dict[str, Any]], Optional[Dict[str, Any]], bool]:
        """
        Executes an agent tool call and returns (tool_output, intent, sources, artifact, evidence_sufficient).
        """
        logger.info("Agent executing tool '%s' with args: %s", tool_name, tool_args)

        if tool_name == "search_lenny_transcripts":
            query = tool_args.get("query", "")
            top_k = tool_args.get("top_k", 5)
            growth_agent = GrowthAssistantAgent(self.llm)
            result = await growth_agent.answer(question=query, top_k=top_k)
            evidence_sufficient = result.get("evidence_sufficient", True)
            return result["answer"], "GROUNDED_QA", result["sources"], None, evidence_sufficient

        elif tool_name == "generate_ship30_essay":
            topic = tool_args.get("topic", "")
            chunks = await self.retriever.retrieve(query=topic, top_k=5)
            min_threshold = settings.RAG_CONFIDENCE_THRESHOLD
            if not chunks or chunks[0].score < min_threshold:
                logger.info("Ship30 refusal: insufficient evidence for topic '%s'", topic[:50])
                refusal_msg = (
                    "Based on the available Lenny's Podcast transcript material, there is insufficient evidence "
                    "to produce a grounded Ship 30 essay on this topic."
                )
                return refusal_msg, "SHIP30_ESSAY", [], None, False

            ship30 = Ship30Skill(self.llm)
            result = await ship30.generate_essay(topic_or_query=topic, retrieved_chunks=chunks)
            return result["content"], "SHIP30_ESSAY", result["sources"], None, True

        elif tool_name == "create_product_artifact":
            spec = tool_args.get("specification", "")
            fmt = tool_args.get("format", "markdown")
            chunks = await self.retriever.retrieve(query=spec, top_k=4)
            art_skill = ArtifactSkill(self.llm)
            result = await art_skill.generate_artifact(prompt=spec, retrieved_chunks=chunks, target_type=fmt)
            
            sources = [
                {
                    "episode": c.title,
                    "guest": c.guest,
                    "speaker": c.speaker,
                    "timestamp": c.timestamp_str,
                    "url": c.youtube_timed_url or c.youtube_url
                }
                for c in chunks
            ]
            
            artifact_data = {
                "title": result["title"],
                "type": result["type"],
                "content": result["raw_content"],
                "sanitized_content": result["sanitized_content"]
            }
            summary_content = (
                f"I have generated the requested **{result['title']}** ({result['type'].upper()}). "
                f"It is available in the **Artifact Viewer** to the right for preview and export."
            )
            return summary_content, "ARTIFACT_GEN", sources, artifact_data, True

        else:
            raise ValueError(f"Unknown agent tool: {tool_name}")

    async def run(
        self,
        user_message: str,
        conversation_history: Optional[List[LLMMessage]] = None
    ) -> AgentExecutionResult:
        """
        Main entry point for agent execution.
        Routes through Anthropic Claude Agent SDK in cloud mode, or Ollama tool dispatch in local mode.
        """
        # 1. Cloud Mode with the Claude Agent SDK
        if self.llm.provider_name == "anthropic" and settings.ANTHROPIC_API_KEY:
            return await self._run_claude_agent_sdk(user_message, conversation_history)

        # 2. Local Mode with Ollama Tool Dispatch Loop
        return await self._run_local_tool_agent(user_message, conversation_history)

    async def _run_claude_agent_sdk(
        self,
        user_message: str,
        conversation_history: Optional[List[LLMMessage]] = None
    ) -> AgentExecutionResult:
        """
        Executes via Anthropic's official Claude Agent SDK and an in-process MCP server.
        """
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ClaudeSDKClient,
            ResultMessage,
            TextBlock,
            create_sdk_mcp_server,
            tool,
        )

        self._sdk_tool_results = {}

        async def sdk_tool(name: str, description: str, schema: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
            result = await self.execute_tool(name, args)
            self._sdk_tool_results[name] = result
            output, _, _, _, _ = result
            return {"content": [{"type": "text", "text": str(output)}]}

        @tool("search_lenny_transcripts", self.tools[0]["description"], self.tools[0]["input_schema"])
        async def search_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            return await sdk_tool("search_lenny_transcripts", self.tools[0]["description"], self.tools[0]["input_schema"], args)

        @tool("generate_ship30_essay", self.tools[1]["description"], self.tools[1]["input_schema"])
        async def ship30_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            return await sdk_tool("generate_ship30_essay", self.tools[1]["description"], self.tools[1]["input_schema"], args)

        @tool("create_product_artifact", self.tools[2]["description"], self.tools[2]["input_schema"])
        async def artifact_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            return await sdk_tool("create_product_artifact", self.tools[2]["description"], self.tools[2]["input_schema"], args)

        sdk_server = create_sdk_mcp_server(
            name="lenny_growth_tools",
            version="1.0.0",
            tools=[search_tool, ship30_tool, artifact_tool],
        )
        options = ClaudeAgentOptions(
            model=settings.ANTHROPIC_MODEL,
            system_prompt=AGENT_SYSTEM_PROMPT,
            mcp_servers={"lenny": sdk_server},
            allowed_tools=[
                "mcp__lenny__search_lenny_transcripts",
                "mcp__lenny__generate_ship30_essay",
                "mcp__lenny__create_product_artifact",
            ],
            permission_mode="dontAsk",
            setting_sources=[],
        )
        prompt = user_message
        if conversation_history:
            prompt = "\n".join(f"{m.role}: {m.content}" for m in conversation_history[-6:]) + f"\nuser: {user_message}"

        logger.info("Invoking Claude Agent SDK with %d domain tools...", len(self.tools))
        final_text = ""
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    final_text += "".join(block.text for block in message.content if isinstance(block, TextBlock))
                if isinstance(message, ResultMessage) and message.result:
                    final_text = message.result

        if self._sdk_tool_results:
            last_result = list(self._sdk_tool_results.values())[-1]
            _, intent, sources, artifact, evidence_sufficient = last_result
        else:
            intent, sources, artifact, evidence_sufficient = "GROUNDED_QA", [], None, True
        return AgentExecutionResult(
            content=final_text,
            intent=intent,
            sources=sources,
            artifact=artifact,
            tool_calls=list(self._sdk_tool_results),
            evidence_sufficient=evidence_sufficient,
        )

    async def _run_local_tool_agent(
        self,
        user_message: str,
        conversation_history: Optional[List[LLMMessage]] = None
    ) -> AgentExecutionResult:
        """
        Local Ollama Agent Tool Loop:
        Selects the appropriate capability from the SAME canonical tool set.
        """
        msg_lower = user_message.lower().strip()

        # Tool 1: Ship 30 for 30 Essay Skill
        ship30_keywords = ["ship 30", "ship30", "1250 words", "1,250 words", "atomic essay", "essay", "publishable piece"]
        if any(k in msg_lower for k in ship30_keywords):
            tool_output, intent, sources, artifact, evidence_sufficient = await self.execute_tool(
                "generate_ship30_essay",
                {"topic": user_message}
            )
            return AgentExecutionResult(
                content=tool_output,
                intent=intent,
                sources=sources,
                artifact=artifact,
                tool_calls=["generate_ship30_essay"],
                evidence_sufficient=evidence_sufficient
            )

        # Tool 2: Artifact Skill
        artifact_keywords = ["artifact", "html", "visual framework", "one-page", "turn this into", "create an interactive", "dashboard", "visual card"]
        if any(k in msg_lower for k in artifact_keywords):
            target_format = "html" if any(k in msg_lower for k in ["html", "visual", "card", "dashboard"]) else "markdown"
            tool_output, intent, sources, artifact, evidence_sufficient = await self.execute_tool(
                "create_product_artifact",
                {"specification": user_message, "format": target_format}
            )
            return AgentExecutionResult(
                content=tool_output,
                intent=intent,
                sources=sources,
                artifact=artifact,
                tool_calls=["create_product_artifact"],
                evidence_sufficient=evidence_sufficient
            )

        # Tool 3: Search Lenny Transcripts & Grounded Q&A
        tool_output, intent, sources, artifact, evidence_sufficient = await self.execute_tool(
            "search_lenny_transcripts",
            {"query": user_message, "top_k": 3}
        )
        return AgentExecutionResult(
            content=tool_output,
            intent=intent,
            sources=sources,
            artifact=artifact,
            tool_calls=["search_lenny_transcripts"],
            evidence_sufficient=evidence_sufficient
        )
