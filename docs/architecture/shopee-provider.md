# provedor oficial da shopee — busca e links (etapa 19a)

Integração com a Open API de afiliados da Shopee. Cobre **busca de produtos** e
**geração de link curto**. A sincronização de conversões (19b) fica para depois:
a janela testada não retornou pedidos reais para validar o mapeamento.

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
    "sorts": ["relevance", "commission_desc", "sales_desc", "price_asc", "price_desc"]
  }
}
```

O frontend esconde os controles não suportados. O backend também recusa esses
filtros com `422 validation_error`, para proteger quem chamar a API direto.
Filtrar localmente depois da busca deixaria paginação e contagem erradas.

## Erros e resiliência

| código | tratamento |
|---|---|
| `10020` | credencial/assinatura recusada → `provider_auth_error`, sem retry |
| `10035` | conta sem acesso à Open API → `provider_auth_error`, sem retry |
| `10030` | rate limit → backoff e `provider_rate_limited` após 3 tentativas |
| `10000` | erro interno intermitente → retry com backoff em queries |
| `11001` | parâmetros inválidos → `provider_invalid_response`, sem retry |

HTTP `401/403`, `429`, `5xx`, timeouts e falhas de rede também são tratados.
Nenhuma mensagem de erro inclui App ID ou Secret.

## Correções à documentação não oficial

A documentação comunitária foi útil como pista, mas errou:

- input do link: `ShortLinkInput`, não `GenerateShortLinkInput`;
- `conversionReport` tem `conversionStatus`; `orderStatus` no nó é inválido;
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
- `list_categories()` vazio.

A validação manual fez uma busca real e gerou um link de teste com Sub ID
`validacao19a`, sem gravar no banco local.

## Limitações

- Sem conversões sincronizadas (19b): falta uma resposta real de pedido para
  validar o mapeamento.
- Sem filtro de categoria por nome enquanto não houver catálogo.
- Sem total de resultados.
- `10000` pode aparecer mesmo com retry; nesse caso a busca retorna
  `503 provider_unavailable`.
