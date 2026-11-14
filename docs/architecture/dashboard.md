# dashboard — agregações e endpoint (etapa 15)

Métricas de conversão calculadas a partir de `orders` e `clicks`. A tela que
consome esses dados é a etapa 16; aqui ficam apenas as regras e a API.

## Endpoint

```http
GET /api/dashboard?source=csv&start=2026-11-01&end=2026-11-30
```

| parâmetro | regra |
|---|---|
| `source` | obrigatório: `demo`, `shopee` ou `csv` |
| `start` | primeiro dia local; padrão `end - 29 dias` |
| `end` | último dia local; padrão hoje em Brasília |
| janela | no máximo 366 dias |

Origem é obrigatória de propósito: somar `csv` com `shopee` dobraria pedidos que
aparecem nos dois relatórios. O dashboard nunca mistura origens.

Datas são **dias locais** (America/Sao_Paulo) e o limite final é exclusivo. Um
pedido gravado às `2026-11-01T02:59Z` pertence ao dia local `2026-10-31`.

## Fuso horário

O Brasil não tem horário de verão desde 2019, então o fuso de São Paulo é UTC-3
o ano inteiro. O projeto usa um **offset fixo de -3 horas** em vez de
`zoneinfo`, porque `tzdata` não vem instalado no Windows por padrão e a
aplicação precisa rodar sem configuração extra.

- `local_day_start_utc(dia)` devolve `dia 03:00` UTC.
- `local_day_end_utc(dia)` devolve `dia+1 03:00` UTC (exclusivo).
- O agrupamento diário usa `date(coluna, '-3 hours')` do SQLite.

Limitação conhecida: se o Brasil voltar a adotar horário de verão, o offset fixo
precisa ser revisto. A decisão está isolada em `app/core/time.py` e em
`app/repositories/dashboard.py`.

## Métricas

| métrica | cálculo |
|---|---|
| `sales_cents` | soma de `sales_cents` dos pedidos `approved` |
| `commission_cents` | soma de `commission_cents` dos pedidos `approved` |
| `orders` | `count(distinct external_order_id)` dos pedidos `approved` |
| `clicks` | todas as linhas de `clicks` no período |
| `conversion_bp` | `orders / clicks` em pontos-base; `null` sem cliques |
| `average_ticket_cents` | `sales_cents / orders`; `null` sem pedidos |

Pedidos são contados pelo identificador do pedido, não por linha: um pedido com
três itens continua sendo um pedido. Cliques não são filtrados por status
porque o status é do pedido, não do clique.

Conversão é arredondada para o ponto-base mais próximo (`5000` = 50%). Ticket
médio é arredondado para o centavo mais próximo. Nenhum dos dois usa ponto
flutuante.

## Comparação

O período anterior tem a mesma quantidade de dias e termina no dia anterior ao
início do período atual.

```json
"comparisons": {
  "sales_cents": { "previous": 700, "absolute": 2800, "variation_bp": 40000 },
  "orders": { "previous": 1, "absolute": 1, "variation_bp": 10000 }
}
```

`absolute = atual - anterior`. `variation_bp = (atual - anterior) / anterior` em
pontos-base (`40000` = +400%). Quando o período anterior é zero, `variation_bp`
é `null`: não existe base percentual, e inventar 100% ou ∞ esconderia isso.

## Série diária

`daily` traz **todos** os dias do período, inclusive os sem movimento:

```json
{ "date": "2026-11-05", "sales_cents": 19990, "commission_cents": 1700, "orders": 1, "clicks": 1 }
```

Só as quatro métricas aditivas entram na série; conversão e ticket por dia são
deriváveis na tela e não precisam trafegar.

## Rankings

- `top_sub_ids`: até 10 Sub IDs por comissão no período. O grupo `null`
  representa pedidos sem `sub_id_1` e aparece como qualquer outro; os cliques
  são cruzados pelo Sub ID.
- `top_items`: até 10 `external_item_id` por comissão. Linhas sem
  `external_item_id` ficam fora, porque não há identidade para agrupar. O
  título exibido é o mais recente conhecido para o item.

Ordenação determinística: comissão `desc`, vendas `desc`, chave `asc`.

`top_sub_ids` é montado a partir dos pedidos aprovados. Um Sub ID que só teve
cliques, sem venda aprovada, não aparece no ranking — o ranking responde "quem
mais comissionou", não "quem mais recebeu cliques".

## Resposta

```json
{
  "source": "csv",
  "is_demo": false,
  "start": "2026-11-01",
  "end": "2026-11-30",
  "days": 30,
  "previous_start": "2026-10-02",
  "previous_end": "2026-10-31",
  "metrics": {
    "sales_cents": 3500,
    "commission_cents": 350,
    "orders": 2,
    "clicks": 4,
    "conversion_bp": 5000,
    "average_ticket_cents": 1750
  },
  "comparisons": { "...": "..." },
  "daily": ["..."],
  "top_sub_ids": ["..."],
  "top_items": ["..."]
}
```

Erros usam o envelope padrão: `422 validation_error` para origem desconhecida,
período invertido ou janela acima do limite.

## Normalização antes da agregação

CSV e Shopee passam pelas mesmas regras em `app/core/conversion_rules.py`:
classificação de status, separação e canonicalização de Sub IDs, canal, limites
de texto, quantidade padrão e valores não negativos. O teste
`backend/tests/services/test_conversion_normalization.py` percorre os dois
caminhos com o mesmo pedido e exige campos idênticos.

Sem isso, "Aprovado" no CSV e `COMPLETED` na Shopee poderiam cair em grupos
diferentes e o mesmo pedido render números distintos conforme a origem.

## Limitações

- Metas ainda não entram no dashboard (etapa 17).
- Não há filtro por canal ou por Sub ID; os rankings são o recorte disponível.
- O dashboard lê o banco na hora, sem cache: o volume é de uso pessoal.
- A tela e o gráfico são a etapa 16.
