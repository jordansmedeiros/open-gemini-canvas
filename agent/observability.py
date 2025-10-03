"""
Sistema de Debugging e Observabilidade
Este módulo implementa observabilidade avançada para agentes LangGraph com integração LangSmith.
"""

import os
import json
import time
import uuid
import asyncio
import traceback
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import contextmanager, asynccontextmanager
from functools import wraps
import logging
import threading
from collections import defaultdict, deque

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from pydantic import BaseModel, Field

try:
    from langsmith import Client as LangSmithClient
    from langsmith.run_helpers import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    traceable = lambda func: func  # Fallback decorator

load_dotenv()

# ==================== CONFIGURAÇÃO ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== ENUMS E TIPOS ====================

class TraceLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    NODE_ENTER = "node_enter"
    NODE_EXIT = "node_exit"
    TOOL_CALL = "tool_call"
    LLM_CALL = "llm_call"
    ERROR = "error"
    CHECKPOINT = "checkpoint"
    HANDOFF = "handoff"
    STATE_UPDATE = "state_update"


class MetricType(Enum):
    LATENCY = "latency"
    TOKEN_COUNT = "token_count"
    COST = "cost"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"


# ==================== MODELOS DE DADOS ====================

@dataclass
class TraceEvent:
    """Evento de trace."""
    id: str
    trace_id: str
    parent_id: Optional[str]
    event_type: EventType
    timestamp: datetime
    level: TraceLevel
    agent_name: str
    node_name: Optional[str]
    message: str
    data: Dict[str, Any]
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['event_type'] = self.event_type.value
        result['level'] = self.level.value
        return result


@dataclass
class PerformanceMetric:
    """Métrica de performance."""
    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    agent_name: str
    node_name: Optional[str] = None
    session_id: Optional[str] = None
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['metric_type'] = self.metric_type.value
        return result


class ObservabilityConfig(BaseModel):
    """Configuração de observabilidade."""
    langsmith_enabled: bool = True
    langsmith_project_name: str = "open-gemini-canvas"
    trace_level: TraceLevel = TraceLevel.INFO
    max_trace_events: int = 10000
    max_metrics: int = 50000
    enable_performance_monitoring: bool = True
    enable_error_tracking: bool = True
    enable_state_tracking: bool = True
    enable_cost_tracking: bool = True
    flush_interval_seconds: int = 30
    retention_days: int = 7


# ==================== LANGSMITH INTEGRATION ====================

class LangSmithIntegration:
    """Integração com LangSmith para observabilidade."""
    
    def __init__(self, config: ObservabilityConfig):
        self.config = config
        self.client = None
        
        if LANGSMITH_AVAILABLE and config.langsmith_enabled:
            try:
                self.client = LangSmithClient()
                logger.info("LangSmith integração inicializada")
            except Exception as e:
                logger.warning(f"Falha ao inicializar LangSmith: {e}")
    
    def trace_agent_execution(self, agent_name: str, run_id: str):
        """Cria trace para execução de agente."""
        if not self.client:
            return self._mock_tracer(agent_name, run_id)
        
        @traceable(
            run_type="agent",
            project_name=self.config.langsmith_project_name,
            name=agent_name
        )
        def traced_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return inputs
        
        return traced_execution
    
    def _mock_tracer(self, agent_name: str, run_id: str):
        """Tracer mock quando LangSmith não está disponível."""
        def mock_traced_execution(inputs: Dict[str, Any]) -> Dict[str, Any]:
            logger.debug(f"Mock trace: {agent_name} - {run_id}")
            return inputs
        return mock_traced_execution


# ==================== CALLBACK HANDLER ====================

