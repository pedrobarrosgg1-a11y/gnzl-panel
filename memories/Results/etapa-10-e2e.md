# Etapa 10 — testes E2E com Playwright

Data: 2026-11-12

## Entrega

- Playwright instalado no frontend (`@playwright/test` + Chromium).
- `frontend/playwright.config.ts` com duas instâncias isoladas:
  - API em `127.0.0.1:8100`;
  - interface em `127.0.0.1:5274`, com proxy para a API de teste.
- `backend/scripts/serve_e2e.py` recria `data/e2e/gnzl-e2e.db` pelas migrations
  reais antes de subir a API. O banco de desenvolvimento não é tocado.
- `frontend/tests/e2e/flows.spec.ts` com três fluxos completos:
  1. busca → seleção de produto → criação do lote → geração → detalhe →
     conferência na lista de lotes;
  2. lote originado de lista com um item que falha → status `parcial`, feedback
     de sucesso + falha, mensagem e código `provider_unavailable`;
  3. histórico filtrado por lote → regeneração com Sub ID alterado → link
     anterior visível como `substituído` → filtro `status=replaced` sem ação de
     regenerar.
- O terceiro fluxo também confirma que o cliente bloqueia a regeneração quando
  nenhum Sub ID mudou.
- Script `npm run test:e2e`.
- Vitest limitado a `src/**` para não coletar os arquivos do Playwright.
- `tsconfig.e2e.json` incluído em `tsc -b`, então configuração e fluxos E2E
  também passam pelo typecheck do build.

## Decisões

- Portas e banco exclusivos evitam depender do ambiente de desenvolvimento e
  permitem rodar E2E com os servidores normais ligados.
- `reuseExistingServer: false` garante que a API de teste sempre recrie o banco
  descartável.
- Um único worker: os testes compartilham o mesmo SQLite e criam dados entre si.
- A lista e o lote do terceiro fluxo são preparados pela API; a interface é
  exercitada no que a etapa 10 precisa validar (filtro, regeneração e histórico).
- Os testes usam seletores acessíveis (`getByRole`, `getByLabel`) em vez de
  classes CSS.

## Bug encontrado e corrigido

O primeiro E2E em banco vazio falhou com
`UNIQUE constraint failed: products.item_id, products.shop_id, products.data_source`.
Duas buscas simultâneas (o React em modo estrito dispara o efeito duas vezes)
faziam `select` antes de qualquer `insert` e ambas tentavam inserir o mesmo
produto.

Correção em `backend/app/repositories/products.py`: gravação atômica com
`INSERT ... ON CONFLICT DO UPDATE`, seguida da leitura dos registros na ordem
original. Foi adicionado o teste
`backend/tests/services/test_products_repository.py`, que executa dois upserts
concorrentes e confirma uma única linha.

## Evidências

- `npm run test:e2e`: 3 testes aprovados em 13,9s.
- Backend: 128 testes aprovados.
- Vitest: 54 testes em 8 arquivos, aprovados.
- `npm run build`: aprovado (80 módulos).
- `data/e2e/gnzl-e2e.db` ficou com 3 lotes, 4 links e 1 lista após a execução,
  enquanto `data/gnzl.db` permaneceu sem links novos.
- Artefatos de `playwright-report/`, `test-results/` e `data/e2e/` são
  ignorados pelo Git.

## Limites

- E2E cobre apenas Chromium em viewport desktop; não há projeto mobile.
- Criação, edição e exclusão de listas continuam cobertas por Vitest e Pytest,
  não por E2E.
- O provedor `shopee` segue não implementado; os fluxos usam o provedor demo.
- Os testes não verificam a área de transferência de forma nativa; a cópia já
  foi validada manualmente na etapa 9.
