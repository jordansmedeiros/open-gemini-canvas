# Configuração OpenRouter - Open Gemini Canvas

## Visão Geral da Migração

Este projeto foi migrado do uso direto da API do Google Gemini para OpenRouter, proporcionando maior flexibilidade e acesso a múltiplos modelos de IA através de uma interface unificada.

## Configuração de Ambiente

### 1. Variáveis de Ambiente Necessárias

Copie os arquivos `.env.example` para `.env` tanto na raiz quanto na pasta `agent/`:

**Raiz do projeto (`.env`):**
```env
# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-pro
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Configuration
NEXT_PUBLIC_LANGGRAPH_URL=http://localhost:8000/copilotkit
NODE_ENV=development
```

**Pasta agent (`.env`):**
```env
# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-pro
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Configuration  
NEXT_PUBLIC_LANGGRAPH_URL=http://localhost:8000/copilotkit
NODE_ENV=development
```

### 2. Obter Chave API do OpenRouter

1. Acesse [OpenRouter.ai](https://openrouter.ai/)
2. Crie uma conta ou faça login
3. Navegue para as configurações de API
4. Gere uma nova chave API
5. Substitua `your_openrouter_api_key_here` pela sua chave real

## Modelos Disponíveis

O OpenRouter oferece acesso a múltiplos modelos. Alguns exemplos:

### Modelos Google
- `google/gemini-2.5-pro` (padrão, mantém compatibilidade)
- `google/gemini-pro-1.5`
- `google/gemini-flash-1.5`

### Modelos OpenAI
- `openai/gpt-4o`
- `openai/gpt-4-turbo`
- `openai/gpt-3.5-turbo`

### Modelos Anthropic
- `anthropic/claude-3-opus`
- `anthropic/claude-3-sonnet`
- `anthropic/claude-3-haiku`

Para usar um modelo diferente, altere a variável `OPENROUTER_MODEL` nos arquivos `.env`.

## Alterações Técnicas Implementadas

### Backend (Python/FastAPI)

#### Dependências Atualizadas (`agent/pyproject.toml`)
```toml
dependencies = [
    "openai (>=1.50.0,<2.0.0)",           # Cliente OpenAI compatível
    "python-dotenv (>=1.0.0,<2.0.0)",    # Carregamento de env
    "langchain-openai (>=0.2.0,<0.3.0)", # LangChain + OpenAI
    "langchain-core (>=0.3.78,<0.4.0)",  # Core do LangChain
    "langgraph (>=1.0.0,<2.0.0)",        # Orquestração de agentes
    "fastapi (>=0.115.0,<0.116.0)",      # Framework web
    "uvicorn (>=0.35.0,<0.36.0)",        # Servidor ASGI
    "copilotkit (==0.1.58)",             # Integração CopilotKit
    "requests (>=2.31.0,<3.0.0)",        # HTTP requests
    "httpx (>=0.27.0,<0.28.0)"           # HTTP client assíncrono
]
```

#### Agentes Migrados
- **`posts_generator_agent.py`**: Migrado para `ChatOpenAI` com OpenRouter
- **`stack_agent.py`**: Migrado para `ChatOpenAI` com OpenRouter

### Frontend (Next.js/TypeScript)

#### API Route Atualizada (`app/api/copilotkit/route.ts`)
```typescript
// Antes (Google Gemini direto)
const serviceAdapter = new GoogleGenerativeAIAdapter();

// Depois (OpenRouter)
const serviceAdapter = new OpenAIAdapter({
  api_key: process.env.OPENROUTER_API_KEY,
  baseURL: process.env.OPENROUTER_BASE_URL || "https://openrouter.ai/api/v1",
  model: process.env.OPENROUTER_MODEL || "google/gemini-2.5-pro",
});
```

## Instalação e Execução

### 1. Instalar Dependências

```bash
# Frontend
pnpm install

# Backend (será executado automaticamente via postinstall)
cd agent
poetry install
```

### 2. Configurar Ambiente

```bash
# Copiar arquivos de exemplo
cp .env.example .env
cp agent/.env.example agent/.env

# Editar arquivos .env com suas credenciais
```

### 3. Executar Aplicação

```bash
# Desenvolvimento (executa frontend e backend simultaneamente)
pnpm dev

# Ou separadamente
pnpm dev:ui    # Frontend (porta 3000)
pnpm dev:agent # Backend (porta 8000)
```

## Funcionalidades Mantidas

### Geração de Posts
- ✅ Análise inteligente de consultas do usuário
- ✅ Pesquisa web contextual (via ferramenta personalizada)
- ✅ Geração de conteúdo para LinkedIn e Twitter
- ✅ Interface de chat em tempo real
- ✅ Logs de progresso no frontend

### Análise de Stack
- ✅ Análise de repositórios GitHub
- ✅ Identificação de tecnologias e frameworks
- ✅ Análise estruturada de arquitetura
- ✅ Cartões de visualização organizados
- ✅ Extração de metadados e dependências

## Benefícios da Migração

### 1. Flexibilidade de Modelos
- Acesso a múltiplos provedores (Google, OpenAI, Anthropic, etc.)
- Mudança de modelo sem alteração de código
- Fallback entre modelos em caso de falha

### 2. Gestão Centralizada
- Dashboard unificado no OpenRouter
- Monitoramento de uso e custos
- Controle de rate limits

### 3. Melhor Confiabilidade
- Múltiplos endpoints disponíveis
- Redundância automática
- Monitoramento de status

## Troubleshooting

### Erro de Autenticação
```
Error: Invalid API key
```
**Solução**: Verifique se `OPENROUTER_API_KEY` está configurado corretamente nos arquivos `.env`.

### Modelo Não Encontrado
```
Error: Model not found
```
**Solução**: Verifique se o modelo especificado em `OPENROUTER_MODEL` está disponível no OpenRouter.

### Conexão Recusada
```
Error: Connection refused
```
**Solução**: Verifique se `OPENROUTER_BASE_URL` está correto e se há conectividade com a internet.

### Cota Excedida
```
Error: Rate limit exceeded
```
**Solução**: Verifique seu plano no OpenRouter e considere upgrading ou aguarde o reset do limite.

## Monitoramento

### Dashboard OpenRouter
Acesse o dashboard do OpenRouter para monitorar:
- Uso por modelo
- Custos em tempo real
- Performance das requisições
- Logs de erro

### Logs da Aplicação
```bash
# Backend logs
cd agent && poetry run python main.py

# Frontend logs
pnpm dev:ui
```

## Migração de Volta (Rollback)

Caso precise reverter para Google Gemini direto:

1. Restaure as dependências antigas no `pyproject.toml`
2. Reverta os arquivos de agente para usar `ChatGoogleGenerativeAI`
3. Configure `GOOGLE_API_KEY` nos arquivos `.env`
4. Atualize `route.ts` para usar `GoogleGenerativeAIAdapter`

## Suporte

Para questões técnicas sobre:
- **OpenRouter**: [Documentação OpenRouter](https://openrouter.ai/docs)
- **CopilotKit**: [Documentação CopilotKit](https://docs.copilotkit.ai/)
- **LangChain**: [Documentação LangChain](https://python.langchain.com/)

---

*Documentação atualizada em Outubro 2025 - Versão OpenRouter Migration*