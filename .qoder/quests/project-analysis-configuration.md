# Análise e Configuração do Projeto Open Gemini Canvas

## Visão Geral

O Open Gemini Canvas é uma aplicação full-stack que utiliza inteligência artificial avançada para gerar conteúdo para redes sociais e analisar stacks tecnológicos de repositórios GitHub. A aplicação combina o poder dos modelos Gemini da Google com a interface interativa do CopilotKit para criar uma experiência de usuário fluida e inteligente.

### Propósito Principal
- **Geração de Posts**: Criação automatizada de conteúdo para LinkedIn e Twitter usando Gemini AI e pesquisa web do Google
- **Análise de Stack**: Análise detalhada de repositórios GitHub para identificar tecnologias, arquitetura e propósito dos projetos
- **Interface Conversacional**: Experiência de chat inteligente para interação natural com os agentes de IA

## Stack Tecnológico & Dependências

### Frontend
| Componente | Tecnologia | Versão | Propósito |
|------------|------------|---------|-----------|
| Framework | Next.js | 15.6+ | Framework React para aplicações web |
| Runtime | React | 19.2.0 | Biblioteca de interface de usuário |
| Linguagem | TypeScript | 5.1+ | Tipagem estática para JavaScript |
| Estilização | Tailwind CSS | 4.1.13 | Framework CSS utilitário |
| Componentes UI | Radix UI | Múltiplas | Componentes acessíveis e customizáveis |
| Ícones | Lucide React | 0.460+ | Biblioteca de ícones SVG |
| Validação | Zod | 3.25+ | Validação de esquemas TypeScript |

### Backend (Agent)
| Componente | Tecnologia | Versão | Propósito |
|------------|------------|---------|-----------|
| Framework | FastAPI | 0.115+ | Framework web Python para APIs |
| Servidor | Uvicorn | 0.35+ | Servidor ASGI para Python |
| Linguagem | Python | 3.12+ | Linguagem de programação |
| Orquestração | LangGraph | 1.0+ | Framework para workflows de IA |
| LLM Core | LangChain Core | 0.3.78 | Framework para aplicações LLM |
| Modelo IA | Google Gemini | 2.5-pro | Modelo de linguagem avançado |

### Integrações e Ferramentas
| Categoria | Tecnologia | Propósito |
|-----------|------------|-----------|
| Plataforma IA | CopilotKit | 1.9+ | Interface conversacional e orquestração de agentes |
| Provedor LLM | Google Generative AI | 1.28+ | Acesso aos modelos Gemini |
| Pesquisa Web | Google Search API | v1 | Busca contextual para geração de conteúdo |
| Validação | GitHub API | v3/v4 | Análise de repositórios e metadados |
| Gerenciamento | Poetry | 1.8+ | Gerenciamento de dependências Python |

## Arquitetura do Sistema

### Arquitetura Geral

```
graph TB
    subgraph "Frontend (Next.js)"
        UI[Interface do Usuário]
        CK[CopilotKit Runtime]
        Pages[Páginas de Aplicação]
    end
    
    subgraph "Backend (FastAPI)"
        Server[Servidor FastAPI]
        Agents[Sistema de Agentes]
        PostGen[Post Generator Agent]
        StackAnalyzer[Stack Analyzer Agent]
    end
    
    subgraph "Serviços Externos"
        Gemini[Google Gemini API]
        Search[Google Search API]
        GitHub[GitHub API]
    end
    
    UI --> CK
    CK --> Server
    Server --> Agents
    Agents --> PostGen
    Agents --> StackAnalyzer
    PostGen --> Gemini
    PostGen --> Search
    StackAnalyzer --> Gemini
    StackAnalyzer --> GitHub
```

### Fluxo de Comunicação

```
sequenceDiagram
    participant User as Usuário
    participant Frontend as Frontend (Next.js)
    participant CopilotKit as CopilotKit Runtime
    participant Backend as Backend (FastAPI)
    participant Agent as Agente Específico
    participant External as APIs Externas

    User->>Frontend: Interage com a interface
    Frontend->>CopilotKit: Envia mensagem do usuário
    CopilotKit->>Backend: Requisição HTTP para /copilotkit
    Backend->>Agent: Roteia para agente específico
    Agent->>External: Consulta APIs externas
    External-->>Agent: Retorna dados
    Agent-->>Backend: Processa resposta
    Backend-->>CopilotKit: Retorna resultado estruturado
    CopilotKit-->>Frontend: Atualiza interface
    Frontend-->>User: Exibe resultado processado
```

## Componentes da Arquitetura

### Frontend (Next.js Application)

#### Estrutura de Componentes

