from livekit.agents import (
  JobContext,
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
import asyncio
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def prewarm(proc: JobProcess):
  # Preload VAD model to improve startup time
  proc.userdata["vad"] = silero.VAD.load()

async def auto_leave_if_empty(ctx: JobContext, check_interval: int = 10):
  """Monitor room and disconnect if empty"""
  while True:
    try:
      await asyncio.sleep(check_interval)
      participants = ctx.room.participants
      visible_users = [p for p in participants.values() if not p.is_hidden]

      if len(visible_users) <= 1:
        logger.info("Room empty, leaving...")
        await ctx.room.disconnect()
        break
    except Exception as e:
      logger.error(f"Error in auto_leave_if_empty: {e}")

class TranslatorVoiceAgent(VoicePipelineAgent):
  async def process_user_text(self, text: str) -> str:
    if not text.strip():
      return ""
      
    logger.info(f"[🇮🇩 INPUT]: {text}")
    try:
      translation = await self.llm_respond(text)
      logger.info(f"[🇬🇧 TRANSLATED]: {translation}")
      return translation
    except Exception as e:
      logger.error(f"Translation failed: {e}")
      return text

async def entrypoint(ctx: JobContext):
  try:
    await ctx.connect(
      auto_subscribe=AutoSubscribe.AUDIO_ONLY,
      identity="fluentgo-translator-bot",
      name="FluentGo Translator",
      hidden=False,
      metadata='{"bot": true}',
      role="participant"
    )
    
    await ctx.wait_for_participant()
    
    initial_ctx = ChatContext(
      messages=[
        ChatMessage(
          role="system",
          content="You are a professional translator. The user will speak in Indonesian. Translate everything they say into fluent, natural English. Do not explain or add anything. Just translate only.",
        )
      ]
    )
    
    # Use the custom agent class defined earlier
    agent = TranslatorVoiceAgent(
      vad=ctx.proc.userdata.get("vad") or silero.VAD.load(),
      stt=groq.STT(),
      llm=groq.LLM(),
      tts=groq.TTS(voice="Cheyenne-PlayAI"),
      chat_ctx=initial_ctx,
    )
    
    @agent.on("metrics_collected")
    def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
      metrics.log_metrics(mtrcs)
    
    agent.start(ctx.room)
    
    # Start both background tasks
    auto_leave_task = asyncio.create_task(auto_leave_if_empty(ctx))
    auto_shutdown_task = asyncio.create_task(auto_shutdown(ctx, timeout=600))  # 10 minutes
    
    await agent.say("Hello, I am ready to translate your conversation", allow_interruptions=True)
    
    # Wait for either task to complete
    done, pending = await asyncio.wait(
      [auto_leave_task, auto_shutdown_task], 
      return_when=asyncio.FIRST_COMPLETED
    )
    
    # Cancel remaining tasks
    for task in pending:
      task.cancel()
      
  except Exception as e:
    logger.error(f"Error in entrypoint: {e}")
    await ctx.room.disconnect()

async def auto_shutdown(ctx: JobContext, timeout: int = 600):
  """Auto shutdown after inactivity"""
  await asyncio.sleep(timeout)
  logger.info("Inactive too long. Leaving...")
  await ctx.room.disconnect()