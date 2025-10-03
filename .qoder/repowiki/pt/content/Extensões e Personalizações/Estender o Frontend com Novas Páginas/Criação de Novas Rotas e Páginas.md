# Criação de Novas Rotas e Páginas

<cite>
**Arquivos Referenciados neste Documento**  
- [app/post-generator/page.tsx](file://app/post-generator/page.tsx)
- [app/stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx)
- [app/layout.tsx](file://app/layout.tsx)
- [app/contexts/LayoutContext.tsx](file://app/contexts/LayoutContext.tsx)
- [app/wrapper.tsx](file://app/wrapper.tsx)
- [components/ui/stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx)
- [package.json](file://package.json)
</cite>

## Sumário
1. [Introdução](#introdução)
2. [Estrutura de Diretórios no Next.js](#estrutura-de-diretórios-no-nextjs)
3. [Criação de uma Nova Página](#criação-de-uma-nova-página)
4. [Uso de Hooks: useCoAgent e useCopilotChat](#uso-de-hooks-usecoagent-e-usecopilothchat)
5. [Configuração do Layout com Contexto](#configuração-do-layout-com-contexto)
6. [Integração com Componentes UI Existentes](#integração-com-componentes-ui-existentes)
7. [Replicação de Funcionalidades Existentes](#replicação-de-funcionalidades-existentes)
8. [Boas Práticas de Organização de Código](#boas-práticas-de-organização-de-código)
9. [Conclusão](#conclusão)

## Introdução
Este guia detalha o processo de criação de novas páginas no frontend do projeto Next.js, seguindo a estrutura atual do repositório. O foco está em como criar novas rotas dentro do diretório `app/`, configurar o componente `page.tsx` com os hooks necessários, integrar com o sistema de agentes e manter a consistência com os padrões de UI e arquitetura já estabelecidos. O objetivo é permitir a implementação rápida e padronizada de novas funcionalidades, como as páginas `post-generator` e `stack-analyzer`.

## Estrutura de Diretórios no Next.js
O projeto utiliza a estrutura do App Router do Next.js, onde cada diretório dentro de `app/` representa uma rota. A organização atual inclui:

- `app/post-generator/` – Página para geração de posts
- `app/stack-analyzer/` – Página para análise de stacks de projetos
- `app/api/` – Rotas de API
- `app/contexts/` – Provedores de contexto
- `app/globals.css`, `layout.tsx`, `page.tsx`, `wrapper.tsx` – Arquivos principais do layout global

Para criar uma nova página, basta adicionar um novo diretório em `app/` com o nome da rota desejada (ex: `app/nova-funcionalidade/`) e incluir um arquivo `page.tsx`.

**Section sources**
- [app/post-generator/page.tsx](file://app/post-generator/page.tsx#L1-L411)
- [app/stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx#L1-L348)

## Criação de uma Nova Página
Para criar uma nova página:

1. **Crie um novo diretório** em `app/` com o nome da funcionalidade (ex: `app/nova-ferramenta/`).
2. **Adicione um arquivo `page.tsx`** dentro do diretório.
3. **Defina o componente funcional** com `"use client"` no início para habilitar interatividade no cliente.
4. **Importe os componentes e hooks necessários** do projeto.

Exemplo básico:
```tsx
"use client"
import { useCoAgent, useCopilotChat } from "@copilotkit/react-core"
import { Button } from "@/components/ui/button"

export default function NovaFerramenta() {
  return (
    <div>Conteúdo da nova ferramenta</div>
  )
}
```

**Section sources**
- [app/post-generator/page.tsx](file://app/post-generator/page.tsx#L1-L411)

## Uso de Hooks: useCoAgent e useCopilotChat
Os hooks principais para integração com o sistema de agentes são:

### `useCoAgent`
Inicializa um agente com estado persistente. Deve ser usado com o nome do agente definido no backend (ex: `"post_generation_agent"`).

```tsx
const { setState, running } = useCoAgent({
  name: "nome_do_agente",
  initialState: {
    tool_logs: []
  }
})
```

### `useCopilotChat`
Gerencia a comunicação com o chat do CopilotKit, permitindo o envio e recebimento de mensagens.

```tsx
const { appendMessage, setMessages } = useCopilotChat()
```

### `useCopilotAction`
Define ações que o agente pode executar, como renderizar conteúdo dinâmico.

```tsx
useCopilotAction({
  name: "gerar_conteudo",
  handler: (args) => {
    // Atualiza estado com conteúdo gerado
  },
  render: ({ args }) => {
    // Renderiza componente com base nos argumentos
  }
})
```

**Section sources**
- [app/post-generator/page.tsx](file://app/post-generator/page.tsx#L100-L150)
- [app/stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx#L100-L130)

## Configuração do Layout com Contexto
O layout global é gerenciado pelo `LayoutContext`, que permite atualizar dinamicamente o título, descrição e agente ativo.

### `useLayout`
Hook para acessar e atualizar o estado do layout:

```tsx
const { updateLayout } = useLayout()
```

Ao mudar de rota, o layout pode ser atualizado:

```tsx
updateLayout({ 
  agent: "novo_agente_id",
  title: "Novo Título",
  description: "Nova descrição"
})
```

O componente `wrapper.tsx` envolve o conteúdo com `CopilotKit`, usando o agente definido no contexto:

```tsx
<CopilotKit runtimeUrl="/api/copilotkit" agent={layoutState.agent}>
  {children}
</CopilotKit>
```

**Section sources**
- [app/contexts/LayoutContext.tsx](file://app/contexts/LayoutContext.tsx#L1-L54)
- [app/wrapper.tsx](file://app/wrapper.tsx#L1-L12)

## Integração com Componentes UI Existentes
O projeto utiliza componentes UI baseados no Radix UI e Tailwind CSS, localizados em `components/ui/`. Para manter a consistência:

- Use componentes como `Button`, `Textarea`, `Card`, `Badge`, `ScrollArea`, etc.
- Importe diretamente de `@/components/ui/nome-componente`
- Utilize classes de utilidade do Tailwind e `cn` para composição de classes

Exemplo:
```tsx
<Button variant="outline" className="bg-white/50 backdrop-blur-sm">
  <Send className="mr-2 h-4 w-4" />
  Enviar
</Button>
```

Componentes específicos como `XPost`, `LinkedInPost`, `StackAnalysisCards` podem ser reutilizados ou adaptados.

**Section sources**
- [components/ui/stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L1-L259)
- [app/post-generator/page.tsx](file://app/post-generator/page.tsx#L20-L30)

## Replicação de Funcionalidades Existentes
Para replicar funcionalidades como `post-generator` ou `stack-analyzer`:

1. **Copie a estrutura básica** do `page.tsx` de uma página existente.
2. **Ajuste o nome do agente** no `useCoAgent`.
3. **Atualize os prompts** (se houver) em `prompts.ts`.
4. **Modifique os componentes de renderização** no `useCopilotAction`.
5. **Atualize o cabeçalho e ações rápidas** conforme necessário.

Exemplo de adaptação:
- Substitua `post_generation_agent` por `novo_agente`
- Altere os `quickActions` para prompts relevantes
- Atualize os componentes de preview (`XPostPreview`, `LinkedInPostPreview`) para o novo conteúdo

**Section sources**
- [app/post-generator/page.tsx](file://app/post-generator/page.tsx#L1-L411)
- [app/stack-analyzer/page.tsx](file://app/stack-analyzer/page.tsx#L1-L348)

## Boas Práticas de Organização de Código
- **Nomenclatura clara**: Use nomes descritivos para diretórios e componentes.
- **Separação de concerns**: Mantenha lógica de UI separada da lógica de negócios.
- **Reutilização de componentes**: Evite duplicação usando componentes em `components/ui/`.
- **Gestão de estado**: Use `useCoAgent` para estado compartilhado entre agente e UI.
- **Tipagem TypeScript**: Defina interfaces para dados complexos (ex: `PostInterface`).
- **Efeitos colaterais**: Use `useEffect` com cuidado, evitando loops infinitos.

**Section sources**
- [app/post-generator/page.tsx](file://app/post-generator/page.tsx#L40-L50)
- [components/ui/stack-analysis-cards.tsx](file://components/ui/stack-analysis-cards.tsx#L10-L30)

## Conclusão
A criação de novas páginas no frontend Next.js deste projeto segue um padrão claro e reutilizável. Ao seguir a estrutura do App Router, utilizar os hooks `useCoAgent` e `useCopilotChat`, integrar com o `LayoutContext` e reutilizar componentes UI, é possível implementar novas funcionalidades de forma rápida, consistente e escalável. A chave está em replicar os padrões das páginas existentes enquanto adapta os detalhes específicos da nova funcionalidade.