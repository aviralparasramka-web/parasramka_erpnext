frappe.ui.form.on('CST Cost Sheet', {

    refresh(frm) {
        highlight_final_price(frm);
    },

    tender(frm) {
        if (!frm.doc.tender) {
            frm.set_value('item', '');
            frm.set_value('drawing_no', '');
            frm.set_value('drawing_rev', '');
            frm.set_value('customer', '');
            frm.set_value('sector', '');
            frm.set_value('total_quantity', 0);
            recalculate_all(frm);
            return;
        }
        // Fetch all header fields from the selected Tender
        frappe.db.get_value(
            'Tender Management',
            frm.doc.tender,
            ['item', 'drawing_no', 'drawing_rev', 'customer', 'sector', 'quantity'],
            (values) => {
                frm.set_value('item', values.item);
                frm.set_value('drawing_no', values.drawing_no);
                frm.set_value('drawing_rev', values.drawing_rev);
                frm.set_value('customer', values.customer);
                frm.set_value('sector', values.sector);
                frm.set_value('total_quantity', values.quantity);
                // After total_quantity is set, recalculate all BOM rows
                recalculate_all(frm);
            }
        );
    },

    total_quantity(frm) {
        recalculate_all(frm);
    },

    machining_cost(frm) {
        recalculate_totals(frm);
    },

    overhead_percent(frm) {
        recalculate_totals(frm);
    },

    profit_percent(frm) {
        recalculate_totals(frm);
    },
});

// ── Child table event handlers ────────────────────────────────────────────────

frappe.ui.form.on('CST BOM Item', {

    qty_per_unit(frm, cdt, cdn) {
        recalculate_row(frm, cdt, cdn);
    },

    rate(frm, cdt, cdn) {
        recalculate_row(frm, cdt, cdn);
    },

    cst_bom_items_remove(frm) {
        // Recalculate totals when a row is deleted
        recalculate_totals(frm);
    },
});

// ── Calculation helpers ───────────────────────────────────────────────────────

function recalculate_row(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const total_qty = flt(row.qty_per_unit) * flt(frm.doc.total_quantity);
    const amount = total_qty * flt(row.rate);
    // Use frappe.model.set_value so the grid cell refreshes immediately
    frappe.model.set_value(cdt, cdn, 'total_qty', total_qty);
    frappe.model.set_value(cdt, cdn, 'amount', amount);
    recalculate_totals(frm);
}

function recalculate_all(frm) {
    // Recalculate every BOM row (called when total_quantity or tender changes)
    (frm.doc.cst_bom_items || []).forEach((row) => {
        const total_qty = flt(row.qty_per_unit) * flt(frm.doc.total_quantity);
        const amount = total_qty * flt(row.rate);
        frappe.model.set_value(row.doctype, row.name, 'total_qty', total_qty);
        frappe.model.set_value(row.doctype, row.name, 'amount', amount);
    });
    recalculate_totals(frm);
}

function recalculate_totals(frm) {
    // Sum all BOM amounts
    const total_rm = (frm.doc.cst_bom_items || []).reduce(
        (sum, r) => sum + flt(r.amount), 0
    );
    frm.set_value('total_rm_cost', total_rm);

    // Overhead on (RM + machining)
    const base = total_rm + flt(frm.doc.machining_cost);
    const overhead = base * flt(frm.doc.overhead_percent) / 100;
    frm.set_value('overhead_amount', overhead);

    // Profit on (RM + machining + overhead)
    const before_profit = base + overhead;
    const profit = before_profit * flt(frm.doc.profit_percent) / 100;
    frm.set_value('profit_amount', profit);

    // Final calculated price
    const final_price = before_profit + profit;
    frm.set_value('final_unit_price', final_price);

    highlight_final_price(frm);
}

function highlight_final_price(frm) {
    if (!frm.doc.final_unit_price) return;

    // Show final price prominently in the form header
    const formatted = frappe.format(
        frm.doc.final_unit_price,
        { fieldtype: 'Currency', options: 'INR' }
    );
    const proposed = frm.doc.proposed_price
        ? ` &nbsp;|&nbsp; Proposed: <strong>${frappe.format(frm.doc.proposed_price, { fieldtype: 'Currency', options: 'INR' })}</strong>`
        : '';

    frm.dashboard.set_headline_alert(
        `<span style="font-size:1.1em;">
            Calculated Price: <strong style="color:#003580;">${formatted}</strong>${proposed}
        </span>`
    );
}
