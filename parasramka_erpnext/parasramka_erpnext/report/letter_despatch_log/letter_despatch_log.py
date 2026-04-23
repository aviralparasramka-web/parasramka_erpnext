import frappe
from frappe import _


# Map subject keywords to letter-type labels for readable display
LETTER_TYPE_KEYWORDS = {
    "NABL":       "RM Offer – NABL Lab",
    "Quotation":  "RM Offer – Customer",
    "Drawing":    "Drawing / Spec Request",
    "Inspection": "Proof Schedule Request",
    "Lot":        "Lot Request",
    "Bulk Lot":   "Bulk Lot Offer",
    "Payment":    "Payment Request",
    "Advance":    "Down Payment Request",
}


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "date",         "label": _("Date"),             "fieldtype": "Date",  "width": 100},
        {"fieldname": "letter_type",  "label": _("Letter Type"),      "fieldtype": "Data",  "width": 190},
        {"fieldname": "customer",     "label": _("Customer"),         "fieldtype": "Data",  "width": 180},
        {"fieldname": "subject",      "label": _("Subject"),          "fieldtype": "Data",  "width": 250},
        {"fieldname": "linked_doc",   "label": _("Linked Document"),  "fieldtype": "Data",  "width": 150},
        {"fieldname": "sent_by",      "label": _("Sent By"),          "fieldtype": "Data",  "width": 140},
    ]


def _infer_letter_type(subject):
    """Guess letter type from the Communication subject line."""
    subject_upper = (subject or "").upper()
    for keyword, label in LETTER_TYPE_KEYWORDS.items():
        if keyword.upper() in subject_upper:
            return label
    return "General Letter"


def get_data(filters):
    comm_filters = {
        "communication_type": "Communication",
        "sent_or_received": "Sent",
        "communication_medium": "Email",
    }
    if filters.get("from_date") and filters.get("to_date"):
        comm_filters["communication_date"] = ["between", [filters["from_date"], filters["to_date"]]]
    elif filters.get("from_date"):
        comm_filters["communication_date"] = [">=", filters["from_date"]]
    elif filters.get("to_date"):
        comm_filters["communication_date"] = ["<=", filters["to_date"]]

    comms = frappe.get_all(
        "Communication",
        filters=comm_filters,
        fields=["name", "communication_date", "subject", "recipients",
                "sender", "reference_doctype", "reference_name"],
        order_by="communication_date desc",
        limit=500,
    )

    data = []
    for c in comms:
        # Infer letter type from subject keywords
        letter_type = _infer_letter_type(c.subject)

        # Apply letter-type filter if set
        if filters.get("letter_type") and filters["letter_type"] != letter_type:
            continue

        # Customer name from recipient email or linked document
        customer = c.recipients or "—"
        if filters.get("customer") and filters["customer"].lower() not in customer.lower():
            continue

        linked = ""
        if c.reference_doctype and c.reference_name:
            linked = f"{c.reference_doctype}: {c.reference_name}"

        data.append({
            "date":        c.communication_date,
            "letter_type": letter_type,
            "customer":    customer,
            "subject":     c.subject or "—",
            "linked_doc":  linked or "—",
            "sent_by":     c.sender or "—",
        })

    return data
