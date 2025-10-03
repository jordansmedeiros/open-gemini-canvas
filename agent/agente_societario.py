"""
Agente Especializado em Estruturação Societária & Holdings
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


# ==================== ENUMS E MODELOS ====================

class TipoSociedade(Enum):
    LTDA = "limitada"
    SA = "sociedade_anonima"
    EIRELI = "eireli"
    MEI = "mei"


class TipoHolding(Enum):
    PATRIMONIAL = "patrimonial"
    FAMILIAR = "familiar"
    MISTA = "mista"
    ADMINISTRATIVA = "administrativa"


class SocietarioAgentState(CopilotKitState):
    """Estado do agente societário."""
    tipo_estruturacao: Optional[str] = None
    socios_info: List[Dict[str, Any]] = Field(default_factory=list)
    patrimonio_envolvido: Optional[float] = None
    documentos_gerados: List[str] = Field(default_factory=list)
    recomendacoes: List[str] = Field(default_factory=list)
    tool_logs: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== FERRAMENTAS ESPECIALIZADAS ====================

@tool
async def gerar_contrato_social(
    tipo_sociedade: str,
    socios: List[Dict[str, Any]],
    capital_social: float,
    objeto_social: str,
    sede: str = "São Paulo, SP"
) -> Dict[str, Any]:
    """
    Gera minuta de contrato social para sociedade limitada ou S.A.
    
    Args:
        tipo_sociedade: Tipo da sociedade (limitada, sociedade_anonima)
        socios: Lista com dados dos sócios (nome, cpf, participacao, residencia)
        capital_social: Valor do capital social
        objeto_social: Descrição do objeto social
        sede: Localização da sede da empresa
    """
    
    try:
        # Validações básicas
        if not socios or len(socios) < 1:
            return {"error": "É necessário pelo menos um sócio"}
        
        total_participacao = sum(socio.get("participacao", 0) for socio in socios)
        if abs(total_participacao - 100) > 0.01:
            return {"error": "Participações dos sócios devem somar 100%"}
        
        # Gerar minuta baseada no tipo
        if tipo_sociedade == "limitada":
            minuta = await _gerar_minuta_ltda(socios, capital_social, objeto_social, sede)
        elif tipo_sociedade == "sociedade_anonima":
            minuta = await _gerar_minuta_sa(socios, capital_social, objeto_social, sede)
        else:
            return {"error": f"Tipo de sociedade não suportado: {tipo_sociedade}"}
        
        return {
            "tipo_documento": "contrato_social",
            "tipo_sociedade": tipo_sociedade,
            "minuta": minuta,
            "capital_social": capital_social,
            "numero_socios": len(socios),
            "observacoes": [
                "Contrato social deve ser registrado na Junta Comercial",
                "Verificar exigências específicas do estado",
                "Considerar regime tributário mais adequado"
            ],
            "proximos_passos": [
                "Revisão pelos sócios",
                "Coleta de documentos pessoais",
                "Registro na Junta Comercial",
                "Inscrições fiscais"
            ]
        }
        
    except Exception as e:
        return {"error": f"Erro na geração do contrato: {str(e)}"}


async def _gerar_minuta_ltda(socios, capital_social, objeto_social, sede):
    """Gera minuta específica para Ltda."""
    
    nome_empresa = "EMPRESA LTDA"  # Placeholder
    
    minuta = f"""# CONTRATO SOCIAL DE CONSTITUIÇÃO
## {nome_empresa}

### CLÁUSULA 1ª - CONSTITUIÇÃO E DENOMINAÇÃO
Fica constituída uma sociedade empresária limitada, que se regerá pelo presente contrato social e pelas disposições legais aplicáveis, sob a denominação de **{nome_empresa}**.

### CLÁUSULA 2ª - SEDE E PRAZO
A sociedade tem sede e foro na cidade de {sede}, podendo abrir filiais, agências ou escritórios em qualquer parte do território nacional ou no exterior.
O prazo de duração da sociedade é por tempo indeterminado.

### CLÁUSULA 3ª - OBJETO SOCIAL
A sociedade tem por objeto: {objeto_social}

### CLÁUSULA 4ª - CAPITAL SOCIAL
O capital social é de R$ {capital_social:,.2f}, dividido em quotas no valor nominal de R$ 1,00 cada uma, integralizadas em moeda corrente nacional.

#### PARTICIPAÇÃO DOS SÓCIOS:
"""
    
    for i, socio in enumerate(socios, 1):
        nome = socio.get("nome", f"Sócio {i}")
        participacao = socio.get("participacao", 0)
        quotas = int((participacao / 100) * capital_social)
        
        minuta += f"""
