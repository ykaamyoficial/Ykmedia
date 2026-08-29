# Frontend React + Tauri

> **Status:** migracao concluida. A interface PySide6 (`app/desktop/`) foi
> removida; as mencoes a ela neste documento sao historicas e descrevem o
> comportamento que a interface React/Tauri agora reproduz.

## Arquitetura

A nova interface desktop fica separada do backend Python:

- `app/`: backend FastAPI existente.
- `frontend/`: React, TypeScript, Vite, Tailwind CSS, shell visual e testes.
- `src-tauri/`: empacotamento desktop Tauri.

O React consulta o backend por HTTP. Nenhuma regra de negocio foi movida para o frontend.

## Shell Da Aplicacao

O shell permanente fica em `frontend/src/components/system/YkAppShell.tsx`.

Estrutura:

- Header fixo: `YkHeader`.
- Sidebar fixa/compactavel: `YkSidebar`.
- Conteudo roteado: `Outlet` do React Router.

O shell e responsavel somente por estrutura visual e navegacao.

## Design System

Componentes base criados em `frontend/src/components/system/`:

- `YkAppShell`
- `YkSidebar`
- `YkSidebarItem`
- `YkSidebarSection`
- `YkHeader`
- `YkPage`
- `YkPanel`
- `YkCard`
- `YkButton`
- `YkSearch`
- `YkStatusBadge`
- `YkAvatar`
- `YkEmptyState`
- `YkLoading`
- `YkSeparator`
- `YkTooltip`

Tokens oficiais:

- CSS variables em `frontend/src/styles/globals.css`.
- Tokens TypeScript em `frontend/src/styles/tokens.ts`.

## Providers

Providers criados em `frontend/src/providers/`:

- `ThemeProvider`: tema claro, escuro e automatico.
- `AppProvider`: estado visual do shell, como sidebar compacta.
- `BackendStatusProvider`: centraliza o health check do backend.
- `RootProviders`: composicao dos providers principais.
- `UserPreferencesProvider`: preferencias locais do usuario.
- `PermissionProvider`: base futura de permissoes.
- `DialogProvider`: renderizacao centralizada de dialogs.
- `ToastProvider`: renderizacao centralizada de toasts.

Componentes do shell devem consumir `BackendStatusProvider`; nao devem consultar `/health` diretamente.

## Infraestrutura Compartilhada

A infraestrutura reutilizavel fica em `frontend/src/shared/`.

Estrutura:

- `components/`: loading, empty states, paginacao e busca.
- `config/`: preferencias locais e hooks de configuracao.
- `constants/`: rotas, timeouts, mensagens e tokens compartilhados.
- `dialogs/`: servico e provider oficial de dialogs.
- `errors/`: erros da aplicacao, mensagens amigaveis e ErrorBoundary.
- `events/`: Event Bus interno.
- `forms/`: formulario oficial baseado em React Hook Form.
- `hooks/`: hooks reutilizaveis.
- `icons/`: unico ponto permitido para importar icones externos.
- `rbac/`: infraestrutura futura de permissoes.
- `services/`: cliente HTTP oficial.
- `tables/`: tabela oficial baseada em TanStack Table.
- `toast/`: servico e provider oficial de toasts.
- `utils/`: formatadores e utilitarios puros.
- `validators/`: base de validacao com Zod.
- `websocket/`: estrutura futura de conexao em tempo real.

Nenhuma feature deve depender diretamente de outra feature. Codigo reutilizavel deve ser promovido para `shared`.

Os diretorios compartilhados principais possuem `index.ts` para manter imports curtos e permitir refatoracoes internas sem impacto nos modulos.

## Padrao De Features

Toda feature nova deve seguir o mesmo formato:

```text
frontend/src/features/nome-da-feature/
  api/
  components/
  hooks/
  pages/
  types/
  utils/
  index.ts
```

Regras:

- `api/`: somente comunicacao HTTP da feature.
- `components/`: componentes especificos da feature.
- `hooks/`: hooks especificos da feature.
- `pages/`: paginas roteadas da feature.
- `types/`: DTOs, schemas e tipos especificos.
- `utils/`: formatadores e utilitarios especificos da feature.
- `index.ts`: API publica da feature.

