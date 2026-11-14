# provedor oficial da shopee — busca, links e conversões

Integração com a Open API de afiliados da Shopee. Cobre **busca de produtos**,
**geração de link curto** (etapa 19a) e **sincronização de conversões**
(etapa 19b). A conta usada no desenvolvimento não tem pedidos reais, então o
mapeamento de conversões é validado por schema introspectado e testes com
respostas simuladas.

## Configuração

```dotenv
GNZL_PROVIDER=shopee
GNZL_SHOPEE_APP_ID=...
GNZL_SHOPEE_SECRET=...
GNZL_SHOPEE_API_BASE=https://open-api.affiliate.shopee.com.br/graphql
```

As credenciais ficam apenas no backend. `/api/config` expõe somente o nome do
provedor, `is_demo` e as capacidades.

## Autenticação

A assinatura cobre **os bytes JSON exatos** enviados:

```text
Signature = SHA256(app_id + timestamp + body + secret)
Authorization: SHA256 Credential=<app_id>, Timestamp=<unix>, Signature=<hex>
```

Por isso o corpo é serializado uma única vez, em UTF-8 compacto
(`ensure_ascii=False`, separadores `,` e `:`), e os mesmos bytes são assinados e
enviados. Reformatar o JSON depois de assinar invalida a assinatura (`10020`).

## Query de produtos

Argumentos reais confirmados por introspecção:

```text
listType, matchId, keyword, sortType, page, limit,
itemId, shopId, productCatId, isAMSOffer, isKeySeller
```

- `listType: 1` é enviado explicitamente (maior comissão). `listType: 0`
  retornou `10000` de forma consistente nos testes.
- `sortType` é um `Int` sem enum GraphQL. Valores documentados:

  | nosso `sort` | `sortType` |
  |---|---|
  | `relevance` | 1 |
  | `sales_desc` | 2 |
  | `price_desc` | 3 |
  | `price_asc` | 4 |
  | `commission_desc` | 5 |

- A API não informa o total. `ProductPage.total` fica `None`; o frontend mostra
  "N nesta página".
- `pageInfo.hasNextPage` alimenta `has_next`.

## Mutation de link

```graphql
mutation ($input: ShortLinkInput!) {
  generateShortLink(input: $input) { shortLink }
}
```

- O tipo é `ShortLinkInput`, não `GenerateShortLinkInput`.
- Até 5 `subIds`.
- O domínio do link não é fixado no código (`s.shopee.com.br` nos testes).
- **Nunca há retry automático.** Se a resposta se perder, o link pode já ter
  sido criado. A mensagem pede para conferir a lista antes de repetir.

## Mapeamento

| API | Nossa unidade | Regra |
|---|---|---|
| `price` (string) | `price_cents` | `Decimal × 100` |
| `commissionRate` (`"0.53"`) | `commission_rate_bp` | fração × 10000 → `5300` |
| `ratingStar` (`5`) | `rating_x100` | × 100 → `500` |
| `sales` | `sales` | inteiro |
| `itemId`, `shopId` | `item_id`, `shop_id` | inteiro |
| `productLink` | `product_url` | direto |
| `imageUrl` | `image_url` | direto |
| `productCatIds` | `category` | `None`: são IDs, não nomes |

`commissionRate` é a soma de `sellerCommissionRate` + `shopeeCommissionRate`
(ex.: `0.5 + 0.03 = 0.53`). Valores fora de `[0, 1]` são rejeitados em vez de
gravados.

## Capacidades declaradas

A API oficial não aceita:

- filtro por preço;
- filtro por comissão mínima;
- filtro por categoria por nome (só `productCatId`, sem catálogo nome → ID);
- ordenação por avaliação (`rating_desc`).

`/api/config` passa a devolver:

```json
{
  "provider": "shopee",
  "is_demo": false,
  "capabilities": {
    "category_filter": false,
    "price_filter": false,
    "commission_filter": false,
    "conversion_sync": true,
    "conversion_window_days": 90,
    "sorts": ["relevance", "commission_desc", "sales_desc", "price_asc", "price_desc"]
  }
}
```

Em modo demo, `conversion_sync` é `false` e o endpoint de sincronização recusa
a operação com `409` (ver abaixo).

