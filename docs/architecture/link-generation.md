# geração de links em lote — fase 1

Fluxo: criar lote → executar → consultar histórico. O lote guarda a
configuração e o resultado item a item; o link gerado é um registro separado e
imutável no histórico.

## Endpoints

| método | rota | função |
|---|---|---|
| `POST` | `/api/link-batches` | cria o lote com os itens ainda pendentes |
| `POST` | `/api/link-batches/{id}/run` | gera os links pendentes e os que falharam |
| `GET` | `/api/link-batches` | lista lotes, com filtros de status e origem |
| `GET` | `/api/link-batches/{id}` | detalhe do lote, com itens e erros |
| `GET` | `/api/links` | histórico, com filtros e busca |
| `GET` | `/api/links/{id}` | detalhe de um link |
| `POST` | `/api/links/{id}/regenerate` | cria novo link e marca o antigo como `replaced` |

## Criação do lote

- `destination_type=product`: recebe `product_ids` na ordem desejada.
- `destination_type=list`: recebe `product_list_id` e copia os produtos da
  lista **no momento da criação**. Alterar a lista depois não muda o lote.
- Produtos de origem diferente da do provedor ativo são recusados. Isso impede
  um lote demo apontar para produto real (ou o contrário).
- Itens são deduplicados por `original_url`, porque a mesma URL não pode
  aparecer duas vezes no lote.
- Limite de **200 itens** por lote (`MAX_BATCH_ITEMS`).
- Os cinco Sub IDs são normalizados na criação (minúsculos, sem acento, apenas
  `[a-z0-9-]`) e gravados no lote.

## Execução

`POST /run` processa apenas itens com status `pending` ou `failed`.

1. O lote passa para `running`.
2. As chamadas ao provedor rodam em um `ThreadPoolExecutor` com
   `GNZL_LINK_CONCURRENCY` workers (1 a 10, padrão 3).
3. Cada falha é capturada por item, sem interromper os demais.
4. Os resultados são gravados na thread da requisição. Uma `Session` do
   SQLAlchemy não é segura para uso concorrente; por isso só a chamada externa
   acontece nas threads.
5. O status final é derivado dos contadores:
   - todos com sucesso → `completed`
   - sucesso e falha → `partial`
   - nenhum sucesso → `failed`

O campo `attempts` conta execuções por item. Um novo `run` reexecuta somente os
que falharam; itens já concluídos não são chamados de novo.

O Sub ID é registrado no autocomplete apenas na primeira execução e se ao menos
um link foi gerado. Repetições de retry não inflam a contagem de uso.

## Deduplicação e regeneração

O link de afiliado é determinístico para a mesma URL de origem + Sub IDs.
`affiliate_url` é único no banco:

- se a URL gerada já existir, o item do lote aponta para o registro existente;
  nenhum link duplicado é criado;
- `POST /api/links/{id}/regenerate` exige Sub IDs diferentes dos atuais. A URL
  nova vira um registro `active` e o anterior passa a `replaced`, com
  `replaced_by_id` apontando para o novo. O histórico não é sobrescrito;
- regenerar sem mudar nada é recusado, porque produziria a mesma URL.

## Limitações conhecidas desta etapa

- A execução é síncrona: a requisição `POST /run` só responde ao final. Com o
  provedor demo é imediato; com a API oficial, o frontend deverá exibir estado
  de carregamento e respeitar o timeout.
- O provedor oficial ainda não está implementado (fase 1, pendente).
  `GNZL_PROVIDER=shopee` falha no startup de forma explícita.
- Não há retry automático com backoff nesta etapa. O retry é manual, pelo mesmo
  endpoint, e reexecuta apenas os itens falhos.
- O limite de 200 itens é local; os limites oficiais da Shopee serão aplicados
  quando a Open API for validada.
