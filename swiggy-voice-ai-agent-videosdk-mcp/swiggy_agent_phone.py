"""
Swiggy Voice Agent (Phone) — powered by VideoSDK AI Agents.

Registers the agent with VideoSDK's telephony service for
inbound/outbound phone calls (SIP) and WhatsApp voice calls.

Setup:
  1. Run `./setup.sh` or `python swiggy_mcp.py` to login to Swiggy
  2. Configure SIP gateways and routing rules in VideoSDK Dashboard
  3. Run `python swiggy_agent_phone.py`

Docs:
  - Telephony: https://docs.videosdk.live/ai_agents/ai-phone-agent-quick-start
  - WhatsApp:  https://docs.videosdk.live/ai_agents/whatsapp-voice-agent-quick-start
"""

import asyncio
import logging

from videosdk.agents import (
    Agent,
    AgentSession,
    Pipeline,
    JobContext,
    RoomOptions,
    WorkerJob,
    Options,
)
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig

from instructions import SWIGGY_AGENT_INSTRUCTIONS, GREETING, GOODBYE
from swiggy_mcp import build_swiggy_mcp_servers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


class SwiggyPhoneAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=SWIGGY_AGENT_INSTRUCTIONS,
            mcp_servers=build_swiggy_mcp_servers(),
        )

    async def on_enter(self):
        await self.session.say(GREETING)

    async def on_exit(self):
        await self.session.say(GOODBYE)


async def entrypoint(ctx: JobContext):
    model = GeminiRealtime(
        model="gemini-3.1-flash-live-preview",
        config=GeminiLiveConfig(
            voice="Leda",
            response_modalities=["AUDIO"],
        ),
    )

    pipeline = Pipeline(llm=model)
    agent = SwiggyPhoneAgent()

    session = AgentSession(
        agent=agent,
        pipeline=pipeline,
    )

    await session.start(
        wait_for_participant=True,
        run_until_shutdown=True,
    )


def make_context() -> JobContext:
    return JobContext(room_options=RoomOptions())


if __name__ == "__main__":
    options = Options(
        agent_id="SwiggyVoiceAgent",
        register=True,
        max_processes=10,
        host="localhost",
        port=8081,
    )

    job = WorkerJob(
        entrypoint=entrypoint,
        jobctx=make_context,
        options=options,
    )
    job.start()
