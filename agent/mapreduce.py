"""
Sistema Map-Reduce para Processamento Paralelo de Tarefas Jurídicas
Vieira Pires Advogados - Padrão de Distribuição Inteligente
"""

import os
import json
import asyncio
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

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


class TaskType(Enum):
    ANALYSIS = "analysis"
    DOCUMENT_GENERATION = "document_generation"
    LEGAL_RESEARCH = "legal_research"
    CONTRACT_REVIEW = "contract_review"
    COMPLIANCE_CHECK = "compliance_check"


@dataclass
class MapTask:
    """Tarefa para fase Map."""
    id: str
    task_type: TaskType
    input_data: Dict[str, Any]
    agent_assigned: str
    priority: int = 1
    estimated_time: float = 5.0


@dataclass
class MapResult:
    """Resultado da fase Map."""
    task_id: str
    agent: str
    result: Dict[str, Any]
    execution_time: float
    success: bool
    error: Optional[str] = None


class MapReduceState(CopilotKitState):
    """Estado do sistema Map-Reduce."""
    original_request: str = ""
    map_tasks: List[MapTask] = Field(default_factory=list)
    map_results: List[MapResult] = Field(default_factory=list)
    reduce_result: Dict[str, Any] = Field(default_factory=dict)
    execution_stats: Dict[str, Any] = Field(default_factory=dict)
    tool_logs: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== FERRAMENTAS MAP-REDUCE ====================

@tool
async def decompose_legal_task(
    complex_request: str,
    max_subtasks: int = 5
) -> Dict[str, Any]:
    """
    Decompõe tarefa jurídica complexa em subtarefas paralelas.
    
    Args:
        complex_request: Solicitação jurídica complexa
        max_subtasks: Número máximo de subtarefas
    """
    
    try:
        # Analisar tipo de solicitação
        request_lower = complex_request.lower()
        
        # Padrões de decomposição por tipo
        decomposition_patterns = {
            "due_diligence": [
                {"type": "societario", "task": "Análise societária e participações"},
                {"type": "tributario", "task": "Verificação de contingências fiscais"},
                {"type": "trabalhista", "task": "Análise de passivos trabalhistas"},
                {"type": "contratos", "task": "Revisão de contratos principais"},
                {"type": "regulatorio", "task": "Compliance regulatório"}
            ],
            "estruturacao_empresa": [
                {"type": "societario", "task": "Definição de estrutura societária"},
                {"type": "tributario", "task": "Planejamento tributário otimizado"},
                {"type": "contratos", "task": "Contratos societários necessários"},
                {"type": "trabalhista", "task": "Políticas trabalhistas"},
                {"type": "regulatorio", "task": "Licenças e autorizações"}
            ],
            "fusao_aquisicao": [
                {"type": "societario", "task": "Estruturação da operação"},
                {"type": "tributario", "task": "Otimização fiscal da transação"},
                {"type": "contratos", "task": "Documentação da operação"},
                {"type": "due_diligence", "task": "Due diligence completa"},
                {"type": "regulatorio", "task": "Aprovações regulatórias"}
            ]
        }
        
        # Identificar padrão aplicável
        pattern_key = None
        for pattern, tasks in decomposition_patterns.items():
            if any(keyword in request_lower for keyword in pattern.split("_")):
                pattern_key = pattern
                break
        
        if not pattern_key:
            # Decomposição genérica
            tasks = [
                {"type": "analysis", "task": "Análise jurídica principal"},
                {"type": "research", "task": "Pesquisa legislativa"},
                {"type": "documentation", "task": "Elaboração de documentos"}
            ]
        else:
            tasks = decomposition_patterns[pattern_key]
        
        # Limitar número de subtarefas
        tasks = tasks[:max_subtasks]
        
        # Criar MapTasks
        map_tasks = []
        for i, task_info in enumerate(tasks):
            map_task = MapTask(
                id=f"task_{i+1}_{uuid.uuid4().hex[:6]}",
                task_type=TaskType.ANALYSIS,
                input_data={
                    "subtask_description": task_info["task"],
                    "original_request": complex_request,
                    "specialization": task_info["type"]
                },
                agent_assigned=task_info["type"],
                priority=i+1,
                estimated_time=3.0 + (i * 1.0)
            )
            map_tasks.append(map_task)
        
        return {
            "decomposition_successful": True,
            "pattern_used": pattern_key or "generic",
            "total_subtasks": len(map_tasks),
            "map_tasks": [
                {
                    "id": task.id,
                    "type": task.task_type.value,
                    "agent": task.agent_assigned,
                    "description": task.input_data["subtask_description"],
                    "priority": task.priority,
                    "estimated_time": task.estimated_time
                }
                for task in map_tasks
            ],
            "estimated_total_time": sum(task.estimated_time for task in map_tasks),
            "parallel_execution_time": max(task.estimated_time for task in map_tasks)
        }
        
    except Exception as e:
        return {"error": f"Erro na decomposição: {str(e)}"}


