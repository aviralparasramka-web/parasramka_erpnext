"""
Claude AI integration for Parasramka Engineering Pvt. Ltd.

Option A — Natural language ERP query  (query_erpnext_data)
Option B — AI letter drafter             (draft_letter)
Option D — PEPL Assistant chat page      (served by pepl_assistant page)

The Anthropic API key is stored in site_config.json (never in code).
To add the key on Frappe Cloud:
  Site → Settings → Site Config → Add key: anthropic_api_key
"""

import json

import frappe
import requests
from frappe import _
from frappe.utils import flt, nowdate

# ── Constants ──────────────────────────────────────────────────────────────────

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL   = "claude-opus-4-5"   # upgrade to claude-opus-4-5 when available

SYSTEM_BASE = """You are PEPL Assistant, an AI helper for Parasramka Engineering Pvt. Ltd.
PEPL is a heavy engineering company that manufactures precision components for Indian
Defence (MIL, YIL, AWEIL) and Railways (Loco, Coaches, Zonal) customers.
Always be concise, professional, and data-driven in your answers.
Amounts are in Indian Rupees (INR). Dates follow DD-MMM-YYYY format."""

# Keyword → DocType routing for natural language queries
DOCTYPE_KEYWORDS = {
    "Tender Management":  ["tender", "bid", "bidding", "rfp", "l1", "won", "lost tender"],
    "CO7 Tracker":        ["co7", "railway payment", "invoice stage", "bills submitted", "co7 status"],
    "PSD Tracker":        ["psd", "performance security", "security deposit", "ndc", "refund"],
    "CST Cost Sheet":     ["cost sheet", "cst", "costing", "bom", "unit price", "material cost"],
    "Sales Order":        ["sales order", "order", "delivery", "purchase order"],
    "Sales Invoice":      ["invoice", "outstanding", "payment due", "ageing"],
    "Quotation":          ["quotation", "quote", "offer"],
    "Customer":           ["customer", "client", "buyer", "vendor approval"],
}

# Letter type → doc fields to fetch and prompt instruction
LETTER_CONFIG = {
    "Payment Request": {
        "doctype": "Sales Invoice",
        "fields":  ["name", "customer", "customer_name", "posting_date", "grand_total",
                    "outstanding_amount", "po_no"],
        "instruction": (
            "Draft a formal payment request letter on behalf of PEPL asking the customer "
            "to release the outstanding invoice amount. Be polite but firm. Include reference "
            "to the invoice number, amount, and request for UTR upon payment."
        ),
    },
    "Down Payment Request": {
        "doctype": "Sales Order",
        "fields":  ["name", "customer", "customer_name", "transaction_date",
                    "grand_total", "delivery_date", "po_no"],
        "instruction": (
            "Draft a formal advance/down-payment request letter asking the customer to "
            "release the agreed advance (typically 30%) before PEPL commences raw material "
            "procurement and manufacturing."
        ),
    },
    "Drawing Request": {
        "doctype": "Tender Management",
        "fields":  ["name", "tender_no", "item", "customer", "drawing_no",
                    "specification", "bid_deadline"],
        "instruction": (
            "Draft a formal letter requesting the customer to release approved drawings "
            "and technical specifications for the tendered item so PEPL can prepare an "
            "accurate technical and commercial offer."
        ),
    },
    "Lot Offer": {
        "doctype": "Sales Order",
        "fields":  ["name", "customer", "customer_name", "transaction_date",
                    "items"],
        "instruction": (
            "Draft a formal letter offering a manufactured lot for inspection. "
            "Mention that the lot has been manufactured as per drawing and specification, "
            "in-process checks are complete, and request the customer to depute an "
            "Inspecting Officer / RITES representative."
        ),
    },
    "Quotation Letter": {
        "doctype": "Quotation",
        "fields":  ["name", "party_name", "transaction_date", "grand_total",
                    "valid_till", "payment_terms_template", "items"],
        "instruction": (
            "Draft a professional quotation cover letter submitting PEPL's price offer "
            "for the items listed. Highlight quality, compliance with spec/drawing, "
            "and competitive delivery schedule. Invite the customer to place a Purchase Order."
        ),
    },
}


# ── Public API (whitelisted) ───────────────────────────────────────────────────

@frappe.whitelist()
def query_erpnext_data(question, doctype=None):
    """Option A — Answer a natural-language business question using live ERP data.

    Args:
        question: Free-text question from the user.
        doctype:  Optional DocType hint; auto-detected if omitted.

    Returns:
        Claude's natural-language answer as a string.
    """
    api_key = get_api_key()

    # Determine the best DocType to query if caller didn't specify
    if not doctype:
        doctype = _infer_doctype(question)

    # Fetch a representative data snapshot from ERPNext (max 30 records)
    context_text = _build_data_context(doctype, question)

    prompt = (
        f"Business question: {question}\n\n"
        f"Relevant ERP data snapshot (today: {nowdate()}):\n"
        f"{context_text}\n\n"
        "Answer the question using only the data above. "
        "If you cannot answer from the data, say so clearly and suggest what to look for."
    )

    return _call_claude(SYSTEM_BASE, prompt, api_key)


