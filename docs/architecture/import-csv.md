# importação CSV — fase 2

Importa pedidos (Conversion Report) e cliques (Click Report) sem depender da
Open API da Shopee. O contrato é **canônico e próprio do projeto**: o adaptador
do relatório oficial será escrito quando o arquivo real for confirmado.

## Contrato canônico

### Pedidos

Cabeçalho completo (as colunas obrigatórias precisam existir; as demais são
opcionais):

```csv
order_id,item_id,shop_id,status,status_group,ordered_at,completed_at,quantity,sales_cents,commission_cents,sub_id_1,sub_id_2,sub_id_3,sub_id_4,sub_id_5,channel,title,image_url
```

| coluna | regra |
|---|---|
| `order_id` | obrigatória; identificador do pedido na origem |
| `item_id` | obrigatória; identificador do item |
| `status` | obrigatória; texto bruto do relatório |
| `status_group` | opcional; `pending`, `approved`, `cancelled`, `refunded` ou `unknown` |
| `ordered_at` | obrigatória; ISO-8601 ou `DD/MM/AAAA HH:MM[:SS]` |
| `completed_at` | opcional; mesmo formato de data |
| `quantity` | opcional; inteiro ≥ 0, padrão 1 |
| `sales_cents` | opcional; inteiro em centavos, padrão 0 |
| `commission_cents` | opcional; inteiro em centavos, padrão 0 |
| `sub_id_1..5` | opcionais; normalizados para minúsculas |
| `channel`, `title`, `image_url` | opcionais |

`status` preserva o texto recebido. `status_group` é a classificação usada nas
métricas; quando ausente, fica `unknown` e não entra como venda aprovada.
Nenhum status oficial da Shopee é presumido — o adaptador futuro preencherá a
classificação.

### Cliques

```csv
click_id,clicked_at,region,channel,referrer,sub_id_1,sub_id_2,sub_id_3,sub_id_4,sub_id_5
```

`click_id` e `clicked_at` são obrigatórios. Os demais são opcionais.

## Formatos aceitos

- UTF-8 com ou sem BOM; Windows-1252 como alternativa.
- Separador `,` ou `;` (detectado pelo cabeçalho).
- Datas em ISO-8601 (`2026-11-01T10:00:00`, `Z` ou offset) ou
  `DD/MM/AAAA HH:MM[:SS]`. Datas com offset são convertidas para UTC.
- Valores monetários **já em centavos** (`19990` = R$ 199,90).
- Arquivo de até 10 MB.

## Deduplicação

Cada linha gera uma chave determinística:

- pedido: `order:<sha256(order_id|item_id)>`
- clique: `click:<sha256(click_id)>`

A chave é única com `data_source = 'csv'`. Reimportar o mesmo arquivo não
duplica registros: as linhas voltam como `skipped` e apontam para o pedido ou
clique já existente. Linhas repetidas dentro do próprio arquivo também são
marcadas como `skipped`.

## Resultado por linha

| status | significado |
|---|---|
| `imported` | registro criado e vinculado |
| `skipped` | já existia (arquivo anterior ou repetição interna) |
| `error` | linha inválida; o motivo fica em `message` |

Linhas inválidas não interrompem o arquivo. O `raw_data` guarda os valores
originais para auditoria.

## Status da importação

| status | condição |
|---|---|
| `completed` | nenhuma linha com erro |
| `partial` | há erros, mas ao menos uma linha foi importada ou ignorada |
| `failed` | todas as linhas falharam |

Problemas estruturais (arquivo vazio, cabeçalho ausente, coluna obrigatória
faltando) são recusados com `422 validation_error` e **nada** é gravado.

## API

```text
POST /api/imports/orders?filename=conversion.csv
POST /api/imports/clicks?filename=clicks.csv
GET  /api/imports?report_type=&status=&page=&page_size=
GET  /api/imports/{id}?row_status=&page=&page_size=
```

O corpo do `POST` é o CSV cru (`Content-Type: text/csv`). Exemplo:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/imports/orders?filename=conversion.csv" `
  -H "Content-Type: text/csv" `
  --data-binary "@conversion.csv"
```

O nome do arquivo é reduzido ao nome base antes de ser gravado. O corpo é
lido em memória, com o limite de 10 MB.

## Limitações atuais

- O mapeamento das colunas oficiais da Shopee ainda não existe. É preciso um
  arquivo real de exemplo para escrever o adaptador.
- A interface de importação ainda não foi construída. Ela entra junto do
  dashboard (etapa 16), com estado vazio, seleção de arquivo e relatório de
  linhas.
- O arquivo é processado em uma única transação; arquivos muito grandes
  bloqueiam a requisição até o fim.
