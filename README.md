# PetroQA-Brasil

`PetroQA-Brasil` é um projeto de criação, curadoria e auditoria de um dataset de question-answering em português voltado para Geociências, com ênfase em Geologia do Petróleo. O foco do projeto não é responder perguntas por simples extração literal do contexto, mas construir itens em que a resposta esperada dependa de inferência relacional entre entidades, processos e propriedades geológicas descritas em fontes reais.

A versão atualmente presente neste repositório contém:

- `dataset_full.json`: dataset final em JSON, com 150 itens;
- `dataset_full.csv`: dataset final em CSV, com 150 itens;
- `sources.csv`: catálogo de 20 fontes em português usadas na construção;
- `audit_questions_vs_sources.csv`: trilha de auditoria ligando trechos de contexto às fontes;
- `ragas_evaluation.csv`: avaliação automatizada por item com métricas de contexto e resposta;
- `scripts_geracao/`: pipeline reproduzível para gerar, validar, corrigir e exportar o dataset.

Repository (v.1 - RAG): <https://github.com/tiagoriosrocha/PetroQA-Brasil>
Repository (v.2 - GraphRAG): <https://github.com/tiagoriosrocha/PetroQA-Brasil-GraphRAG>

## Objetivo

O projeto foi desenhado para avaliar sistemas de QA em Geociências em cenários nos quais a resposta exige combinar evidências, por exemplo:

- bacia sedimentar -> unidade estratigráfica -> litologia;
- rocha geradora -> migração -> reservatório -> selo;
- fácies -> ambiente deposicional -> propriedade petrofísica;
- estrutura/falha -> compartimentação -> fluido ou regime de pressão;
- idade relativa -> posição estratigráfica -> evolução geológica.

Em outras palavras, o dataset serve melhor para testar recuperação contextual, fidelidade à fonte e capacidade de inferência geocientífica do que para perguntas puramente factuais de uma única sentença.

## Artefatos principais

### `dataset_full.json` e `dataset_full.csv`

Arquivo principal do projeto. Cada item contém:

```json
{
  "id": 1,
  "question": "Pergunta em português.",
  "context": [
    [
      "Título da fonte",
      [
        "Trecho literal da fonte.",
        "Outro trecho literal da mesma fonte."
      ]
    ]
  ],
  "expected_answer": "Resposta esperada inferida a partir dos trechos.",
  "tipo_inferencia": "rotulo_metodologico",
  "source": [
    "https://link-da-fonte"
  ]
}
```

Campos:

| Campo | Descrição |
|---|---|
| `id` | Identificador numérico do item. |
| `question` | Pergunta em português, com uma única intenção e uma única interrogação. |
| `context` | Lista de blocos multicontexto. Cada bloco contém o título da fonte e uma lista de trechos literais. |
| `expected_answer` | Resposta esperada, fiel ao contexto, mas não necessariamente uma cópia literal. |
| `tipo_inferencia` | Rótulo analítico do tipo principal de inferência exigida. |
| `source` | Lista de URLs alinhada aos blocos de contexto. |

### `sources.csv`

Catálogo das fontes usadas na construção do dataset, com colunas:

```csv
id,fonte,link
```

### `audit_questions_vs_sources.csv`

Arquivo de rastreabilidade para auditoria. Ele liga questões e trechos de contexto às respectivas fontes, permitindo revisar de onde cada evidência textual foi extraída.

### `ragas_evaluation.csv`

Arquivo com uma rodada de avaliação automatizada por item. Hoje ele registra, entre outras, as métricas:

- `context_precision_score`
- `contextual_relevancy_score`
- `contextual_recall_score`
- `faithfulness_score`
- `answer_relevance_score`

## Como o dataset foi construído

O fluxo do projeto, como implementado em `scripts_geracao/scripts/`, é o seguinte:

1. `01_fetch_sources.py`  
   Baixa cada URL de `sources.csv` e tenta extrair texto bruto de HTML ou PDF.

2. `02_extract_candidate_passages.py`  
   Divide os textos em parágrafos e seleciona passagens candidatas usando heurísticas e palavras-chave geocientíficas.

3. `03_build_generation_prompts.py`  
   Agrupa evidências em pequenos conjuntos multicontexto e monta prompts para geração de itens por LLM.

4. `04_generate_with_llm.py`  
   Envia os prompts para um endpoint compatível com Chat Completions e salva a resposta bruta.

5. `05_merge_and_validate_dataset.py`  
   Consolida os itens gerados, renumera IDs, valida schema, formato de `context`, termos proibidos e aderência literal ao banco de evidências.

6. `06_apply_item_corrections.py`  
   Aplica correções manuais por ID quando a geração automática precisa de ajuste editorial.

7. `07_export_csv.py`  
   Exporta o dataset final para CSV com `id`, `question`, `context` e `expected_answer`.