class ObservabilityCallbackHandler(BaseCallbackHandler):
    """Callback handler para capturar eventos de LangChain."""
    
    def __init__(self, observability_manager: 'ObservabilityManager'):
        self.manager = observability_manager
        self.run_stack = []
    
    def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """Início de chamada LLM."""
        run_id = kwargs.get('run_id', str(uuid.uuid4()))
        
        event = TraceEvent(
            id=str(uuid.uuid4()),
            trace_id=self.manager.current_trace_id,
            parent_id=self.run_stack[-1] if self.run_stack else None,
            event_type=EventType.LLM_CALL,
            timestamp=datetime.now(),
            level=TraceLevel.INFO,
            agent_name=self.manager.current_agent_name,
            node_name=self.manager.current_node_name,
            message="LLM call started",
            data={
                "model": serialized.get("name", "unknown"),
                "prompts": prompts[:2],  # Primeiros 2 prompts para debug
                "prompt_length": sum(len(p) for p in prompts)
            }
        )
        
        self.manager.add_trace_event(event)
        self.run_stack.append(run_id)
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Fim de chamada LLM."""
        if self.run_stack:
            self.run_stack.pop()
        
        # Extrair tokens se disponível
        token_usage = getattr(response, 'llm_output', {}).get('token_usage', {})
        
        event = TraceEvent(
            id=str(uuid.uuid4()),
            trace_id=self.manager.current_trace_id,
            parent_id=self.run_stack[-1] if self.run_stack else None,
            event_type=EventType.LLM_CALL,
            timestamp=datetime.now(),
            level=TraceLevel.INFO,
            agent_name=self.manager.current_agent_name,
            node_name=self.manager.current_node_name,
            message="LLM call completed",
            data={
                "generations_count": len(response.generations),
                "token_usage": token_usage
            }
        )
        
        self.manager.add_trace_event(event)
        
        # Adicionar métricas de tokens
        if token_usage:
            self.manager.add_metric(PerformanceMetric(
                name="llm_tokens_total",
                metric_type=MetricType.TOKEN_COUNT,
                value=token_usage.get('total_tokens', 0),
                unit="tokens",
                timestamp=datetime.now(),
                agent_name=self.manager.current_agent_name,
                node_name=self.manager.current_node_name
            ))
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Erro em chamada LLM."""
        if self.run_stack:
            self.run_stack.pop()
        
        event = TraceEvent(
            id=str(uuid.uuid4()),
            trace_id=self.manager.current_trace_id,
            parent_id=self.run_stack[-1] if self.run_stack else None,
            event_type=EventType.ERROR,
            timestamp=datetime.now(),
            level=TraceLevel.ERROR,
            agent_name=self.manager.current_agent_name,
            node_name=self.manager.current_node_name,
            message=f"LLM error: {str(error)}",
            data={"error_type": type(error).__name__},
            error=str(error),
            stack_trace=traceback.format_exc()
        )
        
        self.manager.add_trace_event(event)


# ==================== PERFORMANCE MONITOR ====================

