from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Supplier(Base):
    __tablename__ = "supplier"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vat_number: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(255))


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("supplier.id"))
    order_date: Mapped[date]

    supplier: Mapped[Supplier] = relationship()
    lines: Mapped[list[PurchaseOrderLine]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLine.line_number",
    )


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_line"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_order.id", ondelete="CASCADE")
    )
    line_number: Mapped[int]
    item_code: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 4))

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="lines")


class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("supplier.id"))
    invoice_number: Mapped[str] = mapped_column(String(50))
    invoice_date: Mapped[date]
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    order_number: Mapped[str | None] = mapped_column(String(50))
    ddt_number: Mapped[str | None] = mapped_column(String(50))
    source_filename: Mapped[str] = mapped_column(String(255))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    supplier: Mapped[Supplier] = relationship()
    lines: Mapped[list[InvoiceLine]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.line_number",
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_line"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice.id", ondelete="CASCADE"))
    line_number: Mapped[int]
    item_code: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(1000))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    invoice: Mapped[Invoice] = relationship(back_populates="lines")