**{nome}**
- CPF: {socio.get('cpf', 'XXX.XXX.XXX-XX')}
- Participação: {participacao}%
- Quotas: {quotas:,} quotas
- Valor: R$ {quotas:,.2f}
"""
    
    minuta += """
### CLÁUSULA 5ª - ADMINISTRAÇÃO
A administração da sociedade caberá aos sócios, isolada ou conjuntamente, vedado o uso da denominação social em atos estranhos aos negócios sociais.

### CLÁUSULA 6ª - DELIBERAÇÕES SOCIAIS
As deliberações sociais serão tomadas em reunião de sócios, por maioria de votos, representativa de mais da metade do capital social.

### CLÁUSULA 7ª - EXERCÍCIO SOCIAL E LUCROS
O exercício social coincide com o ano civil. Os lucros ou prejuízos apurados serão distribuídos ou suportados pelos sócios na proporção de suas quotas.

### CLÁUSULA 8ª - DISSOLUÇÃO
A sociedade dissolve-se nos casos previstos em lei, ou por deliberação dos sócios representativa de mais da metade do capital social.

**LOCAL E DATA**
São Paulo, {datetime.now().strftime('%d de %B de %Y')}

**ASSINATURAS DOS SÓCIOS**
"""
    
    for socio in socios:
        minuta += f"\n______________________________\n{socio.get('nome', 'Nome do Sócio')}"
    
    return minuta


async def _gerar_minuta_sa(socios, capital_social, objeto_social, sede):
    """Gera minuta específica para S.A."""
    
    nome_empresa = "EMPRESA S.A."  # Placeholder
    
    minuta = f"""# ESTATUTO SOCIAL
## {nome_empresa}

### CAPÍTULO I - DENOMINAÇÃO, SEDE, OBJETO E DURAÇÃO

**ARTIGO 1º** - A sociedade anônima denomina-se **{nome_empresa}**, e reger-se-á pelo presente estatuto e pelas disposições legais aplicáveis.

**ARTIGO 2º** - A Companhia tem sede e foro em {sede}, podendo, por deliberação da Diretoria, criar filiais, agências, depósitos ou escritórios em qualquer parte do território nacional ou no exterior.

**ARTIGO 3º** - O objeto da Companhia é: {objeto_social}

**ARTIGO 4º** - O prazo de duração da Companhia é por tempo indeterminado.

### CAPÍTULO II - CAPITAL SOCIAL E AÇÕES

**ARTIGO 5º** - O capital social é de R$ {capital_social:,.2f}, dividido em {int(capital_social)} ações ordinárias nominativas, sem valor nominal.

#### SUBSCRIÇÃO DO CAPITAL:
"""
    
    for i, socio in enumerate(socios, 1):
        nome = socio.get("nome", f"Acionista {i}")
        participacao = socio.get("participacao", 0)
        acoes = int((participacao / 100) * capital_social)
        
        minuta += f"""
**{nome}**
- CPF: {socio.get('cpf', 'XXX.XXX.XXX-XX')}
- Ações: {acoes:,} ações ordinárias
- Participação: {participacao}%
"""
    
    minuta += """
### CAPÍTULO III - ADMINISTRAÇÃO

**ARTIGO 6º** - A Companhia será administrada por uma Diretoria composta de no mínimo 1 (um) e no máximo 3 (três) membros, acionistas ou não, residentes no País.

**ARTIGO 7º** - O mandato dos Diretores será de 3 (três) anos, permitida a reeleição.

### CAPÍTULO IV - ASSEMBLEIA GERAL

**ARTIGO 8º** - A Assembleia Geral reunir-se-á ordinariamente uma vez por ano, nos quatro primeiros meses seguintes ao término do exercício social.

### CAPÍTULO V - EXERCÍCIO SOCIAL E DEMONSTRAÇÕES FINANCEIRAS

**ARTIGO 9º** - O exercício social termina em 31 de dezembro de cada ano, quando serão levantadas as demonstrações financeiras.

### CAPÍTULO VI - DISSOLUÇÃO E LIQUIDAÇÃO

**ARTIGO 10º** - A Companhia dissolve-se nos casos previstos em lei.

**LOCAL E DATA**
São Paulo, {datetime.now().strftime('%d de %B de %Y')}

