"""
Agente Especializado em Direito Tributário Empresarial
Vieira Pires Advogados - Tier 1 Agent
"""

import os
import json
from typing import Any, Dict, List, Optional
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


class TributarioAgentState(CopilotKitState):
    """Estado do agente tributário."""
    tributo_analisado: Optional[str] = None
    economia_estimada: Optional[float] = None
    defesas_elaboradas: List[str] = Field(default_factory=list)
    alertas_reforma: List[str] = Field(default_factory=list)
    tool_logs: List[Dict[str, Any]] = Field(default_factory=list)


@tool
async def gerar_impugnacao(
    tipo_tributo: str,
    valor_autuacao: float,
    fundamento_autuacao: str,
    fatos_contestacao: List[str]
) -> Dict[str, Any]:
    """Gera impugnação contra auto de infração."""
    
    try:
        numero_processo = f"IMP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Fundamentos por tipo de tributo
        fundamentos_especificos = {
            "icms": ["Não configuração do fato gerador", "Base de cálculo incorreta"],
            "ipi": ["Produto não enquadrado na TIPI", "Industrialização não caracterizada"],
            "pis_cofins": ["Regime de apuração incorreto", "Base de cálculo indevida"],
            "irpj": ["Dedutibilidade dos custos/despesas", "Regime inadequado"]
        }
        
        fundamentos = fundamentos_especificos.get(tipo_tributo, ["Ausência de fato gerador"])
        
        minuta = f"""# IMPUGNAÇÃO - Processo {numero_processo}

## I - DOS FATOS
A empresa foi autuada em {datetime.now().strftime('%d/%m/%Y')} referente ao tributo **{tipo_tributo.upper()}**, no valor de **R$ {valor_autuacao:,.2f}**.

## II - DO DIREITO
{fundamento_autuacao}

## III - DOS FUNDAMENTOS
"""
        
        for i, fundamento in enumerate(fundamentos[:2], 1):
            minuta += f"{i}. {fundamento}\n"
        
        for i, fato in enumerate(fatos_contestacao[:3], 1):
            minuta += f"\n**Fato {i}:** {fato}\n"
        
        minuta += f"""
## IV - DOS PEDIDOS
Requer-se a anulação do auto de infração.

São Paulo, {datetime.now().strftime('%d/%m/%Y')}
Vieira Pires Advogados
"""
        
        return {
            "numero_processo": numero_processo,
            "tipo_tributo": tipo_tributo,
            "valor_autuacao": valor_autuacao,
            "minuta_impugnacao": minuta,
            "chances_sucesso": "70-85%",
            "prazo_apresentacao": "30 dias",
            "proximos_passos": ["Revisão com cliente", "Coleta documentos", "Protocolo"]
        }
        
    except Exception as e:
        return {"error": f"Erro na geração: {str(e)}"}


@tool
async def analisar_reforma_tributaria(
    setor_empresa: str,
    faturamento_anual: float,
    operacoes_principais: List[str]
) -> Dict[str, Any]:
    """Analisa impacto da Reforma Tributária (EC 132/2023)."""
    
    try:
        # Impactos por setor
        impactos_setor = {
            "comercio": {
                "impacto": "Positivo - simplificação",
                "reducao": "8-15%",
                "beneficios": ["Fim da cumulatividade", "Crédito integral", "Menos burocracia"]
            },
            "industria": {
                "impacto": "Muito Positivo", 
                "reducao": "15-25%",
                "beneficios": ["Crédito ampliado", "Fim guerra fiscal", "Competitividade"]
            },
            "servicos": {
                "impacto": "Neutro a Positivo",
                "reducao": "5-12%",
                "beneficios": ["IBS único", "Menos complexidade"]
            }
        }
        
        setor_info = impactos_setor.get(setor_empresa, impactos_setor["comercio"])
        
        cronograma = {
            "2027": "Início CBS (substitui PIS/COFINS/IPI)",
            "2029": "Início IBS (substitui ICMS/ISS)",
            "2032": "Implementação completa"
        }
        
        return {
            "setor": setor_empresa,
            "impacto_geral": setor_info["impacto"],
            "reducao_estimada": setor_info["reducao"],
            "economia_anual": f"R$ {faturamento_anual * 0.15:,.2f}",
            "beneficios": setor_info["beneficios"],
            "cronograma": cronograma,
            "acoes_imediatas": [
                "Diagnóstico atual",
                "Simulação novo regime", 
                "Adequação sistemas",
                "Capacitação equipe"
            ],
            "prazo_preparacao": "18-24 meses"
        }
        
    except Exception as e:
        return {"error": f"Erro na análise: {str(e)}"}


@tool
async def calcular_economia_tributaria(
    regime_atual: str,
    faturamento: float,
    custos: float,
    atividade: str
) -> Dict[str, Any]:
    """Calcula economia tributária com mudança de regime."""
    
    try:
        # Alíquotas simplificadas
        if regime_atual == "simples_nacional":
            tributo_atual = faturamento * 0.10  # 10% média
        elif regime_atual == "lucro_presumido":
            tributo_atual = faturamento * 0.25  # 25% média
        else:  # lucro_real
            lucro = faturamento - custos
            tributo_atual = (lucro * 0.34) + (faturamento * 0.15)
        
        # Simular regimes alternativos
        simulacoes = {}
        
        if regime_atual != "simples_nacional" and faturamento <= 4800000:
            tributo_simples = faturamento * 0.10
            economia = tributo_atual - tributo_simples
            
            simulacoes["simples_nacional"] = {
                "tributo_total": tributo_simples,
                "economia_anual": economia,
                "economia_percentual": (economia / tributo_atual) * 100,
                "viavel": economia > 0
            }
        
        # Determinar melhor opção
        melhor_opcao = regime_atual
        maior_economia = 0
        
        for regime, dados in simulacoes.items():
            if dados["viavel"] and dados["economia_anual"] > maior_economia:
                maior_economia = dados["economia_anual"]
                melhor_opcao = regime
        
        return {
            "regime_atual": regime_atual,
            "tributo_atual": tributo_atual,
            "simulacoes": simulacoes,
            "melhor_opcao": melhor_opcao,
            "economia_maxima": maior_economia,
            "recomendacao": "Manter atual" if melhor_opcao == regime_atual else f"Migrar para {melhor_opcao}",
            "prazo_opcao": "Até 31/01 do ano seguinte"
        }
        
    except Exception as e:
        return {"error": f"Erro no cálculo: {str(e)}"}


