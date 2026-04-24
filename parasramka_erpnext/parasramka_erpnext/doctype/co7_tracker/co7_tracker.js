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

        // ── Linkage 9: cross-module navigation buttons ─────────────────────
        _add_navigation_buttons(frm);
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

// ── Linkage 9 helpers ─────────────────────────────────────────────────────────

function _add_navigation_buttons(frm) {
    // Remove stale buttons first so they don't accumulate on re-render
    frm.remove_custom_button(__('View Sales Order'),  __('Navigate'));
    frm.remove_custom_button(__('View PSD Tracker'),  __('Navigate'));
    frm.remove_custom_button(__('View Sales Invoice'), __('Navigate'));

    if (frm.doc.__islocal) return;

    // Sales Invoice is always linkable (core field)
    if (frm.doc.sales_invoice) {
        frm.add_custom_button(__('View Sales Invoice'), () => {
            frappe.set_route('Form', 'Sales Invoice', frm.doc.sales_invoice);
        }, __('Navigate'));
    }

    // Sales Order (new Linkage 7 field)
    if (frm.doc.sales_order) {
        frm.add_custom_button(__('View Sales Order'), () => {
            frappe.set_route('Form', 'Sales Order', frm.doc.sales_order);
        }, __('Navigate'));
    }

    // PSD Tracker (new Linkage 7 field, auto-filled by Linkage 6 logic)
    if (frm.doc.psd_tracker) {
        frm.add_custom_button(__('View PSD Tracker'), () => {
            frappe.set_route('Form', 'PSD Tracker', frm.doc.psd_tracker);
        }, __('Navigate'));
    } else if (frm.doc.sales_order) {
        // If psd_tracker field not yet populated, try to find one on-the-fly
        frappe.db.get_value('PSD Tracker', { sales_order: frm.doc.sales_order }, 'name',
            (r) => {
                if (r && r.name) {
                    frm.add_custom_button(__('View PSD Tracker'), () => {
                        frappe.set_route('Form', 'PSD Tracker', r.name);
                    }, __('Navigate'));
                }
            }
        );
    }
}

function _recalc_payment(frm) {
    const received = flt(frm.doc.amount_received);
    const tds      = flt(frm.doc.tds_deducted);
    const sd_ld    = flt(frm.doc.sd_ld_deduction);
    const net      = received - tds - sd_ld;
    const outstanding = flt(frm.doc.invoice_amount) - net;
    frm.set_value('net_payment_received', net);
    frm.set_value('outstanding_amount',   outstanding);
}
