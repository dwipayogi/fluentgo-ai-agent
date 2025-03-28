from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    JobProcess,
    AutoSubscribe,
    metrics,
)
from livekit.agents.llm import (
    ChatContext,
    ChatMessage,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import silero, groq
from langdetect import detect

from dotenv import load_dotenv

load_dotenv()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

    print(f"connected to room : {ctx.room.name}\nwith participant : {participant.identity}")

    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content="You are a professional translator. The user will speak in Indonesian. Translate everything they say into fluent, natural English. Do not explain or add anything. Just translate only.",
            )
        ]
    )

    # 🎯 Custom agent to handle translation
    class TranslatorVoiceAgent(VoicePipelineAgent):
        async def process_user_text(self, text: str) -> str:
            print(f"[User Input]: {text}")

            if len(text.strip().split()) < 2:
                return ""

            try:
                detected_lang = detect(text)
            except Exception as e:
                print(f"[LangDetect Error]: {e}")
                return ""  # skip on error

            print(f"[Detected Language]: {detected_lang}")

            if detected_lang == "en":
                print("[Skip] Input already in English.")
                return ""  # Don't respond if it's already English

            # Otherwise, translate
            translation = await self.llm_respond(text)
            print(f"[Translation 🇬🇧]: {translation}")

            return translation

    agent = TranslatorVoiceAgent(
        vad=ctx.proc.userdata["vad"],
        stt=groq.STT(),
        llm=groq.LLM(),
        tts=groq.TTS(voice="Cheyenne-PlayAI"),
        chat_ctx=initial_ctx,
    )

    @agent.on("metrics_collected")
    def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
        metrics.log_metrics(mtrcs)

    agent.start(ctx.room)
    await agent.say("Hello, I am your translator. Please speak in Indonesian and I will translate your words into fluent English.", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="indo-to-english-translator",
        )
    )