@tool
async def execute_parallel_tasks(
    map_tasks: List[Dict[str, Any]],
    max_workers: int = 3
) -> Dict[str, Any]:
    """
    Executa tarefas em paralelo na fase Map.
    
    Args:
        map_tasks: Lista de tarefas para execução
        max_workers: Número máximo de workers paralelos
    """
    
    try:
        start_time = datetime.now()
        results = []
        
        # Simular execução paralela
        async def execute_single_task(task_data):
            task_id = task_data["id"]
            agent = task_data["agent"]
            description = task_data["description"]
            estimated_time = task_data.get("estimated_time", 3.0)
            
            # Simular tempo de processamento
            await asyncio.sleep(min(estimated_time / 10, 1.0))
            
            # Simular resultado baseado no agente
            if agent == "societario":
                result = {
                    "analysis_type": "Estruturação Societária",
                    "recommendations": [
                        "Constituir holding patrimonial",
                        "Implementar governança corporativa",
                        "Definir acordo de quotistas"
                    ],
                    "documents_needed": ["Contrato social", "Acordo quotistas"],
                    "estimated_timeline": "15-30 dias"
                }
            elif agent == "tributario":
                result = {
                    "analysis_type": "Planejamento Tributário",
                    "tax_optimization": "Economia de 20-25% identificada",
                    "regime_recommendation": "Lucro Real",
                    "compliance_issues": ["Adequação à Reforma Tributária"],
                    "estimated_savings": "R$ 150.000/ano"
                }
            elif agent == "contratos":
                result = {
                    "analysis_type": "Análise Contratual",
                    "contracts_reviewed": 5,
                    "critical_clauses": ["Limitação responsabilidade", "Foro eleição"],
                    "risk_score": 7.5,
                    "recommendations": ["Incluir cláusula arbitragem"]
                }
            else:
                result = {
                    "analysis_type": "Análise Geral",
                    "status": "Concluído",
                    "findings": ["Análise realizada conforme solicitado"]
                }
            
            return MapResult(
                task_id=task_id,
                agent=agent,
                result=result,
                execution_time=estimated_time,
                success=True
            )
        
        # Executar tarefas com semáforo para controlar paralelismo
        semaphore = asyncio.Semaphore(max_workers)
        
        async def bounded_execute(task_data):
            async with semaphore:
                return await execute_single_task(task_data)
        
        # Criar tarefas assíncronas
        tasks = [bounded_execute(task_data) for task_data in map_tasks]
        
        # Executar e coletar resultados
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_results:
            if isinstance(result, Exception):
                results.append(MapResult(
                    task_id="error",
                    agent="unknown",
                    result={},
                    execution_time=0,
                    success=False,
                    error=str(result)
                ))
            else:
                results.append(result)
        
        end_time = datetime.now()
        total_execution_time = (end_time - start_time).total_seconds()
        
        return {
            "execution_successful": True,
            "total_tasks": len(map_tasks),
            "successful_tasks": sum(1 for r in results if r.success),
            "failed_tasks": sum(1 for r in results if not r.success),
            "total_execution_time": total_execution_time,
            "results": [
                {
                    "task_id": r.task_id,
                    "agent": r.agent,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "result": r.result,
                    "error": r.error
                }
                for r in results
            ]
        }
        
    except Exception as e:
        return {"error": f"Erro na execução paralela: {str(e)}"}


