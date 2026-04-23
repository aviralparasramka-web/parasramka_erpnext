import frappe
from frappe import _
from frappe.utils import getdate, nowdate, date_diff, flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "invoice_no",       "label": _("Invoice No."),       "fieldtype": "Link",     "options": "Sales Invoice", "width": 150},
        {"fieldname": "customer",         "label": _("Customer"),          "fieldtype": "Link",     "options": "Customer",      "width": 180},
        {"fieldname": "invoice_amount",   "label": _("Invoice Amt"),       "fieldtype": "Currency",                             "width": 120},
        {"fieldname": "bucket_0_30",      "label": _("0–30 Days"),         "fieldtype": "Currency",                             "width": 110},
        {"fieldname": "bucket_31_60",     "label": _("31–60 Days"),        "fieldtype": "Currency",                             "width": 110},
        {"fieldname": "bucket_61_90",     "label": _("61–90 Days"),        "fieldtype": "Currency",                             "width": 110},
        {"fieldname": "bucket_90_plus",   "label": _("90+ Days"),          "fieldtype": "Currency",                             "width": 110},
        {"fieldname": "total_outstanding","label": _("Total Outstanding"), "fieldtype": "Currency",                             "width": 140},
        {"fieldname": "co7_status",       "label": _("CO7 Status"),        "fieldtype": "Data",                                 "width": 150},
    ]


def get_data(filters):
    today = getdate(nowdate())

    inv_filters = {
        "docstatus": 1,
        "outstanding_amount": [">", 0],
    }
    if filters.get("customer"):
        inv_filters["customer"] = filters["customer"]
    if filters.get("from_date") and filters.get("to_date"):
        inv_filters["posting_date"] = ["between", [filters["from_date"], filters["to_date"]]]
    elif filters.get("from_date"):
        inv_filters["posting_date"] = [">=", filters["from_date"]]
    elif filters.get("to_date"):
        inv_filters["posting_date"] = ["<=", filters["to_date"]]

    invoices = frappe.get_all(
        "Sales Invoice",
        filters=inv_filters,
        fields=["name", "customer", "customer_name", "posting_date",
                "grand_total", "outstanding_amount"],
        order_by="posting_date asc",
    )

    if not invoices:
        return []

    # Build a CO7 lookup map — single query for all invoices
    co7_records = frappe.get_all(
        "CO7 Tracker",
        fields=["sales_invoice", "current_stage"],
    )
    co7_map = {r.sales_invoice: r.current_stage for r in co7_records}

    data = []
    for inv in invoices:
        age = date_diff(today, inv.posting_date) if inv.posting_date else 0
        outstanding = flt(inv.outstanding_amount)

        # Bucket the entire outstanding amount into the correct ageing slot
        bucket_0_30 = outstanding if age <= 30 else 0
        bucket_31_60 = outstanding if 31 <= age <= 60 else 0
        bucket_61_90 = outstanding if 61 <= age <= 90 else 0
        bucket_90_plus = outstanding if age > 90 else 0

        data.append({
            "invoice_no":        inv.name,
            "customer":          inv.customer,
            "invoice_amount":    flt(inv.grand_total),
            "bucket_0_30":       bucket_0_30,
            "bucket_31_60":      bucket_31_60,
            "bucket_61_90":      bucket_61_90,
            "bucket_90_plus":    bucket_90_plus,
            "total_outstanding": outstanding,
            "co7_status":        co7_map.get(inv.name, "No CO7 Record"),
        })

    return data
