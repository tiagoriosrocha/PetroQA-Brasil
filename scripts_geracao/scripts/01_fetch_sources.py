#!/usr/bin/env python3
"""
Baixa fontes de um sources.csv e tenta extrair texto bruto de HTML ou PDF.

Entrada:
  sources.csv com colunas: id, fonte, link

Saída:
  data/raw_sources/source_<id>.txt
  data/raw_sources/source_index.json
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import time
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from tqdm import tqdm


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_html_text(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    paragraphs = []
    for node in soup.find_all(["p", "li", "h1", "h2", "h3", "h4"]):
        txt = node.get_text(" ", strip=True)
        if txt and len(txt) > 30:
            paragraphs.append(txt)
    return clean_text("\n\n".join(paragraphs))


def extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return clean_text("\n\n".join(pages))


def fetch_url(url: str, timeout: int = 40) -> tuple[str, str]:
    headers = {
        "User-Agent": "GeoInfer-PT dataset research script/1.0"
    }
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "application/pdf" in content_type or url.lower().endswith(".pdf"):
        return extract_pdf_text(response.content), "pdf"
    return extract_html_text(response.content), "html"


def read_sources(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"id", "fonte", "link"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"sources.csv sem colunas obrigatórias: {sorted(missing)}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_sources(args.sources)
    index = []

    for row in tqdm(rows, desc="Baixando fontes"):
        sid = str(row["id"]).strip()
        title = row["fonte"].strip()
        url = row["link"].strip()
        out_txt = args.out_dir / f"source_{sid}.txt"

        status = "ok"
        kind = None
        error = None

        try:
            text, kind = fetch_url(url)
            out_txt.write_text(text, encoding="utf-8")
        except Exception as exc:
            status = "error"
            error = repr(exc)
            if not out_txt.exists():
                out_txt.write_text("", encoding="utf-8")

        index.append({
            "id": sid,
            "fonte": title,
            "link": url,
            "file": str(out_txt),
            "type": kind,
            "status": status,
            "error": error
        })

        time.sleep(args.delay)

    (args.out_dir / "source_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Fontes processadas: {len(index)}")
    print(f"Índice salvo em: {args.out_dir / 'source_index.json'}")


if __name__ == "__main__":
    main()
