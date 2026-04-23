frappe.query_reports["Monthly Sales Summary"] = {
    filters: [
        {
            fieldname: "year",
            label: __("Year"),
            fieldtype: "Select",
            options: (function () {
                const current = new Date().getFullYear();
                return [current, current - 1, current - 2, current - 3, current - 4]
                    .map(String).join("\n");
            })(),
            default: String(new Date().getFullYear()),
            reqd: 1,
        },
    ],
};
