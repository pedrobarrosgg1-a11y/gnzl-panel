# Etapa 5 — lotes e links

Data: 2026-11-09

## Entrega

- CRUD de leitura e criação de lotes em `/api/link-batches`.
- Execução síncrona com chamadas externas em `ThreadPoolExecutor`
  (`GNZL_LINK_CONCURRENCY`).
- Falha isolada por item, com `attempts`, `error_code` e `error_message`.
- Retry processa apenas itens `pending` ou `failed`.
- Histórico `/api/links` com filtros por lote, status, origem, Sub IDs e busca
  por título/URL.
- Regeneração cria novo registro `active` e marca o anterior como `replaced`.
- Deduplicação global de `affiliate_url`: a mesma URL reaproveita o registro.
- Sub IDs normalizados e persistidos no lote para retry com a mesma configuração.

## Evidências

- `127 passed` com `pytest` em `backend/`.
- `alembic check`: sem operações pendentes.
- Banco de desenvolvimento recriado vazio com as 11 CHECKs de `link_batches`
  (6 de estrutura + 5 de formato de Sub ID).

## Limites

- Execução bloqueia a requisição até terminar.
- Provedor oficial ainda não implementado; modo demo.
- Retry é manual, sem backoff automático nesta fase.
- Máximo local de 200 itens por lote.
