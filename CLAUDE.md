# Parasramka Engineering — ERPNext Custom App

## Company Context
- Company: Parasramka Engineering Pvt. Ltd. (PEPL)
- Sector: Heavy Engineering — Defence & Railways
- ERP: ERPNext v16 on Frappe Cloud (managed hosting)
- App name: parasramka_erpnext
- GitHub: https://github.com/aviralparasramka-web/parasramka_erpnext
- Inner package: parasramka_erpnext/parasramka_erpnext/

## Business Context
- Engineer-to-Order (ETO) manufacturer
- Customers: Railway zones (Loco/Coaches/Zonal),
  Defence (MIL/YIL/AWEIL), Private
- Key modules to build:
  1. CO7 Tracker — Railway payment pipeline ✅ DONE
  2. Tender Management + CST costing ✅ DONE (Tender Management)
  3. PSD Tracker — Performance Security Deposit ✅ DONE
  4. Customer enrichment — vendor registration
  5. Jinja2 Print Formats — 8 letter types
  6. Reports — 9 custom reports
  7. Claude AI integration — Options A, B, D

## Technical Rules — ALWAYS Follow
- DocTypes go in:
  parasramka_erpnext/parasramka_erpnext/parasramka_erpnext/doctype/
- Every DocType needs exactly 4 files:
  doctype_name.json
  doctype_name.py
  doctype_name.js
  __init__.py
- Module name in all JSON files: "Parasramka ERPNext"
- All currency fields: INR
- Naming series format: CO7-.YYYY.-, TND-.YYYY.-, PSD-.YYYY.-
- Always use frappe.utils functions for dates
- Always use frappe.get_all() not raw SQL
- Always add inline comments on Python logic
- Always set track_changes: 1 on all DocTypes
- Never hardcode values — use frappe.db.get_value
- Scheduled tasks must be registered in hooks.py
- Doc events must be registered in hooks.py

## Deployment
- Claude Code writes files and pushes to GitHub
- Human clicks Pull on Frappe Cloud to deploy
- No SSH access to Frappe Cloud

## CO7 Tracker Fields
naming_series, sales_invoice, customer, railway_zone,
po_contract_no, invoice_date, invoice_amount,
current_stage (Invoice Raised / Dispatched /
R-Note Received / Bills Submitted / CO7 Issued /
Payment Received), ageing_days, dispatch_date,
lr_rr_no, transporter, consignee, r_note_no,
r_note_date, bill_submission_date, paying_authority,
co7_no, co7_date, payment_expected_date,
amount_received, payment_date, tds_deducted,
sd_ld_deduction, net_payment_received,
outstanding_amount, remarks

## CO7 Python Logic
- before_save: calculate ageing (today - invoice_date),
  net_payment (received - tds - sd_ld),
  outstanding (invoice_amount - net_payment),
  auto-advance stage based on fields filled,
  set payment_expected_date (co7_date + 7 days)
- validate: date sequence check, warn if
  amount_received > invoice_amount
- check_co7_ageing(): daily scheduler — find records
  with ageing > 90 days and stage != Payment Received,
  send email to Accounts Manager users

## Tender Management Fields
tender_no, item, drawing_no, drawing_rev,
specification, quantity, customer, sector,
railway_sub_sector, defence_sub_sector,
bid_deadline, emd_amount, emd_mode, emd_ref,
emd_expiry, estimated_value, status
(Upcoming/Submitted/Won/Lost/Cancelled),
linked_cost_sheet, linked_quotation, linked_so,
l1_price, loss_reason, remarks

## PSD Tracker Fields
sales_order, customer, order_value, psd_amount
(auto: 5% of order_value), psd_submitted,
submission_date, submission_doc, last_supply_date,
psd_expiry (auto: last_supply_date + 14 months),
ndc_received, ndc_date, ndc_doc,
refund_received, refund_date, status, remarks