**FUNDADORES**
"""
    
    for socio in socios:
        minuta += f"\n______________________________\n{socio.get('nome', 'Nome do Fundador')}"
    
    return minuta


@tool
async def estruturar_holding(
    tipo_holding: str,
    patrimonio: List[Dict[str, Any]],
    herdeiros: List[Dict[str, Any]] = [],
    objetivos: List[str] = []
) -> Dict[str, Any]:
    """
    Propõe estrutura de holding patrimonial ou familiar.
    
    Args:
        tipo_holding: Tipo (patrimonial, familiar, mista, administrativa)
        patrimonio: Lista de bens/empresas a serem transferidos
        herdeiros: Lista de herdeiros (para holding familiar)
        objetivos: Objetivos da estruturação (blindagem, sucessão, tributário)
    """
    
    try:
        valor_total = sum(item.get("valor", 0) for item in patrimonio)
        
        # Estrutura básica baseada no tipo
        estruturas = {
            "patrimonial": {
                "finalidade": "Separação e proteção do patrimônio pessoal",
                "vantagens": [
                    "Blindagem patrimonial",
                    "Organização de investimentos", 
                    "Facilita sucessão",
                    "Otimização tributária"
                ],
                "estrutura_recomendada": "Holding Patrimonial → Patrimônio/Investimentos"
            },
            "familiar": {
                "finalidade": "Planejamento sucessório e governança familiar",
                "vantagens": [
                    "Evita inventário",
                    "Reduz conflitos familiares",
                    "Profissionaliza gestão",
                    "Proteção de menores"
                ],
                "estrutura_recomendada": "Holding Familiar → Empresas Operacionais → Distribuição Controlada"
            },
            "mista": {
                "finalidade": "Combinação de proteção patrimonial e sucessória",
                "vantagens": [
                    "Flexibilidade máxima",
                    "Múltiplos objetivos",
                    "Governança corporativa",
                    "Eficiência fiscal"
                ],
                "estrutura_recomendada": "Holding Mista → [Patrimônio + Empresas] → Beneficiários"
            }
        }
        
        estrutura = estruturas.get(tipo_holding, estruturas["patrimonial"])
        
        # Recomendações específicas
        recomendacoes = [
            "Constituir holding como sociedade limitada",
            "Definir acordo de quotistas robusto",
            "Implementar governança corporativa",
            "Estabelecer política de distribuição de resultados"
        ]
        
        if "sucessao" in objetivos:
            recomendacoes.extend([
                "Criar conselho de família",
                "Definir protocolo familiar",
                "Estabelecer cláusulas de inalienabilidade/impenhorabilidade"
            ])
        
        if "tributario" in objetivos:
            recomendacoes.extend([
                "Analisar regime tributário ótimo",
                "Considerar holding em regime do lucro real",
                "Avaliar benefícios da reorganização societária"
            ])
        
        # Documentos necessários
        documentos = [
            "Contrato social da holding",
            "Acordo de quotistas",
            "Laudos de avaliação dos bens",
            "Contratos de transferência"
        ]
        
        if herdeiros:
            documentos.extend([
                "Protocolo familiar",
                "Estatuto do conselho de família"
            ])
        
        return {
            "tipo_holding": tipo_holding,
            "estrutura": estrutura,
            "valor_patrimonio": valor_total,
            "numero_bens": len(patrimonio),
            "numero_herdeiros": len(herdeiros),
            "recomendacoes": recomendacoes,
            "documentos_necessarios": documentos,
            "prazo_estruturacao": "30-60 dias",
            "investimento_estimado": f"R$ {max(15000, valor_total * 0.002):,.2f} - R$ {max(25000, valor_total * 0.005):,.2f}",
            "beneficios_fiscais": "Redução de 15-30% na carga tributária sucessória",
            "alertas": [
                "Verificar impacto do novo marco do ITCMD",
                "Considerar prazo de carência para blindagem",
                "Avaliar impacto na declaração de IR pessoa física"
            ]
        }
        
    except Exception as e:
        return {"error": f"Erro na estruturação: {str(e)}"}


@tool
async def analisar_acordo_socios(
    acordo_atual: str,
    pontos_atencao: List[str] = []
) -> Dict[str, Any]:
    """
    Revisa acordo de sócios e sugere melhorias.
    
    Args:
        acordo_atual: Texto do acordo atual ou pontos principais
        pontos_atencao: Pontos específicos para análise
    """
    
    try:
        # Cláusulas essenciais que devem estar presentes
        clausulas_essenciais = {
            "tag_along": "Direito de acompanhar venda",
            "drag_along": "Direito de arrastar na venda", 
            "direito_preferencia": "Preferência na compra de quotas",
            "restricoes_transferencia": "Limitações à transferência",
            "governanca": "Estrutura de governança",
            "deadlock": "Resolução de impasses",
            "exclusao": "Exclusão de sócio",
            "dissolucao": "Dissolução da sociedade",
            "confidencialidade": "Sigilo empresarial",
            "nao_concorrencia": "Vedação à concorrência"
        }
        
        # Análise do acordo (simulada - seria uma análise real do texto)
        acordo_lower = acordo_atual.lower()
        clausulas_presentes = []
        clausulas_ausentes = []
        
        for clausula, descricao in clausulas_essenciais.items():
            if clausula.replace("_", " ") in acordo_lower or clausula in acordo_lower:
                clausulas_presentes.append({"clausula": clausula, "descricao": descricao})
            else:
                clausulas_ausentes.append({"clausula": clausula, "descricao": descricao})
        
        # Sugestões de melhoria
        sugestoes = []
        
        if len(clausulas_ausentes) > 0:
            sugestoes.append(f"Incluir {len(clausulas_ausentes)} cláusulas ausentes essenciais")
        
        if "tag_along" in [c["clausula"] for c in clausulas_ausentes]:
            sugestoes.append("Implementar cláusula Tag Along com percentual mínimo de 10%")
        
        if "deadlock" in [c["clausula"] for c in clausulas_ausentes]:
            sugestoes.append("Criar mecanismo de resolução de deadlock (arbitragem/compra forçada)")
        
        if "governanca" in [c["clausula"] for c in clausulas_ausentes]:
            sugestoes.append("Definir estrutura de governança com conselhos e comitês")
        
        # Pontos de atenção específicos
        alertas = [
            "Verificar aderência ao novo Código Civil",
            "Confirmar jurisdição e foro de eleição",
            "Validar mecanismos de avaliação de quotas"
        ]
        
        if pontos_atencao:
            alertas.extend([f"Atenção especial: {ponto}" for ponto in pontos_atencao])
        
        # Score de qualidade
        score_qualidade = (len(clausulas_presentes) / len(clausulas_essenciais)) * 100
        
        return {
            "score_qualidade": round(score_qualidade, 1),
            "clausulas_presentes": clausulas_presentes,
            "clausulas_ausentes": clausulas_ausentes,
            "sugestoes_melhoria": sugestoes,
            "alertas": alertas,
            "minuta_melhorada": len(clausulas_ausentes) == 0,
            "nivel_protecao": "Alto" if score_qualidade >= 80 else "Médio" if score_qualidade >= 60 else "Baixo",
            "recomendacao": "Aprovado com ressalvas" if score_qualidade >= 70 else "Requer revisão substancial"
        }
        
    except Exception as e:
        return {"error": f"Erro na análise: {str(e)}"}


# ==================== NODOS DO AGENTE ====================

async def societario_analyzer_node(state: SocietarioAgentState, config: RunnableConfig) -> Command:
    """Analisa demanda societária e define estratégia."""
    
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    if isinstance(state, dict):
        if "tool_logs" not in state:
            state["tool_logs"] = []
        state["tool_logs"].append({
            "id": str(uuid.uuid4()),
            "message": "Analisando demanda societária",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        })
    else:
        state.tool_logs.append({
            "id": str(uuid.uuid4()),
            "message": "Analisando demanda societária",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Configurar modelo especializado
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=0.1,
        max_retries=2,
    )
    
    tools = [gerar_contrato_social, estruturar_holding, analisar_acordo_socios]
    
    # System prompt especializado em direito societário
    system_prompt = """
    Você é especialista em Direito Societário do escritório Vieira Pires Advogados.
    
    EXPERTISE:
    🏢 Estruturação de holdings (patrimoniais, familiares, mistas)
    📋 Contratos sociais (Ltda, S.A., EIRELI)
    🤝 Acordos de sócios/quotistas
    ⚖️ Planejamento sucessório empresarial
    🛡️ Blindagem patrimonial
    
    LEGISLAÇÃO PRINCIPAL:
    - Lei 6.404/76 (Lei das S.A.)
    - Código Civil (Arts. 981-1.195) 
    - Lei 13.874/19 (Marco da Liberdade Econômica)
    
    ABORDAGEM:
    - Foque na proteção patrimonial e sucessória
    - Sempre considere aspectos tributários
    - Proponha governança corporativa adequada
    - Use linguagem técnica mas acessível
    
    Para cada consulta, use as ferramentas disponíveis para gerar documentos precisos e análises detalhadas.
    SEMPRE cite a legislação aplicável e identifique riscos/oportunidades.
    """
    
    if isinstance(state, dict):
        messages_list = state.get("messages", [])
        last_message = messages_list[-1].content if messages_list else "Inicializar análise societária"
    else:
        last_message = state.messages[-1].content if state.messages else "Inicializar análise societária"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Consulta societária: {last_message}")
    ]
    
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(messages, config)
    
    state.tool_logs[-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return Command(goto="execute_societario", update={"messages": [response]})
    else:
        return Command(goto="finalize_societario", update={"messages": [response]})


async def execute_societario_node(state: SocietarioAgentState, config: RunnableConfig) -> Command:
    """Executa ferramentas societárias."""
    
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
                if tool_name == "gerar_contrato_social":
                    result = await gerar_contrato_social.ainvoke(tool_args)
                    if "minuta" in result:
                        state.documentos_gerados.append("Contrato Social")
                elif tool_name == "estruturar_holding":
                    result = await estruturar_holding.ainvoke(tool_args)
                    if "recomendacoes" in result:
                        state.recomendacoes.extend(result["recomendacoes"])
                elif tool_name == "analisar_acordo_socios":
                    result = await analisar_acordo_socios.ainvoke(tool_args)
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
                
                results.append({"tool": tool_name, "result": result, "success": "error" not in result})
                state.tool_logs[-1]["status"] = "completed"
                
            except Exception as e:
                results.append({"tool": tool_name, "error": str(e), "success": False})
                state.tool_logs[-1]["status"] = "failed"
            
            await copilotkit_emit_state(config, state)
    
    return Command(goto="finalize_societario", update={"resultados_ferramentas": results})


async def finalize_societario_node(state: SocietarioAgentState, config: RunnableConfig) -> Command:
    """Finaliza com parecer societário."""
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Finalizando análise societária",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    # Gerar parecer societário
    parecer = "# PARECER SOCIETÁRIO\n"
    parecer += "## Vieira Pires Advogados - Estruturação Societária & Holdings\n\n"
    parecer += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if state.documentos_gerados:
        parecer += "## DOCUMENTOS ELABORADOS\n"
        for doc in state.documentos_gerados:
            parecer += f"✅ {doc}\n"
        parecer += "\n"
    
    if state.recomendacoes:
        parecer += "## RECOMENDAÇÕES ESTRATÉGICAS\n"
        for rec in state.recomendacoes[:5]:  # Primeiras 5
            parecer += f"• {rec}\n"
        parecer += "\n"
    
    results = getattr(state, 'resultados_ferramentas', [])
    if results:
        parecer += "## ANÁLISE TÉCNICA\n"
        for result in results:
            if result.get("success"):
                parecer += f"✅ **{result['tool'].replace('_', ' ').title()}:** Concluído\n"
            else:
                parecer += f"❌ **{result['tool'].replace('_', ' ').title()}:** Revisar\n"
        parecer += "\n"
    
    parecer += """## PRÓXIMOS PASSOS
