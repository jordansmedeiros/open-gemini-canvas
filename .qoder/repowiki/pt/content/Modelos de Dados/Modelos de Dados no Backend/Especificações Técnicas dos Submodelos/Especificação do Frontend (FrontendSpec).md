# Especificação do Frontend (FrontendSpec)

<cite>
**Arquivos Referenciados neste Documento**  
- [stack_agent.py](file://agent/stack_agent.py)
- [package.json](file://package.json)
- [next.config.mjs](file://next.config.mjs)
- [tsconfig.json](file://tsconfig.json)
</cite>

## Sumário
1. [Introdução](#introdução)
2. [Estrutura da Classe FrontendSpec](#estrutura-da-classe-frontendspec)
3. [Campos da Especificação](#campos-da-especificação)
4. [População da Especificação](#população-da-especificação)
5. [Exemplo de Instanciação](#exemplo-de-instanciação)

## Introdução

A classe `FrontendSpec` é uma componente fundamental do sistema de análise de stack tecnológico, definida dentro do módulo `StructuredStackAnalysis`. Seu propósito principal é modelar e estruturar as tecnologias, ferramentas e configurações relacionadas à camada de interface do usuário (frontend) de uma aplicação. Essa classe permite uma representação clara, consistente e opcionalmente detalhada das escolhas tecnológicas feitas no frontend, facilitando a documentação, análise e comunicação sobre a arquitetura do projeto. Ela é utilizada como um campo opcional dentro da classe `StructuredStackAnalysis`, que agrega informações sobre todas as camadas do stack (frontend, backend, banco de dados, infraestrutura, etc.).

## Estrutura da Classe FrontendSpec

A classe `FrontendSpec` é definida como um modelo Pydantic (`BaseModel`), o que garante validação de tipos e estrutura dos dados. Todos os seus campos são opcionais, refletindo a natureza flexível e adaptável das stacks de frontend, onde nem todas as tecnologias ou configurações podem estar presentes ou serem relevantes para uma análise específica. A utilização de `Optional[str]` para campos de texto simples e `List[str]` para coleções permite uma grande flexibilidade na descrição de stacks variados, desde projetos simples até aplicações complexas com múltiplas bibliotecas.

**Section sources**
- [stack_agent.py](file://agent/stack_agent.py#L39-L44)

## Campos da Especificação

A classe `FrontendSpec` é composta pelos seguintes campos, cada um descrevendo um aspecto específico da tecnologia frontend:

- **`framework`**: Especifica o framework principal utilizado para construir a interface do usuário (por exemplo, React, Vue, Angular). Este campo é do tipo `Optional[str]`, indicando que a análise pode ser feita mesmo na ausência de um framework principal identificado.
- **`language`**: Define a linguagem de programação principal do frontend (por exemplo, JavaScript, TypeScript). Também é do tipo `Optional[str]`.
- **`package_manager`**: Indica o gerenciador de pacotes utilizado (por exemplo, npm, pnpm, yarn). Este campo é crucial para entender o ecossistema de dependências do projeto e é do tipo `Optional[str]`.
- **`styling`**: Descreve a tecnologia ou metodologia utilizada para estilização (por exemplo, Tailwind CSS, CSS Modules, Styled Components). Este campo é do tipo `Optional[str]`.
- **`key_libraries`**: Uma lista (`List[str]`) de bibliotecas de interface de usuário ou utilitários principais que complementam o framework principal (por exemplo, Radix UI, Lucide React, Recharts). O uso de uma lista permite capturar múltiplas dependências relevantes.

Todos os campos são opcionais, permitindo que a especificação seja populada com base no que pode ser inferido da análise do código, sem exigir que todos os aspectos sejam identificados.

**Section sources**
- [stack_agent.py](file://agent/stack_agent.py#L39-L44)

## População da Especificação

A instância de `FrontendSpec` é populada automaticamente pela análise do repositório, principalmente através da leitura e interpretação de arquivos de configuração e manifesto. O processo de análise examina arquivos-chave como `package.json` para identificar dependências e scripts, `next.config.mjs` para inferir o framework e configurações específicas, e `tsconfig.json` para determinar a linguagem de programação. Por exemplo, a presença de `next` como dependência no `package.json` indica o uso do Next.js, enquanto as dependências `tailwindcss` e `tailwind-merge` apontam para o uso do Tailwind CSS como sistema de estilização. O gerenciador de pacotes é inferido do arquivo de bloqueio (`pnpm-lock.yaml` no caso deste projeto). Essa análise automatizada permite uma coleta de dados precisa e eficiente sobre a stack frontend.

**Section sources**
- [package.json](file://package.json#L1-L86)
- [next.config.mjs](file://next.config.mjs#L1-L14)
- [tsconfig.json](file://tsconfig.json#L1-L27)

## Exemplo de Instanciação

Com base na análise do repositório, um exemplo de como a classe `FrontendSpec` seria instanciada para um projeto que utiliza React com TypeScript e Tailwind CSS é o seguinte:

```python
frontend_spec = FrontendSpec(
    framework="Next.js",
    language="TypeScript",
    package_manager="pnpm",
    styling="Tailwind CSS",
    key_libraries=["Radix UI", "Lucide React", "Recharts", "Sonner"]
)
```

Esta instanciação reflete com precisão as tecnologias identificadas: o framework Next.js (inferido pela configuração e dependências), a linguagem TypeScript (configurada no `tsconfig.json`), o gerenciador de pacotes pnpm (indicado pelo arquivo `pnpm-lock.yaml`), o sistema de estilização Tailwind CSS (presente nas dependências) e uma lista de bibliotecas de interface de usuário principais que são amplamente utilizadas no projeto.

**Section sources**
- [package.json](file://package.json#L1-L86)
- [next.config.mjs](file://next.config.mjs#L1-L14)
- [tsconfig.json](file://tsconfig.json#L1-L27)