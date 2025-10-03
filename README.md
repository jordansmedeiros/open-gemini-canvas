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


### 2. Environment Configuration

Create a `.env` file in each relevant directory as needed. 

#### Backend (`agent/.env`):
```env
GOOGLE_API_KEY=<<your-gemini-key-here>>
```

#### Frontend (`/.env`):
```env
GOOGLE_API_KEY=<<your-gemini-key-here>>
```

---

### 3. Running the project

```bash
pnpm install
pnpm dev
```

---

Open [http://localhost:3000](http://localhost:3000) in your browser to view the app.

---

## Notes
- Ensure the backend agent is running before using the frontend.
- Update environment variables as needed for your deployment.

---

### Hosted URL: https://copilot-kit-deepmind.vercel.app/
