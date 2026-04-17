from flask import json


prompt_summarize = """
Crie um material didático curto em Markdown com base no trecho.

Estrutura:
# Título

## Conceitos
- Explique de forma simples e direta.

## Exemplo
- Dê 1 exemplo claro (com código se necessário).

## Aplicação
- Cite 1 uso prático.

Regras:
- Seja breve e objetivo
- Máx 400 palavras
- Evite explicações longas
- Use Markdown

Trecho:
"""

data_questions = {
    "questao1": {
        "pergunta": "",
        "alternativas": ["A","B","C","D"],
        "dica": "",
        "resposta_correta": "",
        "justificativa": "",
        "Dificuldade": ""
    }
}

prompt_questions = f"""
Gere 1 questão de múltipla escolha com base no trecho.
Retorne somente JSON válido.

Formato exato (não altere chaves):
{json.dumps(data_questions, ensure_ascii=False)}

Regras:
- Não adicione nem remova campos
- Não use aspas duplas dentro dos textos
- Use apenas texto simples
- Sem quebras de linha
- dificuldade deve ser Fácil, Média ou Difícil
- resposta_correta deve ser igual a uma alternativa
- Máx 150 caracteres por campo
- Sem texto fora do JSON

Trecho:
"""