8. `08_build_source_audit.py`  
   Gera uma tabela de auditoria item-contexto-fonte para rastreabilidade.

## Premissas metodológicas

O projeto segue algumas regras centrais:

- usar somente fontes em português;
- manter os trechos do `context` de forma literal, sem parafrasear;
- evitar perguntas metalinguísticas sobre RAG, GraphRAG, ontologias ou o próprio dataset;
- exigir uma única intenção por pergunta;
- produzir respostas esperadas sustentadas pelo contexto, mesmo quando inferenciais;
- manter `tipo_inferencia` como rótulo de análise, não como dica explícita dentro da pergunta ou da resposta;
- revisar manualmente os itens após a geração automática.

A taxonomia usada na construção dos prompts está em `scripts_geracao/config/relation_types.json`. Como o dataset foi refinado iterativamente, a versão final pode conter rótulos adicionais ou consolidados em relação a essa taxonomia-base.

## Reproduzindo a pipeline

Os artefatos intermediários não estão versionados na raiz. Se quiser reproduzir a geração, um fluxo prático a partir da raiz do projeto é:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts_geracao/requirements-generation.txt

mkdir -p data/raw_sources

python scripts_geracao/scripts/01_fetch_sources.py \
  --sources sources.csv \
  --out-dir data/raw_sources

python scripts_geracao/scripts/02_extract_candidate_passages.py \
  --raw-dir data/raw_sources \
  --sources sources.csv \
  --out data/evidence_bank.jsonl

python scripts_geracao/scripts/03_build_generation_prompts.py \
  --evidence data/evidence_bank.jsonl \
  --relations scripts_geracao/config/relation_types.json \
  --system-prompt scripts_geracao/prompts/system_prompt_geoinfer_pt.md \
  --user-template scripts_geracao/prompts/user_prompt_template.md \
  --out data/prompts.jsonl \
  --target-items 150

export LLM_API_URL="https://SEU-ENDPOINT/chat/completions"
export LLM_API_KEY="SUA_CHAVE"
export LLM_MODEL="seu-modelo"

python scripts_geracao/scripts/04_generate_with_llm.py \
  --prompts data/prompts.jsonl \
  --out data/generations.jsonl

python scripts_geracao/scripts/05_merge_and_validate_dataset.py \
  --generations data/generations.jsonl \
  --evidence data/evidence_bank.jsonl \
  --out data/dataset_generated.json \
  --max-items 150

python scripts_geracao/scripts/06_apply_item_corrections.py \
  --dataset data/dataset_generated.json \
  --patch caminho/para/correcoes.json \
  --out data/dataset_generated_corrected.json

python scripts_geracao/scripts/07_export_csv.py \
  --dataset data/dataset_generated_corrected.json \
  --out data/petroqa_brasil.csv

python scripts_geracao/scripts/08_build_source_audit.py \
  --dataset data/dataset_generated_corrected.json \
  --sources sources.csv \
  --out data/audit_questions_vs_sources.csv
```

## Validações aplicadas na consolidação

O script `05_merge_and_validate_dataset.py` verifica, entre outros pontos:

- presença dos campos obrigatórios;
- estrutura multicontexto de `context`;
- existência de exatamente uma interrogação em `question`;
- ausência de termos proibidos como `rag`, `graphrag`, `ontologia` e expressões como `relação espacial`;
- presença literal dos parágrafos de contexto no banco de evidências;
- existência de lista não vazia em `source`.

## Como usar o dataset

Para avaliação de sistemas de QA, a prática mais consistente é:

1. fornecer ao modelo apenas `question` e `context`;
2. manter `tipo_inferencia` fora da entrada do modelo e usar esse campo apenas para análise posterior;
3. usar `expected_answer` como referência de avaliação, não como contexto adicional;
4. consultar `audit_questions_vs_sources.csv` quando for necessário auditar a origem de um trecho;
5. usar `ragas_evaluation.csv` como apoio comparativo, não como substituto de revisão humana.

## Limitações

- Extração automática de HTML e PDF pode falhar, especialmente em páginas dinâmicas.
- A qualidade final depende da geração do LLM e da revisão manual posterior.
- Fontes externas podem mudar, sair do ar ou alterar o texto ao longo do tempo.
- O projeto redistribui trechos literais de fontes externas; antes de publicar ou reaproveitar o dataset, revise licenças e termos de uso.
- Alguns arquivos auxiliares ainda refletem o nome legado `GeoInfer-PT` e exemplos antigos de caminho; use este README como referência atual da organização do repositório.

## Citação sugerida

```text
PetroQA-Brasil is a Portuguese geoscience question-answering dataset focused on source-grounded relational inference over geological and petroleum-geology texts.

Authors: Tiago Rios da Rocha, João Netto, Karin Becker
Institution: Universidade Federal do Rio Grande do Sul
Project: OntoKG
```
