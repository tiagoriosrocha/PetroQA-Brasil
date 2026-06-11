#!/usr/bin/env python3
"""
Executa prompts contra um endpoint compatível com Chat Completions.

Variáveis esperadas:
  LLM_API_URL   endpoint completo, por exemplo: https://.../chat/completions
  LLM_API_KEY   chave de API
  LLM_MODEL     nome do modelo

Este script salva a resposta bruta em JSONL para posterior consolidação.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests
from tqdm import tqdm


def call_llm(api_url: str, api_key: str, model: str, system: str, user: str, temperature: float = 0.2) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    }
    response = requests.post(api_url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    api_url = os.environ.get("LLM_API_URL")
    api_key = os.environ.get("LLM_API_KEY")
    model = os.environ.get("LLM_MODEL")

    if not api_url or not api_key or not model:
        raise RuntimeError("Defina LLM_API_URL, LLM_API_KEY e LLM_MODEL.")

    prompts = [json.loads(line) for line in args.prompts.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        prompts = prompts[:args.limit]

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("a", encoding="utf-8") as out:
        for prompt in tqdm(prompts, desc="Gerando"):
            try:
                content = call_llm(api_url, api_key, model, prompt["system"], prompt["user"], args.temperature)
                record = {
                    "prompt_id": prompt["prompt_id"],
                    "status": "ok",
                    "content": content,
                    "source_ids": prompt.get("source_ids", [])
                }
            except Exception as exc:
                record = {
                    "prompt_id": prompt["prompt_id"],
                    "status": "error",
                    "error": repr(exc),
                    "source_ids": prompt.get("source_ids", [])
                }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            time.sleep(args.delay)

    print(f"Gerações salvas em: {args.out}")


if __name__ == "__main__":
    main()
