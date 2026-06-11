# PetroQA-Brasil

`PetroQA-Brasil` e um projeto de criacao, curadoria e auditoria de um dataset de question-answering em portugues voltado para Geociencias, com enfase em Geologia do Petroleo. O foco do projeto nao e responder perguntas por simples extracao literal do contexto, mas construir itens em que a resposta esperada dependa de inferencia relacional entre entidades, processos e propriedades geologicas descritas em fontes reais.

A versao atualmente presente neste repositorio contem:

- `dataset_full.json`: dataset final em JSON, com 150 itens;
- `sources.csv`: catalogo de 20 fontes em portugues usadas na construcao;
- `audit_questions_vs_sources.csv`: trilha de auditoria ligando trechos de contexto as fontes;
- `ragas_evaluation.csv`: avaliacao automatizada por item com metricas de contexto e resposta;
- `scripts_geracao/`: pipeline reproduzivel para gerar, validar, corrigir e exportar o dataset.

## Objetivo

O projeto foi desenhado para avaliar sistemas de QA em Geociencias em cenarios nos quais a resposta exige combinar evidencias, por exemplo:

- bacia sedimentar -> unidade estratigrafica -> litologia;
- rocha geradora -> migracao -> reservatorio -> selo;
- facies -> ambiente deposicional -> propriedade petrofisica;
- estrutura/falha -> compartimentacao -> fluido ou regime de pressao;
- idade relativa -> posicao estratigrafica -> evolucao geologica.

Em outras palavras, o dataset serve melhor para testar recuperacao contextual, fidelidade a fonte e capacidade de inferencia geocientifica do que para perguntas puramente factuais de uma unica sentenca.

## Estrutura do repositorio

```text
.
├── README.md
├── dataset_full.json
├── sources.csv
├── audit_questions_vs_sources.csv
├── ragas_evaluation.csv
└── scripts_geracao/
    ├── README_GENERATION_SCRIPTS.md
    ├── requirements-generation.txt
    ├── run_pipeline_example.sh
    ├── config/
    │   └── relation_types.json
    ├── examples/
    │   └── sources.example.csv
    ├── prompts/
    │   ├── system_prompt_geoinfer_pt.md
    │   └── user_prompt_template.md
    └── scripts/
        ├── 01_fetch_sources.py
        ├── 02_extract_candidate_passages.py
        ├── 03_build_generation_prompts.py
        ├── 04_generate_with_llm.py
        ├── 05_merge_and_validate_dataset.py
        ├── 06_apply_item_corrections.py
        ├── 07_export_csv.py
        └── 08_build_source_audit.py
```

## Artefatos principais

### `dataset_full.json`

Arquivo principal do projeto. Cada item contem:

