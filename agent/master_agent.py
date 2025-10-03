"""
Agente Supervisor Master - Coordenação Hierárquica Jurídica
Sistema de coordenação para agentes jurídicos especializados do Vieira Pires Advogados.
"""

import os
import json
from typing import Any, Dict, List, Literal, Optional
from enum import Enum
import uuid
import asyncio
from datetime import datetime

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from copilotkit import CopilotKitState
from copilotkit.langgraph import copilotkit_emit_state
from copilotkit.langchain import copilotkit_customize_config

load_dotenv()


# ==================== ENUMS E TIPOS ====================

class AreaJuridica(Enum):
    SOCIETARIO = "societario"
    TRIBUTARIO = "tributario" 
    CONTRATOS = "contratos"
    TRABALHISTA = "trabalhista"
    FRANQUIAS = "franquias"


class TipoConsulta(Enum):
    ESTRUTURACAO = "estruturacao"
    PARECER = "parecer"
    MINUTA = "minuta"
    DEFESA = "defesa"
    COMPLIANCE = "compliance"


class MasterAgentState(CopilotKitState):
    """Estado do agente supervisor master."""
    area_identificada: Optional[str] = None
    complexidade: Optional[str] = None
    agentes_necessarios: List[str] = Field(default_factory=list)
    resultados_analise: Dict[str, Any] = Field(default_factory=dict)
    tool_logs: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== FERRAMENTAS ESPECIALIZADAS ====================

@tool
async def analisar_consulta_juridica(
    descricao_consulta: str,
    contexto_empresa: str = "",
    urgencia: bool = False
) -> Dict[str, Any]:
    """Analisa consulta jurídica e determina área especializada."""
    
    descricao_lower = descricao_consulta.lower()
    
    # Mapeamento de áreas por palavras-chave
    area_keywords = {
        "societario": ["holding", "sociedade", "sócio", "contrato social", "sucessão"],
        "tributario": ["tributo", "imposto", "icms", "ipi", "fiscalização", "reforma tributária"],
        "contratos": ["contrato", "prestação de serviços", "fornecimento", "due diligence"],
        "trabalhista": ["trabalhista", "empregado", "clt", "rescisão", "reclamação"],
        "franquias": ["franquia", "franqueado", "cof", "marca", "royalties"]
    }
    
    # Calcular pontuações
    pontuacoes = {}
    for area, keywords in area_keywords.items():
        pontuacao = sum(1 for keyword in keywords if keyword in descricao_lower)
        if pontuacao > 0:
            pontuacoes[area] = pontuacao
    
    area_principal = max(pontuacoes.keys(), key=lambda x: pontuacoes[x]) if pontuacoes else "contratos"
    
    # Determinar complexidade
    indicadores_complexidade = ["holding", "internacional", "due diligence", "reforma tributária"]
    complexidade_score = sum(1 for ind in indicadores_complexidade if ind in descricao_lower)
    
    if complexidade_score >= 2:
        complexidade = "alta"
    elif complexidade_score >= 1:
        complexidade = "media"
    else:
        complexidade = "baixa"
    
    return {
        "area_principal": area_principal,
        "complexidade": complexidade,
        "pontuacao_areas": pontuacoes,
        "urgencia": urgencia,
        "agentes_recomendados": [area_principal] + [area for area, pont in pontuacoes.items() 
                                                   if area != area_principal and pont > 0]
    }


