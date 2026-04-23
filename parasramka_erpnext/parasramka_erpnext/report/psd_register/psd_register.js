frappe.query_reports["PSD Register"] = {
    filters: [
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Select",
            options: "\nPending Submission\nSubmitted\nNDC Awaited\nRefund Awaited\nClosed",
        },
    ],
};