1. **Aprovação:** Revisão e aprovação dos documentos pelos interessados
2. **Documentação:** Coleta de documentos pessoais e empresariais
3. **Registro:** Protocolo na Junta Comercial competente
4. **Implementação:** Transferência de bens e adequação operacional

## PRAZOS E INVESTIMENTOS
- **Elaboração:** 5-10 dias úteis
- **Registro:** 15-30 dias úteis
- **Honorários:** Conforme tabela OAB + custos cartorários

---
*Departamento Societário - Vieira Pires Advogados*  
*"Excelência em Estruturação Societária e Blindagem Patrimonial"*
"""
    
    # Limpar logs
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(goto=END, update={"messages": [AIMessage(content=parecer)]})


# ==================== CRIAÇÃO DO GRAFO ====================

def create_societario_agent_graph() -> StateGraph:
    """Cria grafo do agente societário."""
    
    workflow = StateGraph(SocietarioAgentState)
    
    workflow.add_node("analyzer", societario_analyzer_node)
    workflow.add_node("execute_societario", execute_societario_node)
    workflow.add_node("finalize_societario", finalize_societario_node)
    
    workflow.set_entry_point("analyzer")
    workflow.set_finish_point("finalize_societario")
    
    workflow.add_edge(START, "analyzer")
    workflow.add_edge("execute_societario", "finalize_societario")
    workflow.add_edge("finalize_societario", END)
    
    return workflow.compile(checkpointer=MemorySaver())


# Instância do agente societário
societario_agent_graph = create_societario_agent_graph()