frappe.ui.form.on('CO7 Tracker', {

    refresh(frm) {
        // Colour-badge the pipeline stage in the form header
        const palette = {
            'Invoice Raised':   'blue',
            'Dispatched':       'orange',
            'R-Note Received':  'yellow',
            'Bills Submitted':  'purple',
            'CO7 Issued':       'green',
            'Payment Received': 'darkgreen',
        };
        if (frm.doc.current_stage) {
            frm.page.set_indicator(
                frm.doc.current_stage,
                palette[frm.doc.current_stage] || 'grey'
            );
        }
    },

    // Auto-fill invoice fields when a Sales Invoice is selected
    sales_invoice(frm) {
        if (!frm.doc.sales_invoice) return;
        frappe.db.get_value(
            'Sales Invoice',
            frm.doc.sales_invoice,
            ['customer', 'posting_date', 'grand_total'],
            (r) => {
                if (!r) return;
                frm.set_value('customer',       r.customer);
                frm.set_value('invoice_date',   r.posting_date);
                frm.set_value('invoice_amount', r.grand_total);
            }
        );
    },

    // Recalculate derived payment fields on any payment input change
    amount_received(frm)  { _recalc_payment(frm); },
    tds_deducted(frm)     { _recalc_payment(frm); },
    sd_ld_deduction(frm)  { _recalc_payment(frm); },
    invoice_amount(frm)   { _recalc_payment(frm); },

    // Auto-set Payment Expected Date 7 days after CO7 Date
    co7_date(frm) {
        if (!frm.doc.co7_date) return;
        const expected = frappe.datetime.add_days(frm.doc.co7_date, 7);
        frm.set_value('payment_expected_date', expected);
    },
});

function _recalc_payment(frm) {
    const received = flt(frm.doc.amount_received);
    const tds      = flt(frm.doc.tds_deducted);
    const sd_ld    = flt(frm.doc.sd_ld_deduction);
    const net      = received - tds - sd_ld;
    const outstanding = flt(frm.doc.invoice_amount) - net;
    frm.set_value('net_payment_received', net);
    frm.set_value('outstanding_amount',   outstanding);
}
