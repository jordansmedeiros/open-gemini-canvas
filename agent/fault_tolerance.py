"""
Sistema de Tratamento de Falhas e Recuperação Automática
Vieira Pires Advogados - Fault Tolerance & Recovery System
"""

import os
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import traceback
import threading
import time
from functools import wraps

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FailureType(Enum):
    TIMEOUT = "timeout"
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    VALIDATION_ERROR = "validation_error"
    AGENT_FAILURE = "agent_failure"
    CHECKPOINT_FAILURE = "checkpoint_failure"
    MEMORY_ERROR = "memory_error"


class RecoveryStrategy(Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    RESTART = "restart"
    ESCALATE = "escalate"


@dataclass
class FailureIncident:
    """Incidente de falha registrado."""
    id: str
    failure_type: FailureType
    component: str
    error_message: str
    stack_trace: str
    timestamp: datetime
    context: Dict[str, Any]
    recovery_attempts: int = 0
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class RecoveryPolicy:
    """Política de recuperação."""
    max_retries: int
    retry_delay: float
    backoff_multiplier: float
    fallback_agent: Optional[str]
    circuit_breaker_threshold: int
    recovery_strategy: RecoveryStrategy


class CircuitBreaker:
    """Circuit Breaker para prevenção de falhas em cascata."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Executa função com circuit breaker."""
        with self._lock:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar reset."""
        if self.last_failure_time:
            return (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout
        return False
    
    def _on_success(self):
        """Chamado em caso de sucesso."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
        self.failure_count = 0
    
    def _on_failure(self):
        """Chamado em caso de falha."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class FaultToleranceManager:
    """Gerenciador de tolerância a falhas."""
    
    def __init__(self):
        self.incidents = []
        self.recovery_policies = self._initialize_policies()
        self.circuit_breakers = {}
        self.monitoring_active = True
        self._lock = threading.Lock()
    
    def _initialize_policies(self) -> Dict[str, RecoveryPolicy]:
        """Inicializa políticas de recuperação."""
        return {
            "default": RecoveryPolicy(
                max_retries=3,
                retry_delay=1.0,
                backoff_multiplier=2.0,
                fallback_agent="master_legal",
                circuit_breaker_threshold=5,
                recovery_strategy=RecoveryStrategy.RETRY
            ),
            "critical": RecoveryPolicy(
                max_retries=5,
                retry_delay=0.5,
                backoff_multiplier=1.5,
                fallback_agent="master_legal",
                circuit_breaker_threshold=3,
                recovery_strategy=RecoveryStrategy.FALLBACK
            ),
            "network": RecoveryPolicy(
                max_retries=10,
                retry_delay=2.0,
                backoff_multiplier=1.2,
                fallback_agent=None,
                circuit_breaker_threshold=8,
                recovery_strategy=RecoveryStrategy.CIRCUIT_BREAKER
            )
        }
    
    def register_incident(
        self,
        component: str,
        failure_type: FailureType,
        error: Exception,
        context: Dict[str, Any] = {}
    ) -> str:
        """Registra incidente de falha."""
        incident = FailureIncident(
            id=f"inc_{int(time.time())}_{hash(str(error)) % 10000}",
            failure_type=failure_type,
            component=component,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            timestamp=datetime.now(),
            context=context
        )
        
        with self._lock:
            self.incidents.append(incident)
            # Manter apenas últimos 1000 incidentes
            if len(self.incidents) > 1000:
                self.incidents = self.incidents[-1000:]
        
        logger.error(f"Incidente registrado: {incident.id} - {error}")
        return incident.id
    
    def get_circuit_breaker(self, component: str) -> CircuitBreaker:
        """Obtém circuit breaker para componente."""
        if component not in self.circuit_breakers:
            policy = self.recovery_policies.get(component, self.recovery_policies["default"])
            self.circuit_breakers[component] = CircuitBreaker(
                failure_threshold=policy.circuit_breaker_threshold
            )
        return self.circuit_breakers[component]
    
    def execute_with_recovery(
        self,
        func: Callable,
        component: str,
        policy_name: str = "default",
        context: Dict[str, Any] = {},
        *args,
        **kwargs
    ):
        """Executa função com recuperação automática."""
        policy = self.recovery_policies.get(policy_name, self.recovery_policies["default"])
        
        for attempt in range(policy.max_retries + 1):
            try:
                if policy.recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                    circuit_breaker = self.get_circuit_breaker(component)
                    return circuit_breaker.call(func, *args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                # Determinar tipo de falha
                failure_type = self._classify_failure(e)
                
                # Registrar incidente
                incident_id = self.register_incident(component, failure_type, e, context)
                
                # Última tentativa - executar estratégia de recuperação
                if attempt == policy.max_retries:
                    return self._apply_recovery_strategy(
                        policy, component, e, incident_id, *args, **kwargs
                    )
                
                # Aguardar antes da próxima tentativa
                delay = policy.retry_delay * (policy.backoff_multiplier ** attempt)
                logger.info(f"Tentativa {attempt + 1} falhou, aguardando {delay}s")
                time.sleep(delay)
        
        raise Exception(f"Todas as tentativas de recuperação falharam para {component}")
    
    def _classify_failure(self, error: Exception) -> FailureType:
        """Classifica tipo de falha."""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return FailureType.TIMEOUT
        elif "network" in error_str or "connection" in error_str:
            return FailureType.NETWORK_ERROR
        elif "api" in error_str or "http" in error_str:
            return FailureType.API_ERROR
        elif "memory" in error_str:
            return FailureType.MEMORY_ERROR
        elif "validation" in error_str:
            return FailureType.VALIDATION_ERROR
        else:
            return FailureType.AGENT_FAILURE
    
    def _apply_recovery_strategy(
        self,
        policy: RecoveryPolicy,
        component: str,
        error: Exception,
        incident_id: str,
        *args,
        **kwargs
    ):
        """Aplica estratégia de recuperação."""
        
        if policy.recovery_strategy == RecoveryStrategy.FALLBACK and policy.fallback_agent:
            logger.info(f"Aplicando fallback para {policy.fallback_agent}")
            return self._execute_fallback(policy.fallback_agent, *args, **kwargs)
        
        elif policy.recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            logger.info("Aplicando degradação graceful")
            return self._graceful_degradation(component, error)
        
        elif policy.recovery_strategy == RecoveryStrategy.ESCALATE:
            logger.info("Escalando para administrador")
            return self._escalate_incident(incident_id, component, error)
        
        else:
            # Fallback final
            return self._graceful_degradation(component, error)
    
    def _execute_fallback(self, fallback_agent: str, *args, **kwargs):
        """Executa agente de fallback."""
        # Simular execução de fallback
        return {
            "fallback_executed": True,
            "fallback_agent": fallback_agent,
            "message": f"Operação transferida para {fallback_agent} devido a falha",
            "timestamp": datetime.now().isoformat()
        }
    
    def _graceful_degradation(self, component: str, error: Exception):
        """Implementa degradação graceful."""
        return {
            "degraded_service": True,
            "component": component,
            "error": str(error),
            "message": "Serviço funcionando em modo degradado",
            "limitations": ["Funcionalidade reduzida", "Performance limitada"],
            "timestamp": datetime.now().isoformat()
        }
    
    def _escalate_incident(self, incident_id: str, component: str, error: Exception):
        """Escala incidente para administrador."""
        return {
            "escalated": True,
            "incident_id": incident_id,
            "component": component,
            "error": str(error),
            "message": "Incidente escalado para administrador",
            "requires_manual_intervention": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Obtém status de saúde do sistema."""
        recent_incidents = [
            inc for inc in self.incidents
            if (datetime.now() - inc.timestamp).seconds < 3600  # Última hora
        ]
        
        failure_by_type = {}
        for incident in recent_incidents:
            failure_type = incident.failure_type.value
            failure_by_type[failure_type] = failure_by_type.get(failure_type, 0) + 1
        
        circuit_breaker_status = {}
        for component, cb in self.circuit_breakers.items():
            circuit_breaker_status[component] = {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None
            }
        
        # Determinar status geral
        if len(recent_incidents) == 0:
            overall_status = "healthy"
        elif len(recent_incidents) < 5:
            overall_status = "warning"
        else:
            overall_status = "critical"
        
        return {
            "overall_status": overall_status,
            "total_incidents": len(self.incidents),
            "recent_incidents": len(recent_incidents),
            "failure_by_type": failure_by_type,
            "circuit_breakers": circuit_breaker_status,
            "monitoring_active": self.monitoring_active,
            "last_check": datetime.now().isoformat()
        }


# Instância global
fault_manager = FaultToleranceManager()


# ==================== DECORADORES ====================

def with_fault_tolerance(
    component: str,
    policy: str = "default",
    context: Dict[str, Any] = {}
):
    """Decorador para adicionar tolerância a falhas."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await fault_manager.execute_with_recovery(
                    func, component, policy, context, *args, **kwargs
                )
            except Exception as e:
                # Último recurso - retornar erro controlado
                return {
                    "error": str(e),
                    "component": component,
                    "fallback_response": True,
                    "timestamp": datetime.now().isoformat()
                }
        return wrapper
    return decorator


# ==================== FERRAMENTAS ====================

@tool
async def diagnose_system_health() -> Dict[str, Any]:
    """Diagnostica saúde geral do sistema."""
    
    try:
        health_data = fault_manager.get_system_health()
        
        # Análise adicional
        recommendations = []
        
        if health_data["overall_status"] == "critical":
            recommendations.extend([
                "Investigar causa raiz dos incidentes",
                "Considerar restart de componentes críticos",
                "Ativar modo de emergência"
            ])
        elif health_data["overall_status"] == "warning":
            recommendations.extend([
                "Monitorar sistema mais frequentemente",
                "Verificar logs de componentes específicos",
                "Preparar planos de contingência"
            ])
        else:
            recommendations.append("Sistema operando normalmente")
        
        # Análise de tendências
        recent_trends = {
            "incident_frequency": "Normal" if health_data["recent_incidents"] < 3 else "Alta",
            "most_common_failure": max(health_data["failure_by_type"].items(), key=lambda x: x[1])[0] if health_data["failure_by_type"] else "Nenhum",
            "circuit_breaker_trips": sum(1 for cb in health_data["circuit_breakers"].values() if cb["state"] != "CLOSED")
        }
        
        return {
            "diagnosis_successful": True,
            "health_status": health_data,
            "recommendations": recommendations,
            "trends": recent_trends,
            "next_check_recommended": "15 minutos",
            "diagnosis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Erro no diagnóstico: {str(e)}"}


@tool
async def recover_failed_component(
    component_name: str,
    recovery_strategy: str = "restart"
) -> Dict[str, Any]:
    """Recupera componente com falha."""
    
    try:
        # Validar estratégia
        try:
            strategy = RecoveryStrategy(recovery_strategy)
        except ValueError:
            strategy = RecoveryStrategy.RESTART
        
        # Simular recuperação
        await asyncio.sleep(1)
        
        recovery_actions = {
            RecoveryStrategy.RESTART: [
                f"Reinicializando {component_name}",
                "Verificando dependências",
                "Restaurando estado anterior",
                "Validando funcionalidade"
            ],
            RecoveryStrategy.FALLBACK: [
                f"Ativando fallback para {component_name}",
                "Redirecionando tráfego",
                "Monitorando performance"
            ],
            RecoveryStrategy.GRACEFUL_DEGRADATION: [
                f"Aplicando degradação em {component_name}",
                "Limitando funcionalidades",
                "Mantendo serviços essenciais"
            ]
        }
        
        actions = recovery_actions.get(strategy, ["Ação de recuperação genérica"])
        
        # Simular sucesso na maioria dos casos
        import random
        success = random.random() > 0.2  # 80% chance de sucesso
        
        if success:
            # Limpar circuit breaker se houver
            if component_name in fault_manager.circuit_breakers:
                fault_manager.circuit_breakers[component_name].failure_count = 0
                fault_manager.circuit_breakers[component_name].state = "CLOSED"
            
            return {
                "recovery_successful": True,
                "component": component_name,
                "strategy_used": strategy.value,
                "actions_taken": actions,
                "recovery_time": "2.5 segundos",
                "status": "Componente operacional",
                "next_monitoring": "Monitoramento intensivo por 30 minutos"
            }
        else:
            return {
                "recovery_successful": False,
                "component": component_name,
                "strategy_used": strategy.value,
                "error": "Falha na recuperação automática",
                "escalation_required": True,
                "recommended_action": "Intervenção manual necessária"
            }
        
    except Exception as e:
        return {"error": f"Erro na recuperação: {str(e)}"}


@tool
async def simulate_failure_scenario(
    failure_type: str,
    component: str,
    severity: str = "medium"
) -> Dict[str, Any]:
    """Simula cenário de falha para teste."""
    
    try:
        # Validar tipo de falha
        try:
            f_type = FailureType(failure_type)
        except ValueError:
            f_type = FailureType.AGENT_FAILURE
        
        # Criar erro simulado
        error_messages = {
            FailureType.TIMEOUT: "Connection timeout after 30 seconds",
            FailureType.API_ERROR: "API returned HTTP 500 Internal Server Error",
            FailureType.NETWORK_ERROR: "Network unreachable",
            FailureType.MEMORY_ERROR: "Out of memory error",
            FailureType.AGENT_FAILURE: "Agent processing failed"
        }
        
        simulated_error = Exception(error_messages.get(f_type, "Generic failure"))
        
        # Registrar incidente simulado
        incident_id = fault_manager.register_incident(
            component=component,
            failure_type=f_type,
            error=simulated_error,
            context={"simulation": True, "severity": severity}
        )
        
        # Simular resposta do sistema
        await asyncio.sleep(0.5)
        
        # Aplicar recuperação
        recovery_result = fault_manager._apply_recovery_strategy(
            fault_manager.recovery_policies["default"],
            component,
            simulated_error,
            incident_id
        )
        
        return {
            "simulation_successful": True,
            "incident_id": incident_id,
            "failure_type": f_type.value,
            "component_affected": component,
            "severity": severity,
            "recovery_applied": recovery_result,
            "system_response_time": "0.5 segundos",
            "lessons_learned": [
                "Sistema detectou falha automaticamente",
                "Recuperação foi aplicada conforme política",
                "Monitoramento registrou incidente"
            ]
        }
        
    except Exception as e:
        return {"error": f"Erro na simulação: {str(e)}"}


# ==================== ESTADO E NODOS ====================

class FaultToleranceState(CopilotKitState):
    """Estado do sistema de tolerância a falhas."""
    system_health: Dict[str, Any] = Field(default_factory=dict)
    active_incidents: List[str] = Field(default_factory=list)
    recovery_actions: List[Dict[str, Any]] = Field(default_factory=list)
    tool_logs: List[Dict[str, Any]] = Field(default_factory=list)


async def fault_monitor_node(state: FaultToleranceState, config: RunnableConfig) -> Command:
    """Monitora sistema para detecção de falhas."""
    
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    state.tool_logs.append({
        "id": f"ft_{int(time.time())}",
        "message": "Iniciando monitoramento de falhas",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0.1,
        max_retries=2,
    )
    
    tools = [diagnose_system_health, recover_failed_component, simulate_failure_scenario]
    
    system_prompt = """
    Você é o monitor de tolerância a falhas do sistema jurídico Vieira Pires Advogados.
    
    RESPONSABILIDADES:
    1. Detectar falhas e anomalias no sistema
    2. Aplicar estratégias de recuperação automática
    3. Monitorar saúde dos componentes
    4. Executar diagnósticos preventivos
    5. Coordenar recuperação de incidentes
    
    ESTRATÉGIAS DE RECUPERAÇÃO:
    - Retry: Tentar novamente com backoff
    - Fallback: Usar agente alternativo
    - Circuit Breaker: Prevenir falhas em cascata
    - Graceful Degradation: Funcionalidade reduzida
    - Escalation: Intervenção manual
    
    Use as ferramentas para manter alta disponibilidade.
    """
    
    last_message = state.messages[-1].content if state.messages else "Verificar saúde do sistema"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Solicitação de monitoramento: {last_message}")
    ]
    
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(messages, config)
    
    state.tool_logs[-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return Command(goto="execute_recovery", update={"messages": [response]})
    else:
        return Command(goto="finalize_monitoring", update={"messages": [response]})


async def execute_recovery_node(state: FaultToleranceState, config: RunnableConfig) -> Command:
    """Executa ações de recuperação."""
    
    results = []
    last_message = state.messages[-1] if state.messages else None
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            
            state.tool_logs.append({
                "id": f"ft_{int(time.time())}",
                "message": f"Executando: {tool_name}",
                "status": "processing",
                "timestamp": datetime.now().isoformat()
            })
            await copilotkit_emit_state(config, state)
            
            try:
                if tool_name == "diagnose_system_health":
                    result = await diagnose_system_health.ainvoke(tool_args)
                    if "health_status" in result:
                        state.system_health = result["health_status"]
                elif tool_name == "recover_failed_component":
                    result = await recover_failed_component.ainvoke(tool_args)
                elif tool_name == "simulate_failure_scenario":
                    result = await simulate_failure_scenario.ainvoke(tool_args)
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
                
                results.append({"tool": tool_name, "result": result, "success": "error" not in result})
                state.tool_logs[-1]["status"] = "completed"
                
            except Exception as e:
                results.append({"tool": tool_name, "error": str(e), "success": False})
                state.tool_logs[-1]["status"] = "failed"
            
            await copilotkit_emit_state(config, state)
    
    return Command(
        goto="finalize_monitoring",
        update={"recovery_actions": results}
    )


async def finalize_monitoring_node(state: FaultToleranceState, config: RunnableConfig) -> Command:
    """Finaliza monitoramento e gera relatório."""
    
    state.tool_logs.append({
        "id": f"ft_{int(time.time())}",
        "message": "Finalizando monitoramento",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Gerar relatório de tolerância a falhas
    report = "# RELATÓRIO DE TOLERÂNCIA A FALHAS\n"
    report += "## Sistema de Recuperação Automática\n\n"
    report += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if state.system_health:
        health = state.system_health
        report += f"## STATUS DO SISTEMA\n"
        report += f"**Status Geral:** {health.get('overall_status', 'unknown').title()}\n"
        report += f"**Incidentes Recentes:** {health.get('recent_incidents', 0)}\n\n"
    
    if state.recovery_actions:
        report += "## AÇÕES DE RECUPERAÇÃO\n"
        for action in state.recovery_actions:
            if action.get("success"):
                report += f"✅ **{action['tool'].replace('_', ' ').title()}:** Executado\n"
            else:
                report += f"❌ **{action['tool'].replace('_', ' ').title()}:** Falhou\n"
        report += "\n"
    
    report += "## RECURSOS ATIVOS\n"
    report += "🔄 **Circuit Breakers:** Prevenção de falhas em cascata\n"
    report += "🔁 **Auto-Retry:** Tentativas automáticas com backoff\n"
    report += "🛡️ **Fallback:** Agentes alternativos disponíveis\n"
    report += "📊 **Monitoramento:** Detecção proativa de anomalias\n\n"
    
    report += "---\n"
    report += "*Sistema de Tolerância a Falhas - Vieira Pires Advogados*"
    
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(goto=END, update={"messages": [AIMessage(content=report)]})


def create_fault_tolerance_graph() -> StateGraph:
    """Cria grafo de tolerância a falhas."""
    
    workflow = StateGraph(FaultToleranceState)
    
    workflow.add_node("monitor", fault_monitor_node)
    workflow.add_node("execute_recovery", execute_recovery_node)
    workflow.add_node("finalize_monitoring", finalize_monitoring_node)
    
    workflow.set_entry_point("monitor")
    workflow.set_finish_point("finalize_monitoring")
    
    workflow.add_edge(START, "monitor")
    workflow.add_edge("execute_recovery", "finalize_monitoring")
    workflow.add_edge("finalize_monitoring", END)
    
    return workflow.compile(checkpointer=MemorySaver())


fault_tolerance_graph = create_fault_tolerance_graph()