"""Valuta l'estrazione DDT su piu' modelli confrontandola con samples/eval/expected.json."""

import json
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from anthropic import Anthropic

from reconciliation.config import settings
from reconciliation.ddt_extraction import DdtExtractionError, ExtractedDdt, extract_ddt

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "samples" / "eval" / "expected.json"
REPORT = ROOT / "reports" / "extraction_eval.json"

MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
}

# Dollari per milione di token (input, output).
# Verificare sulla pagina Pricing della console prima di citarli nel README.
PRICES = {
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-sonnet-5": (3.0, 15.0),
}

FIELDS = ["ddt_number", "ddt_date", "supplier_vat_number", "order_number"]


def _text(value) -> str:
    return "" if value is None else str(value).strip().upper()


def score(expected: dict, extracted: ExtractedDdt) -> dict:
    actual = {
        "ddt_number": extracted.ddt_number,
        "ddt_date": extracted.ddt_date.isoformat(),
        "supplier_vat_number": extracted.supplier_vat_number,
        "order_number": extracted.order_number,
    }
    errors = []
    correct = 0

    for name in FIELDS:
        if _text(actual[name]) == _text(expected[name]):
            correct += 1
        else:
            errors.append(f"{name}: atteso {expected[name]!r}, letto {actual[name]!r}")

    expected_lines = {(_text(code), Decimal(quantity)) for code, quantity in expected["lines"]}
    extracted_lines = {(_text(line.item_code), line.quantity) for line in extracted.lines}

    correct += len(expected_lines & extracted_lines)
    for code, quantity in sorted(expected_lines - extracted_lines):
        errors.append(f"riga {code} x {quantity}: mancante o letta male")
    for code, quantity in sorted(extracted_lines - expected_lines):
        errors.append(f"riga {code} x {quantity}: non attesa")

    return {"correct": correct, "total": len(FIELDS) + len(expected_lines), "errors": errors}


def cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES[model]
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def evaluate_model(client: Anthropic, label: str, model: str, cases: list[dict]) -> dict:
    documents = []
    for case in cases:
        pdf = (ROOT / case["file"]).read_bytes()
        start = time.perf_counter()
        input_tokens = output_tokens = 0
        try:
            extraction = extract_ddt(pdf, client=client, model=model)
            result = score(case, extraction.ddt)
            input_tokens, output_tokens = extraction.input_tokens, extraction.output_tokens
        except DdtExtractionError as error:
            result = {"correct": 0, "total": len(FIELDS) + len(case["lines"]), "errors": [str(error)]}
        seconds = time.perf_counter() - start

        document = {
            "file": case["file"],
            "case": case["case"],
            **result,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost(model, input_tokens, output_tokens),
            "seconds": round(seconds, 2),
        }
        documents.append(document)
        status = "ok" if not result["errors"] else f"{len(result['errors'])} errori"
        print(f"  [{label}] {Path(case['file']).name}: {status} ({seconds:.1f} s)")

    correct = sum(d["correct"] for d in documents)
    total = sum(d["total"] for d in documents)
    return {
        "model": model,
        "field_accuracy": correct / total,
        "perfect_documents": sum(1 for d in documents if not d["errors"]),
        "documents": documents,
        "total_cost_usd": sum(d["cost_usd"] for d in documents),
        "avg_seconds": sum(d["seconds"] for d in documents) / len(documents),
    }


def main() -> None:
    cases = json.loads(EXPECTED.read_text(encoding="utf-8"))
    client = Anthropic(api_key=settings.anthropic_api_key.get_secret_value())

    results = {}
    for label, model in MODELS.items():
        print(f"\nValutazione {label} ({model})")
        results[label] = evaluate_model(client, label, model, cases)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {"generated_at": datetime.now(UTC).isoformat(), "cases": len(cases), "results": results},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\n| Modello | Precisione campi | Documenti perfetti | Costo totale | Tempo medio |")
    print("|---|---|---|---|---|")
    for label, r in results.items():
        print(
            f"| {label} | {r['field_accuracy']:.1%} | {r['perfect_documents']}/{len(cases)} "
            f"| ${r['total_cost_usd']:.4f} | {r['avg_seconds']:.1f} s |"
        )

    for label, r in results.items():
        failed = [d for d in r["documents"] if d["errors"]]
        print(f"\nErrori {label}: {'nessuno' if not failed else ''}")
        for d in failed:
            print(f"  {Path(d['file']).name} ({d['case']})")
            for error in d["errors"]:
                print(f"    - {error}")

    print(f"\nReport completo: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()