@frappe.whitelist()
def draft_letter(letter_type, document_name):
    """Option B — AI-drafted business letter from an ERPNext document.

    Args:
        letter_type:   Key from LETTER_CONFIG (e.g. 'Payment Request').
        document_name: The ERPNext document name (e.g. 'SINV-2024-00001').

    Returns:
        Drafted letter body text (excluding letterhead; ready for copy-paste).
    """
    api_key = get_api_key()

    config = LETTER_CONFIG.get(letter_type)
    if not config:
        frappe.throw(_(f"Letter type '{letter_type}' is not configured."))

    # Fetch document data from ERPNext
    doc_data = _fetch_doc_data(config["doctype"], document_name, config["fields"])

    prompt = (
        f"{config['instruction']}\n\n"
        f"Document details:\n{doc_data}\n\n"
        "Write ONLY the letter body — no letterhead, no 'To:' block. "
        "Start from the salutation (Dear Sir/Madam,). "
        "End with 'Thanking you.' followed by a blank line. "
        "Use formal Indian business English."
    )

    system = (
        SYSTEM_BASE + "\n\n"
        "You are writing on behalf of Parasramka Engineering Pvt. Ltd. "
        "Always sign off as: 'For Parasramka Engineering Pvt. Ltd.' "
        "followed by '[Authorised Signatory]'."
    )

    return _call_claude(system, prompt, api_key)


@frappe.whitelist()
def get_letter_types():
    """Return available letter types for the UI dropdown."""
    return list(LETTER_CONFIG.keys())


# ── Key management ─────────────────────────────────────────────────────────────

def get_api_key():
    """Read the Anthropic API key from site_config.json — never from code.

    On Frappe Cloud: Site → Settings → Site Config → anthropic_api_key
    """
    api_key = frappe.conf.get("anthropic_api_key")
    if not api_key:
        frappe.throw(
            _("Anthropic API key is not configured. "
              "Add 'anthropic_api_key' to this site's Site Config on Frappe Cloud."),
            title=_("Claude API Not Configured"),
        )
    return api_key


# ── Claude HTTP call ───────────────────────────────────────────────────────────

def _call_claude(system_prompt, user_message, api_key, max_tokens=2048):
    """Make a single-turn call to the Claude Messages API via requests."""
    headers = {
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }
    payload = {
        "model":      CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "system":     system_prompt,
        "messages":   [{"role": "user", "content": user_message}],
    }
    try:
        resp = requests.post(CLAUDE_API_URL, headers=headers,
                             json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]
    except requests.exceptions.Timeout:
        frappe.log_error("Claude API timed out", "Claude Integration")
        frappe.throw(_("Claude API timed out. Please try again."))
    except requests.exceptions.HTTPError as exc:
        body = exc.response.text if exc.response else ""
        frappe.log_error(f"{exc}\n{body}", "Claude Integration")
        frappe.throw(_("Claude API error: {0}").format(str(exc)))
    except Exception as exc:
        frappe.log_error(str(exc), "Claude Integration")
        frappe.throw(_("Unexpected error calling Claude: {0}").format(str(exc)))


# ── DocType inference ──────────────────────────────────────────────────────────

def _infer_doctype(question):
    """Map question keywords to the most relevant DocType."""
    q_lower = question.lower()
    scores = {}
    for doctype, keywords in DOCTYPE_KEYWORDS.items():
        scores[doctype] = sum(1 for kw in keywords if kw in q_lower)

    best = max(scores, key=scores.get)
    # Default to Sales Order if nothing matches
    return best if scores[best] > 0 else "Sales Order"


# ── Data context builders ──────────────────────────────────────────────────────

def _build_data_context(doctype, question):
    """Fetch relevant records and format as compact text for the Claude prompt."""
    try:
        if doctype == "Tender Management":
            return _context_tender(question)
        if doctype == "CO7 Tracker":
            return _context_co7(question)
        if doctype == "PSD Tracker":
            return _context_psd(question)
        if doctype == "Sales Invoice":
            return _context_invoices(question)
        if doctype == "Sales Order":
            return _context_orders(question)
        if doctype == "Quotation":
            return _context_quotations(question)
        if doctype == "Customer":
            return _context_customers(question)
        return f"No specific data handler for DocType: {doctype}"
    except Exception as exc:
        frappe.log_error(str(exc), "Claude data context")
        return f"[Error fetching data: {exc}]"


