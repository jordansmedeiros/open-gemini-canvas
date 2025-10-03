# Open Gemini Canvas

https://github.com/user-attachments/assets/1e95c9e1-2d55-4f63-b805-be49fe94a493

# CopilotKit + OpenRouter (Gemini) + LangGraph Template

This project showcases how to build practical AI agents with **CopilotKit**, **OpenRouter** (accessing Google Gemini), and **LangGraph**.  
It includes two agents, exposed through a **Next.js frontend** and a **FastAPI backend**.

## 🔄 Latest Update: OpenRouter Migration

**📅 Outubro 2025** - O projeto foi migrado para usar **OpenRouter** em vez da API direta do Google Gemini, proporcionando:
- ✅ **Flexibilidade**: Acesso a múltiplos modelos de IA (Google, OpenAI, Anthropic, etc.)
- ✅ **Confiabilidade**: Fallback automático entre modelos
- ✅ **Monitoramento**: Dashboard centralizado de uso e custos
- ✅ **Escalabilidade**: Melhor gestão de rate limits

📖 **[Ver Guia Completo de Migração](./OPENROUTER_SETUP.md)**

## ✨ Features

- **Post Generator Agent**  
  Generate LinkedIn and Twitter posts from the context you provide.  
  Useful for creating professional, context-aware social content.

- **Stack Analyzer Agent**  
  Provide a URL and get a detailed breakdown of the site’s technology stack.  
  Quickly identify frameworks, libraries, and infrastructure used.

## 🛠️ Tech Stack

- **Frontend**: Next.js 15 + TypeScript
- **Backend**: FastAPI + Python 3.12+
- **AI Provider**: OpenRouter (acesso a Google Gemini 2.5-pro e outros modelos)
- **Orquestração**: LangGraph para workflows de agentes
- **UI Integration**: CopilotKit para interface conversacional
- **Styling**: Tailwind CSS + Radix UI


## 📌 About

This demo illustrates how CopilotKit can be paired with LangGraph and Gemini to create agents that are:
- **Context-aware** (understand the input you provide)
- **Task-focused** (generate content or analyze stacks)
- **UI-integrated** (feels like part of your app, not just a chatbox)


---

## Project Structure

- `/` — Next.js 15 app (UI) in the Project Root 
- `agent/` — FastAPI backend agent (Python)

---

## 🚀 Getting Started

### 1. Clone the repository
Clone this repo `git clone <project URL>`


### 2. Environment Configuration (OpenRouter)

**🔴 Importante**: Este projeto agora usa OpenRouter em vez da API direta do Google Gemini.

#### Passo 1: Obter Chave API do OpenRouter
1. Acesse [OpenRouter.ai](https://openrouter.ai/)
2. Crie uma conta ou faça login
3. Gere uma chave API nas configurações

#### Passo 2: Configurar Variáveis de Ambiente

Copie os arquivos de exemplo e configure:

```bash
# Copiar arquivos de exemplo
cp .env.example .env
cp agent/.env.example agent/.env
```

#### Backend (`agent/.env`):
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-pro
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
NEXT_PUBLIC_LANGGRAPH_URL=http://localhost:8000/copilotkit
```

#### Frontend (`/.env`):
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-pro
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
NEXT_PUBLIC_LANGGRAPH_URL=http://localhost:8000/copilotkit
```

---

### 3. Running the project

#### Instalação Rápida (Recomendado):
```bash
# Instalar dependências do frontend e backend
pnpm install

# Executar aplicação completa (frontend + backend)
pnpm dev
```

#### Instalação Manual do Backend (se necessário):
```bash
# Ir para a pasta do backend
cd agent

# Opção 1: Usando Poetry (se instalado)
poetry install
poetry run python main.py

# Opção 2: Usando script de setup
# Windows
.\..\scripts\setup-openrouter.bat

# Linux/Mac
sh ../scripts/setup-openrouter.sh
```

#### Execução Separada:
```bash
# Frontend apenas (porta 3000)
pnpm dev:ui

# Backend apenas (porta 8000)
pnpm dev:agent
```

---

Open [http://localhost:3000](http://localhost:3000) in your browser to view the app.

---

## 📝 Notes

- **OpenRouter Setup**: Este projeto agora usa OpenRouter para maior flexibilidade
- **Backend First**: Certifique-se de que o backend está rodando antes de usar o frontend
- **Modelos Disponíveis**: Além do Gemini, você pode usar GPT-4, Claude, e outros modelos
- **Monitoramento**: Use o dashboard do OpenRouter para acompanhar uso e custos

## 🔧 Troubleshooting

### Erro de Autenticação
Se receber erro de API key:
1. Verifique se `OPENROUTER_API_KEY` está configurado corretamente
2. Confirme que a chave é válida no dashboard do OpenRouter

### Problemas de Depências
Se houver problemas com instalação:
1. Use os scripts em `./scripts/setup-openrouter.*`
2. Verifique se Python 3.12+ está instalado
3. Consulte [OPENROUTER_SETUP.md](./OPENROUTER_SETUP.md) para guia detalhado

## 📚 Documentação Adicional

- **[Guia Completo OpenRouter](./OPENROUTER_SETUP.md)** - Instruções detalhadas de migração
- **[OpenRouter Docs](https://openrouter.ai/docs)** - Documentação oficial
- **[CopilotKit Docs](https://docs.copilotkit.ai/)** - Integração de interface
- **[LangGraph Docs](https://python.langchain.com/docs/langgraph/)** - Orquestração de agentes

---

### Hosted URL: https://copilot-kit-deepmind.vercel.app/
