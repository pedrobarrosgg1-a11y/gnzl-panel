# Alembic, SQLite e CHECK constraints

## Sintoma

Ao adicionar colunas com CHECK em uma tabela SQLite, as constraints existentes
apareciam duplicadas e com nome prefixado duas vezes
(`ck_link_batches_ck_link_batches_status`). Uma tentativa de downgrade quebrou
com `no such column` durante a recriação da tabela.

## Causas

1. O SQLite não altera CHECK com `ALTER TABLE`; o `batch_alter_table` recria a
   tabela por baixo.
2. O SQLAlchemy 2.1 **reflete** CHECK constraints existentes. Declará-las de
   novo no `batch_op` duplica tudo.
3. A convenção de nomes `ck_%(table_name)s_%(constraint_name)s` já prefixa o
   nome. Passar `ck_link_batches_status` para `create_check_constraint` gera
   `ck_link_batches_ck_link_batches_status`. Passe apenas o nome curto
   (`status`).
4. O `downgrade` não pode usar `drop_constraint(..., type_="check")` para
   checks que não foram refletidas, e a ordem entre remover coluna e recriar a
   tabela importa.

## Regra prática

- Em migration de coluna com CHECK no SQLite, declare **somente as novas**
  constraints, com nome curto.
- Não redeclare constraints já refletidas.
- Teste `upgrade head`, `downgrade -1` e `upgrade head` em um banco vazio.
- Confira o DDL final em `sqlite_master`; `alembic check` não compara CHECK.

## Referência

Migration `backend/migrations/versions/ecc7e5e706b4_sub_ids_no_lote.py`.
