#!/usr/bin/env python3
"""
Gera uma tabela de auditoria item-contexto-fonte.

Como o dataset usa contextos multicontexto, cada parágrafo vira uma linha.
A linha em sources.csv é calculada considerando cabeçalho como linha 1.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_source_lines(path: Path) -> dict:
    mapping = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            mapping[row["link"].strip()] = line_no
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    data = json.loads(args.dataset.read_text(encoding="utf-8"))
    source_lines = read_source_lines(args.sources)

    fieldnames = [
        "id", "question", "expected_answer", "tipo_inferencia",
        "titulo_contexto", "texto_contexto", "source", "linha_sources_csv"
    ]

    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for item in data:
            sources = item.get("source", [])
            for block_idx, block in enumerate(item.get("context", [])):
                title = block[0]
                paragraphs = block[1]
                source_url = sources[block_idx] if block_idx < len(sources) else ""
                for paragraph in paragraphs:
                    writer.writerow({
                        "id": item.get("id"),
                        "question": item.get("question", ""),
                        "expected_answer": item.get("expected_answer", ""),
                        "tipo_inferencia": item.get("tipo_inferencia", ""),
                        "titulo_contexto": title,
                        "texto_contexto": paragraph,
                        "source": source_url,
                        "linha_sources_csv": source_lines.get(source_url, "")
                    })

    print(f"Auditoria salva em: {args.out}")


if __name__ == "__main__":
    main()