Arquivos fora da feature devem importar apenas da API publica da feature.

```ts
import { DashboardPage } from "@/features/dashboard";
```

Nao importar arquivos internos de outra feature.

## Barrels E Imports

Use aliases `@/...` em todo o frontend.

Evitar imports relativos longos como `../../../shared`.

Diretorios com API publica devem possuir `index.ts`.

## Cliente HTTP Oficial

O unico cliente HTTP permitido fica em:

```text
frontend/src/shared/services/http-client.ts
```

Responsabilidades:

- URL base centralizada por `VITE_API_BASE_URL`.
- timeout configuravel.
- retry configuravel.
- headers padrao.
- interceptors.
- cancelamento via `AbortSignal`.
- tratamento de erro de rede.
- tratamento de erro HTTP.
- tratamento de JSON invalido.

Componentes React nao devem chamar `fetch()` diretamente.

## TanStack Query

A configuracao oficial fica em:

```text
frontend/src/shared/query/query-client.ts
frontend/src/shared/query/query-keys.ts
```

Regras:

- criar QueryClient apenas por `createAppQueryClient()`;
- query keys devem vir de `queryKeys`;
- hooks de feature devem usar TanStack Query;
- componentes visuais nao devem montar URLs nem chamar HTTP diretamente.

Padroes atuais:

- `staleTime`: 10 segundos;
- `gcTime`: 5 minutos;
- `retry`: 1;
- `refetchOnWindowFocus`: false.

## Erros

Erros oficiais:

- `AppError`
- `NetworkError`
- `ValidationError`
- `ServerError`
- `UnknownError`

Use `friendlyErrorMessage()` para mensagens exibidas ao usuario. Erros crus da API nao devem aparecer em tela.

`ErrorBoundary` envolve apenas a area roteada do shell. Assim, se uma feature falhar, Header e Sidebar continuam disponiveis.

Estados visuais oficiais:

- `YkNoDataState`
- `YkNoConnectionState`
- `YkOfflineState`
- `YkErrorState`
- `YkNoPermissionState`
- `YkForbiddenState`
- `YkNoResultsState`
- `YkNoHistoryState`

Telas futuras devem usar esses componentes para loading, vazio, erro, proibido e offline.

## Toasts E Dialogs

Toasts devem usar somente:

```ts
toast.success("Mensagem");
toast.error("Mensagem");
toast.warning("Mensagem");
toast.info("Mensagem");
toast.loading("Mensagem");
```

Dialogs devem usar somente `dialog.confirm()`, `dialog.alert()`, `dialog.info()`, `dialog.error()` ou `dialog.question()`.

Bibliotecas ou implementacoes visuais nao devem ser importadas diretamente por features.

## Formularios

Formularios devem usar:

- `YkForm`
- `YkInput`
- `YkTextarea`
- `YkSelect`
- `YkCheckbox`
- `YkSwitch`
- `YkRadio`
- `YkDatePicker`

A base esta preparada para React Hook Form e Zod. Formularios reais de modulos serao criados em fases futuras.

## Tabelas, Busca E Paginacao

Tabelas devem usar `YkDataTable`.

Busca deve usar `YkSearchBox`, que ja prepara debounce e limpeza rapida.

Paginacao deve usar `YkPagination`.

Cada modulo futuro deve configurar apenas colunas, filtros e dados; nao deve recriar tabela, busca ou paginacao.

## Eventos E Tempo Real

O Event Bus interno fica em:

```text
frontend/src/shared/events/event-bus.ts
```

Ele deve ser usado para comunicacao desacoplada entre infraestrutura global e componentes distantes.

A estrutura de WebSocket foi criada em:

```text
frontend/src/shared/websocket/
```

Ainda nao existe conexao real. A camada esta pronta para estados, eventos e reconexao futura.

## Icones

Nenhum componente deve importar `lucide-react` diretamente.

Use sempre:

```ts
import { YkIcons } from "@/shared/icons";
```

Isso mantem consistencia visual e permite trocar a biblioteca de icones no futuro sem tocar nos modulos.

## Hooks Reutilizaveis

