import os
from collections.abc import Callable
from typing import Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from reconciliation import agent_tools
from reconciliation.approvals import Decision, DecisionError, Role

Status = Literal["MATCHED", "DISCREPANCIES", "WAITING_FOR_DDT"]


def _call(function: Callable, *args):
    """Errori previsti (regole, dati mancanti) -> messaggio leggibile per il modello.

    Qualsiasi altra eccezione resta un errore imprevisto e il suo dettaglio non viene esposto.
    """
    try:
        return function(*args)
    except (DecisionError, ValueError) as error:
        raise ToolError(str(error)) from error


def create_mcp_server(role: Role, actor: str) -> MCPServer:
    """Crea un server MCP con i soli tool consentiti al ruolo.

    Ruolo e utente vengono fissati qui, lato server: il modello non puo' sceglierli.
    """
    mcp = MCPServer("invoice-reconciliation")

    @mcp.tool()
    def list_reconciliations(status: Status | None = None) -> list[dict]:
        """Elenca le fatture passive con l'esito della riconciliazione fattura / DDT / ordine.

        Usalo per domande generali tipo "quali fatture hanno problemi?".
        Filtra per status: MATCHED (tutto ok), DISCREPANCIES (anomalie),
        WAITING_FOR_DDT (manca ancora il documento di trasporto).
        Ogni fattura riporta amount_at_risk (euro che si rischia di pagare in piu')
        e approval_status (PENDING da decidere, APPROVED approvata, BLOCKED bloccata).
        """
        return _call(agent_tools.list_reconciliations, status)

    @mcp.tool()
    def get_reconciliation(invoice_number: str) -> dict:
        """Dettaglio della riconciliazione di una fattura, con l'elenco delle anomalie.

        invoice_number e' il numero della fattura esattamente come appare nel documento
        (es. "EM/26/1022"). Ogni anomalia ha un tipo, un messaggio leggibile,
        il valore atteso, quello fatturato e l'importo a rischio.
        """
        return _call(agent_tools.get_reconciliation, invoice_number)

    @mcp.tool()
    def get_purchase_order(order_number: str) -> dict:
        """Righe di un ordine d'acquisto: articoli, quantita' e prezzi concordati.

        Utile per spiegare un'anomalia confrontando la fattura con l'ordine (es. "PO-2026-003").
        """
        return _call(agent_tools.get_purchase_order, order_number)

    if role == Role.OPERATOR:

        @mcp.tool()
        def approve_invoice(invoice_number: str, note: str | None = None) -> dict:
            """Approva il pagamento di una fattura. Azione definitiva.

            Usalo solo dopo che l'utente ha chiesto esplicitamente di approvare quella fattura.
            Se la fattura ha anomalie, note e' obbligatoria e deve riportare la motivazione
            data dall'utente: non inventarla.
            """
            return _call(agent_tools.decide_invoice, invoice_number, Decision.APPROVE, actor, role, note)

        @mcp.tool()
        def block_invoice(invoice_number: str, reason: str) -> dict:
            """Blocca il pagamento di una fattura. Azione definitiva.

            Usalo solo dopo che l'utente ha chiesto esplicitamente di bloccare quella fattura.
            reason e' la motivazione data dall'utente (es. "attendere nota di credito").
            """
            return _call(agent_tools.decide_invoice, invoice_number, Decision.BLOCK, actor, role, reason)

    return mcp


# Server di default con ruolo di sola lettura
mcp = create_mcp_server(Role.VIEWER, "mcp-client")


if __name__ == "__main__":
    create_mcp_server(
        Role(os.environ.get("MCP_ROLE", "viewer")),
        os.environ.get("MCP_ACTOR", "mcp-client"),
    ).run()