#!/usr/bin/env python3
"""
Aplica correções manuais por id.

O patch deve ser uma lista de objetos completos ou parciais.
Campos presentes no patch substituem os campos do item original.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    patches = json.loads(args.patch.read_text(encoding="utf-8"))

    by_id = {int(item["id"]): item for item in dataset}
    changed = []

    for patch in patches:
        pid = int(patch["id"])
        if pid not in by_id:
            raise KeyError(f"ID {pid} não encontrado no dataset.")
        by_id[pid].update(patch)
        changed.append(pid)

    updated = [by_id[i] for i in sorted(by_id)]
    args.out.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Correções aplicadas aos IDs: {changed}")
    print(f"Arquivo salvo em: {args.out}")


if __name__ == "__main__":
    main()
