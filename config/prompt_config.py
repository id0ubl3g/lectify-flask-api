prompt_ptBR = '''Leia o trecho fornecido e crie um resumo didático em formato Markdown, transformando um recorte de videoaula em uma explicação clara e bem estruturada.

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

prompt_enUS = '''Read the provided excerpt and create a didactic summary in Markdown format, transforming a video lesson excerpt into a clear and well-structured explanation.

### Guidelines:
1. **Title:** Create a clear and direct title that reflects the main content.
2. **Introduction:** Provide an initial paragraph that simply explains the context of the topic.
3. **Content Structure:** Organize the explanation into clear sections, such as:
    - *"Fundamental Concepts"*: Present the basic concepts in a simple and objective manner.
    - *"Practical Examples"*: Provide practical examples or illustrations to help understand the discussed topic. If the content involves programming, include code snippets with an explanation of what each part of the code does. Use the following format to highlight the code:
    
    **Code:**
    ```python
    def add(a, b):  # Defines a function that adds two numbers
        return a + b  # Returns the sum of the two numbers
    ```

    - *"Applications"*: Explain how these concepts can be applied in real-world scenarios.

### Formatting Requirements:
- Use Markdown to structure the text in a readable format:
    - Titles and subtitles: `#`, `##`, `###`
    - Lists: `-`, `1.`
    - Code blocks: Use the standard Markdown syntax with three backticks (```) to highlight code. Pay attention to **indentation and spacing** inside the code blocks to ensure clarity and readability.

**Important:** If the provided content does not include specific code or examples, create examples and explanations based on the described concepts. The AI must always provide a complete, well-organized, and structured explanation without mentioning the lack of material or code. The focus is on delivering a clear and didactic explanation of the topic, detailing the concepts in an accessible way.
    
### Excerpt to Work With:
'''

prompt_questions = '''Leia o trecho fornecido e crie 5 questões de múltipla escolha em formato JSON, com base no conteúdo. As questões devem ser criadas no mesmo idioma do texto fornecido. Se o texto estiver em inglês, as perguntas devem ser em inglês.

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

### Importante:
1. Forneça apenas as 5 questões no formato JSON especificado. Não adicione explicações extras ou formatação adicional.
2. Se o texto fornecido estiver em inglês, as perguntas devem ser geradas em inglês.
3. Certifique-se de não incluir a marcação de código (como ```json```) ao formatar as questões em JSON.

### Trecho para trabalhar:
'''