O frontend esconde os controles não suportados. O backend também recusa esses
filtros com `422 validation_error`, para proteger quem chamar a API direto.
Filtrar localmente depois da busca deixaria paginação e contagem erradas.

## Sincronização de conversões (19b)

`POST /api/conversions/sync?days=30` lê o Conversion Report da janela e grava os
pedidos em `orders` com `data_source = "shopee"`.

### Janela

- `days` entre 1 e 90; padrão 30.
- O fim é o instante da chamada; o início é `fim - days`.
- A API só aceita janelas dentro dos últimos 90 dias. Uma janela anterior
  responde `11001`; o provedor recusa antes de chamar, com tolerância de 5
  minutos para diferença de relógio.

### Query

```graphql
query ($limit: Int, $scrollId: String) {
  conversionReport(
    purchaseTimeStart: 1760000000
    purchaseTimeEnd: 1762000000
    conversionStatus: ALL
    limit: $limit
    scrollId: $scrollId
  ) { ... }
}
```

- `purchaseTimeStart`/`purchaseTimeEnd` são `Int64`. A API recusa variáveis
  desse tipo com `10010 "wrong type"`, então os tempos vão **inline** na query;
  apenas `limit: Int` e `scrollId: String` são variáveis.
- `limit = 500` e a paginação segue `scrollId` até `hasNextPage = false`.
- Teto de 100 páginas por sincronização, para não repetir cursor
  indefinidamente. `hasNextPage = true` sem `scrollId` é erro de resposta.
- A página é processada antes de buscar a próxima; o cursor usado na chamada
  seguinte é o devolvido por `pageInfo`.

### Mapeamento

| API | Nossa unidade | Regra |
|---|---|---|
| `purchaseTime` | `ordered_at` | segundos Unix → UTC sem timezone |
| `orders[].orderId` | `external_order_id` | string, até 100 caracteres |
| `items[].itemId`, `items[].shopId` | `external_item_id`, `shop_id` | inteiro |
| `items[].itemName` | `title` | até 300 caracteres |
| `items[].qty` | `quantity` | ausente vira 0 |
| `items[].actualAmount` | `sales_cents` | cai para `itemPrice × qty` |
| `items[].itemTotalCommission` | `commission_cents` | cai para `itemCommission`, depois 0 |
| `items[].completeTime` | `completed_at` | 0 significa ausência |
| `displayItemStatus` → `orderStatus` → `conversionStatus` | `status` | primeiro valor não vazio |
| `device` | `channel` | `ALL` é filtro, não dispositivo → `None` |
| `items[].modelId` | identidade | entra no `dedup_key` |

### Sub IDs

O nó de conversão **não expõe campos de Sub ID**: o único vínculo é
`utmContent`. O separador real de múltiplos valores não está documentado, então
vírgula, ponto e vírgula, barra vertical e espaço são aceitos. Cada parte passa
pela canonicalização (`a-z0-9-`, até 64) e as cinco primeiras viram
`sub_id_1..5`. O valor bruto fica em `imported_rows.raw_data`.

### Status

O status bruto é preservado em `orders.status`. A classificação usa tokens
conhecidos, sem presumir um vocabulário fechado:

- `cancel*` → `cancelled`;
- `refund*`, `return*`, `devolu*` → `refunded`;
- `unpaid`, `pending`, `process`, `ship`, `transit`, `await` → `pending`;
- `complete`, `approv`, `paid`, `deliver`, `conclu` → `approved`;
- qualquer outro → `unknown`.

### Deduplicação e histórico

- `dedup_key = order:<sha256(orderId|itemId|modelId)>`, sempre por origem.
- Pedido existente com os mesmos dados → `skipped`.
- Pedido existente com status, comissão ou outro campo mutável diferente →
  atualizado e marcado como `imported`, com mensagem de atualização.
- Repetição dentro da mesma execução → `skipped`.
- Cada execução cria um `import_logs` com `report_type="orders"`,
  `data_source="shopee"` e nome
  `shopee:conversion-report:AAAA-MM-DD:AAAA-MM-DD`.
- `rows_imported` conta criados + atualizados; `rows_skipped` conta inalterados e
  repetidos.
