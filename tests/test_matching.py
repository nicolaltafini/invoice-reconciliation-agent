from datetime import date
from decimal import Decimal as D

from reconciliation.matching import DiscrepancyType, ReconciliationStatus, reconcile
from reconciliation.models import (
    Ddt,
    DdtLine,
    Invoice,
    InvoiceLine,
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
)

SUPPLIER = Supplier(vat_number="01111111111", name="Ferramenta Adige Srl")


def make_order(lines, supplier=SUPPLIER):
    order = PurchaseOrder(order_number="PO-1", supplier=supplier, order_date=date(2026, 9, 1))
    for number, (code, quantity, price) in enumerate(lines, start=1):
        order.lines.append(PurchaseOrderLine(
            line_number=number, item_code=code, description=code,
            quantity=D(quantity), unit_price=D(price),
        ))
    return order


def make_invoice(lines, supplier=SUPPLIER):
    invoice = Invoice(
        invoice_number="F-1", supplier=supplier, invoice_date=date(2026, 9, 8),
        order_number="PO-1", ddt_number="DDT-1", source_filename="f.xml",
    )
    for number, (code, quantity, price) in enumerate(lines, start=1):
        invoice.lines.append(InvoiceLine(
            line_number=number, item_code=code, description=code,
            quantity=D(quantity), unit_price=D(price), line_total=D(quantity) * D(price),
        ))
    return invoice


def make_ddt(lines, supplier=SUPPLIER):
    ddt = Ddt(
        ddt_number="DDT-1", supplier=supplier, ddt_date=date(2026, 9, 4), order_number="PO-1",
        source_filename="d.pdf", extraction_model="test", input_tokens=0, output_tokens=0,
    )
    for number, (code, quantity) in enumerate(lines, start=1):
        ddt.lines.append(DdtLine(line_number=number, item_code=code, description=code,
                                 quantity=D(quantity), unit="PZ"))
    return ddt


def types(result):
    return [d.type for d in result.discrepancies]


def test_everything_matches():
    result = reconcile(
        make_invoice([("VIT", "1000", "0.085")]),
        make_order([("VIT", "1000", "0.0850")]),
        make_ddt([("VIT", "1000")]),
    )

    assert result.status == ReconciliationStatus.MATCHED
    assert result.discrepancies == []


def test_price_higher_than_order():
    result = reconcile(
        make_invoice([("SCA", "500", "1.05")]),
        make_order([("SCA", "500", "0.95")]),
        make_ddt([("SCA", "500")]),
    )

    assert types(result) == [DiscrepancyType.PRICE_MISMATCH]
    assert result.amount_at_risk == D("50.00")


def test_invoiced_more_than_delivered():
    result = reconcile(
        make_invoice([("INT", "25", "12.50")]),
        make_order([("INT", "25", "12.50")]),
        make_ddt([("INT", "20")]),
    )

    assert types(result) == [DiscrepancyType.QUANTITY_EXCEEDS_DELIVERED]
    assert result.amount_at_risk == D("62.50")


def test_line_not_in_order():
    result = reconcile(
        make_invoice([("VIT", "2000", "0.061"), ("TRASP", "1", "25")]),
        make_order([("VIT", "2000", "0.061")]),
        make_ddt([("VIT", "2000")]),
    )

    assert types(result) == [DiscrepancyType.LINE_NOT_IN_ORDER]
    assert result.amount_at_risk == D("25.00")


def test_waiting_for_ddt():
    result = reconcile(
        make_invoice([("VIT", "1000", "0.085")]),
        make_order([("VIT", "1000", "0.085")]),
        None,
    )

    assert result.status == ReconciliationStatus.WAITING_FOR_DDT


def test_order_not_found():
    result = reconcile(make_invoice([("VIT", "1000", "0.085")]), None, None)

    assert result.status == ReconciliationStatus.DISCREPANCIES
    assert types(result) == [DiscrepancyType.ORDER_NOT_FOUND]


def test_order_from_another_supplier():
    other = Supplier(vat_number="02222222222", name="Altro Srl")
    result = reconcile(
        make_invoice([("VIT", "1000", "0.085")]),
        make_order([("VIT", "1000", "0.085")], supplier=other),
        make_ddt([("VIT", "1000")]),
    )

    assert DiscrepancyType.SUPPLIER_MISMATCH in types(result)