```
graph TD
    Layout[RootLayout] --> LayoutProvider[LayoutProvider]
    Layout --> Wrapper[CopilotKit Wrapper]
    
    Wrapper --> PostGen[Post Generator Page]
    Wrapper --> StackAnalyzer[Stack Analyzer Page]
    
    PostGen --> PostUI[Post Generation UI]
    PostGen --> ChatInterface[Chat Interface]
    
    StackAnalyzer --> AnalysisUI[Analysis UI]
    StackAnalyzer --> ChatInterface2[Chat Interface]
    
    ChatInterface --> CopilotChat[CopilotChat Component]
    ChatInterface2 --> CopilotChat2[CopilotChat Component]
```

#### Gestão de Estado

| Componente | Responsabilidade | Escopo |
|------------|------------------|---------|
| LayoutContext | Gerencia estado global da aplicação | Global |
| useCoAgent | Estado específico do agente ativo | Por página |
| useCopilotChat | Estado das mensagens do chat | Por sessão |
| useCopilotAction | Ações executáveis pelos agentes | Por agente |

### Backend (FastAPI Agent System)

#### Arquitetura dos Agentes

```
graph TB
    subgraph "Sistema de Agentes"
        SDK[CopilotKit SDK]
        PostAgent[Post Generation Agent]
        StackAgent[Stack Analysis Agent]
    end
    
    subgraph "Post Generation Workflow"
        ChatNode[Chat Node]
        FEActions[Frontend Actions Node]
        EndNode[End Node]
    end
    
    subgraph "Stack Analysis Workflow"
        GatherContext[Gather Context Node]
        AnalyzeGemini[Analyze with Gemini Node]
        EndNode2[End Node]
    end
    
    SDK --> PostAgent
    SDK --> StackAgent
    PostAgent --> ChatNode
    ChatNode --> FEActions
    FEActions --> EndNode
    StackAgent --> GatherContext
    GatherContext --> AnalyzeGemini
    AnalyzeGemini --> EndNode2
```

#### Definição de Estados dos Agentes

**Post Generation Agent State:**
- `tool_logs`: Lista de logs de ferramentas para interface
- `response`: Resposta processada do modelo Gemini
- `messages`: Histórico de mensagens da conversa

**Stack Analysis Agent State:**
- `tool_logs`: Logs de progresso da análise
- `analysis`: Análise estruturada do repositório
- `show_cards`: Flag para exibição de cartões de análise
- `context`: Contexto coletado do repositório GitHub
- `last_user_content`: Último conteúdo do usuário

## Modelos de Dados & Esquemas

### Post Generation Schema

| Campo | Tipo | Descrição |
|-------|------|-----------|
| tweet.title | string | Título do post para Twitter |
| tweet.content | string | Conteúdo do post para Twitter |
| linkedIn.title | string | Título do post para LinkedIn |
| linkedIn.content | string | Conteúdo do post para LinkedIn |

### Stack Analysis Schema

| Seção | Campos | Descrição |
|-------|--------|-----------|
| purpose | string | Propósito do projeto |
| frontend | FrontendSpec | Especificações do frontend |
| backend | BackendSpec | Especificações do backend |
| database | DatabaseSpec | Configuração de banco de dados |
| infrastructure | InfrastructureSpec | Especificações de infraestrutura |
| ci_cd | CICDSpec | Configuração de CI/CD |
| key_root_files | List[KeyRootFileSpec] | Arquivos importantes na raiz |
| how_to_run | HowToRunSpec | Instruções de execução |
| risks_notes | List[RiskNoteSpec] | Notas e riscos identificados |

## Referência de Endpoints da API

### Endpoints do Backend

| Endpoint | Método | Descrição | Parâmetros |
|----------|--------|-----------|------------|
| `/copilotkit` | POST | Endpoint principal do CopilotKit | Mensagens e configuração do agente |
| `/healthz` | GET | Verificação de saúde do servidor | Nenhum |
| `/` | GET | Endpoint raiz | Nenhum |

### Endpoints do Frontend

| Rota | Componente | Descrição |
|------|------------|-----------|
| `/` | Home Page | Redirecionamento para post-generator |
| `/post-generator` | PostGenerator | Interface de geração de posts |
| `/stack-analyzer` | StackAnalyzer | Interface de análise de stack |
| `/api/copilotkit` | CopilotKit Runtime | Proxy para o backend |
| `/api/chat` | Chat Route | Endpoint de chat alternativo |

## Lógica de Negócio (Arquitetura de Funcionalidades)

### Funcionalidade: Geração de Posts

#### Fluxo de Execução

