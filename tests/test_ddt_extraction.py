from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from reconciliation.ddt_extraction import DdtExtractionError, extract_ddt


class FakeClient:
    def __init__(self, content):
        self.response = SimpleNamespace(
            content=content,
            usage=SimpleNamespace(input_tokens=100, output_tokens=50),
        )
        self.messages = self

    def create(self, **kwargs):
        self.last_request = kwargs
        return self.response


def tool_use(data):
    return SimpleNamespace(type="tool_use", input=data)


VALID_DDT = {
    "ddt_number": "EM-DDT-3310",
    "ddt_date": "2026-09-11",
    "supplier_name": "Elettroforniture Mincio Srl",
    "supplier_vat_number": "03333333333",
    "order_number": "PO-2026-003",
    "lines": [
        {"item_code": "INT-16A", "description": "Interruttore", "quantity": 20, "unit": "PZ"},
    ],
}


def test_parses_structured_output():
    client = FakeClient([tool_use(VALID_DDT)])

    result = extract_ddt(b"%PDF-fake", client=client, model="test-model")

    assert result.ddt.ddt_number == "EM-DDT-3310"
    assert result.ddt.ddt_date == date(2026, 9, 11)
    assert result.ddt.lines[0].quantity == Decimal("20")
    assert result.input_tokens == 100
    assert client.last_request["tool_choice"]["type"] == "tool"


def test_fails_without_tool_use():
    client = FakeClient([SimpleNamespace(type="text", text="Non so leggerlo")])

    with pytest.raises(DdtExtractionError, match="strutturati"):
        extract_ddt(b"%PDF-fake", client=client, model="test-model")


def test_fails_on_invalid_data():
    broken = {**VALID_DDT, "ddt_date": "non una data"}
    client = FakeClient([tool_use(broken)])

    with pytest.raises(DdtExtractionError, match="non validi"):
        extract_ddt(b"%PDF-fake", client=client, model="test-model")