Hooks compartilhados disponiveis:

- `useDebounce`
- `useLocalStorage`
- `useToggle`
- `usePrevious`
- `useEventListener`
- `useMediaQuery`
- `useOnlineStatus`
- `useClipboard`

Antes de criar um novo hook, verificar se ja existe equivalente em `shared/hooks`.

## Fluxo De Dados

Fluxo recomendado para novas telas:

```text
Feature -> hook/api da feature -> httpClient -> FastAPI
Feature -> shared components -> UI
Feature -> toast/dialog/event bus -> feedback global
```

Regras:

- regra de negocio permanece no backend;
- frontend orquestra exibicao, estado visual e chamadas HTTP;
- componentes nao devem chamar infraestrutura externa diretamente quando houver servico oficial;
- novas features devem ser carregaveis sem acoplar uma feature a outra.

## Dashboard Operacional

O primeiro modulo real do frontend fica em:

```text
frontend/src/features/dashboard/
```

Estrutura:

- `components/`: cards, secoes e tabela recente do Dashboard.
- `api/`: chamada HTTP da feature.
- `hooks/`: hook oficial da feature.
- `pages/`: pagina roteada.
- `types/`: schema Zod e tipos TypeScript.
- `utils/`: formatadores especificos da feature.
- `tests/`: testes da feature.
- `index.ts`: API publica da feature.

O Dashboard nao contem regra de negocio no React. Ele apenas apresenta o DTO consolidado pelo backend, reproduzindo o comportamento da tela PySide6.

### Endpoint

Endpoint unico:

```text
GET /dashboard/overview
```

O endpoint chama `DashboardService` e nao possui logica propria.

### DTO

O DTO `DashboardOverview` contem mais dados do que a tela exibe, para reutilizacao futura. Na migracao do Dashboard, a tela utiliza somente os dados equivalentes ao PySide6.

- `generated_at`
- `system`: versao, uptime, backend online e banco conectado.
- `evolution`: status, instancia, ultima sincronizacao e erro controlado.
- `whatsapp`: conectado, desconectado ou QR pendente.
- `downloads`: em andamento, concluidos, falhas e fila.
- `files`: quantidade armazenada, espaco utilizado e categorias.
- `conversations`: total, contatos ativos e ultimas mensagens.
- `history`: ultimas atividades de midia.
- `health`: Backend, Banco, Evolution, WhatsApp e Storage.
- `has_data`

### Origem Dos Dados

As informacoes sao reunidas no backend a partir de fontes reais ja existentes:

- `StorageService.list_processing_jobs()`
- `StorageService.list_media_history()`
- `StorageService.list_sessions()`
- `StorageService.list_categories()`
- `StorageService.list_conversation_contacts()`
- `EvolutionClient.health()`
- `EvolutionClient.get_connection_state()`
- configuracoes em `app.core.config.settings`

Nao foram criados KPIs ficticios nem graficos com dados inventados.

### Cache E Atualizacao

O frontend usa TanStack Query no hook:

```text
frontend/src/features/dashboard/hooks/useDashboardOverview.ts
```

Configuracao:

- `queryKey`: `queryKeys.dashboard.overview`
- `staleTime`: 10 segundos
- `refetchInterval`: 15 segundos
- um unico request para alimentar todos os cards e secoes

### Layout Migrado Do PySide6

A tela React apresenta:

- seis cards: Sistema, WhatsApp, Worker, Na fila, Concluidos e Erros;
- secao "Atividade nas ultimas 24 horas" com estado vazio;
- secao "Resumo operacional" com pendentes, processando, concluidos, erros, backend, inicializacao e pasta de midias.

Os campos "Inicializacao" e "Pasta de midias" aparecem como "Sem dados" porque o endpoint React ainda nao expoe esses dados reais. Eles nao foram inventados no frontend.

### Estados

A pagina suporta:

- loading com skeletons;
- erro com empty state amigavel e toast;
- sem dados com empty state;
- sucesso com cards, atividade e resumo operacional.

Erros crus do backend nao sao exibidos diretamente.

## Central De Conversas

O modulo real de conversas fica em:

```text
frontend/src/features/conversations/
```

