"""
================================================================
 OmniOrder - Pricing & Invoice Agent  (AGENT #4)
================================================================
Takes a structured order, prices every line from the catalog,
adds tax, generates a PDF invoice, logs the record, and sends
the priced Invoice back to the Coordinator.

Run:  python agents/invoice_agent.py
================================================================
"""
import sys, os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low

from shared.models import StructuredOrder, Invoice, LineItem
from shared import config
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
agent = Agent(
    name="omniorder_invoice",
    seed="omniorder-invoice-2r5vn8-2026",
    port=8003,
    endpoint=["http://127.0.0.1:8003/submit"],
)
fund_agent_if_low(agent.wallet.address())

catalog = config.load_catalog()
ROOT = Path(__file__).resolve().parent.parent
INVOICE_DIR = ROOT / "invoices"
INVOICE_DIR.mkdir(exist_ok=True)
LOG_FILE = ROOT / "orders_log.csv"

_counter = {"n": 1000}


def next_invoice_id() -> str:
    _counter["n"] += 1
    return f"INV-{_counter['n']}"


def price_order(order: StructuredOrder):
    priced = []
    subtotal = 0.0
    for it in order.items:
        unit = catalog["items"].get(it.key, {}).get("price", 0.0)
        total = unit * it.quantity
        subtotal += total
        priced.append(LineItem(key=it.key, name=it.name, quantity=it.quantity,
                               unit_price=unit, line_total=total))
    tax = round(subtotal * catalog["tax_percent"] / 100.0, 2)
    grand = round(subtotal + tax, 2)
    return priced, round(subtotal, 2), tax, grand


def make_pdf(inv: Invoice):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "OmniOrder - Invoice", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Invoice: {inv.invoice_id}", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.now():%d %b %Y, %H:%M}", ln=True)
    pdf.cell(0, 8, f"Customer: {inv.customer_name}  ({inv.channel})", ln=True)
    if inv.delivery_address:
        pdf.cell(0, 8, f"Deliver to: {inv.delivery_address}", ln=True)
    if inv.delivery_date:
        pdf.cell(0, 8, f"Delivery date: {inv.delivery_date}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(80, 8, "Item", border=1)
    pdf.cell(25, 8, "Qty", border=1, align="C")
    pdf.cell(40, 8, "Unit", border=1, align="R")
    pdf.cell(45, 8, "Total", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "", 11)
    for i in inv.items:
        pdf.cell(80, 8, i.name, border=1)
        pdf.cell(25, 8, str(i.quantity), border=1, align="C")
        pdf.cell(40, 8, f"{i.unit_price:.0f}", border=1, align="R")
        pdf.cell(45, 8, f"{i.line_total:.0f}", border=1, align="R", ln=True)

    pdf.ln(2)
    pdf.cell(145, 8, "Subtotal", align="R")
    pdf.cell(45, 8, f"{inv.currency} {inv.subtotal:.2f}", align="R", ln=True)
    pdf.cell(145, 8, f"Tax ({catalog['tax_percent']}%)", align="R")
    pdf.cell(45, 8, f"{inv.currency} {inv.tax:.2f}", align="R", ln=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(145, 10, "TOTAL", align="R")
    pdf.cell(45, 10, f"{inv.currency} {inv.total:.2f}", align="R", ln=True)

    path = INVOICE_DIR / f"{inv.invoice_id}.pdf"
    pdf.output(str(path))
    return str(path)


def log_order(inv: Invoice, pdf_path: str):
    new = not LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "invoice_id", "channel", "customer",
                        "total", "status", "pdf"])
        w.writerow([datetime.now().isoformat(), inv.invoice_id, inv.channel,
                    inv.customer_name, inv.total, inv.status, pdf_path])


@agent.on_message(model=StructuredOrder)
async def generate(ctx: Context, sender: str, order: StructuredOrder):
    ctx.logger.info(f"[Invoice] Pricing order for {order.customer_name}")
    items, subtotal, tax, total = price_order(order)

    inv = Invoice(
        invoice_id=next_invoice_id(),
        channel=order.channel,
        sender=order.sender,
        customer_name=order.customer_name,
        items=items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        currency=catalog["currency"],
        delivery_address=order.delivery_address,
        delivery_date=order.delivery_date,
        status="pending",
    )
    pdf_path = make_pdf(inv)
    log_order(inv, pdf_path)
    ctx.logger.info(f"[Invoice] {inv.invoice_id} total={inv.total} pdf={pdf_path}")

    await ctx.send(config.COORDINATOR_ADDRESS, inv)


if __name__ == "__main__":
    print("Invoice address:", agent.address)
    agent.run()
