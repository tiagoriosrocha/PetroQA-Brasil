#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/raw_sources data

python scripts/01_fetch_sources.py \
  --sources sources.csv \
  --out-dir data/raw_sources

python scripts/02_extract_candidate_passages.py \
  --raw-dir data/raw_sources \
  --sources sources.csv \
  --out data/evidence_bank.jsonl

python scripts/03_build_generation_prompts.py \
  --evidence data/evidence_bank.jsonl \
  --relations config/relation_types.json \
  --system-prompt prompts/system_prompt_geoinfer_pt.md \
  --user-template prompts/user_prompt_template.md \
  --out data/prompts.jsonl \
  --target-items 150

# Requer LLM_API_URL, LLM_API_KEY e LLM_MODEL.
python scripts/04_generate_with_llm.py \
  --prompts data/prompts.jsonl \
  --out data/generations.jsonl

python scripts/05_merge_and_validate_dataset.py \
  --generations data/generations.jsonl \
  --evidence data/evidence_bank.jsonl \
  --out data/dataset_generated.json \
  --max-items 150

python scripts/06_apply_item_corrections.py \
  --dataset data/dataset_generated.json \
  --patch patches/corrections_113_124_144.json \
  --out data/dataset_generated_corrected.json

python scripts/07_export_csv.py \
  --dataset data/dataset_generated_corrected.json \
  --out data/geoinfer_pt.csv

python scripts/08_build_source_audit.py \
  --dataset data/dataset_generated_corrected.json \
  --sources sources.csv \
  --out data/audit_questions_vs_sources.csv
