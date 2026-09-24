package it.nicolaltafini.reconciliation.invoice;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record ParsedInvoice(
        String supplierVatNumber,
        String supplierName,
        String invoiceNumber,
        LocalDate invoiceDate,
        BigDecimal totalAmount,
        String orderNumber,
        String ddtNumber,
        List<ParsedInvoiceLine> lines) {
}