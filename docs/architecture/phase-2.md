# visão da fase 2

Conversão, dashboard, gráficos, metas e importação CSV. A fase 2 continua
local, demo-first e separada da fase 1: nenhum dado real é misturado com dado
fictício sem identificação.

## Etapas

| etapa | entrega | situação |
|---|---|---|
| 13 | Modelagem e migrations de pedidos, cliques, metas e importações | concluída |
| 14 | Importação CSV com validação, deduplicação e relatório de linhas | concluída |
| 15 | Agregações e endpoints de dashboard | pendente |
| 16 | Tela de dashboard com métricas, gráfico e rankings | pendente |
| 17 | Metas: cadastro, acompanhamento e integração com o dashboard | pendente |
| 18 | Testes E2E e fechamento da fase 2 | pendente |

A ordem pode ser ajustada, mas a importação CSV não deve ser implementada antes
de o formato real do relatório ser confirmado com um arquivo de exemplo.

## Modelo de dados

As decisões da fase 1 continuam valendo: centavos, pontos-base, UTC,
`data_source` em toda entidade de dado, migrations como única forma de alterar
o esquema e histórico que não é sobrescrito.

### orders

Uma linha por item de pedido do Conversion Report. Guarda o pedido externo,
produto, data, status, quantidade, valor de venda, comissão, Sub IDs e canal.
`status_group` é a classificação usada nas métricas (`pending`, `approved`,
`cancelled`, `refunded`, `unknown`); o status bruto do relatório fica em
`status`.

`dedup_key` + `data_source` são únicos para que a mesma linha não seja
importada duas vezes, mesmo em arquivos diferentes.

### clicks

Uma linha por clique do Click Report, com data, canal, região, Sub IDs e
`dedup_key`. Cliques podem ser agregados por período, canal ou Sub ID.

### goals

Meta por período e métrica (`commission_cents`, `sales_cents`, `orders` ou
`clicks`). O progresso é calculado no momento da consulta, não persistido.

### import_logs e imported_rows

`import_logs` registra o arquivo, o tipo de relatório, o status da importação e
os contadores. `imported_rows` guarda o resultado linha a linha, inclusive
linhas ignoradas ou com erro, para auditoria e para explicar importações
parciais.

## Métricas do dashboard

- **comissão:** soma de `commission_cents` dos pedidos com status aprovado.
- **vendas:** soma de `sales_cents` dos pedidos com status aprovado.
- **pedidos:** quantidade de pedidos aprovados; quando o relatório for por
  item, agrupar por `external_order_id`.
- **cliques:** contagem de linhas de `clicks`.
- **conversão:** pedidos aprovados divididos por cliques no mesmo período,
  exibida apenas quando houver cliques.
- **ticket médio:** vendas aprovadas divididas por pedidos aprovados.
- **comparação:** período atual contra o período anterior de mesma duração.

Todo agregado deve informar a origem dos dados (`demo`, `shopee` ou `csv`). O
dashboard não soma origens diferentes sem um filtro explícito.

## Importação CSV

O importador usa um contrato canônico e próprio, documentado em
[`import-csv.md`](import-csv.md). Ele está implementado:

- um arquivo por vez, enviado como CSV cru;
- cabeçalho obrigatório, com colunas obrigatórias validadas;
- UTF-8 com ou sem BOM, ou Windows-1252;
- separador vírgula ou ponto e vírgula;
- valores monetários em centavos, como no restante do banco;
- datas em ISO-8601 ou `DD/MM/AAAA HH:MM[:SS]`, convertidas para UTC;
- relatório de linhas importadas, ignoradas e com erro;
- reimportação idempotente por `dedup_key`;
- erros de linha não interrompem o arquivo.

O mapeamento das colunas reais da Shopee continua pendente de um arquivo de
exemplo. Nenhum nome de coluna oficial foi inventado; o adaptador futuro
converterá o relatório oficial para o contrato canônico.

## Dashboard

A tela segue o `DESIGN.md`:

- filtro de período no cabeçalho;
- métricas em faixa horizontal, sem cards;
- um gráfico principal de evolução diária;
- rankings em tabelas;
- estado vazio com explicação e ação para importar um relatório ou gerar dados
  demo;
- nenhum gráfico vazio nem zeros espalhados;
- uma única cor de acento por tela.

Chart.js será usado apenas quando a tela de dashboard for implementada, para
não adicionar dependência antes de existir uso real.

## Critérios de aceitação

- Importar o mesmo CSV duas vezes não duplica pedidos ou cliques.
- Linhas inválidas não derrubam a importação inteira; cada uma tem erro
  registrado.
- Dashboard e metas respeitam o período e a origem selecionados.
- Dados demo aparecem identificados e não contaminam métricas reais.
- Nenhuma migration destrutiva; o banco existente continua válido.
- Testes de backend, frontend e E2E cobrem os fluxos principais.
