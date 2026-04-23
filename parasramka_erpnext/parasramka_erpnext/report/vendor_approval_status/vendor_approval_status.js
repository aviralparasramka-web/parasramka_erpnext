frappe.query_reports["Vendor Approval Status"] = {
    filters: [
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "sector",
            label: __("Sector / Customer Group"),
            fieldtype: "Link",
            options: "Customer Group",
        },
    ],
};