```
graph TD
    UserInput[Entrada do Usuário] --> AnalyzeQuery[Análise da Query]
    AnalyzeQuery --> WebSearch[Pesquisa Web Google]
    WebSearch --> ContentGeneration[Geração de Conteúdo]
    ContentGeneration --> StructuredOutput[Saída Estruturada]
    StructuredOutput --> RenderPosts[Renderização dos Posts]
```

#### Componentes de Processamento

| Etapa | Responsabilidade | Tecnologia |
|-------|------------------|------------|
| Análise Inicial | Interpretar intenção do usuário | Gemini 2.5-pro |
| Pesquisa Contextual | Buscar informações relevantes | Google Search API |
| Geração de Conteúdo | Criar posts otimizados | Gemini 2.5-pro + prompts |
| Validação | Verificar qualidade e formato | LangChain tools |

### Funcionalidade: Análise de Stack

#### Fluxo de Coleta de Contexto

```
graph TD
    URLInput[URL do GitHub] --> ParseURL[Parse da URL]
    ParseURL --> FetchMetadata[Buscar Metadados]
    FetchMetadata --> FetchLanguages[Buscar Linguagens]
    FetchLanguages --> FetchREADME[Buscar README]
    FetchREADME --> FetchManifests[Buscar Manifestos]
    FetchManifests --> StructuredAnalysis[Análise Estruturada]
```

#### Componentes de Análise

| Componente | Dados Coletados | Fonte |
|------------|-----------------|-------|
| Repository Info | Metadados gerais, estrelas, forks | GitHub API |
| Language Detection | Bytes de código por linguagem | GitHub API |
| Documentation | README, arquivos de configuração | GitHub Raw |
| Manifest Analysis | package.json, requirements.txt, etc. | GitHub Contents API |
| Structural Analysis | Hierarquia de pastas e arquivos | GitHub Contents API |

## Middleware & Interceptadores

### CopilotKit Runtime Middleware

| Funcionalidade | Descrição | Implementação |
|----------------|-----------|---------------|
| Message Routing | Roteia mensagens para agentes corretos | CopilotRuntime |
| State Management | Gerencia estado entre frontend e backend | copilotkit_emit_state |
| Tool Integration | Integra ferramentas externas | useCopilotAction |
| Error Handling | Tratamento de erros de API | GoogleGenerativeAIAdapter |

### Configuração de Interceptadores

**Frontend (CopilotKit Wrapper):**
- Intercepta mensagens do usuário
- Roteia para endpoint correto baseado no agente ativo
- Gerencia estado de loading e erro

**Backend (FastAPI Middleware):**
- Valida requisições de entrada
- Configura headers CORS
- Gerencia timeout de requisições
- Log de atividades dos agentes

## Estratégia de Teste

### Testes Unitários

| Componente | Foco dos Testes | Ferramentas |
|------------|-----------------|-------------|
| Agentes Python | Lógica de processamento, validação de esquemas | pytest, pytest-asyncio |
| Componentes React | Renderização, interações do usuário | Jest, React Testing Library |
| Utilitários | Funções de parsing, validação | Jest, vitest |

### Testes de Integração

| Cenário | Descrição | Validação |
|---------|-----------|-----------|
| Fluxo Completo de Posts | Da entrada do usuário até renderização | UI + API + Gemini |
| Análise de Repositório | Parse de URL até análise completa | GitHub API + Gemini |
| Troca de Agentes | Mudança entre funcionalidades | Estado da aplicação |

### Cenários de Teste

**Geração de Posts:**
- Entrada simples: tópico direto
- Entrada complexa: pesquisa contextual necessária
- Falha de API: tratamento de erros
- Formato inválido: validação de entrada

**Análise de Stack:**
- URL válida do GitHub: análise completa
- URL inválida: tratamento de erro
- Repositório privado: acesso negado
- Repositório vazio: análise mínima

## Configuração de Migração para OpenRouter

### Objetivo da Migração

Substituir o uso direto da API do Google Gemini por uma integração com OpenRouter, mantendo a funcionalidade existente e adicionando flexibilidade para múltiplos provedores de modelo.

### Arquitetura Proposta

```
graph TB
    subgraph "Configuração Atual"
        CurrentApp[Aplicação]
        CurrentGemini[Google Gemini Direct]
    end
    
    subgraph "Configuração Futura"
        NewApp[Aplicação]
        OpenRouter[OpenRouter Gateway]
        Gemini[Google Gemini]
        OpenAI[OpenAI]
        Anthropic[Anthropic]
        Others[Outros Modelos]
    end
    
    CurrentApp --> CurrentGemini
    NewApp --> OpenRouter
    OpenRouter --> Gemini
    OpenRouter --> OpenAI
    OpenRouter --> Anthropic
    OpenRouter --> Others
```

