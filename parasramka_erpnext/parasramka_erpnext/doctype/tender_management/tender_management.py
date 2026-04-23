import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime, nowdate, add_days, getdate


class TenderManagement(Document):

    def validate(self):
        self._validate_loss_fields()
        self._validate_bid_deadline()

    def before_save(self):
        self._clear_sub_sector()

    # ── Validation helpers ────────────────────────────────────────────────────

    def _validate_loss_fields(self):
        # L1 price and loss reason are mandatory when a tender is marked Lost
        if self.status == "Lost":
            if not self.l1_price:
                frappe.throw(_("L1 Price is mandatory when Status is Lost"))
            if not self.loss_reason:
                frappe.throw(_("Loss Reason is mandatory when Status is Lost"))

    def _validate_bid_deadline(self):
        # New tenders cannot have a bid deadline that has already passed
        if self.is_new() and self.bid_deadline:
            if get_datetime(self.bid_deadline) < now_datetime():
                frappe.throw(
                    _("Bid Deadline cannot be set in the past for a new Tender")
                )

    # ── Before-save helpers ───────────────────────────────────────────────────

    def _clear_sub_sector(self):
        # Keep only the sub-sector relevant to the chosen sector
        if self.sector == "Railways":
            self.defence_sub_sector = None
        elif self.sector == "Defence":
            self.railway_sub_sector = None
        else:
            # Private / Others — neither sub-sector applies
            self.railway_sub_sector = None
            self.defence_sub_sector = None


# ── Scheduled task ────────────────────────────────────────────────────────────

def check_tender_deadlines():
    """Daily scheduler: email Sales Managers about tenders due within 3 days."""

    today = getdate(nowdate())
    deadline_cutoff = add_days(today, 3)

    # Tenders that are still Upcoming and expire within the next 3 days
    tenders = frappe.get_all(
        "Tender Management",
        filters={
            "status": "Upcoming",
            "bid_deadline": ["between", [today, deadline_cutoff]],
        },
        fields=["name", "tender_no", "customer", "item", "bid_deadline"],
    )

    if not tenders:
        return

    # Collect all users who hold the Sales Manager role
    sales_managers = frappe.get_all(
        "Has Role",
        filters={"role": "Sales Manager", "parenttype": "User"},
        fields=["parent as email"],
    )

    if not sales_managers:
        return

    recipients = [u["email"] for u in sales_managers]

    # Build an HTML table row per tender for the alert email
    rows = "".join(
        "<tr>"
        f"<td>{t.tender_no}</td>"
        f"<td>{t.customer}</td>"
        f"<td>{t.item}</td>"
        f"<td>{frappe.format(t.bid_deadline, {'fieldtype': 'Datetime'})}</td>"
        "</tr>"
        for t in tenders
    )

    message = f"""
    <p>The following tenders have bid deadlines <strong>within the next 3 days</strong>.
    Please take immediate action:</p>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
      <thead>
        <tr>
          <th>Tender No.</th>
          <th>Customer</th>
          <th>Item</th>
          <th>Bid Deadline</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <p>Please log in to ERPNext to review and act on these tenders.</p>
    """

    frappe.sendmail(
        recipients=recipients,
        subject=_("Tender Deadline Alert — Action Required"),
        message=message,
        now=True,
    )
