"""
Agente Especializado em Contratos Empresariais
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


class TipoContrato(Enum):
    PRESTACAO_SERVICOS = "prestacao_servicos"
    FORNECIMENTO = "fornecimento"
    DISTRIBUICAO = "distribuicao"
    JOINT_VENTURE = "joint_venture"
    LICENCIAMENTO = "licenciamento"
    CONFIDENCIALIDADE = "confidencialidade"


class ContratosAgentState(CopilotKitState):
    """Estado do agente de contratos."""
    tipo_contrato: Optional[str] = None
    partes_envolvidas: List[str] = Field(default_factory=list)
    valor_contrato: Optional[float] = None
    contratos_gerados: List[str] = Field(default_factory=list)
    clausulas_criticas: List[str] = Field(default_factory=list)
    tool_logs: List[Dict[str, Any]] = Field(default_factory=list)


@tool
async def gerar_contrato(
    tipo_contrato: str,
    partes: List[Dict[str, Any]],
    objeto: str,
    valor: Optional[float] = None,
    prazo: str = "12 meses"
) -> Dict[str, Any]:
    """
    Gera minuta de contrato comercial.
    
    Args:
        tipo_contrato: Tipo do contrato
        partes: Lista com dados das partes (nome, cnpj, endereco)
        objeto: Objeto do contrato
        valor: Valor do contrato (opcional)
        prazo: Prazo de vigência
    """
    
    try:
        numero_contrato = f"CT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Cláusulas essenciais por tipo
        clausulas_por_tipo = {
            "prestacao_servicos": [
                "Descrição detalhada dos serviços",
                "Cronograma de execução",
                "Forma de pagamento",
                "Limitação de responsabilidade",
                "Confidencialidade",
                "Propriedade intelectual"
            ],
            "fornecimento": [
                "Especificações do produto",
                "Condições de entrega",
                "Garantia do produto",
                "Prazo de pagamento",
                "Penalidades por atraso",
                "Força maior"
            ],
            "distribuicao": [
                "Território de distribuição",
                "Exclusividade",
                "Metas de vendas",
                "Comissões",
                "Marketing e publicidade",
                "Rescisão"
            ]
        }
        
        clausulas_especificas = clausulas_por_tipo.get(tipo_contrato, [
            "Objeto do contrato",
            "Obrigações das partes", 
            "Condições de pagamento",
            "Prazo e rescisão",
            "Foro e lei aplicável"
        ])
        
        # Gerar minuta
        minuta = await _gerar_minuta_contrato(
            numero_contrato, tipo_contrato, partes, objeto, valor, prazo, clausulas_especificas
        )
        
        # Cláusulas críticas para atenção
        clausulas_criticas = [
            "Limitação de responsabilidade",
            "Resolução de conflitos", 
            "Rescisão contratual",
            "Propriedade intelectual",
            "Confidencialidade"
        ]
        
        return {
            "numero_contrato": numero_contrato,
            "tipo_contrato": tipo_contrato,
            "valor_contrato": valor,
            "minuta_contrato": minuta,
            "clausulas_incluidas": clausulas_especificas,
            "clausulas_criticas": clausulas_criticas,
            "prazo_vigencia": prazo,
            "numero_partes": len(partes),
            "proximos_passos": [
                "Revisão jurídica detalhada",
                "Aprovação pelas partes",
                "Coleta de documentos",
                "Assinatura e registro"
            ],
            "alertas": [
                "Verificar capacidade jurídica das partes",
                "Confirmar legislação aplicável",
                "Validar cláusulas especiais"
            ]
        }
        
    except Exception as e:
        return {"error": f"Erro na geração do contrato: {str(e)}"}


async def _gerar_minuta_contrato(numero, tipo, partes, objeto, valor, prazo, clausulas):
    """Gera minuta específica do contrato."""
    
    parte1 = partes[0] if partes else {"nome": "PARTE 1", "cnpj": "XX.XXX.XXX/0001-XX"}
    parte2 = partes[1] if len(partes) > 1 else {"nome": "PARTE 2", "cnpj": "YY.YYY.YYY/0001-YY"}
    
    minuta = f"""# CONTRATO DE {tipo.replace('_', ' ').upper()}
## Contrato nº {numero}

### PARTES CONTRATANTES

**CONTRATANTE:** {parte1.get('nome', 'EMPRESA 1')}  
CNPJ: {parte1.get('cnpj', 'XX.XXX.XXX/0001-XX')}  
Endereço: {parte1.get('endereco', 'Endereço da Empresa 1')}

**CONTRATADA:** {parte2.get('nome', 'EMPRESA 2')}  
CNPJ: {parte2.get('cnpj', 'YY.YYY.YYY/0001-YY')}  
Endereço: {parte2.get('endereco', 'Endereço da Empresa 2')}

