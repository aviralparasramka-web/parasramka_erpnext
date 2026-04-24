"""
Sales Order — doc_events

on_submit:
  Linkage 3 — Auto-create PSD Tracker for every new SO.
  Linkage 8 — If SO carries a custom_tender_ref, mark that Tender as Won.
"""

import frappe
from frappe import _
from frappe.utils import flt


def on_submit(doc, method):
    _create_psd_tracker(doc)
    _update_tender_on_so_submit(doc)


# ── Linkage 3 ─────────────────────────────────────────────────────────────────

def _create_psd_tracker(doc):
    """Create a PSD Tracker the first time a Sales Order is submitted.

    If one already exists for this SO, skip silently — idempotent.
    """
    # Guard: check for existing tracker so we never create duplicates
    existing = frappe.db.get_value("PSD Tracker", {"sales_order": doc.name}, "name")
    if existing:
        return

    psd = frappe.get_doc({
        "doctype":    "PSD Tracker",
        "sales_order": doc.name,
        "customer":   doc.customer,
        "order_value": flt(doc.grand_total),
        # 5% PSD — mirrors the before_save logic in psd_tracker.py
        "psd_amount": flt(doc.grand_total) * 0.05,
        "status":     "Pending Submission",
    })
    psd.flags.ignore_permissions = True
    psd.insert()

    frappe.msgprint(
        msg=_(
            "PSD Tracker <strong>{0}</strong> created automatically for Sales Order {1}."
        ).format(psd.name, doc.name),
        title=_("PSD Tracker Created"),
        indicator="green",
    )


# ── Linkage 8 ─────────────────────────────────────────────────────────────────

def _update_tender_on_so_submit(doc):
    """If this SO was raised against a tender (via custom_tender_ref),
    mark the Tender as Won and back-link the SO.

    Assumes a Custom Field 'custom_tender_ref' of type Link→Tender Management
    exists on Sales Order (create via Customize Form if not present).
    """
    tender_ref = doc.get("custom_tender_ref")
    if not tender_ref:
        return  # not a tender-driven SO — nothing to do

    try:
        tender = frappe.get_doc("Tender Management", tender_ref)
    except frappe.DoesNotExistError:
        frappe.log_error(
            f"Tender '{tender_ref}' not found while updating from SO {doc.name}",
            "Linkage 8 — Tender Update",
        )
        return

    # Only advance if not already marked Won or Cancelled
    if tender.status not in ("Won", "Cancelled"):
        tender.status    = "Won"
        tender.linked_so = doc.name
        tender.flags.ignore_permissions = True
        tender.save()

        frappe.msgprint(
            msg=_(
                "Tender <strong>{0}</strong> marked as <strong>Won</strong> "
                "and linked to Sales Order {1}."
            ).format(tender.name, doc.name),
            title=_("Tender Updated"),
            indicator="green",
        )
