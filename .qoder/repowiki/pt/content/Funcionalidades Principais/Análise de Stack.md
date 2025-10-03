# Análise de Stack

<cite>
**Arquivos Referenciados neste Documento**   
- [stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx)
- [agent/stack_agent.py](file://agent/stack_agent.py)
- [components/ui/stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx)
- [app/prompts/prompts.ts](file://app/prompts/prompts.ts)
</cite>

## Sumário
1. [Introdução](#introdução)
2. [Fluxo de Entrada do Usuário](#fluxo-de-entrada-do-usuário)
3. [Arquitetura do Backend e Fluxo de Trabalho](#arquitetura-do-backend-e-fluxo-de-trabalho)
4. [Estrutura de Estado do Agente](#estrutura-de-estado-do-agente)
5. [Renderização dos Resultados](#renderização-dos-resultados)
6. [Prompts de Análise](#prompts-de-análise)
7. [Casos de Uso e Interpretação](#casos-de-uso-e-interpretação)
8. [Limitações e Dicas](#limitações-e-dicas)

## Introdução
A funcionalidade de Análise de Stack é um sistema integrado que permite aos usuários fornecer a URL de um repositório público do GitHub e receber uma análise detalhada da tecnologia utilizada no projeto. O sistema combina uma interface web com um agente de IA backend, utilizando a API do GitHub para coletar metadados e o modelo de IA Google Gemini para inferir e estruturar insights sobre a stack tecnológica (frontend, backend, banco de dados, infraestrutura, etc.). Este documento detalha todo o fluxo, desde a entrada do usuário até a exibição final dos resultados.

## Fluxo de Entrada do Usuário
O ponto de entrada para a funcionalidade de Análise de Stack é a interface de usuário localizada em `stack-analyzer/page.tsx`. O usuário interage com um campo de entrada de texto onde pode digitar uma mensagem contendo a URL de um repositório do GitHub. A interface também fornece ações rápidas (quick actions) que preenchem automaticamente a entrada com URLs de repositórios populares, como o do freeCodeCamp ou do React, para facilitar o teste.

Quando o usuário envia a mensagem, o componente `CopilotChat` captura o conteúdo e o envia ao agente de IA. O agente é gerenciado pelo hook `useCoAgent`, que é inicializado com o nome `stack_analysis_agent`. O estado inicial desse agente é definido com `tool_logs` vazio, `show_cards` definido como `false` e `analysis` como uma string vazia. O envio da mensagem aciona o fluxo de trabalho do agente no backend.

**Seção fontes**
- [stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx#L61-L110)

## Arquitetura do Backend e Fluxo de Trabalho
O backend da funcionalidade é implementado no arquivo `stack_agent.py` como um grafo de estado (`StateGraph`) usando a biblioteca LangGraph. O fluxo de trabalho é composto por três nós principais: `gather_context`, `analyze` e `end`.

O nó `gather_context_node` é o ponto de entrada. Ele extrai a URL do GitHub da última mensagem do usuário usando a função `_parse_github_url`. Em seguida, realiza uma série de chamadas à API do GitHub para coletar metadados do repositório, incluindo informações gerais do repositório, linguagens utilizadas, o conteúdo do README, a lista de arquivos na raiz e o conteúdo de arquivos de manifesto comuns (como `package.json` ou `requirements.txt`). Todos esses dados são agregados em um dicionário `context`.

Após a coleta de contexto, o fluxo avança para o nó `analyze_with_gemini_node`. Neste nó, o contexto coletado é formatado em um prompt de texto que instrui o modelo de IA (Google Gemini) a atuar como um arquiteto de software sênior. O prompt fornece todos os metadados coletados e solicita uma análise estruturada do stack tecnológico. O modelo é instruído a usar a ferramenta `return_stack_analysis` para retornar seus resultados em um formato JSON estrito, definido pela classe `StructuredStackAnalysis`.

**Seção fontes**
- [agent/stack_agent.py](file://agent/stack_agent.py#L266-L303)
- [agent/stack_agent.py](file://agent/stack_agent.py#L338-L379)
- [agent/stack_agent.py](file://agent/stack_agent.py#L377-L411)

## Estrutura de Estado do Agente
O estado do agente é definido pela classe `StackAgentState`, que herda de `CopilotKitState`. Essa classe define os campos que persistem durante a execução do fluxo de trabalho. Os dois campos mais críticos para a funcionalidade de UI são `show_cards` e `analysis`.

O campo `show_cards` é um booleano que atua como um sinalizador para a interface do usuário. Quando o agente inicia, `show_cards` é `false`, e a interface exibe uma tela de boas-vindas. Durante a análise, quando o modelo de IA retorna um resultado bem-sucedido, o campo `show_cards` é explicitamente definido como `true` dentro do nó `analyze_with_gemini_node`. Isso dispara uma atualização de estado que é capturada pela interface.

O campo `analysis` é uma string que armazena a representação JSON do resultado da análise. Quando o modelo de IA faz uma chamada para a ferramenta `return_stack_analysis`, os argumentos dessa chamada são serializados em JSON e armazenados neste campo. Esse campo é então passado diretamente para o componente de UI responsável por renderizar os resultados.

**Seção fontes**
- [agent/stack_agent.py](file://agent/stack_agent.py#L409-L436)
- [stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx#L61-L110)

## Renderização dos Resultados
A renderização dos resultados é gerenciada pelo componente `StackAnalysisCards`, localizado em `components/ui/stack-analysis-cards.tsx`. Este componente é condicionalmente renderizado na interface principal quando o valor de `state.show_cards` é `true`.

O componente `StackAnalysisCards` recebe a string JSON do campo `state.analysis` como uma propriedade. Ele tenta analisar essa string em um objeto JavaScript que corresponde à interface `StackAnalysis`. Se a análise falhar ou o objeto estiver vazio, o componente exibe uma mensagem indicando que nenhuma análise está disponível.

Se os dados forem válidos, o componente mapeia o objeto de análise para uma série de cartões (cards) organizados em duas seções. A primeira seção exibe cartões para `purpose`, `frontend`, `backend`, `database`, `infrastructure` e `ci_cd`. A segunda seção exibe cartões para `key_root_files`, `how_to_run` e `risks_notes`, se esses dados estiverem presentes. Cada cartão utiliza ícones e uma estrutura de lista de definições para apresentar as informações de forma clara e visualmente atraente.

**Seção fontes**
- [components/ui/stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L0-L48)
- [components/ui/stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L107-L153)
- [stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx#L296-L317)

## Prompts de Análise
Os prompts utilizados para guiar o modelo de IA são definidos em `app/prompts/prompts.ts`. O prompt principal para a análise de stack é construído dinamicamente no backend, mas as instruções do sistema são fixas. O prompt instrui o modelo a atuar como um arquiteto de software sênior e a sempre chamar a ferramenta `return_stack_analysis` com todos os campos aplicáveis preenchidos. O prompt fornece ao modelo um contexto rico, incluindo metadados do repositório, linguagens, arquivos raiz, manifestos e o conteúdo do README, truncado para os primeiros 8000 caracteres.

O prompt também instrui o modelo a inferir tecnologias específicas, como Next.js, Express, FastAPI, Prisma ou Postgres, sempre que possível, com base nos arquivos de manifesto e no conteúdo do código. No frontend, o prompt `suggestionPrompt1` é usado para gerar sugestões de repositórios públicos para análise, garantindo que os usuários tenham exemplos prontos para testar a funcionalidade.

**Seção fontes**
- [agent/stack_agent.py](file://agent/stack_agent.py#L266-L303)
- [app/prompts/prompts.ts](file://app/prompts/prompts.ts#L20-L23)

## Casos de Uso e Interpretação
Um caso de uso comum para esta funcionalidade é a análise de projetos open-source. Um desenvolvedor pode usar a ferramenta para rapidamente entender a arquitetura de um projeto antes de contribuir ou de usá-lo como base para seu próprio trabalho. Para interpretar os resultados, o usuário deve examinar os cartões gerados. O cartão "Purpose" fornece uma visão geral do objetivo do projeto. Os cartões "Frontend" e "Backend" detalham as tecnologias principais, como linguagens, frameworks e bibliotecas-chave. O cartão "Database" indica o tipo de banco de dados utilizado, e o cartão "Infrastructure" pode revelar onde o frontend e o backend são hospedados. O cartão "How To Run" é particularmente útil, pois fornece um resumo e passos para executar o projeto localmente.

## Limitações e Dicas
A funcionalidade tem algumas limitações importantes. Ela só pode analisar repositórios públicos do GitHub, pois depende da API pública. Repositórios privados não podem ser acessados sem credenciais adequadas. Além disso, a precisão da análise depende fortemente da estrutura do repositório. Projetos com estruturas atípicas ou arquivos de manifesto ausentes podem resultar em uma análise imprecisa ou incompleta.

Para melhorar a precisão da análise, é essencial fornecer URLs completas e válidas do GitHub. A URL deve apontar diretamente para a página do repositório (por exemplo, `https://github.com/user/repo`). URLs malformadas ou que não contêm o padrão `github.com/owner/repo` serão ignoradas. Além disso, repositórios com um README bem escrito e arquivos de manifesto claros (como `package.json` ou `requirements.txt`) tendem a produzir análises mais completas e confiáveis.