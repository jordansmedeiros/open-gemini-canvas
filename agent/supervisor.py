"""
Supervisor Agent - Padrão Centralizado com Tool-Calling
Este módulo implementa um agente supervisor que coordena outros agentes através de ferramentas.
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


class AgentType(Enum):
    POST_GENERATOR = "post_generator"
    STACK_ANALYZER = "stack_analyzer"
    RESEARCH = "research"
    CONTENT_OPTIMIZER = "content_optimizer"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: AgentType
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class SupervisorState(CopilotKitState):
    """Estado do agente supervisor com controle centralizado"""
    current_task: Optional[AgentTask] = None
    task_queue: List[AgentTask] = Field(default_factory=list)
    completed_tasks: List[AgentTask] = Field(default_factory=list)
    failed_tasks: List[AgentTask] = Field(default_factory=list)
    active_agents: Dict[str, str] = Field(default_factory=dict)  # agent_id -> status
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    tool_logs: List[Dict[str, Any]] = Field(default_factory=list)
    final_result: Dict[str, Any] = Field(default_factory=dict)


# ==================== FERRAMENTAS DE AGENTES ====================

@tool
async def execute_post_generator(
    topic: str, 
    platform: str = "both", 
    context: str = "",
    research_required: bool = True
) -> Dict[str, Any]:
    """
    Executa o agente de geração de posts.
    
    Args:
        topic: Tópico para gerar o post
        platform: Plataforma alvo ("linkedin", "twitter", "both")
        context: Contexto adicional para o post
        research_required: Se deve realizar pesquisa antes de gerar
    """
    try:
        # Simular execução do agente de posts
        await asyncio.sleep(1)
        
        result = {
            "agent": "post_generator",
            "status": "success",
            "linkedin_post": f"Post profissional sobre {topic} para LinkedIn com emojis 🚀" if platform in ["linkedin", "both"] else "",
            "twitter_post": f"Post casual sobre {topic} #hashtag" if platform in ["twitter", "both"] else "",
            "research_data": {"sources": ["fonte1", "fonte2"]} if research_required else {},
            "metadata": {
                "topic": topic,
                "platform": platform,
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return result
    except Exception as e:
        return {
            "agent": "post_generator", 
            "status": "error", 
            "error": str(e)
        }


@tool
async def execute_stack_analyzer(
    github_url: str,
    analysis_depth: str = "standard"
) -> Dict[str, Any]:
    """
    Executa o agente de análise de stack.
    
    Args:
        github_url: URL do repositório GitHub
        analysis_depth: Profundidade da análise ("quick", "standard", "deep")
    """
    try:
        # Simular execução do agente de análise
        await asyncio.sleep(2)
        
        result = {
            "agent": "stack_analyzer",
            "status": "success",
            "analysis": {
                "purpose": "Aplicação web moderna",
                "frontend": {"framework": "Next.js", "language": "TypeScript"},
                "backend": {"framework": "FastAPI", "language": "Python"},
                "database": {"type": "PostgreSQL"},
                "infrastructure": {"hosting": "Vercel/Railway"}
            },
            "confidence_score": 0.95,
            "metadata": {
                "url": github_url,
                "analyzed_at": datetime.now().isoformat(),
                "depth": analysis_depth
            }
        }
        
        return result
    except Exception as e:
        return {
            "agent": "stack_analyzer", 
            "status": "error", 
            "error": str(e)
        }


@tool
async def execute_research_agent(
    query: str,
    sources: List[str] = ["web", "academic"],
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Executa agente de pesquisa para coletar informações.
    
    Args:
        query: Consulta de pesquisa
        sources: Fontes para pesquisar
        max_results: Número máximo de resultados
    """
    try:
        await asyncio.sleep(1.5)
        
        result = {
            "agent": "research",
            "status": "success",
            "results": [
                {"title": f"Resultado {i}", "url": f"url{i}", "summary": f"Resumo {i}"}
                for i in range(min(max_results, 5))
            ],
            "total_found": max_results,
            "metadata": {
                "query": query,
                "sources": sources,
                "searched_at": datetime.now().isoformat()
            }
        }
        
        return result
    except Exception as e:
        return {
            "agent": "research", 
            "status": "error", 
            "error": str(e)
        }


