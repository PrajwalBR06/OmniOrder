"""
================================================================
 OmniOrder - Channel Ingestion Agent  (AGENT #2)
================================================================
Turns ANY channel input into clean plain text, then forwards it
to the Intent agent.

Handles:
  - WhatsApp / email text  -> passed through
  - WhatsApp VOICE note     -> transcribe()  (stub; plug in Whisper/any STT)
  - WhatsApp IMAGE / photo  -> ocr()         (stub; plug in Tesseract/vision)
  - Phone CALL recording    -> transcribe()

For the hackathon MVP, text works out of the box. The voice/image
functions are clearly marked stubs you can wire to a real API later.

Run:  python agents/ingestion_agent.py
================================================================
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low

from shared.models import RawMessage
from shared import config
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
agent = Agent(
    name="omniorder_ingestion",
    seed="omniorder-ingestion-7k2mp4-2026",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)
fund_agent_if_low(agent.wallet.address())


# ---------------- Media helpers (stubs to extend) ----------------
def transcribe(audio_ref: str) -> str:
    """
    STUB: convert a voice note / call recording into text.
    Plug in OpenAI Whisper, Deepgram, or Google STT here.
    For the demo, you can drop a pre-transcribed string instead.
    """
    # Example (pseudo):
    #   import openai; openai.audio.transcriptions.create(...)
    return audio_ref  # treat the passed text as already-transcribed for MVP


def ocr(image_ref: str) -> str:
    """
    STUB: read a handwritten list / product photo into text.
    Plug in Tesseract (pytesseract) or a vision model here.
    """
    return image_ref  # treat the passed text as already-OCR'd for MVP


@agent.on_message(model=RawMessage)
async def ingest(ctx: Context, sender: str, msg: RawMessage):
    ctx.logger.info(f"[Ingestion] Received via {msg.channel} from {msg.sender}")

    text = msg.text
    # If your channel layer tags media type, route it here:
    if msg.text.startswith("[voice]"):
        text = transcribe(msg.text.replace("[voice]", "").strip())
    elif msg.text.startswith("[image]"):
        text = ocr(msg.text.replace("[image]", "").strip())

    normalized = RawMessage(
        channel=msg.channel,
        sender=msg.sender,
        text=text,
        customer_name=msg.customer_name,
    )
    ctx.logger.info(f"[Ingestion] Normalized text -> {text}")
    await ctx.send(config.INTENT_ADDRESS, normalized)


if __name__ == "__main__":
    print("Ingestion address:", agent.address)
    agent.run()
