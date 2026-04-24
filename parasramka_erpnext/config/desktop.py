from frappe import _


def get_data():
    return [
        {
            "module_name": "Parasramka ERPNext",
            "color": "#003580",
            "icon": "octicon octicon-tools",
            "type": "module",
            "label": _("Parasramka ERPNext"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Tender Management",
                    "label": _("Tender Management"),
                    "description": _("Track government tenders"),
                },
                {
                    "type": "doctype",
                    "name": "CO7 Tracker",
                    "label": _("CO7 Tracker"),
                    "description": _("Railway payment pipeline"),
                },
                {
                    "type": "doctype",
                    "name": "PSD Tracker",
                    "label": _("PSD Tracker"),
                    "description": _("Performance Security Deposit"),
                },
                {
                    "type": "doctype",
                    "name": "CST Cost Sheet",
                    "label": _("CST Cost Sheet"),
                    "description": _("Tender-based costing"),
                },
                {
                    "type": "page",
                    "name": "pepl-assistant",
                    "label": _("PEPL Assistant"),
                    "description": _("AI assistant for PEPL"),
                },
                {
                    "type": "report",
                    "name": "CO7 Pipeline Summary",
                    "label": _("CO7 Pipeline"),
                    "doctype": "CO7 Tracker",
                },
                {
                    "type": "report",
                    "name": "Outstanding Orders",
                    "label": _("Outstanding Orders"),
                    "doctype": "Sales Order",
                },
                {
                    "type": "report",
                    "name": "PSD Register",
                    "label": _("PSD Register"),
                    "doctype": "PSD Tracker",
                },
                {
                    "type": "report",
                    "name": "Payment Outstanding Ageing",
                    "label": _("Payment Ageing"),
                    "doctype": "Sales Invoice",
                },
                {
                    "type": "report",
                    "name": "Tender Win/Loss Analysis",
                    "label": _("Win/Loss Analysis"),
                    "doctype": "Tender Management",
                },
                {
                    "type": "report",
                    "name": "Monthly Sales Summary",
                    "label": _("Monthly Summary"),
                    "doctype": "Sales Invoice",
                },
                {
                    "type": "report",
                    "name": "Vendor Approval Status",
                    "label": _("Vendor Approvals"),
                    "doctype": "Customer",
                },
                {
                    "type": "report",
                    "name": "Quotation Conversion Rate",
                    "label": _("Quotation Conversion"),
                    "doctype": "Quotation",
                },
                {
                    "type": "report",
                    "name": "Letter Despatch Log",
                    "label": _("Letter Log"),
                    "doctype": "Sales Invoice",
                },
            ],
        }
    ]