Estrutura:

- `api/`: chamadas HTTP da feature.
- `components/`: lista, item, cabecalho, painel e historico.
- `hooks/`: hooks TanStack Query da feature.
- `pages/`: pagina roteada.
- `types/`: schemas Zod e DTOs TypeScript.
- `utils/`: formatadores, agrupamento e constantes.
- `tests/`: testes da feature.
- `index.ts`: API publica da feature.

A feature nao envia mensagens. Nesta etapa ela apenas consulta dados reais do backend.

### Endpoints

Endpoints de leitura:

```text
GET /conversations
GET /conversations/{conversation_id}
GET /conversations/{conversation_id}/messages
```

As rotas chamam `ConversationQueryService`. O endpoint nao acessa tabelas diretamente e nao consolida regra de negocio.

### DTOs

DTOs criados no backend:

- `PaginationMetadata`
- `ConversationProfile`
- `ConversationListItem`
- `ConversationListResponse`
- `ConversationDetails`
- `ConversationMessageItem`
- `ConversationMessagesResponse`

Os DTOs escondem identificadores tecnicos do usuario sempre que o telefone pode ser resolvido.

### Origem Dos Dados

As conversas usam dados persistidos em:

- `conversation_messages`
- `conversation_sessions`
- `contact_profiles`

O PySide6 continua usando seus fluxos atuais. A nova API React adiciona consultas paginadas ao `StorageService`, sem alterar gravacao, processamento, Evolution ou fluxo de conversa.

### Paginacao E Pesquisa

A lista de conversas usa:

```text
GET /conversations?page=1&page_size=30&search=termo
```

As mensagens usam:

```text
GET /conversations/{conversation_id}/messages?page=1&page_size=50
```

Mensagens recentes sao carregadas primeiro no backend e exibidas em ordem visual cronologica no frontend. O botao "Carregar anteriores" usa a proxima pagina.

A pesquisa acontece no backend e considera telefone e nome salvo em `contact_profiles`.

### Resolucao De Nomes

A prioridade fica no backend, em `ConversationQueryService`:

1. nome salvo no perfil do contato;
2. telefone formatado;
3. identificador original somente quando nao for possivel extrair telefone.

Para numeros brasileiros, o backend devolve formato semelhante a:

```text
(62) 99999-9999
```

### Fotos De Perfil

A API devolve `profile_photo_url` e `profile_photo_path` quando ja existirem em `contact_profiles`.

O navegador nao chama a Evolution diretamente. Falhas ou ausencia de foto nao bloqueiam a tela; `YkAvatar` mostra iniciais como fallback. A atualizacao/cache da foto continua responsabilidade dos servicos backend existentes.

### Cache E Atualizacao

Query keys oficiais:

- `queryKeys.conversations.all`
- `queryKeys.conversations.list(filters)`
- `queryKeys.conversations.detail(id)`
- `queryKeys.conversations.messages(id, pageSize)`

Polling controlado:

- lista: 15 segundos;
- detalhes: 10 segundos;
- mensagens: 7 segundos.

As consultas sao desabilitadas quando o navegador esta offline.

### Navegacao

Rotas:

```text
/conversas
/conversas/:conversationId
```

A conversa selecionada fica refletida na URL. A primeira conversa nao e selecionada automaticamente.

### Scroll

Ao abrir uma conversa, o historico posiciona nas mensagens mais recentes. Se novas mensagens chegam e o usuario esta no fim, o scroll acompanha. Se o usuario esta lendo mensagens antigas, aparece um indicador discreto de novas mensagens.

## Workspace Profissional De Conversa

A area central de Conversas foi evoluida para um workspace de atendimento sem envio de mensagens.

Estrutura visual:

```text
Lista de conversas | Historico e cabecalho | Painel de contexto
```

O workspace reutiliza a feature `frontend/src/features/conversations/` e nao criou providers globais, alteracoes de shell ou mudancas no design system.

### Provider Local

O estado visual fica no provider local:

```text
frontend/src/features/conversations/providers/
```

Responsabilidades:

- painel lateral aberto/fechado;
- busca local aberta/fechada;
- termo de busca local;
- indice ativo da busca.

