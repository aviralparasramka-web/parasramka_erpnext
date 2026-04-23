frappe.query_reports["Tender Win/Loss Analysis"] = {
    filters: [
        {
            fieldname: "sector",
            label: __("Sector"),
            fieldtype: "Select",
            options: "\nRailways\nDefence\nPrivate\nOthers",
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "from_date",
            label: __("Bid Deadline From"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
        },
        {
            fieldname: "to_date",
            label: __("Bid Deadline To"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
    ],
};
