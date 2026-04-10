prompt_summarize = """
Crie um material didático em Markdown com base no trecho.

Estrutura:
# Título claro
Breve introdução explicando o tema e sua importância.

## Conceitos Fundamentais
- Liste e explique os conceitos principais de forma simples.

## Exemplos Práticos
- Dê exemplos claros.
- Se envolver programação, inclua código comentado e explique.
- Caso contrário use analogias, tabelas ou explicações passo a passo.

## Aplicações no Mundo Real
- Mostre onde o conceito é usado na prática.

Regras:
- Texto claro e educativo.
- Use Markdown (#, ##, listas).
- Complete lacunas se necessário.
- Não mencione videoaula.

Trecho:
"""

prompt_questions = """
Gere 5 questões de múltipla escolha com base no trecho.
Retorne somente JSON válido.

Formato:
{
"questão1":{"pergunta":"","alternativas":["A","B","C","D"],"dica":"","resposta_correta":"","justificativa":"","Dificuldade":"Fácil"},
"questão2":{"pergunta":"","alternativas":["A","B","C","D"],"dica":"","resposta_correta":"","justificativa":"","Dificuldade":"Fácil"},
"questão3":{"pergunta":"","alternativas":["A","B","C","D"],"dica":"","resposta_correta":"","justificativa":"","Dificuldade":"Médio"},
"questão4":{"pergunta":"","alternativas":["A","B","C","D"],"dica":"","resposta_correta":"","justificativa":"","Dificuldade":"Médio"},
"questão5":{"pergunta":"","alternativas":["A","B","C","D"],"dica":"","resposta_correta":"","justificativa":"","Dificuldade":"Difícil"}
}

Regras:
- Apenas uma alternativa correta
- resposta_correta deve ser igual a uma alternativa
- Máx 150 caracteres por campo
- Sem quebras de linha
- Sem texto fora do JSON

Trecho:
"""