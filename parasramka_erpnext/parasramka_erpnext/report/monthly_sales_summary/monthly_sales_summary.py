import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate
from calendar import monthrange
import calendar as cal_mod


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns():
    return [
        {"fieldname": "month_label",    "label": _("Month"),              "fieldtype": "Data",     "width": 110},
        {"fieldname": "new_orders",     "label": _("New Orders (₹)"),     "fieldtype": "Currency", "width": 140},
        {"fieldname": "despatches",     "label": _("Despatches (₹)"),     "fieldtype": "Currency", "width": 140},
        {"fieldname": "invoices_raised","label": _("Invoices Raised (₹)"),"fieldtype": "Currency", "width": 150},
        {"fieldname": "collections",    "label": _("Collections (₹)"),    "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    year = int(filters.get("year") or getdate(nowdate()).year)
    data = []

    for month in range(1, 13):
        _, last_day = monthrange(year, month)
        start = f"{year}-{month:02d}-01"
        end   = f"{year}-{month:02d}-{last_day:02d}"
        date_range = ["between", [start, end]]

        # New orders booked this month
        orders = frappe.get_all(
            "Sales Order",
            filters={"docstatus": 1, "transaction_date": date_range},
            fields=["grand_total"],
        )
        order_value = sum(flt(o.grand_total) for o in orders)

        # Despatches (Delivery Notes posted this month)
        dns = frappe.get_all(
            "Delivery Note",
            filters={"docstatus": 1, "posting_date": date_range},
            fields=["grand_total"],
        )
        despatch_value = sum(flt(d.grand_total) for d in dns)

        # Invoices raised this month
        invs = frappe.get_all(
            "Sales Invoice",
            filters={"docstatus": 1, "posting_date": date_range},
            fields=["grand_total"],
        )
        invoice_value = sum(flt(i.grand_total) for i in invs)

        # Collections received (Payment Entries) this month
        payments = frappe.get_all(
            "Payment Entry",
            filters={"docstatus": 1, "payment_type": "Receive", "posting_date": date_range},
            fields=["paid_amount"],
        )
        collection_value = sum(flt(p.paid_amount) for p in payments)

        data.append({
            "month_label":     cal_mod.month_abbr[month] + f" {year}",
            "new_orders":      order_value,
            "despatches":      despatch_value,
            "invoices_raised": invoice_value,
            "collections":     collection_value,
        })

    return data


def get_chart(data):
    # Simple bar chart showing all four metrics per month
    labels = [row["month_label"] for row in data]
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "New Orders",      "values": [r["new_orders"]      for r in data]},
                {"name": "Invoices Raised", "values": [r["invoices_raised"] for r in data]},
                {"name": "Collections",     "values": [r["collections"]     for r in data]},
            ],
        },
        "type": "bar",
        "colors": ["#003580", "#27ae60", "#e67e22"],
        "barOptions": {"stacked": False},
    }