@tool
async def executar_agente_especializado(
    agente: str,
    consulta: str,
    contexto: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """Executa agente jurídico especializado."""
    
    # Simular execução do agente especializado
    await asyncio.sleep(1)
    
    resultados_agentes = {
        "societario": {
            "tipo": "Estruturação Societária",
            "documentos": ["Contrato Social", "Acordo de Sócios"],
            "recomendacoes": ["Implementar holding patrimonial", "Blindagem patrimonial"],
            "prazo": "5-7 dias úteis"
        },
        "tributario": {
            "tipo": "Análise Tributária", 
            "economia_estimada": "15-25% redução tributária",
            "estrategias": ["Planejamento fiscal", "Regime tributário otimizado"],
            "prazo": "3-5 dias úteis"
        },
        "contratos": {
            "tipo": "Elaboração Contratual",
            "contratos": ["Prestação de Serviços", "Confidencialidade"],
            "clausulas_criticas": ["Limitação responsabilidade", "Foro"],
            "prazo": "2-3 dias úteis"
        },
        "trabalhista": {
            "tipo": "Compliance Trabalhista",
            "politicas": ["Manual Empregado", "Código Ética"],
            "riscos": ["Configuração vínculo PJ", "Adequação jornada"],
            "prazo": "4-6 dias úteis"
        },
        "franquias": {
            "tipo": "Estruturação Franquia",
            "documentos": ["COF", "Contrato Franquia"],
            "investimento": "R$ 150k - R$ 300k",
            "prazo": "7-10 dias úteis"
        }
    }
    
    return resultados_agentes.get(agente, {"erro": "Agente não encontrado"})


# ==================== NODOS DO MASTER AGENT ====================

async def master_analyzer_node(state: MasterAgentState, config: RunnableConfig) -> Command:
    """Nodo principal de análise e coordenação."""
    
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Iniciando análise jurídica master",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Configurar modelo
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0.1,
        max_retries=2,
    )
    
    tools = [analisar_consulta_juridica, executar_agente_especializado]
    
    system_prompt = """
    Você é o MASTER AGENT do escritório Vieira Pires Advogados.
    
    ÁREAS ESPECIALIZADAS:
    🏢 SOCIETÁRIO: Holdings, estruturas societárias, sucessão
    📊 TRIBUTÁRIO: Planejamento fiscal, defesas fiscais
    📄 CONTRATOS: Contratos empresariais, due diligence
    👔 TRABALHISTA: Compliance trabalhista, defesas
    🏪 FRANQUIAS: Estruturação de franquias, COF
    
    PROCESSO:
    1. Analise a consulta com analisar_consulta_juridica
    2. Execute agentes especializados conforme necessário
    3. Coordene resultados em parecer executivo
    
    Use SEMPRE as ferramentas disponíveis para análise precisa.
    """
    
    last_message = state.messages[-1].content if state.messages else "Inicializar análise"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Consulta: {last_message}")
    ]
    
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(messages, config)
    
    state.tool_logs[-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return Command(goto="execute_tools", update={"messages": [response]})
    else:
        return Command(goto="finalize", update={"messages": [response]})


async def execute_tools_node(state: MasterAgentState, config: RunnableConfig) -> Command:
    """Executa ferramentas de análise."""
    
    results = []
    last_message = state.messages[-1] if state.messages else None
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            
            state.tool_logs.append({
                "id": str(uuid.uuid4()),
                "message": f"Executando: {tool_name}",
                "status": "processing",
                "timestamp": datetime.now().isoformat()
            })
            await copilotkit_emit_state(config, state)
            
            try:
                if tool_name == "analisar_consulta_juridica":
                    result = await analisar_consulta_juridica.ainvoke(tool_args)
                    state.area_identificada = result.get("area_principal")
                    state.complexidade = result.get("complexidade")
                    state.agentes_necessarios = result.get("agentes_recomendados", [])
                elif tool_name == "executar_agente_especializado":
                    result = await executar_agente_especializado.ainvoke(tool_args)
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
                
                results.append({"tool": tool_name, "result": result, "success": True})
                state.tool_logs[-1]["status"] = "completed"
                
            except Exception as e:
                results.append({"tool": tool_name, "error": str(e), "success": False})
                state.tool_logs[-1]["status"] = "failed"
            
            await copilotkit_emit_state(config, state)
    
    return Command(
        goto="finalize",
        update={"resultados_analise": {"tool_results": results}}
    )


async def finalize_node(state: MasterAgentState, config: RunnableConfig) -> Command:
    """Finaliza com parecer executivo."""
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Gerando parecer executivo",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Gerar parecer baseado nos resultados
    parecer = "# PARECER EXECUTIVO - VIEIRA PIRES ADVOGADOS\n\n"
    parecer += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if state.area_identificada:
        parecer += f"## ANÁLISE JURÍDICA\n"
        parecer += f"- **Área Principal:** {state.area_identificada.title()}\n"
        parecer += f"- **Complexidade:** {state.complexidade.title()}\n\n"
    
    results = state.resultados_analise.get("tool_results", [])
    if results:
        parecer += "## RESULTADOS\n"
        for result in results:
            if result.get("success"):
                tool_result = result["result"]
                parecer += f"✅ **{result['tool']}:** Concluído\n"
                
                # Adicionar detalhes específicos
                if "prazo" in tool_result:
                    parecer += f"   - Prazo: {tool_result['prazo']}\n"
                if "documentos" in tool_result:
                    parecer += f"   - Documentos: {', '.join(tool_result['documentos'])}\n"
            else:
                parecer += f"❌ **{result['tool']}:** Erro\n"
        
        parecer += "\n"
    
    parecer += "## PRÓXIMOS PASSOS\n"
    parecer += "1. Agendar reunião para apresentação dos resultados\n"
    parecer += "2. Definir cronograma de execução\n"
    parecer += "3. Iniciar elaboração dos documentos\n\n"
    parecer += "---\n"
    parecer += "*Vieira Pires Advogados - Excelência Jurídica Empresarial*"
    
    # Limpar logs
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(
        goto=END,
        update={"messages": [AIMessage(content=parecer)]}
    )


# ==================== CRIAÇÃO DO GRAFO ====================

def create_master_agent_graph() -> StateGraph:
    """Cria grafo do agente supervisor master."""
    
    workflow = StateGraph(MasterAgentState)
    
    # Adicionar nodos
    workflow.add_node("analyzer", master_analyzer_node)
    workflow.add_node("execute_tools", execute_tools_node) 
    workflow.add_node("finalize", finalize_node)
    
    # Definir fluxo
    workflow.set_entry_point("analyzer")
    workflow.set_finish_point("finalize")
    
    # Adicionar arestas
    workflow.add_edge(START, "analyzer")
    workflow.add_edge("execute_tools", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow.compile(checkpointer=MemorySaver())


# Instância do grafo master
master_agent_graph = create_master_agent_graph()