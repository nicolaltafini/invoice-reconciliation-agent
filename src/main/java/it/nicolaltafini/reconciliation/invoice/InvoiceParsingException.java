package it.nicolaltafini.reconciliation.invoice;

public class InvoiceParsingException extends RuntimeException {

    public InvoiceParsingException(String message) {
        super(message);
    }

    public InvoiceParsingException(String message, Throwable cause) {
        super(message, cause);
    }
}