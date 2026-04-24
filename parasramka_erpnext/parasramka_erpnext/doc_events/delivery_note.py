"""
Delivery Note — doc_events

on_submit:
  Linkage 5 — Advance linked CO7 Tracker stage from "Invoice Raised"
              to "Dispatched" and populate dispatch fields automatically.
"""

import frappe
from frappe import _
from frappe.utils import flt


def on_submit(doc, method):
    _advance_co7_stage(doc)


# ── Linkage 5 ─────────────────────────────────────────────────────────────────

def _advance_co7_stage(doc):
    """Find Sales Invoice(s) linked to this Delivery Note, then advance
    any CO7 Tracker that is still at the 'Invoice Raised' stage.

    Route: Delivery Note items → Sales Order → Sales Invoice → CO7 Tracker.
    We also attempt a direct DN→Invoice link via Sales Invoice Item.
    """
    invoice_names = _find_invoices_for_dn(doc)
    if not invoice_names:
        return

    advanced = []
    for inv_name in invoice_names:
        co7_name = frappe.db.get_value(
            "CO7 Tracker", {"sales_invoice": inv_name}, "name"
        )
        if not co7_name:
            continue

        co7 = frappe.get_doc("CO7 Tracker", co7_name)

        # Only advance if we're still at the very first stage
        if co7.current_stage != "Invoice Raised":
            continue

        co7.current_stage = "Dispatched"
        co7.dispatch_date = doc.posting_date
        co7.delivery_note = doc.name          # back-link to this DN (new field added in Linkage 7)

        # Populate transporter details from Delivery Note fields (graceful fallback)
        co7.lr_rr_no    = doc.get("lr_no") or doc.get("lr_rr_no") or co7.lr_rr_no
        co7.transporter = doc.get("transporter_name") or doc.get("transporter") or co7.transporter

        # Append an audit note rather than overwriting existing remarks
        note = f"Stage auto-advanced to 'Dispatched' from Delivery Note {doc.name}."
        co7.remarks = (co7.remarks + "\n" + note).strip() if co7.remarks else note

        co7.flags.ignore_permissions = True
        co7.save()
        advanced.append(co7.name)

    if advanced:
        frappe.msgprint(
            msg=_(
                "CO7 Tracker(s) advanced to <strong>Dispatched</strong>: {0}"
            ).format(", ".join(advanced)),
            title=_("CO7 Stage Advanced"),
            indicator="blue",
        )


def _find_invoices_for_dn(doc):
    """Return a de-duplicated list of Sales Invoice names related to this DN.

    Strategy 1 (most direct): look for Sales Invoice Items that reference
    this Delivery Note's items via dn_detail.
    Strategy 2 (fallback): go via Sales Order → Sales Invoice.
    """
    invoice_names = set()

    # Strategy 1 — Sales Invoice Item table has a 'delivery_note' column
    # (standard ERPNext field that stores which DN the SI item came from)
    si_items = frappe.get_all(
        "Sales Invoice Item",
        filters={"delivery_note": doc.name, "docstatus": 1},
        pluck="parent",
    )
    invoice_names.update(si_items)

    if invoice_names:
        return list(invoice_names)

    # Strategy 2 — collect Sales Orders referenced in this DN's items
    so_names = set()
    for item in doc.items:
        so = item.get("against_sales_order") or item.get("sales_order")
        if so:
            so_names.add(so)

    for so_name in so_names:
        si_items_via_so = frappe.get_all(
            "Sales Invoice Item",
            filters={"sales_order": so_name, "docstatus": 1},
            pluck="parent",
        )
        invoice_names.update(si_items_via_so)

    return list(invoice_names)
