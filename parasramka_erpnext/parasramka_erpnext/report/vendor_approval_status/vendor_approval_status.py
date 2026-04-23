import frappe
from frappe import _
from frappe.utils import getdate, nowdate, date_diff


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "customer",         "label": _("Customer"),           "fieldtype": "Link",  "options": "Customer", "width": 200},
        {"fieldname": "customer_group",   "label": _("Sector / Group"),     "fieldtype": "Data",                         "width": 130},
        {"fieldname": "approved_items",   "label": _("Approved Items"),     "fieldtype": "Data",                         "width": 180},
        {"fieldname": "reg_expiry",       "label": _("Registration Expiry"),"fieldtype": "Date",                         "width": 140},
        {"fieldname": "days_to_expiry",   "label": _("Days to Expiry"),     "fieldtype": "Int",                          "width": 120},
        {"fieldname": "vendor_code",      "label": _("Vendor Code"),        "fieldtype": "Data",                         "width": 130},
        {"fieldname": "status",           "label": _("Status"),             "fieldtype": "Data",                         "width": 160},
    ]


def get_data(filters):
    today = getdate(nowdate())

    cust_filters = {"disabled": 0}
    if filters.get("customer"):
        cust_filters["name"] = filters["customer"]
    if filters.get("sector"):
        cust_filters["customer_group"] = filters["sector"]

    customers = frappe.get_all(
        "Customer",
        filters=cust_filters,
        fields=["name", "customer_name", "customer_group",
                "custom_approved_items", "custom_vendor_reg_expiry",
                "custom_vendor_code"],
        order_by="custom_vendor_reg_expiry asc",
    )

    data = []
    for c in customers:
        expiry = c.get("custom_vendor_reg_expiry")
        if expiry:
            days_left = date_diff(expiry, today)
            if days_left < 0:
                status = f'<span style="color:#c0392b; font-weight:bold;">🔴 Expired ({abs(days_left)}d ago)</span>'
            elif days_left <= 60:
                status = f'<span style="color:#e67e22; font-weight:bold;">🟡 Expiring in {days_left}d</span>'
            else:
                status = '<span style="color:#27ae60;">🟢 Active</span>'
        else:
            days_left = None
            status = '<span style="color:#7f8c8d;">No Expiry Recorded</span>'

        data.append({
            "customer":       c.name,
            "customer_group": c.customer_group or "—",
            "approved_items": c.get("custom_approved_items") or "—",
            "reg_expiry":     expiry,
            "days_to_expiry": days_left,
            "vendor_code":    c.get("custom_vendor_code") or "—",
            "status":         status,
        })

    return data