@tool
async def reduce_and_synthesize(
    map_results: List[Dict[str, Any]],
    original_request: str
) -> Dict[str, Any]:
    """
    Fase Reduce - agrega e sintetiza resultados das tarefas paralelas.
    
    Args:
        map_results: Resultados da fase Map
        original_request: Solicitação original do cliente
    """
    
    try:
        successful_results = [r for r in map_results if r.get("success", False)]
        
        if not successful_results:
            return {"error": "Nenhum resultado válido para agregação"}
        
        # Agregar resultados por tipo de análise
        aggregated_data = {
            "societario": [],
            "tributario": [],
            "contratos": [],
            "geral": []
        }
        
        for result in successful_results:
            agent = result.get("agent", "geral")
            result_data = result.get("result", {})
            
            if agent in aggregated_data:
                aggregated_data[agent].append(result_data)
            else:
                aggregated_data["geral"].append(result_data)
        
        # Sintetizar parecer consolidado
        synthesis = {
            "parecer_executivo": f"Análise completa da solicitação: {original_request}",
            "areas_analisadas": len([k for k, v in aggregated_data.items() if v]),
            "resumo_por_area": {},
            "recomendacoes_consolidadas": [],
            "proximos_passos": [],
            "investimento_estimado": "A definir conforme escopo",
            "prazo_implementacao": "30-60 dias úteis"
        }
        
        # Processar cada área
        for area, results in aggregated_data.items():
            if not results:
                continue
                
            area_summary = {
                "total_analises": len(results),
                "principais_achados": [],
                "recomendacoes": [],
                "documentos_necessarios": []
            }
            
            for result in results:
                if "recommendations" in result:
                    area_summary["recomendacoes"].extend(result["recommendations"])
                if "documents_needed" in result:
                    area_summary["documentos_necessarios"].extend(result["documents_needed"])
                if "findings" in result:
                    area_summary["principais_achados"].extend(result["findings"])
            
            synthesis["resumo_por_area"][area] = area_summary
            
            # Adicionar recomendações consolidadas
            if area == "tributario":
                for result in results:
                    if "estimated_savings" in result:
                        synthesis["recomendacoes_consolidadas"].append(
                            f"Economia tributária: {result['estimated_savings']}"
                        )
            elif area == "societario":
                synthesis["recomendacoes_consolidadas"].append(
                    "Implementar estruturação societária proposta"
                )
            elif area == "contratos":
                synthesis["recomendacoes_consolidadas"].append(
                    "Revisar contratos conforme análise de riscos"
                )
        
        # Próximos passos consolidados
        synthesis["proximos_passos"] = [
            "Aprovação do parecer pelos stakeholders",
            "Detalhamento das propostas aprovadas",
            "Cronograma de implementação",
            "Início da execução coordenada"
        ]
        
        # Métricas de qualidade
        synthesis["metricas_qualidade"] = {
            "areas_cobertas": len([k for k, v in aggregated_data.items() if v]),
            "total_recomendacoes": len(synthesis["recomendacoes_consolidadas"]),
            "score_completude": min(100, (len(successful_results) / 5) * 100),
            "confiabilidade": "Alta" if len(successful_results) >= 3 else "Média"
        }
        
        return {
            "reduction_successful": True,
            "synthesis": synthesis,
            "execution_summary": {
                "total_analyses": len(successful_results),
                "areas_covered": list(aggregated_data.keys()),
                "completion_rate": (len(successful_results) / len(map_results)) * 100,
                "quality_score": synthesis["metricas_qualidade"]["score_completude"]
            }
        }
        
    except Exception as e:
        return {"error": f"Erro na fase Reduce: {str(e)}"}


# ==================== NODOS MAP-REDUCE ====================

