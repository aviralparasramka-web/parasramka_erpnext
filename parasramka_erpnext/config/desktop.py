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
                    "name": "Deploy Test",
                    "label": _("Deploy Test"),
                    "description": _("Diagnostic — verify Frappe Cloud build")
                }
            ]
        }
    ]