### CLÁUSULA 1ª - OBJETO
O presente contrato tem por objeto: {objeto}

### CLÁUSULA 2ª - PRAZO
O prazo de vigência é de {prazo}, iniciando-se em {datetime.now().strftime('%d/%m/%Y')}.
"""
    
    if valor:
        minuta += f"""
### CLÁUSULA 3ª - VALOR E PAGAMENTO
O valor total do contrato é de R$ {valor:,.2f}, a ser pago conforme cronograma anexo.
"""
    
    # Adicionar cláusulas específicas
    for i, clausula in enumerate(clausulas[:5], 4):
        minuta += f"""
### CLÁUSULA {i}ª - {clausula.upper()}
{clausula} será regida conforme especificações técnicas e condições estabelecidas.
"""
    
    minuta += f"""
### CLÁUSULA FINAL - DISPOSIÇÕES GERAIS
- **Foro:** Comarca de São Paulo/SP
- **Lei Aplicável:** Legislação brasileira
- **Rescisão:** Conforme condições estabelecidas
- **Alterações:** Somente por escrito

**ASSINATURAS**

São Paulo, {datetime.now().strftime('%d de %B de %Y')}

_________________________        _________________________
{parte1.get('nome', 'CONTRATANTE')}            {parte2.get('nome', 'CONTRATADA')}

