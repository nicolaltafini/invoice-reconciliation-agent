package it.nicolaltafini.reconciliation.invoice;

import java.io.InputStream;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;

import org.springframework.stereotype.Component;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.helpers.DefaultHandler;

@Component
public class FatturaPaParser {

    private static final String SUPPLIER = "/*/FatturaElettronicaHeader/CedentePrestatore/DatiAnagrafici";
    private static final String BODY = "/*/FatturaElettronicaBody[1]";
    private static final String GENERAL = BODY + "/DatiGenerali";
    private static final String DOCUMENT = GENERAL + "/DatiGeneraliDocumento";

    public ParsedInvoice parse(InputStream xml) {
        try {
            Document doc = newSecureDocumentBuilder().parse(xml);
            XPath xpath = XPathFactory.newInstance().newXPath();

            List<ParsedInvoiceLine> lines = parseLines(xpath, doc);
            if (lines.isEmpty()) {
                throw new InvoiceParsingException("La fattura non contiene righe DettaglioLinee");
            }

            String total = optional(xpath, doc, DOCUMENT + "/ImportoTotaleDocumento");

            return new ParsedInvoice(
                    required(xpath, doc, SUPPLIER + "/IdFiscaleIVA/IdCodice"),
                    required(xpath, doc, SUPPLIER + "/Anagrafica/Denominazione"),
                    required(xpath, doc, DOCUMENT + "/Numero"),
                    LocalDate.parse(required(xpath, doc, DOCUMENT + "/Data")),
                    total == null ? null : new BigDecimal(total),
                    optional(xpath, doc, GENERAL + "/DatiOrdineAcquisto[1]/IdDocumento"),
                    optional(xpath, doc, GENERAL + "/DatiDDT[1]/NumeroDDT"),
                    lines);
        } catch (InvoiceParsingException e) {
            throw e;
        } catch (Exception e) {
            throw new InvoiceParsingException("XML FatturaPA non valido: " + e.getMessage(), e);
        }
    }

    private List<ParsedInvoiceLine> parseLines(XPath xpath, Document doc) throws XPathExpressionException {
        NodeList nodes = (NodeList) xpath.evaluate(
                BODY + "/DatiBeniServizi/DettaglioLinee", doc, XPathConstants.NODESET);

        List<ParsedInvoiceLine> lines = new ArrayList<>();
        for (int i = 0; i < nodes.getLength(); i++) {
            Node node = nodes.item(i);
            String quantity = optional(xpath, node, "Quantita");
            lines.add(new ParsedInvoiceLine(
                    Integer.parseInt(required(xpath, node, "NumeroLinea")),
                    optional(xpath, node, "CodiceArticolo[1]/CodiceValore"),
                    required(xpath, node, "Descrizione"),
                    quantity == null ? BigDecimal.ONE : new BigDecimal(quantity),
                    new BigDecimal(required(xpath, node, "PrezzoUnitario")),
                    new BigDecimal(required(xpath, node, "PrezzoTotale"))));
        }
        return lines;
    }

    private static String required(XPath xpath, Object context, String expression)
            throws XPathExpressionException {
        String value = optional(xpath, context, expression);
        if (value == null) {
            throw new InvoiceParsingException("Campo obbligatorio mancante: " + expression);
        }
        return value;
    }

    private static String optional(XPath xpath, Object context, String expression)
            throws XPathExpressionException {
        String value = xpath.evaluate(expression, context).trim();
        return value.isEmpty() ? null : value;
    }

    private static DocumentBuilder newSecureDocumentBuilder() throws ParserConfigurationException {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        factory.setXIncludeAware(false);
        factory.setExpandEntityReferences(false);

        DocumentBuilder builder = factory.newDocumentBuilder();
        builder.setErrorHandler(new DefaultHandler());
        return builder;
    }
}