async def tributario_analyzer_node(state: TributarioAgentState, config: RunnableConfig) -> Command:
    """Analisa demanda tributária."""
    
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Analisando questão tributária",
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
    
    tools = [gerar_impugnacao, analisar_reforma_tributaria, calcular_economia_tributaria]
    
    system_prompt = """
    Você é especialista em Direito Tributário do Vieira Pires Advogados.
    
    EXPERTISE:
    📊 Planejamento tributário otimizado
    ⚖️ Defesas fiscais (impugnações, recursos)  
    📈 Reforma Tributária (EC 132/2023)
    💰 Economia fiscal lícita
    
    LEGISLAÇÃO:
    - CTN (Lei 5.172/66)
    - CF/88 (Arts. 145-162)
    - EC 132/2023 (Reforma Tributária)
    
    ABORDAGEM:
    - Foque na legalidade estrita
    - Identifique oportunidades de economia
    - Para defesas: explore vícios formais e materiais
    - Use jurisprudência favorável
    
    Use sempre as ferramentas para análises precisas.
    """
    
    last_message = state.messages[-1].content if state.messages else "Análise tributária"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Consulta: {last_message}")
    ]
    
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(messages, config)
    
    state.tool_logs[-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return Command(goto="execute_tributario", update={"messages": [response]})
    else:
        return Command(goto="finalize_tributario", update={"messages": [response]})


async def execute_tributario_node(state: TributarioAgentState, config: RunnableConfig) -> Command:
    """Executa ferramentas tributárias."""
    
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
                if tool_name == "gerar_impugnacao":
                    result = await gerar_impugnacao.ainvoke(tool_args)
                    if "minuta_impugnacao" in result:
                        state.defesas_elaboradas.append("Impugnação")
                elif tool_name == "analisar_reforma_tributaria":
                    result = await analisar_reforma_tributaria.ainvoke(tool_args)
                    if "beneficios" in result:
                        state.alertas_reforma.extend(result["beneficios"])
                elif tool_name == "calcular_economia_tributaria":
                    result = await calcular_economia_tributaria.ainvoke(tool_args)
                    if "economia_maxima" in result:
                        state.economia_estimada = result["economia_maxima"]
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
                
                results.append({"tool": tool_name, "result": result, "success": "error" not in result})
                state.tool_logs[-1]["status"] = "completed"
                
            except Exception as e:
                results.append({"tool": tool_name, "error": str(e), "success": False})
                state.tool_logs[-1]["status"] = "failed"
            
            await copilotkit_emit_state(config, state)
    
    return Command(goto="finalize_tributario", update={"resultados_ferramentas": results})


async def finalize_tributario_node(state: TributarioAgentState, config: RunnableConfig) -> Command:
    """Finaliza com parecer tributário."""
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Finalizando análise tributária",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    parecer = "# PARECER TRIBUTÁRIO\n"
    parecer += "## Vieira Pires Advogados - Direito Tributário Empresarial\n\n"
    parecer += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if state.economia_estimada:
        parecer += f"## ECONOMIA FISCAL\n"
        parecer += f"💰 **Economia Estimada:** R$ {state.economia_estimada:,.2f}/ano\n\n"
    
    if state.defesas_elaboradas:
        parecer += "## DEFESAS ELABORADAS\n"
        for defesa in state.defesas_elaboradas:
            parecer += f"⚖️ {defesa}\n"
        parecer += "\n"
    
    if state.alertas_reforma:
        parecer += "## REFORMA TRIBUTÁRIA\n"
        for alerta in state.alertas_reforma[:3]:
            parecer += f"📈 {alerta}\n"
        parecer += "\n"
    
    parecer += """## ESTRATÉGIA
1. **Imediato:** Implementar economia identificada
2. **Curto Prazo:** Preparar para Reforma Tributária  
3. **Médio Prazo:** Otimizar regime tributário
4. **Contínuo:** Monitorar mudanças legislativas

## PRÓXIMOS PASSOS
1. Aprovação das estratégias propostas
2. Implementação das medidas de economia
3. Acompanhamento de prazos e resultados

---
*Departamento Tributário - Vieira Pires Advogados*
"""
    
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(goto=END, update={"messages": [AIMessage(content=parecer)]})


def create_tributario_agent_graph() -> StateGraph:
    """Cria grafo do agente tributário."""
    
    workflow = StateGraph(TributarioAgentState)
    
    workflow.add_node("analyzer", tributario_analyzer_node)
    workflow.add_node("execute_tributario", execute_tributario_node)
    workflow.add_node("finalize_tributario", finalize_tributario_node)
    
    workflow.set_entry_point("analyzer")
    workflow.set_finish_point("finalize_tributario")
    
    workflow.add_edge(START, "analyzer")
    workflow.add_edge("execute_tributario", "finalize_tributario")
    workflow.add_edge("finalize_tributario", END)
    
    return workflow.compile(checkpointer=MemorySaver())


tributario_agent_graph = create_tributario_agent_graph()