Nao ha regra de negocio nesse provider.

### Painel Lateral

O painel lateral `ConversationContextPanel` mostra apenas dados reais ja entregues pelo backend:

- nome;
- telefone;
- foto quando houver URL;
- primeira interacao;
- ultima atividade;
- quantidade de mensagens;
- categoria;
- estado de sessao;
- status adicional;
- origem WhatsApp.

Nao sao exibidas metricas falsas. Identificador interno e modo desenvolvedor ficaram adiados porque ainda nao existe configuracao real de modo desenvolvedor no frontend.

### Cabecalho Enriquecido

`ConversationHeader` exibe:

- avatar;
- nome;
- telefone;
- quantidade de mensagens;
- ultima atividade;
- categoria;
- estado da sessao;
- indicador de polling/atualizacao;
- controles visuais para busca local e painel lateral.

Nao foram criadas acoes funcionais de atendimento.

### Barra De Informacoes

`ConversationWorkspaceInfoBar` exibe:

- mensagens carregadas;
- total de mensagens;
- ultima sincronizacao do TanStack Query;
- estado do polling.

Todos os valores derivam do DTO real ou do estado real da consulta.

### Pesquisa Local

`ConversationLocalSearchBar` pesquisa somente nas mensagens ja carregadas.

Comportamento:

- destaque visual dos termos encontrados;
- contador de resultados;
- proximo/anterior;
- limpar/fechar;
- atalho `Ctrl+F` para abrir;
- `Esc` para fechar.

Nao ha consulta adicional ao backend nesta etapa.

### Menu De Contexto

`MessageContextMenu` permite:

- copiar texto;
- copiar conteudo bruto.

Nao ha edicao, exclusao ou alteracao de mensagens.

### Scroll Inteligente

`ConversationMessageList` preserva posicao ao carregar mensagens anteriores, mostra indicador de novas mensagens e oferece botao "Ir para o final" quando o usuario esta distante do fim.

Virtualizacao nao foi aplicada nesta etapa porque a paginacao carrega lotes de 50 mensagens e ainda nao ha volume real que justifique complexidade adicional.

### Limitacoes Atuais

- `unread_count` ainda e sempre `0`, porque o backend nao possui controle real de leitura.
- Foto local em `profile_photo_path` ainda nao e servida como arquivo HTTP para o React; quando nao houver URL, o avatar usa iniciais.
- Nao ha envio de mensagens, anexos, player de midia, WebSocket ou notificacoes desktop nesta etapa.
- A listagem mostra mensagens reais persistidas; a galeria exclusiva de arquivos sera um modulo posterior ou uma evolucao de Arquivos/Conversas.

## Downloads

O modulo de Downloads migra a tela de fila existente no PySide6 para React/Tauri.

Estrutura:

```text
frontend/src/features/downloads/
  api/
  components/
  hooks/
  pages/
  types/
  utils/
  tests/
  index.ts
```

A tela nao altera o processamento. Ela apenas apresenta os jobs que a fila em memoria/persistida ja conhece e executa a mesma acao de limpar jobs concluidos.

### Endpoints

Endpoints usados:

```text
GET /downloads/jobs
DELETE /downloads/jobs/completed
```

As rotas chamam `DownloadQueryService`, que encapsula a leitura da `ProcessingQueue`. A API nao acessa widgets, nao executa downloads e nao altera regra de negocio.

### DTO

DTOs:

- `DownloadJobItem`: id, short_id, sender, sender_raw, origin, file, kind, status e created_at.
- `DownloadJobsResponse`: items e total.
- `ClearCompletedDownloadsResponse`: removed.

Os campos seguem a apresentacao ja usada pelo PySide6, incluindo telefone formatado, nome do arquivo extraido do payload e tipo amigavel da midia.

### Fluxo Da Tela

Fluxo:

```text
DownloadsPage -> useDownloadJobs -> fetchDownloadJobs -> httpClient -> FastAPI
DownloadsPage -> useClearCompletedDownloads -> clearCompletedDownloadJobs -> httpClient -> FastAPI
```

Filtros e busca reproduzem o comportamento do PySide6:

