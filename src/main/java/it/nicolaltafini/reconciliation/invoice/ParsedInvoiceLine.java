package it.nicolaltafini.reconciliation.invoice;

import java.math.BigDecimal;

public record ParsedInvoiceLine(
        int lineNumber,
        String itemCode,
        String description,
        BigDecimal quantity,
        BigDecimal unitPrice,
        BigDecimal lineTotal) {
}