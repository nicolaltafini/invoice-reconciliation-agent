from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from reconciliation.db import engine
from reconciliation.models import PurchaseOrder, PurchaseOrderLine, Supplier

SUPPLIERS = {
    "01111111111": "Ferramenta Adige Srl",
    "02222222222": "Imballaggi Veneto Spa",
    "03333333333": "Elettroforniture Mincio Srl",
}

# (numero ordine, P.IVA fornitore, data, [(codice, descrizione, quantita, prezzo)])
ORDERS = [
    ("PO-2026-001", "01111111111", date(2026, 9, 1), [
        ("VIT-M8-50", "Viti M8x50 zincate", "1000", "0.0850"),
        ("DAD-M8", "Dadi M8 zincati", "1000", "0.0320"),
        ("RON-M8", "Rondelle M8", "1000", "0.0150"),
    ]),
    ("PO-2026-002", "02222222222", date(2026, 9, 3), [
        ("SCA-403030", "Scatole cartone 40x30x30", "500", "0.9500"),
        ("NAS-50", "Nastro adesivo 50mm", "120", "1.8000"),
    ]),
    ("PO-2026-003", "03333333333", date(2026, 9, 5), [
        ("CAV-3G15", "Cavo 3G1,5 al metro", "200", "0.7400"),
        ("INT-16A", "Interruttore magnetotermico 16A", "25", "12.5000"),
        ("QUA-12M", "Quadro elettrico 12 moduli", "5", "38.0000"),
    ]),
    ("PO-2026-004", "01111111111", date(2026, 9, 10), [
        ("VIT-M6-30", "Viti M6x30 inox", "2000", "0.0610"),
        ("TAS-8", "Tasselli nylon 8mm", "1500", "0.0420"),
    ]),
]


def seed(session: Session) -> None:
    suppliers = {}
    for vat_number, name in SUPPLIERS.items():
        supplier = session.scalar(select(Supplier).where(Supplier.vat_number == vat_number))
        if supplier is None:
            supplier = Supplier(vat_number=vat_number, name=name)
            session.add(supplier)
        suppliers[vat_number] = supplier

    for order_number, vat_number, order_date, lines in ORDERS:
        existing = session.scalar(
            select(PurchaseOrder).where(PurchaseOrder.order_number == order_number)
        )
        if existing is not None:
            continue

        order = PurchaseOrder(
            order_number=order_number,
            supplier=suppliers[vat_number],
            order_date=order_date,
        )
        for line_number, (code, description, quantity, price) in enumerate(lines, start=1):
            order.lines.append(
                PurchaseOrderLine(
                    line_number=line_number,
                    item_code=code,
                    description=description,
                    quantity=Decimal(quantity),
                    unit_price=Decimal(price),
                )
            )
        session.add(order)


def main() -> None:
    with Session(engine) as session, session.begin():
        seed(session)
    print("Dati demo caricati")


if __name__ == "__main__":
    main()