```json
{
  "id": 1,
  "question": "Pergunta em portugues.",
  "context": [
    [
      "Titulo da fonte",
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

| Campo | Descricao |
|---|---|
| `id` | Identificador numerico do item. |
| `question` | Pergunta em portugues, com uma unica intencao e uma unica interrogacao. |
| `context` | Lista de blocos multicontexto. Cada bloco contem o titulo da fonte e uma lista de trechos literais. |
| `expected_answer` | Resposta esperada, fiel ao contexto, mas nao necessariamente uma copia literal. |
| `tipo_inferencia` | Rotulo analitico do tipo principal de inferencia exigida. |
| `source` | Lista de URLs alinhada aos blocos de contexto. |

### `sources.csv`

Catalogo das fontes usadas na construcao do dataset, com colunas:

```csv
id,fonte,link
```

### `audit_questions_vs_sources.csv`

Arquivo de rastreabilidade para auditoria. Ele liga questoes e trechos de contexto as respectivas fontes, permitindo revisar de onde cada evidencia textual foi extraida.

### `ragas_evaluation.csv`

Arquivo com uma rodada de avaliacao automatizada por item. Hoje ele registra, entre outras, as metricas:

- `context_precision_score`
- `contextual_relevancy_score`
- `contextual_recall_score`
- `faithfulness_score`
- `answer_relevance_score`

## Como o dataset foi construido

O fluxo do projeto, como implementado em `scripts_geracao/scripts/`, e o seguinte:

1. `01_fetch_sources.py`  
   Baixa cada URL de `sources.csv` e tenta extrair texto bruto de HTML ou PDF.

2. `02_extract_candidate_passages.py`  
   Divide os textos em paragrafos e seleciona passagens candidatas usando heuristicas e palavras-chave geocientificas.

3. `03_build_generation_prompts.py`  
   Agrupa evidencias em pequenos conjuntos multicontexto e monta prompts para geracao de itens por LLM.

4. `04_generate_with_llm.py`  
   Envia os prompts para um endpoint compativel com Chat Completions e salva a resposta bruta.

5. `05_merge_and_validate_dataset.py`  
   Consolida os itens gerados, renumera IDs, valida schema, formato de `context`, termos proibidos e aderencia literal ao banco de evidencias.

6. `06_apply_item_corrections.py`  
   Aplica correcoes manuais por ID quando a geracao automatica precisa de ajuste editorial.

7. `07_export_csv.py`  
   Exporta o dataset final para CSV com `id`, `question`, `context` e `expected_answer`.

8. `08_build_source_audit.py`  
   Gera uma tabela de auditoria item-contexto-fonte para rastreabilidade.

## Premissas metodologicas

O projeto segue algumas regras centrais:

- usar somente fontes em portugues;
- manter os trechos do `context` de forma literal, sem parafrasear;
- evitar perguntas metalinguisticas sobre RAG, GraphRAG, ontologias ou o proprio dataset;
- exigir uma unica intencao por pergunta;
- produzir respostas esperadas sustentadas pelo contexto, mesmo quando inferenciais;
- manter `tipo_inferencia` como rotulo de analise, nao como dica explicita dentro da pergunta ou da resposta;
- revisar manualmente os itens apos a geracao automatica.

A taxonomia usada na construcao dos prompts esta em `scripts_geracao/config/relation_types.json`. Como o dataset foi refinado iterativamente, a versao final pode conter rotulos adicionais ou consolidados em relacao a essa taxonomia-base.

## Reproduzindo a pipeline

Os artefatos intermediarios nao estao versionados na raiz. Se quiser reproduzir a geracao, um fluxo pratico a partir da raiz do projeto e:

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

## Validacoes aplicadas na consolidacao

O script `05_merge_and_validate_dataset.py` verifica, entre outros pontos:

- presenca dos campos obrigatorios;
- estrutura multicontexto de `context`;
- existencia de exatamente uma interrogacao em `question`;
- ausencia de termos proibidos como `rag`, `graphrag`, `ontologia` e expressoes como `relacao espacial`;
- presenca literal dos paragrafos de contexto no banco de evidencias;
- existencia de lista nao vazia em `source`.

## Como usar o dataset

Para avaliacao de sistemas de QA, a pratica mais consistente e:

1. fornecer ao modelo apenas `question` e `context`;
2. manter `tipo_inferencia` fora da entrada do modelo e usar esse campo apenas para analise posterior;
3. usar `expected_answer` como referencia de avaliacao, nao como contexto adicional;
4. consultar `audit_questions_vs_sources.csv` quando for necessario auditar a origem de um trecho;
5. usar `ragas_evaluation.csv` como apoio comparativo, nao como substituto de revisao humana.

## Limitacoes

- Extracao automatica de HTML e PDF pode falhar, especialmente em paginas dinamicas.
- A qualidade final depende da geracao do LLM e da revisao manual posterior.
- Fontes externas podem mudar, sair do ar ou alterar o texto ao longo do tempo.
- O projeto redistribui trechos literais de fontes externas; antes de publicar ou reaproveitar o dataset, revise licencas e termos de uso.
- Alguns arquivos auxiliares ainda refletem o nome legado `GeoInfer-PT` e exemplos antigos de caminho; use este README como referencia atual da organizacao do repositorio.

## Citacao sugerida

```text
PetroQA-Brasil is a Portuguese geoscience question-answering dataset focused on source-grounded relational inference over geological and petroleum-geology texts.

Authors: Tiago Rios da Rocha, João Netto, Karin Becker
Institution: Universidade Federal do Rio Grande do Sul
Project: OntoKG
```
