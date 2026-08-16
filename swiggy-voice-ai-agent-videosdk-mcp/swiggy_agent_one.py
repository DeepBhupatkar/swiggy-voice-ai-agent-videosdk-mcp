"""
Swiggy Voice Agent One — powered by VideoSDK AI Agents.

Multi-provider pipeline: Deepgram STT + Google Gemini LLM + Cartesia TTS.
Richer voice quality with fine-grained control over each stage.
Requires VideoSDK + Google + Deepgram + Cartesia API keys.

Run: python swiggy_agent_one.py
Then open: https://playground.videosdk.live
"""

from videosdk.agents import (
    Agent,
    AgentSession,
    Pipeline,
    JobContext,
    RoomOptions,
    WorkerJob
)
from videosdk.agents.plugins import GoogleLLM, DeepgramSTT, CartesiaTTS, SileroVAD
from videosdk.agents.inference import TurnV2


from instructions import SWIGGY_AGENT_INSTRUCTIONS, GREETING, GOODBYE
from swiggy_mcp import build_swiggy_mcp_servers

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

pre_download_model()


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
    agent = SwiggyVoiceAgent()

    pipeline = Pipeline(
        stt=DeepgramSTT(),
        llm=GoogleLLM(),
        tts=CartesiaTTS(),
        vad=SileroVAD(),
        turn_detector=TurnV2(),
    )

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
