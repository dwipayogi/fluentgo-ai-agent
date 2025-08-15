from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    groq,
    silero,
    noise_cancellation
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="Anda adalah penerjemah AI yang membantu. Terjemahkan semua yang dikatakan pengguna dari Bahasa Indonesia ke Bahasa Inggris atau sebaliknya. Jangan tambahkan kata-kata lain selain terjemahan dari pernyataan pengguna.")

async def entrypoint(ctx: agents.JobContext):
    
    agent = AgentSession(
        stt=groq.STT(model="whisper-large-v3-turbo"),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=groq.TTS(voice="Cheyenne-PlayAI"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await agent.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await agent.generate_reply(
        instructions="Sapa pengguna dan kenalkan diri anda dan tawarkan bantuan."
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))