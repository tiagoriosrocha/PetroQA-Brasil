#!/usr/bin/env python3
"""
Consolida respostas do LLM em um dataset JSON e aplica validações.

A validação de contexto literal verifica se cada parágrafo do campo context aparece
em alguma passagem do evidence_bank.jsonl.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


FORBIDDEN_IN_QA = [
    "graph rag", "graphrag", "rag", "ontologia", "ontology", "dataset",
    "relação espacial", "relação temporal", "relação interpretativa",
    "relação composicional", "inferência espacial", "inferência temporal",
    "inferência interpretativa", "tipo de inferência"
]


def extract_json(content: str) -> Any:
    content = content.strip()
    # Remove cercas markdown se existirem
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # tenta capturar a primeira lista JSON
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end + 1])
        # tenta objeto único
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end + 1])
        raise


def flatten_context(context: Any) -> List[str]:
    texts = []
    if not isinstance(context, list):
        return texts
    for block in context:
        if not (isinstance(block, list) and len(block) == 2):
            continue
        paragraphs = block[1]
        if isinstance(paragraphs, list):
            texts.extend([str(p).strip() for p in paragraphs if str(p).strip()])
    return texts


def validate_item(item: Dict[str, Any], evidence_texts: List[str]) -> List[str]:
    errors = []
    required = ["id", "question", "context", "expected_answer", "tipo_inferencia", "source"]
    for field in required:
        if field not in item:
            errors.append(f"campo ausente: {field}")

    q = str(item.get("question", ""))
    ans = str(item.get("expected_answer", ""))

    if q.count("?") != 1:
        errors.append("question deve conter exatamente uma interrogação")

    qa_lower = (q + " " + ans).lower()
    for term in FORBIDDEN_IN_QA:
        if term in qa_lower:
            errors.append(f"termo proibido em question/expected_answer: {term}")

    if not isinstance(item.get("context"), list):
        errors.append("context deve ser lista multicontexto")

    for i, block in enumerate(item.get("context", [])):
        if not (isinstance(block, list) and len(block) == 2 and isinstance(block[1], list)):
            errors.append(f"context bloco {i} inválido")

    for paragraph in flatten_context(item.get("context")):
        if not any(paragraph in ev for ev in evidence_texts):
            errors.append("parágrafo de context não encontrado literalmente no evidence_bank")

    if not isinstance(item.get("source"), list) or not item.get("source"):
        errors.append("source deve ser lista não vazia")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generations", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-items", type=int, default=150)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    evidence_records = [json.loads(line) for line in args.evidence.read_text(encoding="utf-8").splitlines() if line.strip()]
    evidence_texts = [r["text"] for r in evidence_records]

    items: List[Dict[str, Any]] = []
    parse_errors = []

    for line in args.generations.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("status") != "ok":
            parse_errors.append({"prompt_id": rec.get("prompt_id"), "error": rec.get("error", "status error")})
            continue
        try:
            parsed = extract_json(rec["content"])
            if isinstance(parsed, dict):
                parsed = [parsed]
            if isinstance(parsed, list):
                for obj in parsed:
                    if isinstance(obj, dict):
                        items.append(obj)
        except Exception as exc:
            parse_errors.append({"prompt_id": rec.get("prompt_id"), "error": repr(exc)})

    # normaliza IDs e corta no máximo desejado
    items = items[:args.max_items]
    for idx, item in enumerate(items, start=1):
        item["id"] = idx

    report = {
        "total_items": len(items),
        "parse_errors": parse_errors,
        "item_errors": []
    }

    valid_items = []
    for item in items:
        errs = validate_item(item, evidence_texts)
        if errs:
            report["item_errors"].append({"id": item.get("id"), "errors": errs})
        valid_items.append(item)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(valid_items, ensure_ascii=False, indent=2), encoding="utf-8")

    report_path = args.report or args.out.with_suffix(".validation_report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Itens consolidados: {len(valid_items)}")
    print(f"Dataset salvo em: {args.out}")
    print(f"Relatório salvo em: {report_path}")
    if report["item_errors"]:
        print(f"Atenção: {len(report['item_errors'])} itens têm erros de validação.")


if __name__ == "__main__":
    main()
