from typing import Literal

from mcp.server import MCPServer

from reconciliation import agent_tools

mcp = MCPServer("invoice-reconciliation")

Status = Literal["MATCHED", "DISCREPANCIES", "WAITING_FOR_DDT"]


@mcp.tool()
def list_reconciliations(status: Status | None = None) -> list[dict]:
    """Elenca le fatture passive con l'esito della riconciliazione fattura / DDT / ordine.

    Usalo per domande generali tipo "quali fatture hanno problemi?".
    Filtra per status: MATCHED (tutto ok), DISCREPANCIES (anomalie),
    WAITING_FOR_DDT (manca ancora il documento di trasporto).
    Ogni fattura riporta amount_at_risk: gli euro che si rischia di pagare in piu'.
    """
    return agent_tools.list_reconciliations(status)


@mcp.tool()
def get_reconciliation(invoice_number: str) -> dict:
    """Dettaglio della riconciliazione di una fattura, con l'elenco delle anomalie.

    invoice_number e' il numero della fattura esattamente come appare nel documento
    (es. "EM/26/1022"). Ogni anomalia ha un tipo, un messaggio leggibile,
    il valore atteso, quello fatturato e l'importo a rischio.
    """
    return agent_tools.get_reconciliation(invoice_number)


@mcp.tool()
def get_purchase_order(order_number: str) -> dict:
    """Righe di un ordine d'acquisto: articoli, quantita' e prezzi concordati.

    Utile per spiegare un'anomalia confrontando la fattura con l'ordine (es. "PO-2026-003").
    """
    return agent_tools.get_purchase_order(order_number)


if __name__ == "__main__":
    mcp.run()