- busca local sobre os valores exibidos;
- filtro de status com `Todos`, `PENDENTE`, `PROCESSANDO`, `CONCLUIDO` e `ERRO`;
- botao `Atualizar`;
- botao `Limpar concluidos`;
- tabela com `Remetente`, `Origem`, `Arquivo`, `Tipo`, `Status`, `Recebido em` e `ID`.

### Cache E Atualizacao

O hook `useDownloadJobs` usa TanStack Query com:

- `queryKey`: `queryKeys.downloads.jobs`;
- `staleTime`: 5 segundos;
- `refetchInterval`: 10 segundos.

A atualizacao manual usa o mesmo cache e nao cria chamadas paralelas independentes.

## Arquivos

O modulo de Arquivos expõe em React/Tauri a biblioteca de midias processadas que ja existe no PySide6 atraves do Historico e dos cards de midia em Conversas.

Estrutura:

```text
frontend/src/features/files/
  api/
  components/
  hooks/
  pages/
  types/
  utils/
  tests/
  index.ts
```

A feature nao move regra de negocio para o frontend. Ela consulta os registros reais de `media_history` via backend e renderiza a lista com busca, filtros e acoes de arquivo equivalentes ao que ja existe no PySide6.

### Endpoint

Endpoint usado:

```text
GET /files
```

A rota chama `FileQueryService`, que usa `StorageService.list_media_history()` e resolve somente dados de apresentacao como telefone formatado, tipo da midia e tamanho do arquivo quando ele existe no disco.

### DTO

DTOs:

- `FileLibraryItem`: id, data, remetente, origem, categoria, nome final, caminho, caminho absoluto, tipo, status, tamanho e existencia no disco.
- `FileLibraryResponse`: items e total.

### Fluxo Da Tela

Fluxo:

```text
FilesPage -> useFiles -> fetchFiles -> httpClient -> FastAPI
```

Comportamento migrado:

- busca local por nome, remetente ou categoria;
- filtro de categoria;
- filtro de origem;
- botao `Atualizar`;
- tabela com nome, tipo, tamanho, data, origem, categoria, status e acoes;
- acoes `Abrir` e `Abrir pasta` usando abertura local quando disponivel.

### Cache E Atualizacao

O hook `useFiles` usa TanStack Query com:

- `queryKey`: `queryKeys.files.list`;
- `staleTime`: 10 segundos;
- `refetchInterval`: 15 segundos.

## Historico

O modulo de Historico migra a tela PySide6 de midias processadas para React/Tauri.

Estrutura:

```text
frontend/src/features/history/
  api/
  components/
  hooks/
  pages/
  types/
  utils/
  tests/
  index.ts
```

A feature nao altera o fluxo de processamento. Ela apenas apresenta os registros reais de `media_history` ja persistidos pelo backend.

### Endpoint

Endpoint usado:

```text
GET /history
```

A rota chama `HistoryQueryService`, que usa `StorageService.list_media_history()` e aplica somente a mesma formatação visual que o PySide6 ja aplicava no `DesktopDataProvider`.

### DTO

DTOs:

- `HistoryItem`: id, data original, data formatada, remetente, origem, categoria, nome final, caminho, tipo e status.
- `HistoryResponse`: items e total.

### Fluxo Da Tela

Fluxo:

```text
HistoryPage -> useHistory -> fetchHistory -> httpClient -> FastAPI
```

Comportamento migrado:

- busca local por nome, remetente ou categoria;
- filtro de categoria;
- filtro de origem;
- botao `Atualizar`;
- contador de registros;
- tabela com `Data`, `Remetente`, `Origem`, `Categoria`, `Nome final`, `Tipo` e `Status`;
- empty state igual ao PySide6 quando nao ha registros.

### Cache E Atualizacao

O hook `useHistory` usa TanStack Query com:

- `queryKey`: `queryKeys.history.list`;
- `staleTime`: 10 segundos;
- `refetchInterval`: 15 segundos.

## Categorias

O modulo de Categorias migra a tela PySide6 de cadastro e ordenacao de categorias para React/Tauri.

Estrutura:

