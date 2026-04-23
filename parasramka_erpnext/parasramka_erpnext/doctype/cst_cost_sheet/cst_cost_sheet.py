import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CSTCostSheet(Document):

    def before_save(self):
        self._fetch_from_tender()
        self._calculate_bom_rows()
        self._calculate_totals()

    # ── Data-fetch helpers ────────────────────────────────────────────────────

    def _fetch_from_tender(self):
        if not self.tender:
            return
        # Pull all header fields from the linked Tender Management record
        tender = frappe.db.get_value(
            "Tender Management",
            self.tender,
            ["item", "drawing_no", "drawing_rev", "customer", "sector", "quantity"],
            as_dict=True,
        )
        if not tender:
            return
        self.item = tender.item
        self.drawing_no = tender.drawing_no
        self.drawing_rev = tender.drawing_rev
        self.customer = tender.customer
        self.sector = tender.sector
        self.total_quantity = flt(tender.quantity)

    # ── BOM row calculations ──────────────────────────────────────────────────

    def _calculate_bom_rows(self):
        # Recalculate total_qty and amount for every BOM line
        for row in self.cst_bom_items or []:
            row.total_qty = flt(row.qty_per_unit) * flt(self.total_quantity)
            row.amount = flt(row.total_qty) * flt(row.rate)

    # ── Summary calculations ──────────────────────────────────────────────────

    def _calculate_totals(self):
        # Sum all BOM row amounts into total RM cost
        self.total_rm_cost = sum(flt(row.amount) for row in self.cst_bom_items or [])

        # Base for overhead = RM cost + machining
        base_cost = flt(self.total_rm_cost) + flt(self.machining_cost)

        # Overhead is applied on (RM + machining)
        self.overhead_amount = base_cost * flt(self.overhead_percent) / 100

        # Profit is applied on (RM + machining + overhead)
        total_before_profit = base_cost + flt(self.overhead_amount)
        self.profit_amount = total_before_profit * flt(self.profit_percent) / 100

        # Final calculated unit price before any manual adjustment
        self.final_unit_price = total_before_profit + flt(self.profit_amount)
