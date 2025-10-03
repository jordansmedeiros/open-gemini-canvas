        if "reasoning" in decision:
            reasoning = decision["reasoning"]
            report += f"### Raciocínio da Seleção\n"
            report += f"- **Método:** {reasoning.get('selection_method', 'N/A')}\n\n"
    
    report += "## EFICIÊNCIA DO ROTEAMENTO\n"
    report += "✅ **Análise Contextual:** Urgência e complexidade avaliadas\n"
    report += "✅ **Balanceamento:** Carga dos agentes considerada\n"
    report += "✅ **Especialização:** Capacidades correspondidas\n"
    report += "✅ **Otimização:** Performance monitorada\n\n"
    
    report += "---\n"
    report += "*Sistema de Roteamento Inteligente - Vieira Pires Advogados*"
    
    state.tool_logs[-1]["status"] = "completed"
    state.tool_logs = []
    await copilotkit_emit_state(config, state)
    
    return Command(goto=END, update={"messages": [AIMessage(content=report)]})


def create_routing_graph() -> StateGraph:
    """Cria grafo de roteamento inteligente."""
    
    workflow = StateGraph(RoutingState)
    
    workflow.add_node("analyzer", routing_analyzer_node)
    workflow.add_node("execute_routing", execute_routing_node)
    workflow.add_node("finalize_routing", finalize_routing_node)
    
    workflow.set_entry_point("analyzer")
    workflow.set_finish_point("finalize_routing")
    
    workflow.add_edge(START, "analyzer")
    workflow.add_edge("execute_routing", "finalize_routing")
    workflow.add_edge("finalize_routing", END)
    
    return workflow.compile(checkpointer=MemorySaver())


routing_graph = create_routing_graph()