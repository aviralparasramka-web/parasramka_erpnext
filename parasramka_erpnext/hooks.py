app_version     = "0.0.1"

app_name        = "parasramka_erpnext"
app_title       = "Parasramka ERPNext"
app_publisher   = "Parasramka Engineering Pvt. Ltd."
app_description = "Custom ERP for Defence & Railways heavy engineering"
app_email       = "aviral.parasramka@gmail.com"
app_license     = "MIT"

# ── Scheduled Tasks ───────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "parasramka_erpnext.parasramka_erpnext.doctype.co7_tracker.co7_tracker.check_co7_ageing",
        "parasramka_erpnext.parasramka_erpnext.doctype.tender_management.tender_management.check_tender_deadlines",
        "parasramka_erpnext.parasramka_erpnext.doctype.psd_tracker.psd_tracker.check_psd_expiry",
    ],
}

# ── DocType JS Overrides ──────────────────────────────────────────────────────
# Injects "Draft with Claude" button into the Quotation form
doctype_js = {
    "Quotation": "public/js/quotation_claude.js",
}

# ── Page JS registration ──────────────────────────────────────────────────────
page_js = {
    "pepl-assistant": "parasramka_erpnext/parasramka_erpnext/page/pepl_assistant/pepl_assistant.js",
}

# ── Document Event Hooks ──────────────────────────────────────────────────────
doc_events = {
    # Linkage 3: Auto-create PSD Tracker on Sales Order submit
    # Linkage 8: Auto-mark Tender as Won if SO carries custom_tender_ref
    "Sales Order": {
        "on_submit": "parasramka_erpnext.parasramka_erpnext.doc_events.sales_order.on_submit",
    },
    # Linkage 4: Auto-create CO7 Tracker for Railway invoices
    "Sales Invoice": {
        "on_submit": "parasramka_erpnext.parasramka_erpnext.doc_events.sales_invoice.on_submit",
    },
    # Linkage 5: Advance CO7 stage to Dispatched on Delivery Note submit
    "Delivery Note": {
        "on_submit": "parasramka_erpnext.parasramka_erpnext.doc_events.delivery_note.on_submit",
    },
}

# ── Fixtures ──────────────────────────────────────────────────────────────────
# fixtures = [
#     {
#         "doctype": "Custom Field",
#         "filters": [["module", "=", "Parasramka ERPNext"]]
#     },
# ]