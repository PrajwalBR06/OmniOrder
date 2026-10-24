"""
================================================================
 OmniOrder - Payment & Reply Agent  (AGENT #5)
================================================================
1. Creates a Razorpay payment LINK for the invoice (TEST mode).
2. "Sends" the invoice + link back on the customer's channel.
3. Runs a small webhook server that Razorpay pings when paid.
4. On payment -> reports PaymentResult(status="paid") to Coordinator,
   which then CONFIRMS the order. No payment = order stays pending.

DEMO MODE: if RAZORPAY keys are empty, it creates a fake link and
auto-confirms after a few seconds so you can demo without real keys.

Run:  python agents/payment_agent.py
================================================================
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import threading
from datetime import datetime

from uagents import Agent, Context
from uagents.setup import fund_agent_if_low

from shared.models import PaymentRequest, PaymentResult, Invoice
from shared import config

try:
    import razorpay
except ImportError:
    razorpay = None
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
agent = Agent(
    name="omniorder_payment",
    seed="omniorder-payment-6t1cy3-2026",
    port=8004,
    endpoint=["http://127.0.0.1:8004/submit"],
)
fund_agent_if_low(agent.wallet.address())

DEMO_MODE = not (config.RAZORPAY_KEY_ID and config.RAZORPAY_KEY_SECRET)

# invoice_id -> Invoice (so the webhook can look it up when payment arrives)
PENDING = {}

rzp = None
if not DEMO_MODE and razorpay:
    rzp = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))


def create_payment_link(inv: Invoice) -> str:
    """Return a payable URL. Real in live mode, fake in demo mode."""
    if DEMO_MODE or not rzp:
        return f"https://demo.omniorder.pay/{inv.invoice_id}?amt={inv.total}"
    link = rzp.payment_link.create({
        "amount": int(inv.total * 100),          # paise
        "currency": inv.currency,
        "description": f"Order {inv.invoice_id}",
        "reference_id": inv.invoice_id,
        "notify": {"sms": True, "email": True},
        "callback_url": config.PAYMENT_WEBHOOK_URL,
        "callback_method": "get",
    })
    return link["short_url"]


def send_on_channel(channel: str, to: str, text: str):
    """
    STUB: deliver the invoice + link back on the SAME channel.
    Wire these to real providers:
      - whatsapp -> Twilio / WhatsApp Cloud API
      - email    -> SMTP / Gmail API
      - call/sms -> Twilio SMS
    For the MVP we just log it (and the Coordinator also replies on ASI:One).
    """
    print(f"\n--- OUTBOUND [{channel} -> {to}] ---\n{text}\n--------------------------------\n")


# ---------------- Webhook server (runs in a background thread) ----------------
def start_webhook(loop, ctx_ref):
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route("/razorpay-webhook", methods=["GET", "POST"])
    def webhook():
        ref = (request.args.get("reference_id")
               or (request.json or {}).get("payload", {})
               .get("payment_link", {}).get("entity", {}).get("reference_id"))
        if ref and ref in PENDING:
            inv = PENDING.pop(ref)
            asyncio.run_coroutine_threadsafe(_confirm(ctx_ref[0], inv), loop)
        return jsonify({"ok": True})

    app.run(host="0.0.0.0", port=5055)


async def _confirm(ctx: Context, inv: Invoice):
    ctx.logger.info(f"[Payment] PAID -> {inv.invoice_id}")
    send_on_channel(inv.channel, inv.sender,
                    f"Payment received for {inv.invoice_id}. Order confirmed!")
    await ctx.send(config.COORDINATOR_ADDRESS, PaymentResult(
        invoice_id=inv.invoice_id, status="paid",
        amount=inv.total, sender=inv.sender, channel=inv.channel))


_CTX = [None]


@agent.on_message(model=PaymentRequest)
async def collect(ctx: Context, sender: str, req: PaymentRequest):
    _CTX[0] = ctx
    inv = req.invoice
    PENDING[inv.invoice_id] = inv
    link = create_payment_link(inv)

    msg = (f"Here is your invoice {inv.invoice_id} for {inv.currency} {inv.total:.2f}.\n"
           f"Pay here to confirm your order: {link}\n"
           f"(No payment = order not placed; you can pay anytime.)")
    send_on_channel(inv.channel, inv.sender, msg)
    ctx.logger.info(f"[Payment] Link sent for {inv.invoice_id} (demo={DEMO_MODE})")

    if DEMO_MODE:
        # Auto-confirm after 8s so you can show the full happy path on video.
        ctx.logger.info("[Payment] DEMO MODE: auto-confirming in 8s...")
        await asyncio.sleep(8)
        PENDING.pop(inv.invoice_id, None)
        await _confirm(ctx, inv)


@agent.on_event("startup")
async def boot(ctx: Context):
    _CTX[0] = ctx
    if not DEMO_MODE:
        loop = asyncio.get_event_loop()
        threading.Thread(target=start_webhook, args=(loop, _CTX), daemon=True).start()
        ctx.logger.info("[Payment] Webhook listening on :5055 /razorpay-webhook")
    else:
        ctx.logger.info("[Payment] Running in DEMO MODE (no Razorpay keys).")


if __name__ == "__main__":
    print("Payment address:", agent.address)
    agent.run()