---
*Contrato elaborado por Vieira Pires Advogados*
"""
    
    return minuta


@tool
async def revisar_contrato(
    texto_contrato: str,
    pontos_atencao: List[str] = []
) -> Dict[str, Any]:
    """
    Analisa riscos e sugere melhorias em contrato.
    
    Args:
        texto_contrato: Texto do contrato para revisão
        pontos_atencao: Pontos específicos para análise
    """
    
    try:
        # Cláusulas essenciais que devem estar presentes
        clausulas_essenciais = {
            "objeto": "Definição clara do objeto contratual",
            "obrigacoes": "Obrigações específicas das partes",
            "prazo": "Prazo de vigência e condições",
            "pagamento": "Condições e forma de pagamento",
            "rescisao": "Condições de rescisão",
            "foro": "Foro de eleição",
            "lei_aplicavel": "Lei aplicável ao contrato",
            "forca_maior": "Cláusula de força maior",
            "confidencialidade": "Proteção de informações",
            "propriedade_intelectual": "Direitos de PI"
        }
        
        # Análise do texto (simulada)
        texto_lower = texto_contrato.lower()
        clausulas_presentes = []
        clausulas_ausentes = []
        
        for clausula, descricao in clausulas_essenciais.items():
            termos_busca = [clausula.replace("_", " "), clausula]
            if any(termo in texto_lower for termo in termos_busca):
                clausulas_presentes.append({"clausula": clausula, "descricao": descricao})
            else:
                clausulas_ausentes.append({"clausula": clausula, "descricao": descricao})
        
        # Identificar riscos potenciais
        riscos_identificados = []
        
        if "responsabilidade ilimitada" in texto_lower:
            riscos_identificados.append("Responsabilidade ilimitada - risco alto")
        
        if "multa" not in texto_lower and "penalidade" not in texto_lower:
            riscos_identificados.append("Ausência de penalidades por descumprimento")
        
        if "arbitragem" not in texto_lower and "mediação" not in texto_lower:
            riscos_identificados.append("Falta de método alternativo de resolução")
        
        if "exclusividade" in texto_lower:
            riscos_identificados.append("Cláusula de exclusividade - verificar adequação")
        
        # Sugestões de melhoria
        sugestoes = []
        
        if len(clausulas_ausentes) > 0:
            sugestoes.append(f"Incluir {len(clausulas_ausentes)} cláusulas essenciais ausentes")
        
        sugestoes.extend([
            "Revisar limitação de responsabilidade",
            "Incluir cláusula de compliance",
            "Definir método de resolução de conflitos",
            "Estabelecer cronograma detalhado"
        ])
        
        # Pontos de atenção específicos
        if pontos_atencao:
            sugestoes.extend([f"Atenção especial: {ponto}" for ponto in pontos_atencao])
        
        # Score de qualidade
        score = (len(clausulas_presentes) / len(clausulas_essenciais)) * 100
        
        return {
            "score_qualidade": round(score, 1),
            "nivel_risco": "Baixo" if score >= 80 else "Médio" if score >= 60 else "Alto",
            "clausulas_presentes": clausulas_presentes,
            "clausulas_ausentes": clausulas_ausentes,
            "riscos_identificados": riscos_identificados,
            "sugestoes_melhoria": sugestoes,
            "recomendacao": "Aprovado" if score >= 85 else "Aprovado com ressalvas" if score >= 70 else "Requer revisão",
            "pontos_criticos": [
                "Limitação de responsabilidade",
                "Condições de rescisão",
                "Foro e lei aplicável",
                "Penalidades"
            ]
        }
        
    except Exception as e:
        return {"error": f"Erro na revisão: {str(e)}"}


@tool
async def analisar_due_diligence(
    empresa_alvo: str,
    tipo_operacao: str,
    documentos_fornecidos: List[str] = []
) -> Dict[str, Any]:
    """
    Realiza análise de due diligence para M&A.
    
    Args:
        empresa_alvo: Nome da empresa analisada
        tipo_operacao: Tipo (aquisição, fusão, joint venture)
        documentos_fornecidos: Lista de documentos disponíveis
    """
    
    try:
        # Documentos essenciais para due diligence
        documentos_essenciais = {
            "societario": [
                "Contrato social atualizado",
                "Atas de assembleias",
                "Livros societários",
                "Participações societárias"
            ],
            "tributario": [
                "Certidões negativas",
                "Declarações fiscais (3 anos)",
                "Autos de infração",
                "Parcelamentos fiscais"
            ],
            "trabalhista": [
                "Certidão negativa trabalhista",
                "Contratos de trabalho",
                "Acordos coletivos",
                "Processos trabalhistas"
            ],
            "contratual": [
                "Contratos principais",
                "Contratos com terceiros",
                "Garantias prestadas",
                "Seguros contratados"
            ],
            "regulatorio": [
                "Licenças operacionais",
                "Alvarás municipais",
                "Certificações",
                "Processos administrativos"
            ]
        }
        
        # Verificar documentos fornecidos vs. necessários
        documentos_analisados = {}
        total_essenciais = 0
        fornecidos_essenciais = 0
        
        for categoria, docs in documentos_essenciais.items():
            total_essenciais += len(docs)
            fornecidos = 0
            faltantes = []
            
            for doc in docs:
                if any(doc.lower() in fornecido.lower() for fornecido in documentos_fornecidos):
                    fornecidos += 1
                    fornecidos_essenciais += 1
                else:
                    faltantes.append(doc)
            
            documentos_analisados[categoria] = {
                "fornecidos": fornecidos,
                "total": len(docs),
                "percentual": (fornecidos / len(docs)) * 100,
                "faltantes": faltantes
            }
        
        # Riscos identificados por categoria
        riscos_por_categoria = {
            "Alto": [],
            "Médio": [],
            "Baixo": []
        }
        
        for categoria, analise in documentos_analisados.items():
            if analise["percentual"] < 50:
                riscos_por_categoria["Alto"].append(f"Documentação {categoria} insuficiente")
            elif analise["percentual"] < 80:
                riscos_por_categoria["Médio"].append(f"Documentação {categoria} incompleta")
            else:
                riscos_por_categoria["Baixo"].append(f"Documentação {categoria} adequada")
        
        # Recomendações específicas
        recomendacoes = []
        
        if documentos_analisados["tributario"]["percentual"] < 80:
            recomendacoes.append("Priorizar análise tributária - risco fiscal alto")
        
        if documentos_analisados["trabalhista"]["percentual"] < 80:
            recomendacoes.append("Revisar passivos trabalhistas - contingências possíveis")
        
        if documentos_analisados["contratual"]["percentual"] < 70:
            recomendacoes.append("Analisar contratos principais - obrigações não mapeadas")
        
        recomendacoes.extend([
            "Realizar visita técnica às instalações",
            "Entrevistar gestores-chave",
            "Validar informações financeiras",
            "Verificar licenças operacionais"
        ])
        
        # Score geral
        score_geral = (fornecidos_essenciais / total_essenciais) * 100
        
        return {
            "empresa_analisada": empresa_alvo,
            "tipo_operacao": tipo_operacao,
            "score_due_diligence": round(score_geral, 1),
            "documentos_por_categoria": documentos_analisados,
            "riscos_identificados": riscos_por_categoria,
            "recomendacoes": recomendacoes,
            "status_analise": "Completa" if score_geral >= 85 else "Em andamento" if score_geral >= 60 else "Insuficiente",
            "proximas_etapas": [
                "Completar documentação faltante",
                "Análise jurídica detalhada",
                "Avaliação de contingências",
                "Estruturação da operação"
            ],
            "prazo_conclusao": "15-30 dias úteis",
            "nivel_complexidade": "Alta" if score_geral < 60 else "Média" if score_geral < 80 else "Baixa"
        }
        
    except Exception as e:
        return {"error": f"Erro na análise: {str(e)}"}


# Nodos do agente
async def contratos_analyzer_node(state: ContratosAgentState, config: RunnableConfig) -> Command:
    """Analisa demanda contratual."""
    
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Analisando demanda contratual",
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
    
    tools = [gerar_contrato, revisar_contrato, analisar_due_diligence]
    
    system_prompt = """
    Você é especialista em Contratos Empresariais do Vieira Pires Advogados.
    
    EXPERTISE:
    📄 Contratos empresariais complexos
    🤝 Contratos de prestação de serviços
    📦 Contratos de fornecimento e distribuição
    🏢 M&A e due diligence
    🌍 Contratos internacionais
    
    LEGISLAÇÃO:
    - Código Civil (Arts. 421-480)
    - CDC (proteção contratual)
    - Lei de Arbitragem (9.307/96)
    - Marco Civil da Internet
    
    PRINCÍPIOS:
    - Equilíbrio entre proteção e viabilidade
    - Clareza e precisão nas cláusulas
    - Prevenção de litígios
    - Conformidade regulatória
    
    Use sempre as ferramentas para elaboração e análise precisa.
    """
    
    last_message = state.messages[-1].content if state.messages else "Análise contratual"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Consulta: {last_message}")
    ]
    
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(messages, config)
    
    state.tool_logs[-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        return Command(goto="execute_contratos", update={"messages": [response]})
    else:
        return Command(goto="finalize_contratos", update={"messages": [response]})


async def execute_contratos_node(state: ContratosAgentState, config: RunnableConfig) -> Command:
    """Executa ferramentas contratuais."""
    
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
                if tool_name == "gerar_contrato":
                    result = await gerar_contrato.ainvoke(tool_args)
                    if "minuta_contrato" in result:
                        state.contratos_gerados.append(result["tipo_contrato"])
                        state.clausulas_criticas.extend(result.get("clausulas_criticas", []))
                elif tool_name == "revisar_contrato":
                    result = await revisar_contrato.ainvoke(tool_args)
                elif tool_name == "analisar_due_diligence":
                    result = await analisar_due_diligence.ainvoke(tool_args)
                else:
                    result = {"error": f"Ferramenta desconhecida: {tool_name}"}
                
                results.append({"tool": tool_name, "result": result, "success": "error" not in result})
                state.tool_logs[-1]["status"] = "completed"
                
            except Exception as e:
                results.append({"tool": tool_name, "error": str(e), "success": False})
                state.tool_logs[-1]["status"] = "failed"
            
            await copilotkit_emit_state(config, state)
    
    return Command(goto="finalize_contratos", update={"resultados_ferramentas": results})


async def finalize_contratos_node(state: ContratosAgentState, config: RunnableConfig) -> Command:
    """Finaliza com parecer contratual."""
    
    state.tool_logs.append({
        "id": str(uuid.uuid4()),
        "message": "Finalizando análise contratual",
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    })
    await copilotkit_emit_state(config, state)
    
    parecer = "# PARECER CONTRATUAL\n"
    parecer += "## Vieira Pires Advogados - Contratos Empresariais\n\n"
    parecer += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if state.contratos_gerados:
        parecer += "## CONTRATOS ELABORADOS\n"
        for contrato in state.contratos_gerados:
            parecer += f"📄 {contrato.replace('_', ' ').title()}\n"
        parecer += "\n"
    
    if state.clausulas_criticas:
        parecer += "## CLÁUSULAS CRÍTICAS\n"
        for clausula in set(state.clausulas_criticas[:5]):
            parecer += f"⚠️ {clausula}\n"
        parecer += "\n"
    
    parecer += """## RECOMENDAÇÕES
