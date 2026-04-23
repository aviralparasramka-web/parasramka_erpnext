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

# ── Document Event Hooks ──────────────────────────────────────────────────────
# doc_events = {
#     "Sales Invoice": {
#         "on_submit": "parasramka_erpnext.overrides.sales_invoice.on_submit",
#     },
# }

# ── Fixtures ──────────────────────────────────────────────────────────────────
# fixtures = [
#     {
#         "doctype": "Custom Field",
#         "filters": [["module", "=", "Parasramka ERPNext"]]
#     },
# ]