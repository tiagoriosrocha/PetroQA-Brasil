#!/usr/bin/env python3
"""
Extrai passagens candidatas de textos brutos.

A seleção é heurística: prioriza parágrafos com termos geológicos e de petróleo.
O texto de cada passagem continua literal, apenas normalizado em espaços.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List


KEYWORDS = [
    "bacia", "sedimentar", "formação", "membro", "estratigrafia", "estratigráfico",
    "litologia", "rocha", "carbonático", "carbonato", "calcário", "dolomito",
    "evaporito", "sal", "halita", "anidrita", "reservatório", "selo", "selante",
    "trapa", "armadilha", "hidrocarboneto", "petróleo", "óleo", "gás",
    "matéria orgânica", "rocha geradora", "migração", "acumulação",
    "falha", "fratura", "estrutura", "compartimentação", "pressão", "fluido",
    "fácies", "sísmica", "turbidito", "turbidítico", "leque", "talude",
    "porosidade", "permeabilidade", "permoporosa", "poço", "sondagem",
    "fóssil", "paleontologia", "idade", "geocronologia", "deposicional",
    "lacustre", "marinho", "delta", "ambiente"
]


def normalize_ws(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_paragraphs(text: str) -> List[str]:
    chunks = re.split(r"\n\s*\n+", text)
    paragraphs = []
    for chunk in chunks:
        txt = normalize_ws(chunk)
        if 120 <= len(txt) <= 1200:
            paragraphs.append(txt)
    return paragraphs


def score_passage(text: str) -> int:
    lower = text.lower()
    score = 0
    for kw in KEYWORDS:
        if kw in lower:
            score += 1
    # bônus para passagens com entidades nomeadas geológicas comuns
    for marker in ["Bacia de", "Formação", "Campo de", "pré-sal", "Pré-sal", "Aptiano", "Santos", "Campos"]:
        if marker in text:
            score += 2
    return score


def read_sources(path: Path) -> Dict[str, Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return {str(r["id"]).strip(): r for r in csv.DictReader(f)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--min-score", type=int, default=2)
    args = parser.parse_args()

    source_meta = read_sources(args.sources)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with args.out.open("w", encoding="utf-8") as out:
        for txt_file in sorted(args.raw_dir.glob("source_*.txt")):
            sid = txt_file.stem.replace("source_", "")
            meta = source_meta.get(sid, {})
            title = meta.get("fonte", f"Fonte {sid}")
            url = meta.get("link", "")
            text = txt_file.read_text(encoding="utf-8", errors="ignore")

            for i, paragraph in enumerate(split_paragraphs(text), start=1):
                score = score_passage(paragraph)
                if score >= args.min_score:
                    record = {
                        "source_id": sid,
                        "source_title": title,
                        "source_url": url,
                        "paragraph_id": i,
                        "score": score,
                        "text": paragraph
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    total += 1

    print(f"Passagens candidatas salvas: {total}")
    print(f"Arquivo: {args.out}")


if __name__ == "__main__":
    main()
