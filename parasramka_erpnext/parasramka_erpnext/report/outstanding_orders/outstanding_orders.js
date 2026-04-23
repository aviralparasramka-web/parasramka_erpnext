frappe.query_reports["Outstanding Orders"] = {
    filters: [
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "from_date",
            label: __("Order Date From"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
        },
        {
            fieldname: "to_date",
            label: __("Order Date To"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
    ],
};
