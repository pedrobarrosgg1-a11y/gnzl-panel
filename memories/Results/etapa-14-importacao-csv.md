# Etapa 14 - importação CSV

Data: 2026-11-12

## Entrega

Importação de pedidos e cliques por CSV, com contrato canônico próprio:

- `POST /api/imports/orders?filename=...`
- `POST /api/imports/clicks?filename=...`
- `GET /api/imports` (histórico paginado e filtrável)
- `GET /api/imports/{id}` (relatório de linhas, com filtro e paginação)

Arquivos:

- `backend/app/services/csv_import.py`
- `backend/app/repositories/imports.py`
- `backend/app/schemas/imports.py`
- `backend/app/api/imports.py`
- `docs/architecture/import-csv.md`
- `backend/tests/services/test_csv_import.py`
- `backend/tests/api/test_imports.py`

## Decisões

- **Contrato canônico, não Shopee.** As colunas oficiais ainda não foram
  confirmadas. O arquivo aceito usa nomes próprios (`order_id`, `item_id`,
  `click_id`, `sales_cents` etc.). O adaptador do relatório real será escrito
  quando houver um exemplo.
- **`status_group` explícito.** O texto bruto vai para `status`; a
  classificação usada nas métricas é opcional e, quando ausente, fica
  `unknown`. Nada é inferido do texto da Shopee.
- **CSV cru no corpo da requisição.** Evita adicionar `python-multipart` só
  para upload local. O frontend envia o `File` como `text/csv`.
- **Deduplicação antes da inserção.** As chaves existentes são consultadas em
  lote; duplicatas no mesmo arquivo são detectadas em memória. Reimportar não
  cria pedido nem clique novo.
- **Erro de linha não derruba o arquivo.** Cada linha tem status
  `imported`, `skipped` ou `error` e o `raw_data` original.
- **Teto de 10 MB** para o arquivo, validado no serviço.

## Comportamentos verificados

- Reimportação do mesmo arquivo: `imported=0`, `skipped=N`, sem duplicar.
- Linha repetida dentro do mesmo arquivo: ignorada.
- Datas ISO-8601, com offset, `Z` e `DD/MM/AAAA HH:MM[:SS]`.
- Offset convertido para UTC (`10:00-03:00` → `13:00`).
- UTF-8 com BOM, separador `;` e Windows-1252.
- Coluna obrigatória ausente: `422 validation_error`, nada gravado.
- Arquivo vazio ou só com cabeçalho: recusado.
- Todas as linhas com erro: status `failed`; parte com erro: `partial`.
- Nome de arquivo com caminho (`..\..\x.csv`) reduzido ao nome base.

## Evidências

- `pytest`: **164 testes aprovados** (143 anteriores + 21 novos).
- Testes novos: 14 de serviço/parser e 7 de API.

## Limitações

- Sem mapeamento do CSV oficial da Shopee até receber um arquivo real.
- Sem interface de importação; ela entra com o dashboard (etapa 16).
- Processamento síncrono em uma transação.
