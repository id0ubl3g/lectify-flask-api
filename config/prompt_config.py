prompt = '''Leia o trecho fornecido e crie um resumo didático em formato Markdown, transformando um recorte de videoaula em uma explicação clara e bem estruturada.

### Diretrizes:
1. **Título:** Crie um título claro e direto que reflita o conteúdo principal.
2. **Introdução:** Forneça um parágrafo inicial que explique de forma simples o contexto do tema.
3. **Estrutura do Conteúdo:** Organize a explicação em seções claras, como:
    - *"Conceitos Fundamentais"*: Apresente os conceitos básicos de forma simples e objetiva.
    - *"Exemplos Práticos"*: Apresente exemplos práticos ou ilustrações que ajudem a entender o que foi abordado. Caso o conteúdo envolva programação, inclua trechos de código com a explicação do que cada parte do código faz. Use o seguinte formato para destacar o código:
    
    **Código:**
    ```python
    def somar(a, b):  # Definindo a função que soma dois números
        return a + b  # Retorna a soma dos dois números
    ```

    - *"Aplicações"*: Explique como os conceitos podem ser aplicados no mundo real.

### Requisitos de Formatação:
- Use Markdown para estruturar o texto de forma legível:
    - Títulos e subtítulos: `#`, `##`, `###`
    - Listas: `-`, `1.`
    - Blocos de código: Use a sintaxe padrão de Markdown com 3 crases (```) para destacar código. Preste atenção na **identação e no espaçamento** dentro dos blocos de código para garantir que não fique embolado e seja facilmente legível.

**Importante:** Se o conteúdo fornecido não incluir código ou exemplos específicos, crie os exemplos e explicações de acordo com os conceitos descritos. A IA deve sempre fornecer um conteúdo completo, organizado e bem estruturado, sem mencionar a falta de material ou código. O foco é fornecer uma explicação didática, baseada no tema, e detalhar os conceitos de forma clara.
    
### Trecho para trabalhar:
'''

prompt_questions = '''Leia o trecho fornecido e crie 5 questões de múltipla escolha em formato JSON, com base no conteúdo. Cada questão deve ser clara, objetiva e ajudar a avaliar o entendimento do tema apresentado.

### Exemplo Formato JSON:
As questões devem ser organizadas em um objeto JSON com 5 propriedades, uma para cada questão. Abaixo está um exemplo de como o formato JSON deve ser:

{
    "questão1": {
        "pergunta": "Texto da pergunta.",
        "alternativas": [
            "Alternativa A",
            "Alternativa B",
            "Alternativa C",
            "Alternativa D"
        ],
        "dica": "Dica para ajudar na resposta.",
        "resposta_correta": "Alternativa correta",
        "justificativa": "Explicação sobre a resposta correta."
    },
    "questão2": { ... },
    "questão3": { ... },
    "questão4": { ... },
    "questão5": { ... }
}

**Importante:** Forneça apenas as 5 questões no formato JSON especificado. Não adicione explicações extras ou formatação adicional. Apenas crie o JSON com as perguntas, alternativas, respostas corretas e justificativas, conforme o exemplo fornecido. Certifique-se de não incluir a marcação de código (como ```json```) ao formatar as questões em JSON.

### Trecho para trabalhar:
'''