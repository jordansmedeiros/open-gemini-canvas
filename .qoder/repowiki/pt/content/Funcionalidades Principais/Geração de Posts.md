# Geração de Posts

<cite>
**Arquivos Referenciados neste Documento**  
- [post-generator/page.tsx](file://app/post-generator/page.tsx)
- [posts_generator_agent.py](file://agent/posts_generator_agent.py)
- [prompts.py](file://agent/prompts.py)
- [prompts.ts](file://app/prompts/prompts.ts)
- [x-post.tsx](file://components/ui/x-post.tsx)
- [linkedin-post.tsx](file://components/ui/linkedin-post.tsx)
- [tool-logs.tsx](file://components/ui/tool-logs.tsx)
</cite>

## Sumário
1. [Introdução](#introdução)
2. [Estrutura do Projeto](#estrutura-do-projeto)
3. [Componentes Principais](#componentes-principais)
4. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
5. [Análise Detalhada dos Componentes](#análise-detalhada-dos-componentes)
6. [Análise de Dependências](#análise-de-dependências)
7. [Considerações de Desempenho](#considerações-de-desempenho)
8. [Guia de Solução de Problemas](#guia-de-solução-de-problemas)
9. [Conclusão](#conclusão)

## Introdução

O sistema de Geração de Posts é uma aplicação web avançada que utiliza inteligência artificial para criar conteúdo personalizado para redes sociais, especificamente LinkedIn e X (Twitter). O sistema combina a potência do modelo de IA Google Gemini com pesquisa web em tempo real para gerar posts informativos, atualizados e otimizados para cada plataforma. A interação do usuário é intuitiva, permitindo a inserção de tópicos e a geração automática de conteúdo formatado com base em prompts sofisticados. Este documento detalha o fluxo completo da funcionalidade, desde a interface do usuário até a geração final do conteúdo.

## Estrutura do Projeto

A aplicação segue uma arquitetura modular com uma clara separação entre a camada de frontend (Next.js) e a camada de backend/agentes (Python com LangGraph). Os componentes principais estão organizados em diretórios distintos, facilitando a manutenção e a escalabilidade.

```mermaid
graph TB
subgraph "Frontend (Next.js)"
UI[Interface do Usuário]
PostGen[post-generator/page.tsx]
Components[components/ui]
PromptsTS[app/prompts/prompts.ts]
end
subgraph "Backend (Python)"
Agent[agent/posts_generator_agent.py]
PromptsPY[agent/prompts.py]
Main[agent/main.py]
end
UI --> PostGen
PostGen --> PromptsTS
PostGen --> Components
PostGen --> Agent
Agent --> PromptsPY
Agent --> Main
```

**Diagram sources**
- [post-generator/page.tsx](file://app/post-generator/page.tsx)
- [posts_generator_agent.py](file://agent/posts_generator_agent.py)

**Section sources**
- [post-generator/page.tsx](file://app/post-generator/page.tsx)
- [posts_generator_agent.py](file://agent/posts_generator_agent.py)

## Componentes Principais

Os componentes principais do sistema de Geração de Posts são a interface do usuário em `post-generator/page.tsx`, o agente de IA `posts_generator_agent.py`, os prompts definidos em `prompts.py` e `prompts.ts`, e os componentes de UI `x-post.tsx` e `linkedin-post.tsx` para exibição das pré-visualizações. O gerenciamento de estado é feito através de hooks personalizados como `useCoAgent` e `useCopilotAction`, enquanto os logs das ferramentas são exibidos pelo componente `ToolLogs`.

**Section sources**
- [post-generator/page.tsx](file://app/post-generator/page.tsx#L1-L50)
- [posts_generator_agent.py](file://agent/posts_generator_agent.py#L1-L20)
- [prompts.py](file://agent/prompts.py#L1-L10)
- [prompts.ts](file://app/prompts/prompts.ts#L1-L5)

## Visão Geral da Arquitetura

A arquitetura do sistema é baseada em um fluxo de trabalho orientado a eventos, onde a ação do usuário aciona uma cadeia de processos envolvendo comunicação entre frontend e backend, execução de ferramentas de IA e atualização da interface.

```mermaid
sequenceDiagram
participant Usuario as "Usuário"
participant UI as "Interface (page.tsx)"
participant CoAgent as "useCoAgent"
participant Agent as "post_generation_agent"
participant Search as "google_search"
participant Model as "Google Gemini"
participant ToolLogs as "ToolLogs"
participant Preview as "XPost/LinkedInPost"
Usuario->>UI : Insere tópico e envia
UI->>CoAgent : Envia mensagem via appendMessage
CoAgent->>Agent : Recebe mensagem e inicia chat_node
Agent->>Search : Executa google_search(query)
Search-->>Agent : Retorna resultados da pesquisa
Agent->>Model : Invoca modelo com contexto pesquisado
Model-->>Agent : Gera resposta intermediária
Agent->>Agent : Processa resposta e prepara para fe_actions_node
Agent->>ToolLogs : Atualiza logs com status "processing"
Agent->>Model : Invoca modelo com system_prompt_3
Model-->>Agent : Gera objeto com posts para X e LinkedIn
Agent->>UI : Retorna comando com posts via generate_post
UI->>Preview : Renderiza pré-visualizações
ToolLogs-->>UI : Exibe logs atualizados
UI-->>Usuario : Mostra posts gerados e logs
```

**Diagram sources**
- [post-generator/page.tsx](file://app/post-generator/page.tsx#L150-L400)
- [posts_generator_agent.py](file://agent/posts_generator_agent.py#L50-L170)

## Análise Detalhada dos Componentes

### Análise do Componente de Geração de Posts

O componente principal `PostGenerator` em `page.tsx` é responsável por gerenciar todo o fluxo de interação do usuário, estado da aplicação e comunicação com o agente de IA. Ele utiliza hooks do CopilotKit para integrar-se com o backend e renderizar dinamicamente os resultados.

#### Análise do Fluxo de Estado e Ações

O gerenciamento de estado é centralizado no hook `useCoAgent`, que inicializa o estado do agente com uma lista vazia de `tool_logs`. O hook `useCopilotAction` define a ação `generate_post`, que é acionada pelo backend quando os posts são gerados. Essa ação recebe um objeto com as propriedades `tweet` e `linkedIn`, cada uma contendo `title` e `content`, e atualiza o estado local para exibir as pré-visualizações.

```mermaid
classDiagram
class PostInterface {
+tweet : Tweet
+linkedIn : LinkedIn
}
class Tweet {
+title : string
+content : string
}
class LinkedIn {
+title : string
+content : string
}
class PostGenerator {
-selectedAgent : Agent
-showColumns : boolean
-posts : PostInterface
-isAgentActive : boolean
+useCoAgent() : void
+useCopilotAction() : void
+useCopilotChatSuggestions() : void
}
class ToolLogs {
+logs : ToolLog[]
+render() : JSX.Element
}
class XPost {
+title : string
+content : string
+render() : JSX.Element
}
class LinkedInPost {
+title : string
+content : string
+render() : JSX.Element
}
PostInterface --> Tweet
PostInterface --> LinkedIn
PostGenerator --> PostInterface
PostGenerator --> ToolLogs
PostGenerator --> XPost
PostGenerator --> LinkedInPost
```

**Diagram sources**
- [post-generator/page.tsx](file://app/post-generator/page.tsx#L62-L71)
- [post-generator/page.tsx](file://app/post-generator/page.tsx#L100-L150)

**Section sources**
- [post-generator/page.tsx](file://app/post-generator/page.tsx#L1-L410)

#### Análise do Agente de Geração de Posts

O agente `posts_generator_agent.py` é implementado usando LangGraph e define um grafo de estado com três nós principais: `chat_node`, `fe_actions_node` e `end_node`. O `chat_node` inicia a conversa, realiza a pesquisa web usando a ferramenta `google_search` e gera uma resposta inicial. O `fe_actions_node` então utiliza o modelo Gemini para gerar os posts formatados para X e LinkedIn, acionando a ação `generate_post` no frontend. O fluxo é controlado por uma função de roteamento que determina o próximo nó com base no estado da conversa.

```mermaid
flowchart TD
Start([Início]) --> ChatNode["chat_node: Recebe mensagem do usuário"]
ChatNode --> GoogleSearch["google_search: Realiza pesquisa web"]
GoogleSearch --> ModelInvoke["Modelo Gemini: Gera resposta com contexto"]
ModelInvoke --> FeActionsNode["fe_actions_node: Prepara ação de frontend"]
FeActionsNode --> GeneratePost["generate_post: Renderiza posts no frontend"]
GeneratePost --> EndNode["end_node: Finaliza processo"]
EndNode --> End([Fim])
style ChatNode fill:#4A90E2,stroke:#357ABD,stroke-width:2px
style GoogleSearch fill:#50C878,stroke:#3D9970,stroke-width:2px
style ModelInvoke fill:#FFD700,stroke:#FFC107,stroke-width:2px
style FeActionsNode fill:#8E44AD,stroke:#7D3C98,stroke-width:2px
style GeneratePost fill:#E67E22,stroke:#D35400,stroke-width:2px
style EndNode fill:#27AE60,stroke:#229954,stroke-width:2px
```

**Diagram sources**
- [posts_generator_agent.py](file://agent/posts_generator_agent.py#L50-L170)

**Section sources**
- [posts_generator_agent.py](file://agent/posts_generator_agent.py#L1-L175)

#### Análise dos Prompts

Os prompts são definidos em dois arquivos: `prompts.py` para o backend e `prompts.ts` para o frontend. No backend, `system_prompt` instrui o agente a sempre realizar uma pesquisa web antes de responder, garantindo que a informação seja atual. O `system_prompt_3` fornece diretrizes específicas para a geração de posts, incluindo formatação com emojis, uso de hashtags para X e tom mais formal para LinkedIn. No frontend, `initialPrompt` define a mensagem inicial exibida ao usuário.

**Section sources**
- [prompts.py](file://agent/prompts.py#L1-L50)
- [prompts.ts](file://app/prompts/prompts.ts#L1-L10)

## Análise de Dependências

O sistema depende de várias bibliotecas e serviços externos. O frontend utiliza Next.js, React e Tailwind CSS, além de bibliotecas específicas do CopilotKit para integração com o backend. O backend depende do LangChain, LangGraph e da API do OpenRouter para acessar o modelo Gemini. A comunicação entre frontend e backend é feita através de rotas API definidas em `app/api/copilotkit/route.ts`.

```mermaid
erDiagram
FRONTEND ||--o{ BACKEND : "Comunicação via API"
FRONTEND ||--o{ PROMPTS_TS : "Usa prompts iniciais"
BACKEND ||--o{ PROMPTS_PY : "Usa prompts do sistema"
BACKEND ||--o{ GOOGLE_SEARCH : "Executa pesquisas"
BACKEND ||--o{ GEMINI : "Gera conteúdo"
FRONTEND ||--o{ X_POST : "Renderiza pré-visualização"
FRONTEND ||--o{ LINKEDIN_POST : "Renderiza pré-visualização"
FRONTEND ||--o{ TOOL_LOGS : "Exibe status das ferramentas"
```

**Diagram sources**
- [package.json](file://package.json)
- [pyproject.toml](file://agent/pyproject.toml)

**Section sources**
- [package.json](file://package.json)
- [agent/pyproject.toml](file://agent/pyproject.toml)

## Considerações de Desempenho

O desempenho do sistema é influenciado principalmente pela latência das chamadas à API do Gemini e à ferramenta de pesquisa web. O uso de `async/await` permite que as operações de E/S sejam executadas de forma não bloqueante, mantendo a interface responsiva. A renderização das pré-visualizações é otimizada com componentes compactos (`XPostCompact`, `LinkedInPostCompact`) durante o processo de geração, reduzindo o custo de renderização.

## Guia de Solução de Problemas

Problemas comuns incluem falhas na pesquisa web devido a conectividade ou limites de taxa da API, e erros na geração de posts devido a prompts mal formatados. O componente `ToolLogs` é essencial para o diagnóstico, exibindo o status de cada etapa do processo (processamento ou concluído). Para otimizar os resultados, recomenda-se formular prompts claros e específicos, evitando ambiguidades que possam levar a pesquisas irrelevantes.

**Section sources**
- [tool-logs.tsx](file://components/ui/tool-logs.tsx#L1-L50)

## Conclusão

O sistema de Geração de Posts demonstra uma integração eficaz entre frontend e backend, utilizando IA para automatizar a criação de conteúdo para redes sociais. A arquitetura modular, o uso de prompts bem definidos e a interface de usuário intuitiva tornam o sistema poderoso e fácil de usar. A dependência de conectividade para pesquisa web é uma limitação conhecida, mas também uma força, pois garante que o conteúdo gerado seja baseado em informações atualizadas. Futuras melhorias podem incluir suporte a mais plataformas sociais e personalização avançada do estilo de escrita.