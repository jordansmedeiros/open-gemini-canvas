# Modelos de Dados no Frontend

<cite>
**Arquivos Referenciados neste Documento**  
- [stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx)
- [utils.ts](file://lib/utils.ts)
</cite>

## Sumário
1. [Introdução](#introdução)
2. [Interface `StackAnalysis`](#interface-stackanalysis)
3. [Estrutura dos Campos](#estrutura-dos-campos)
4. [Uso no Componente `StackAnalysisCards`](#uso-no-componente-stackanalysiscards)
5. [Exemplo Prático de Dados](#exemplo-prático-de-dados)
6. [Tratamento de Dados e Fallback](#tratamento-de-dados-e-fallback)
7. [Boas Práticas para Extensão](#boas-práticas-para-extensão)
8. [Funções Auxiliares](#funções-auxiliares)
9. [Validação de Tipo e Tratamento de Erros](#validação-de-tipo-e-tratamento-de-erros)

## Introdução

Este documento detalha o modelo de dados `StackAnalysis`, uma interface TypeScript central no frontend do projeto `open-gemini-canvas`. Essa interface é utilizada para estruturar e exibir a análise de stacks tecnológicos de repositórios GitHub. O componente `StackAnalysisCards` é responsável por renderizar esses dados de forma clara e organizada, utilizando uma abordagem de renderização condicional baseada na presença de campos específicos. A interface foi projetada para ser flexível, permitindo a inclusão de campos opcionais e genéricos, o que a torna adaptável a diferentes tipos de projetos e tecnologias.

## Interface `StackAnalysis`

A interface `StackAnalysis` é a estrutura de dados principal para representar a análise de um stack tecnológico. Ela é definida em `stack-analysis-cards.tsx` e serve como um contrato entre o backend (que gera a análise) e o frontend (que a exibe). A interface é projetada para ser extensível, utilizando campos opcionais (`?`) e uma *index signature* (`[key: string]: unknown`) para acomodar dados que podem não ser previstos inicialmente.

**Section sources**
- [stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L31-L42)

## Estrutura dos Campos

A interface `StackAnalysis` é composta por vários campos, cada um representando uma categoria diferente da análise do stack.

### Campos Principais

- **`purpose`**: Uma string opcional que descreve o propósito geral do repositório analisado.
- **`frontend`**: Um objeto do tipo `StackSection` que contém detalhes sobre a tecnologia frontend.
- **`backend`**: Um objeto do tipo `StackSection` que contém detalhes sobre a tecnologia backend.
- **`database`**: Um objeto com campos `type` (tipo de banco de dados) e `notes` (notas adicionais).
- **`infrastructure`**: Um objeto com informações sobre hospedagem (`hosting_frontend`, `hosting_backend`) e dependências externas (`dependencies`).
- **`ci_cd`**: Um objeto com um campo `setup` que descreve a configuração de CI/CD.
- **`key_root_files`**: Um array de objetos `RootFileEntry`, cada um contendo um nome de arquivo e sua descrição.
- **`how_to_run`**: Um objeto com um `summary` (resumo) e um array de `steps` (passos) para executar o projeto.
- **`risks_notes`**: Um array de objetos `RiskNote`, cada um com uma área de risco e uma nota descritiva.

### Estruturas Aninhadas

- **`StackSection`**: Uma interface genérica para seções de stack (frontend/backend), contendo campos como `language`, `framework`, `package_manager`, `styling`, `dependency_manager`, `architecture` e `key_libraries`. A *index signature* `[key: string]: unknown` permite a inclusão de campos adicionais não especificados.
- **`RootFileEntry`**: Define a estrutura de um arquivo raiz com `file` (nome) e `description` (descrição).
- **`RiskNote`**: Define a estrutura de uma nota de risco com `area` (área) e `note` (nota).

### Tipos Opcionais e Index Signatures

Todos os campos da interface `StackAnalysis` são opcionais, indicados pelo sufixo `?`. Isso permite que o objeto seja parcialmente preenchido, o que é crucial para lidar com repositórios que podem não ter todas as categorias de tecnologia. A *index signature* `[key: string]: unknown` é um recurso poderoso do TypeScript que permite que a interface aceite qualquer propriedade adicional, cujo valor pode ser de qualquer tipo. Isso garante que a interface seja futuramente compatível com novos campos sem necessidade de alteração.

**Section sources**
- [stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L12-L30)

## Uso no Componente `StackAnalysisCards`

O componente `StackAnalysisCards` é responsável por renderizar os dados da interface `StackAnalysis` em uma UI amigável. Ele aceita uma prop `analysis` que pode ser um objeto `StackAnalysis` ou uma string JSON contendo esse objeto.

### Renderização Condicional

O componente utiliza extensivamente a renderização condicional. Cada seção (como "Frontend", "Backend") só é renderizada se o campo correspondente no objeto `parsed` estiver presente e não for `null` ou `undefined`. Isso é feito com expressões JSX como `{parsed.frontend && (...)}`.

### Mapeamento de Dados

O mapeamento de dados é feito principalmente pela função `DefinitionList`. Esta função recebe um objeto `data` (por exemplo, `parsed.frontend`) e o transforma em uma lista de definições (`<dl>`). A função `humanize` é usada para converter nomes de campos em formato de exibição (por exemplo, `package_manager` se torna `Package Manager`). O parâmetro `order` permite definir uma ordem específica para a exibição dos campos.

```mermaid
flowchart TD
A["Entrada: analysis (objeto ou string)"] --> B{"É uma string?"}
B --> |Sim| C[Tentar JSON.parse()]
B --> |Não| D[Usar objeto diretamente]
C --> E{"Parsing bem-sucedido?"}
E --> |Sim| F[Objeto parsed]
E --> |Não| G[Objeto parsed = undefined]
D --> F
F --> H{"Objeto vazio ou indefinido?"}
H --> |Sim| I[Exibir mensagem de 'No analysis available']
H --> |Não| J[Renderizar seções baseadas nos campos presentes]
```

**Diagram sources**
- [stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L118-L256)

**Section sources**
- [stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L118-L256)

## Exemplo Prático de Dados

Um objeto `StackAnalysis` preenchido com dados reais de um repositório Next.js com PostgreSQL poderia ser:

```json
{
  "purpose": "Aplicação web de blog com gerenciamento de conteúdo.",
  "frontend": {
    "language": "TypeScript",
    "framework": "Next.js",
    "package_manager": "pnpm",
    "styling": "Tailwind CSS",
    "key_libraries": ["react", "react-dom", "next-themes"]
  },
  "backend": {
    "language": "TypeScript",
    "framework": "Next.js API Routes",
    "dependency_manager": "pnpm"
  },
  "database": {
    "type": "PostgreSQL",
    "notes": "Usado com Prisma ORM."
  },
  "infrastructure": {
    "hosting_frontend": "Vercel",
    "hosting_backend": "Vercel",
    "dependencies": ["Prisma", "PostgreSQL"]
  },
  "ci_cd": {
    "setup": "GitHub Actions"
  },
  "key_root_files": [
    { "file": "next.config.mjs", "description": "Configuração principal do Next.js." },
    { "file": "tailwind.config.ts", "description": "Configuração do Tailwind CSS." }
  ],
  "how_to_run": {
    "summary": "Instale as dependências e inicie o servidor de desenvolvimento.",
    "steps": [
      "Execute 'pnpm install' para instalar as dependências.",
      "Execute 'pnpm dev' para iniciar o servidor de desenvolvimento."
    ]
  },
  "risks_notes": [
    { "area": "Dependência", "note": "Alta dependência de serviços da Vercel." },
    { "area": "Segurança", "note": "Verificar configurações de autenticação." }
  ]
}
```

## Tratamento de Dados e Fallback

O componente `StackAnalysisCards` implementa uma lógica robusta de tratamento de dados para garantir uma experiência de usuário suave mesmo com entradas inválidas.

### Parsing de JSON

O componente verifica o tipo da prop `analysis`. Se for uma string, ele tenta fazer o *parsing* com `JSON.parse()`. Se o *parsing* falhar (por exemplo, devido a uma string JSON malformada), o bloco `catch` define `parsed` como `undefined`, evitando quebrar a aplicação.

### Lógica de Fallback

Se o objeto `parsed` for `undefined`, `null` ou um objeto vazio, o componente renderiza uma mensagem amigável: "No analysis available yet. Ask the agent to analyze a repository." Isso fornece um feedback claro ao usuário em vez de exibir uma tela em branco.

**Section sources**
- [stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L125-L145)

## Boas Práticas para Extensão

Para estender a interface `StackAnalysis` com novos campos, siga estas práticas:

1.  **Use o campo opcional**: Sempre declare novos campos como opcionais (com `?`) para manter a compatibilidade com dados existentes.
2.  **Considere a *index signature***: Se o novo campo for muito específico e não for parte do core da análise, considere se ele pode ser representado dentro da *index signature* existente.
3.  **Atualize o backend**: Qualquer novo campo adicionado ao frontend deve ser suportado pelo backend para que os dados sejam gerados corretamente.
4.  **Atualize a documentação**: Documente o novo campo e seu propósito para outros desenvolvedores.

## Funções Auxiliares

Duas funções auxiliares são definidas no mesmo arquivo e são cruciais para o funcionamento do componente.

### `isNonEmptyArray`

Essa função de tipo (type guard) verifica se um valor é um array e se não está vazio. Ela é usada para renderizar condicionalmente seções que dependem de arrays, como `key_root_files` e `risks_notes`. O uso de um *type guard* (`arr is T[]`) permite que o TypeScript saiba que, dentro do bloco `if`, o valor é definitivamente um array não vazio, permitindo o uso seguro de operações de array.

### `humanize`

Esta função converte uma string em formato de código (como `package_manager`) em um formato legível para humanos (como `Package Manager`). Ela faz isso substituindo underscores por espaços e capitalizando a primeira letra de cada palavra. Essa função é usada pela `DefinitionList` para melhorar a experiência do usuário.

**Section sources**
- [stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L44-L55)

## Validação de Tipo e Tratamento de Erros

A validação de tipo em tempo de execução é implícita no uso do TypeScript e na estrutura do componente.

- **Validação de Tipo**: O TypeScript garante que, dentro do escopo do componente, o objeto `parsed` siga a estrutura da interface `StackAnalysis` após o *parsing*. No entanto, como o dado vem de uma fonte externa (string JSON), a validação é limitada.
- **Tratamento de Erros de Parsing**: O tratamento de erros é feito de forma elegante com o bloco `try...catch`. Qualquer erro de *parsing* resulta em `parsed` sendo `undefined`, o que aciona a mensagem de fallback. Isso evita que erros de dados causem falhas na UI.

Para uma validação mais rigorosa, seria necessário um esquema de validação como Zod ou Yup, mas o atual mecanismo de fallback já fornece uma boa camada de segurança contra entradas inválidas.