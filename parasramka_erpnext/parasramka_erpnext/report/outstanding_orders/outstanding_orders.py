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
        {"fieldname": "so_no",        "label": _("SO No."),        "fieldtype": "Link",     "options": "Sales Order", "width": 140},
        {"fieldname": "customer",     "label": _("Customer"),      "fieldtype": "Link",     "options": "Customer",    "width": 180},
        {"fieldname": "item",         "label": _("Item"),          "fieldtype": "Data",                               "width": 180},
        {"fieldname": "order_value",  "label": _("Order Value"),   "fieldtype": "Currency",                           "width": 120},
        {"fieldname": "delivery_date","label": _("Delivery Date"), "fieldtype": "Date",                               "width": 110},
        {"fieldname": "days_overdue", "label": _("Days Overdue"),  "fieldtype": "Int",                                "width": 110},
        {"fieldname": "status",       "label": _("Status"),        "fieldtype": "Data",                               "width": 110},
        {"fieldname": "alert",        "label": _("Alert"),         "fieldtype": "Data",                               "width": 140},
    ]


def get_data(filters):
    today = getdate(nowdate())

    # Build dynamic filter list for frappe.get_all
    so_filters = {
        "docstatus": 1,
        "status": ["not in", ["Completed", "Cancelled", "Closed"]],
    }
    if filters.get("customer"):
        so_filters["customer"] = filters["customer"]
    if filters.get("from_date"):
        so_filters["transaction_date"] = [">=", filters["from_date"]]
    if filters.get("to_date"):
        # Override to a between filter if both dates provided
        if filters.get("from_date"):
            so_filters["transaction_date"] = ["between", [filters["from_date"], filters["to_date"]]]
        else:
            so_filters["transaction_date"] = ["<=", filters["to_date"]]

    orders = frappe.get_all(
        "Sales Order",
        filters=so_filters,
        fields=["name", "customer", "customer_name", "grand_total", "delivery_date",
                "transaction_date", "status"],
        order_by="delivery_date asc",
    )

    # Fetch the first item per Sales Order in one query, then build a lookup dict
    so_names = [o.name for o in orders]
    if not so_names:
        return []

    so_items = frappe.get_all(
        "Sales Order Item",
        filters={"parent": ["in", so_names], "idx": 1},
        fields=["parent", "item_code", "item_name"],
    )
    item_map = {i.parent: (i.item_name or i.item_code) for i in so_items}

    data = []
    for so in orders:
        # Calculate how many days until/past the delivery date
        days_diff = date_diff(so.delivery_date, today) if so.delivery_date else None

        if days_diff is None:
            days_overdue = 0
            alert = '<span style="color:#888;">No Date</span>'
        elif days_diff < 0:
            # Past the delivery date — overdue
            days_overdue = abs(days_diff)
            alert = f'<span style="color:#c0392b; font-weight:bold;">🔴 Overdue ({days_overdue}d)</span>'
        elif days_diff <= 7:
            # Due within the next 7 days — amber warning
            days_overdue = 0
            alert = f'<span style="color:#e67e22; font-weight:bold;">🟡 Due in {days_diff}d</span>'
        else:
            # Comfortably on track
            days_overdue = 0
            alert = '<span style="color:#27ae60;">🟢 On Track</span>'

        data.append({
            "so_no":         so.name,
            "customer":      so.customer,
            "item":          item_map.get(so.name, "—"),
            "order_value":   flt(so.grand_total),
            "delivery_date": so.delivery_date,
            "days_overdue":  days_overdue,
            "status":        so.status,
            "alert":         alert,
        })

    return data
