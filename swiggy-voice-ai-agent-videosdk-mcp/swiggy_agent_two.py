"""
Swiggy Voice Agent Two — powered by VideoSDK AI Agents.

Uses Gemini native audio for the lowest latency voice experience.
Single model handles STT + LLM + TTS — minimal setup, fastest response.
Only requires VideoSDK + Google API keys.

Run: python swiggy_agent_two.py
Then open: https://playground.videosdk.live
"""

from videosdk.agents import (
    Agent,
    AgentSession,
    RealTimePipeline,
    JobContext,
    RoomOptions,
    WorkerJob,
)
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig

from instructions import SWIGGY_AGENT_INSTRUCTIONS, GREETING, GOODBYE
from swiggy_mcp import build_swiggy_mcp_servers

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


class SwiggyVoiceAgent(Agent):
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
        model="gemini-2.5-flash-native-audio-preview-09-2025",
        config=GeminiLiveConfig(
            voice="Leda",
            response_modalities=["AUDIO"],
        ),
    )

    pipeline = RealTimePipeline(model=model)
    agent = SwiggyVoiceAgent()

    session = AgentSession(
        agent=agent,
        pipeline=pipeline,
    )

    await session.start(
        wait_for_participant=True,
        run_until_shutdown=True,
    )


def make_context() -> JobContext:
    return JobContext(
        room_options=RoomOptions(
            name="Swiggy Voice Agent",
            playground=True,
        )
    )


if __name__ == "__main__":
    job = WorkerJob(
        entrypoint=entrypoint,
        jobctx=make_context,
    )
    job.start()