def _context_tender(question):
    records = frappe.get_all(
        "Tender Management",
        fields=["name", "tender_no", "item", "customer", "sector",
                "status", "bid_deadline", "estimated_value", "l1_price", "loss_reason"],
        order_by="bid_deadline desc",
        limit=30,
    )
    lines = [f"Tender Management — {len(records)} records:"]
    for r in records:
        lines.append(
            f"  {r.tender_no or r.name} | {r.customer} | {r.item} | "
            f"Status: {r.status} | Deadline: {r.bid_deadline} | "
            f"Est Value: ₹{flt(r.estimated_value):,.0f} | L1: ₹{flt(r.l1_price):,.0f}"
        )
    return "\n".join(lines)


def _context_co7(question):
    records = frappe.get_all(
        "CO7 Tracker",
        fields=["name", "sales_invoice", "customer", "invoice_amount",
                "current_stage", "ageing_days", "outstanding_amount"],
        order_by="ageing_days desc",
        limit=30,
    )
    lines = [f"CO7 Tracker — {len(records)} records:"]
    for r in records:
        lines.append(
            f"  {r.sales_invoice} | {r.customer} | ₹{flt(r.invoice_amount):,.0f} | "
            f"Stage: {r.current_stage} | Ageing: {r.ageing_days}d | "
            f"Outstanding: ₹{flt(r.outstanding_amount):,.0f}"
        )
    return "\n".join(lines)


def _context_psd(question):
    records = frappe.get_all(
        "PSD Tracker",
        fields=["name", "sales_order", "customer", "psd_amount",
                "psd_expiry", "status", "ndc_received"],
        order_by="psd_expiry asc",
        limit=30,
    )
    lines = [f"PSD Tracker — {len(records)} records:"]
    for r in records:
        lines.append(
            f"  {r.name} | SO: {r.sales_order} | {r.customer} | "
            f"₹{flt(r.psd_amount):,.0f} | Expiry: {r.psd_expiry} | "
            f"Status: {r.status} | NDC: {'Yes' if r.ndc_received else 'No'}"
        )
    return "\n".join(lines)


def _context_invoices(question):
    records = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["name", "customer", "posting_date", "grand_total", "outstanding_amount"],
        order_by="posting_date asc",
        limit=30,
    )
    lines = [f"Unpaid Sales Invoices — {len(records)} records:"]
    for r in records:
        lines.append(
            f"  {r.name} | {r.customer} | Date: {r.posting_date} | "
            f"Total: ₹{flt(r.grand_total):,.0f} | Outstanding: ₹{flt(r.outstanding_amount):,.0f}"
        )
    return "\n".join(lines)


def _context_orders(question):
    records = frappe.get_all(
        "Sales Order",
        filters={"docstatus": 1, "status": ["not in", ["Completed", "Cancelled"]]},
        fields=["name", "customer", "transaction_date", "grand_total",
                "delivery_date", "status"],
        order_by="delivery_date asc",
        limit=30,
    )
    lines = [f"Open Sales Orders — {len(records)} records:"]
    for r in records:
        lines.append(
            f"  {r.name} | {r.customer} | ₹{flt(r.grand_total):,.0f} | "
            f"Delivery: {r.delivery_date} | Status: {r.status}"
        )
    return "\n".join(lines)


def _context_quotations(question):
    records = frappe.get_all(
        "Quotation",
        filters={"docstatus": 1},
        fields=["name", "party_name", "transaction_date", "grand_total", "status", "valid_till"],
        order_by="transaction_date desc",
        limit=30,
    )
    lines = [f"Quotations — {len(records)} records:"]
    for r in records:
        lines.append(
            f"  {r.name} | {r.party_name} | ₹{flt(r.grand_total):,.0f} | "
            f"Status: {r.status} | Valid till: {r.valid_till}"
        )
    return "\n".join(lines)


def _context_customers(question):
    records = frappe.get_all(
        "Customer",
        filters={"disabled": 0},
        fields=["name", "customer_name", "customer_group", "territory"],
        limit=50,
    )
    lines = [f"Customers — {len(records)} records:"]
    for r in records:
        lines.append(f"  {r.customer_name} | Group: {r.customer_group} | Territory: {r.territory}")
    return "\n".join(lines)


# ── Document data fetcher for draft_letter ─────────────────────────────────────

def _fetch_doc_data(doctype, document_name, fields):
    """Fetch a document and return key fields as formatted text."""
    try:
        doc = frappe.get_doc(doctype, document_name)
    except frappe.DoesNotExistError:
        frappe.throw(_(f"{doctype} '{document_name}' not found."))

    lines = [f"DocType: {doctype}", f"Document: {document_name}"]
    for field in fields:
        val = doc.get(field)
        if field == "items" and val:
            # Summarise child table items
            lines.append(f"Items:")
            for item in val:
                lines.append(
                    f"  - {item.get('item_name') or item.get('item_code')} | "
                    f"Qty: {item.get('qty')} | Rate: ₹{flt(item.get('rate')):,.0f}"
                )
        elif val is not None:
            lines.append(f"{field}: {val}")
    return "\n".join(lines)
