import frappe
from frappe import _
from frappe.utils import flt


# Pipeline stages in business-process order
STAGE_ORDER = [
    "Invoice Raised",
    "Dispatched",
    "R-Note Received",
    "Bills Submitted",
    "CO7 Issued",
    "Payment Received",
]


def execute(filters=None):
    columns = get_columns()
    data = get_data()
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns():
    return [
        {"fieldname": "stage",        "label": _("Stage"),              "fieldtype": "Data",     "width": 180},
        {"fieldname": "count",        "label": _("No. of Invoices"),    "fieldtype": "Int",      "width": 130},
        {"fieldname": "total_value",  "label": _("Total Value (₹)"),    "fieldtype": "Currency", "width": 160},
        {"fieldname": "avg_ageing",   "label": _("Avg. Days in Stage"), "fieldtype": "Float",    "precision": 1, "width": 160},
        {"fieldname": "oldest_days",  "label": _("Max Days in Stage"),  "fieldtype": "Int",      "width": 140},
    ]


def get_data():
    # Fetch all active CO7 records in one call, grouped by stage in Python
    records = frappe.get_all(
        "CO7 Tracker",
        fields=["current_stage", "invoice_amount", "ageing_days"],
    )

    # Build a dict: stage → list of records
    stage_buckets = {s: [] for s in STAGE_ORDER}
    for r in records:
        stage = r.current_stage or "Invoice Raised"
        if stage in stage_buckets:
            stage_buckets[stage].append(r)

    data = []
    for stage in STAGE_ORDER:
        bucket = stage_buckets[stage]
        count = len(bucket)
        if count == 0:
            data.append({
                "stage": stage, "count": 0,
                "total_value": 0, "avg_ageing": 0, "oldest_days": 0,
            })
            continue

        total_value = sum(flt(r.invoice_amount) for r in bucket)
        ageing_vals = [flt(r.ageing_days) for r in bucket if r.ageing_days]
        avg_ageing  = round(sum(ageing_vals) / len(ageing_vals), 1) if ageing_vals else 0
        oldest_days = max(ageing_vals) if ageing_vals else 0

        data.append({
            "stage":       stage,
            "count":       count,
            "total_value": total_value,
            "avg_ageing":  avg_ageing,
            "oldest_days": int(oldest_days),
        })

    return data


def get_chart(data):
    # Funnel-style bar chart showing count per stage
    labels = [r["stage"] for r in data]
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Invoices",    "values": [r["count"]        for r in data]},
                {"name": "Value (Lac)", "values": [round(r["total_value"] / 100000, 2) for r in data]},
            ],
        },
        "type": "bar",
        "colors": ["#003580", "#27ae60"],
        "barOptions": {"stacked": False},
    }
