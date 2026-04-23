from . import __version__ as app_version

app_name        = "parasramka_erpnext"
app_title       = "Parasramka ERPNext"
app_publisher   = "Parasramka Engineering Pvt. Ltd."
app_description = "Custom ERP for Defence & Railways heavy engineering"
app_email       = "aviral.parasramka@gmail.com"
app_license     = "MIT"
app_version     = __version__

# ── Scheduled Tasks ───────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "parasramka_erpnext.parasramka_erpnext.doctype.co7_tracker.co7_tracker.check_co7_ageing",
    ],
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