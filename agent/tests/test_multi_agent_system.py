"""
Testes Unitários para Sistema Multi-Agente
Vieira Pires Advogados - Test Suite
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Imports dos módulos testados
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from master_agent import MasterAgentState, analisar_consulta_juridica
from agente_societario import SocietarioAgentState, gerar_contrato_social, estruturar_holding
from agente_tributario import TributarioAgentState, gerar_impugnacao, analisar_reforma_tributaria
from handoffs import HandoffRequest, HandoffPriority, HandoffReason
from checkpointing import AdvancedCheckpointSaver, CheckpointType
from observability import ObservabilityManager, TraceEvent, EventType
from mapreduce import decompose_legal_task, execute_parallel_tasks
from persistent_memory import PersistentMemorySystem, MemoryEntry, MemoryType, AccessLevel
from routing import IntelligentRouter, RoutingContext, AgentCapability
from fault_tolerance import FaultToleranceManager, FailureType, RecoveryStrategy


class TestMasterAgent:
    """Testes do Master Agent."""
    
    @pytest.mark.asyncio
    async def test_analisar_consulta_juridica_societario(self):
        """Testa análise de consulta societária."""
        result = await analisar_consulta_juridica.ainvoke({
            "descricao_consulta": "Preciso estruturar uma holding patrimonial para minha empresa",
            "contexto_empresa": "Empresa familiar com múltiplos negócios",
            "urgencia": False
        })
        
        assert result["area_principal"] == "societario"
        assert "holding" in result["pontuacao_areas"]
        assert result["complexidade"] in ["media", "complexa"]
        assert "workflow_estruturacao_societaria" in result["workflow_sugerido"]
    
    @pytest.mark.asyncio
    async def test_analisar_consulta_juridica_tributario(self):
        """Testa análise de consulta tributária."""
        result = await analisar_consulta_juridica.ainvoke({
            "descricao_consulta": "Recebi auto de infração do ICMS, preciso de impugnação",
            "contexto_empresa": "Indústria com faturamento R$ 50 milhões",
            "urgencia": True
        })
        
        assert result["area_principal"] == "tributario"
        assert "impugnação" in result["ferramentas_necessarias"]
        assert "URGENTE" in result["estimativa_tempo"]
    
    def test_master_agent_state_creation(self):
        """Testa criação do estado do master agent."""
        state = MasterAgentState()
        assert state.area_identificada is None
        assert state.complexidade is None
        assert isinstance(state.agentes_necessarios, list)
        assert isinstance(state.tool_logs, list)


class TestAgentesSocietario:
    """Testes do Agente Societário."""
    
    @pytest.mark.asyncio
    async def test_gerar_contrato_social_ltda(self):
        """Testa geração de contrato social Ltda."""
        socios = [
            {"nome": "João Silva", "cpf": "123.456.789-00", "participacao": 60},
            {"nome": "Maria Santos", "cpf": "987.654.321-00", "participacao": 40}
        ]
        
        result = await gerar_contrato_social.ainvoke({
            "tipo_sociedade": "limitada",
            "socios": socios,
            "capital_social": 100000.0,
            "objeto_social": "Prestação de serviços de consultoria"
        })
        
        assert result["tipo_sociedade"] == "limitada"
        assert result["capital_social"] == 100000.0
        assert result["numero_socios"] == 2
        assert "minuta" in result
        assert "CONTRATO SOCIAL" in result["minuta"]
    
    @pytest.mark.asyncio
    async def test_estruturar_holding_patrimonial(self):
        """Testa estruturação de holding patrimonial."""
        patrimonio = [
            {"tipo": "Imóvel", "valor": 500000, "descricao": "Casa praia"},
            {"tipo": "Empresa", "valor": 1000000, "descricao": "Empresa ABC"}
        ]
        
        result = await estruturar_holding.ainvoke({
            "tipo_holding": "patrimonial",
            "patrimonio": patrimonio,
            "objetivos": ["blindagem", "sucessao"]
        })
        
        assert result["tipo_holding"] == "patrimonial"
        assert result["valor_patrimonio"] == 1500000
        assert "blindagem patrimonial" in str(result["recomendacoes"])
        assert "30-60 dias" in result["prazo_estruturacao"]
    
    def test_societario_state_creation(self):
        """Testa criação do estado societário."""
        state = SocietarioAgentState()
        assert isinstance(state.documentos_gerados, list)
        assert isinstance(state.recomendacoes, list)


class TestAgenteTributario:
    """Testes do Agente Tributário."""
    
    @pytest.mark.asyncio
    async def test_gerar_impugnacao_icms(self):
        """Testa geração de impugnação ICMS."""
        result = await gerar_impugnacao.ainvoke({
            "tipo_tributo": "icms",
            "valor_autuacao": 50000.0,
            "fundamento_autuacao": "Base de cálculo incorreta",
            "fatos_contestacao": [
                "Operação não configura fato gerador",
                "Documentação fiscal regular"
            ]
        })
        
        assert result["tipo_tributo"] == "icms"
        assert result["valor_autuacao"] == 50000.0
        assert "minuta_impugnacao" in result
        assert "30 dias" in result["prazo_apresentacao"]
        assert "70-85%" in result["chances_sucesso"]
    
    @pytest.mark.asyncio
    async def test_analisar_reforma_tributaria_industria(self):
        """Testa análise da reforma tributária para indústria."""
        result = await analisar_reforma_tributaria.ainvoke({
            "setor_empresa": "industria",
            "faturamento_anual": 10000000.0,
            "operacoes_principais": ["fabricação", "vendas", "exportação"]
        })
        
        assert result["setor"] == "industria"
        assert "Muito Positivo" in result["impacto_geral"]
        assert "15-25%" in result["reducao_estimada"]
        assert "2027" in str(result["cronograma"])


class TestHandoffSystem:
    """Testes do Sistema de Handoffs."""
    
    def test_handoff_request_creation(self):
        """Testa criação de requisição de handoff."""
        request = HandoffRequest(
            from_agent="master",
            to_agent="societario",
            reason=HandoffReason.SPECIALIZATION,
            priority=HandoffPriority.HIGH,
            task_description="Estruturação de holding familiar"
        )
        
        assert request.from_agent == "master"
        assert request.to_agent == "societario"
        assert request.reason == HandoffReason.SPECIALIZATION
        assert request.priority == HandoffPriority.HIGH


class TestCheckpointing:
    """Testes do Sistema de Checkpointing."""
    
    def test_checkpoint_saver_initialization(self):
        """Testa inicialização do checkpoint saver."""
        saver = AdvancedCheckpointSaver()
        assert saver.config is not None
        assert saver.storage is not None
    
    def test_checkpoint_creation(self):
        """Testa criação de checkpoint."""
        saver = AdvancedCheckpointSaver()
        session_id = "test_session"
        state = {"test_key": "test_value", "timestamp": datetime.now().isoformat()}
        
        checkpoint_id = saver.save_checkpoint(
            session_id=session_id,
            state=state,
            checkpoint_type=CheckpointType.MANUAL,
            description="Teste de checkpoint"
        )
        
        assert checkpoint_id is not None
        assert len(checkpoint_id) > 0


class TestObservability:
    """Testes do Sistema de Observabilidade."""
    
    def test_observability_manager_initialization(self):
        """Testa inicialização do gerenciador de observabilidade."""
        manager = ObservabilityManager()
        assert manager.config is not None
        assert manager.performance_monitor is not None
    
    def test_trace_event_creation(self):
        """Testa criação de evento de trace."""
        event = TraceEvent(
            id="test_event",
            trace_id="test_trace",
            parent_id=None,
            event_type=EventType.AGENT_START,
            timestamp=datetime.now(),
            level=manager.config.trace_level if 'manager' in locals() else TraceLevel.INFO,
            agent_name="test_agent",
            node_name="test_node",
            message="Test event",
            data={"test": "data"}
        )
        
        assert event.event_type == EventType.AGENT_START
        assert event.agent_name == "test_agent"


class TestMapReduce:
    """Testes do Sistema Map-Reduce."""
    
    @pytest.mark.asyncio
    async def test_decompose_legal_task_due_diligence(self):
        """Testa decomposição de tarefa de due diligence."""
        result = await decompose_legal_task.ainvoke({
            "complex_request": "Preciso de due diligence completa para aquisição de empresa",
            "max_subtasks": 5
        })
        
        assert result["decomposition_successful"] is True
        assert result["pattern_used"] == "due_diligence"
        assert result["total_subtasks"] <= 5
        assert len(result["map_tasks"]) > 0
    
    @pytest.mark.asyncio
    async def test_execute_parallel_tasks(self):
        """Testa execução de tarefas paralelas."""
        tasks = [
            {
                "id": "task_1",
                "agent": "societario",
                "description": "Análise societária",
                "estimated_time": 3.0
            },
            {
                "id": "task_2", 
                "agent": "tributario",
                "description": "Análise tributária",
                "estimated_time": 4.0
            }
        ]
        
        result = await execute_parallel_tasks.ainvoke({
            "map_tasks": tasks,
            "max_workers": 2
        })
        
        assert result["execution_successful"] is True
        assert result["total_tasks"] == 2
        assert result["successful_tasks"] >= 0


class TestPersistentMemory:
    """Testes do Sistema de Memória Persistente."""
    
    def test_memory_system_initialization(self):
        """Testa inicialização do sistema de memória."""
        memory = PersistentMemorySystem()
        assert memory.db_path is not None
    
    def test_memory_entry_creation(self):
        """Testa criação de entrada de memória."""
        entry = MemoryEntry(
            id="test_memory",
            memory_type=MemoryType.LEGAL_PRECEDENT,
            title="Teste STJ",
            content="Precedente teste para validação",
            tags=["teste", "stj"],
            access_level=AccessLevel.INTERNAL,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert entry.memory_type == MemoryType.LEGAL_PRECEDENT
        assert entry.access_level == AccessLevel.INTERNAL
        assert "teste" in entry.tags


class TestIntelligentRouting:
    """Testes do Sistema de Roteamento Inteligente."""
    
    def test_router_initialization(self):
        """Testa inicialização do roteador."""
        router = IntelligentRouter()
        assert len(router.agent_profiles) > 0
        assert "master_legal" in router.agent_profiles
    
    def test_context_analysis(self):
        """Testa análise de contexto."""
        router = IntelligentRouter()
        context = router.analyze_request_context(
            "Urgente: preciso estruturar holding internacional complexa",
            {"client_tier": "premium"}
        )
        
        assert context.urgency_level in ["high", "critical"]
        assert context.complexity_score > 0.5
        assert AgentCapability.CORPORATE_LAW in context.required_capabilities
    
    def test_agent_selection(self):
        """Testa seleção de agente."""
        router = IntelligentRouter()
        context = RoutingContext(
            client_tier="premium",
            urgency_level="high",
            complexity_score=0.8,
            estimated_duration=30.0,
            required_capabilities=[AgentCapability.CORPORATE_LAW]
        )
        
        agent, confidence, reasoning = router.select_optimal_agent(context)
        
        assert agent is not None
        assert confidence >= 0.0
        assert reasoning is not None


class TestFaultTolerance:
    """Testes do Sistema de Tolerância a Falhas."""
    
    def test_fault_manager_initialization(self):
        """Testa inicialização do gerenciador de falhas."""
        manager = FaultToleranceManager()
        assert len(manager.recovery_policies) > 0
        assert "default" in manager.recovery_policies
    
    def test_incident_registration(self):
        """Testa registro de incidente."""
        manager = FaultToleranceManager()
        error = Exception("Teste de erro")
        
        incident_id = manager.register_incident(
            component="test_component",
            failure_type=FailureType.AGENT_FAILURE,
            error=error,
            context={"test": True}
        )
        
        assert incident_id is not None
        assert len(manager.incidents) > 0
    
    def test_circuit_breaker(self):
        """Testa circuit breaker."""
        manager = FaultToleranceManager()
        cb = manager.get_circuit_breaker("test_component")
        
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0


# ==================== TESTES DE INTEGRAÇÃO ====================

class TestSystemIntegration:
    """Testes de integração do sistema completo."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_societario(self):
        """Testa workflow completo societário."""
        # 1. Análise pelo Master Agent
        analysis = await analisar_consulta_juridica.ainvoke({
            "descricao_consulta": "Estruturar holding para empresa familiar",
            "contexto_empresa": "Família com múltiplos negócios"
        })
        
        assert analysis["area_principal"] == "societario"
        
        # 2. Execução pelo Agente Societário
        holding_result = await estruturar_holding.ainvoke({
            "tipo_holding": "familiar",
            "patrimonio": [{"tipo": "Empresa", "valor": 1000000}],
            "herdeiros": [{"nome": "Filho 1"}, {"nome": "Filho 2"}]
        })
        
        assert holding_result["tipo_holding"] == "familiar"
        assert "recomendacoes" in holding_result
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Testa workflow de recuperação de erro."""
        manager = FaultToleranceManager()
        
        # Simular erro
        error = Exception("Falha simulada")
        incident_id = manager.register_incident(
            "test_agent",
            FailureType.AGENT_FAILURE,
            error
        )
        
        assert incident_id is not None
        
        # Verificar estado do sistema
        health = manager.get_system_health()
        assert health["total_incidents"] > 0


# ==================== CONFIGURAÇÃO DE TESTES ====================

@pytest.fixture
def mock_openrouter():
    """Mock para OpenRouter API."""
    with patch('langchain_openai.ChatOpenAI') as mock:
        mock_instance = Mock()
        mock_instance.ainvoke = AsyncMock(return_value=Mock(
            content="Resposta simulada",
            tool_calls=[]
        ))
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_legal_context():
    """Contexto jurídico de exemplo."""
    return {
        "client_name": "Empresa Teste Ltda",
        "area": "societario", 
        "urgency": "medium",
        "complexity": "high",
        "estimated_value": 100000.0
    }


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])