#!/usr/bin/env python3
"""
Exporta dataset JSON para CSV com:
id, question, context, expected_answer

O campo context concatena todos os parágrafos, sem incluir títulos das fontes.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, List


def flatten_context(context: Any) -> str:
    paragraphs: List[str] = []
    if isinstance(context, list):
        for block in context:
            if isinstance(block, list) and len(block) == 2 and isinstance(block[1], list):
                paragraphs.extend(str(p).strip() for p in block[1] if str(p).strip())
    return " ".join(paragraphs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    data = json.loads(args.dataset.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "question", "context", "expected_answer"])
        writer.writeheader()
        for item in data:
            writer.writerow({
                "id": item.get("id"),
                "question": item.get("question", ""),
                "context": flatten_context(item.get("context", [])),
                "expected_answer": item.get("expected_answer", "")
            })

    print(f"CSV salvo em: {args.out}")


if __name__ == "__main__":
    main()
