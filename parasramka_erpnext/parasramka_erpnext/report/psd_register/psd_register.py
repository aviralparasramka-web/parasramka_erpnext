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
        {"fieldname": "psd_ref",         "label": _("PSD Ref."),         "fieldtype": "Link",     "options": "PSD Tracker", "width": 130},
        {"fieldname": "sales_order",     "label": _("Sales Order"),      "fieldtype": "Link",     "options": "Sales Order", "width": 140},
        {"fieldname": "customer",        "label": _("Customer"),         "fieldtype": "Link",     "options": "Customer",    "width": 180},
        {"fieldname": "order_value",     "label": _("Order Value"),      "fieldtype": "Currency",                           "width": 120},
        {"fieldname": "psd_amount",      "label": _("PSD Amount"),       "fieldtype": "Currency",                           "width": 120},
        {"fieldname": "submission_date", "label": _("Submitted On"),     "fieldtype": "Date",                               "width": 110},
        {"fieldname": "last_supply_date","label": _("Last Supply"),      "fieldtype": "Date",                               "width": 110},
        {"fieldname": "psd_expiry",      "label": _("PSD Expiry"),       "fieldtype": "Date",                               "width": 110},
        {"fieldname": "days_to_expiry",  "label": _("Days to Expiry"),   "fieldtype": "Int",                                "width": 120},
        {"fieldname": "ndc_status",      "label": _("NDC Status"),       "fieldtype": "Data",                               "width": 120},
        {"fieldname": "status",          "label": _("Status"),           "fieldtype": "Data",                               "width": 140},
    ]


def get_data(filters):
    today = getdate(nowdate())

    psd_filters = {}
    if filters.get("customer"):
        psd_filters["customer"] = filters["customer"]
    if filters.get("status"):
        psd_filters["status"] = filters["status"]

    records = frappe.get_all(
        "PSD Tracker",
        filters=psd_filters,
        fields=["name", "sales_order", "customer", "order_value", "psd_amount",
                "submission_date", "last_supply_date", "psd_expiry",
                "ndc_received", "status"],
        order_by="psd_expiry asc",
    )

    data = []
    for r in records:
        # Days to expiry — negative means already expired
        if r.psd_expiry:
            days_to_expiry = date_diff(r.psd_expiry, today)
        else:
            days_to_expiry = None

        # Build a coloured status indicator
        if r.status == "Closed":
            status_html = '<span style="color:#27ae60; font-weight:bold;">✅ Closed</span>'
        elif days_to_expiry is not None and days_to_expiry < 0:
            status_html = f'<span style="color:#c0392b; font-weight:bold;">🔴 EXPIRED ({abs(days_to_expiry)}d ago)</span>'
        elif days_to_expiry is not None and days_to_expiry <= 60:
            status_html = f'<span style="color:#e67e22; font-weight:bold;">🟡 Expiring ({days_to_expiry}d)</span>'
        else:
            status_html = f'<span style="color:#2980b9;">{r.status}</span>'

        data.append({
            "psd_ref":          r.name,
            "sales_order":      r.sales_order,
            "customer":         r.customer,
            "order_value":      flt(r.order_value),
            "psd_amount":       flt(r.psd_amount),
            "submission_date":  r.submission_date,
            "last_supply_date": r.last_supply_date,
            "psd_expiry":       r.psd_expiry,
            "days_to_expiry":   days_to_expiry if days_to_expiry is not None else "—",
            "ndc_status":       "Received" if r.ndc_received else "Pending",
            "status":           status_html,
        })

    return data
