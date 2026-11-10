# gnzl achados

Painel local para gerenciamento de atividades de afiliado da Shopee Brasil:
busca de produtos, geração de links em lote com Sub IDs e histórico.

- **Backend:** Python + FastAPI + SQLite (SQLAlchemy 2)
- **Frontend:** React 19 + TypeScript + Vite (em construção)
- **Execução:** local, em `127.0.0.1`

Este é um projeto pessoal que roda exclusivamente na sua máquina. Nenhum dado
sai do computador, exceto as chamadas oficiais à API da Shopee quando o
provedor `shopee` estiver habilitado.

## Estado atual

| Etapa | Situação |
|---|---|
| 0 — Fundação (config, app mínimo, testes) | concluída |
| 1 — Banco de dados e migrations | concluída |
| 2 — Provedores (demo) | concluída |
| 3 — Busca de produtos e listas | concluída |
| 4 — Sub IDs | concluída |
| 5 — Lotes e links | concluída |
| 6 a 12 — Frontend, E2E e fechamento | pendente |

Enquanto a Open API de afiliados não estiver liberada, a aplicação funciona em
**modo demo**, com dados fictícios identificados como tal.

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

```powershell
python app.py
```

- API: http://127.0.0.1:8000/api/docs
- Saúde: http://127.0.0.1:8000/api/health

## Testes

```powershell
cd backend
pytest
```

## Configuração

Todas as variáveis usam o prefixo `GNZL_` e vivem no `.env` da raiz.
Consulte `.env.example` para a lista completa.

| Variável | Padrão | Função |
|---|---|---|
| `GNZL_ENVIRONMENT` | `dev` | `dev` habilita CORS para o Vite |
| `GNZL_PROVIDER` | `demo` | `demo` ou `shopee` |
| `GNZL_HOST` / `GNZL_PORT` | `127.0.0.1` / `8000` | Endereço da API |
| `GNZL_LINK_CONCURRENCY` | `3` | Gerações simultâneas por lote |
| `GNZL_HTTP_TIMEOUT_SECONDS` | `15` | Timeout das chamadas externas |
| `GNZL_SHOPEE_APP_ID` / `GNZL_SHOPEE_SECRET` | vazio | Credenciais da Open API |

Credenciais nunca são expostas pela API, nem registradas em logs.

## Estrutura

```
backend/app/     API, regras de negócio, provedores, modelos e persistência
backend/tests/   Pytest
frontend/        Interface React (etapa 6 em diante)
data/            Banco SQLite e logs (não versionado)
docs/            Arquitetura e decisões técnicas
```
