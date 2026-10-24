"""
Shared message models for the OmniOrder multi-agent system.
Every agent imports these so they all "speak the same language"
over the uAgents messaging protocol.
"""
from typing import List, Optional
from uagents import Model


class LineItem(Model):
    """One product line in an order."""
    key: str            # catalog key, e.g. "chair"
    name: str           # display name, e.g. "Wooden Chair"
    quantity: int
    unit_price: float = 0.0
    line_total: float = 0.0


# ---------- Channel Ingestion Agent ----------
class RawMessage(Model):
    """A raw incoming order from any channel, normalized to text."""
    channel: str        # "whatsapp" | "email" | "call"
    sender: str         # phone number or email of the customer
    text: str           # transcribed / OCR'd / plain text of the order
    customer_name: Optional[str] = None


# ---------- Intent Agent ----------
class StructuredOrder(Model):
    """The cleaned-up order after ASI:One understands the raw text."""
    channel: str
    sender: str
    customer_name: str
    items: List[LineItem]
    delivery_address: str = ""
    delivery_date: str = ""
    clarifying_questions: List[str] = []
    needs_clarification: bool = False


# ---------- Pricing & Invoice Agent ----------
class Invoice(Model):
    """A priced, generated invoice."""
    invoice_id: str
    channel: str
    sender: str
    customer_name: str
    items: List[LineItem]
    subtotal: float
    tax: float
    total: float
    currency: str
    delivery_address: str = ""
    delivery_date: str = ""
    status: str = "pending"      # pending | paid | expired


# ---------- Payment & Reply Agent ----------
class PaymentRequest(Model):
    """Ask the payment agent to create a link and send the invoice out."""
    invoice: Invoice


class PaymentResult(Model):
    """Reported back after payment succeeds (or times out)."""
    invoice_id: str
    status: str                  # paid | expired
    amount: float
    sender: str
    channel: str


# ---------- Coordinator <-> ASI:One / user ----------
class UserEntry(Model):
    """Entry point: a message the Coordinator receives (from ASI:One or a channel)."""
    channel: str
    sender: str
    text: str
    customer_name: Optional[str] = None


class Ack(Model):
    """Generic acknowledgement so senders know a message was received."""
    ok: bool
    message: str = ""
