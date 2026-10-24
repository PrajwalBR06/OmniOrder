"""
================================================================
 OmniOrder - Intent Agent  (AGENT #3, the "understanding" brain)
================================================================
Uses ASI:One to turn a messy order message into a clean,
structured order (customer, items, quantities, delivery).
If something important is missing, it asks a clarifying question.

Run:  python agents/intent_agent.py
================================================================
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from uagents import Agent
import json
from openai import OpenAI

from uagents import Agent, Context
from uagents.setup import fund_agent_if_low

from shared.models import RawMessage, StructuredOrder, LineItem
from shared import config
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
agent = Agent(
    name="omniorder_intent",
    seed="omniorder-intent-4w8qz1-2026",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"],
)
fund_agent_if_low(agent.wallet.address())

# ASI:One is OpenAI-API-compatible, so we use the OpenAI client pointed at it.
client = OpenAI(api_key=config.ASI_ONE_API_KEY, base_url=config.ASI_ONE_BASE_URL)

catalog = config.load_catalog()
CATALOG_KEYS = list(catalog["items"].keys())

SYSTEM_PROMPT = f"""You are an order-extraction assistant for a furniture shop.
From the customer's message, extract a JSON object with EXACTLY these keys:
- customer_name (string, "" if unknown)
- items: list of {{ "key": <one of {CATALOG_KEYS}>, "quantity": <int> }}
- delivery_address (string, "" if not given)
- delivery_date (string, "" if not given)
- clarifying_questions: list of short strings (empty if nothing is missing)

Rules:
- Map synonyms/Hindi words to the closest catalog key (kursi=chair, mez=table, almirah=wardrobe).
- If the customer mentions an item NOT in {CATALOG_KEYS}, add a clarifying question instead of guessing.
- If quantity is vague ("a couple", "some"), add a clarifying question.
- Return ONLY valid JSON, no extra text.
"""


def extract_order(text: str) -> dict:
    resp = client.chat.completions.create(
        model=config.ASI_ONE_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    content = resp.choices[0].message.content.strip()
    # Be forgiving if the model wraps JSON in ```.
    if content.startswith("```"):
        content = content.strip("`").replace("json", "", 1).strip()
    return json.loads(content)


@agent.on_message(model=RawMessage)
async def understand(ctx: Context, sender: str, msg: RawMessage):
    ctx.logger.info(f"[Intent] Understanding: {msg.text}")
    try:
        data = extract_order(msg.text)
    except Exception as e:
        ctx.logger.error(f"[Intent] ASI:One parse failed: {e}")
        data = {"customer_name": "", "items": [], "delivery_address": "",
                "delivery_date": "", "clarifying_questions": ["Could you repeat your order clearly?"]}

    items = []
    for it in data.get("items", []):
        key = it.get("key", "")
        name = catalog["items"].get(key, {}).get("name", key)
        items.append(LineItem(key=key, name=name, quantity=int(it.get("quantity", 1))))

    questions = data.get("clarifying_questions", [])
    if not items and not questions:
        questions = ["I couldn't find any items in your order. What would you like to buy?"]

    order = StructuredOrder(
        channel=msg.channel,
        sender=msg.sender,
        customer_name=data.get("customer_name") or (msg.customer_name or "Customer"),
        items=items,
        delivery_address=data.get("delivery_address", ""),
        delivery_date=data.get("delivery_date", ""),
        clarifying_questions=questions,
        needs_clarification=bool(questions),
    )
    ctx.logger.info(f"[Intent] Structured -> {order.customer_name}, {len(items)} item(s), "
                    f"clarify={order.needs_clarification}")
    await ctx.send(config.COORDINATOR_ADDRESS, order)


if __name__ == "__main__":
    print("Intent address:", agent.address)
    agent.run()
