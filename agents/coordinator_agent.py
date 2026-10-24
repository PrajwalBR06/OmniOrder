"""
================================================================
 OmniOrder - Coordinator Agent  (AGENT #1, the "brain")
================================================================
This is the agent you register on Agentverse and that ASI:One talks to.

What it does:
  1. Implements the Agent Chat Protocol  -> so ASI:One can discover & chat with it.
  2. Receives an order message (from ASI:One chat OR from a channel).
  3. Routes it through the pipeline:
        Ingestion -> Intent -> Invoice -> Payment
  4. Tracks order status and reports back to the user.

Run:  python agents/coordinator_agent.py
================================================================
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low

# The standard Agent Chat Protocol (required for ASI:One compatibility)
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    chat_protocol_spec,
)

from shared.models import RawMessage, StructuredOrder, Invoice, PaymentRequest, PaymentResult, Ack
from shared import config
import asyncio
from uagents import Agent
import asyncio


try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


agent = Agent(
    name="omniorder_coordinator",
    seed="omniorder-coordinator-9f3ax7-2026",
    port=8000,
    mailbox=True,
)
fund_agent_if_low(agent.wallet.address())

# In-memory order tracker:  sender -> last known status
ORDERS = {}

# ---------------------------------------------------------------
# 1) AGENT CHAT PROTOCOL  (this is what ASI:One speaks)
# ---------------------------------------------------------------
chat_proto = Protocol(spec=chat_protocol_spec)


@chat_proto.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    """A human (via ASI:One) sent us a chat message = an order in plain text."""
    # Acknowledge receipt (required by the protocol)
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))

    # Pull the text out of the chat message
    text = " ".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()
    if not text:
        return

    ctx.logger.info(f"[Coordinator] New chat order from {sender}: {text}")

    # Remember who to reply to on ASI:One
    ctx.storage.set("asi_user", sender)

    # Kick off the pipeline by sending to the Ingestion agent
    raw = RawMessage(channel="whatsapp", sender=sender, text=text)
    await ctx.send(config.INGESTION_ADDRESS, raw)


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"[Coordinator] Chat ack from {sender}")


async def reply_to_user(ctx: Context, text: str):
    """Send a text reply back to the ASI:One user."""
    user = ctx.storage.get("asi_user")
    if not user:
        ctx.logger.info(f"[Coordinator] (no ASI user) -> {text}")
        return
    await ctx.send(user, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    ))


# ---------------------------------------------------------------
# 2) PIPELINE ROUTING  (internal agent-to-agent messages)
# ---------------------------------------------------------------

# A channel adapter (WhatsApp/email) can also push orders straight here.
@agent.on_message(model=RawMessage)
async def from_channel(ctx: Context, sender: str, msg: RawMessage):
    ctx.logger.info(f"[Coordinator] Channel order ({msg.channel}) from {msg.sender}")
    await ctx.send(config.INGESTION_ADDRESS, msg)


# Intent agent returns the structured order -> forward to Invoice agent
@agent.on_message(model=StructuredOrder)
async def got_structured(ctx: Context, sender: str, order: StructuredOrder):
    if order.needs_clarification:
        q = " ".join(order.clarifying_questions)
        await reply_to_user(ctx, f"Quick question before I make your bill: {q}")
        return
    ctx.logger.info(f"[Coordinator] Order understood for {order.customer_name}, pricing it...")
    await ctx.send(config.INVOICE_ADDRESS, order)


# Invoice agent returns a priced invoice -> ask Payment agent to collect money
@agent.on_message(model=Invoice)
async def got_invoice(ctx: Context, sender: str, inv: Invoice):
    ORDERS[inv.sender] = "pending"
    summary = ", ".join(f"{i.quantity}x {i.name}" for i in inv.items)
    await reply_to_user(
        ctx,
        f"Invoice {inv.invoice_id} created: {summary}. "
        f"Total {inv.currency} {inv.total:.2f} (incl. tax). "
        f"Sending you a payment link now..."
    )
    await ctx.send(config.PAYMENT_ADDRESS, PaymentRequest(invoice=inv))


# Payment agent reports the final result
@agent.on_message(model=PaymentResult)
async def got_payment(ctx: Context, sender: str, res: PaymentResult):
    ORDERS[res.sender] = res.status
    if res.status == "paid":
        await reply_to_user(
            ctx,
            f"Payment received for {res.invoice_id}. Your order is CONFIRMED and placed! "
            f"Thank you."
        )
    else:
        await reply_to_user(
            ctx,
            f"Invoice {res.invoice_id} is still unpaid, so the order is NOT placed yet. "
            f"The payment link is still valid whenever you're ready."
        )


agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print("Coordinator address:", agent.address)
    agent.run()
