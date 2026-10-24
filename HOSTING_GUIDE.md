# OmniOrder — Full Step-by-Step Hosting Guide
### Build → run locally → host on Agentverse → connect to ASI:One → submit

This is the complete walkthrough. Follow it top to bottom.

---

## PART A — Get your accounts and keys (10 min)

1. **ASI:One API key**
   - Go to https://asi1.ai → sign in.
   - Redeem premium: use code `FETCHATHONINDFETCHATHONIND` (ASI:One Pro + Agentverse Premium, 1 month).
   - Open **API Keys** → create a key → copy it.
   - Put it in `.env` as `ASI_ONE_API_KEY`.

2. **Agentverse account**
   - Go to https://agentverse.ai → sign in with the same account.

3. **Razorpay (optional — payments)**
   - Go to https://dashboard.razorpay.com → **Settings → API Keys** → generate **TEST** keys.
   - Put them in `.env` as `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`.
   - Skip this to run in DEMO MODE (payment auto-confirms — perfect for a first demo).

---

## PART B — Run all 5 agents locally (15 min)

1. Install:
   ```bash
   cd omniorder
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```
   Fill `ASI_ONE_API_KEY` in `.env`.

2. **First run** — start each agent in its own terminal. Each prints its address:
   ```
   python agents/payment_agent.py       ->  Payment address: agent1q...
   python agents/invoice_agent.py       ->  Invoice address: agent1q...
   python agents/intent_agent.py        ->  Intent address: agent1q...
   python agents/ingestion_agent.py     ->  Ingestion address: agent1q...
   python agents/coordinator_agent.py   ->  Coordinator address: agent1q...
   ```

3. **Wire them** — copy those 5 addresses into `.env`:
   ```
   COORDINATOR_ADDRESS=agent1q...
   INGESTION_ADDRESS=agent1q...
   INTENT_ADDRESS=agent1q...
   INVOICE_ADDRESS=agent1q...
   PAYMENT_ADDRESS=agent1q...
   ```

4. **Restart all 5 agents.** Now they can route to each other.
   Order: payment → invoice → intent → ingestion → coordinator.

5. **Why this order?** Downstream agents should be up before the ones that call them,
   so the very first message doesn't hit a dead address.

---

## PART C — Test the full pipeline locally (5 min)

Send the Coordinator a test order. Easiest way: add a tiny sender script, OR just
chat through ASI:One after Part D. A quick local test message looks like:

> "Hi, I'm Rahul. I need 3 chairs and 2 tables delivered to MG Road by Friday."

Watch the terminals. You should see:
`Ingestion → Intent (understood) → Invoice (INV-xxxx, PDF saved) → Payment (link sent) → PAID → Order CONFIRMED`

Check:
- `invoices/INV-xxxx.pdf` was created.
- `orders_log.csv` has a new row.

---

## PART D — Host the Coordinator on Agentverse (15 min)

You only need to host the **Coordinator** on Agentverse (it's the one ASI:One discovers).
Two options:

### Option 1 — Hosted Agent (easiest, recommended for the hackathon)
1. https://agentverse.ai → **Agents → + New Agent → Blank Agent**.
2. Paste the contents of `agents/coordinator_agent.py` into the code editor.
   - It already uses the **Agent Chat Protocol** and `publish_manifest=True`.
   - On Agentverse, the agent runs in the cloud — no local endpoint needed.
3. For the hosted version, the 4 worker agents can also be hosted the same way,
   OR you can keep workers running locally and expose them with a **Mailbox**
   (see Option 2). Simplest path: host all 5 as hosted agents and set their
   addresses in Agentverse secrets/env.
4. Click **Run / Deploy**.
5. Open the agent's page → copy its **Agent Profile URL**. ✅ (submission deliverable)

### Option 2 — Keep agents local, connect via Mailbox
1. In each agent, add a mailbox when creating it:
   ```python
   agent = Agent(name="...", seed="...", mailbox=True)
   ```
2. Run the agent locally → it prints a link to connect the mailbox to Agentverse.
3. Open that link, sign in, **connect**. Your local agent is now reachable from
   Agentverse and ASI:One without a public server.
4. Copy the **Agent Profile URL** from Agentverse. ✅

> Tip: For a first submission, Mailbox (Option 2) is the fastest way to get your
> locally-running Coordinator onto ASI:One.

---

## PART E — Connect to ASI:One and get the Shared Chat URL (5 min)

1. Make sure the Coordinator is running/hosted and its **manifest is published**
   (it is, via `publish_manifest=True`).
2. Go to https://asi1.ai → start a new chat.
3. ASI:One discovers agents through the Agent Chat Protocol. Ask it to use/route to
   your agent (search by your agent name `omniorder_coordinator`), or invoke it
   directly from your Agentverse profile's "Chat with Agent" button.
4. Run a complete order conversation:
   - "I'm Priya, send me 1 sofa and 4 chairs to Pune."
   - Watch: invoice → payment link → (pay in test mode) → order confirmed.
5. Click **Share** on the chat → copy the **Shared Chat URL**. ✅ (submission deliverable)

---

## PART F — (Optional) Real payment webhook with ngrok

Only if you set real Razorpay test keys and want a *real* paid→confirm flow:

1. Install ngrok, then:  `ngrok http 5055`
2. Copy the https URL → set `PAYMENT_WEBHOOK_URL` in `.env` to
   `https://<id>.ngrok-free.app/razorpay-webhook`.
3. In Razorpay dashboard → **Settings → Webhooks** → add that URL, event
   `payment_link.paid`.
4. Restart `payment_agent.py`. Now paying the link (test card / test UPI)
   triggers a real confirmation.

---

## PART G — Record the demo video (3–5 min)

Suggested script:
1. (20s) The problem: shop owners get orders on WhatsApp/email/calls, invoice by hand.
2. (60s) Send an order via ASI:One chat. Show it understood + invoice generated.
3. (60s) Show the payment link; pay in test mode; order flips to CONFIRMED.
4. (40s) Show `orders_log.csv` / the PDF — the unified record.
5. (30s) Mention multi-agent architecture (5 agents) + channels (text/voice/image).
6. (20s) Impact: zero manual invoicing, no payment = no order.

---

## PART H — Submit (via ASI:One dashboard)

Checklist:
- [ ] Public GitHub repo (all code + README)
- [ ] Agentverse Agent Profile URL (Coordinator)
- [ ] ASI:One Shared Chat URL
- [ ] Demo video (3–5 min)
- [ ] Project description (problem / users / outcomes)

Prizes you're positioned for: **Best Multi-Agent Workflow** (5-agent swarm),
**Best Agentverse Deployment**, plus the main rubric (Functionality 25%, Fetch tech 20%).

---

## Troubleshooting

- **"Address is empty / message not delivered"** → you forgot to paste the 5 addresses
  into `.env` and restart. Do Part B steps 3–4 again.
- **ASI:One parse errors** → check `ASI_ONE_API_KEY`; try model `asi1-mini`.
- **Agent not found on ASI:One** → confirm `publish_manifest=True` and the agent is
  running/mailbox-connected.
- **PDF font errors** → `fpdf2` uses built-in Helvetica; avoid non-latin chars in the
  catalog names, or add a Unicode TTF font.
