from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from reconciliation.models import Ddt, Invoice, PurchaseOrder

CENT = Decimal("0.01")


class DiscrepancyType(StrEnum):
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    SUPPLIER_MISMATCH = "SUPPLIER_MISMATCH"
    LINE_NOT_IN_ORDER = "LINE_NOT_IN_ORDER"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    QUANTITY_EXCEEDS_ORDERED = "QUANTITY_EXCEEDS_ORDERED"
    QUANTITY_EXCEEDS_DELIVERED = "QUANTITY_EXCEEDS_DELIVERED"


class ReconciliationStatus(StrEnum):
    MATCHED = "MATCHED"
    DISCREPANCIES = "DISCREPANCIES"
    WAITING_FOR_DDT = "WAITING_FOR_DDT"


@dataclass
class Discrepancy:
    type: DiscrepancyType
    message: str
    item_code: str | None = None
    expected: Decimal | None = None
    actual: Decimal | None = None
    amount_at_risk: Decimal = Decimal("0.00")


@dataclass
class ReconciliationResult:
    invoice_number: str
    status: ReconciliationStatus
    discrepancies: list[Discrepancy] = field(default_factory=list)

    @property
    def amount_at_risk(self) -> Decimal:
        return sum((d.amount_at_risk for d in self.discrepancies), Decimal("0.00"))


def reconcile(invoice: Invoice, order: PurchaseOrder | None, ddt: Ddt | None) -> ReconciliationResult:
    discrepancies: list[Discrepancy] = []

    if order is None:
        discrepancies.append(Discrepancy(
            DiscrepancyType.ORDER_NOT_FOUND,
            f"Ordine {invoice.order_number or '(non indicato)'} non trovato",
        ))
    elif order.supplier.vat_number != invoice.supplier.vat_number:
        discrepancies.append(Discrepancy(
            DiscrepancyType.SUPPLIER_MISMATCH,
            f"L'ordine {order.order_number} e' di {order.supplier.name}, "
            f"la fattura di {invoice.supplier.name}",
        ))

    ordered = {line.item_code: line for line in order.lines} if order else {}
    delivered: dict[str | None, Decimal] = {}
    if ddt is not None:
        for line in ddt.lines:
            delivered[line.item_code] = delivered.get(line.item_code, Decimal("0")) + line.quantity

    for line in invoice.lines:
        code = line.item_code

        if order is not None:
            order_line = ordered.get(code)
            if order_line is None:
                discrepancies.append(Discrepancy(
                    DiscrepancyType.LINE_NOT_IN_ORDER,
                    f"{code} ({line.description}) fatturato ma non presente nell'ordine",
                    item_code=code,
                    actual=line.line_total,
                    amount_at_risk=line.line_total.quantize(CENT),
                ))
                continue

            if line.unit_price != order_line.unit_price:
                difference = line.unit_price - order_line.unit_price
                discrepancies.append(Discrepancy(
                    DiscrepancyType.PRICE_MISMATCH,
                    f"{code}: prezzo fatturato {_fmt(line.unit_price)} invece di "
                    f"{_fmt(order_line.unit_price)} dell'ordine",
                    item_code=code,
                    expected=order_line.unit_price,
                    actual=line.unit_price,
                    amount_at_risk=(max(difference, Decimal("0")) * line.quantity).quantize(CENT),
                ))

            if line.quantity > order_line.quantity:
                excess = line.quantity - order_line.quantity
                discrepancies.append(Discrepancy(
                    DiscrepancyType.QUANTITY_EXCEEDS_ORDERED,
                    f"{code}: fatturati {_fmt(line.quantity)}, ordinati {_fmt(order_line.quantity)}",
                    item_code=code,
                    expected=order_line.quantity,
                    actual=line.quantity,
                    amount_at_risk=(excess * line.unit_price).quantize(CENT),
                ))

        if ddt is not None:
            delivered_quantity = delivered.get(code, Decimal("0"))
            if line.quantity > delivered_quantity:
                missing = line.quantity - delivered_quantity
                discrepancies.append(Discrepancy(
                    DiscrepancyType.QUANTITY_EXCEEDS_DELIVERED,
                    f"{code}: fatturati {_fmt(line.quantity)}, consegnati {_fmt(delivered_quantity)} "
                    f"(DDT {ddt.ddt_number})",
                    item_code=code,
                    expected=delivered_quantity,
                    actual=line.quantity,
                    amount_at_risk=(missing * line.unit_price).quantize(CENT),
                ))

    if discrepancies:
        status = ReconciliationStatus.DISCREPANCIES
    elif ddt is None:
        status = ReconciliationStatus.WAITING_FOR_DDT
    else:
        status = ReconciliationStatus.MATCHED

    return ReconciliationResult(invoice.invoice_number, status, discrepancies)


def _fmt(value: Decimal) -> str:
    return f"{value.normalize():f}"