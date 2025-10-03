# Referência de API

<cite>
**Arquivos Referenciados neste Documento**  
- [app/api/copilotkit/route.ts](file://app/api/copilotkit/route.ts)
- [app/api/chat/route.ts](file://app/api/chat/route.ts)
- [agent/main.py](file://agent/main.py)
- [agent/posts_generator_agent.py](file://agent/posts_generator_agent.py)
- [agent/stack_agent.py](file://agent/stack_agent.py)
- [app/wrapper.tsx](file://app/wrapper.tsx)
</cite>

## Sumário
1. [Introdução](#introdução)
2. [Endpoints do Frontend](#endpoints-do-frontend)
3. [Endpoints do Backend FastAPI](#endpoints-do-backend-fastapi)
4. [Estratégias de Rate Limiting e Tratamento de Erros](#estratégias-de-rate-limiting-e-tratamento-de-erros)
5. [Diretrizes para Clientes](#diretrizes-para-clientes)
6. [Considerações de Autenticação](#considerações-de-autenticação)
7. [Exemplos de Uso](#exemplos-de-uso)

## Introdução
Este documento fornece uma referência completa das APIs públicas do projeto Open Gemini Canvas, que combina inteligência artificial avançada com análise de repositórios e geração de conteúdo. O sistema é composto por um frontend Next.js e um backend FastAPI, integrados via CopilotKit para suporte a agentes de IA. Os endpoints principais incluem `/api/copilotkit` para ações de agentes de IA e `/api/chat` para interações diretas com modelos de linguagem. O backend expõe agentes especializados em geração de posts e análise de stacks tecnológicos.

**Seção fontes**
- [app/api/copilotkit/route.ts](file://app/api/copilotkit/route.ts#L1-L25)
- [agent/main.py](file://agent/main.py#L1-L62)

## Endpoints do Frontend

### `/api/copilotkit` (POST)
Este endpoint é o ponto de integração entre o frontend e os agentes de IA do backend via CopilotKit. Ele atua como um proxy para rotear solicitações aos agentes apropriados com base no contexto da sessão.

**Método HTTP**: `POST`  
**Padrão de URL**: `/api/copilotkit`  
**Autenticação**: Não requer autenticação explícita; a segurança é baseada em variáveis de ambiente e rotas internas.  
**Headers Esperados**:
- `Content-Type: application/json`

**Esquema de Requisição**:
```json
{
  "action": "string",
  "payload": {}
}
```

**Esquema de Resposta**:
- **200 OK**: Resposta do agente processada com sucesso.
- **500 Internal Server Error**: Erro ao processar a solicitação no backend.

**Códigos de Status**:
- `200`: Sucesso
- `500`: Erro interno do servidor

Este endpoint utiliza o `CopilotRuntime` com `GoogleGenerativeAIAdapter` para conectar-se ao backend em `NEXT_PUBLIC_LANGGRAPH_URL`. Ele é configurado no frontend via `CopilotKit` no componente `Wrapper`.

**Seção fontes**
- [app/api/copilotkit/route.ts](file://app/api/copilotkit/route.ts#L1-L25)
- [app/wrapper.tsx](file://app/wrapper.tsx#L1-L11)

### `/api/chat` (POST)
Este endpoint permite interações diretas com o modelo GPT-4o da OpenAI, habilitando ferramentas de pesquisa e geração de relatórios.

**Método HTTP**: `POST`  
**Padrão de URL**: `/api/chat`  
**Autenticação**: Não requer autenticação explícita.  
**Headers Esperados**:
- `Content-Type: application/json`

**Esquema de Requisição**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "string"
    }
  ]
}
```

**Esquema de Resposta**:
- **200 OK**: Stream de texto com mensagens do modelo.
- **400 Bad Request**: Corpo da requisição inválido.
- **500 Internal Server Error**: Falha ao gerar resposta.

**Ferramentas Disponíveis**:
- `researchTopic`: Pesquisa um tópico com profundidade básica ou abrangente.
- `generateReport`: Gera relatórios em formatos como resumo executivo ou análise detalhada.

**Seção fontes**
- [app/api/chat/route.ts](file://app/api/chat/route.ts#L1-L114)

## Endpoints do Backend FastAPI

### `/copilotkit` (POST)
Endpoint principal do backend FastAPI que expõe os agentes LangGraph ao frontend via CopilotKit.

**Método HTTP**: `POST`  
**Padrão de URL**: `/copilotkit`  
**Autenticação**: Baseada em variáveis de ambiente (ex: `GOOGLE_API_KEY`).  
**Headers Esperados**:
- `Content-Type: application/json`

**Agentes Disponíveis**:
1. **post_generation_agent**: Gera posts para LinkedIn e X com base em pesquisa web.
2. **stack_analysis_agent**: Analisa repositórios GitHub para inferir stack tecnológico.

**Esquema de Resposta**:
- **200 OK**: Resposta do agente em formato JSON.
- **400 Bad Request**: Entrada inválida.
- **500 Internal Server Error**: Erro no processamento do agente.

Este endpoint é configurado com `add_fastapi_endpoint` e usa `CopilotKitSDK` para integrar os agentes.

**Seção fontes**
- [agent/main.py](file://agent/main.py#L1-L62)

### `/healthz` (GET)
Verifica a saúde do serviço backend.

**Método HTTP**: `GET`  
**Padrão de URL**: `/healthz`  
**Resposta de Sucesso**:
```json
{ "status": "ok" }
```
**Códigos de Status**:
- `200`: Serviço ativo e saudável.

**Seção fontes**
- [agent/main.py](file://agent/main.py#L54-L57)

### `/` (GET)
Endpoint raiz para verificação básica.

**Método HTTP**: `GET`  
**Padrão de URL**: `/`  
**Resposta de Sucesso**:
```json
{ "message": "Hello, World!" }
```

**Seção fontes**
- [agent/main.py](file://agent/main.py#L59-L62)

## Estratégias de Rate Limiting e Tratamento de Erros

### Rate Limiting
O projeto não implementa rate limiting explícito nos endpoints. A limitação é gerenciada indiretamente por:
- Timeout do Next.js: `maxDuration = 30` segundos para `/api/chat`.
- Limites de taxa das APIs externas (Google AI, OpenAI).

### Tratamento de Erros
- **Erros de Rede**: Requisições ao backend são feitas via URL configurável (`NEXT_PUBLIC_LANGGRAPH_URL`), com fallback para `localhost:8000`.
- **Erros de Validação**: O frontend valida entradas antes de enviar ao backend.
- **Erros de Agente**: O backend retorna `500` em falhas internas, com logs detalhados no estado do agente (`tool_logs`).
- **Erros de Autenticação**: Falhas em chaves de API (ex: `GOOGLE_API_KEY`) resultam em respostas de erro do modelo subjacente.

**Seção fontes**
- [app/api/chat/route.ts](file://app/api/chat/route.ts#L2)
- [agent/main.py](file://agent/main.py#L1-L62)

## Diretrizes para Clientes

### Timeouts
- **Frontend para Backend**: O cliente deve configurar timeout de pelo menos 30 segundos devido ao `maxDuration` definido.
- **Streaming**: O endpoint `/api/chat` usa streaming, então o cliente deve manter a conexão aberta durante a geração.

### Lógica de Retentativa (Retry Logic)
- **Estratégia Recomendada**: Exponential backoff com jitter.
- **Condições para Retentativa**:
  - `5xx` erros do servidor.
  - Timeout de conexão.
  - Erros de rede (ex: ECONNRESET).
- **Limite de Retentativa**: 3 tentativas antes de falhar.

### Estado do Cliente
O frontend mantém estado ativo via `useCoAgent` e `useCopilotChat`, permitindo recuperação de sessões após desconexões.

**Seção fontes**
- [app/api/chat/route.ts](file://app/api/chat/route.ts#L2)
- [app/stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx#L1-L347)

## Considerações de Autenticação
O sistema não implementa autenticação de usuário tradicional. A segurança é baseada em:
- **Variáveis de Ambiente**: Chaves de API (ex: `GOOGLE_API_KEY`, `GITHUB_TOKEN`) são carregadas no backend.
- **Isolamento de Rotas**: Endpoints sensíveis são protegidos por variáveis de ambiente e não expostos diretamente.
- **Frontend**: O agente ativo é gerenciado pelo contexto `LayoutContext`, mas não há controle de acesso baseado em usuário.

**Seção fontes**
- [agent/main.py](file://agent/main.py#L1-L62)
- [agent/stack_agent.py](file://agent/stack_agent.py#L1-L503)

## Exemplos de Uso

### Exemplo com curl para `/api/chat`
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Pesquise sobre tendências de IA em 2025"
      }
    ]
  }'
```

### Exemplo com JavaScript para `/api/copilotkit`
```javascript
fetch('/api/copilotkit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    action: 'researchTopic',
    payload: { topic: 'IA Generativa', depth: 'comprehensive' }
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Exemplo de Inicialização do Agente de Análise de Stack
```javascript
// No frontend, ao selecionar o agente
updateLayout({ agent: "stack_analysis_agent" });
appendMessage(new TextMessage({
  role: Role.User,
  content: "Analyze https://github.com/example/repo"
}));
```

**Seção fontes**
- [app/api/chat/route.ts](file://app/api/chat/route.ts#L1-L114)
- [app/api/copilotkit/route.ts](file://app/api/copilotkit/route.ts#L1-L25)
- [app/stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx#L1-L347)