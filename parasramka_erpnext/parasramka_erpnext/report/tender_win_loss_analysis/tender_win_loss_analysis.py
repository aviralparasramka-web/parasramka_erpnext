import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data, summary = get_data(filters)
    return columns, data, None, None, summary


def get_columns():
    return [
        {"fieldname": "tender_no",    "label": _("Tender No."),    "fieldtype": "Data",     "width": 130},
        {"fieldname": "tender_link",  "label": _("Record"),        "fieldtype": "Link",     "options": "Tender Management", "width": 80},
        {"fieldname": "item",         "label": _("Item"),          "fieldtype": "Data",     "width": 180},
        {"fieldname": "customer",     "label": _("Customer"),      "fieldtype": "Link",     "options": "Customer",          "width": 170},
        {"fieldname": "sector",       "label": _("Sector"),        "fieldtype": "Data",     "width": 90},
        {"fieldname": "our_price",    "label": _("Our Price"),     "fieldtype": "Currency",                                 "width": 120},
        {"fieldname": "l1_price",     "label": _("L1 Price"),      "fieldtype": "Currency",                                 "width": 120},
        {"fieldname": "outcome",      "label": _("Win / Loss"),    "fieldtype": "Data",                                     "width": 100},
        {"fieldname": "loss_reason",  "label": _("Loss Reason"),   "fieldtype": "Data",                                     "width": 130},
        {"fieldname": "bid_deadline", "label": _("Bid Deadline"),  "fieldtype": "Date",                                     "width": 110},
    ]


def get_data(filters):
    t_filters = {"status": ["in", ["Won", "Lost", "Submitted", "Cancelled"]]}

    if filters.get("customer"):
        t_filters["customer"] = filters["customer"]
    if filters.get("sector"):
        t_filters["sector"] = filters["sector"]
    if filters.get("from_date") and filters.get("to_date"):
        t_filters["bid_deadline"] = ["between", [filters["from_date"], filters["to_date"]]]
    elif filters.get("from_date"):
        t_filters["bid_deadline"] = [">=", filters["from_date"]]
    elif filters.get("to_date"):
        t_filters["bid_deadline"] = ["<=", filters["to_date"]]

    tenders = frappe.get_all(
        "Tender Management",
        filters=t_filters,
        fields=["name", "tender_no", "item", "customer", "sector",
                "estimated_value", "l1_price", "status", "loss_reason", "bid_deadline"],
        order_by="bid_deadline desc",
    )

    total = len(tenders)
    wins = sum(1 for t in tenders if t.status == "Won")
    win_rate = round((wins / total * 100), 1) if total else 0

    data = []
    for t in tenders:
        if t.status == "Won":
            outcome = '<span style="color:#27ae60; font-weight:bold;">✅ Won</span>'
        elif t.status == "Lost":
            outcome = '<span style="color:#c0392b; font-weight:bold;">❌ Lost</span>'
        else:
            outcome = f'<span style="color:#7f8c8d;">{t.status}</span>'

        data.append({
            "tender_no":    t.tender_no or t.name,
            "tender_link":  t.name,
            "item":         t.item or "—",
            "customer":     t.customer,
            "sector":       t.sector or "—",
            "our_price":    flt(t.estimated_value),
            "l1_price":     flt(t.l1_price),
            "outcome":      outcome,
            "loss_reason":  t.loss_reason or "—",
            "bid_deadline": t.bid_deadline,
        })

    # Summary row shown at the top of the report
    summary = [
        {"value": total, "label": _("Total Tenders"), "datatype": "Int", "indicator": "blue"},
        {"value": wins,  "label": _("Won"),           "datatype": "Int", "indicator": "green"},
        {"value": total - wins, "label": _("Lost / Other"), "datatype": "Int", "indicator": "red"},
        {"value": win_rate,     "label": _("Win Rate %"),   "datatype": "Float", "indicator": "blue"},
    ]

    return data, summary