class PerformanceMonitor:
    """Monitor de performance para agentes."""
    
    def __init__(self):
        self.metrics = deque(maxlen=50000)
        self.aggregated_metrics = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_latency(
        self, 
        operation: str, 
        duration_ms: float, 
        agent_name: str, 
        node_name: str = None
    ):
        """Registra latência de operação."""
        metric = PerformanceMetric(
            name=f"{operation}_latency",
            metric_type=MetricType.LATENCY,
            value=duration_ms,
            unit="ms",
            timestamp=datetime.now(),
            agent_name=agent_name,
            node_name=node_name
        )
        
        with self._lock:
            self.metrics.append(metric)
            self.aggregated_metrics[f"{agent_name}_{operation}"].append(duration_ms)
    
    def record_token_usage(
        self, 
        tokens: int, 
        agent_name: str, 
        node_name: str = None
    ):
        """Registra uso de tokens."""
        metric = PerformanceMetric(
            name="token_usage",
            metric_type=MetricType.TOKEN_COUNT,
            value=tokens,
            unit="tokens",
            timestamp=datetime.now(),
            agent_name=agent_name,
            node_name=node_name
        )
        
        with self._lock:
            self.metrics.append(metric)
    
    def get_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Obtém resumo de métricas."""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            recent_metrics = [
                m for m in self.metrics 
                if m.timestamp > cutoff_time
            ]
        
        if not recent_metrics:
            return {"message": "Nenhuma métrica no período"}
        
        # Agrupar por tipo
        by_type = defaultdict(list)
        for metric in recent_metrics:
            by_type[metric.metric_type].append(metric.value)
        
        # Calcular estatísticas
        summary = {}
        for metric_type, values in by_type.items():
            if values:
                summary[metric_type.value] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "total": sum(values)
                }
        
        return summary


# ==================== OBSERVABILITY MANAGER ====================

class ObservabilityManager:
    """Gerenciador principal de observabilidade."""
    
    def __init__(self, config: ObservabilityConfig = None):
        self.config = config or ObservabilityConfig()
        self.trace_events = deque(maxlen=self.config.max_trace_events)
        self.performance_monitor = PerformanceMonitor()
        self.langsmith_integration = LangSmithIntegration(self.config)
        self.callback_handler = ObservabilityCallbackHandler(self)
        
        # Estado atual
        self.current_trace_id = None
        self.current_agent_name = "unknown"
        self.current_node_name = None
        self.active_sessions = {}
        
        # Locks para thread safety
        self._trace_lock = threading.Lock()
        self._session_lock = threading.Lock()
        
        # Iniciar flush automático
        self._start_auto_flush()
    
    def start_trace(self, agent_name: str, session_id: str = None) -> str:
        """Inicia um novo trace."""
        trace_id = str(uuid.uuid4())
        
        with self._session_lock:
            self.current_trace_id = trace_id
            self.current_agent_name = agent_name
            
            session_info = {
                "trace_id": trace_id,
                "agent_name": agent_name,
                "start_time": datetime.now(),
                "session_id": session_id or trace_id
            }
            self.active_sessions[trace_id] = session_info
        
        # Criar evento de início
        event = TraceEvent(
            id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_id=None,
            event_type=EventType.AGENT_START,
            timestamp=datetime.now(),
            level=TraceLevel.INFO,
            agent_name=agent_name,
            node_name=None,
            message=f"Agent {agent_name} started",
            data={"session_id": session_id}
        )
        
        self.add_trace_event(event)
        logger.info(f"Trace iniciado: {trace_id} para agente {agent_name}")
        
        return trace_id
    
    def end_trace(self, trace_id: str = None):
        """Finaliza um trace."""
        target_trace_id = trace_id or self.current_trace_id
        
        if not target_trace_id:
            return
        
        with self._session_lock:
            session_info = self.active_sessions.get(target_trace_id)
            if session_info:
                duration = (datetime.now() - session_info["start_time"]).total_seconds() * 1000
                
                # Criar evento de fim
                event = TraceEvent(
                    id=str(uuid.uuid4()),
                    trace_id=target_trace_id,
                    parent_id=None,
                    event_type=EventType.AGENT_END,
                    timestamp=datetime.now(),
                    level=TraceLevel.INFO,
                    agent_name=session_info["agent_name"],
                    node_name=None,
                    message=f"Agent {session_info['agent_name']} completed",
                    data={"duration_ms": duration},
                    duration_ms=duration
                )
                
                self.add_trace_event(event)
                
                # Remover sessão ativa
                del self.active_sessions[target_trace_id]
                
                if target_trace_id == self.current_trace_id:
                    self.current_trace_id = None
                    self.current_agent_name = "unknown"
                    self.current_node_name = None
                
                logger.info(f"Trace finalizado: {target_trace_id} ({duration:.2f}ms)")
    
    @contextmanager
    def trace_node(self, node_name: str):
        """Context manager para trace de nodo."""
        old_node_name = self.current_node_name
        self.current_node_name = node_name
        start_time = time.time()
        
        # Evento de entrada no nodo
        enter_event = TraceEvent(
            id=str(uuid.uuid4()),
            trace_id=self.current_trace_id,
            parent_id=None,
            event_type=EventType.NODE_ENTER,
            timestamp=datetime.now(),
            level=TraceLevel.DEBUG,
            agent_name=self.current_agent_name,
            node_name=node_name,
            message=f"Entering node {node_name}",
            data={}
        )
        self.add_trace_event(enter_event)
        
        try:
            yield
        except Exception as e:
            # Registrar erro
            error_event = TraceEvent(
                id=str(uuid.uuid4()),
                trace_id=self.current_trace_id,
                parent_id=None,
                event_type=EventType.ERROR,
                timestamp=datetime.now(),
                level=TraceLevel.ERROR,
                agent_name=self.current_agent_name,
                node_name=node_name,
                message=f"Error in node {node_name}: {str(e)}",
                data={"error_type": type(e).__name__},
                error=str(e),
                stack_trace=traceback.format_exc()
            )
            self.add_trace_event(error_event)
            raise
        finally:
            # Evento de saída do nodo
            duration_ms = (time.time() - start_time) * 1000
            
            exit_event = TraceEvent(
                id=str(uuid.uuid4()),
                trace_id=self.current_trace_id,
                parent_id=None,
                event_type=EventType.NODE_EXIT,
                timestamp=datetime.now(),
                level=TraceLevel.DEBUG,
                agent_name=self.current_agent_name,
                node_name=node_name,
                message=f"Exiting node {node_name}",
                data={},
                duration_ms=duration_ms
            )
            self.add_trace_event(exit_event)
            
            # Registrar métrica de latência
            self.performance_monitor.record_latency(
                f"node_{node_name}",
                duration_ms,
                self.current_agent_name,
                node_name
            )
            
            self.current_node_name = old_node_name
    
    def add_trace_event(self, event: TraceEvent):
        """Adiciona evento de trace."""
        if event.level.value not in [l.value for l in [self.config.trace_level] + 
                                    [TraceLevel.WARNING, TraceLevel.ERROR, TraceLevel.CRITICAL]]:
            return
        
        with self._trace_lock:
            self.trace_events.append(event)
    
    def add_metric(self, metric: PerformanceMetric):
        """Adiciona métrica de performance."""
        self.performance_monitor.metrics.append(metric)
    
    def log_tool_call(
        self, 
        tool_name: str, 
        args: Dict[str, Any], 
        result: Any = None, 
        error: Exception = None
    ):
        """Registra chamada de ferramenta."""
        level = TraceLevel.ERROR if error else TraceLevel.INFO
        message = f"Tool call: {tool_name}"
        
        if error:
            message += f" - Error: {str(error)}"
        
        event = TraceEvent(
            id=str(uuid.uuid4()),
            trace_id=self.current_trace_id,
            parent_id=None,
            event_type=EventType.TOOL_CALL,
            timestamp=datetime.now(),
            level=level,
            agent_name=self.current_agent_name,
            node_name=self.current_node_name,
            message=message,
            data={
                "tool_name": tool_name,
                "args": args,
                "result_type": type(result).__name__ if result else None,
                "success": error is None
            },
            error=str(error) if error else None,
            stack_trace=traceback.format_exc() if error else None
        )
        
        self.add_trace_event(event)
    
    def log_state_update(self, old_state: Dict[str, Any], new_state: Dict[str, Any]):
        """Registra atualização de estado."""
        if not self.config.enable_state_tracking:
            return
        
        # Calcular diff simplificado
        changed_keys = []
        for key in set(old_state.keys()) | set(new_state.keys()):
            if old_state.get(key) != new_state.get(key):
                changed_keys.append(key)
        
        event = TraceEvent(
            id=str(uuid.uuid4()),
            trace_id=self.current_trace_id,
            parent_id=None,
            event_type=EventType.STATE_UPDATE,
            timestamp=datetime.now(),
            level=TraceLevel.DEBUG,
            agent_name=self.current_agent_name,
            node_name=self.current_node_name,
            message=f"State updated: {len(changed_keys)} keys changed",
            data={
                "changed_keys": changed_keys,
                "state_size": len(new_state)
            }
        )
        
        self.add_trace_event(event)
    
    def get_trace_summary(self, trace_id: str = None) -> Dict[str, Any]:
        """Obtém resumo de um trace."""
        target_trace_id = trace_id or self.current_trace_id
        
        if not target_trace_id:
            return {"error": "Nenhum trace ativo"}
        
        with self._trace_lock:
            trace_events = [e for e in self.trace_events if e.trace_id == target_trace_id]
        
        if not trace_events:
            return {"error": f"Trace {target_trace_id} não encontrado"}
        
        # Estatísticas básicas
        start_time = min(e.timestamp for e in trace_events)
        end_time = max(e.timestamp for e in trace_events)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Contar eventos por tipo
        event_counts = defaultdict(int)
        error_count = 0
        
        for event in trace_events:
            event_counts[event.event_type.value] += 1
            if event.level == TraceLevel.ERROR:
                error_count += 1
        
        # Nodos visitados
        nodes_visited = list(set(e.node_name for e in trace_events if e.node_name))
        
        return {
            "trace_id": target_trace_id,
            "agent_name": trace_events[0].agent_name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_ms": duration_ms,
            "total_events": len(trace_events),
            "error_count": error_count,
            "event_counts": dict(event_counts),
            "nodes_visited": nodes_visited,
            "success": error_count == 0
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtém resumo de performance."""
        return self.performance_monitor.get_metrics_summary()
    
    def _start_auto_flush(self):
        """Inicia flush automático de dados."""
        async def auto_flush_loop():
            while True:
                await asyncio.sleep(self.config.flush_interval_seconds)
                await self._flush_data()
        
        asyncio.create_task(auto_flush_loop())
    
    async def _flush_data(self):
        """Flush dados para sistemas externos."""
        # Implementar flush para LangSmith ou outros sistemas
        logger.debug("Flush automático de dados de observabilidade")