```text
frontend/src/features/categories/
  api/
  components/
  hooks/
  pages/
  types/
  utils/
  tests/
  index.ts
```

A feature preserva o fluxo atual: a interface altera uma lista ordenada e envia a lista completa para persistencia, como o PySide6 faz em `_save_categories_from_list()`.

### Endpoints

Endpoints usados:

```text
GET /categories
PUT /categories
```

As rotas chamam `CategoryQueryService`, que usa o `CategoryService` existente. A API apenas expõe leitura e persistência da lista ordenada; regras e validacoes continuam no backend.

### DTO

DTOs:

- `CategoryItem`: posicao, nome e pasta correspondente.
- `CategoriesResponse`: items e total.
- `SaveCategoriesRequest`: lista ordenada de categorias.

### Fluxo Da Tela

Comportamento migrado:

- tabela com `Posicao`, `Categoria` e `Pasta correspondente`;
- botao `Nova categoria`;
- botao `Editar`;
- botao `Excluir`;
- botao `Mover acima`;
- botao `Mover abaixo`;
- dialog de nome equivalente ao `QInputDialog`;
- confirmacao de exclusao com o mesmo texto do PySide6;
- nenhuma pesquisa, pois a tela atual nao possui busca.

### Cache

O hook `useCategories` usa TanStack Query com:

- `queryKey`: `queryKeys.categories.list`;
- `staleTime`: 10 segundos.

## Configuracoes

O modulo de Configuracoes migra a tela PySide6 de preferencias e conexoes para React/Tauri.

Estrutura:

```text
frontend/src/features/settings/
  api/
  components/
  hooks/
  pages/
  types/
  utils/
  tests/
  index.ts
```

A feature preserva as secoes atuais do PySide6:

- Pastas;
- WhatsApp;
- Downloads;
- Atualizacoes;
- Tema;
- Idioma;
- Backup;
- Sistema;
- Avancado.

### Endpoints

Endpoints usados:

```text
GET /settings
PUT /settings
GET /settings/evolution
POST /settings/evolution/connect
POST /settings/evolution/disconnect
POST /settings/prepare
GET /settings/diagnostics
```

As rotas chamam `SettingsQueryService`, que coordena somente servicos existentes: `AppConfigurationManager`, `DiagnosticService`, `AutomaticSetupService` e `EvolutionClient`. A API apenas expoe dados e comandos ja existentes na interface PySide6.

### DTO

DTOs:

- `AppSettingsResponse`: pasta de midias, FFmpeg, SQLite, instancia WhatsApp e estado da Evolution.
- `SaveAppSettingsRequest`: campos editaveis existentes no PySide6.
- `EvolutionSessionResponse`: instancia, estado, mensagem e QR Code quando existir.
- `DiagnosticReportResponse`: status, mensagem e itens do diagnostico.
- `SetupReportResponse`: status, mensagem e passos da preparacao automatica.

### Fluxo Da Tela

Comportamento migrado:

- menu lateral interno com as nove secoes existentes;
- campos de Pastas e Avancado equivalentes aos `QLineEdit`;
- botoes `Salvar` e `Cancelar`;
- WhatsApp com `Verificar`, `Conectar WhatsApp` e `Desconectar`;
- area de QR Code para conexao da sessao;
- Sistema com `Preparar Sistema Automaticamente`, `Abrir assistente` e `Executar Diagnostico`;
- secoes reservadas exibem a mesma mensagem de configuracao automatica do PySide6.

### Cache

Os hooks usam TanStack Query com:

- `queryKeys.settings.detail`;
- `queryKeys.settings.evolution`;
- `staleTime`: 10 segundos.

## Rotas

Rotas em `frontend/src/routes/routes.tsx`.

Constantes de rotas em `frontend/src/routes/route-paths.ts`.

Separacao preparada:

- `publicRoutes`
- `internalRoutes`
- `protectedRoutes`

`protectedRoutes` ainda esta vazio. A arquitetura esta preparada para autenticacao futura, mas autenticacao nao foi implementada.

Paginas criadas nesta etapa:

- `/dashboard`
- `/conversas`
- `/conversas/:conversationId`
- `/downloads`
- `/arquivos`
- `/categorias`
- `/historico`
- `/configuracoes`

