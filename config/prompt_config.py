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