@tool
async def transfer_to_specialist(
    agent_type: str,
    task_description: str,
    context: Dict[str, Any],
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Transfere tarefa para agente especialista.
    
    Args:
        agent_type: Tipo do agente especialista
        task_description: Descrição da tarefa
        context: Contexto para a tarefa
        priority: Prioridade da tarefa
    """
    return {
        "action": "transfer",
        "target_agent": agent_type,
        "task": task_description,
        "context": context,
        "priority": priority,
        "transfer_id": str(uuid.uuid4())
    }


# ==================== NODOS DO SUPERVISOR ====================

async def supervisor_node(state: SupervisorState, config: RunnableConfig) -> Command:
    """
    Nodo supervisor principal que decide qual ação tomar.
    """
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    # Log de início
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Analisando requisição do usuário",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Configurar modelo
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0.3,
        max_retries=2,
    )
    
    # Ferramentas disponíveis
    tools = [
        execute_post_generator,
        execute_stack_analyzer, 
        execute_research_agent,
        transfer_to_specialist
    ]
    
    # Prompt do supervisor
    system_prompt = """
    Você é um supervisor inteligente que coordena agentes especializados.
    
    Agentes disponíveis:
    - POST_GENERATOR: Gera posts para redes sociais (LinkedIn, Twitter)
    - STACK_ANALYZER: Analisa repositórios GitHub para identificar tecnologias
    - RESEARCH: Realiza pesquisas na web e fontes acadêmicas
    - CONTENT_OPTIMIZER: Otimiza conteúdo para SEO e engajamento
    
    Para cada requisição do usuário:
    1. Analise o tipo de tarefa solicitada
    2. Determine qual(is) agente(s) são necessários
    3. Execute as ferramentas apropriadas na ordem correta
    4. Coordene fluxos multi-agente quando necessário
    5. Agregue os resultados de forma coerente
    
    Sempre use as ferramentas disponíveis em vez de tentar responder diretamente.
    """
    
    # Obter última mensagem do usuário
    last_message = state.messages[-1].content if state.messages else "Olá"
    
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
    
    # Verificar se há tool calls
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return Command(
            goto="execute_tools",
            update={"messages": [response]}
        )
    else:
        # Resposta direta sem ferramentas
        return Command(
            goto="finalize",
            update={
                "messages": [response],
                "final_result": {"type": "direct_response", "content": response.content}
            }
        )


async def execute_tools_node(state: SupervisorState, config: RunnableConfig) -> Command:
    """
    Executa as ferramentas solicitadas pelo supervisor.
    """
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    results = []
    last_message = state.messages[-1] if state.messages else None
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            
            # Log da execução da ferramenta
            state.tool_logs.append({
                "id": str(uuid.uuid4()),
                "message": f"Executando {tool_name}",
                "status": "processing",
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "args": tool_args
            })
            await copilotkit_emit_state(config, state)
            
            try:
                # Executar ferramenta baseado no nome
                if tool_name == "execute_post_generator":
                    result = await execute_post_generator.ainvoke(tool_args)
                elif tool_name == "execute_stack_analyzer":
                    result = await execute_stack_analyzer.ainvoke(tool_args)
                elif tool_name == "execute_research_agent":
                    result = await execute_research_agent.ainvoke(tool_args)
                elif tool_name == "transfer_to_specialist":
                    result = await transfer_to_specialist.ainvoke(tool_args)
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
                
                results.append({
                    "tool": tool_name,
                    "result": result,
                    "success": True
                })
                
                # Atualizar log de sucesso
                state.tool_logs[-1]["status"] = "completed"
                state.tool_logs[-1]["result"] = result
                
            except Exception as e:
                results.append({
                    "tool": tool_name,
                    "error": str(e),
                    "success": False
                })
                
                # Atualizar log de erro
                state.tool_logs[-1]["status"] = "failed"
                state.tool_logs[-1]["error"] = str(e)
            
            await copilotkit_emit_state(config, state)
    
    # Compilar resultados finais
    aggregated_result = {
        "execution_summary": f"Executou {len(results)} ferramenta(s)",
        "tool_results": results,
        "success_count": sum(1 for r in results if r.get("success", False)),
        "total_tools": len(results)
    }
    
    return Command(
        goto="finalize",
        update={
            "final_result": aggregated_result,
            "execution_context": {"tool_execution_completed": True}
        }
    )


async def finalize_node(state: SupervisorState, config: RunnableConfig) -> Command:
    """
    Finaliza a execução e prepara resposta final.
    """
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True
    )
    
    # Log de finalização
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Finalizando processamento",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Gerar resposta final baseada nos resultados
    final_response = "Processamento concluído com sucesso!\n\n"
    
    if state.final_result.get("tool_results"):
        for tool_result in state.final_result["tool_results"]:
            if tool_result.get("success"):
                tool_name = tool_result["tool"]
                result_data = tool_result["result"]
                final_response += f"✅ {tool_name}: {result_data.get('status', 'success')}\n"
            else:
                tool_name = tool_result["tool"]
                error = tool_result.get("error", "Erro desconhecido")
                final_response += f"❌ {tool_name}: {error}\n"
    
    # Atualizar mensagens
    response_message = AIMessage(content=final_response)
    
    # Limpar logs
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(
        goto=END,
        update={
            "messages": [response_message]
        }
    )


# ==================== CRIAÇÃO DO GRAFO ====================

def create_supervisor_graph() -> StateGraph:
    """
    Cria o grafo do supervisor com padrão centralizado.
    """
    workflow = StateGraph(SupervisorState)
    
    # Adicionar nodos
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("execute_tools", execute_tools_node)
    workflow.add_node("finalize", finalize_node)
    
    # Definir entrada e saída
    workflow.set_entry_point("supervisor")
    workflow.set_finish_point("finalize")
    
    # Adicionar arestas
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("execute_tools", "finalize")
    workflow.add_edge("finalize", END)
    
    # Compilar com checkpoint
    return workflow.compile(checkpointer=MemorySaver())


# Instanciar o grafo principal
supervisor_graph = create_supervisor_graph()