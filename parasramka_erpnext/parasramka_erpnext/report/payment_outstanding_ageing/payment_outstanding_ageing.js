frappe.query_reports["Payment Outstanding Ageing"] = {
    filters: [
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "from_date",
            label: __("Invoice Date From"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
        },
        {
            fieldname: "to_date",
            label: __("Invoice Date To"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
    ],
};
