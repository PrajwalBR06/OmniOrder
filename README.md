# OmniOrder — Omnichannel Order-to-Invoice-to-Payment Agent

> Built for **Fetch-A-Thon 3.0 — ASI:One Agent Challenge: From Intent to Action**

OmniOrder is a team of five AI agents that reads a customer's order from **any channel**
— WhatsApp (text, voice note, or photo), email, or a phone call — understands it,
generates an invoice, sends a payment link, and **confirms the order only once the
customer pays**. One message in, a paid and placed order out. No manual invoicing.

---

## Table of contents
- [The problem](#the-problem)
- [The solution](#the-solution)
- [How it works](#how-it-works)
- [Architecture — the 5 agents](#architecture--the-5-agents)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Setup & installation](#setup--installation)
- [Running locally](#running-locally)
- [Hosting on Agentverse & ASI:One](#hosting-on-agentverse--asione)
- [The UI — ASI:One Interactive Cards](#the-ui--asione-interactive-cards)
- [Payments](#payments)
- [Customizing for your business](#customizing-for-your-business)
- [Demo](#demo)
- [Submission checklist](#submission-checklist)

---

## The problem

Small businesses in India receive orders in chaos — a WhatsApp text, a voice note, a
photo of a handwritten list, an email, or a phone call, often mixing Hindi and English.
The owner then manually reads each order, works out prices, types an invoice, saves it,
collects payment, and confirms. It's slow, error-prone, and WhatsApp-first — which most
existing tools ignore.

## The solution

OmniOrder collapses the entire order cycle into one autonomous flow:

**understand → invoice → pay → confirm**

The customer never changes how they order. The agents adapt to the customer — reading
whatever format the order arrives in, and replying on the **same channel** the customer
used. A simple, realistic rule protects the owner: **no payment, no order.**

This is the hackathon theme — *intent to action* — taken all the way to a real transaction.

---

## How it works

```
Customer orders on ANY channel
(WhatsApp text / voice / photo · email · phone call)
                │
                ▼
        1. INGESTION  — normalize to plain text (transcribe / OCR)
                │
                ▼
        2. INTENT     — ASI:One extracts a structured order
                │        (asks a clarifying question if info is missing)
                ▼
        3. INVOICE    — price items, add tax, make PDF, log the order
                │
                ▼
        4. PAYMENT    — create pay link; show REVIEW card
                │
        ┌───────┴─────────────┐
        ▼                     ▼
   Customer PAYS         Customer DOESN'T pay
        │                     │
        ▼                     ▼
   Order CONFIRMED       Stays "pending"
   Receipt + status      (invoice viewable; no order placed)
```

The **Coordinator** orchestrates all of this over the Agent Chat Protocol and replies to
the customer inside ASI:One using Interactive Cards.

---

## Architecture — the 5 agents

A multi-agent swarm, each agent with a single responsibility, communicating over the
uAgents messaging protocol.

| # | Agent | File | Responsibility |
|---|-------|------|----------------|
| 1 | **Coordinator** | `agents/coordinator_agent.py` | The brain. Implements the **Agent Chat Protocol** (ASI:One-compatible), routes the pipeline, tracks order status, renders Interactive Cards. **This is the agent registered on Agentverse.** |
| 2 | **Channel Ingestion** | `agents/ingestion_agent.py` | Normalizes any channel into plain text. Hooks for voice-note transcription and image/handwriting OCR. |
| 3 | **Intent** | `agents/intent_agent.py` | Uses **ASI:One** to turn messy text into a structured order (customer, items, quantities, delivery). Raises clarifying questions when data is missing. |
| 4 | **Pricing & Invoice** | `agents/invoice_agent.py` | Prices each line from the catalog, applies tax, generates a **PDF invoice**, and logs every order to `orders_log.csv`. |
| 5 | **Payment & Reply** | `agents/payment_agent.py` | Creates a payment link via a **provider-agnostic interface** (Razorpay/UPI by default), waits for the paid webhook, and confirms the order. |

**Message flow:** `ASI:One → Coordinator → Ingestion → Intent → Invoice → Payment → Coordinator → customer`

---

## Tech stack

- **uAgents** (`>=0.25.5`) — the autonomous-agent framework (Python 3.10–3.13).
- **Agent Chat Protocol (ACP)** — required for ASI:One discovery & chat.
- **ASI:One** — agentic LLM used for order understanding; also renders Interactive Cards.
- **Agentverse** — marketplace where the Coordinator is registered/hosted.
- **ASI Interactive Cards** — the UI: Form, Carousel, Review, and Detail cards.
- **Razorpay** (pluggable) — payment links + webhook; behind a provider interface.
- **fpdf2** — PDF invoice generation. **Flask** — the payment webhook + owner dashboard.

---

## Project structure

```
omniorder/
├── agents/
│   ├── coordinator_agent.py    # Agent 1 — brain + ASI:One Chat Protocol + cards
│   ├── ingestion_agent.py      # Agent 2 — channel normalization (text/voice/image)
│   ├── intent_agent.py         # Agent 3 — ASI:One order extraction
│   ├── invoice_agent.py        # Agent 4 — pricing, PDF invoice, logging
│   └── payment_agent.py        # Agent 5 — payment link + webhook + confirm
├── shared/
│   ├── models.py               # Message schemas shared across all agents
│   ├── config.py               # Loads .env + catalog
│   ├── catalog.json            # Your products, prices, tax, currency, aliases
│   ├── cards.py                # ASI:One Interactive Card builders (the UI)
│   └── payments.py             # Provider-agnostic payment interface (Razorpay/Stripe/Demo)
├── dashboard/
│   └── owner_dashboard.py      # Optional web view of all orders (owner side)
├── ui_simulation.html          # Clickable preview of the card UX (SayBriefly style)
├── requirements.txt
├── .env.example                # Copy to .env and fill in keys
├── README.md
├── HOSTING_GUIDE.md            # Full step-by-step hosting walkthrough
└── UI_GUIDE.md                 # How the Interactive Cards UI works
```

---

## Setup & installation

**Prerequisite:** Python 3.10–3.13 (3.14+ not yet supported).

```bash
# 1. Create & activate a virtual environment
cd omniorder
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your config
copy .env.example .env          # Windows  (cp on macOS/Linux)
```

Fill in `.env`:
```
ASI_ONE_API_KEY=your_asi_one_key     # from https://asi1.ai -> Developer -> Create New
PAYMENT_PROVIDER=demo                 # "demo" needs no keys; auto-confirms payment
# (optional, for real payments)
# PAYMENT_PROVIDER=razorpay
# RAZORPAY_KEY_ID=rzp_test_xxxx
# RAZORPAY_KEY_SECRET=xxxx
```

> Redeem code **`FETCHATHONINDFETCHATHONIND`** on ASI:One for one month of
> ASI:One Pro + Agentverse Premium.

---

## Running locally

Each agent runs in its own terminal. **First run** prints each agent's address:

```bash
python agents/payment_agent.py       # -> Payment address: agent1q...
python agents/invoice_agent.py       # -> Invoice address: agent1q...
python agents/intent_agent.py        # -> Intent address: agent1q...
python agents/ingestion_agent.py     # -> Ingestion address: agent1q...
python agents/coordinator_agent.py   # -> Coordinator address: agent1q...  (start LAST)
```

**Wire them:** copy the five printed addresses into `.env`:
```
COORDINATOR_ADDRESS=agent1q...
INGESTION_ADDRESS=agent1q...
INTENT_ADDRESS=agent1q...
INVOICE_ADDRESS=agent1q...
PAYMENT_ADDRESS=agent1q...
```

**Restart all five agents** (Ctrl+C in each terminal, then run again). They can now route
to each other. Send the Coordinator an order and watch the pipeline run end-to-end.

> This address-wiring step is the single most common setup mistake — don't skip the restart.

---

## Hosting on Agentverse & ASI:One

Full details in **HOSTING_GUIDE.md**. Short version:

1. In `coordinator_agent.py`, set `mailbox=True` on the agent.
2. Run it — the terminal prints a **mailbox / Inspector link**.
3. Open it → sign in to **https://agentverse.ai** → **Connect**. The Coordinator is now
   registered. Copy its **Agent Profile URL** (a submission deliverable).
4. Go to **https://asi1.ai**, chat with `omniorder_coordinator`, run a full order, and
   copy the **Shared Chat URL** (a submission deliverable).

Because the Coordinator publishes its manifest (`publish_manifest=True`) with the Agent
Chat Protocol, ASI:One can discover and talk to it.

---

## The UI — ASI:One Interactive Cards

**You don't build a website — ASI:One is the interface.** The agents reply with
Interactive Cards (built in `shared/cards.py`), and ASI:One renders them in a drawer.

| Card | When it shows | Purpose |
|------|---------------|---------|
| **Form** | Delivery info is missing | Capture address / date / time slot |
| **Carousel** | Product is vague / upsell | Scrollable product picker |
| **Review** | Invoice is ready | Summary + **Confirm & Pay / Cancel** (hero card) |
| **Detail** (pay) | After Confirm | Amount + **Pay Now / UPI** |
| **Detail** (status) | After payment | "Order confirmed" + status tracker |

Button clicks come back from ASI:One as JSON text — the Coordinator does `json.loads()`
first and falls back to natural language, exactly as the docs recommend.

A clickable preview of the whole journey is in **`ui_simulation.html`**. An optional
owner-facing dashboard (`dashboard/owner_dashboard.py`) shows every order from every
channel in one table.

---

## Payments

Payments sit behind a **provider interface** (`shared/payments.py`), so the agent is not
coupled to any single gateway:

- `DemoProvider` — no keys, auto-confirms after a few seconds (great for first demo).
- `RazorpayProvider` — real payment links + webhook; all Razorpay-specific code is
  isolated here.
- Adding Stripe/Cashfree = one new class + one env var; **no agent code changes.**

Set the active gateway with `PAYMENT_PROVIDER` in `.env`. For real Razorpay payments,
expose the webhook (`:5055`) with a tunnel (ngrok / cloudflared) and register the
`payment_link.paid` event in the Razorpay dashboard.

---

## Customizing for your business

OmniOrder is **business-agnostic**. To adapt it from the sample catalog to your own
(restaurant, pharmacy, grocery, bakery, electronics, etc.):

1. Edit **`shared/catalog.json`** — your items, prices, `tax_percent`, `currency`, and
   local-language `aliases`.
2. Update the business line in the **`intent_agent.py`** prompt (e.g. "a pharmacy").
3. Optionally update the demo order and carousel in `ui_simulation.html`.

Nothing else needs to change — the pipeline, cards, and payments stay the same.

---

## Demo

Suggested 3–5 minute video flow:
1. The problem — orders arrive on WhatsApp/email/calls; invoicing is manual.
2. Send an order through ASI:One → show it understood + the invoice **Review card**.
3. Tap **Confirm & Pay** → pay (test mode) → order flips to **Confirmed**.
4. Show `orders_log.csv` / the owner dashboard — the unified record.
5. Highlight the architecture (5 agents) and multichannel capture (text/voice/image).

---



---

## Key references
- uAgent creation — https://innovationlab.fetch.ai/resources/docs/agent-creation/uagent-creation
- ASI:One quickstart — https://innovationlab.fetch.ai/resources/docs/asione/asi-one-quickstart
- Interactive Cards — https://innovationlab.fetch.ai/resources/docs/interactive-cards/asi-interactive-cards
- Examples repo — https://github.com/fetchai/innovation-lab-examples
- Submission dashboard — https://asi1.ai/festival/fetchathon3/dashboard
