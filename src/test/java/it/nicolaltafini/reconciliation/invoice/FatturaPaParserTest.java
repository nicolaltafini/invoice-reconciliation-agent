package it.nicolaltafini.reconciliation.invoice;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;

import org.junit.jupiter.api.Test;

class FatturaPaParserTest {

    private static final Path SAMPLES = Path.of("samples", "invoices");

    private final FatturaPaParser parser = new FatturaPaParser();

    private ParsedInvoice parseSample(String fileName) throws IOException {
        try (InputStream in = Files.newInputStream(SAMPLES.resolve(fileName))) {
            return parser.parse(in);
        }
    }

    @Test
    void parsesHeaderFields() throws IOException {
        ParsedInvoice invoice = parseSample("IT01111111111_00145.xml");

        assertThat(invoice.supplierVatNumber()).isEqualTo("01111111111");
        assertThat(invoice.supplierName()).isEqualTo("Ferramenta Adige Srl");
        assertThat(invoice.invoiceNumber()).isEqualTo("FA-2026/0145");
        assertThat(invoice.invoiceDate()).isEqualTo(LocalDate.of(2026, 9, 8));
        assertThat(invoice.totalAmount()).isEqualByComparingTo("161.04");
        assertThat(invoice.orderNumber()).isEqualTo("PO-2026-001");
        assertThat(invoice.ddtNumber()).isEqualTo("DDT-0877");
    }

    @Test
    void parsesLines() throws IOException {
        ParsedInvoice invoice = parseSample("IT01111111111_00145.xml");

        assertThat(invoice.lines()).hasSize(3);
        ParsedInvoiceLine first = invoice.lines().get(0);
        assertThat(first.lineNumber()).isEqualTo(1);
        assertThat(first.itemCode()).isEqualTo("VIT-M8-50");
        assertThat(first.quantity()).isEqualByComparingTo("1000");
        assertThat(first.unitPrice()).isEqualByComparingTo("0.085");
        assertThat(first.lineTotal()).isEqualByComparingTo("85.00");
    }

    @Test
    void parsesLineNotInOrder() throws IOException {
        ParsedInvoice invoice = parseSample("IT01111111111_00162.xml");

        assertThat(invoice.lines())
                .extracting(ParsedInvoiceLine::itemCode)
                .containsExactly("VIT-M6-30", "TAS-8", "TRASP");
    }

    @Test
    void parsesAllSamples() throws IOException {
        try (DirectoryStream<Path> files = Files.newDirectoryStream(SAMPLES, "*.xml")) {
            for (Path file : files) {
                ParsedInvoice invoice = parseSample(file.getFileName().toString());
                assertThat(invoice.lines()).as(file.toString()).isNotEmpty();
            }
        }
    }

    @Test
    void rejectsXmlWithDoctype() {
        String malicious = """
                <?xml version="1.0"?>
                <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">]>
                <foo>&xxe;</foo>
                """;
        InputStream in = new ByteArrayInputStream(malicious.getBytes(StandardCharsets.UTF_8));

        assertThatThrownBy(() -> parser.parse(in)).isInstanceOf(InvoiceParsingException.class);
    }
}