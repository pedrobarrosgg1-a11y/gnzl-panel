# gnzl achados

Painel local para gerenciamento de atividades de afiliado da Shopee Brasil:
busca de produtos, geração de links em lote com Sub IDs, histórico e
sincronização de conversões.

- **Backend:** Python + FastAPI + SQLite (SQLAlchemy 2)
- **Frontend:** React 19 + TypeScript + Vite
- **Execução:** local, em `127.0.0.1`

Este é um projeto pessoal que roda exclusivamente na sua máquina. Nenhum dado
sai do computador, exceto as chamadas oficiais à API da Shopee quando o
provedor `shopee` estiver habilitado.

## Estado atual

### Fase 1

| Etapa | Situação |
|---|---|
| 0 — Fundação (config, app mínimo, testes) | concluída |
| 1 — Banco de dados e migrations | concluída |
| 2 — Provedores (demo) | concluída |
| 3 — Busca de produtos e listas | concluída |
| 4 — Sub IDs | concluída |
| 5 — Lotes e links | concluída |
| 6 — Fundação do frontend | concluída |
| 7 — Busca de produtos (interface) | concluída |
| 8 — Listas de produtos (interface) | concluída |
| 9 — Lotes e links (interface) | concluída |
| 10 — Testes E2E (Playwright) | concluída |
| 11 — Revisão de fechamento (config, design, código, docs) | concluída |
| 12 — Fechamento final da fase 1 | concluída |

O provedor oficial está implementado (`GNZL_PROVIDER=shopee`): busca de
produtos, geração de link curto e sincronização de conversões dos últimos 90
dias. O padrão continua sendo **modo demo** (`GNZL_PROVIDER=demo`), com dados
fictícios identificados como tal. A visão do provedor está em
[`docs/architecture/shopee-provider.md`](docs/architecture/shopee-provider.md).

A visão consolidada da fase 1 está em
[`docs/architecture/phase-1.md`](docs/architecture/phase-1.md).

### Fase 2

| Etapa | Situação |
|---|---|
| 13 — Modelagem de conversão, importações e metas | concluída |
| 14 — Importação CSV | concluída |
| 15 — Agregações e endpoints do dashboard | concluída |
| 16 — Tela de dashboard com gráfico e rankings | pendente |
| 17 — Metas | pendente |
| 18 — Testes E2E e fechamento da fase 2 | pendente |
| 19a — Provedor oficial da Shopee: busca e links | concluída |
| 19b — Sincronização de conversões pela Open API | concluída |

O escopo e os critérios da fase 2 estão em
[`docs/architecture/phase-2.md`](docs/architecture/phase-2.md). O endpoint do
dashboard (`GET /api/dashboard`) já existe e está documentado em
[`docs/architecture/dashboard.md`](docs/architecture/dashboard.md); a tela
correspondente é a etapa 16. A importação CSV depende da confirmação do formato
real do relatório da Shopee.

## Requisitos

- Python 3.14 (testado com 3.14.5)
- Node.js 22.12+ ou 26+ (necessário a partir da etapa 6)

## Instalação (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements-dev.txt
Copy-Item .env.example .env
```

O `.env` é opcional para rodar em modo demo: os valores padrão já funcionam.

## Execução

Durante o desenvolvimento, backend e frontend rodam em dois terminais.

```powershell
# terminal 1 — API
python app.py
```

```powershell
# terminal 2 — interface
cd frontend
npm install
npm run dev
```

- Interface: http://127.0.0.1:5173
- API: http://127.0.0.1:8000/api/docs
- Saúde: http://127.0.0.1:8000/api/health

O Vite encaminha `/api` para `127.0.0.1:8000`, então o frontend chama caminhos
relativos e não precisa de configuração extra de CORS.

## Testes

```powershell
# backend
cd backend
pytest
```

```powershell
# frontend (Vitest)
cd frontend
npm run test
npm run build
```

```powershell
# e2e (Playwright) — instale o Chromium uma vez
cd frontend
npx playwright install chromium
npm run test:e2e
```

Os testes E2E usam instâncias próprias: API em `127.0.0.1:8100` e interface
em `127.0.0.1:5274`. O banco `data/e2e/gnzl-e2e.db` é descartável e recriado
pelas migrations a cada execução, então os testes não leem nem alteram
`data/gnzl.db`. Os servidores de desenvolvimento podem continuar rodando.

## Configuração

Todas as variáveis usam o prefixo `GNZL_` e vivem no `.env` da raiz.
Consulte `.env.example` para a lista completa.

| Variável | Padrão | Função |
|---|---|---|
| `GNZL_ENVIRONMENT` | `dev` | `dev` habilita CORS para o Vite |
| `GNZL_PROVIDER` | `demo` | `demo` ou `shopee` |
| `GNZL_HOST` / `GNZL_PORT` | `127.0.0.1` / `8000` | Endereço da API |
| `GNZL_DATABASE_URL` | vazio | Caminho alternativo do SQLite; vazio usa `data/gnzl.db` |
| `GNZL_LINK_CONCURRENCY` | `3` | Gerações simultâneas por lote |
| `GNZL_HTTP_TIMEOUT_SECONDS` | `15` | Timeout das chamadas externas |
| `GNZL_SHOPEE_APP_ID` / `GNZL_SHOPEE_SECRET` | vazio | Credenciais da Open API |
| `GNZL_SHOPEE_API_BASE` | endpoint oficial | Base da Open API, sobrescrevível |

Credenciais nunca são expostas pela API, nem registradas em logs.

## Estrutura

```
backend/app/     API, regras de negócio, provedores, modelos e persistência
backend/scripts/ Utilitários de execução (servidor E2E)
backend/tests/   Pytest
frontend/        Interface React (busca, listas, lotes e histórico)
frontend/tests/  Testes E2E em Playwright
data/            Banco SQLite e logs (não versionado)
docs/            Arquitetura e decisões técnicas
```