# ==================== DECORADORES ====================

def observe_agent(agent_name: str, session_id: str = None):
    """Decorador para observabilidade de agentes."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_observability_manager()
            trace_id = manager.start_trace(agent_name, session_id)
            
            try:
                # Adicionar callback handler se possível
                if args and hasattr(args[0], 'callbacks'):
                    if not args[0].callbacks:
                        args[0].callbacks = []
                    args[0].callbacks.append(manager.callback_handler)
                
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                logger.error(f"Erro na execução do agente {agent_name}: {e}")
                raise
            finally:
                manager.end_trace(trace_id)
        
        return wrapper
    return decorator


def observe_node(node_name: str):
    """Decorador para observabilidade de nodos."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_observability_manager()
            
            with manager.trace_node(node_name):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def observe_tool(tool_name: str):
    """Decorador para observabilidade de ferramentas."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_observability_manager()
            
            try:
                result = await func(*args, **kwargs)
                manager.log_tool_call(tool_name, kwargs, result)
                return result
            except Exception as e:
                manager.log_tool_call(tool_name, kwargs, error=e)
                raise
        
        return wrapper
    return decorator


# ==================== INSTÂNCIA GLOBAL ====================

_global_observability_manager = None

def get_observability_manager() -> ObservabilityManager:
    """Obtém instância global do gerenciador de observabilidade."""
    global _global_observability_manager
    
    if _global_observability_manager is None:
        config = ObservabilityConfig(
            langsmith_enabled=os.getenv("LANGSMITH_API_KEY") is not None,
            langsmith_project_name=os.getenv("LANGSMITH_PROJECT", "open-gemini-canvas"),
            trace_level=TraceLevel.INFO,
            enable_performance_monitoring=True,
            enable_error_tracking=True,
            enable_state_tracking=True
        )
        _global_observability_manager = ObservabilityManager(config)
    
    return _global_observability_manager


# Instância padrão
observability_manager = get_observability_manager()