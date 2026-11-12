# visão da fase 1

Registro consolidado do que foi construído e das decisões que as próximas
fases devem preservar. Detalhes de esquema e de geração de links continuam em
[`data-model.md`](data-model.md) e [`link-generation.md`](link-generation.md).

## Escopo entregue

- Busca de produtos no provedor demo, com filtros, ordenação e paginação.
- Listas de produtos com inclusão, remoção, edição e exclusão.
- Sub IDs normalizados e autocomplete a partir do uso real.
- Lotes de links a partir de produtos selecionados ou de uma lista.
- Execução de lote com falha isolada por item e retry dos itens falhos.
- Histórico imutável de links, com filtros e regeneração encadeada.
- Interface React para busca, listas, lotes e histórico.
- Testes de backend, de componentes e três fluxos E2E em Playwright.

O provedor oficial da Shopee **não** faz parte da entrega. `GNZL_PROVIDER=shopee`
falha no startup com mensagem explícita, em vez de cair silenciosamente no demo.

## Camadas

### Backend

```
api/          endpoints, validação de entrada e envelope de erro
services/     regras de negócio e orquestração
repositories/ consultas e persistência
models/       entidades SQLAlchemy
providers/    contratos e fontes de dados (demo implementado)
schemas/      contratos Pydantic de resposta
core/         configuração, constantes, erros e tempo
```

Os endpoints não concentram regra de negócio. Os serviços dependem dos
protocolos `ProductProvider` e `LinkProvider`, nunca de uma implementação
concreta. Trocar demo por Shopee ou CSV não deve exigir alterar API, serviços
ou frontend.

### Frontend

```
pages/       telas e seus estados
layouts/     sidebar, menu móvel e estrutura comum
components/  tabelas, formulários, estados vazios, feedback e ícones
hooks/       estado compartilhado (configuração do sistema)
services/    cliente HTTP e tradução de erros
types/       contratos espelhando a API
utils/       formatação de moeda, data, links e busca
```

O frontend chama apenas caminhos relativos `/api`. Em desenvolvimento, o proxy
do Vite encaminha para `127.0.0.1:8000`; nos testes E2E, para `127.0.0.1:8100`.
Credenciais e acesso ao SQLite nunca passam pelo navegador.

## Fluxos principais

1. **Busca e persistência local.** O provedor devolve produtos normalizados; o
   repositório faz upsert atômico por `item_id + shop_id + data_source`. A mesma
   busca pode rodar em paralelo sem violar a unicidade.
2. **Criação de lote.** Os itens são copiados no momento da criação, com URL de
   origem, deduplicação e limite de 200. Lote de lista não muda se a lista mudar
   depois.
3. **Execução.** Somente itens `pending`/`failed` são processados. A chamada ao
   provedor roda em threads; a gravação no SQLAlchemy permanece na thread da
   requisição. O status final é `completed`, `partial` ou `failed`.
4. **Histórico.** `affiliate_url` é único. Regenerar cria um novo registro e
   marca o anterior como `replaced`, sem apagar o histórico.

## Dados e integridade

- SQLite criado exclusivamente por migrations Alembic (`backend/migrations/`).
- Valores monetários em centavos e percentuais em pontos-base.
- Datas em UTC sem timezone; a conversão para `America/Sao_Paulo` é de
  apresentação.
- `data_source` (`demo`, `shopee`, `csv`) em produtos, lotes e links impede
  misturar dado fictício com real sem rótulo.
- Sub IDs canônicos (`[a-z0-9-]`, até 64 caracteres) validados no serviço e no
  banco.
- Restrições de unicidade, `CHECK` e chaves estrangeiras protegem o histórico.

## Segurança e execução local

- API e interface escutam em loopback (`127.0.0.1`).
- CORS existe apenas em `environment=dev` e apenas para a origem do Vite em
  `5173`; o uso normal passa pelo proxy e não depende de CORS.
- Segredos vivem somente no `.env`, ignorado pelo Git. `.env.example` contém
  apenas nomes e valores vazios.
- `/api/config` expõe versão, ambiente, provedor e `is_demo` — nunca
  credenciais.
- Erros inesperados são registrados no log do servidor e devolvidos ao cliente
  como `internal_error`, sem detalhes internos.
- Não há scraping nem uso de endpoints privados. O provedor oficial será
  implementado apenas com a Open API liberada.

## Testes

| suíte | comando | foco |
|---|---|---|
| Pytest | `cd backend; pytest` | serviços, API, repositórios, migrations, erros |
| Vitest | `cd frontend; npm run test` | páginas, hooks, formatação e estados |
| Playwright | `cd frontend; npm run test:e2e` | busca → lote → links; falha parcial; regeneração |

Os testes E2E usam `data/e2e/gnzl-e2e.db`, recriado pelas migrations, em portas
próprias. Nenhum teste toca o banco de desenvolvimento. O typecheck dos testes
E2E faz parte de `npm run build`.

## Limitações conhecidas da fase 1

- Provedor oficial da Shopee pendente; tudo roda com dados demo identificados.
- A execução do lote é síncrona: `POST /run` responde ao final. Ainda não há
  fila, execução em segundo plano nem retry automático com backoff.
- Não há autenticação de usuário. Isso é aceitável porque a aplicação é pessoal
  e escuta apenas em loopback; não deve ser exposta à rede sem essa camada.
- E2E cobre Chromium em viewport desktop; a responsividade foi verificada
  manualmente em 390 px.
- Dashboard, metas, importação CSV, vídeos, templates e publicações pertencem às
  fases 2 e 3 e não foram antecipados.

## Decisões que não devem ser revertidas sem análise

- `data_source` em toda entidade de dado e ausência de fallback silencioso entre
  provedores.
- Upsert atômico de produtos, para suportar buscas concorrentes.
- Migrations como única forma de criar ou alterar o esquema.
- Histórico de links imutável: regeneração encadeia registros, não sobrescreve.
- Separação entre regra de negócio no backend e apresentação no frontend.