### Etapas de Migração

#### 1. Configuração de Ambiente

| Variável | Valor Atual | Valor Proposto |
|----------|-------------|----------------|
| `GOOGLE_API_KEY` | Chave direta do Gemini | Removida |
| `OPENROUTER_API_KEY` | N/A | Chave do OpenRouter |
| `OPENROUTER_MODEL` | N/A | `google/gemini-2.5-pro` |
| `OPENROUTER_BASE_URL` | N/A | `https://openrouter.ai/api/v1` |

#### 2. Modificações no Backend

**Arquivo: `agent/posts_generator_agent.py`**
- Substituir `from google import genai` por cliente OpenRouter
- Atualizar configuração do modelo para usar OpenRouter
- Manter interface LangChain existente

**Arquivo: `agent/stack_agent.py`**
- Migrar configuração do `ChatGoogleGenerativeAI` para OpenRouter
- Preservar funcionalidade de structured output
- Atualizar parâmetros de configuração

#### 3. Modificações no Frontend

**Arquivo: `app/api/copilotkit/route.ts`**
- Substituir `GoogleGenerativeAIAdapter` por `OpenAIAdapter`
- Configurar URL base do OpenRouter
- Manter compatibilidade com CopilotKit

#### 4. Validação de Compatibilidade

| Funcionalidade | Status Atual | Pós-Migração |
|----------------|--------------|--------------|
| Geração de Posts | Gemini direto | OpenRouter → Gemini |
| Análise de Stack | Gemini direto | OpenRouter → Gemini |
| Structured Output | Suportado | Mantido |
| Tool Calling | Suportado | Mantido |
| Streaming | Suportado | Mantido |

### Configuração de Dependências

#### Dependências a Adicionar

```
# Backend (pyproject.toml)
openai >= 1.50.0  # Cliente OpenAI compatível com OpenRouter
httpx >= 0.27.0  # Cliente HTTP para requisições customizadas
langchain >= 0.3.78  # Versão mais recente do LangChain
langgraph >= 1.0.0  # LangGraph versão estável

# Frontend (package.json)
@ai-sdk/openai: "latest"  # Cliente AI SDK para OpenRouter
@copilotkit/react-core: "^1.9+"  # CopilotKit core atualizado
```

#### Dependências a Remover

```
# Backend (Dependências Obsoletas - Remover)
google (==3.0.0)
google-genai (==1.28.0)
google-generativeai (>=0.8.5,<0.9.0)
langchain[google-genai] (==0.3.26)

# Substituir por:
openai >= 1.50.0
langchain-openai >= 0.2.0
langchain-core >= 0.3.78
```

### Configuração de Deployment

#### Variáveis de Ambiente Atualizadas

**Desenvolvimento (Outubro 2025):**
```
OPENROUTER_API_KEY=seu_openrouter_key_aqui
OPENROUTER_MODEL=google/gemini-2.5-pro
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
NEXT_PUBLIC_LANGGRAPH_URL=http://localhost:8000/copilotkit
NODE_ENV=development
```

**Produção (Deploy PoC - Outubro 2025):**
- Configurar secrets no ambiente de deploy (Vercel, Railway, etc.)
- Monitoramento básico de funcionamento
- Validação de funcionalidades core

### Benefícios da Migração (PoC)

| Benefício | Descrição | Impacto |
|-----------|-----------|---------|
| Flexibilidade | Acesso a múltiplos modelos via uma interface | Alto |
| Fallback | Possibilidade de fallback entre modelos | Médio |
| Monitoramento | Dashboard básico de uso | Médio |
| Prova de Conceito | Validação da viabilidade técnica | Alto |

### Riscos e Mitigações (PoC)

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Latência adicional | Baixa | Médio | Monitoramento básico de performance |
| Compatibilidade | Baixa | Alto | Testes extensivos, rollback plan |
| Dependência externa | Média | Médio | Plano de contingência simples |

### Cronograma de Migração (Outubro 2025)

| Fase | Duração | Atividades |
|------|----------|------------|
| Preparação | 1-2 dias | Setup OpenRouter, atualização de dependências |
| Desenvolvimento | 3-5 dias | Implementação da migração, testes locais |
| Teste | 2-3 dias | Testes de integração, validação de funcionalidades |
| Deploy | 1 dia | Deploy em produção, monitoramento |
| Validação | 2-3 dias | Monitoramento pós-deploy, ajustes finos |

**Total Estimado: 9-14 dias**
