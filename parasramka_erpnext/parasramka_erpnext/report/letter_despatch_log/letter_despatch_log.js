frappe.query_reports["Letter Despatch Log"] = {
    filters: [
        {
            fieldname: "letter_type",
            label: __("Letter Type"),
            fieldtype: "Select",
            options: [
                "",
                "RM Offer – NABL Lab",
                "RM Offer – Customer",
                "Drawing / Spec Request",
                "Proof Schedule Request",
                "Lot Request",
                "Bulk Lot Offer",
                "Payment Request",
                "Down Payment Request",
                "General Letter",
            ].join("\n"),
        },
        {
            fieldname: "customer",
            label: __("Customer (Email / Name)"),
            fieldtype: "Data",
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
    ],
};
