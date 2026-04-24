"""
Sales Invoice — doc_events

on_submit:
  Linkage 4 — Auto-create CO7 Tracker for Railway customers.
"""

import frappe
from frappe import _
from frappe.utils import flt


def on_submit(doc, method):
    _create_co7_tracker(doc)


# ── Linkage 4 ─────────────────────────────────────────────────────────────────

# Identifiers used to decide if a customer belongs to Railways.
# We check both the Customer's custom sector field and the customer_group.
RAILWAY_KEYWORDS = ("railway", "railways", "ir ", "indian railway")


def _create_co7_tracker(doc):
    """Auto-create a CO7 Tracker when a Sales Invoice is submitted for a
    Railway-sector customer.  Idempotent — skips if one already exists.
    """
    if not _is_railway_customer(doc.customer):
        return

    # Guard against duplicates
    existing = frappe.db.get_value("CO7 Tracker", {"sales_invoice": doc.name}, "name")
    if existing:
        return

    # Try to pick up the railway_zone from the invoice custom field; fall back gracefully
    railway_zone = doc.get("custom_railway_zone") or ""

    co7 = frappe.get_doc({
        "doctype":       "CO7 Tracker",
        "sales_invoice": doc.name,
        "customer":      doc.customer,
        "invoice_date":  doc.posting_date,
        "invoice_amount": flt(doc.grand_total),
        "current_stage": "Invoice Raised",
        "railway_zone":  railway_zone,
    })
    co7.flags.ignore_permissions = True
    co7.insert()

    frappe.msgprint(
        msg=_(
            "CO7 Tracker <strong>{0}</strong> created automatically for "
            "Railway customer invoice {1}."
        ).format(co7.name, doc.name),
        title=_("CO7 Tracker Created"),
        indicator="green",
    )


def _is_railway_customer(customer_name):
    """Return True if the customer is in the Railways sector.

    Checks:
    1. Customer's custom_sector field (e.g. "Railways").
    2. Customer's customer_group field (e.g. "Indian Railways").
    """
    if not customer_name:
        return False

    try:
        cust = frappe.get_cached_doc("Customer", customer_name)
    except frappe.DoesNotExistError:
        return False

    sector = (cust.get("custom_sector") or "").lower()
    group  = (cust.customer_group or "").lower()
    combined = sector + " " + group

    return any(kw in combined for kw in RAILWAY_KEYWORDS)
