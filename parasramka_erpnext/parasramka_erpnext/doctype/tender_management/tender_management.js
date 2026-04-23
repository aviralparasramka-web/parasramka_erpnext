frappe.ui.form.on('Tender Management', {

    refresh(frm) {
        toggle_sub_sectors(frm);
        toggle_loss_fields(frm);
        add_cost_sheet_button(frm);
    },

    sector(frm) {
        // Clear the now-irrelevant sub-sector value before hiding it
        if (frm.doc.sector === 'Railways') {
            frm.set_value('defence_sub_sector', '');
        } else if (frm.doc.sector === 'Defence') {
            frm.set_value('railway_sub_sector', '');
        } else {
            frm.set_value('railway_sub_sector', '');
            frm.set_value('defence_sub_sector', '');
        }
        toggle_sub_sectors(frm);
    },

    status(frm) {
        toggle_loss_fields(frm);
        add_cost_sheet_button(frm);
    },

    bid_deadline(frm) {
        if (!frm.doc.bid_deadline) return;

        const deadline = moment(frm.doc.bid_deadline);
        const now = moment();
        const days_left = deadline.diff(now, 'days');

        // Warn the user if the deadline is uncomfortably close
        if (days_left >= 0 && days_left <= 3) {
            frappe.msgprint({
                title: __('Deadline Warning'),
                indicator: 'orange',
                message: __(
                    'Bid deadline is within 3 days — {0} day(s) remaining.',
                    [days_left]
                ),
            });
        }
    },
});

// ── Helper functions ──────────────────────────────────────────────────────────

function toggle_sub_sectors(frm) {
    // Show only the sub-sector field that matches the selected sector
    frm.toggle_display('railway_sub_sector', frm.doc.sector === 'Railways');
    frm.toggle_display('defence_sub_sector', frm.doc.sector === 'Defence');
}

function toggle_loss_fields(frm) {
    // L1 price and loss reason are only relevant when a tender is Lost
    const is_lost = frm.doc.status === 'Lost';
    frm.toggle_display('l1_price', is_lost);
    frm.toggle_display('loss_reason', is_lost);
    frm.toggle_reqd('l1_price', is_lost);
    frm.toggle_reqd('loss_reason', is_lost);
}

function add_cost_sheet_button(frm) {
    // "Create Cost Sheet" appears when status is Submitted and none is linked yet
    frm.remove_custom_button(__('Create Cost Sheet'), __('Actions'));
    if (frm.doc.status === 'Submitted' && !frm.doc.linked_cost_sheet && !frm.doc.__islocal) {
        frm.add_custom_button(__('Create Cost Sheet'), function () {
            frappe.new_doc('CST Cost Sheet', {
                tender: frm.doc.name,
            });
        }, __('Actions'));
    }
}
