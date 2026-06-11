# Scripts de geração do GeoInfer-PT

Este pacote contém uma pipeline reproduzível para gerar um dataset de Question Answering geocientífico em português, com perguntas inferenciais baseadas em relações entre entidades geológicas.

A ideia é partir de um `sources.csv` contendo fontes públicas em português, extrair trechos originais dos textos, selecionar evidências relevantes e montar prompts para um LLM gerar questões cuja resposta esperada dependa de inferência relacional, e não de simples extração literal.

> Observação importante: a versão final do GeoInfer-PT foi construída de forma iterativa, com revisão manual e correções de consistência. Estes scripts organizam e reproduzem a metodologia de geração, validação e exportação, mas a etapa de geração por LLM ainda deve ser revisada manualmente antes da publicação.

---

## Estrutura esperada

```text
project/
├── sources.csv
├── data/
│   ├── raw_sources/
│   ├── evidence_bank.jsonl
│   ├── prompts.jsonl
│   ├── generations.jsonl
│   └── dataset_generated.json
├── scripts/
│   ├── 01_fetch_sources.py
│   ├── 02_extract_candidate_passages.py
│   ├── 03_build_generation_prompts.py
│   ├── 04_generate_with_llm.py
│   ├── 05_merge_and_validate_dataset.py
│   ├── 06_apply_item_corrections.py
│   └── 07_export_csv.py
├── prompts/
│   ├── system_prompt_geoinfer_pt.md
│   └── user_prompt_template.md
├── config/
│   └── relation_types.json
└── patches/
    └── corrections_113_124_144.json
```

---

## Formato de `sources.csv`

O arquivo deve conter, no mínimo, as colunas:

```csv
id,fonte,link
1,Nome da fonte,https://...
```

Exemplo:

```csv
id,fonte,link
1,Pré-sal: mergulhe nessa jornada ultraprofunda | Petrobras,https://petrobras.com.br/pre-sal
2,Petróleo | SGB,https://www.sgb.gov.br/petroleo
```

---

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-generation.txt
```

---

## Execução completa

### 1. Baixar e extrair textos das fontes

```bash
python scripts/01_fetch_sources.py \
  --sources sources.csv \
  --out-dir data/raw_sources
```

O script tenta extrair texto de HTML e PDF. Quando a extração automática falhar, salve manualmente o texto original da fonte em:

```text
data/raw_sources/source_<id>.txt
```

### 2. Extrair passagens candidatas

```bash
python scripts/02_extract_candidate_passages.py \
  --raw-dir data/raw_sources \
  --sources sources.csv \
  --out data/evidence_bank.jsonl
```

Esse script seleciona parágrafos candidatos contendo conceitos como bacia, formação, litologia, fácies, reservatório, selo, falha, estratigrafia, fósseis, turbidito, carbonato, evaporito e propriedades petrofísicas.

### 3. Construir prompts de geração

```bash
python scripts/03_build_generation_prompts.py \
  --evidence data/evidence_bank.jsonl \
  --relations config/relation_types.json \
  --system-prompt prompts/system_prompt_geoinfer_pt.md \
  --user-template prompts/user_prompt_template.md \
  --out data/prompts.jsonl \
  --target-items 150
```

Os prompts pedem ao LLM que gere itens no schema:

```json
{
  "id": null,
  "question": "...",
  "context": [["Título", ["trecho literal 1", "trecho literal 2"]]],
  "expected_answer": "...",
  "tipo_inferencia": "...",
  "source": ["https://..."]
}
```

### 4. Gerar com LLM

Configure as variáveis de ambiente:

```bash
export LLM_API_URL="https://SEU-ENDPOINT/chat/completions"
export LLM_API_KEY="SUA_CHAVE"
export LLM_MODEL="seu-modelo"
```

Depois execute:

```bash
python scripts/04_generate_with_llm.py \
  --prompts data/prompts.jsonl \
  --out data/generations.jsonl
```

Se você não quiser chamar API, use apenas `data/prompts.jsonl` como lote de prompts para gerar manualmente em outra ferramenta.

### 5. Consolidar e validar

```bash
python scripts/05_merge_and_validate_dataset.py \
  --generations data/generations.jsonl \
  --evidence data/evidence_bank.jsonl \
  --out data/dataset_generated.json \
  --max-items 150
```

Validações realizadas:

- IDs únicos.
- Campos obrigatórios.
- `context` no formato multicontexto.
- Textos de contexto devem aparecer literalmente no banco de evidências.
- Perguntas sem menção a RAG/GraphRAG.
- `question` e `expected_answer` sem marcações explícitas como “relação espacial”.
- Presença de `tipo_inferencia`.
- Uma única interrogação por pergunta.

### 6. Aplicar correções manuais

```bash
python scripts/06_apply_item_corrections.py \
  --dataset data/dataset_generated.json \
  --patch patches/corrections_113_124_144.json \
  --out data/dataset_generated_corrected.json
```

### 7. Exportar CSV

```bash
python scripts/07_export_csv.py \
  --dataset data/dataset_generated_corrected.json \
  --out data/geoinfer_pt.csv
```

O CSV final contém:

```csv
id,question,context,expected_answer
```

O campo `context` concatena somente os parágrafos, sem títulos das fontes.

---

## Critérios metodológicos usados

1. **Somente textos em português**  
   As fontes devem ser páginas, PDFs ou documentos em português.

2. **Contextos literais**  
   O campo `context` deve conter trechos retirados literalmente das fontes, sem paráfrase.

3. **Perguntas não metalinguísticas**  
   As perguntas não devem mencionar RAG, GraphRAG, ontologia, dataset ou avaliação.

4. **Inferência relacional**  
   A resposta esperada deve exigir combinação entre entidades e relações geológicas, como:
   - bacia → unidade estratigráfica → litologia;
   - rocha geradora → migração → reservatório → selo;
   - formação → fácies → ambiente deposicional;
   - falha/estrutura → compartimentação → fluido/pressão;
   - fóssil/estratigrafia → idade relativa;
   - propriedade petrofísica → função de reservatório.

5. **Relação registrada fora da pergunta**  
   O tipo de inferência deve ficar apenas no campo `tipo_inferencia`, nunca explícito em `question` ou `expected_answer`.

6. **Revisão manual obrigatória**  
   Mesmo com validações automáticas, cada item deve ser auditado quanto a:
   - suficiência do contexto;
   - fidelidade da resposta esperada;
   - ausência de conhecimento externo não sustentado;
   - clareza da pergunta;
   - não duplicação de intenções.

---

## Limitações

- A extração automática de PDFs e páginas HTML pode falhar em sites dinâmicos.
- O script de geração depende da qualidade do LLM utilizado.
- O controle de fidelidade exige revisão humana, principalmente quando a resposta esperada faz inferência entre vários contextos.
- A validação de “trecho literal” verifica correspondência textual com o banco de evidências, mas não garante que o trecho ainda esteja disponível online.

---

## Sugestão de citação do dataset

```bibtex
@dataset{geoinferpt2026,
  title = {GeoInfer-PT: A Portuguese Geoscience Question Answering Dataset for Ontology-Guided Relational Inference},
  author = {Rios da Rocha, Tiago},
  year = {2026},
  language = {Portuguese},
  note = {Dataset for inferential geoscience question answering over geological documents}
}
```
