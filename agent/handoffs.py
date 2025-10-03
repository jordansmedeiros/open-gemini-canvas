"""
Sistema de Handoffs entre Agentes
Este módulo implementa um sistema robusto de transferência de controle entre agentes.
"""

import os
import json
from typing import Any, Dict, List, Optional, Union, Literal
from enum import Enum
import uuid
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
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

# ==================== CONFIGURAÇÃO DE LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== MODELOS DE DADOS ====================

class HandoffReason(Enum):
    SPECIALIZATION = "specialization"  # Tarefa requer especialização específica
    CAPACITY = "capacity"  # Agente atual está sobrecarregado
    FAILURE = "failure"  # Agente atual falhou
    OPTIMIZATION = "optimization"  # Melhor agente disponível para a tarefa
    USER_REQUEST = "user_request"  # Usuário solicitou agente específico
    WORKFLOW = "workflow"  # Parte de um fluxo predefinido


class AgentCapability(Enum):
    CONTENT_GENERATION = "content_generation"
    CODE_ANALYSIS = "code_analysis" 
    RESEARCH = "research"
    DATA_PROCESSING = "data_processing"
    TRANSLATION = "translation"
    OPTIMIZATION = "optimization"
    TESTING = "testing"
    DEPLOYMENT = "deployment"


class HandoffPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentMetadata:
    id: str
    name: str
    capabilities: List[AgentCapability]
    max_concurrent_tasks: int = 3
    current_load: int = 0
    average_response_time: float = 5.0  # segundos
    success_rate: float = 0.95
    last_active: datetime = None


class HandoffRequest(BaseModel):
    """Requisição de transferência entre agentes."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str
    to_agent: str
    reason: HandoffReason
    priority: HandoffPriority = HandoffPriority.MEDIUM
    task_description: str
    context_data: Dict[str, Any] = Field(default_factory=dict)
    requirements: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HandoffResponse(BaseModel):
    """Resposta de uma transferência."""
    request_id: str
    accepted: bool
    agent_id: str
    estimated_completion: Optional[datetime] = None
    reason: Optional[str] = None
    alternative_agent: Optional[str] = None


class HandoffState(CopilotKitState):
    """Estado para gerenciamento de handoffs."""
    current_agent: str = "supervisor"
    active_handoffs: List[HandoffRequest] = Field(default_factory=list)
    completed_handoffs: List[HandoffRequest] = Field(default_factory=list)
    agent_registry: Dict[str, AgentMetadata] = Field(default_factory=dict)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    handoff_history: List[Dict[str, Any]] = Field(default_factory=list)
    tool_logs: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== REGISTRO DE AGENTES ====================

def initialize_agent_registry() -> Dict[str, AgentMetadata]:
    """Inicializa o registro de agentes disponíveis."""
    return {
        "post_generator": AgentMetadata(
            id="post_generator",
            name="Gerador de Posts",
            capabilities=[AgentCapability.CONTENT_GENERATION],
            max_concurrent_tasks=5,
            average_response_time=3.0,
            success_rate=0.92
        ),
        "stack_analyzer": AgentMetadata(
            id="stack_analyzer", 
            name="Analisador de Stack",
            capabilities=[AgentCapability.CODE_ANALYSIS, AgentCapability.RESEARCH],
            max_concurrent_tasks=3,
            average_response_time=8.0,
            success_rate=0.98
        ),
        "research_agent": AgentMetadata(
            id="research_agent",
            name="Agente de Pesquisa",
            capabilities=[AgentCapability.RESEARCH, AgentCapability.DATA_PROCESSING],
            max_concurrent_tasks=10,
            average_response_time=5.0,
            success_rate=0.96
        ),
        "content_optimizer": AgentMetadata(
            id="content_optimizer",
            name="Otimizador de Conteúdo",
            capabilities=[AgentCapability.CONTENT_GENERATION, AgentCapability.OPTIMIZATION],
            max_concurrent_tasks=4,
            average_response_time=4.0,
            success_rate=0.94
        ),
        "translator": AgentMetadata(
            id="translator",
            name="Tradutor",
            capabilities=[AgentCapability.TRANSLATION],
            max_concurrent_tasks=8,
            average_response_time=2.0,
            success_rate=0.99
        )
    }


# ==================== FERRAMENTAS DE HANDOFF ====================

@tool
async def transfer_to_post_generator(
    task_description: str,
    platform: str = "both",
    context: str = "",
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Transfere tarefa para o agente gerador de posts.
    
    Args:
        task_description: Descrição da tarefa de geração
        platform: Plataforma alvo (linkedin, twitter, both)
        context: Contexto adicional para geração
        priority: Prioridade da tarefa (low, medium, high, urgent)
    """
    return await _execute_handoff(
        from_agent="supervisor",
        to_agent="post_generator",
        task_description=task_description,
        context_data={
            "platform": platform,
            "context": context
        },
        priority=HandoffPriority[priority.upper()],
        reason=HandoffReason.SPECIALIZATION
    )


