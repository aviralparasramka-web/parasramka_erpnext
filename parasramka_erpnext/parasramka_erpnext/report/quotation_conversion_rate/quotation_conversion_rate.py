import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "customer",         "label": _("Customer"),            "fieldtype": "Link",  "options": "Customer", "width": 200},
        {"fieldname": "quotations_raised","label": _("Quotations Raised"),   "fieldtype": "Int",                          "width": 140},
        {"fieldname": "orders_received",  "label": _("Orders Received"),     "fieldtype": "Int",                          "width": 140},
        {"fieldname": "conversion_rate",  "label": _("Conversion Rate %"),   "fieldtype": "Float", "precision": 1,        "width": 150},
        {"fieldname": "total_quoted",     "label": _("Total Quoted Value"),  "fieldtype": "Currency",                     "width": 160},
        {"fieldname": "total_ordered",    "label": _("Total Order Value"),   "fieldtype": "Currency",                     "width": 160},
    ]


def get_data(filters):
    q_filters = {"docstatus": 1}
    if filters.get("customer"):
        q_filters["party_name"] = filters["customer"]
    if filters.get("from_date") and filters.get("to_date"):
        q_filters["transaction_date"] = ["between", [filters["from_date"], filters["to_date"]]]
    elif filters.get("from_date"):
        q_filters["transaction_date"] = [">=", filters["from_date"]]
    elif filters.get("to_date"):
        q_filters["transaction_date"] = ["<=", filters["to_date"]]

    quotations = frappe.get_all(
        "Quotation",
        filters=q_filters,
        fields=["name", "party_name", "grand_total", "status"],
    )

    # Aggregate by customer
    customer_map = {}
    for q in quotations:
        cust = q.party_name or "Unknown"
        if cust not in customer_map:
            customer_map[cust] = {"quotations": 0, "quoted_value": 0.0,
                                   "orders": 0,     "order_value": 0.0}
        customer_map[cust]["quotations"] += 1
        customer_map[cust]["quoted_value"] += flt(q.grand_total)
        # A quotation status of "Ordered" means it converted to a Sales Order
        if q.status == "Ordered":
            customer_map[cust]["orders"] += 1

    # Get total order values per customer within the same period using Sales Orders
    so_filters = {"docstatus": 1}
    if filters.get("customer"):
        so_filters["customer"] = filters["customer"]
    if filters.get("from_date") and filters.get("to_date"):
        so_filters["transaction_date"] = ["between", [filters["from_date"], filters["to_date"]]]

    orders = frappe.get_all(
        "Sales Order",
        filters=so_filters,
        fields=["customer", "grand_total"],
    )
    for o in orders:
        cust = o.customer
        if cust in customer_map:
            customer_map[cust]["order_value"] += flt(o.grand_total)

    data = []
    for customer, vals in sorted(customer_map.items()):
        rate = round(vals["orders"] / vals["quotations"] * 100, 1) if vals["quotations"] else 0.0
        data.append({
            "customer":          customer,
            "quotations_raised": vals["quotations"],
            "orders_received":   vals["orders"],
            "conversion_rate":   rate,
            "total_quoted":      vals["quoted_value"],
            "total_ordered":     vals["order_value"],
        })

    # Sort by conversion rate descending
    data.sort(key=lambda x: x["conversion_rate"], reverse=True)
    return data
