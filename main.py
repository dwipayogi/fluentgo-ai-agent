from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    noise_cancellation
)
from livekit.plugins import google

load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="Anda adalah penerjemah AI. Terjemahkan semua yang dikatakan pengguna dari Bahasa Indonesia ke Bahasa Inggris atau sebaliknya. Jangan tambahkan kata-kata lain selain terjemahan dari pernyataan pengguna.")

async def entrypoint(ctx: agents.JobContext):
    
    agent = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            temperature=0.8,
            instructions="Anda adalah penerjemah AI. Terjemahkan semua yang dikatakan pengguna dari Bahasa Indonesia ke Bahasa Inggris atau sebaliknya. Jangan tambahkan kata-kata lain selain terjemahan dari pernyataan pengguna.",
        ),
    )

    await agent.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            text_enabled=True,
            audio_enabled=True,
            video_enabled=True,
        ),
    )

    await agent.generate_reply(
        instructions="Sapa pengguna dan kenalkan diri anda dan tawarkan bantuan."
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))