1. **Revisão:** Análise detalhada das cláusulas críticas
2. **Negociação:** Equilíbrio de riscos entre as partes
3. **Compliance:** Adequação às normas aplicáveis
4. **Execução:** Acompanhamento da implementação

## PRÓXIMOS PASSOS
1. Aprovação das minutas pelas partes
2. Negociação de pontos sensíveis
3. Assinatura e formalização
4. Acompanhamento da execução

---
*Departamento Contratual - Vieira Pires Advogados*
"""
    
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(goto=END, update={"messages": [AIMessage(content=parecer)]})


def create_contratos_agent_graph() -> StateGraph:
    """Cria grafo do agente de contratos."""
    
    workflow = StateGraph(ContratosAgentState)
    
    workflow.add_node("analyzer", contratos_analyzer_node)
    workflow.add_node("execute_contratos", execute_contratos_node)
    workflow.add_node("finalize_contratos", finalize_contratos_node)
    
    workflow.set_entry_point("analyzer")
    workflow.set_finish_point("finalize_contratos")
    
    workflow.add_edge(START, "analyzer")
    workflow.add_edge("execute_contratos", "finalize_contratos")
    workflow.add_edge("finalize_contratos", END)
    
    return workflow.compile(checkpointer=MemorySaver())


contratos_agent_graph = create_contratos_agent_graph()