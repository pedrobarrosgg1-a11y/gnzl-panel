# modelo de dados — fase 1

Banco: SQLite em `data/gnzl.db`, criado por migrations Alembic
(`backend/migrations/`). Nunca por `create_all()`.

## Decisões que afetam todo o esquema

**Valores monetários em centavos (`INTEGER`).** SQLite não tem tipo decimal;
guardar `REAL` acumula erro em somas de comissão. `price_cents = 19990` é
R$ 199,90.

**Percentuais em pontos-base (`INTEGER`).** `commission_rate_bp = 850` é 8,50%.
A conversão para exibição acontece no schema de resposta.

**`data_source` em toda entidade de dado.** Valores: `demo`, `shopee`, `csv`.
Impede misturar dado fictício de demonstração com dado real sem rótulo.

**Datas em UTC sem timezone.** O SQLite não guarda tzinfo; a conversão para
`America/Sao_Paulo` é feita na apresentação. `created_at`/`updated_at` são
preenchidos por `app/core/time.py:utcnow`.

**Sub IDs sempre canônicos.** Minúsculos, apenas `[a-z0-9-]`, até 64 caracteres.
A regra existe no banco (`CHECK ... NOT GLOB '*[^a-z0-9-]*'`) e é aplicada pelo
serviço antes de qualquer chamada externa. O limite oficial da Shopee será
confirmado quando a Open API for liberada; 64 é o teto local de segurança.

## Tabelas

### products

| coluna | tipo | regra |
|---|---|---|
| `id` | INTEGER | PK |
| `item_id` | INTEGER | obrigatório, único com `shop_id` |
| `shop_id` | INTEGER | obrigatório, único com `item_id` |
| `title` | VARCHAR(300) | obrigatório |
| `image_url` | TEXT | opcional |
| `price_cents` | INTEGER | ≥ 0 |
| `commission_rate_bp` | INTEGER | 0 a 10000 |
| `sales` | INTEGER | ≥ 0 ou nulo (quando a fonte não informa) |
| `rating_x100` | INTEGER | 0 a 500 ou nulo (`485` = 4,85) |
| `category` | VARCHAR(120) | opcional |
| `data_source` | VARCHAR(20) | `demo` · `shopee` · `csv` |
| `created_at`, `updated_at` | DATETIME | UTC |

Índices: `commission_rate_bp`, `sales`, `price_cents`, `category`.

### product_lists

`id` · `name` · `normalized_name` (único) · `description` · `created_at` ·
`updated_at`

`normalized_name` é calculado pelo serviço. Impede "Black Friday" e
"black friday" como listas diferentes.

### product_list_items

`id` · `product_list_id` (FK → `product_lists`, CASCADE) ·
`product_id` (FK → `products`, RESTRICT) · `created_at`

Único por (`product_list_id`, `product_id`). Apagar uma lista remove seus itens;
apagar um produto com vínculos é bloqueado.

### link_batches

`id` · `name` · `destination_type` (`product` | `list`) · `product_list_id`
(FK → `product_lists`, RESTRICT, nulo quando destino é produto) · `observation` ·
`sub_id_1..5` · `data_source` · `total_items` · `successful_items` ·
`failed_items` · `status` (`pending` | `running` | `completed` | `partial` |
`failed`) · `created_at` · `finished_at`

Regras: destino `list` exige `product_list_id`; destino `product` não pode ter
lista; `successful + failed <= total`.

Os Sub IDs ficam no lote para que uma nova execução de itens falhos use
exatamente a configuração original, sem depender do formulário da interface.

### link_batch_items

`id` · `link_batch_id` (FK CASCADE) · `product_id` (FK RESTRICT, opcional) ·
`original_url` · `status` (`pending` | `success` | `failed` | `skipped`) ·
`affiliate_link_id` (FK SET NULL) · `error_code` · `error_message` · `attempts` ·
`processed_at` · `created_at`

Único por (`link_batch_id`, `original_url`). Item com status `success` exige
`affiliate_link_id`. É esta tabela que permite mostrar quais itens falharam,
por quê, e reexecutar apenas eles.

### affiliate_links

`id` · `product_id` (FK RESTRICT, opcional para URL avulsa) · `link_batch_id`
(FK SET NULL) · `original_url` · `affiliate_url` (**único**) · `sub_id_1..5` ·
`observation` · `status` (`active` | `replaced`) · `replaced_by_id` (FK próprio) ·
`data_source` · `created_at`

`affiliate_url` único é a proteção contra duplo envio e contra registro
duplicado de um link determinístico. Regenerar cria outro registro e marca o
anterior como `replaced`, preservando o histórico.

### sub_id_values

`id` · `dimension` (`sub_id_1`..`sub_id_5`) · `normalized_value` · `display_value` ·
`usage_count` · `last_used_at`

Único por (`dimension`, `normalized_value`). Usada para autocomplete e para
padronizar o que já foi digitado em formas diferentes.

## Relacionamentos

```
product_lists 1─N product_list_items N─1 products
link_batches  1─N link_batch_items   N─1 products
link_batches  1─N affiliate_links
products      1─N affiliate_links
affiliate_links 1─1 affiliate_links (replaced_by_id)
```

## Fase 2 e 3

`orders`, `clicks`, `goals`, `import_logs`, `imported_rows`, `sync_logs`,
`videos`, `publication_templates` e `publications` serão modeladas quando as
respectivas fases começarem, seguindo as mesmas decisões (centavos,
`data_source`, UTC).