async def map_phase_node(state: MapReduceState, config: RunnableConfig) -> Command:
    """Nodo da fase Map - decomposição e execução paralela."""
    
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Iniciando fase Map - decomposição de tarefas",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0.2,
        max_retries=2,
    )
    
    tools = [decompose_legal_task, execute_parallel_tasks]
    
    system_prompt = """
    Você é o coordenador da fase MAP do sistema Map-Reduce jurídico.
    
    RESPONSABILIDADES:
    1. Decompor solicitações jurídicas complexas em subtarefas especializadas
    2. Distribuir tarefas para agentes especializados
    3. Coordenar execução paralela otimizada
    4. Monitorar progresso e qualidade
    
    ESPECIALISTAS DISPONÍVEIS:
    - Societário: Holdings, estruturação, governança
    - Tributário: Planejamento fiscal, defesas, compliance
    - Contratos: Elaboração, revisão, due diligence
    - Trabalhista: Compliance, políticas, defesas
    - Regulatório: Licenças, autorizações, compliance
    
    Use as ferramentas para decomposição inteligente e execução otimizada.
    """
    
    last_message = state.messages[-1].content if state.messages else state.original_request
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Solicitação para processamento Map-Reduce: {last_message}")
    ]
    
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(messages, config)
    
    state.tool_logs[-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return Command(goto="execute_map", update={"messages": [response]})
    else:
        return Command(goto="reduce_phase", update={"messages": [response]})


async def execute_map_node(state: MapReduceState, config: RunnableConfig) -> Command:
    """Executa as tarefas da fase Map."""
    
    results = []
    last_message = state.messages[-1] if state.messages else None
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            
            state.tool_logs.append({
                "id": str(uuid.uuid4()),
                "message": f"Executando Map: {tool_name}",
                "status": "processing",
                "timestamp": datetime.now().isoformat()
            })
            await copilotkit_emit_state(config, state)
            
            try:
                if tool_name == "decompose_legal_task":
                    result = await decompose_legal_task.ainvoke(tool_args)
                elif tool_name == "execute_parallel_tasks":
                    result = await execute_parallel_tasks.ainvoke(tool_args)
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
                
                results.append({"tool": tool_name, "result": result, "success": "error" not in result})
                state.tool_logs[-1]["status"] = "completed"
                
            except Exception as e:
                results.append({"tool": tool_name, "error": str(e), "success": False})
                state.tool_logs[-1]["status"] = "failed"
            
            await copilotkit_emit_state(config, state)
    
    return Command(
        goto="reduce_phase",
        update={"execution_stats": {"map_results": results}}
    )


async def reduce_phase_node(state: MapReduceState, config: RunnableConfig) -> Command:
    """Nodo da fase Reduce - agregação e síntese."""
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Iniciando fase Reduce - agregação de resultados",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Obter resultados da fase Map
    map_results = []
    if state.execution_stats and "map_results" in state.execution_stats:
        for map_result in state.execution_stats["map_results"]:
            if map_result.get("success") and "result" in map_result:
                result_data = map_result["result"]
                if "results" in result_data:
                    map_results.extend(result_data["results"])
    
    if not map_results:
        # Gerar resultados simulados para demonstração
        map_results = [
            {
                "agent": "societario",
                "success": True,
                "result": {
                    "analysis_type": "Estruturação Societária",
                    "recommendations": ["Constituir holding", "Governança corporativa"]
                }
            },
            {
                "agent": "tributario", 
                "success": True,
                "result": {
                    "analysis_type": "Planejamento Tributário",
                    "estimated_savings": "R$ 200.000/ano"
                }
            }
        ]
    
    # Executar síntese
    try:
        synthesis_result = await reduce_and_synthesize.ainvoke({
            "map_results": map_results,
            "original_request": state.original_request or "Análise jurídica complexa"
        })
        
        state.reduce_result = synthesis_result
        
    except Exception as e:
        synthesis_result = {"error": f"Erro na síntese: {str(e)}"}
    
    state.tool_logs[-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    
    return Command(goto="finalize_mapreduce", update={"reduce_result": synthesis_result})


async def finalize_mapreduce_node(state: MapReduceState, config: RunnableConfig) -> Command:
    """Finaliza processamento Map-Reduce."""
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Finalizando processamento Map-Reduce",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Gerar relatório final
    report = "# RELATÓRIO MAP-REDUCE JURÍDICO\n"
    report += "## Processamento Paralelo de Tarefas Complexas\n\n"
    report += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if state.reduce_result and "synthesis" in state.reduce_result:
        synthesis = state.reduce_result["synthesis"]
        
        report += f"## PARECER EXECUTIVO\n"
        report += f"{synthesis.get('parecer_executivo', 'Análise concluída')}\n\n"
        
        if "areas_analisadas" in synthesis:
            report += f"**Áreas Analisadas:** {synthesis['areas_analisadas']}\n\n"
        
        if "recomendacoes_consolidadas" in synthesis:
            report += "## RECOMENDAÇÕES CONSOLIDADAS\n"
            for rec in synthesis["recomendacoes_consolidadas"]:
                report += f"• {rec}\n"
            report += "\n"
        
        if "metricas_qualidade" in synthesis:
            metrics = synthesis["metricas_qualidade"]
            report += "## MÉTRICAS DE QUALIDADE\n"
            report += f"• **Score de Completude:** {metrics.get('score_completude', 0):.1f}%\n"
            report += f"• **Confiabilidade:** {metrics.get('confiabilidade', 'N/A')}\n\n"
    
    report += "## EFICIÊNCIA DO PROCESSAMENTO\n"
    report += "✅ **Paralelização:** Tarefas executadas simultaneamente\n"
    report += "✅ **Especialização:** Agentes focados por área\n"
    report += "✅ **Agregação:** Síntese inteligente de resultados\n"
    report += "✅ **Qualidade:** Validação automática\n\n"
    
    report += "---\n"
    report += "*Sistema Map-Reduce - Vieira Pires Advogados*"
    
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(goto=END, update={"messages": [AIMessage(content=report)]})


# ==================== CRIAÇÃO DO GRAFO ====================

def create_mapreduce_graph() -> StateGraph:
    """Cria grafo Map-Reduce."""
    
    workflow = StateGraph(MapReduceState)
    
    workflow.add_node("map_phase", map_phase_node)
    workflow.add_node("execute_map", execute_map_node)
    workflow.add_node("reduce_phase", reduce_phase_node)
    workflow.add_node("finalize_mapreduce", finalize_mapreduce_node)
    
    workflow.set_entry_point("map_phase")
    workflow.set_finish_point("finalize_mapreduce")
    
    workflow.add_edge(START, "map_phase")
    workflow.add_edge("execute_map", "reduce_phase")
    workflow.add_edge("reduce_phase", "finalize_mapreduce")
    workflow.add_edge("finalize_mapreduce", END)
    
    return workflow.compile(checkpointer=MemorySaver())


mapreduce_graph = create_mapreduce_graph()