# Etapa 19b — sincronização de conversões da Shopee

Data: 2026-11-13

## Entrega

`POST /api/conversions/sync?days=30` passou a ler o Conversion Report da Open
API e gravar pedidos em `orders` com `data_source="shopee"`, reutilizando
`import_logs`/`imported_rows` para auditoria.

- janela de 1 a 90 dias, limitada pela API;
- paginação por `scrollId` até `hasNextPage=false`, com teto de 100 páginas;
- atualização de status, comissão e demais campos mutáveis de pedidos já
  existentes;
- deduplicação por `order:<sha256(orderId|itemId|modelId)>` dentro da origem;
- `409 provider_not_supported` em modo demo;
- capacidades `conversion_sync` e `conversion_window_days` em `/api/config`.

Arquivos principais:

- `backend/app/providers/base.py`
- `backend/app/providers/shopee/provider.py`
- `backend/app/providers/registry.py`
- `backend/app/repositories/conversions.py`
- `backend/app/services/conversion_sync.py`
- `backend/app/schemas/conversions.py`
- `backend/app/api/conversions.py`
- `backend/tests/providers/test_shopee.py`
- `backend/tests/services/test_conversion_sync.py`
- `backend/tests/api/test_conversions.py`
- `docs/architecture/shopee-provider.md`

## Decisões

- Datas `Int64` vão **inline** na query: variáveis desse tipo retornam
  `10010 "wrong type"`. `limit` e `scrollId` continuam variáveis.
- O nó de conversão não tem campos de Sub ID; `utmContent` é separado por
  vírgula, ponto e vírgula, barra vertical ou espaço e canonicalizado em até
  cinco Sub IDs.
- `sales_cents` vem de `actualAmount`, com fallback `itemPrice × qty`;
  `commission_cents` vem de `itemTotalCommission`, com fallback
  `itemCommission` e então 0.
- Status bruto usa `displayItemStatus`, depois `orderStatus`, depois
  `conversionStatus`; o grupo é classificado por tokens conhecidos.
- `rows_imported` conta criados + atualizados. Atualizações aparecem como
  `imported` com mensagem explícita; nada muda de forma silenciosa.
- A chamada externa acontece antes de criar o `ImportLog`: falha do provedor
  não deixa log `running` nem importação parcial.

## Evidências

- `pytest`: **228 testes aprovados** (188 anteriores + 40 novos).
- `vitest`: **55 testes aprovados**.
- `npm run build`: aprovado.
- Validação real com banco descartável criado pelas migrations, sem tocar
  `data/gnzl.db` nem o `.env`:
  - `POST /api/conversions/sync?days=90` respondeu `201`;
  - janela `2026-08-16` → `2026-11-14`;
  - `total/created/updated/skipped = 0`, pois a conta não tem conversões;
  - `import_log` concluído com `report_type="orders"`, `data_source="shopee"`;
  - `orders = 0`, `import_logs = 1`;
  - banco temporário removido ao final.
- Antes da implementação, a janela de 90 dias foi varrida por script
  descartável: apenas a janela atual respondeu; janelas anteriores retornaram
  `11001`.

## Limitações

- A conta não tem pedido real, então nenhum mapeamento de conversão foi
  conferido contra resposta verdadeira; a validação é por schema e mocks.
- O separador de múltiplos Sub IDs em `utmContent` não é documentado.
- Conversões sincronizadas ainda não aparecem em tela: dashboard e metas são
  etapas seguintes.
