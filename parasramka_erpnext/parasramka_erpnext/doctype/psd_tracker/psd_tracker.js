frappe.ui.form.on('PSD Tracker', {

    refresh(frm) {
        toggle_submission_fields(frm);
        toggle_ndc_fields(frm);
        toggle_refund_fields(frm);
        show_expiry_warning(frm);
    },

    sales_order(frm) {
        if (!frm.doc.sales_order) {
            frm.set_value('customer', '');
            frm.set_value('order_value', 0);
            frm.set_value('psd_amount', 0);
            return;
        }
        // Fetch customer and grand_total from the selected Sales Order
        frappe.db.get_value('Sales Order', frm.doc.sales_order,
            ['customer', 'grand_total'],
            (values) => {
                frm.set_value('customer', values.customer);
                frm.set_value('order_value', values.grand_total);
                // Immediately reflect the 5% PSD calculation in the UI
                frm.set_value('psd_amount', flt(values.grand_total) * 0.05);
            }
        );
    },

    order_value(frm) {
        // Recalculate PSD whenever order value changes
        frm.set_value('psd_amount', flt(frm.doc.order_value) * 0.05);
    },

    psd_submitted(frm) {
        toggle_submission_fields(frm);
        update_status_preview(frm);
    },

    last_supply_date(frm) {
        calculate_psd_expiry(frm);
        update_status_preview(frm);
        show_expiry_warning(frm);
    },

    ndc_received(frm) {
        toggle_ndc_fields(frm);
        update_status_preview(frm);
    },

    refund_received(frm) {
        toggle_refund_fields(frm);
        update_status_preview(frm);
    },
});

// ── Helper functions ──────────────────────────────────────────────────────────

function toggle_submission_fields(frm) {
    // Show submission date and document only when PSD has been submitted
    const submitted = frm.doc.psd_submitted == 1;
    frm.toggle_display('submission_date', submitted);
    frm.toggle_display('submission_doc', submitted);
}

function toggle_ndc_fields(frm) {
    // Show NDC date and document only when NDC has been received
    const received = frm.doc.ndc_received == 1;
    frm.toggle_display('ndc_date', received);
    frm.toggle_display('ndc_doc', received);
}

function toggle_refund_fields(frm) {
    // Show refund date only when refund has been received
    frm.toggle_display('refund_date', frm.doc.refund_received == 1);
}

function calculate_psd_expiry(frm) {
    if (!frm.doc.last_supply_date) {
        frm.set_value('psd_expiry', '');
        return;
    }
    // Mirror the Python constant: 425 days = ~14 months
    const expiry = frappe.datetime.add_days(frm.doc.last_supply_date, 425);
    frm.set_value('psd_expiry', expiry);
}

function show_expiry_warning(frm) {
    if (!frm.doc.psd_expiry || frm.doc.status === 'Closed') return;

    const today = frappe.datetime.get_today();
    const days_left = frappe.datetime.get_diff(frm.doc.psd_expiry, today);

    if (days_left < 0) {
        frm.dashboard.set_headline_alert(
            `<span class="text-danger">PSD has EXPIRED (${Math.abs(days_left)} days ago). Take immediate action.</span>`
        );
    } else if (days_left <= 30) {
        frm.dashboard.set_headline_alert(
            `<span class="text-warning">PSD expires in ${days_left} day(s) on ${frm.doc.psd_expiry}. Follow up for NDC / refund.</span>`
        );
    }
}

function update_status_preview(frm) {
    // Mirror the Python status logic so the user sees the new status
    // immediately before saving, without a round-trip to the server
    let new_status;
    if (frm.doc.refund_received) {
        new_status = 'Closed';
    } else if (frm.doc.ndc_received) {
        new_status = 'Refund Awaited';
    } else if (frm.doc.psd_submitted && frm.doc.last_supply_date) {
        new_status = 'NDC Awaited';
    } else if (frm.doc.psd_submitted) {
        new_status = 'Submitted';
    } else {
        new_status = 'Pending Submission';
    }
    frm.set_value('status', new_status);
}
