import frappe
from frappe.model.document import Document
from frappe.utils import today, date_diff, add_days, getdate, flt


class CO7Tracker(Document):
    def before_save(self):
        self._calc_ageing()
        self._calc_payment_fields()
        self._auto_advance_stage()
        self._set_payment_expected_date()

    def validate(self):
        self._check_date_sequence()
        self._warn_over_invoiced()

    def _calc_ageing(self):
        # Calendar days elapsed since invoice was raised
        if self.invoice_date:
            self.ageing_days = date_diff(today(), self.invoice_date)

    def _calc_payment_fields(self):
        # Net payment = amount received minus TDS and SD/LD deductions
        received = flt(self.amount_received)
        tds      = flt(self.tds_deducted)
        sd_ld    = flt(self.sd_ld_deduction)
        self.net_payment_received = received - tds - sd_ld

        # Outstanding = invoice value not yet recovered
        self.outstanding_amount = flt(self.invoice_amount) - self.net_payment_received

    def _auto_advance_stage(self):
        # Promote to the highest milestone for which all required fields are filled
        if self.payment_date and flt(self.amount_received):
            self.current_stage = "Payment Received"
        elif self.co7_no and self.co7_date:
            self.current_stage = "CO7 Issued"
        elif self.bill_submission_date:
            self.current_stage = "Bills Submitted"
        elif self.r_note_no and self.r_note_date:
            self.current_stage = "R-Note Received"
        elif self.dispatch_date:
            self.current_stage = "Dispatched"
        # else remains "Invoice Raised" (form default)

    def _set_payment_expected_date(self):
        # Railway payment norm: CO7 encashment within 7 working days of issuance
        if self.co7_date:
            self.payment_expected_date = add_days(self.co7_date, 7)

    def _check_date_sequence(self):
        # Enforce logical pipeline ordering so users cannot enter back-dated milestones
        sequence = [
            ("invoice_date",        "dispatch_date",        "Invoice Date",         "Dispatch Date"),
            ("dispatch_date",       "r_note_date",          "Dispatch Date",        "R-Note Date"),
            ("r_note_date",         "bill_submission_date",  "R-Note Date",         "Bill Submission Date"),
            ("bill_submission_date","co7_date",              "Bill Submission Date", "CO7 Date"),
            ("co7_date",            "payment_date",          "CO7 Date",             "Payment Date"),
        ]
        for earlier_f, later_f, earlier_lbl, later_lbl in sequence:
            earlier = getattr(self, earlier_f)
            later   = getattr(self, later_f)
            if earlier and later and getdate(later) < getdate(earlier):
                frappe.throw(
                    f"{later_lbl} ({later}) cannot be earlier than {earlier_lbl} ({earlier})."
                )

    def _warn_over_invoiced(self):
        # Alert the user — does not block save, just highlights a potential data entry error
        if flt(self.amount_received) > flt(self.invoice_amount):
            frappe.msgprint(
                msg=(
                    f"Amount Received (₹{flt(self.amount_received):,.2f}) exceeds "
                    f"Invoice Amount (₹{flt(self.invoice_amount):,.2f}). Please verify."
                ),
                title="Over-payment Warning",
                indicator="orange",
            )


def check_co7_ageing():
    """Daily scheduler: email Accounts Managers about invoices pending > 90 days."""
    # Fetch all non-settled records whose ageing has crossed the 90-day threshold
    overdue = frappe.get_all(
        "CO7 Tracker",
        filters=[
            ["ageing_days", ">", 90],
            ["current_stage", "!=", "Payment Received"],
        ],
        fields=[
            "name", "customer", "sales_invoice",
            "invoice_amount", "ageing_days", "current_stage",
        ],
        order_by="ageing_days desc",
    )

    if not overdue:
        return  # nothing to report

    # Resolve email addresses for every user holding the Accounts Manager role
    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Accounts Manager", "parenttype": "User"},
        pluck="parent",
    )

    if not managers:
        frappe.log_error(
            "check_co7_ageing: no users with Accounts Manager role found.",
            "CO7 Ageing Alert",
        )
        return

    # Build an HTML summary table for the email body
    rows = "".join(
        "<tr>"
        f"<td>{r.name}</td>"
        f"<td>{r.customer}</td>"
        f"<td>{r.sales_invoice or '—'}</td>"
        f"<td style='text-align:right'>₹{flt(r.invoice_amount):,.2f}</td>"
        f"<td style='text-align:center'>{r.ageing_days}</td>"
        f"<td>{r.current_stage}</td>"
        "</tr>"
        for r in overdue
    )
    table_style = "border-collapse:collapse;width:100%"
    th_style    = "background:#4472C4;color:#fff;padding:6px 10px;text-align:left"
    td_style    = "border:1px solid #ccc;padding:5px 10px"
    body = f"""
    <p>The following <strong>{len(overdue)}</strong> CO7 record(s) have been
    pending for more than <strong>90 days</strong> and require attention:</p>
    <table style="{table_style}">
      <thead>
        <tr>
          <th style="{th_style}">CO7 Ref</th>
          <th style="{th_style}">Customer</th>
          <th style="{th_style}">Sales Invoice</th>
          <th style="{th_style}">Invoice Amount</th>
          <th style="{th_style}">Ageing (Days)</th>
          <th style="{th_style}">Stage</th>
        </tr>
      </thead>
      <tbody style="{td_style}">{rows}</tbody>
    </table>
    <p style="color:#888;font-size:12px">
      Sent automatically by Parasramka ERPNext — CO7 Ageing Scheduler.
    </p>
    """

    frappe.sendmail(
        recipients=managers,
        subject=f"[PEPL Alert] {len(overdue)} CO7 Record(s) Overdue > 90 Days",
        message=body,
        now=True,
    )
