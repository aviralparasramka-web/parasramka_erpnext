import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, add_days, date_diff, flt


# 14 months expressed as days (used consistently throughout)
PSD_VALIDITY_DAYS = 425


class PSDTracker(Document):

    def before_save(self):
        self._fetch_order_details()
        self._calculate_psd_amount()
        self._calculate_psd_expiry()
        self._auto_update_status()

    # ── Calculation helpers ───────────────────────────────────────────────────

    def _fetch_order_details(self):
        # Pull customer and order value directly from the linked Sales Order
        # so the record is always in sync even if the SO is amended
        if self.sales_order:
            so = frappe.db.get_value(
                "Sales Order",
                self.sales_order,
                ["customer", "grand_total"],
                as_dict=True,
            )
            if so:
                self.customer = so.customer
                self.order_value = flt(so.grand_total)

    def _calculate_psd_amount(self):
        # PSD is always 5% of the Sales Order value
        self.psd_amount = flt(self.order_value) * 0.05

    def _calculate_psd_expiry(self):
        # Expiry is last_supply_date + 425 days (≈ 14 months)
        if self.last_supply_date:
            self.psd_expiry = add_days(self.last_supply_date, PSD_VALIDITY_DAYS)
        else:
            self.psd_expiry = None

    def _auto_update_status(self):
        # Drive status automatically from the boolean fields
        # Priority: Closed > Refund Awaited > NDC Awaited > Submitted > Pending Submission
        if self.refund_received:
            self.status = "Closed"
        elif self.ndc_received:
            self.status = "Refund Awaited"
        elif self.psd_submitted and self.last_supply_date:
            # Supplies are complete; awaiting NDC from the customer
            self.status = "NDC Awaited"
        elif self.psd_submitted:
            # PSD has been lodged; supplies still ongoing
            self.status = "Submitted"
        else:
            self.status = "Pending Submission"


# ── Scheduled task ────────────────────────────────────────────────────────────

def check_psd_expiry():
    """Daily scheduler: alert Accounts Managers of PSDs expiring within 30 days."""

    today = getdate(nowdate())
    alert_cutoff = add_days(today, 30)

    # PSDs that are active (not yet Closed) and expiring within 30 days
    expiring = frappe.get_all(
        "PSD Tracker",
        filters={
            "status": ["not in", ["Closed"]],
            "psd_expiry": ["between", [today, alert_cutoff]],
        },
        fields=[
            "name", "sales_order", "customer",
            "psd_amount", "psd_expiry", "status",
        ],
    )

    if not expiring:
        return

    # Collect all users with the Accounts Manager role
    accounts_managers = frappe.get_all(
        "Has Role",
        filters={"role": "Accounts Manager", "parenttype": "User"},
        fields=["parent as email"],
    )

    if not accounts_managers:
        return

    recipients = [u["email"] for u in accounts_managers]

    rows = "".join(
        "<tr>"
        f"<td>{p.name}</td>"
        f"<td>{p.sales_order}</td>"
        f"<td>{p.customer}</td>"
        f"<td>{frappe.format(p.psd_amount, {'fieldtype': 'Currency'})}</td>"
        f"<td>{p.psd_expiry}</td>"
        f"<td>{p.status}</td>"
        "</tr>"
        for p in expiring
    )

    message = f"""
    <p>The following PSDs are expiring within the next <strong>30 days</strong>.
    Please follow up to obtain NDC / refund before expiry:</p>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
      <thead>
        <tr>
          <th>PSD Ref</th>
          <th>Sales Order</th>
          <th>Customer</th>
          <th>PSD Amount</th>
          <th>Expiry Date</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <p>Log in to ERPNext to take action on these records.</p>
    """

    frappe.sendmail(
        recipients=recipients,
        subject=_("PSD Expiry Alert — Action Required"),
        message=message,
        now=True,
    )