@tool
async def transfer_to_stack_analyzer(
    task_description: str,
    github_url: str,
    analysis_depth: str = "standard",
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Transfere tarefa para o agente analisador de stack.
    
    Args:
        task_description: Descrição da análise necessária
        github_url: URL do repositório para análise
        analysis_depth: Profundidade da análise (quick, standard, deep)
        priority: Prioridade da tarefa
    """
    return await _execute_handoff(
        from_agent="supervisor",
        to_agent="stack_analyzer",
        task_description=task_description,
        context_data={
            "github_url": github_url,
            "analysis_depth": analysis_depth
        },
        priority=HandoffPriority[priority.upper()],
        reason=HandoffReason.SPECIALIZATION
    )


@tool
async def transfer_to_research_agent(
    task_description: str,
    research_query: str,
    sources: List[str] = ["web"],
    max_results: int = 10,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Transfere tarefa para o agente de pesquisa.
    
    Args:
        task_description: Descrição da pesquisa necessária
        research_query: Query de pesquisa
        sources: Fontes para pesquisa
        max_results: Número máximo de resultados
        priority: Prioridade da tarefa
    """
    return await _execute_handoff(
        from_agent="supervisor",
        to_agent="research_agent",
        task_description=task_description,
        context_data={
            "query": research_query,
            "sources": sources,
            "max_results": max_results
        },
        priority=HandoffPriority[priority.upper()],
        reason=HandoffReason.SPECIALIZATION
    )


@tool
async def request_agent_handoff(
    current_agent: str,
    target_agent: str, 
    reason: str,
    task_description: str,
    context_data: Dict[str, Any] = {},
    priority: str = "medium",
    requirements: List[str] = []
) -> Dict[str, Any]:
    """
    Solicita transferência genérica entre agentes.
    
    Args:
        current_agent: Agente atual
        target_agent: Agente de destino
        reason: Motivo da transferência
        task_description: Descrição da tarefa
        context_data: Dados de contexto
        priority: Prioridade da transferência
        requirements: Requisitos específicos
    """
    return await _execute_handoff(
        from_agent=current_agent,
        to_agent=target_agent,
        task_description=task_description,
        context_data=context_data,
        priority=HandoffPriority[priority.upper()],
        reason=HandoffReason[reason.upper()],
        requirements=requirements
    )


@tool
async def get_available_agents(
    required_capabilities: List[str] = [],
    max_load_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Obtém lista de agentes disponíveis com base em critérios.
    
    Args:
        required_capabilities: Capacidades necessárias
        max_load_threshold: Limite máximo de carga do agente
    """
    registry = initialize_agent_registry()
    available_agents = []
    
    for agent_id, metadata in registry.items():
        # Verificar capacidades
        if required_capabilities:
            agent_caps = [cap.value for cap in metadata.capabilities]
            if not any(cap in agent_caps for cap in required_capabilities):
                continue
        
        # Verificar carga
        load_ratio = metadata.current_load / metadata.max_concurrent_tasks
        if load_ratio > max_load_threshold:
            continue
            
        available_agents.append({
            "id": agent_id,
            "name": metadata.name,
            "capabilities": [cap.value for cap in metadata.capabilities],
            "load_ratio": load_ratio,
            "avg_response_time": metadata.average_response_time,
            "success_rate": metadata.success_rate
        })
    
    # Ordenar por melhor disponibilidade (menor carga, maior taxa de sucesso)
    available_agents.sort(
        key=lambda x: (x["load_ratio"], -x["success_rate"])
    )
    
    return {
        "available_agents": available_agents,
        "total_count": len(available_agents),
        "selection_criteria": {
            "required_capabilities": required_capabilities,
            "max_load_threshold": max_load_threshold
        }
    }


# ==================== FUNÇÕES AUXILIARES ====================

async def _execute_handoff(
    from_agent: str,
    to_agent: str,
    task_description: str,
    context_data: Dict[str, Any],
    priority: HandoffPriority,
    reason: HandoffReason,
    requirements: List[str] = []
) -> Dict[str, Any]:
    """Executa uma transferência entre agentes."""
    
    # Criar requisição de handoff
    request = HandoffRequest(
        from_agent=from_agent,
        to_agent=to_agent,
        reason=reason,
        priority=priority,
        task_description=task_description,
        context_data=context_data,
        requirements=requirements
    )
    
    # Simular validação e processamento
    await asyncio.sleep(0.5)  # Simular tempo de processamento
    
    # Verificar disponibilidade do agente alvo
    registry = initialize_agent_registry()
    target_metadata = registry.get(to_agent)
    
    if not target_metadata:
        return {
            "success": False,
            "error": f"Agente '{to_agent}' não encontrado",
            "request_id": request.id
        }
    
    # Verificar capacidade
    load_ratio = target_metadata.current_load / target_metadata.max_concurrent_tasks
    if load_ratio >= 0.9:  # 90% de capacidade
        return {
            "success": False,
            "error": f"Agente '{to_agent}' está sobrecarregado",
            "request_id": request.id,
            "current_load": load_ratio,
            "alternative_agents": _suggest_alternative_agents(
                target_metadata.capabilities, registry
            )
        }
    
    # Simular execução da tarefa no agente alvo
    execution_time = target_metadata.average_response_time
    await asyncio.sleep(min(execution_time / 10, 2))  # Simular parte do tempo
    
    # Gerar resultado baseado na taxa de sucesso
    import random
    success = random.random() < target_metadata.success_rate
    
    if success:
        result = {
            "success": True,
            "request_id": request.id,
            "agent": to_agent,
            "task_completed": True,
            "execution_time": execution_time,
            "result_data": {
                "task": task_description,
                "context": context_data,
                "completed_at": datetime.now().isoformat(),
                "agent_metadata": {
                    "name": target_metadata.name,
                    "capabilities": [cap.value for cap in target_metadata.capabilities]
                }
            }
        }
    else:
        result = {
            "success": False,
            "request_id": request.id,
            "agent": to_agent,
            "error": "Falha na execução da tarefa",
            "retry_recommended": True,
            "alternative_agents": _suggest_alternative_agents(
                target_metadata.capabilities, registry
            )
        }
    
    return result


def _suggest_alternative_agents(
    required_capabilities: List[AgentCapability],
    registry: Dict[str, AgentMetadata]
) -> List[str]:
    """Sugere agentes alternativos baseado em capacidades."""
    alternatives = []
    
    for agent_id, metadata in registry.items():
        # Verificar se tem pelo menos uma capacidade necessária
        if any(cap in metadata.capabilities for cap in required_capabilities):
            load_ratio = metadata.current_load / metadata.max_concurrent_tasks
            if load_ratio < 0.8:  # Apenas agentes com menos de 80% de carga
                alternatives.append(agent_id)
    
    return alternatives[:3]  # Retornar até 3 alternativas


# ==================== NODOS DE HANDOFF ====================

async def handoff_coordinator_node(state: HandoffState, config: RunnableConfig) -> Command:
    """
    Nodo coordenador que gerencia handoffs entre agentes.
    """
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    # Inicializar registro se necessário
    if not state.agent_registry:
        state.agent_registry = initialize_agent_registry()
    
    # Log de início
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Inicializando coordenador de handoffs",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Configurar modelo
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0.2,
        max_retries=2,
    )
    
    # Ferramentas de handoff
    tools = [
        transfer_to_post_generator,
        transfer_to_stack_analyzer,
        transfer_to_research_agent,
        request_agent_handoff,
        get_available_agents
    ]
    
    # Prompt do coordenador
    system_prompt = f"""
    Você é um coordenador inteligente de handoffs entre agentes especializados.
    
    Agentes disponíveis:
    {json.dumps({k: {"name": v.name, "capabilities": [c.value for c in v.capabilities]} for k, v in state.agent_registry.items()}, indent=2)}
    
    Suas responsabilidades:
    1. Analisar requisições e determinar o melhor agente para cada tarefa
    2. Executar transferências usando as ferramentas disponíveis
    3. Monitorar carga e disponibilidade dos agentes
    4. Sugerir alternativas quando agentes estão indisponíveis
    5. Coordenar fluxos multi-agente complexos
    
    Para cada requisição:
    - Identifique as capacidades necessárias
    - Escolha o agente mais adequado
    - Execute a transferência usando as ferramentas
    - Monitore o progresso e resultados
    
    Sempre use as ferramentas de transferência em vez de tentar processar diretamente.
    """
    
    # Obter última mensagem
    last_message = state.messages[-1].content if state.messages else "Inicializar sistema de handoffs"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_message)
    ]
    
    # Executar modelo com ferramentas
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(messages, config)
    
    # Atualizar log
    state.tool_logs[-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    
    # Verificar tool calls
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return Command(
            goto="execute_handoffs",
            update={"messages": [response]}
        )
    else:
        return Command(
            goto="finalize_handoffs",
            update={
                "messages": [response]
            }
        )


async def execute_handoffs_node(state: HandoffState, config: RunnableConfig) -> Command:
    """
    Executa as transferências solicitadas.
    """
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    handoff_results = []
    last_message = state.messages[-1] if state.messages else None
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            
            # Log da execução
            state.tool_logs.append({
                "id": str(uuid.uuid4()),
                "message": f"Executando handoff: {tool_name}",
                "status": "processing",
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "args": tool_args
            })
            await copilotkit_emit_state(config, state)
            
            try:
                # Executar ferramenta
                if tool_name == "transfer_to_post_generator":
                    result = await transfer_to_post_generator.ainvoke(tool_args)
                elif tool_name == "transfer_to_stack_analyzer":
                    result = await transfer_to_stack_analyzer.ainvoke(tool_args)
                elif tool_name == "transfer_to_research_agent":
                    result = await transfer_to_research_agent.ainvoke(tool_args)
                elif tool_name == "request_agent_handoff":
                    result = await request_agent_handoff.ainvoke(tool_args)
                elif tool_name == "get_available_agents":
                    result = await get_available_agents.ainvoke(tool_args)
                else:
                    result = {"error": f"Ferramenta de handoff desconhecida: {tool_name}"}
                
                handoff_results.append({
                    "tool": tool_name,
                    "result": result,
                    "success": result.get("success", True) if isinstance(result, dict) else True
                })
                
                # Atualizar histórico de handoffs
                if isinstance(result, dict) and result.get("request_id"):
                    state.handoff_history.append({
                        "request_id": result["request_id"],
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Atualizar log de sucesso
                state.tool_logs[-1]["status"] = "completed"
                state.tool_logs[-1]["result"] = result
                
            except Exception as e:
                error_result = {
                    "tool": tool_name,
                    "error": str(e),
                    "success": False
                }
                handoff_results.append(error_result)
                
                # Atualizar log de erro
                state.tool_logs[-1]["status"] = "failed"
                state.tool_logs[-1]["error"] = str(e)
            
            await copilotkit_emit_state(config, state)
    
    return Command(
        goto="finalize_handoffs",
        update={
            "execution_context": {
                "handoff_results": handoff_results,
                "total_handoffs": len(handoff_results),
                "successful_handoffs": sum(1 for r in handoff_results if r.get("success", False))
            }
        }
    )


async def finalize_handoffs_node(state: HandoffState, config: RunnableConfig) -> Command:
    """
    Finaliza o processamento de handoffs.
    """
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True
    )
    
    # Log de finalização
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Finalizando handoffs",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Gerar relatório de handoffs
    handoff_results = state.execution_context.get("handoff_results", [])
    successful_count = sum(1 for r in handoff_results if r.get("success", False))
    total_count = len(handoff_results)
    
    final_response = f"Sistema de handoffs processou {total_count} transferência(s).\n"
    final_response += f"✅ Sucessos: {successful_count}\n"
    final_response += f"❌ Falhas: {total_count - successful_count}\n\n"
    
    if handoff_results:
        final_response += "Detalhes dos handoffs:\n"
        for i, result in enumerate(handoff_results, 1):
            tool = result.get("tool", "desconhecido")
            success = result.get("success", False)
            status = "✅" if success else "❌"
            final_response += f"{status} {i}. {tool}\n"
            
            if not success and "error" in result:
                final_response += f"   Erro: {result['error']}\n"
    
    # Limpar logs
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(
        goto=END,
        update={
            "messages": [AIMessage(content=final_response)]
        }
    )


# ==================== CRIAÇÃO DO GRAFO ====================

def create_handoff_graph() -> StateGraph:
    """
    Cria o grafo de gerenciamento de handoffs.
    """
    workflow = StateGraph(HandoffState)
    
    # Adicionar nodos
    workflow.add_node("coordinator", handoff_coordinator_node)
    workflow.add_node("execute_handoffs", execute_handoffs_node)
    workflow.add_node("finalize_handoffs", finalize_handoffs_node)
    
    # Definir entrada e saída
    workflow.set_entry_point("coordinator")
    workflow.set_finish_point("finalize_handoffs")
    
    # Adicionar arestas
    workflow.add_edge(START, "coordinator")
    workflow.add_edge("execute_handoffs", "finalize_handoffs")
    workflow.add_edge("finalize_handoffs", END)
    
    # Compilar com checkpoint
    return workflow.compile(checkpointer=MemorySaver())


# Instanciar o grafo de handoffs
handoff_graph = create_handoff_graph()