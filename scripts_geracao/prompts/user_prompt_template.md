Gere {n_items} itens de Question Answering geocientífico em português a partir dos contextos abaixo.

Tipos de inferência permitidos:
{relation_types}

Contextos disponíveis:
{contexts}

Schema obrigatório para cada item:
{
  "id": null,
  "question": "pergunta em português",
  "context": [
    [
      "Título da fonte",
      [
        "trecho literal da fonte",
        "outro trecho literal, se necessário"
      ]
    ]
  ],
  "expected_answer": "resposta esperada inferencial e fiel aos trechos",
  "tipo_inferencia": "um dos tipos permitidos",
  "source": ["link da fonte"]
}

Condições:
- Use somente trechos presentes nos contextos disponíveis.
- Não adicione títulos no lugar de texto.
- Não use texto de ontologias como contexto.
- Não use fontes em inglês.
- Evite perguntas de comparação com duas perguntas internas.
- A resposta não deve ser uma cópia literal de uma frase do contexto.
- A resposta deve combinar entidades, relações ou propriedades geológicas presentes nos trechos.
- Retorne uma lista JSON.
