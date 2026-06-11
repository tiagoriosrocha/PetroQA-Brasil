#!/usr/bin/env python3
"""
Constrói prompts para geração de itens QA.

O script agrupa passagens candidatas em pequenos conjuntos multicontexto.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List


def load_jsonl(path: Path) -> List[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def format_contexts(records: List[dict]) -> str:
    blocks = []
    for rec in records:
        blocks.append(
            json.dumps({
                "titulo": rec["source_title"],
                "link": rec["source_url"],
                "trecho_literal": rec["text"]
            }, ensure_ascii=False, indent=2)
        )
    return "\n\n".join(blocks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--relations", required=True, type=Path)
    parser.add_argument("--system-prompt", required=True, type=Path)
    parser.add_argument("--user-template", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--target-items", type=int, default=150)
    parser.add_argument("--items-per-prompt", type=int, default=3)
    parser.add_argument("--contexts-per-prompt", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    evidence = load_jsonl(args.evidence)
    evidence = sorted(evidence, key=lambda x: x.get("score", 0), reverse=True)

    relations = json.loads(args.relations.read_text(encoding="utf-8"))
    relation_names = [r["nome"] for r in relations["tipos_inferencia"]]
    relation_text = json.dumps(relations["tipos_inferencia"], ensure_ascii=False, indent=2)

    system_prompt = args.system_prompt.read_text(encoding="utf-8")
    template = args.user_template.read_text(encoding="utf-8")

    # Amostragem estratificada simples por fonte para evitar muitos prompts da mesma origem
    by_source: Dict[str, List[dict]] = {}
    for rec in evidence:
        by_source.setdefault(rec["source_id"], []).append(rec)

    source_ids = list(by_source.keys())
    random.shuffle(source_ids)

    prompts_needed = (args.target_items + args.items_per_prompt - 1) // args.items_per_prompt
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("w", encoding="utf-8") as out:
        for i in range(prompts_needed):
            chosen = []
            random.shuffle(source_ids)
            for sid in source_ids:
                if len(chosen) >= args.contexts_per_prompt:
                    break
                if by_source[sid]:
                    chosen.append(random.choice(by_source[sid]))

            user_prompt = template.format(
                n_items=args.items_per_prompt,
                relation_types=relation_text,
                contexts=format_contexts(chosen)
            )

            record = {
                "prompt_id": i + 1,
                "system": system_prompt,
                "user": user_prompt,
                "relation_types_allowed": relation_names,
                "source_ids": [r["source_id"] for r in chosen]
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Prompts gerados: {prompts_needed}")
    print(f"Arquivo: {args.out}")


if __name__ == "__main__":
    main()
