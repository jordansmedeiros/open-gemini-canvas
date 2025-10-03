"""
Este módulo serve os agentes jurídicos especializados através de um servidor FastAPI.
Sistema multi-agente robusto para o Vieira Pires Advogados.
"""

import os
from dotenv import load_dotenv

load_dotenv()  

from fastapi import FastAPI
import uvicorn
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent

# Importar agentes especializados
from master_agent import master_agent_graph
from agente_societario import societario_agent_graph
from agente_tributario import tributario_agent_graph
from agente_contratos import contratos_agent_graph
from supervisor import supervisor_graph
from handoffs import handoff_graph

app = FastAPI(
    title="Vieira Pires Advogados - Sistema Multi-Agente",
    description="Sistema jurídico avançado com agentes especializados",
    version="2.0.0"
)

# Configurar endpoint remoto com agentes especializados
sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAgent(
            name="master_legal_agent",
            description="Agente supervisor master que coordena consultas jurídicas complexas entre especialistas",
            graph=master_agent_graph,
        ),
        LangGraphAgent(
            name="societario_specialist",
            description="Especialista em estruturação societária, holdings, planejamento sucessório e blindagem patrimonial",
            graph=societario_agent_graph,
        ),
        LangGraphAgent(
            name="tributario_specialist",
            description="Especialista em planejamento tributário, defesas fiscais e reforma tributária",
            graph=tributario_agent_graph,
        ),
        LangGraphAgent(
            name="contratos_specialist",
            description="Especialista em contratos empresariais, due diligence, M&A e acordos comerciais complexos",
            graph=contratos_agent_graph,
        ),
        LangGraphAgent(
            name="supervisor_coordinator",
            description="Coordenador centralizado para workflows multi-agente e distribuição de tarefas",
            graph=supervisor_graph,
        ),
        LangGraphAgent(
            name="handoff_manager",
            description="Gerenciador de transferências entre agentes e coordenação de workflows especializados",
            graph=handoff_graph,
        ),
    ]
)

add_fastapi_endpoint(app, sdk, "/copilotkit")


@app.get("/healthz")
def health():
    """Health check."""
    return {
        "status": "ok", 
        "system": "Vieira Pires Legal Multi-Agent System",
        "agents_available": 6,
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "model": os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        "specialties": ["Societário", "Tributário", "Contratos", "Trabalhista", "Franquias"]
    }


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Vieira Pires Advogados - Sistema Jurídico Multi-Agente",
        "version": "2.0.0",
        "endpoints": {
            "copilotkit": "/copilotkit",
            "health": "/healthz",
            "docs": "/docs"
        },
        "agents": [
            "Master Legal Agent - Coordenação Geral",
            "Societário Specialist - Holdings & Estruturação", 
            "Tributário Specialist - Planejamento Fiscal",
            "Contratos Specialist - Acordos Empresariais",
            "Supervisor Coordinator - Workflows",
            "Handoff Manager - Transferências"
        ]
    }


@app.get("/agents")
def list_agents():
    """Lista agentes disponíveis."""
    return {
        "total_agents": 6,
        "agents": [
            {
                "name": "master_legal_agent",
                "specialty": "Coordenação Jurídica Master",
                "capabilities": ["Análise complexa", "Coordenação multi-agente", "Pareceres executivos"]
            },
            {
                "name": "societario_specialist", 
                "specialty": "Direito Societário & Holdings",
                "capabilities": ["Contratos sociais", "Holdings", "Planejamento sucessório", "Blindagem patrimonial"]
            },
            {
                "name": "tributario_specialist",
                "specialty": "Direito Tributário",
                "capabilities": ["Planejamento fiscal", "Defesas fiscais", "Reforma tributária", "Compliance tributário"]
            },
            {
                "name": "contratos_specialist",
                "specialty": "Contratos Empresariais & M&A",
                "capabilities": ["Contratos comerciais", "Due diligence", "M&A", "Acordos internacionais"]
            },
            {
                "name": "supervisor_coordinator",
                "specialty": "Coordenação de Workflows",
                "capabilities": ["Distribuição tarefas", "Coordenação centralizada", "Tool-calling"]
            },
            {
                "name": "handoff_manager",
                "specialty": "Gerenciamento de Transferências",
                "capabilities": ["Handoffs inteligentes", "Workflows especializados", "Coordenação hierárquica"]
            }
        ]
    }


def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