Dashboard, Conversas, Downloads, Arquivos, Historico, Categorias e Configuracoes ja possuem modulos reais consumindo dados do backend.

## Pre-Requisitos

- Python com as dependencias de `requirements.txt`.
- Node.js 24 ou compativel.
- npm.
- Rust/Cargo para executar `tauri:dev` e `tauri:build`.

Nesta maquina, `cargo` nao foi encontrado durante a validacao.

## Instalacao

```powershell
cd "C:\Users\Industel\Documents\New project\Ykmedia-main\frontend"
npm.cmd install
```

## Backend

```powershell
cd "C:\Users\Industel\Documents\New project\Ykmedia-main"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
```

Endpoint usado:

```text
GET http://127.0.0.1:8010/health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

## Frontend

```powershell
cd "C:\Users\Industel\Documents\New project\Ykmedia-main\frontend"
npm.cmd run dev
```

## Tauri

No desenvolvimento, inicie o backend manualmente antes de abrir o Tauri:

```powershell
cd "C:\Users\Industel\Documents\New project\Ykmedia-main\frontend"
npm.cmd run tauri:dev
```

Build:

```powershell
cd "C:\Users\Industel\Documents\New project\Ykmedia-main"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_backend_sidecar.ps1

cd frontend
npm.cmd run tauri:build
```

O build gera o backend FastAPI como `ykmedia-backend.exe` e o inclui no instalador Tauri.
Na instalacao, o aplicativo inicia esse backend automaticamente se `http://127.0.0.1:8010/health`
nao responder. Depois que o backend estiver online, o aplicativo executa automaticamente a preparacao
existente do sistema em segundo plano: cria configuracoes, verifica o Docker, inicia os containers e
prepara a Evolution. A interface permanece utilizavel durante essa etapa. Dados do usuario, banco SQLite,
logs, downloads e configuracoes ficam em:

```text
%LOCALAPPDATA%\YkMedia
```

Se ja existir um backend respondendo na porta 8010, ele e reutilizado e nao e encerrado ao fechar a interface.

## Instalador Inno Setup

O instalador unico do Windows inclui a interface Tauri e o backend FastAPI. Para gera-lo:

```powershell
cd "C:\Users\Industel\Documents\New project\Ykmedia-main"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_inno_installer.ps1
```

O resultado sera criado em `installer\output`. O Docker Desktop continua sendo preparado pelo
YkMedia na primeira abertura, pois ele e uma dependencia do Windows que pode solicitar permissao
administrativa ou reinicializacao.

## Variaveis De Ambiente

```text
frontend/.env.example
```

```text
VITE_API_BASE_URL=http://127.0.0.1:8010
```

## CORS

O backend permite somente origens locais configuradas em:

```text
FRONTEND_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,tauri://localhost
```

## Limitacoes

- Docker Desktop continua sendo uma dependencia externa para Evolution, PostgreSQL e Redis. A tela
  "Preparar Sistema" continua responsavel por instalar/iniciar o Docker e subir esses servicos.
- O PySide6 continua existindo e funcionando em paralelo.
- O build Tauri depende da instalacao do Rust/Cargo e do Python com PyInstaller na maquina de build.
- O npm reportou vulnerabilidades transitivas; nao foi aplicado `npm audit fix --force` para evitar upgrades quebrando compatibilidade nesta etapa.
- Downloads, Atualizacoes, Tema, Idioma e Backup em Configuracoes exibem paineis informativos fixos
  (`SimpleSettingsPanel`), sem controle real ainda; Pastas, WhatsApp, Sistema e Avancado ja sao funcionais.
- `frontend/src/pages/StartupPage.tsx` (tela de espera de backend) e os componentes de workspace de
  Conversas em `frontend/src/features/conversations/components/` (`ConversationContextPanel`,
  `ConversationMessageList`, `ConversationWorkspaceInfoBar`, `ConversationLocalSearchBar`,
  `MessageContextMenu`) existem, tem testes e sao exportados, mas nao estao conectados as paginas em uso.
  Nao foram religados nesta etapa para evitar mudanca de comportamento sem autorizacao explicita.
