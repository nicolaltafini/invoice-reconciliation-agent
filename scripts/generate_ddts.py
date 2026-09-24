"""Genera i DDT di esempio in PDF in samples/ddt/."""

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT = Path(__file__).resolve().parents[1] / "samples" / "ddt"
CUSTOMER = "Officine Demo Srl - Via Industria 10, 37063 Isola della Scala (VR)"


@dataclass
class Ddt:
    filename: str
    title: str
    number: str
    date: str
    supplier: str
    supplier_vat: str
    supplier_address: str
    order_ref: str
    headers: tuple[str, str, str, str]
    lines: list[tuple[str, str, str, str]]


DDTS = [
    Ddt(
        "DDT-0877_ferramenta-adige.pdf", "DOCUMENTO DI TRASPORTO", "DDT-0877", "04/09/2026",
        "Ferramenta Adige Srl", "01111111111", "Via dei Mestieri 12, 37100 Verona (VR)",
        "Vs. ordine PO-2026-001",
        ("Codice", "Descrizione", "Quantità", "UM"),
        [
            ("VIT-M8-50", "Viti M8x50 zincate", "1.000", "PZ"),
            ("DAD-M8", "Dadi M8 zincati", "1.000", "PZ"),
            ("RON-M8", "Rondelle M8", "1.000", "PZ"),
        ],
    ),
    Ddt(
        "2026-DDT-0540_imballaggi-veneto.pdf", "D.D.T. - Documento di Trasporto", "2026/DDT/0540",
        "09/09/2026", "Imballaggi Veneto Spa", "02222222222",
        "Viale del Lavoro 5, 35100 Padova (PD)", "Rif. ordine cliente: PO-2026-002",
        ("Art.", "Descrizione articolo", "Q.tà", "U.M."),
        [
            ("SCA-403030", "Scatole cartone 40x30x30", "500", "PZ"),
            ("NAS-50", "Nastro adesivo 50mm", "120", "PZ"),
        ],
    ),
    Ddt(
        "EM-DDT-3310_elettroforniture-mincio.pdf", "BOLLA DI CONSEGNA", "EM-DDT-3310", "11/09/2026",
        "Elettroforniture Mincio Srl", "03333333333", "Strada Mantovana 88, 46100 Mantova (MN)",
        "Ordine n. PO-2026-003",
        ("Cod. articolo", "Descrizione", "Qta consegnata", "UM"),
        [
            ("CAV-3G15", "Cavo 3G1,5 al metro", "200", "M"),
            ("INT-16A", "Interruttore magnetotermico 16A", "20", "PZ"),
            ("QUA-12M", "Quadro elettrico 12 moduli", "5", "PZ"),
        ],
    ),
    Ddt(
        "DDT-0912_ferramenta-adige.pdf", "DOCUMENTO DI TRASPORTO", "DDT-0912", "16/09/2026",
        "Ferramenta Adige Srl", "01111111111", "Via dei Mestieri 12, 37100 Verona (VR)",
        "Vs. ordine PO-2026-004",
        ("Codice", "Descrizione", "Quantità", "UM"),
        [
            ("VIT-M6-30", "Viti M6x30 inox", "2.000", "PZ"),
            ("TAS-8", "Tasselli nylon 8mm", "1.500", "PZ"),
        ],
    ),
]


def render(ddt: Ddt) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(OUTPUT / ddt.filename),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    table = Table(
        [list(ddt.headers), *[list(line) for line in ddt.lines]],
        colWidths=[35 * mm, 85 * mm, 30 * mm, 20 * mm],
    )
    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ])
    )

    doc.build([
        Paragraph(f"<b>{ddt.supplier}</b>", styles["Title"]),
        Paragraph(f"{ddt.supplier_address} - P.IVA {ddt.supplier_vat}", styles["Normal"]),
        Spacer(1, 8 * mm),
        Paragraph(f"<b>{ddt.title}</b> n. {ddt.number} del {ddt.date}", styles["Heading2"]),
        Paragraph(f"Destinatario: {CUSTOMER}", styles["Normal"]),
        Paragraph(ddt.order_ref, styles["Normal"]),
        Paragraph("Causale del trasporto: Vendita - Trasporto a cura del mittente", styles["Normal"]),
        Spacer(1, 6 * mm),
        table,
        Spacer(1, 12 * mm),
        Paragraph("Firma vettore ______________    Firma destinatario ______________", styles["Normal"]),
    ])


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for ddt in DDTS:
        render(ddt)
        print(f"Creato {ddt.filename}")


if __name__ == "__main__":
    main()