- Se o provedor falhar, nada é gravado: a chamada externa acontece antes de
  criar o log.

CSV e Shopee mantêm registros separados mesmo quando o `dedup_key` coincide,
porque `data_source` faz parte da chave única.

### Endpoint

```http
POST /api/conversions/sync?days=30
```

Resposta `201`:

```json
{
  "window_start": "2026-08-16T01:29:46Z",
  "window_end": "2026-11-14T01:29:46Z",
  "total": 0,
  "created": 0,
  "updated": 0,
  "skipped": 0,
  "failed": 0,
  "import_log": {
    "id": 1,
    "filename": "shopee:conversion-report:2026-08-16:2026-11-14",
    "status": "completed",
    "source": "shopee"
  }
}
```

Em modo demo (`providers.conversions is None`) responde
`409 provider_not_supported` com mensagem que pede `GNZL_PROVIDER=shopee`.
`days` fora de `1..90` responde `422 validation_error`. O log aparece em
`GET /api/imports` como qualquer outra importação.

## Erros e resiliência

| código | tratamento |
|---|---|
| `10020` | credencial/assinatura recusada → `provider_auth_error`, sem retry |
| `10035` | conta sem acesso à Open API → `provider_auth_error`, sem retry |
| `10030` | rate limit → backoff e `provider_rate_limited` após 3 tentativas |
| `10000` | erro interno intermitente → até 8 tentativas em queries, com backoff de 0,5 s a 2 s |
| `11001` | parâmetros inválidos → `provider_invalid_response`, sem retry |

HTTP `401/403`, `429`, `5xx`, timeouts e falhas de rede também são tratados.
Nenhuma mensagem de erro inclui App ID ou Secret.

## Correções à documentação não oficial

A documentação comunitária foi útil como pista, mas errou:

- input do link: `ShortLinkInput`, não `GenerateShortLinkInput`;
- `conversionReport` tem `conversionStatus`; `orderStatus` no nó é inválido;
- `conversionReport` recusa variáveis `Int64` com `10010 "wrong type"`; os
  tempos precisam ser literais na query;
- a janela do relatório é limitada aos últimos 90 dias;
- o nó de conversão não tem campos de Sub ID; o vínculo chega em `utmContent`;
- domínio do link curto não é `shope.ee`;
- `listType: 0` não é estável para busca por palavra-chave;
- não existe query de cliques; cliques continuam vindo por CSV.

## Testes

`backend/tests/providers/test_shopee.py` cobre, com `httpx.MockTransport`:

- assinatura sobre os bytes UTF-8;
- mapeamento de preço, comissão, avaliação e vendas;
- `listType: 1` e os valores de `sortType`;
- paginação por `hasNextPage`;
- retry de `10000`/`10030` em query;
- ausência de retry em mutation e timeout ambíguo;
- erros `10020`, `10035`, `11001`;
- rejeição dos filtros não suportados;
- `list_categories()` vazio;
- conversão: mapeamento de item, timestamps inline, paginação por `scrollId`,
  janela de 90 dias, fallback de valores, status, Sub IDs, canal e dedup por
  variante.

`backend/tests/services/test_conversion_sync.py` cobre criação, idempotência,
atualização, isolamento por origem, repetição no mesmo lote, execução vazia,
falha do provedor sem escrita e janela inválida.
`backend/tests/api/test_conversions.py` cobre o `409` em modo demo, o `201`
com histórico, a segunda execução e o `422` de `days`.

A validação manual fez uma busca real e gerou um link de teste com Sub ID
`validacao19a`, sem gravar no banco local. A sincronização real foi executada
com banco descartável: `201`, janela de 90 dias, zero conversões na conta e um
`import_log` concluído.

## Limitações

- Nenhum pedido real existe na conta de desenvolvimento: o mapeamento de
  conversões é validado por schema introspectado e respostas simuladas.
- O separador de múltiplos Sub IDs em `utmContent` não é documentado.
- Sem filtro de categoria por nome enquanto não houver catálogo.
- Sem total de resultados.
- `10000` pode aparecer mesmo após as 8 tentativas; nesse caso a busca retorna
  `503 provider_unavailable` e a interface oferece tentar novamente.
