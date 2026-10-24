# OmniOrder — Omnichannel Order-to-Invoice-to-Payment Agent

An AI agent (team of 5 uAgents) for Fetch-A-Thon 3.0.
It reads orders from WhatsApp / email / calls, understands them with ASI:One,
generates an invoice, sends a payment link, and **confirms the order only once the
customer pays**.

> One message in → a paid, placed order out. No manual invoicing.

---

## The 5 agents

| # | File | Role |
|---|------|------|
| 1 | `agents/coordinator_agent.py` | Brain. Talks to ASI:One (Agent Chat Protocol). Routes the pipeline. **Register THIS on Agentverse.** |
| 2 | `agents/ingestion_agent.py` | Normalizes any channel (text / voice / image) into plain text. |
| 3 | `agents/intent_agent.py` | Uses ASI:One to turn messy text into a structured order. |
| 4 | `agents/invoice_agent.py` | Prices items, makes a PDF invoice, logs the record. |
| 5 | `agents/payment_agent.py` | Creates a Razorpay/UPI payment link, waits for payment, confirms the order. |

**Flow:** `ASI:One → Coordinator → Ingestion → Intent → Invoice → Payment → Coordinator → user`

---

## Quick start (local, in 10 minutes)

```bash
# 1. Setup
cd omniorder
python -m venv venv
venv\Scripts\activate        # (Windows)   |  source venv/bin/activate (Mac/Linux)
pip install -r requirements.txt

# 2. Config
copy .env.example .env       # (Windows)   |  cp .env.example .env (Mac/Linux)
#   -> put your ASI_ONE_API_KEY in .env
#   -> leave Razorpay blank to run in DEMO MODE (auto-confirms payment)

# 3. Start each agent in its OWN terminal, in this order:
python agents/payment_agent.py       # prints  Payment address: agent1...
python agents/invoice_agent.py       # prints  Invoice address: agent1...
python agents/intent_agent.py        # prints  Intent address:  agent1...
python agents/ingestion_agent.py     # prints  Ingestion address: agent1...
python agents/coordinator_agent.py   # prints  Coordinator address: agent1...

# 4. Copy each printed address into .env, then RESTART all 5 agents.
#    (They need each other's addresses to route messages.)
```

Once they're all running and wired, send the Coordinator a chat message (via ASI:One
or a local test) like:

> "Hi, I'm Rahul. I need 3 chairs and 2 tables delivered to MG Road by Friday."

You'll watch it flow: understood → invoice → payment link → (demo auto-pay) → **order confirmed.**

---

## Hosting on Agentverse + connecting to ASI:One

See **HOSTING_GUIDE.md** for the full step-by-step with screenshots-level detail.
Short version:

1. Go to https://agentverse.ai → **Agents → New Agent**.
2. Paste the Coordinator agent code into the hosted editor (it already includes the
   Agent Chat Protocol + `publish_manifest=True`).
3. Deploy. Agentverse gives you a public **Agent Profile URL** (a submission deliverable).
4. Go to https://asi1.ai → it discovers your agent via the Chat Protocol.
5. Chat with your agent from ASI:One, run a full order, then copy the **Shared Chat URL**
   (another submission deliverable).

---

## Submission checklist (from the hackpack)

- [ ] Public GitHub repo with all agent code + this README
- [ ] At least one agent registered on Agentverse (the Coordinator)
- [ ] Agentverse Agent Profile URL(s)
- [ ] ASI:One Shared Chat URL (full order → payment → confirmation)
- [ ] Demo video (3–5 min)
- [ ] Project description: problem, target users, outcomes

## Free premium
Redeem code `FETCHATHONINDFETCHATHONIND` for ASI:One Pro + Agentverse Premium.
