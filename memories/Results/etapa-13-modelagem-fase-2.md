# Etapa 13 - modelagem de conversão, importações e metas

Data: 2026-11-12

## Entrega

Migration `473328233d10` cria as cinco tabelas da fase 2:

| tabela | função |
|---|---|
| `orders` | uma linha por item do Conversion Report |
| `clicks` | uma linha do Click Report |
| `goals` | meta por período e métrica |
| `import_logs` | cabeçalho de cada importação CSV |
| `imported_rows` | resultado linha a linha da importação |

Nenhuma tabela da fase 1 foi alterada. A migration só adiciona estruturas e não
recria nem apaga dados existentes.

## Decisões

- **`status` e `status_group` em `orders`.** O texto bruto do relatório é
  preservado; a classificação usada nas métricas fica em `status_group`
  (`pending`, `approved`, `cancelled`, `refunded`, `unknown`).
- **`dedup_key` único com `data_source`.** Impede a mesma linha de ser
  importada duas vezes, sem colidir com o mesmo identificador em outra origem.
- **`imported_rows` como auditoria.** Linhas importadas, ignoradas e com erro
  ficam registradas. `ON DELETE CASCADE` remove as linhas junto com a
  importação; `SET NULL` preserva o histórico quando um pedido ou clique é
  removido.
- **No máximo um vínculo de domínio por linha** (`order_id` ou `click_id`),
  garantido por `CHECK`.
- **Metas sem progresso persistido.** `goals` guarda apenas período, métrica e
  alvo. O progresso é calculado na consulta para não envelhecer após uma
  importação.
- **Helper de Sub IDs compartilhado.** `sub_id_format_constraint` saiu de
  `link.py` para `app/models/constraints.py` e passou a ser usado por
  `orders`, `clicks` e `affiliate_links`.

## Evidências

- `pytest`: **143 testes aprovados** (129 anteriores + 14 novos de esquema).
- `test_migration_upgrade_downgrade_upgrade` aprovado: `base → head` recria o
  esquema completo.
- Novos testes cobrem deduplicação, status inválido, formato de Sub ID,
  período de meta, alvo não positivo, unicidade de meta, contadores de
  importação, FK obrigatória, vínculo duplo, cascade e SET NULL.

## Pendências

- O parser CSV da etapa 14 depende de um exemplo real do relatório. Nenhum
  nome de coluna oficial foi inventado.
